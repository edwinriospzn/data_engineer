"""
DAG 11 — Part 2: Consumer

Responsibility:
    - Be triggered by 1101_trigger_producer in two different ways
    - Show what payload (if any) was received

Key learning:
    - Reading `dag_run.conf` to inspect the payload
    - Inspecting `dag_run.run_type` to know HOW we were triggered
    - Understanding that Dataset-triggered runs have an EMPTY conf
"""
from datetime import datetime

from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator


# Same URI string as in the producer — this is the contract between the two DAGs.
CUSTOMERS_DATASET = Dataset("file:///opt/airflow/data/11/customers_ready.csv")


def read_conf(**context):
    """Print how we were triggered and what payload we received, if any."""
    dag_run = context["dag_run"]
    conf = dag_run.conf or {}

    print("=" * 60)
    print(f"dag_id      : {dag_run.dag_id}")
    print(f"run_id      : {dag_run.run_id}")
    print(f"run_type    : {dag_run.run_type}")   # manual / dataset_triggered / ...
    print(f"external    : {dag_run.external_trigger}")
    print("-" * 60)

    if conf:
        print("📨 Triggered WITH payload:")
        print(f"   source   = {conf.get('source')}")
        print(f"   records  = {conf.get('records')}")
        print(f"   cities   = {conf.get('cities')}")
    else:
        print("📨 Triggered with NO payload (likely by Dataset)")

    print("=" * 60)
    return conf


with DAG(
    dag_id="1102_trigger_consumer",
    start_date=datetime(2024, 1, 1),
    # This DAG runs when:
    #   1. 1101_trigger_producer emits CUSTOMERS_DATASET, OR
    #   2. someone manually triggers it, OR
    #   3. 1101_trigger_producer calls TriggerDagRunOperator(...)
    schedule=[CUSTOMERS_DATASET],
    catchup=False,
    tags=["learning", "trigger", "dataset"],
) as dag:

    start = EmptyOperator(task_id="start")

    show_conf = PythonOperator(
        task_id="show_conf",
        python_callable=read_conf,
    )

    end = EmptyOperator(task_id="end")

    start >> show_conf >> end