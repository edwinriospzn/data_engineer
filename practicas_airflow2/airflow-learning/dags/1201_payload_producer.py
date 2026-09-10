"""
DAG 12 — Part 1: Producer

Responsibility:
    - Build a structured payload
    - Ship it to 1202_payload_consumer through THREE channels:
        1. Small metadata via TriggerDagRunOperator(conf=...)
        2. Full payload as a JSON file on the shared /opt/airflow/data volume
        3. Full payload as rows in a Postgres table
    - Block until the consumer finishes so we can see its result inline

Key learning:
    - XCom does NOT cross DAG boundaries
    - You can only move data via conf, shared files, or a shared DB
    - wait_for_completion=True blocks the producer until the consumer ends
"""
import json
from datetime import datetime
from pathlib import Path

import psycopg2
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "12"

DB_HOST = "etl-postgres"
DB_PORT = 5432
DB_NAME = "dbdags"
DB_USER = "etl_user"
DB_PASSWORD = "etl_pass"


def build_payload(**context):
    """Produce the payload and keep it in this DAG's XCom (local only)."""
    payload = {
        "batch_id": f"batch-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "produced_at": datetime.now().isoformat(),
        "records": [
            {"order_id": 1001, "customer": "Ana",    "amount": 250.0, "status": "Shipped"},
            {"order_id": 1002, "customer": "Beto",   "amount": 80.0,  "status": "Pending"},
            {"order_id": 1003, "customer": "Carlos", "amount": 120.0, "status": "Delivered"},
        ],
    }

    # XCom here only lives inside THIS dag_run.
    # It is NOT visible to the consumer DAG — that's the whole point of DAG 12.
    context["ti"].xcom_push(key="payload", value=payload)

    print(f"📦 Built payload: {len(payload['records'])} records, "
          f"batch_id={payload['batch_id']}")
    return payload["batch_id"]


def write_payload_to_file(**context):
    """Channel 2: full payload → JSON file on the shared volume."""
    payload = context["ti"].xcom_pull(task_ids="build_payload", key="payload")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "orders_payload.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"💾 Wrote payload to {path}")
    return str(path)


def write_payload_to_postgres(**context):
    """Channel 3: full payload → Postgres rows."""
    payload = context["ti"].xcom_pull(task_ids="build_payload", key="payload")

    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS t12_orders_payload (
                batch_id    TEXT,
                order_id    INTEGER,
                customer    TEXT,
                amount      NUMERIC(10,2),
                status      TEXT,
                produced_at TIMESTAMP,
                PRIMARY KEY (batch_id, order_id)
            )
        """)
        for r in payload["records"]:
            cur.execute(
                """
                INSERT INTO t12_orders_payload
                    (batch_id, order_id, customer, amount, status, produced_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (payload["batch_id"], r["order_id"], r["customer"],
                 r["amount"], r["status"], payload["produced_at"]),
            )
    conn.commit()
    conn.close()
    print(f"🗄️  Inserted {len(payload['records'])} rows into t12_orders_payload")


with DAG(
    dag_id="1201_payload_producer",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "payload"],
) as dag:

    start = EmptyOperator(task_id="start")

    build = PythonOperator(
        task_id="build_payload",
        python_callable=build_payload,
    )

    to_file = PythonOperator(
        task_id="write_payload_to_file",
        python_callable=write_payload_to_file,
    )

    to_db = PythonOperator(
        task_id="write_payload_to_postgres",
        python_callable=write_payload_to_postgres,
    )

    # Channel 1: small metadata through conf (NOT the payload itself!)
    # wait_for_completion=True blocks until the consumer finishes.
    trigger = TriggerDagRunOperator(
        task_id="trigger_consumer",
        trigger_dag_id="1202_payload_consumer",
        conf={
            "batch_id": "{{ ti.xcom_pull(task_ids='build_payload', key='payload')['batch_id'] }}",
            "file_path": "/opt/airflow/data/12/orders_payload.json",
            "expected_records": 3,
        },
        wait_for_completion=True,
        reset_dag_run=True,
        poke_interval=10,
        allowed_states=["success", "failed"],
    )

    end = EmptyOperator(task_id="end")

    start >> build >> [to_file, to_db] >> trigger >> end