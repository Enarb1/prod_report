from airflow.sdk import dag, task
from pendulum import datetime

from include.etl.extract.extract_form_s3 import get_s3_paths
from include.config.settings import AWS_CONN_ID, S3_BUCKET, S3_NAMES_DATA, S3_EXTRACTED_DATA, S3_FILE_PATTERNS, \
    S3_REQUIRED_FILE_TYPES


@dag(
    dag_id="etl_pipeline",
    schedule="0 7 * * 1",  # Every Monday at 07:00
    start_date=datetime(2026, 7, 1),
    catchup=False,
)
def etl_pipeline():

    @task
    def discover_source_files() -> dict[str, str]:
        return get_s3_paths(
            aws_conn_id=AWS_CONN_ID,
            bucket=S3_BUCKET,
            folders=[S3_NAMES_DATA, S3_EXTRACTED_DATA],
            file_patterns=S3_FILE_PATTERNS,
            required_file_types=S3_REQUIRED_FILE_TYPES
        )

    source_files = discover_source_files()

etl_pipeline()