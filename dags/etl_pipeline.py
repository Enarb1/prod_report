from airflow.sdk import dag, task
from pendulum import datetime

from include.etl.extract.extract_form_s3 import get_s3_paths, get_todo_s3_paths
from include.config.settings import (AWS_CONN_ID, S3_BUCKET, S3_FILE_PATTERNS, \
                                     S3_REQUIRED_FILE_TYPES, S3_TODO_DATA, S3_CLEANED_EXTRACTED_DATA,
                                     S3_CLEANED_TODO_DATA, S3_DISCOVERY_FOLDERS,
                                     S3_PROCESSED_DATA_FOLDER, SNOWFLAKE_CONN_ID, CLEANSED_LAYER_SCHEMAS,
                                     SNOWFLAKE_CLEANED_STAGE, SNOWFLAKE_FILE_FORMAT, PRESENTATION_LAYER_SCHEMAS,
                                     SNOWFLAKE_PROCESSED_STAGE, SNOWFLAKE_BUSINESS_PROD_REPORT_SCHEMA,
                                     SNOWFLAKE_BUSINESS_STAGE, BUSINESS_LAYER_SCHEMAS)
from include.etl.load.load_to_snowflake import load_to_snowflake
from include.etl.transform.clean import (clean_chat_scores, clean_phone_data, clean_qs_data, clean_names_data,
                                         clean_todo_data)
from include.etl.transform.transform import (transform_chat_data, transform_phone_data, transform_qs_data,
                                             transform_todo_summary)
from include.etl.transform.merge import productivity_table


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

        transformed_files['chat'] = transform_chat_data(
            aws_conn_id=AWS_CONN_ID,
            s3_path=files['chat'],
            bucket=S3_BUCKET,
            processed_folder=S3_PROCESSED_DATA_FOLDER,
            names_df_path=files['names'],
        )

        transformed_files['phone'] = transform_phone_data(
            aws_conn_id=AWS_CONN_ID,
            s3_path=files['phone'],
            bucket=S3_BUCKET,
            processed_folder=S3_PROCESSED_DATA_FOLDER,
            names_df_path=files['names'],
        )

        transformed_files['quality'] = transform_qs_data(
            aws_conn_id=AWS_CONN_ID,
            s3_path=files['quality'],
            bucket=S3_BUCKET,
            processed_folder=S3_PROCESSED_DATA_FOLDER,
        )

        transformed_files['todo_summary'] = transform_todo_summary(
            aws_conn_id=AWS_CONN_ID,
            s3_paths=files['todo_files'],
            bucket=S3_BUCKET,
            processed_folder=S3_PROCESSED_DATA_FOLDER,
            names_df_path=files['names'],
        )


        return transformed_files

    @task
    def merge_data(files: dict) -> dict:
        merged_files = {}

        merged_files['productivity_table'] = productivity_table(
            aws_conn_id=AWS_CONN_ID,
            s3_paths=files,
            bucket=S3_BUCKET,
            processed_folder=S3_PROCESSED_DATA_FOLDER,
        )

        return merged_files

    @task
    def load_data_to_snowflake(cleaned_files: dict, transformed_files, merged_files: dict) -> None:
        load_to_snowflake(
            file_paths=cleaned_files,
            snowflake_conn_id=SNOWFLAKE_CONN_ID,
            schemas=CLEANSED_LAYER_SCHEMAS,
            stage=SNOWFLAKE_CLEANED_STAGE,
            file_format=SNOWFLAKE_FILE_FORMAT
        )

        load_to_snowflake(
            file_paths=transformed_files,
            snowflake_conn_id=SNOWFLAKE_CONN_ID,
            schemas=PRESENTATION_LAYER_SCHEMAS,
            stage=SNOWFLAKE_PROCESSED_STAGE,
            file_format=SNOWFLAKE_FILE_FORMAT
        )

        load_to_snowflake(
            file_paths=merged_files,
            snowflake_conn_id=SNOWFLAKE_CONN_ID,
            schemas=BUSINESS_LAYER_SCHEMAS,
            stage=SNOWFLAKE_BUSINESS_STAGE,
            file_format=SNOWFLAKE_FILE_FORMAT
        )



    source_files = discover_source_files()
    clean_files = clean_data(files=source_files)
    transform_files = transform_data(files=clean_files)
    merged_files = merge_data(files=transform_files)
    load_data_to_snowflake(cleaned_files=clean_files, transformed_files=transform_files, merged_files=merged_files)

etl_pipeline()