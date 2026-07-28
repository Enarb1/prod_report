from airflow.sdk import dag, task
from pendulum import datetime

from include.etl.extract.extract_form_s3 import get_s3_paths, get_todo_s3_paths
from include.config.settings import (AWS_CONN_ID, S3_BUCKET,S3_FILE_PATTERNS, \
    S3_REQUIRED_FILE_TYPES, S3_TODO_DATA, S3_CLEANED_EXTRACTED_DATA, S3_CLEANED_TODO_DATA, S3_DISCOVERY_FOLDERS,
                                     S3_PROCESSED_DATA_FOLDER)
from include.etl.transform.clean import (clean_chat_scores, clean_phone_data, clean_qs_data, clean_names_data,
                                         clean_todo_data)
from include.etl.transform.transform import transform_chat_data


CLEANERS = {
    'chat': clean_chat_scores,
    'phone': clean_phone_data,
    'quality': clean_qs_data,
    'names': clean_names_data,
}


@dag(
    dag_id="etl_pipeline",
    schedule="0 7 * * 1",  # Every Monday at 07:00
    start_date=datetime(2026, 7, 1),
    catchup=False,
)
def etl_pipeline():

    @task
    def discover_source_files() -> dict:
        regular_files = get_s3_paths(
            aws_conn_id=AWS_CONN_ID,
            bucket=S3_BUCKET,
            folders=S3_DISCOVERY_FOLDERS,
            file_patterns=S3_FILE_PATTERNS,
            required_file_types=S3_REQUIRED_FILE_TYPES
        )

        todo_files = get_todo_s3_paths(
            aws_conn_id=AWS_CONN_ID,
            bucket=S3_BUCKET,
            todo_folder=S3_TODO_DATA,
        )

        return {
            **regular_files,
            "todo_files": todo_files,
        }


    @task
    def clean_data(files: dict) -> dict:
        cleaned_files = {
            file_type: cleaner(
                aws_conn_id=AWS_CONN_ID,
                s3_path=files[file_type],
                s3_bucket=S3_BUCKET,
                cleaned_data_folder=S3_CLEANED_EXTRACTED_DATA,
            )
            for file_type, cleaner in CLEANERS.items()
        }

        cleaned_files['todo_files'] = clean_todo_data(
            aws_conn_id=AWS_CONN_ID,
            todo_files=files['todo_files'],
            s3_bucket=S3_BUCKET,
            cleaned_data_folder=S3_CLEANED_TODO_DATA
        )

        return cleaned_files

    @task
    def transform_data(files: dict) -> dict:
        transformed_files = {}
        # TODO map usernames
        transformed_files['chat'] = transform_chat_data(
            aws_conn_id=AWS_CONN_ID,
            s3_path=files['chat'],
            bucket=S3_BUCKET,
            processed_folder=S3_PROCESSED_DATA_FOLDER,
        )

        return transformed_files


    source_files = discover_source_files()
    clean_data = clean_data(files=source_files)
    transform_data = transform_data(files=clean_data)
etl_pipeline()