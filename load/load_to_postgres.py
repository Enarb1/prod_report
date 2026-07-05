import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from config.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DATABASE


def create_db_if_not_exists(db_name: str) -> None:
    db_params = {
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,
        'port': DB_PORT,
        'database': 'postgres'
    }

    conn = psycopg2.connect(**db_params)
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (db_name,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE {db_name};')
                print(f"Created Database: {db_name}")
            else:
                print(f"Database {db_name} already exists")
    finally:
        conn.close()


def load_table_to_postgres(df: pd.DataFrame, table_name: str, if_exists: str = 'replace') -> None:
    try:
        connection_string = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DATABASE}'
        engine = create_engine(connection_string)
        df.to_sql(table_name, engine, index=False, if_exists=if_exists, method='multi', chunksize=1000)
        print(f"Table {table_name} loaded to PostgreSQL successfully!")
    except Exception as e:
        print(f'Error connecting to PostgreSQL: {e}')
        raise
