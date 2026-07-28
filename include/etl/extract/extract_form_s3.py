from pathlib import PurePosixPath

from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from include.config.logger import setup_logger
from include.utils.s3_utils import get_s3_hook_and_storage_options

logging = setup_logger(__name__)

SUPPORTED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'parquet', 'json'}
TODO_EXTENSIONS = {'xls', 'xlsx'}

def identify_file(file_name: str, file_patterns) -> str | None:
    """
    Identify the logical file type from its filename.
    Example:
    Filename:
        Vayu_History_Served_Requests_MOCK.csv

    Pattern configuration:
        {"chat": "vayu"}

    Result:
        "chat"
    """

    logging.info(f"Identifying file type for {file_name}")

    normalized_file_name = file_name.casefold()
    matching_file_types = []

    for file_type, patern in file_patterns.items():
        if patern.casefold() in normalized_file_name:
            matching_file_types.append(file_type)

    if not matching_file_types:
        return None

    if len(matching_file_types) > 1:
        raise ValueError(
            f"File '{file_name}' matches multiple file types: "
            f"{matching_file_types}. Make the patterns more specific."
        )

    return matching_file_types[0]


def _list_files_with_extension(s3_hook: S3Hook, bucket: str, prefix: str, allowed_extensions: set[str]) -> list[str]:
    """
    Shared listing logic for both discovery functions: list every object key under
    `prefix`, skip folder markers, keep only files whose extension is in
    `allowed_extensions`, and return them as full s3:// paths.
    """
    keys = s3_hook.list_keys(bucket_name=bucket, prefix=prefix) or []
    logging.info(f"Found {len(keys)} files in s3://{bucket}/{prefix}")

    paths = []

    for key in keys:
        if key.endswith("/"):
            continue

        extension = PurePosixPath(key).suffix.lower().lstrip(".")

        if extension not in allowed_extensions:
            logging.warning(f"File type '{extension}' is not supported. Skipping s3://{bucket}/{key}")
            continue

        paths.append(f"s3://{bucket}/{key}")

    return paths


def get_s3_paths(
        aws_conn_id: str,
        bucket: str,
        folders: list[str] | tuple[str, ...],
        file_patterns : dict[str, str],
        required_file_types: set[str] | None = None
)-> dict[str, str]:
    """
    Search configured S3 folders and map logical file types to S3 paths.
    Example result:
        {
            "chat": "s3://bucket/raw-data/chat.csv",
            "phone": "s3://bucket/raw-data/phone.xlsx",
        }
    """

    if not folders:
        raise ValueError("At least on S3 folder is needed")

    if not file_patterns:
        raise ValueError("At least one file pattern should be configured")

    s3_hook, _ = get_s3_hook_and_storage_options(aws_conn_id)

    discovered_paths = {}

    for folder in folders:
        logging.info(f"Searching for source files in s3://{bucket}/{folder}")

        s3_paths = _list_files_with_extension(
            s3_hook=s3_hook,bucket=bucket,prefix=folder,allowed_extensions=SUPPORTED_EXTENSIONS
        )

        for s3_path in s3_paths:
            file_name = PurePosixPath(s3_path).name
            file_type = identify_file(file_name=file_name, file_patterns=file_patterns)

            if file_type is None:
                logging.warning(f"Could not classify file: {s3_path}")
                continue

            discovered_paths[file_type] = s3_path
            logging.info(f"Identified {file_type}  in {s3_path}")

    required_type = required_file_types or set()
    missing_types = required_type - discovered_paths.keys()

    if missing_types:
        raise ValueError(f"Required source files were not found for types: {missing_types}")

    if not discovered_paths:
        raise FileNotFoundError(f"No source files were found in: {folders}")

    logging.info(f"Successfully discovered source files for: {discovered_paths}")

    return discovered_paths


def get_todo_s3_paths(aws_conn_id: str, bucket: str, todo_folder: str) -> list[str]:
    """
   Discover every Excel workbook in the TODO folder.
   Unlike regular-file discovery, TODO files are not classified by filename.
   Every Excel workbook in the configured TODO folder is returned.
   """
    s3_hook, _ = get_s3_hook_and_storage_options(aws_conn_id)

    keys = s3_hook.list_keys(bucket_name=bucket, prefix=todo_folder) or []
    logging.info(f"Found {len(keys)} files in S3 {bucket}/{todo_folder}")

    todo_paths = _list_files_with_extension(
        s3_hook=s3_hook,
        bucket=bucket,
        prefix=todo_folder,
        allowed_extensions=TODO_EXTENSIONS,
    )

    if not todo_paths:
        raise FileNotFoundError(f"No TODO files in: {todo_folder}")

    todo_paths.sort()

    return todo_paths
