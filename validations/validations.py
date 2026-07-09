import pandas as pd
import pandera as pa
import pandera.errors


def prod_table_schema() -> pa.DataFrameSchema:
    """Prod table validation schema"""
    gte_zero_check = pa.Check(lambda x: x >= 0, error="Value must be greater than or 0")
    schema = pa.DataFrameSchema({
        'user' : pa.Column(str, nullable=False),
        'chats_count': pa.Column(int, checks=gte_zero_check, nullable=False),
        'calls_count': pa.Column(int, checks=gte_zero_check, nullable=False),
        'emails_count': pa.Column(int, checks=gte_zero_check, nullable=False),
        'todo_counts': pa.Column(int, checks=gte_zero_check, nullable=False),
        'total': pa.Column(int, checks=gte_zero_check, nullable=False),
        'qs': pa.Column(
            float,
            checks=[
                gte_zero_check,
                pa.Check(lambda x: x <= 100, error="QS Score can't be above 100")
            ], nullable=False),
    })
    return schema


def todos_schema() -> pa.DataFrameSchema:
    """Todos table validation schema"""
    schema = pa.DataFrameSchema({
        'user': pa.Column(str, nullable=False),
        'emails_count': pa.Column(
            int,
            checks=pa.Check(
                lambda x: x >= 0, error="Emails count must be greater than or equal to zero"),
            nullable=False
        ),

        'todo_counts': pa.Column(
            int,
            checks=pa.Check(
                lambda x: x >= 0, error="ToDo's count must be greater than or equal to zero"),
            nullable=False
        ),
    })

    return schema


def phone_schema():
    """Phone table validation schema"""
    schema = pa.DataFrameSchema({
        'user': pa.Column(str, nullable=False),
        'calls_count': pa.Column(
            int,
            checks=pa.Check(
                lambda x: x >= 0, error="Calls counts must be greater than or equal to zero"),
            nullable=False
        ),
    })

    return schema

def chat_schema() -> pa.DataFrameSchema:
    """Chat table validation schema"""
    schema = pa.DataFrameSchema({
        'user': pa.Column(str, nullable=False),
        'chats_count':pa.Column(
            int,
            checks=pa.Check(
                lambda x: x >= 0, error="Calls counts must be greater than or equal to zero"),
            nullable=False
        ),
    })

    return schema


def qs_schema():
    """QS table validation schema"""
    checks = pa.Check(lambda x: x >= 0, error="QS Score must be greater than or equal to zero")
    schema = pa.DataFrameSchema({
        'user': pa.Column(str, nullable=False),
        'total_tickets': pa.Column(int,checks=checks, nullable=False),
        'passing_tickets': pa.Column(int,checks=checks, nullable=False),
        'qs': pa.Column(float, checks=pa.Check(lambda x: (x >= 0) & (x <= 100)), nullable=False),
    })

    return schema

def get_schema(df_type: str) -> pa.DataFrameSchema:
    """Get schema for df_type"""
    schema_mapper = {
        'chat': chat_schema,
        'phone': phone_schema,
        'quality': qs_schema,
        'emails_todo': todos_schema,
        'prod_table': prod_table_schema,
    }

    schema_func = schema_mapper.get(df_type)

    if schema_func is None:
        raise ValueError(f'Unknown DF type Error: {df_type}')

    return schema_func()


def validate_df(df: pd.DataFrame, df_type: str) -> pd.DataFrame:
    """Validate a dataframe"""
    try:
        schema = get_schema(df_type)
        validated_df = schema.validate(df)
        print(f"Df type {df_type} validated successfully")
        return validated_df

    except pandera.errors.SchemaErrors as e:
        raise ValueError(f'Validation Error: {e}')


def validate_dfs_dict(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Validate multiple dataframes"""
    validated_dfs = dict()

    for df_type, df in dfs.items():
        valid_df = validate_df(df, df_type)
        validated_dfs[df_type] = valid_df

    return validated_dfs




