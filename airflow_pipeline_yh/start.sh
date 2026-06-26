#!/bin/bash
echo "🚀 Iniciando Pipeline Yahoo Finance"

# ============================================
# 1. Crear carpetas y dar permisos
# ============================================
mkdir -p logs dags scripts plugins data
sudo chmod -R 777 logs/ 2>/dev/null || true

# ============================================
# 2. Detener contenedores anteriores
# ============================================
echo "🧹 Limpiando contenedores anteriores..."
docker compose down -v 2>/dev/null || true

# ============================================
# 3. Levantar servicios
# ============================================
echo "🚀 Levantando contenedores..."
docker compose up -d --build

echo "⏳ Esperando 20 segundos para que PostgreSQL y Airflow estén listos..."
sleep 20

# ============================================
# 4. Inicializar base de datos
# ============================================
echo "🔄 Inicializando base de datos..."
docker compose exec -T airflow-webserver airflow db init 2>/dev/null || \
docker compose run --rm -T airflow-webserver airflow db init

# ============================================
# 5. Verificar que el webserver esté corriendo
# ============================================
echo "🔍 Verificando que el webserver esté corriendo..."
RETRY=0
while [ $RETRY -lt 10 ]; do
    if docker compose exec -T airflow-webserver airflow info &>/dev/null; then
        echo "✅ Webserver está corriendo"
        break
    fi
    echo "⏳ Esperando webserver... (intento $((RETRY+1))/10)"
    sleep 5
    RETRY=$((RETRY+1))
done

# ============================================
# 6. Crear usuario admin
# ============================================
echo "👤 Creando usuario admin..."

docker compose exec -T airflow-webserver airflow users create \
    --username admin \
    --password admin123 \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com 2>/dev/null || \
docker compose run --rm -T airflow-webserver airflow users create \
    --username admin \
    --password admin123 \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# ============================================
# 7. Verificar usuario en DB
# ============================================
echo "🔍 Verificando usuario en base de datos..."
USER_EXISTS=$(docker compose exec -T postgres psql -U airflow -d airflow -t -c "SELECT COUNT(*) FROM ab_user WHERE username = 'admin';" 2>/dev/null | tr -d ' ')

if [ "$USER_EXISTS" = "1" ]; then
    echo "✅ Usuario admin verificado correctamente"
else
    echo "❌ ERROR: Usuario admin NO se creó."
fi

echo "📋 Usuarios en la base de datos:"
docker compose exec -T postgres psql -U airflow -d airflow -c "SELECT id, username, email FROM ab_user;"

# ============================================
# 8. Reiniciar webserver
# ============================================
echo "🔄 Reiniciando webserver para aplicar cambios..."
docker compose restart airflow-webserver

echo "⏳ Esperando 15 segundos para que el webserver reinicie..."
sleep 15

# ============================================
# 9. Esperar a que el scheduler esté saludable (¡NUEVO!)
# ============================================
echo "⏳ Esperando que el scheduler esté saludable..."
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
# 10. Test de conexión final
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
# 11. Mostrar información final
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