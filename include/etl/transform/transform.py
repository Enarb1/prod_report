from pathlib import PurePosixPath

import pandas as pd

from include.utils.s3_utils import get_s3_hook_and_storage_options
from include.utils.dataframes_io import read_dataframe, safe_df_to_s3
from include.config.logger import setup_logger
from include.validations.validations import validate_df_input


logging = setup_logger(__name__)


def _get_df_and_storage_options(aws_conn_id: str, s3_path: str) -> tuple[pd.DataFrame, dict]:
    """
    Shared logic for reading a dataframe and getting the storage options.
    Returning a tuple of (dataframe, storage_options)
    """
    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)
    df = read_dataframe(s3_path, storage_options=storage_options)
    df = df.copy()

    return df, storage_options

def _name_mapper(
        df: pd.DataFrame,
        names_df_path: str,
        storage_options: dict,
        map_to_col: str,
        col_to_map: str
) -> pd.DataFrame:
    """
    Maps the usernames in the different dataframes to their respective names using the names dataframe.
    map_to_col: this is the column in names_df, which shows the username for the system (e.g. chat, phone...)
    col_to_map: this is the column in the passed df , which has to be mapped with the corresponding name in
    the names_df. Returns dataframe with mapped usernames
    """
    logging.info(f"Mapping {map_to_col} to {col_to_map}")

    names_df = read_dataframe(names_df_path, storage_options=storage_options)
    df = df.copy()

    if names_df[map_to_col].duplicated().any():
        duplicates = (
            names_df.loc[names_df[map_to_col].duplicated(keep=False),map_to_col,].dropna().unique().tolist()
        )
        raise ValueError(f"Duplicated values found. Duplicated values: {duplicates}")

    name_map =   names_df.set_index(map_to_col)['name']
    mapped_names = df[col_to_map].map(name_map)

    if mapped_names.isna().any():
        missing_users = df.loc[mapped_names.isna(), col_to_map].dropna().unique().tolist()
        raise ValueError(f"Missing users: {missing_users}")

    df[col_to_map] = mapped_names
    logging.info(f"Successfully mapped {map_to_col} to {col_to_map}")
    return df


def transform_chat_data(aws_conn_id, s3_path: str, bucket: str, processed_folder: str, names_df_path: str) -> str:
    """
    Transform the cleand chat dataframe, by grouping it by users and getting the total number of chats for each user.
    Mapping the chat usernames to the name of the agent in names_df. Loading the new dataframe to S3 in the processed
    folder. Returning the new path in S3.
    """
    df, storage_options = _get_df_and_storage_options(aws_conn_id, s3_path)

    df = df.groupby(['user'], as_index=False).agg(total_chats=('record_id', 'count'))
    logging.info("Successfully grouped chat data by user")
    df['total_chats'] = df['total_chats'].astype(int)
    df = _name_mapper(
        df=df,
        names_df_path=names_df_path,
        storage_options=storage_options,
        map_to_col='chat',
        col_to_map='user'
    )

    logging.info("Successfully transformed chat data.")

    return safe_df_to_s3(
        df=df,
        func_name=transform_chat_data.__name__,
        s3_bucket=bucket,
        destination_folder=processed_folder,
        storage_options=storage_options
    )


def transform_phone_data(aws_conn_id, s3_path: str, bucket: str, processed_folder: str, names_df_path: str) -> str:
    """
    Transform the phone data. The data already comes grouped by agent and total phone calls. Mapping 'user to
    the corresponding name in names_df. Loading the updated dataframe to S3 as a parquet file in the processed folder.
    Returning the new path in S3.
    """

    df, storage_options = _get_df_and_storage_options(aws_conn_id, s3_path)

    df = _name_mapper(
        df=df,
        names_df_path=names_df_path,
        storage_options=storage_options,
        map_to_col='phone',
        col_to_map='user'
    )
    df['total_calls'] = df['total_calls'].astype(int)
    logging.info("Successfully transformed phone data.")
    return safe_df_to_s3(
        df=df,
        func_name=transform_phone_data.__name__,
        s3_bucket=bucket,
        destination_folder=processed_folder,
        storage_options=storage_options
    )


def transform_qs_data(aws_conn_id, s3_path: str, bucket: str, processed_folder: str) -> str:
    """
    Transforming the quality dataframe. Grouping by user and calculating the quality score in percent.
    Names are not mapped, as they are already correct. Loading the new dataframe to S3 as a parquet file in the
    processed folder. Returning the new path in S3.
    """
    df, storage_options = _get_df_and_storage_options(aws_conn_id, s3_path)

    df = df.groupby('user', as_index=False).agg(
        qs_score=('quality_pass', lambda status: status.eq('in ordnung').mean() * 100),
    )
    df['qs_score'] = df['qs_score'].astype(float).round(2)
    logging.info("Successfully transformed qs data.")

    return safe_df_to_s3(
        df=df,
        func_name=transform_qs_data.__name__,
        s3_bucket=bucket,
        destination_folder=processed_folder,
        storage_options=storage_options
    )


def _get_todo_user_data(s3_paths: list, storage_options) -> list[dict]:
    """
    Reading each dataframe from the list with S3 paths. Creating a dictionary with each row from for the new
    summary dataframe. Each row contains 'user_file', 'emails_count' and 'todos_count'. The .xlsx extension is added
    to the file_name, because this is how the todo_file is listed in the names_df, which we will use to map the
    usernames. Returns a list of dictionaries with each row containing 'user_file', 'emails_count' and 'todos_count'
    """
    todo_summary = []

    for s3_path in s3_paths:
        df = read_dataframe(s3_path, storage_options=storage_options)
        df = df.copy()

        file_name = PurePosixPath(s3_path).stem

        user_data = {
            'user_file': f'{file_name}.xlsx',
            'emails_count': df['emails'].count(),
            'todos_count': df['to_do'].count(),
        }
        logging.info(f"Created row with user data: {user_data}")
        todo_summary.append(user_data)

    logging.info("Successfully created user data rows")
    return todo_summary


def transform_todo_summary(aws_conn_id, s3_paths: list, bucket: str, processed_folder: str, names_df_path) -> str:
    """
    Creating a summary table for all agents, containing: User, Total Emails Count, Total Todos Count.
    Validating the new dataframe on input and output. Mapping the usernames to the names_df. Changing column name from
    'user_file' to 'user' . Saving the new dataframe in S3 in the processed folder. Returning the new path in S3.
    """
    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)
    func_name = transform_todo_summary.__name__

    summary_rows = _get_todo_user_data(s3_paths, storage_options)

    todo_summary_df = pd.DataFrame(summary_rows)
    logging.info("Successfully created the Todo Summary dataframe")

    todo_summary_df = validate_df_input(todo_summary_df, func_name)
    logging.info("Successfully validated data on input for the Todo Summary dataframe")

    todo_summary_df = _name_mapper(
        df=todo_summary_df,
        names_df_path=names_df_path,
        storage_options=storage_options,
        map_to_col='todo_file',
        col_to_map='user_file'
    )

    todo_summary_df = todo_summary_df.rename(columns={
        'user_file': 'user',
    })

    todo_summary_df[['emails_count', 'todos_count']] = todo_summary_df[['emails_count', 'todos_count']].astype(int)

    return safe_df_to_s3(
        df=todo_summary_df,
        func_name=func_name,
        s3_bucket=bucket,
        destination_folder=processed_folder,
        storage_options=storage_options
    )