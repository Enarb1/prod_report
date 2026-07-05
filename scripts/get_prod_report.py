from config.config import AWS_BUCKET_NAME, AWS_TEAM_FOLDER_PREFIX, AWS_RAW_EXPORT_FOLDER_PREFIX, AWS_TODO_FILES_FOLDER, \
    DATABASE
from extract.extract_s3 import extract_names_data, extract_qs_chat_phone_data, extract_todo_tables
from load.load_to_postgres import create_db_if_not_exists, load_table_to_postgres
from transform.aggregations import get_aggregations, get_todo_aggregations
from transform.clean import clean_dfs, clean_todo_dfs
from transform.merges import get_final_prod_df


def get_prod_report():

    # Extract Data
    name_df = extract_names_data(AWS_BUCKET_NAME, AWS_TEAM_FOLDER_PREFIX)
    print("Extracted names data")
    dfs_dict = extract_qs_chat_phone_data(AWS_BUCKET_NAME, AWS_RAW_EXPORT_FOLDER_PREFIX)
    print('Chat, Phone and Quality data extracted!')
    todo_dfs = extract_todo_tables(AWS_BUCKET_NAME, AWS_TODO_FILES_FOLDER, 'CW1')
    print("ToDo dataframes extracted")

    # Clean Data
    cleaned_dfs = clean_dfs(dfs_dict, name_df)
    cleaned_todo_dfs = clean_todo_dfs(todo_dfs)
    print("Cleaned all DataFrames")

    # Aggregate Data
    agg_data = get_aggregations(cleaned_dfs)
    agg_todo_data = get_todo_aggregations(cleaned_todo_dfs, name_df)
    agg_data['emails_todo'] = agg_todo_data
    print("Done with all aggregations!")

    # Merge data
    final_productivity_table = get_final_prod_df(agg_data)
    print("Generated final productivity table")

    # Load Data
    create_db_if_not_exists(DATABASE)
    load_table_to_postgres(df=final_productivity_table, table_name='CW1_prod_table')


if __name__ == "__main__":
    get_prod_report()
