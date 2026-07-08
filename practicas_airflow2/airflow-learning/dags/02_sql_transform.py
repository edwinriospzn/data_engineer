import csv
import os
from datetime import datetime
from pathlib import Path

import psycopg2
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

# Set connection as environment variable
os.environ["AIRFLOW_CONN_ETL_POSTGRES"] = "postgres://etl_user:etl_pass@etl-postgres:5432/dbdags"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "02"
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
        cur.execute("DROP TABLE IF EXISTS t02_product_performance")
        cur.execute("DROP TABLE IF EXISTS t02_orders")
        cur.execute("DROP TABLE IF EXISTS t02_products")
        cur.execute("DROP TABLE IF EXISTS t02_customers")
        
        cur.execute("""
            CREATE TABLE t02_customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT,
                city TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE t02_products (
                product_id INTEGER PRIMARY KEY,
                name TEXT,
                price INTEGER,
                category TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE t02_orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER REFERENCES t02_customers(customer_id),
                product_id INTEGER REFERENCES t02_products(product_id),
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
    load_data("t02_customers", rows, ["customer_id", "name", "city"])


def load_products():
    rows = read_csv("products.csv")
    load_data("t02_products", rows, ["product_id", "name", "price", "category"])


def load_orders():
    rows = read_csv("orders.csv")
    load_data("t02_orders", rows, ["order_id", "customer_id", "product_id", "quantity", "amount", "order_date"])


def calculate_performance():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE t02_product_performance AS
            SELECT 
                p.product_id,
                p.name,
                p.category,
                COUNT(o.order_id) AS orders,
                COALESCE(SUM(o.quantity), 0) AS units_sold,
                COALESCE(SUM(o.amount), 0) AS revenue,
                RANK() OVER (ORDER BY COALESCE(SUM(o.amount), 0) DESC) AS rank,
                CURRENT_TIMESTAMP AS executed_at
            FROM t02_products p
            LEFT JOIN t02_orders o ON p.product_id = o.product_id
            GROUP BY p.product_id, p.name, p.category
            ORDER BY revenue DESC;
        """)
    conn.commit()
    conn.close()


with DAG(
    dag_id="02_sql_transform",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "sql"],
) as dag:
    start = EmptyOperator(task_id="start")
    
    create = PythonOperator(task_id="create_tables", python_callable=create_tables)
    load_customers = PythonOperator(task_id="load_customers", python_callable=load_customers)
    load_products = PythonOperator(task_id="load_products", python_callable=load_products)
    load_orders = PythonOperator(task_id="load_orders", python_callable=load_orders)
    performance = PythonOperator(task_id="product_performance", python_callable=calculate_performance)
    end = EmptyOperator(task_id="end")
    
    start >> create >> [load_customers, load_products] >> load_orders >> performance >> end