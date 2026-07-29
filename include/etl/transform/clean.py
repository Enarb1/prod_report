from pathlib import PurePosixPath

import pandas as pd

from datetime import date, timedelta

from include.config.logger import setup_logger
from include.utils.s3_utils import get_s3_hook_and_storage_options
from include.utils.dataframes_io import read_dataframe, safe_df_to_s3
from include.validations.validations import validate_df_input

logging = setup_logger(__name__)

def col_headers_to_snake_case(df: pd.DataFrame) -> pd.DataFrame:
    """Turn headers to snake_case. Returns dataframe with the new column names."""
    df = df.copy()

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", regex=True)
        .str.replace(r"([a-z0-9])([A-Z])", r"\1_\2", regex=True)
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    logging.info(f"Changed column headers to snake_case! New column names: \n{df.columns}")

    return df


def _read_and_prepare(s3_path: str, storage_options: dict, func_name: str, **read_kwargs) -> pd.DataFrame:
    """
    Shared logic for every clean_* functions: read raw file, validate its input and normalize column headers
     to snake_case. Any extra kwargs(sep, encoding, skiprows...) are passed directly to read_dataframe.
    """
    df = read_dataframe(s3_path, storage_options=storage_options, **read_kwargs)
    df = validate_df_input(df, func_name)
    df = col_headers_to_snake_case(df)

    return df


def _strip_string_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Cast the given columns to pandas 'string' dtype and strip whitespace."""
    df = df.copy()

    for col in columns:
        df[col] = df[col].astype('string').str.strip()
    return df


def clean_chat_scores(aws_conn_id: str, s3_path: str, s3_bucket: str, cleaned_data_folder: str) -> str:
    """
    Cleans the data from the chat exports. Receives a s3 path, reads the dataframe from it, validates input,
    renames headers to snake_case, keeps only the useful columns ('record_id', 'employee_name'),
    drops rows with NaN values in those columns, casts 'record_id' to int, renames 'employee_name' to
    'user' and strips it, validates the output dataframe, and loads the cleaned dataframe to the S3
    cleaned folder. Returns the new S3 path.
    """
    _ , storage_options = get_s3_hook_and_storage_options(aws_conn_id)
    useful_columns = ['record_id', 'employee_name']
    func_name = clean_chat_scores.__name__

    df = _read_and_prepare(s3_path=s3_path, storage_options=storage_options, func_name=func_name)
    df = df[useful_columns].copy()
    df.dropna(subset=useful_columns, inplace=True)
    df['record_id'] = df['record_id'].astype(int)
    df = df.rename(columns={'employee_name': 'user'})
    df = _strip_string_columns(df, ['user'])

    return safe_df_to_s3(
        df=df,
        func_name=func_name,
        s3_bucket=s3_bucket,
        destination_folder=cleaned_data_folder,
        storage_options=storage_options
    )


def clean_phone_data(aws_conn_id: str, s3_path: str, s3_bucket: str, cleaned_data_folder: str) -> str:
    """
    Cleans the data from the phone system export. Receives a s3 path, reads the semicolon-separated
    dataframe (skipping the report's 17-line header, decoded as utf-8-sig), validates input, renames
    headers to snake_case, keeps only the useful columns ('user', 'accepted_calls_number'), drops rows
    with NaN values in those columns, strips 'user', renames 'accepted_calls_number' to 'total_calls'
    and casts it to int, validates the output dataframe, and loads the cleaned dataframe to the S3
    cleaned folder. Returns the new S3 path.
    """
    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)
    func_name = clean_phone_data.__name__
    useful_columns = ['user', 'accepted_calls_number']

    df = _read_and_prepare(
        s3_path=s3_path,
        storage_options=storage_options,
        func_name=func_name,
        sep=";",
        skiprows=17,
        encoding="utf-8-sig"
    )

    df = df[useful_columns].copy()
    df.dropna(subset=useful_columns, inplace=True)
    df = _strip_string_columns(df, ['user'])
    df = df[df['user'] != 'Summe']
    df = df.rename(columns={'accepted_calls_number': 'total_calls'})
    df['total_calls'] = df['total_calls'].astype(int)

    return safe_df_to_s3(
        df=df,
        func_name=func_name,
        s3_bucket=s3_bucket,
        destination_folder=cleaned_data_folder,
        storage_options=storage_options
    )


def clean_qs_data(aws_conn_id: str, s3_path: str, s3_bucket: str, cleaned_data_folder: str) -> str:
    """
    Cleans the data from the quality score (QS) export. Receives a s3 path, reads the Excel
    dataframe, validates input, renames headers to snake_case, then renames the source-language
    columns ('ticketnummer', 'ampelstatus_ticket_qs', 'ersteller') to ('ticket_id', 'quality_pass',
    'user'), keeps only those useful columns, drops rows with NaN values in them, strips 'ticket_id'
    and 'user', lowercases and strips 'quality_pass', validates the output dataframe, and loads the
    cleaned dataframe to the S3 cleaned folder. Returns the new S3 path
    """
    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)
    useful_columns = ['ticket_id', 'quality_pass', 'user']
    func_name = clean_qs_data.__name__

    df = _read_and_prepare(s3_path=s3_path, storage_options=storage_options, func_name=func_name, engine='openpyxl')
    df = df.rename(columns={
        'ticketnummer': 'ticket_id',
        'ampelstatus_ticket_qs': 'quality_pass',
        'ersteller': 'user',
        }
    )

    df = df[useful_columns].copy()
    df.dropna(subset=useful_columns, inplace=True)
    df = _strip_string_columns(df, ['ticket_id', 'user'])
    df['quality_pass'] = df['quality_pass'].astype('string').str.lower().str.strip()

    return safe_df_to_s3(
        df=df,
        func_name=func_name,
        s3_bucket=s3_bucket,
        destination_folder=cleaned_data_folder,
        storage_options=storage_options
    )


def clean_names_data(aws_conn_id: str, s3_path: str, s3_bucket: str, cleaned_data_folder: str) -> str:
    """
    Cleans the employee names reference data. Receives a s3 path, reads the dataframe from it,
    validates input, renames headers to snake_case, strips whitespace from every column except
    'id', coerces 'id' to numeric (invalid values become NaN) and casts it to int, validates the
    output dataframe, and loads the cleaned dataframe to the S3 cleaned folder. Returns the new
    S3 path.
    """
    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)
    func_name = clean_names_data.__name__

    df = _read_and_prepare(s3_path=s3_path, storage_options=storage_options, func_name=func_name)
    text_columns = [col for col in df.columns if col != 'id']
    df = _strip_string_columns(df, text_columns)
    df['id'] = pd.to_numeric(df['id'], errors='coerce').astype(int)

    return safe_df_to_s3(
        df=df,
        func_name=func_name,
        s3_bucket=s3_bucket,
        destination_folder=cleaned_data_folder,
        storage_options=storage_options
    )

def get_previous_cw_sheet_name(ref_date: date):
    """
    Builds the calendar-week sheet name (e.g. 'CW30') for the week before `ref_date`, matching
    the sheet-naming convention used in the todo workbooks.
    """
    previous_week_date = ref_date - timedelta(days=7)
    previous_week_number = previous_week_date.isocalendar().week

    return f"CW{previous_week_number}"


def clean_todo_data(aws_conn_id: str, todo_files: list, s3_bucket: str, cleaned_data_folder: str) -> list:
    """
    Cleans a list of todo workbooks. For each s3 path, reads the sheet corresponding to the
    previous calendar week, validates input, renames headers to snake_case, strips whitespace
    from every column, validates the output dataframe, and loads the cleaned dataframe to the
    S3 cleaned folder using the source file's name (instead of the function name, since multiple
    files are processed). Returns the list of new S3 paths, one per input file.
    """
    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)
    func_name = clean_todo_data.__name__
    sheet_name = get_previous_cw_sheet_name(ref_date=date.today())

    todo_cleaned_paths = []

    for s3_path in todo_files:
        df = _read_and_prepare(
            s3_path=s3_path,
            storage_options=storage_options,
            func_name=func_name,
            sheet_name=sheet_name
        )
        df = _strip_string_columns(df, list(df.columns))

        file_name = PurePosixPath(s3_path).stem

        s3_cleaned_path = safe_df_to_s3(
            df=df,
            func_name=func_name,
            s3_bucket=s3_bucket,
            destination_folder=cleaned_data_folder,
            storage_options=storage_options,
            file_name=file_name
        )

        todo_cleaned_paths.append(s3_cleaned_path)

    return todo_cleaned_paths