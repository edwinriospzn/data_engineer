"""
DAG 11 — Part 1: Producer

Responsibility:
    - Prepare some data
    - Trigger 1102_trigger_consumer via TriggerDagRunOperator WITH a small payload
    - Trigger 1102_trigger_consumer again via a Dataset outlet (declarative)

Key learning:
    - Two ways to trigger a downstream DAG
    - The difference between imperative (conf) and declarative (Dataset) triggers
"""
import csv
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


# A Dataset represents a logical data asset this DAG produces.
# When a task declares `outlets=[CUSTOMERS_DATASET]`, Airflow will
# automatically trigger any DAG whose schedule is `[CUSTOMERS_DATASET]`.
CUSTOMERS_DATASET = Dataset("file:///opt/airflow/data/11/customers_ready.csv")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "11"


def prepare_customers():
    """Create a small CSV that represents a data asset being 'published'."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        {"customer_id": 1, "name": "Ana", "city": "Barcelona"},
        {"customer_id": 2, "name": "Beto", "city": "Madrid"},
        {"customer_id": 3, "name": "Carlos", "city": "Valencia"},
    ]
    path = DATA_DIR / "customers_ready.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["customer_id", "name", "city"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Wrote {path}")
    return str(path)


with DAG(
    dag_id="1101_trigger_producer",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,          # manual trigger only
    catchup=False,
    tags=["learning", "trigger", "dataset"],
) as dag:

    start = EmptyOperator(task_id="start")

    prepare = PythonOperator(
        task_id="prepare_customers",
        python_callable=prepare_customers,
    )

    # ------------------------------------------------------------------
    # Way 1: Imperative trigger WITH payload via TriggerDagRunOperator
    # ------------------------------------------------------------------
    # `wait_for_completion=False` means the producer does NOT block;
    # change to True to see the consumer's result before continuing.
    trigger_with_payload = TriggerDagRunOperator(
        task_id="trigger_consumer_with_payload",
        trigger_dag_id="1102_trigger_consumer",
        conf={
            "source": "producer_payload",
            "records": 3,
            "cities": ["Barcelona", "Madrid", "Valencia"],
        },
        wait_for_completion=False,
        reset_dag_run=True,
        poke_interval=10,
    )

    # ------------------------------------------------------------------
    # Way 2: Declarative trigger via Dataset outlet
    # ------------------------------------------------------------------
    # Simply marking a task as producing the Dataset is enough for
    # Airflow to schedule the consumer DAG.
    mark_dataset = EmptyOperator(
        task_id="mark_customers_dataset",
        outlets=[CUSTOMERS_DATASET],
    )

    end = EmptyOperator(task_id="end")

    start >> prepare >> trigger_with_payload >> mark_dataset >> end