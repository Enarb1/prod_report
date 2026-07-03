from config.config import AWS_BUCKET_NAME, AWS_TEAM_FOLDER_PREFIX, AWS_TODO_FILES_FOLDER
from create.create_to_table import add_user_table
from extract.extract_s3 import extract_names_data

def create_todos():
    name_df =  extract_names_data(AWS_BUCKET_NAME, AWS_TEAM_FOLDER_PREFIX)
    add_user_table(name_df, AWS_BUCKET_NAME, AWS_TEAM_FOLDER_PREFIX,AWS_TODO_FILES_FOLDER)


if __name__ == "__main__":
    create_todos()