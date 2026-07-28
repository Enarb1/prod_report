import pandas as pd

from include.config.logger import setup_logger

logging = setup_logger(__name__)

def load_to_s3(df: pd.DataFrame, s3_path: str, storage_options: dict, **kwargs) -> None:
    """
    Load dataframe as parquet into S3.
    """
    try:
        df.to_parquet(s3_path, storage_options=storage_options, **kwargs)
        logging.info(f"Successfully uploaded dataframe to {s3_path} as parquet")
    except Exception as e:
        logging.error(f"Failed to upload dataframe to {s3_path} as parquet: {e}")
        raise e