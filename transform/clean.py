import pandas as pd
import logging

def col_headers_to_snake_case(df: pd.DataFrame) -> pd.DataFrame:
    """Turn headers to snake_case"""
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

    logging.info('Changed column headers to snake_case!')

    return df


def get_useful_cols(df: pd.DataFrame, df_type) -> pd.DataFrame:
    """Get only the useful columns"""

    use_cols = {
        'chat': ['record_id', 'employee_name'],
        'phone': ['user','accepted_calls_number'],
        'quality': ['ticketnummer', 'ampelstatus_ticket_qs', 'ersteller']
    }

    df = df.copy()
    cols = use_cols[df_type]
    df = df[cols]

    logging.info(f'Kept columns: {', '.join(cols)}')

    return df


def drop_nan_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop nan rows"""
    df = df.copy()
    initial_rows = len(df)
    df = df.dropna()
    dropped_rows = initial_rows - len(df)

    logging.info(f'Dropped {dropped_rows} rows!')

    return df


def strip_str_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Strip string columns"""
    df = df.copy()
    string_cols = df.select_dtypes(["object", "string"]).columns
    df[string_cols] = df[string_cols].apply(lambda x: x.str.strip())

    logging.info(f'Stripped {len(string_cols)} columns')
    return df


def drop_duplicate_cols(df: pd.DataFrame, df_type) -> pd.DataFrame:
    """Drops duplicate rows"""
    cols_to_check = {
        'chat': ['record_id'],
        'phone': ['user'],
        'quality': ['ticketnummer'],
    }
    df = df.copy()
    df = df.drop_duplicates(subset=cols_to_check[df_type],keep='first')
    logging.info(f'Dropped {len(cols_to_check[df_type])} duplicate columns')

    return df


def change_user_col_name(df: pd.DataFrame, df_type) -> pd.DataFrame:
    """Changing the different  user columns to 'user'"""
    mapper = {
        'chat': 'employee_name',
        'quality': 'ersteller',
    }

    df = df.copy()

    if df_type in mapper.keys():
        df = df.rename(
            columns={
                mapper[df_type]: 'user',
            }
        )

    logging.info('Renamed user column')

    return df


def get_names_mapper(names_df: pd.DataFrame, df_type) -> pd.DataFrame:
    """Gets the mapper for the usernames"""
    values = {
        'chat':['chat', 'name'],
        'phone':['phone', 'name'],
    }

    logging.info('Received name mappers for usernames.')

    return names_df.set_index(values[df_type][0])[values[df_type][1]]

def map_names(names_df, df, df_type) -> pd.DataFrame:
    """Mapping the chat and phone users to the names from the names table"""
    df = df.copy()
    if df_type != 'quality':
        mapper = get_names_mapper(names_df, df_type)
        df['user'] = df['user'].map(mapper)
    logging.info(f"Mapped Names of {df_type} dataframe!")

    return df


def clean_dfs(dfs_dict: dict, names_df: pd.DataFrame) -> dict:
    """Cleaning dataframes"""
    logging.info('Cleaning dataframes...')
    dataframes = {}

    names_df = col_headers_to_snake_case(names_df)
    names_df = strip_str_cols(names_df)

    if not dfs_dict:
        raise Exception('No dataframes found!')

    for df_type, df in dfs_dict.items():
        df = col_headers_to_snake_case(df)
        df = get_useful_cols(df, df_type)
        df = drop_nan_rows(df)
        df = strip_str_cols(df)
        df = drop_duplicate_cols(df, df_type)
        df = change_user_col_name(df, df_type)


        if df_type == 'phone':
            df = df[df['user'] != 'Summe']

            df['accepted_calls_number'] = pd.to_numeric(
                df["accepted_calls_number"],
                errors="coerce",
            ).astype("Int64")
            df = df.rename(columns={'accepted_calls_number': 'calls_count'})
        df = map_names(names_df, df, df_type)
        dataframes[df_type] = df

    logging.info(f'Cleaned {len(dataframes)} dataframes')

    return dataframes

def clean_todo_dfs(todo_dfs: dict) -> dict:
    """Cleaning todo dataframes"""
    logging.info('Cleaning ToDo dataframes...')
    cleaned_todo_dfs = {}

    if not todo_dfs:
        raise Exception('No todo dataframes found!')

    for key, df in todo_dfs.items():
        df = col_headers_to_snake_case(df)
        df = strip_str_cols(df)
        cleaned_todo_dfs[key] = df

    logging.info(f'Cleaned {len(cleaned_todo_dfs)} dataframes')
    return cleaned_todo_dfs
