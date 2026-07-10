import csv
import os
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator

os.environ["AIRFLOW_CONN_ETL_POSTGRES"] = "postgres://etl_user:etl_pass@etl-postgres:5432/dbdags"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "07"


@task
def load_customers():
    """Load customers from CSV and return list of customer dicts."""
    with open(DATA_DIR / "customers.csv", "r", encoding="utf-8") as f:
        customers = list(csv.DictReader(f))
    
    print(f"📚 Loaded {len(customers)} customers")
    return customers


@task
def process_customer(customer: dict):
    """Process a single customer - runs once for each customer."""
    customer_id = customer["customer_id"]
    name = customer["name"]
    city = customer["city"]
    membership = customer["membership_type"]
    join_date = customer["join_date"]
    
    # Simulate processing time based on membership type
    processing_time = {"Premium": 2, "Standard": 1, "Student": 0.5}
    time_taken = processing_time.get(membership, 1)
    
    # Generate a processed result
    result = {
        "customer_id": customer_id,
        "name": name,
        "city": city,
        "membership": membership,
        "processed": True,
        "processing_time": time_taken,
        "status": "success",
    }
    
    print(f"✅ Processed: {name} ({membership}) - took {time_taken}s")
    return result


@task
def generate_summary(results: list):
    """Aggregate results from all processed customers."""
    total_customers = len(results)
    
    # Count membership types
    membership_counts = {}
    for r in results:
        membership = r["membership"]
        membership_counts[membership] = membership_counts.get(membership, 0) + 1
    
    # Calculate average processing time
    avg_time = sum(r["processing_time"] for r in results) / total_customers if total_customers > 0 else 0
    
    summary = {
        "total_customers": total_customers,
        "membership_counts": membership_counts,
        "avg_processing_time": avg_time,
        "cities": [r["city"] for r in results],
    }
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total customers: {total_customers}")
    print(f"   Membership breakdown: {membership_counts}")
    print(f"   Avg processing time: {avg_time:.2f}s")
    
    return summary


with DAG(
    dag_id="07_dynamic_mapping",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "dynamic", "mapping"],
) as dag:
    start = EmptyOperator(task_id="start")
    
    # Load customers
    customers = load_customers()
    
    # Dynamic mapping: process each customer in parallel
    processed = process_customer.expand(customer=customers)
    
    # Generate summary from all results
    summary = generate_summary(processed)
    
    end = EmptyOperator(task_id="end")
    
    start >> customers >> processed >> summary >> end