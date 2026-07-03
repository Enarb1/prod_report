from config.config import AWS_BUCKET_NAME, AWS_TEAM_FOLDER_PREFIX, AWS_RAW_EXPORT_FOLDER_PREFIX
from extract.extract_s3 import extract_names_data, extract_qs_chat_phone_data


def get_prod_report():
    name_df = extract_names_data(AWS_BUCKET_NAME, AWS_TEAM_FOLDER_PREFIX)
    chat_df, phone_df, qs_df = extract_qs_chat_phone_data(AWS_BUCKET_NAME, AWS_RAW_EXPORT_FOLDER_PREFIX)

    print(chat_df)
    print(phone_df)
    print(qs_df)

if __name__ == "__main__":
    get_prod_report()
