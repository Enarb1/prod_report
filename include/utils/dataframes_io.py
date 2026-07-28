import pandas as pd
from pathlib import PurePosixPath

from include.config.logger import setup_logger
from include.etl.load.load_to_s3 import load_to_s3
from include.validations.validations import validate_df_output

logging = setup_logger(__name__)

READERS = {
    "csv": pd.read_csv,
    "parquet": pd.read_parquet,
    "json": pd.read_json,
    "xlsx": pd.read_excel,
}

def read_dataframe(s3_path: str, storage_options: dict, **kwargs) -> pd.DataFrame:
    """
    Reads dataframe from S3 path. Mapping the reader type, depending on the file type.
    Returns a pandas dataframe on success and raises an exception on failure.
    """
    file_type = PurePosixPath(s3_path.casefold()).suffix.lstrip(".")

    logging.info(f"Reading {file_type} from {s3_path}")

    reader = READERS.get(file_type)

    if file_type is None:
        raise ValueError(f"File type {file_type} is not supported")

    try:
        df = reader(s3_path, storage_options=storage_options, **kwargs)
        logging.info(f"Successfully read {file_type} from {s3_path}")
    except Exception as e:
        logging.error(f"Can not read from {s3_path}. Error: {e}")
        raise

    return df


def safe_df_to_s3(
        df: pd.DataFrame,
        func_name: str,
        s3_bucket: str,
        destination_folder: str,
        storage_options: dict,
        file_name: str | None = None,
) -> str:
    """
    Validate a dataframe as output, build its destination S3 path, log it, persist it
    as parquet, and return the path. Used by any pipeline step that needs to write a
    dataframe to a specific S3 folder (cleaned data, todo data, or elsewhere).
    """
    validated_df = validate_df_output(df, func_name)
    file_name = file_name or func_name
    s3_cleaned_path = f"s3://{s3_bucket}/{destination_folder}{file_name}.parquet"
    logging.info(f"Saving cleaned dataframe to {s3_cleaned_path}")
    load_to_s3(df=validated_df, s3_path=s3_cleaned_path, storage_options=storage_options)

    return s3_cleaned_path