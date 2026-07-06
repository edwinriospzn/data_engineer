from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator


def hello_world():
    print("Hello, World!")


with DAG(
    dag_id="00_hello_world",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning"],
) as dag:
    start = EmptyOperator(task_id="start")
    hello = PythonOperator(task_id="hello_world", python_callable=hello_world)
    end = EmptyOperator(task_id="end")

    start >> hello >> end
