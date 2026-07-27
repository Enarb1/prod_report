from pathlib import PurePosixPath

from include.config.logger import setup_logger
from include.utils.s3_utils import get_s3_hook_and_storage_options

logging = setup_logger(__name__)

SUPPORTED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'parquet', 'json'}


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

    file_pattens = {
        'chat': 'Vayu',
        'phone': 'Statistic_user',
        'quality': 'qs',
        'names': 'names'
    }

    normalized_file_name = file_name.casefold()
    matching_file_types = []

    for file_type, patern in file_pattens.items():
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

        keys = s3_hook.list_keys(bucket_name=bucket, prefix=folder) or []
        logging.info(f"Found {len(keys)} files in s3://{bucket}/{folder}")

        for key in keys:
            if key.endswith("/"):
                continue

            path = PurePosixPath(key)
            extension = path.suffix.lower().lstrip(".")

            if extension not in SUPPORTED_EXTENSIONS:
                logging.warning(f"File type '{extension}' is not supported. Skipping")
                continue

            file_type = identify_file(file_name=path.name, file_patterns=file_patterns)

            if file_type is None:
                logging.warning(f"Could not classify file: s3://{bucket}/{key}")
                continue

            s3_path = f"s3://{bucket}/{key}"

            if file_type in discovered_paths:
                raise ValueError(f"Multiple files identified as {file_type} in s3://{bucket}/{key}")

            discovered_paths[file_type] = s3_path
            logging.info(f"Identified {file_type} in s3://{bucket}/{key}")

    required_type = required_file_types or set()

    missing_types = required_type - discovered_paths.keys()

    if missing_types:
        raise ValueError(f"Required source files were not found for types: {missing_types}")

    if not discovered_paths:
        raise FileNotFoundError(f"No source files were found in: {folders}")

    logging.info(f"Successfully discovered source files for: {discovered_paths}")

    return discovered_paths