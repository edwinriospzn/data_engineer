import csv
import os
from datetime import datetime
from pathlib import Path

import psycopg2
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor

# Set connection as environment variable
os.environ["AIRFLOW_CONN_ETL_POSTGRES"] = "postgres://etl_user:etl_pass@etl-postgres:5432/dbdags"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "05"
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
        cur.execute("DROP TABLE IF EXISTS t05_summary")
        cur.execute("DROP TABLE IF EXISTS t05_orders")
        cur.execute("DROP TABLE IF EXISTS t05_products")
        cur.execute("DROP TABLE IF EXISTS t05_customers")
        
        cur.execute("""
            CREATE TABLE t05_customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT,
                city TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE t05_products (
                product_id INTEGER PRIMARY KEY,
                name TEXT,
                price INTEGER,
                category TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE t05_orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER REFERENCES t05_customers(customer_id),
                product_id INTEGER REFERENCES t05_products(product_id),
                quantity INTEGER,
                amount INTEGER,
                order_date DATE,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()


def load_customers():
    rows = read_csv("customers.csv")
    load_data("t05_customers", rows, ["customer_id", "name", "city"])


def load_products():
    rows = read_csv("products.csv")
    load_data("t05_products", rows, ["product_id", "name", "price", "category"])


def load_orders():
    rows = read_csv("orders.csv")
    load_data("t05_orders", rows, ["order_id", "customer_id", "product_id", "quantity", "amount", "order_date"])


def generate_summary():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        # Create summary table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS t05_summary (
                execution_id SERIAL PRIMARY KEY,
                total_orders INTEGER,
                total_revenue INTEGER,
                avg_order_value DECIMAL(10,2),
                total_customers INTEGER,
                total_products INTEGER,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert summary data
        cur.execute("""
            INSERT INTO t05_summary (
                total_orders,
                total_revenue,
                avg_order_value,
                total_customers,
                total_products
            )
            SELECT
                COUNT(DISTINCT o.order_id) AS total_orders,
                COALESCE(SUM(o.amount), 0) AS total_revenue,
                ROUND(COALESCE(AVG(o.amount), 0)::numeric, 2) AS avg_order_value,
                COUNT(DISTINCT c.customer_id) AS total_customers,
                COUNT(DISTINCT p.product_id) AS total_products
            FROM t05_customers c
            CROSS JOIN t05_products p
            LEFT JOIN t05_orders o ON o.customer_id = c.customer_id AND o.product_id = p.product_id
        """)
        
        print(f"\n📋 Summary generated:")
        cur.execute("""
            SELECT total_orders, total_revenue, avg_order_value, total_customers, total_products
            FROM t05_summary
            ORDER BY execution_id DESC
            LIMIT 1
        """)
        result = cur.fetchone()
        if result:
            print(f"   - Total orders: {result[0]}")
            print(f"   - Total revenue: ${result[1]:,}")
            print(f"   - Avg order value: ${result[2]}")
            print(f"   - Total customers: {result[3]}")
            print(f"   - Total products: {result[4]}")
        
    conn.commit()
    conn.close()


with DAG(
    dag_id="05_sensor",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "sensor"],
) as dag:
    start = EmptyOperator(task_id="start")
    
    create_tables = PythonOperator(task_id="create_tables", python_callable=create_tables)
    
    # Sensor waits for orders.csv to exist - using fs_conn_id=None for local filesystem
    wait_for_orders = FileSensor(
        task_id="wait_for_orders",
        filepath=str(DATA_DIR / "orders.csv"),
        fs_conn_id="fs_default",   # Use the connection we created
        poke_interval=10,          # Check every 10 seconds
        timeout=120,               # Timeout after 2 minutes
        mode="poke",               # Poke mode (or "reschedule")
    )
    
    load_customers = PythonOperator(task_id="load_customers", python_callable=load_customers)
    load_products = PythonOperator(task_id="load_products", python_callable=load_products)
    load_orders = PythonOperator(task_id="load_orders", python_callable=load_orders)
    
    generate_summary = PythonOperator(
        task_id="generate_summary",
        python_callable=generate_summary,
    )
    
    end = EmptyOperator(task_id="end")
    
    # Dependencies
    start >> create_tables >> wait_for_orders
    wait_for_orders >> [load_customers, load_products] >> load_orders >> generate_summary >> end