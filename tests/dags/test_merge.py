"""
Unit tests for include/etl/transform/merge.py

Covers the final join of all processed sources into the productivity table,
including the fillna-on-missing-source behaviour and the appended 'Total' row.
"""
import airflow_stub  # noqa: F401  (stubs airflow when it is not installed, e.g. outside the Astro container)

import pandas as pd
import pytest

from include.etl.transform.merge import productivity_table

FAKE_STORAGE_OPTIONS = {"key": "fake", "secret": "fake"}


@pytest.fixture(autouse=True)
def patch_s3_boundary(monkeypatch):
    monkeypatch.setattr(
        "include.etl.transform.merge.get_s3_hook_and_storage_options",
        lambda aws_conn_id: (None, FAKE_STORAGE_OPTIONS),
    )
    monkeypatch.setattr("include.utils.dataframes_io.load_to_s3", lambda df, s3_path, storage_options: None)


def _sources():
    todo_summary = pd.DataFrame(
        {"user": ["Alice Smith", "Bob Jones"], "emails_count": [2, 0], "todos_count": [2, 1]}
    )
    chat = pd.DataFrame({"user": ["Alice Smith", "Bob Jones"], "total_chats": [5, 3]})
    phone = pd.DataFrame({"user": ["Alice Smith", "Bob Jones"], "total_calls": [10, 5]})
    # Bob has no quality score this week (e.g. no tickets were QS-reviewed)
    quality = pd.DataFrame({"user": ["Alice Smith"], "qs_score": [80.0]})

    return {
        "todo_summary": "s3://bucket/processed/transform_todo_summary.parquet",
        "chat": "s3://bucket/processed/transform_chat_data.parquet",
        "phone": "s3://bucket/processed/transform_phone_data.parquet",
        "quality": "s3://bucket/processed/transform_qs_data.parquet",
    }, {
        "s3://bucket/processed/transform_todo_summary.parquet": todo_summary,
        "s3://bucket/processed/transform_chat_data.parquet": chat,
        "s3://bucket/processed/transform_phone_data.parquet": phone,
        "s3://bucket/processed/transform_qs_data.parquet": quality,
    }


def test_productivity_table_merges_all_sources_and_adds_total_row(monkeypatch):
    s3_paths, tables = _sources()
    monkeypatch.setattr(
        "include.etl.transform.merge.read_dataframe",
        lambda s3_path, storage_options=None, **kwargs: tables[s3_path],
    )

    captured = {}
    monkeypatch.setattr(
        "include.utils.dataframes_io.load_to_s3",
        lambda df, s3_path, storage_options: captured.update(df=df),
    )

    productivity_table(
        aws_conn_id="aws_default", s3_paths=s3_paths, bucket="bucket", processed_folder="processed/",
    )

    out = captured["df"].set_index("user")

    # per-user totals: emails + todos + chats + calls
    assert out.loc["Alice Smith", "total"] == 2 + 2 + 5 + 10
    assert out.loc["Bob Jones", "total"] == 0 + 1 + 3 + 5

    # Bob had no QS-reviewed tickets: his score should be missing, not zero
    assert pd.isna(out.loc["Bob Jones", "qs_score"])
    assert out.loc["Alice Smith", "qs_score"] == 80.0

    # a 'Total' row is appended, summing counts and averaging the qs_score
    assert "Total" in out.index
    assert out.loc["Total", "total_chats"] == 5 + 3
    assert out.loc["Total", "total_calls"] == 10 + 5
    assert out.loc["Total", "emails_count"] == 2
    assert out.loc["Total", "qs_score"] == 80.0  # mean of non-NaN scores


def test_productivity_table_raises_on_duplicate_user_in_a_source(monkeypatch):
    s3_paths, tables = _sources()
    # introduce a duplicate 'user' key in the chat source -> merge(validate='one_to_one') must fail
    duplicated_chat = pd.DataFrame(
        {"user": ["Alice Smith", "Alice Smith"], "total_chats": [5, 1]}
    )
    tables["s3://bucket/processed/transform_chat_data.parquet"] = duplicated_chat

    monkeypatch.setattr(
        "include.etl.transform.merge.read_dataframe",
        lambda s3_path, storage_options=None, **kwargs: tables[s3_path],
    )

    with pytest.raises(Exception):
        productivity_table(
            aws_conn_id="aws_default", s3_paths=s3_paths, bucket="bucket", processed_folder="processed/",
        )
