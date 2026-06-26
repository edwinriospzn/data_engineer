#!/bin/bash
echo "🚀 Iniciando Pipeline Yahoo Finance"
docker compose down
docker compose build
docker compose up -d
sleep 10
echo "✅ Airflow UI: http://localhost:8090"
echo "   Usuario: airflow | Contraseña: airflow"
docker compose ps