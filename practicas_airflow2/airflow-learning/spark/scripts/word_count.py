from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("WordCount") \
    .master("local[*]") \
    .getOrCreate()

# Create sample data
data = [("Hello",), ("World",), ("Hello",), ("Airflow",)]
df = spark.createDataFrame(data, ["word"])
result = df.groupBy("word").count().collect()

for row in result:
    print(f"{row.word}: {row.count}")

spark.stop()
