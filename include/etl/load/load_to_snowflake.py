from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from include.config.logger import setup_logger

logging = setup_logger(__name__)


def _create_sql(target: str, stage_path: str, db: str, schema: str, file_format: str) -> tuple[str, str]:
    """
    Creates the SQL command for TRUNCATE and COPY INTO. Returns a tuple of both commands.
    """
    truncate_sql = f"TRUNCATE TABLE IF EXISTS {target};"

    copy_into_sql = f"""
                    COPY INTO {target}
                    FROM {stage_path}
                    FILE_FORMAT = (FORMAT_NAME  = {db}.{schema}.{file_format})
                    MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
                    ON_ERROR = 'CONTINUE'
                    FORCE = TRUE
                    PURGE = FALSE;
                """

    return truncate_sql, copy_into_sql

def _load_data_in_sf(
        sf_hook: SnowflakeHook,
        truncate_sql: str,
        copy_into_sql: str,
        target: str,
        stage_path: str,
        file_name: str
) -> None:
    """
    Loads data to Snowflake.Receives, SnowflakeHook, TRUNCATE SQL command, COPY INTO SQL command, target,
    stage path and file name. Loads data on success and raises exception on failure.
    """

    logging.info("Loading data to Snowflake...")

    try:
        sf_hook.run(truncate_sql)
        result = sf_hook.run(copy_into_sql, handler=lambda cur: cur.fetchone())
        logging.info(f"COPY INTO result for {target}: {result}")
        logging.info(f"Successfully loaded {file_name} to {target} in Snowflake.")
    except Exception as e:
        logging.error(f"Failed to load {file_name} into {target} from {stage_path}. Error: {e}")
        raise

    logging.info("Successfully loaded all files into Snowflake.")

def _get_targets_and_sql(s3_path: str, schemas: dict, stage: str, file_name: str, file_format: str):
    """
    Getting database, schema, table, object name(file), target and stage path.
    Passing data to the _create_sql function. Returning TRUNCATE SQL, COPY INTO SQL, target and stage path
    on success.
    """
    db, schema, table = schemas[file_name]
    object_name = s3_path.rsplit("/", 1)[-1]
    target = f"{db}.{schema}.{table}"
    stage_path = f"@{db}.{schema}.{stage}/{object_name}"

    logging.info(
        f"Created target, storage path and extracted object name.\n"
        f"Target: {target}\n"
        f"Storage path: {stage_path}\n"
        f"Object name: {object_name}"
    )

    truncate_sql, copy_into_sql = _create_sql(target=target, stage_path=stage_path, db=db, schema=schema,
                                              file_format=file_format)

    return truncate_sql, copy_into_sql, target, stage_path


def load_to_snowflake(file_paths: dict, snowflake_conn_id: str, schemas: dict, stage: str, file_format: str) -> None:
    """
    Loading to Snowflake logic. Getting Snowflake hook, iterating through all file paths.
    Calling _get_targets_and_sql function and then _load_data_in_sf function.
    """
    sf_hook = SnowflakeHook(snowflake_conn_id=snowflake_conn_id)

    logging.info("Getting file name and s3 path...")
    for file_name, s3_path in file_paths.items():
        if file_name not in schemas:
            logging.warning(f"No configured target schema for {file_name}")
            continue


        truncate_sql, copy_into_sql, target, stage_path = _get_targets_and_sql(s3_path=s3_path, schemas=schemas, stage=stage, file_name=file_name, file_format=file_format)
        _load_data_in_sf(sf_hook=sf_hook, truncate_sql=truncate_sql, copy_into_sql=copy_into_sql, target=target, stage_path=stage_path, file_name=file_name)
