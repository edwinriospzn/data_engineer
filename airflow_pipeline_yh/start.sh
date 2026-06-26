#!/bin/bash
echo "🚀 Iniciando Pipeline Yahoo Finance"

# ============================================
# 1. Crear carpetas y dar permisos
# ============================================
mkdir -p logs dags scripts plugins data
sudo chmod -R 777 logs/ 2>/dev/null || true

# ============================================
# 2. Limpiar contenedores anteriores
# ============================================
echo "🧹 Limpiando contenedores anteriores..."
docker compose down -v 2>/dev/null || true

# ============================================
# 3. Levantar SOLO bases de datos
# ============================================
echo "🚀 Levantando PostgreSQL y Redis..."
docker compose up -d postgres redis

echo "⏳ Esperando 15 segundos para que las bases de datos estén listas..."
sleep 15

# ============================================
# 4. Inicializar base de datos (ANTES de los workers)
# ============================================
echo "🔄 Inicializando base de datos de Airflow..."
docker compose run --rm -T airflow-webserver airflow db init

# ============================================
# 5. Crear usuario admin (ANTES de los workers)
# ============================================
echo "👤 Creando usuario admin..."
docker compose run --rm -T airflow-webserver airflow users create \
    --username admin \
    --password admin123 \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com 2>/dev/null || echo "⚠️  Usuario ya existe"

# ============================================
# 6. Verificar usuario en DB
# ============================================
echo "🔍 Verificando usuario en base de datos..."
docker compose exec -T postgres psql -U airflow -d airflow -c "SELECT id, username, email FROM ab_user;"

# ============================================
# 7. Ahora sí, levantar todos los servicios de Airflow
# ============================================
echo "🚀 Levantando Airflow (webserver, scheduler, workers)..."
docker compose up -d

echo "⏳ Esperando 20 segundos para que Airflow esté listo..."
sleep 20

# ============================================
# 8. Verificar que el scheduler esté saludable
# ============================================
echo "🔍 Verificando estado del scheduler..."
SCHEDULER_RETRY=0
while [ $SCHEDULER_RETRY -lt 10 ]; do
    HEALTH=$(docker compose exec -T airflow-webserver curl -s http://localhost:8080/health 2>/dev/null)
    if echo "$HEALTH" | grep -q '"scheduler".*"status": "healthy"'; then
        echo "✅ Scheduler está saludable"
        break
    fi
    echo "⏳ Esperando scheduler... (intento $((SCHEDULER_RETRY+1))/10)"
    sleep 5
    SCHEDULER_RETRY=$((SCHEDULER_RETRY+1))
done

if [ $SCHEDULER_RETRY -eq 10 ]; then
    echo "⚠️  Scheduler no respondió. Puedes verificar con: docker compose logs airflow-scheduler"
fi

# ============================================
# 9. Test de conexión final
# ============================================
echo "🔍 Verificando conexión a Airflow..."

MAX_RETRIES=12
RETRY=0
HTTP_CODE="000"

while [ $RETRY -lt $MAX_RETRIES ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8090/health 2>/dev/null)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Airflow respondiendo correctamente (HTTP $HTTP_CODE)"
        break
    fi
    
    RETRY=$((RETRY+1))
    echo "⏳ Esperando que Airflow responda... (intento $RETRY/$MAX_RETRIES)"
    sleep 5
done

if [ "$HTTP_CODE" != "200" ]; then
    echo "⚠️  No se pudo conectar a Airflow. Verifica logs:"
    echo "   docker compose logs airflow-webserver --tail 30"
fi

# ============================================
# 10. Mostrar información final
# ============================================
echo ""
echo "=========================================="
echo "✅ Pipeline Yahoo Finance listo!"
echo "=========================================="
echo ""
echo "   🌐 Airflow UI: http://localhost:8090"
echo "      (Si no carga, prueba con: http://127.0.0.1:8090)"
echo ""
echo "   👤 Usuario: admin"
echo "   🔑 Contraseña: admin123"
echo ""
echo "   📊 PostgreSQL: localhost:5455"
echo "   🔴 Redis: localhost:6390"
echo ""
echo "   📝 Ver logs: docker compose logs -f"
echo "   🛑 Detener: ./stop.sh"
echo ""
echo "=========================================="
docker compose ps