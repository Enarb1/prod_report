from include.utils.s3_utils import get_s3_hook_and_storage_options
from include.utils.dataframes_io import read_dataframe, safe_df_to_s3


def transform_chat_data(aws_conn_id, s3_path: str, bucket: str, processed_folder: str):
    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)

    df = read_dataframe(s3_path, storage_options=storage_options)
    # TODO map user to name from names df
    df = df.copy()
    df = df.groupby(['user'], as_index=False).agg(total_chats=('record_id', 'count'))
    df['total_chats'] = df['total_chats'].astype(int)
    return safe_df_to_s3(
        df=df,
        func_name=transform_chat_data.__name__,
        s3_bucket=bucket,
        destination_folder=processed_folder,
        storage_options=storage_options
    )
