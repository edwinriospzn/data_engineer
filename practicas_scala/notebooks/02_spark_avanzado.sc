// 🚀 Spark Avanzado
import $ivy.`org.apache.spark::spark-sql:3.4.0`
import org.apache.spark.sql._
import org.apache.spark.sql.functions._

val spark = SparkSession.builder()
  .master("local[*]")
  .appName("Spark-Avanzado")
  .getOrCreate()

println(s"✅ Spark versión: ${spark.version}")

// 1. Generar datos de prueba
val datos = spark.range(1, 1000)
  .select(
    col("id"),
    rand() as "valor_random",
    (rand() * 100).cast("int") as "valor_entero",
    when(rand() > 0.5, "A").otherwise("B") as "categoria"
  )

println("📊 Datos generados:")
datos.show(10)

// 2. Funciones de ventana
import org.apache.spark.sql.expressions.Window

val windowSpec = Window.orderBy(col("valor_entero").desc)

datos
  .withColumn("rank", rank().over(windowSpec))
  .withColumn("dense_rank", dense_rank().over(windowSpec))
  .withColumn("percent_rank", percent_rank().over(windowSpec))
  .select("id", "valor_entero", "rank", "dense_rank", "percent_rank")
  .show(10)

// 3. Agregaciones avanzadas
println("\n📈 Agregaciones avanzadas:")
datos.groupBy("categoria")
  .agg(
    count("*") as "cantidad",
    avg("valor_entero") as "promedio",
    max("valor_entero") as "maximo",
    min("valor_entero") as "minimo",
    stddev("valor_entero") as "desviacion"
  )
  .show()

// 4. Transformaciones con UDFs
val cuadradoUDF = udf((x: Double) => x * x)
val cuboUDF = udf((x: Double) => x * x * x)

datos
  .withColumn("cuadrado", cuadradoUDF(col("valor_random")))
  .withColumn("cubo", cuboUDF(col("valor_random")))
  .select("id", "valor_random", "cuadrado", "cubo")
  .show(10)

// 5. Particionamiento
println("\n🔢 Datos particionados:")
datos.repartition(4)
  .rdd
  .mapPartitionsWithIndex { (idx, iter) => 
    Iterator(s"Partición $idx: ${iter.size} elementos")
  }
  .collect()
  .foreach(println)

// 6. Caché y persistencia
println("\n💾 Usando caché:")
datos.cache()
println(s"Registros en caché: ${datos.count()}")
datos.unpersist()

println("✅ ¡Spark avanzado funcionando correctamente!")

spark.stop()
