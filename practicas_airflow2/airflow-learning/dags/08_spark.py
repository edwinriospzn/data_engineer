import os
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

os.environ["AIRFLOW_CONN_ETL_POSTGRES"] = "postgres://etl_user:etl_pass@etl-postgres:5432/dbdags"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "08"


def run_word_count():
    """Run word count using PySpark."""
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder \
        .appName("WordCount") \
        .master("local[*]") \
        .getOrCreate()
    
    data = [("Hello",), ("World",), ("Hello",), ("Airflow",), ("Spark",), ("Hello",)]
    df = spark.createDataFrame(data, ["word"])
    result = df.groupBy("word").count().orderBy("count", ascending=False)
    
    print("\n📊 WORD COUNT RESULTS:")
    result.show()
    
    spark.stop()


def run_sales_processing():
    """Run sales processing using PySpark."""
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import sum as spark_sum, col, avg, count
    
    spark = SparkSession.builder \
        .appName("SalesProcessing") \
        .master("local[*]") \
        .getOrCreate()
    
    # Read data
    df = spark.read.csv("/opt/airflow/data/08/sales_data.csv",
                        header=True, inferSchema=True)
    
    print("\n📊 RAW DATA:")
    df.show()
    
    # Total sales per category
    category_sales = df.groupBy("category") \
        .agg(spark_sum("amount").alias("total_revenue"),
             avg("amount").alias("avg_amount"),
             count("*").alias("transaction_count")) \
        .orderBy(col("total_revenue").desc())
    
    print("\n💰 SALES BY CATEGORY:")
    category_sales.show()
    
    # Top products by revenue
    product_sales = df.groupBy("product_id") \
        .agg(spark_sum("amount").alias("total_revenue")) \
        .orderBy(col("total_revenue").desc()) \
        .limit(5)
    
    print("\n🏆 TOP 5 PRODUCTS BY REVENUE:")
    product_sales.show()
    
    spark.stop()


with DAG(
    dag_id="08_spark",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "spark", "python"],
) as dag:
    start = EmptyOperator(task_id="start")
    
    run_word_count = PythonOperator(
        task_id="run_word_count",
        python_callable=run_word_count,
    )
    
    run_sales_processing = PythonOperator(
        task_id="run_sales_processing",
        python_callable=run_sales_processing,
    )
    
    end = EmptyOperator(task_id="end")
    
    start >> [run_word_count, run_sales_processing] >> end