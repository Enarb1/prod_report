import pandas as pd

from include.utils.dataframes_io import read_dataframe, safe_df_to_s3
from include.config.logger import setup_logger
from include.utils.s3_utils import get_s3_hook_and_storage_options

logging = setup_logger(__name__)

def productivity_table(aws_conn_id: str, s3_paths: dict, bucket: str, processed_folder: str) -> str:
    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)
    paths = s3_paths.copy()

    merged_df = read_dataframe(s3_path=s3_paths['todo_summary'],storage_options=storage_options)
    paths.pop('todo_summary')

    for file_name, s3_path in paths.items():
        df = read_dataframe(s3_path=s3_path, storage_options=storage_options)
        merged_df = merged_df.merge(df, how='left', on='user', validate='one_to_one')

    total_counts = ['emails_count', 'todos_count', 'total_chats', 'total_calls']
    merged_df[total_counts] = merged_df[total_counts].fillna(0)
    merged_df['total'] = merged_df[total_counts].sum(axis=1)
    merged_df = merged_df[['user', 'emails_count', 'todos_count', 'total_chats', 'total_calls', 'total', 'qs_score']]

    merged_df.loc[len(merged_df)] = {
        'user': 'Total',
        'emails_count': merged_df['emails_count'].sum(),
        'todos_count': merged_df['todos_count'].sum(),
        'total_chats': merged_df['total_chats'].sum(),
        'total_calls': merged_df['total_calls'].sum(),
        'total': merged_df['total'].sum(),
        'qs_score': round(merged_df['qs_score'].mean(), 2),
    }

    count_columns = total_counts + ['total']
    merged_df[count_columns] = merged_df[count_columns].astype(int)
    merged_df['qs_score'] = pd.to_numeric(merged_df['qs_score'], errors='coerce')

    return safe_df_to_s3(
        df=merged_df,
        func_name=productivity_table.__name__,
        s3_bucket=bucket,
        destination_folder=processed_folder,
        storage_options=storage_options
    )
