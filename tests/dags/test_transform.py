"""
Unit tests for include/etl/transform/transform.py

Covers the per-source aggregation logic (chat/phone/quality/todo) and the
shared `_name_mapper` helper, including its two failure modes: duplicated
mapping keys and unmapped/missing users.
"""
import airflow_stub  # noqa: F401  (stubs airflow when it is not installed, e.g. outside the Astro container)

import pandas as pd
import pytest

from include.etl.transform.transform import (
    _name_mapper,
    transform_chat_data,
    transform_phone_data,
    transform_qs_data,
    transform_todo_summary,
)

FAKE_STORAGE_OPTIONS = {"key": "fake", "secret": "fake"}
NAMES_DF_PATH = "s3://bucket/cleaned/clean_names_data.parquet"


@pytest.fixture(autouse=True)
def patch_s3_boundary(monkeypatch):
    monkeypatch.setattr(
        "include.etl.transform.transform.get_s3_hook_and_storage_options",
        lambda aws_conn_id: (None, FAKE_STORAGE_OPTIONS),
    )
    monkeypatch.setattr("include.utils.dataframes_io.load_to_s3", lambda df, s3_path, storage_options: None)


def names_df():
    return pd.DataFrame(
        {
            "id": [1, 2],
            "name": ["Alice Smith", "Bob Jones"],
            "phone": ["alice.p", "bob.p"],
            "chat": ["alice.c", "bob.c"],
            "email_address": ["alice@x.com", "bob@x.com"],
            "todo_file": ["alice.xlsx", "bob.xlsx"],
        }
    )


def fake_read_dataframe_factory(source_df):
    """Returns a stand-in for read_dataframe: cleaned/source data for the first
    call, names_df for the second (the names_df_path lookup)."""

    def _reader(s3_path, storage_options=None, **kwargs):
        if s3_path == NAMES_DF_PATH:
            return names_df()
        return source_df

    return _reader


def test_name_mapper_raises_on_duplicated_map_column():
    dup_names = pd.DataFrame({"chat": ["alice.c", "alice.c"], "name": ["Alice", "Alice2"]})
    df = pd.DataFrame({"user": ["alice.c"]})

    import include.etl.transform.transform as transform_mod

    # bypass the real S3 read by monkeypatching read_dataframe inline
    orig_read = transform_mod.read_dataframe
    transform_mod.read_dataframe = lambda *a, **k: dup_names
    try:
        with pytest.raises(ValueError, match="Duplicated values"):
            _name_mapper(
                df=df, names_df_path=NAMES_DF_PATH, storage_options=FAKE_STORAGE_OPTIONS,
                map_to_col="chat", col_to_map="user",
            )
    finally:
        transform_mod.read_dataframe = orig_read


def test_name_mapper_raises_on_missing_user():
    import include.etl.transform.transform as transform_mod

    df = pd.DataFrame({"user": ["unknown.c"]})
    orig_read = transform_mod.read_dataframe
    transform_mod.read_dataframe = lambda *a, **k: names_df()
    try:
        with pytest.raises(ValueError, match="Missing users"):
            _name_mapper(
                df=df, names_df_path=NAMES_DF_PATH, storage_options=FAKE_STORAGE_OPTIONS,
                map_to_col="chat", col_to_map="user",
            )
    finally:
        transform_mod.read_dataframe = orig_read


def test_transform_chat_data_groups_and_maps_names(monkeypatch):
    cleaned_chat = pd.DataFrame(
        {
            "record_id": [1, 2, 3],
            "user": ["alice.c", "alice.c", "bob.c"],
        }
    )
    monkeypatch.setattr(
        "include.etl.transform.transform.read_dataframe",
        fake_read_dataframe_factory(cleaned_chat),
    )

    captured = {}
    monkeypatch.setattr(
        "include.utils.dataframes_io.load_to_s3",
        lambda df, s3_path, storage_options: captured.update(df=df),
    )

    transform_chat_data(
        aws_conn_id="aws_default", s3_path="s3://bucket/cleaned/clean_chat_scores.parquet",
        bucket="bucket", processed_folder="processed/", names_df_path=NAMES_DF_PATH,
    )

    out = captured["df"].set_index("user")
    assert out.loc["Alice Smith", "total_chats"] == 2
    assert out.loc["Bob Jones", "total_chats"] == 1


def test_transform_phone_data_maps_names_and_keeps_totals(monkeypatch):
    cleaned_phone = pd.DataFrame({"user": ["alice.p", "bob.p"], "total_calls": [10, 5]})
    monkeypatch.setattr(
        "include.etl.transform.transform.read_dataframe",
        fake_read_dataframe_factory(cleaned_phone),
    )

    captured = {}
    monkeypatch.setattr(
        "include.utils.dataframes_io.load_to_s3",
        lambda df, s3_path, storage_options: captured.update(df=df),
    )

    transform_phone_data(
        aws_conn_id="aws_default", s3_path="s3://bucket/cleaned/clean_phone_data.parquet",
        bucket="bucket", processed_folder="processed/", names_df_path=NAMES_DF_PATH,
    )

    out = captured["df"].set_index("user")
    assert out.loc["Alice Smith", "total_calls"] == 10
    assert out.loc["Bob Jones", "total_calls"] == 5


def test_transform_qs_data_computes_pass_rate_percentage(monkeypatch):
    cleaned_qs = pd.DataFrame(
        {
            "ticket_id": ["T1", "T2", "T3", "T4"],
            "quality_pass": ["in ordnung", "in ordnung", "in ordnung", "durchgefallen"],
            "user": ["Alice Smith", "Alice Smith", "Alice Smith", "Alice Smith"],
        }
    )
    monkeypatch.setattr("include.etl.transform.transform.read_dataframe", lambda *a, **k: cleaned_qs)

    captured = {}
    monkeypatch.setattr(
        "include.utils.dataframes_io.load_to_s3",
        lambda df, s3_path, storage_options: captured.update(df=df),
    )

    transform_qs_data(
        aws_conn_id="aws_default", s3_path="s3://bucket/cleaned/clean_qs_data.parquet",
        bucket="bucket", processed_folder="processed/",
    )

    out = captured["df"].set_index("user")
    assert out.loc["Alice Smith", "qs_score"] == 75.0


def test_transform_todo_summary_counts_emails_and_todos(monkeypatch):
    alice_todo = pd.DataFrame({"emails": ["a@x.com", None, "c@x.com"], "to_do": ["Fix bug", "Call back", None]})
    bob_todo = pd.DataFrame({"emails": [None], "to_do": ["Update ticket"]})

    def fake_read_dataframe(s3_path, storage_options=None, **kwargs):
        if s3_path == NAMES_DF_PATH:
            return names_df()
        if "alice" in s3_path:
            return alice_todo
        return bob_todo

    monkeypatch.setattr("include.etl.transform.transform.read_dataframe", fake_read_dataframe)

    captured = {}
    monkeypatch.setattr(
        "include.utils.dataframes_io.load_to_s3",
        lambda df, s3_path, storage_options: captured.update(df=df),
    )

    transform_todo_summary(
        aws_conn_id="aws_default",
        s3_paths=["s3://bucket/cleaned/todo/alice.parquet", "s3://bucket/cleaned/todo/bob.parquet"],
        bucket="bucket", processed_folder="processed/", names_df_path=NAMES_DF_PATH,
    )

    out = captured["df"].set_index("user")
    assert out.loc["Alice Smith", "emails_count"] == 2
    assert out.loc["Alice Smith", "todos_count"] == 2
    assert out.loc["Bob Jones", "emails_count"] == 0
    assert out.loc["Bob Jones", "todos_count"] == 1
