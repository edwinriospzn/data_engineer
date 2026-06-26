// 📊 Spark Básico
// Importar Spark
import $ivy.`org.apache.spark::spark-sql:3.4.0`
import org.apache.spark.sql._

// Crear SparkSession
val spark = SparkSession.builder()
  .master("local[*]")
  .appName("Practica-Spark")
  .config("spark.sql.adaptive.enabled", "false")
  .getOrCreate()

println(s"✅ Spark versión: ${spark.version}")
println(s"✅ Scala versión: ${scala.util.Properties.versionNumberString}")

// 1. Crear DataFrame desde secuencia
val data = Seq(
  (1, "Ana", 25, "Madrid"),
  (2, "Luis", 30, "Barcelona"),
  (3, "María", 22, "Valencia"),
  (4, "Juan", 28, "Sevilla"),
  (5, "Laura", 35, "Bilbao")
)

val df = spark.createDataFrame(data).toDF("id", "nombre", "edad", "ciudad")
println("\n📋 DataFrame creado:")
df.show()

// 2. Operaciones básicas
println("\n📊 Estadísticas:")
df.describe("edad").show()

println("\n🔍 Personas mayores de 25 años:")
df.filter("edad > 25").show()

println("\n📈 Agrupación por ciudad:")
df.groupBy("ciudad").count().show()

// 3. Leer archivos
println("\n📂 Leyendo archivos...")

// Si existe el archivo CSV
try {
  val dfCSV = spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv("work/data/input/ejemplo.csv")
  
  println("📄 Datos desde CSV:")
  dfCSV.show()
} catch {
  case e: Exception => println(s"⚠️ No se encontró archivo CSV: ${e.getMessage}")
}

// 4. SQL con Spark
df.createOrReplaceTempView("personas")
val result = spark.sql("""
  SELECT ciudad, AVG(edad) as edad_promedio, COUNT(*) as cantidad
  FROM personas
  GROUP BY ciudad
  ORDER BY edad_promedio DESC
""")

println("\n📊 Análisis SQL:")
result.show()

println("✅ ¡Spark funciona correctamente!")

// Limpiar
spark.stop()
