from airflow.providers.amazon.aws.hooks.s3 import S3Hook


def get_s3_hook_and_storage_options(aws_conn_id: str) -> tuple[S3Hook, dict]:
    """
    Get S3 hook and storage options for Amazon S3 connection.
    Returning S3 hook and storage options
    """
    hook = S3Hook(aws_conn_id=aws_conn_id)
    creds = hook.get_credentials()

    storage_options = {
        'key': creds.access_key,
        'secret': creds.secret_key,
    }

    return hook, storage_options