import datetime
import logging

import pandas as pd
from io import StringIO
from datetime import datetime, UTC

from config.s3_utils import get_s3_client_and_storage_options


def upload_df_csv_to_s3(df: pd.DataFrame, bucket: str ,folder: str, file_prefix: str) -> None:
    """Upload CSV file to S3"""
    timestamp = datetime.now(UTC).strftime('%Y%m%d-%H%M%S')
    csv_buffer = StringIO()
    key = f'{folder}{file_prefix}_{timestamp}.csv'
    logging.info(f'Created key: {key}')

    try:
        df.to_csv(csv_buffer, index=False)
        logging.info('Uploaded CSV to buffer')
    except Exception as e:
        logging.error(f'Error uploading CSV to buffer: {e}')
        raise

    s3_client, _ = get_s3_client_and_storage_options()

    try:
        s3_client.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())
        logging.info(f'Uploaded CSV to s3: {key}')
    except Exception as e:
        logging.error(f'Error uploading CSV to s3: {e}')
        raise


def upload_dfs_to_s3(dfs: dict[str, pd.DataFrame], bucket: str ,folder: str, cw: int) -> None:
    """Upload multiple dataframes to S3"""
    logging.info(f'Uploading {len(dfs)} dataframes to s3')
    for df_type, df in dfs.items():
        try:
            upload_df_csv_to_s3(df=df, bucket=bucket, folder=folder, file_prefix=f'cw{cw}_{df_type}')
        except Exception as e:
            logging.error(f'Error uploading {df_type} to s3: {e}')
            raise

    logging.info(f'Uploaded {len(dfs)} dataframes to s3')



