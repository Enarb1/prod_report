"""
Unit tests for include/etl/extract/extract_form_s3.py

Covers filename-to-file-type classification and the S3 discovery functions,
using a fake S3Hook so no real AWS calls are made.
"""
import airflow_stub  # noqa: F401  (stubs airflow when it is not installed, e.g. outside the Astro container)

import pytest

from include.etl.extract.extract_form_s3 import get_s3_paths, get_todo_s3_paths, identify_file

FILE_PATTERNS = {"chat": "vayu", "phone": "phone_report", "quality": "qs_export", "names": "agent_names"}


class FakeS3Hook:
    """Stand-in for airflow.providers.amazon.aws.hooks.s3.S3Hook."""

    def __init__(self, keys):
        self._keys = keys

    def list_keys(self, bucket_name=None, prefix=None):
        return [k for k in self._keys if k.startswith(prefix)]


@pytest.fixture(autouse=True)
def patch_s3_hook(monkeypatch):
    def _patch(keys):
        monkeypatch.setattr(
            "include.etl.extract.extract_form_s3.get_s3_hook_and_storage_options",
            lambda aws_conn_id: (FakeS3Hook(keys), {}),
        )
    return _patch


def test_identify_file_matches_expected_pattern():
    assert identify_file("Vayu_History_Served_Requests_MOCK.csv", FILE_PATTERNS) == "chat"
    assert identify_file("phone_report_week30.xlsx", FILE_PATTERNS) == "phone"


def test_identify_file_returns_none_when_no_pattern_matches():
    assert identify_file("random_export.csv", FILE_PATTERNS) is None


def test_identify_file_raises_on_ambiguous_match():
    patterns = {"chat": "report", "phone": "report"}
    with pytest.raises(ValueError, match="matches multiple file types"):
        identify_file("weekly_report.csv", patterns)


def test_get_s3_paths_classifies_and_skips_unsupported_extensions(patch_s3_hook):
    patch_s3_hook(
        keys=[
            "raw-data/",  # folder marker, must be skipped
            "raw-data/Vayu_History_Served_Requests_MOCK.csv",
            "raw-data/phone_report_week30.xlsx",
            "raw-data/notes.txt",  # unsupported extension, must be skipped
        ]
    )

    result = get_s3_paths(
        aws_conn_id="aws_default", bucket="bucket",
        folders=["raw-data/"], file_patterns=FILE_PATTERNS,
    )

    assert result == {
        "chat": "s3://bucket/raw-data/Vayu_History_Served_Requests_MOCK.csv",
        "phone": "s3://bucket/raw-data/phone_report_week30.xlsx",
    }


def test_get_s3_paths_raises_when_required_type_is_missing(patch_s3_hook):
    patch_s3_hook(keys=["raw-data/phone_report_week30.xlsx"])

    with pytest.raises(ValueError, match="Required source files were not found"):
        get_s3_paths(
            aws_conn_id="aws_default", bucket="bucket",
            folders=["raw-data/"], file_patterns=FILE_PATTERNS,
            required_file_types={"chat"},
        )


def test_get_s3_paths_raises_when_no_folders_given():
    with pytest.raises(ValueError, match="At least on S3 folder"):
        get_s3_paths(aws_conn_id="aws_default", bucket="bucket", folders=[], file_patterns=FILE_PATTERNS)


def test_get_todo_s3_paths_returns_only_excel_files_sorted(patch_s3_hook):
    patch_s3_hook(
        keys=[
            "todo/bob.xlsx",
            "todo/alice.xlsx",
            "todo/readme.txt",
        ]
    )

    result = get_todo_s3_paths(aws_conn_id="aws_default", bucket="bucket", todo_folder="todo/")

    assert result == ["s3://bucket/todo/alice.xlsx", "s3://bucket/todo/bob.xlsx"]


def test_get_todo_s3_paths_raises_when_folder_is_empty(patch_s3_hook):
    patch_s3_hook(keys=[])

    with pytest.raises(FileNotFoundError, match="No TODO files"):
        get_todo_s3_paths(aws_conn_id="aws_default", bucket="bucket", todo_folder="todo/")
