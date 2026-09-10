"""
DAG 12 — Part 2: Consumer

Responsibility:
    - Receive the batch_id and file_path through `dag_run.conf`
    - Read the payload from BOTH the shared file and the shared DB
    - Reconcile the counts against what the producer promised

Key learning:
    - The consumer reads `dag_run.conf` — not XCom from the producer
    - File and DB channels must agree — this is how you detect silent truncation
    - The pattern generalizes to S3, Kafka, Redis, etc.
"""
import json
from datetime import datetime
from pathlib import Path

import psycopg2
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator


DB_HOST = "etl-postgres"
DB_PORT = 5432
DB_NAME = "dbdags"
DB_USER = "etl_user"
DB_PASSWORD = "etl_pass"


def read_conf(**context):
    """Print the metadata the producer sent through conf."""
    conf = context["dag_run"].conf or {}
    print("=" * 60)
    print("📨 Received conf from producer:")
    for k, v in conf.items():
        print(f"   {k:18} = {v}")
    print("=" * 60)
    return conf


def read_from_file(**context):
    """Channel 2: read the full payload from the shared JSON file."""
    conf = context["dag_run"].conf or {}
    file_path = conf.get("file_path")

    if not file_path or not Path(file_path).exists():
        print(f"⚠️  File not found: {file_path}")
        return 0

    with open(file_path, encoding="utf-8") as f:
        payload = json.load(f)

    n = len(payload.get("records", []))
    print(f"📁 Read {n} records from file (batch={payload.get('batch_id')})")
    for r in payload.get("records", []):
        print(f"   {r}")
    return n


def read_from_postgres(**context):
    """Channel 3: read the full payload from Postgres."""
    conf = context["dag_run"].conf or {}
    batch_id = conf.get("batch_id")

    if not batch_id:
        print("⚠️  No batch_id in conf — cannot query DB")
        return 0

    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT order_id, customer, amount, status
            FROM t12_orders_payload
            WHERE batch_id = %s
            ORDER BY order_id
            """,
            (batch_id,),
        )
        rows = cur.fetchall()
    conn.close()

    print(f"🗄️  Read {len(rows)} rows from DB for batch={batch_id}")
    for r in rows:
        print(f"   {r}")
    return len(rows)


def reconcile(**context):
    """Compare file count, DB count, and what the producer promised."""
    ti = context["ti"]
    n_file = ti.xcom_pull(task_ids="read_from_file") or 0
    n_db = ti.xcom_pull(task_ids="read_from_postgres") or 0
    expected = (context["dag_run"].conf or {}).get("expected_records", 0)

    print("\n🧮 Reconciliation:")
    print(f"   expected   = {expected}")
    print(f"   from file  = {n_file}")
    print(f"   from DB    = {n_db}")

    assert n_file == n_db == expected, (
        f"❌ Mismatch: expected={expected}, file={n_file}, db={n_db}"
    )
    print("   ✅ All copies agree")


with DAG(
    dag_id="1202_payload_consumer",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,     # only runs when triggered by the producer
    catchup=False,
    tags=["learning", "payload"],
) as dag:

    start = EmptyOperator(task_id="start")

    conf = PythonOperator(
        task_id="read_conf",
        python_callable=read_conf,
    )

    from_file = PythonOperator(
        task_id="read_from_file",
        python_callable=read_from_file,
    )

    from_db = PythonOperator(
        task_id="read_from_postgres",
        python_callable=read_from_postgres,
    )

    recon = PythonOperator(
        task_id="reconcile",
        python_callable=reconcile,
    )

    end = EmptyOperator(task_id="end")

    start >> conf >> [from_file, from_db] >> recon >> end