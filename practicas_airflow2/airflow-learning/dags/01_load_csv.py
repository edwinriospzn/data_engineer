from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator


def print_hello():
    print("Hello from Airflow")


with DAG(
    dag_id="01_load_csv",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning"],
) as dag:
    start = EmptyOperator(task_id="start")
    hello = PythonOperator(task_id="hello", python_callable=print_hello)
    end = EmptyOperator(task_id="end")

    start >> hello >> end
