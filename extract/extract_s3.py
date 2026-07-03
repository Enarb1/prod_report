from pathlib import PurePosixPath

import pandas as pd
import s3fs
import fsspec

from botocore.exceptions import BotoCoreError

from config.config import AWS_BUCKET_NAME, AWS_TEAM_FOLDER_PREFIX
from config.s3_utils import get_s3_client_and_storage_options


def get_folder_contents_s3(bucket_name: str, folder: str):
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
    contents, storage_options = get_folder_contents_s3(bucket_name, folder)

    for obj in contents:
        key = obj['Key']

        if PurePosixPath(key).name.lower() != file_name.lower():
            print(f"Skipping {key}")
            continue

        s3_path = f's3://{bucket_name}/{key}'

        try:
            df = pd.read_excel(s3_path, storage_options=storage_options, engine='openpyxl')
            print(f"Loaded: {df}")
            return df
        except Exception as e:
            print(f"Skipping {s3_path}")
            print(f"{type(e).__name__}: {e}")
    return None
