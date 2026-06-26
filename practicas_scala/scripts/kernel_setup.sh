#!/bin/bash
# scripts/kernel_setup.sh
# Script para instalar y configurar el kernel Scala en el contenedor

echo "🔧 Configurando kernel Scala-Spark..."

# Verificar que el contenedor está corriendo
if ! docker ps | grep -q spark-scala-practicas; then
    echo "❌ El contenedor spark-scala-practicas no está corriendo"
    echo "📝 Ejecuta primero: docker compose up -d"
    exit 1
fi

# 1. Instalar coursier
echo "📦 Instalando coursier..."
docker exec -it --user jovyan spark-scala-practicas /bin/bash -c "
mkdir -p /home/jovyan/.local/bin
curl -Lo /home/jovyan/.local/bin/coursier https://git.io/coursier-cli
chmod +x /home/jovyan/.local/bin/coursier
/home/jovyan/.local/bin/coursier --version
"

# 2. Eliminar kernel existente si hay
echo "🗑️ Eliminando kernel anterior..."
docker exec -it --user jovyan spark-scala-practicas /bin/bash -c "
rm -rf /home/jovyan/.local/share/jupyter/kernels/scala
"

# 3. Instalar Almond (SIN argumentos --scala)
echo "📦 Instalando kernel Scala..."
docker exec -it --user jovyan spark-scala-practicas /bin/bash -c "
export PATH=/home/jovyan/.local/bin:\$PATH
/home/jovyan/.local/bin/coursier launch almond:0.13.3 -- --install
"

# 4. Crear el directorio del kernel
echo "📁 Creando directorio del kernel..."
docker exec -it --user jovyan spark-scala-practicas /bin/bash -c "
mkdir -p /home/jovyan/.local/share/jupyter/kernels/scala
"

# 5. Configurar el kernel.json
echo "⚙️ Configurando kernel.json..."
docker exec -it --user jovyan spark-scala-practicas /bin/bash -c "
cat > /home/jovyan/.local/share/jupyter/kernels/scala/kernel.json << 'EOF'
{
  \"display_name\": \"Scala-Spark (Java 17)\",
  \"language\": \"scala\",
  \"argv\": [
    \"/home/jovyan/.local/bin/coursier\",
    \"launch\",
    \"almond:0.13.3\",
    \"--connection-file\",
    \"{connection_file}\"
  ],
  \"env\": {
    \"JAVA_OPTS\": \"--add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED\",
    \"SPARK_OPTS\": \"--add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED\",
    \"PATH\": \"/home/jovyan/.local/bin:/usr/local/bin:/usr/bin:/bin\"
  }
}
EOF
"

# 6. Verificar
echo "✅ Verificando instalación..."
docker exec -it --user jovyan spark-scala-practicas /bin/bash -c "
jupyter kernelspec list
cat /home/jovyan/.local/share/jupyter/kernels/scala/kernel.json
"

# 7. Reiniciar Jupyter
echo "🔄 Reiniciando Jupyter Lab..."
docker compose restart spark-scala-notebook

echo ""
echo "✅ Kernel configurado exitosamente"
echo "📊 Accede a: http://localhost:8888"
echo "🔑 Token: practicas123"
echo "📝 Crea un notebook y selecciona 'Scala-Spark (Java 17)'"