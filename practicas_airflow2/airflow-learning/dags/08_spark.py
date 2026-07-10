import os
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

os.environ["AIRFLOW_CONN_ETL_POSTGRES"] = "postgres://etl_user:etl_pass@etl-postgres:5432/dbdags"

# Paths (for reference only)
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "08"
SPARK_DIR = Path(__file__).resolve().parents[1] / "spark" / "scripts"


with DAG(
    dag_id="08_spark",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "spark", "bash"],
) as dag:
    start = EmptyOperator(task_id="start")
    
    # Task 1: Run word count example
    run_word_count = BashOperator(
        task_id="run_word_count",
        bash_command="""
            echo "🚀 Running Word Count Example..."
            spark-submit \
                --master local[*] \
                /opt/airflow/spark/scripts/word_count.py
        """,
    )
    
    # Task 2: Run sales data processing
    run_sales_processing = BashOperator(
        task_id="run_sales_processing",
        bash_command="""
            echo "🚀 Running Sales Data Processing..."
            mkdir -p /opt/airflow/data/08/output
            spark-submit \
                --master local[*] \
                --driver-memory 1g \
                --executor-memory 1g \
                /opt/airflow/spark/scripts/sales_processing.py
        """,
    )
    
    end = EmptyOperator(task_id="end")
    
    # Dependencies
    start >> [run_word_count, run_sales_processing] >> end