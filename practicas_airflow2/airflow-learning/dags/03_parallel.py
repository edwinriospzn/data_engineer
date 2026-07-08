from datetime import datetime
from pathlib import Path
import csv

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def process_file(filename):
    """Read a CSV file and print basic stats."""
    filepath = DATA_DIR / filename
    with filepath.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    
    print(f"📊 {filename}: {len(rows)} rows")
    if rows:
        print(f"   Sample: {rows[0]}")
        if "amount" in rows[0]:
            total = sum(int(r["amount"]) for r in rows)
            print(f"   Total amount: {total}")
        elif "price" in rows[0]:
            avg = sum(float(r["price"]) for r in rows) / len(rows)
            print(f"   Average price: {avg:.2f}")


with DAG(
    dag_id="03_parallel",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "parallel"],
) as dag:
    start = EmptyOperator(task_id="start")
    split = EmptyOperator(task_id="split")
    
    # Parallel branches
    process_customers = PythonOperator(
        task_id="process_customers",
        python_callable=process_file,
        op_args=["customers.csv"]
    )
    process_orders = PythonOperator(
        task_id="process_orders",
        python_callable=process_file,
        op_args=["orders.csv"]
    )
    process_products = PythonOperator(
        task_id="process_products",
        python_callable=process_file,
        op_args=["products.csv"]
    )
    
    # Logging tasks after each branch
    log_customers = EmptyOperator(task_id="log_customers")
    log_orders = EmptyOperator(task_id="log_orders")
    log_products = EmptyOperator(task_id="log_products")
    
    join = EmptyOperator(task_id="join")
    end = EmptyOperator(task_id="end")

    # Dependencies
    start >> split
    split >> [process_customers, process_orders, process_products]
    process_customers >> log_customers
    process_orders >> log_orders
    process_products >> log_products
    [log_customers, log_orders, log_products] >> join                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
    join >> end