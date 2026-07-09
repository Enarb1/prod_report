import datetime

import pandas as pd
from io import StringIO
from datetime import datetime, UTC

from config.s3_utils import get_s3_client_and_storage_options


def upload_df_csv_to_s3(df: pd.DataFrame, bucket: str ,folder: str, file_prefix: str) -> None:
    """Upload CSV file to S3"""
    timestamp = datetime.now(UTC).strftime('%Y%m%d-%H%M%S')
    csv_buffer = StringIO()
    key = f'{folder}{file_prefix}_{timestamp}.csv'
    print(f'Created key: {key}')

    df.to_csv(csv_buffer, index=False)
    print('Uploaded CSV to buffer')

    s3_client, _ = get_s3_client_and_storage_options()
    print("Got s3 client")
    s3_client.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())
    print(f'Uploaded CSV to s3: {key}')


def upload_dfs_to_s3(dfs: dict[str, pd.DataFrame], bucket: str ,folder: str, cw: int) -> None:
    """Upload multiple dataframes to S3"""
    for df_type, df in dfs.items():
        upload_df_csv_to_s3(df=df, bucket=bucket, folder=folder, file_prefix=f'cw{cw}_{df_type}')



