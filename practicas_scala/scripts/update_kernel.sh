#!/bin/bash
# scripts/update_kernel.sh
# Script para actualizar el kernel.json desde el archivo local

echo "⚙️ Actualizando kernel.json..."

# Verificar que el contenedor está corriendo
if ! docker ps | grep -q spark-scala-practicas; then
    echo "❌ El contenedor spark-scala-practicas no está corriendo"
    echo "📝 Ejecuta primero: docker compose up -d"
    exit 1
fi

# Crear el directorio si no existe
docker exec -it --user jovyan spark-scala-practicas /bin/bash -c "
mkdir -p /home/jovyan/.local/share/jupyter/kernels/scala
"

# Copiar la configuración desde el archivo local (docker/kernel/kernel.json)
docker exec -it --user jovyan spark-scala-practicas /bin/bash -c "
cat > /home/jovyan/.local/share/jupyter/kernels/scala/kernel.json << 'EOF'
{
  \"display_name\": \"Scala-Spark\",
  \"language\": \"scala\",
  \"argv\": [
    \"java\",
    \"-jar\",
    \"/home/jovyan/.local/share/jupyter/kernels/scala/launcher.jar\",
    \"--connection-file\",
    \"{connection_file}\"
  ],
  \"env\": {
    \"JAVA_OPTS\": \"--add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED\",
    \"SPARK_OPTS\": \"--add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED\"
  }
}
EOF
"

echo "✅ kernel.json actualizado"

# Reiniciar Jupyter
echo "🔄 Reiniciando Jupyter Lab..."
docker compose restart spark-scala-notebook

echo "✅ Configuración aplicada"