"""
Unit tests for include/etl/transform/clean.py

These tests exercise the cleaning logic (column renaming, filtering, casting)
without touching real S3 or Snowflake. `get_s3_hook_and_storage_options` and
`read_dataframe`/`load_to_s3` are patched so no network calls are made; the
real pandera validation in `safe_df_to_s3` still runs, so a test also fails
if a cleaner stops producing a schema-valid output.
"""
import airflow_stub  # noqa: F401  (stubs airflow when it is not installed, e.g. outside the Astro container)

import pandas as pd
import pytest

from include.etl.transform.clean import (
    clean_chat_scores,
    clean_names_data,
    clean_phone_data,
    clean_qs_data,
    clean_todo_data,
    col_headers_to_snake_case,
    get_previous_cw_sheet_name,
)


FAKE_STORAGE_OPTIONS = {"key": "fake", "secret": "fake"}


@pytest.fixture(autouse=True)
def patch_s3_boundary(monkeypatch):
    """
    Patch the S3 boundary for every clean_* function: no real credentials are
    fetched and no parquet file is actually written to S3.
    """
    monkeypatch.setattr(
        "include.etl.transform.clean.get_s3_hook_and_storage_options",
        lambda aws_conn_id: (None, FAKE_STORAGE_OPTIONS),
    )
    monkeypatch.setattr("include.utils.dataframes_io.load_to_s3", lambda df, s3_path, storage_options: None)


def test_col_headers_to_snake_case():
    df = pd.DataFrame(columns=["RecordId", "Employee Name", "  Total Calls[Number] "])
    result = col_headers_to_snake_case(df)
    assert result.columns.tolist() == ["record_id", "employee_name", "total_calls_number"]


def test_col_headers_to_snake_case_does_not_mutate_input():
    df = pd.DataFrame(columns=["Employee Name"])
    col_headers_to_snake_case(df)
    assert df.columns.tolist() == ["Employee Name"]


@pytest.mark.parametrize(
    "ref_date,expected",
    [
        (__import__("datetime").date(2026, 7, 27), "CW30"),
        (__import__("datetime").date(2026, 1, 5), "CW1"),
    ],
)
def test_get_previous_cw_sheet_name(ref_date, expected):
    assert get_previous_cw_sheet_name(ref_date) == expected


def test_clean_chat_scores_keeps_and_renames_expected_columns(monkeypatch):
    raw = pd.DataFrame(
        {
            "RecordId": ["1", "2", None],
            "EmployeeName": [" Alice ", "Bob", "Carol"],
            "ChatType": ["Support", "Support", "Support"],
        }
    )
    monkeypatch.setattr("include.etl.transform.clean.read_dataframe", lambda *a, **k: raw)

    result_path = clean_chat_scores(
        aws_conn_id="aws_default", s3_path="s3://bucket/raw/chat.csv",
        s3_bucket="bucket", cleaned_data_folder="cleaned/",
    )

    assert result_path == "s3://bucket/cleaned/clean_chat_scores.parquet"


def test_clean_chat_scores_output_content(monkeypatch):
    raw = pd.DataFrame(
        {
            "RecordId": ["1", "2", None],
            "EmployeeName": [" Alice ", "Bob", "Carol"],
        }
    )
    monkeypatch.setattr("include.etl.transform.clean.read_dataframe", lambda *a, **k: raw)

    captured = {}
    monkeypatch.setattr(
        "include.utils.dataframes_io.load_to_s3",
        lambda df, s3_path, storage_options: captured.update(df=df),
    )

    clean_chat_scores(
        aws_conn_id="aws_default", s3_path="s3://bucket/raw/chat.csv",
        s3_bucket="bucket", cleaned_data_folder="cleaned/",
    )

    out = captured["df"]
    # the row with a missing record_id must be dropped
    assert len(out) == 2
    assert list(out.columns) == ["record_id", "user"]
    assert out["record_id"].tolist() == [1, 2]
    assert out["user"].tolist() == ["Alice", "Bob"]
    assert out["record_id"].dtype.kind == "i"


def test_clean_phone_data_drops_summe_row(monkeypatch):
    raw = pd.DataFrame(
        {
            "User": ["Alice", "Bob", "Summe"],
            "AcceptedCallsNumber": [10, 5, 15],
        }
    )
    monkeypatch.setattr("include.etl.transform.clean.read_dataframe", lambda *a, **k: raw)

    captured = {}
    monkeypatch.setattr(
        "include.utils.dataframes_io.load_to_s3",
        lambda df, s3_path, storage_options: captured.update(df=df),
    )

    clean_phone_data(
        aws_conn_id="aws_default", s3_path="s3://bucket/raw/phone.csv",
        s3_bucket="bucket", cleaned_data_folder="cleaned/",
    )

    out = captured["df"]
    assert "Summe" not in out["user"].tolist()
    assert out["total_calls"].tolist() == [10, 5]


def test_clean_qs_data_maps_german_columns_and_lowercases_status(monkeypatch):
    raw = pd.DataFrame(
        {
            "Ticketnummer": ["T-1", "T-2"],
            "AmpelstatusTicketQs": [" In Ordnung ", "DURCHGEFALLEN"],
            "Ersteller": ["Alice", "Bob"],
        }
    )
    monkeypatch.setattr("include.etl.transform.clean.read_dataframe", lambda *a, **k: raw)

    captured = {}
    monkeypatch.setattr(
        "include.utils.dataframes_io.load_to_s3",
        lambda df, s3_path, storage_options: captured.update(df=df),
    )

    clean_qs_data(
        aws_conn_id="aws_default", s3_path="s3://bucket/raw/qs.xlsx",
        s3_bucket="bucket", cleaned_data_folder="cleaned/",
    )

    out = captured["df"]
    assert out["quality_pass"].tolist() == ["in ordnung", "durchgefallen"]
    assert set(out.columns) == {"ticket_id", "quality_pass", "user"}


def test_clean_names_data_casts_id_and_strips_text(monkeypatch):
    raw = pd.DataFrame(
        {
            "Id": ["1", "2"],
            "Name": [" Alice ", "Bob "],
            "Phone": ["alice.p", "bob.p"],
            "Chat": ["alice.c", "bob.c"],
            "EmailAddress": ["alice@x.com", "bob@x.com"],
            "TodoFile": ["alice.xlsx", "bob.xlsx"],
        }
    )
    monkeypatch.setattr("include.etl.transform.clean.read_dataframe", lambda *a, **k: raw)

    captured = {}
    monkeypatch.setattr(
        "include.utils.dataframes_io.load_to_s3",
        lambda df, s3_path, storage_options: captured.update(df=df),
    )

    clean_names_data(
        aws_conn_id="aws_default", s3_path="s3://bucket/raw/names.csv",
        s3_bucket="bucket", cleaned_data_folder="cleaned/",
    )

    out = captured["df"]
    assert out["id"].dtype.kind == "i"
    assert out["name"].tolist() == ["Alice", "Bob"]


def test_clean_todo_data_returns_one_path_per_file(monkeypatch):
    raw = pd.DataFrame({"Emails": ["a@x.com", None], "ToDo": ["Fix bug", "Reply to client"]})
    monkeypatch.setattr("include.etl.transform.clean.read_dataframe", lambda *a, **k: raw)
    monkeypatch.setattr("include.utils.dataframes_io.load_to_s3", lambda df, s3_path, storage_options: None)

    paths = clean_todo_data(
        aws_conn_id="aws_default",
        todo_files=["s3://bucket/todo/alice.xlsx", "s3://bucket/todo/bob.xlsx"],
        s3_bucket="bucket",
        cleaned_data_folder="cleaned/todo/",
    )

    assert paths == [
        "s3://bucket/cleaned/todo/alice.parquet",
        "s3://bucket/cleaned/todo/bob.parquet",
    ]
