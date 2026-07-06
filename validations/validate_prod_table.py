import pandas as pd
import pandera as pa

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

def validate_prod_table(data: pd.DataFrame,) -> pd.DataFrame:
    validated_df = schema.validate(data)
    return validated_df
