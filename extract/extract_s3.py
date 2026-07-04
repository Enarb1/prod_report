from pathlib import PurePosixPath
from typing import Any

import pandas as pd
import s3fs
import fsspec

from botocore.exceptions import BotoCoreError

from config.config import AWS_BUCKET_NAME, AWS_TEAM_FOLDER_PREFIX
from config.s3_utils import get_s3_client_and_storage_options


def get_folder_contents_s3(bucket_name: str, folder: str) -> tuple[Any, Any]:
    """Get folder contents from S3 bucket"""
    s3_client, storage_options = get_s3_client_and_storage_options()

    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder)
        contents = response.get("Contents", [])
        if not contents:
            raise FileNotFoundError(f"No files found in {bucket_name}/{folder}")

    except BotoCoreError:
        print(f"S3 access error for {bucket_name}")
        raise

    return contents, storage_options

def extract_names_data(bucket_name, folder, file_name: str = 'names.xlsx') -> pd.DataFrame | None:
    """Extract the names.xlsx file from S3 bucket"""
    contents, storage_options = get_folder_contents_s3(bucket_name, folder)

    for obj in contents:
        key = obj['Key']

        if PurePosixPath(key).name.lower() != file_name.lower():
            print(f"Skipping {key}")
            continue

        s3_path = f's3://{bucket_name}/{key}'

        try:
            df = pd.read_excel(s3_path, storage_options=storage_options, engine='openpyxl')
            print(f"Loaded {file_name}:\n{df.head(5)}")
            return df
        except Exception as e:
            print(f"Skipping {s3_path}")
            print(f"{type(e).__name__}: {e}")
    return None

def extract_qs_chat_phone_data(bucket_name: str, folder: str) -> list[pd.DataFrame] | None:
    """Extract the tables with the quality data, chat data and the phone data"""

    contents, storage_options = get_folder_contents_s3(bucket_name, folder)
    print(contents)
    df_mapper = {'qs': 'quality', 'vayu': 'chat', 'statistic': 'phone'}
    mapping = {'chat': None, 'phone': None, 'quality': None}

    for obj in contents:
        key = obj['Key']
        print(key)
        if not key.lower().endswith(('.csv', '.xlsx')):
            continue

        s3_path = f's3://{bucket_name}/{key}'

        try:
            if key.lower().endswith('.csv'):
                if 'statistic' in key.lower():
                    df = pd.read_csv(
                        s3_path,
                        storage_options=storage_options,
                        sep=";",
                        skiprows=17,
                        encoding="utf-8-sig"
                    )
                else:
                    df = pd.read_csv(s3_path, storage_options=storage_options)
            else:
                df = pd.read_excel(s3_path, storage_options=storage_options, engine='openpyxl')
        except Exception as e:
            print(f"Skipping {s3_path}")
            print(f"{type(e).__name__}: {e}")

        for df_name in df_mapper.keys():
            if df_name in key.lower():
                mapping[df_mapper[df_name]] = df
                break

    return [mapping['chat'], mapping['phone'], mapping['quality']]

