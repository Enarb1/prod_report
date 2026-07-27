import yaml

from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent / 'config.yaml'

def load_config() -> dict[str, Any]:

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")

    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(f"Invalid configuration.File in {CONFIG_PATH} is empty")

    return config

CONFIG = load_config()

AWS_CONFIG = CONFIG["aws"]
RAW_DATA_FOLDERS = AWS_CONFIG["folders"]["raw_data"]

AWS_CONN_ID = AWS_CONFIG["conn_id"]
S3_BUCKET = AWS_CONFIG["bucket"]

S3_EXTRACTED_DATA = RAW_DATA_FOLDERS["extracted_data"]
S3_NAMES_DATA = RAW_DATA_FOLDERS["names"]
S3_TODO_DATA = RAW_DATA_FOLDERS["todo_data"]

S3_DISCOVERY_FOLDERS = (
    S3_EXTRACTED_DATA,
    S3_NAMES_DATA,
)

S3_FILE_PATTERNS = AWS_CONFIG["file_patterns"]

S3_REQUIRED_FILE_TYPES = set(
    AWS_CONFIG.get("required_file_types", [])
)

SNOWFLAKE_CONFIG = CONFIG["snowflake"]

SNOWFLAKE_CONN_ID = SNOWFLAKE_CONFIG["conn_id"]
SNOWFLAKE_DATABASE = SNOWFLAKE_CONFIG["database"]