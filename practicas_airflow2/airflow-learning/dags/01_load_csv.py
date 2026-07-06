import csv
from datetime import datetime
from pathlib import Path

import psycopg2
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "customers.csv"
DB_HOST = "etl-postgres"
DB_PORT = 5432
DB_NAME = "dbdags"
DB_USER = "etl_user"
DB_PASSWORD = "etl_pass"


def read_customers():
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def create_customers_table():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT,
                city TEXT
            )
            """
        )
    conn.commit()
    conn.close()


def insert_customers(**context):
    rows = context["ti"].xcom_pull(task_ids="read_customers")
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(
                "INSERT INTO customers (customer_id, name, city) VALUES (%s, %s, %s) ON CONFLICT (customer_id) DO NOTHING",
                (int(row["customer_id"]), row["name"], row["city"]),
            )
    conn.commit()
    conn.close()


with DAG(
    dag_id="01_load_csv",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning"],
) as dag:
    start = EmptyOperator(task_id="start")
    read = PythonOperator(task_id="read_customers", python_callable=read_customers)
    create_table = PythonOperator(task_id="create_customers_table", python_callable=create_customers_table)
    insert = PythonOperator(task_id="insert_customers", python_callable=insert_customers, provide_context=True)
    end = EmptyOperator(task_id="end")

    start >> read >> create_table >> insert >> end
