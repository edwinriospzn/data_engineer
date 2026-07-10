from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as spark_sum, col, to_date

spark = SparkSession.builder \
    .appName("SalesProcessing") \
    .master("local[*]") \
    .getOrCreate()

# Read data
df = spark.read.csv("/opt/airflow/data/08/sample_data.csv",
                   header=True, inferSchema=True)

# Process: Total sales per category
result = df.groupBy("category") \
    .agg(spark_sum("amount").alias("total_amount")) \
    .orderBy(col("total_amount").desc())

result.show()

# Save results
result.write.mode("overwrite") \
    .parquet("/opt/airflow/data/08/output/sales_summary.parquet")

spark.stop()
