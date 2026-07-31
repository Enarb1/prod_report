import sys, types

def install_airflow_stubs():
    """
    Only install a fake S3Hook if the real Airflow provider package cannot be
    imported (e.g. running these tests outside the Astro/Airflow container).
    Inside `astro dev pytest`, the real package is installed and is used as-is.
    """
    try:
        import airflow.providers.amazon.aws.hooks.s3  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    airflow = types.ModuleType("airflow")
    p1 = types.ModuleType("airflow.providers")
    p2 = types.ModuleType("airflow.providers.amazon")
    p3 = types.ModuleType("airflow.providers.amazon.aws")
    p4 = types.ModuleType("airflow.providers.amazon.aws.hooks")
    p5 = types.ModuleType("airflow.providers.amazon.aws.hooks.s3")

    class FakeS3Hook:
        def __init__(self, aws_conn_id=None):
            self.aws_conn_id = aws_conn_id
        def get_credentials(self):
            class Creds:
                access_key = "fake"
                secret_key = "fake"
            return Creds()
        def list_keys(self, bucket_name=None, prefix=None):
            return []

    p5.S3Hook = FakeS3Hook

    for name, mod in [
        ("airflow", airflow), ("airflow.providers", p1), ("airflow.providers.amazon", p2),
        ("airflow.providers.amazon.aws", p3), ("airflow.providers.amazon.aws.hooks", p4),
        ("airflow.providers.amazon.aws.hooks.s3", p5),
    ]:
        sys.modules[name] = mod

install_airflow_stubs()
