#!/bin/bash
#chmod +x stop.sh
echo "🛑 Deteniendo Pipeline Yahoo Finance"

# Detener contenedores y eliminar volúmenes
docker compose down -v

# Eliminar imagen personalizada (opcional, para rebuild completo)
docker rmi airflow-custom:latest 2>/dev/null || echo "⚠️  Imagen no encontrada"

echo "✅ Limpieza completa: contenedores, volúmenes e imagen eliminados"
echo "📌 Ejecuta ./start.sh para reconstruir todo desde cero"