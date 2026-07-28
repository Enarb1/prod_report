import pandera.pandas as pa
import pandas as pd
from pandera.errors import SchemaErrors

from include.validations.input_schemas import (CHAT_DATA_INPUT_SCHEMA, PHONE_DATA_INPUT_SCHEMA,
                                               TICKET_QS_INPUT_SCHEMA, NAMES_DATA_INPUT_SCHEMA, TODO_INPUT_SCHEMA)
from include.validations.output_schema import (CHAT_DATA_OUTPUT_SCHEMA, PHONE_DATA_OUTPUT_SCHEMA,
                                               TICKET_QS_OUTPUT_SCHEMA, NAMES_DATA_OUTPUT_SCHEMA, TODO_OUTPUT_SCHEMA,
                                               CHAT_TRANSFORMED_OUTPUT_SCHEMA)
from include.config.logger import setup_logger

logging = setup_logger(__name__)

INPUT_SCHEMA = {
    'clean_chat_scores': CHAT_DATA_INPUT_SCHEMA,
    'clean_phone_data': PHONE_DATA_INPUT_SCHEMA,
    'clean_qs_data': TICKET_QS_INPUT_SCHEMA,
    'clean_names_data': NAMES_DATA_INPUT_SCHEMA,
    'clean_todo_data': TODO_INPUT_SCHEMA
}

OUTPUT_SCHEMA = {
    'clean_chat_scores': CHAT_DATA_OUTPUT_SCHEMA,
    'clean_phone_data': PHONE_DATA_OUTPUT_SCHEMA,
    'clean_qs_data': TICKET_QS_OUTPUT_SCHEMA,
    'clean_names_data': NAMES_DATA_OUTPUT_SCHEMA,
    'clean_todo_data': TODO_OUTPUT_SCHEMA,
    'transform_chat_data': CHAT_TRANSFORMED_OUTPUT_SCHEMA
}


def validate_df_input(df: pd.DataFrame, func_name: str) -> pd.DataFrame:
    logging.info(f"Loading input schema for: {func_name}")
    schema = INPUT_SCHEMA.get(func_name)
    validate_df = validate_schema(df=df, schema=schema, raise_on_error=False)

    return validate_df


def validate_df_output(df: pd.DataFrame, func_name: str) -> pd.DataFrame:
    logging.info(f"Loading output schema for: {func_name}")
    schema = OUTPUT_SCHEMA.get(func_name)
    validate_df = validate_schema(df=df, schema=schema)

    return validate_df


def validate_schema(df: pd.DataFrame, schema: pa.DataFrameSchema, raise_on_error: bool = True) -> pd.DataFrame:

    if schema is None:
        raise KeyError(f"No input schema: \n {df.columns.to_list}")

    try:
        validated_df = schema.validate(df, lazy=True)
        logging.info("Successfully validated dataframe!")
        return validated_df

    except SchemaErrors as se:

        if raise_on_error:
            logging.error(f"Can't validate input schema: {se}")
            raise

        failed_cases = se.failure_cases

        logging.warning(f"Validation on input schema failed: \n {failed_cases.to_string()}")
        return df
