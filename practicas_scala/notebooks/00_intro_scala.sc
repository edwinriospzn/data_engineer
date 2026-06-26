// 📘 Introducción a Scala
// Este es un notebook de Scala para practicar

println("¡Hola Mundo desde Scala!")

// 1. Variables y tipos básicos
val nombre: String = "Scala"
var edad: Int = 10
val pi: Double = 3.14159

println(s"Nombre: $nombre, Edad: $edad, PI: $pi")

// 2. Estructuras de datos
val lista = List(1, 2, 3, 4, 5)
val mapa = Map("uno" -> 1, "dos" -> 2, "tres" -> 3)

println(s"Lista: $lista")
println(s"Mapa: $mapa")

// 3. Funciones
def suma(a: Int, b: Int): Int = a + b
println(s"Suma de 5 y 3: ${suma(5, 3)}")

// 4. Clases y case classes
case class Persona(nombre: String, edad: Int)
val persona = Persona("Ana", 25)
println(s"Persona: $persona")

// 5. Colecciones funcionales
val numeros = List(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
val pares = numeros.filter(_ % 2 == 0)
val cuadrados = numeros.map(n => n * n)

println(s"Números originales: $numeros")
println(s"Números pares: $pares")
println(s"Cuadrados: $cuadrados")

println("✅ ¡Scala funciona correctamente!")
