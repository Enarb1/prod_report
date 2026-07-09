import os
from dotenv import load_dotenv

load_dotenv()

#AWS Credentials
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

AWS_REGION = os.getenv("AWS_REGION")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_TEAM_FOLDER_PREFIX = os.getenv("AWS_TEAM_FOLDER_PREFIX")
AWS_RAW_EXPORT_FOLDER_PREFIX = os.getenv("AWS_RAW_EXPORT_FOLDER_PREFIX")
AWS_TODO_FILES_FOLDER = os.getenv("AWS_TODO_FILES_FOLDER")
AWS_WEEKLY_FOLDER = os.getenv("AWS_WEEKLY_FOLDER")


# Database Credentials
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DATABASE = os.getenv("DATABASE")
