import csv
import os
from datetime import datetime
from pathlib import Path

import psycopg2
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator

# Set connection as environment variable
os.environ["AIRFLOW_CONN_ETL_POSTGRES"] = "postgres://etl_user:etl_pass@etl-postgres:5432/dbdags"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "04"
DB_HOST = "etl-postgres"
DB_PORT = 5432
DB_NAME = "dbdags"
DB_USER = "etl_user"
DB_PASSWORD = "etl_pass"


def read_csv(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_data(table_name, rows, columns):
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join(columns)
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        for row in rows:
            cur.execute(sql, tuple(row[col] for col in columns))
    conn.commit()
    conn.close()


def create_tables():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS t04_order_summary")
        cur.execute("DROP TABLE IF EXISTS t04_orders")
        cur.execute("DROP TABLE IF EXISTS t04_customers")
        
        cur.execute("""
            CREATE TABLE t04_customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT,
                city TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE t04_orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER REFERENCES t04_customers(customer_id),
                amount INTEGER,
                status TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()


def load_customers():
    rows = read_csv("customers.csv")
    load_data("t04_customers", rows, ["customer_id", "name", "city"])


def load_orders():
    rows = read_csv("orders.csv")
    load_data("t04_orders", rows, ["order_id", "customer_id", "amount", "status"])


def check_data_size():
    """Branch function - returns next task_id based on order count."""
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM t04_orders")
        count = cur.fetchone()[0]
    conn.close()
    
    # Log the count for visibility
    print(f"📊 Total orders: {count}")
    
    if count < 30:
        print("➡️ Branch: SMALL (light processing)")
        return "process_small"
    elif count < 80:
        print("➡️ Branch: MEDIUM (standard processing)")
        return "process_medium"
    else:
        print("➡️ Branch: LARGE (heavy processing)")
        return "process_large"


def process_small():
    print("🟢 Processing SMALL order volume (< 30 orders)")
    print("   - Quick validation")
    print("   - Simple aggregation")
    print("   - Fast execution")


def process_medium():
    print("🟡 Processing MEDIUM order volume (30-80 orders)")
    print("   - Standard validation")
    print("   - Full aggregation")
    print("   - Normal execution")


def process_large():
    print("🔴 Processing LARGE order volume (> 80 orders)")
    print("   - Intensive validation")
    print("   - Complex aggregation")
    print("   - Slow execution (simulated)")


def generate_summary(**context):
    """Generate summary table with execution details."""
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        # Get the branch that was triggered from context
        # We'll determine it from the task that ran before this
        # Or we can query the data and infer from count
        cur.execute("SELECT COUNT(*) FROM t04_orders")
        count = cur.fetchone()[0]
        
        if count < 30:
            branch = "SMALL"
        elif count < 80:
            branch = "MEDIUM"
        else:
            branch = "LARGE"
        
        # Create summary table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS t04_order_summary (
                execution_id SERIAL PRIMARY KEY,
                total_orders INTEGER,
                total_revenue INTEGER,
                status_pending INTEGER,
                status_shipped INTEGER,
                status_delivered INTEGER,
                status_cancelled INTEGER,
                branch_triggered TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert summary data
        cur.execute("""
            INSERT INTO t04_order_summary (
                total_orders,
                total_revenue,
                status_pending,
                status_shipped,
                status_delivered,
                status_cancelled,
                branch_triggered
            )
            SELECT
                COUNT(*) AS total_orders,
                COALESCE(SUM(amount), 0) AS total_revenue,
                COUNT(CASE WHEN status = 'Pending' THEN 1 END) AS status_pending,
                COUNT(CASE WHEN status = 'Shipped' THEN 1 END) AS status_shipped,
                COUNT(CASE WHEN status = 'Delivered' THEN 1 END) AS status_delivered,
                COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) AS status_cancelled,
                %s AS branch_triggered
            FROM t04_orders
        """, (branch,))
        
        print(f"\n📋 Summary generated:")
        print(f"   - Branch: {branch}")
        print(f"   - Total orders: {count}")
        
        # Show results
        cur.execute("""
            SELECT total_orders, total_revenue, status_pending, status_shipped, status_delivered, status_cancelled
            FROM t04_order_summary
            ORDER BY execution_id DESC
            LIMIT 1
        """)
        result = cur.fetchone()
        print(f"   - Total revenue: ${result[1] if result else 0}")
        print(f"   - Status: Pending={result[2]}, Shipped={result[3]}, Delivered={result[4]}, Cancelled={result[5]}")
        
    conn.commit()
    conn.close()


with DAG(
    dag_id="04_branch",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "branching"],
) as dag:
    start = EmptyOperator(task_id="start")
    
    create = PythonOperator(task_id="create_tables", python_callable=create_tables)
    load_customers = PythonOperator(task_id="load_customers", python_callable=load_customers)
    load_orders = PythonOperator(task_id="load_orders", python_callable=load_orders)
    
    check_size = BranchPythonOperator(
        task_id="check_data_size",
        python_callable=check_data_size,
    )
    
    process_small = PythonOperator(task_id="process_small", python_callable=process_small)
    process_medium = PythonOperator(task_id="process_medium", python_callable=process_medium)
    process_large = PythonOperator(task_id="process_large", python_callable=process_large)
    
    generate_summary = PythonOperator(
        task_id="generate_summary",
        python_callable=generate_summary,
        provide_context=True,
    )
    
    end = EmptyOperator(task_id="end")
    
    # Dependencies
    start >> create >> [load_customers, load_orders] >> check_size
    check_size >> [process_small, process_medium, process_large]
    [process_small, process_medium, process_large] >> generate_summary >> end