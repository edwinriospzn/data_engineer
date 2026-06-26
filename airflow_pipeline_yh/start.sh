#!/bin/bash
echo "🚀 Iniciando Pipeline Yahoo Finance"

# ============================================
# 1. Crear carpetas y dar permisos
# ============================================
mkdir -p logs dags scripts plugins data
sudo chmod -R 777 logs/ 2>/dev/null || true

# ============================================
# 2. Detener contenedores anteriores (limpieza)
# ============================================
echo "🧹 Limpiando contenedores anteriores..."
docker compose down -v 2>/dev/null || true

# ============================================
# 3. Levantar servicios (postgres, redis, airflow)
# ============================================
echo "🚀 Levantando contenedores..."
docker compose up -d --build

echo "⏳ Esperando 15 segundos para que PostgreSQL esté listo..."
sleep 15

# ============================================
# 4. Inicializar base de datos de Airflow
# ============================================
echo "🔄 Inicializando base de datos..."
docker compose exec -T airflow-webserver airflow db init 2>/dev/null || \
docker compose exec -T airflow-scheduler airflow db init 2>/dev/null || \
docker compose run --rm -T airflow-webserver airflow db init

# ============================================
# 5. Crear usuario admin (con validación)
# ============================================
echo "👤 Creando usuario admin..."

# Verificar si el usuario ya existe
USER_EXISTS=$(docker compose exec -T postgres psql -U airflow -d airflow -t -c "SELECT COUNT(*) FROM ab_user WHERE username = 'admin';" 2>/dev/null | tr -d ' ')

if [ "$USER_EXISTS" = "0" ] || [ -z "$USER_EXISTS" ]; then
    echo "   ✅ Creando usuario admin..."
    docker compose exec -T airflow-webserver airflow users create \
        --username admin \
        --password admin123 \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com 2>/dev/null || \
    docker compose exec -T airflow-scheduler airflow users create \
        --username admin \
        --password admin123 \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com
else
    echo "   ⚠️  Usuario admin ya existe. Verificando..."
fi

# ============================================
# 6. Verificar que el usuario se creó
# ============================================
echo "🔍 Verificando usuario en base de datos..."
USER_CHECK=$(docker compose exec -T postgres psql -U airflow -d airflow -t -c "SELECT COUNT(*) FROM ab_user WHERE username = 'admin';" 2>/dev/null | tr -d ' ')

if [ "$USER_CHECK" = "1" ]; then
    echo "   ✅ Usuario admin verificado correctamente"
    
    # Verificar rol
    ROLE_CHECK=$(docker compose exec -T postgres psql -U airflow -d airflow -t -c "
        SELECT COUNT(*) FROM ab_user_role ur
        JOIN ab_user u ON u.id = ur.user_id
        JOIN ab_role r ON r.id = ur.role_id
        WHERE u.username = 'admin' AND r.name = 'Admin';
    " 2>/dev/null | tr -d ' ')
    
    if [ "$ROLE_CHECK" != "1" ]; then
        echo "   ⚠️  Rol Admin no asignado. Asignando..."
        docker compose exec -T postgres psql -U airflow -d airflow -c "
            INSERT INTO ab_user_role (user_id, role_id)
            SELECT u.id, r.id 
            FROM ab_user u, ab_role r 
            WHERE u.username = 'admin' AND r.name = 'Admin'
            ON CONFLICT DO NOTHING;
        "
    fi
else
    echo "   ❌ ERROR: Usuario admin NO se creó correctamente"
    echo "   🔄 Intentando crear usuario con método alternativo..."
    
    # Método alternativo: usar scheduler
    docker compose exec -T airflow-scheduler airflow users create \
        --username admin \
        --password admin123 \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com 2>/dev/null || \
    docker compose exec -T postgres psql -U airflow -d airflow -c "
        INSERT INTO ab_user (username, password, email, first_name, last_name, active, created_on, changed_on, _password)
        VALUES ('admin', 'pbkdf2:sha256:600000\$fUFeNXVOVkH5Fc5WkHjqTA\$6Q1zWlYQ9VpFVn8g6Ok3vHjWlXkVCpH9j3cF7NnKjP0', 'admin@example.com', 'Admin', 'User', true, NOW(), NOW(), 'admin123')
        ON CONFLICT (username) DO NOTHING;
    "
fi

# ============================================
# 7. Mostrar usuarios en la base de datos
# ============================================
echo "📋 Usuarios en la base de datos:"
docker compose exec -T postgres psql -U airflow -d airflow -c "SELECT id, username, email FROM ab_user;"

# ============================================
# 8. Reiniciar webserver para tomar cambios
# ============================================
echo "🔄 Reiniciando webserver..."
docker compose restart airflow-webserver

echo "⏳ Esperando 15 segundos para que el webserver inicie..."
sleep 15

# ============================================
# 9. Test de conexión
# ============================================
echo "🔍 Verificando conexión..."

MAX_RETRIES=15
RETRY=0
HTTP_CODE="000"

while [ $RETRY -lt $MAX_RETRIES ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/health 2>/dev/null)
    
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
# 10. Mostrar información
# ============================================
echo ""
echo "=========================================="
echo "✅ Pipeline Yahoo Finance listo!"
echo "=========================================="
echo ""
echo "   🌐 Airflow UI: http://localhost:8090"
echo "   👤 Usuario: admin"
echo "   🔑 Contraseña: admin123"
echo ""
echo "   📊 PostgreSQL: localhost:5455 (usuario: airflow, password: airflow)"
echo "   🔴 Redis: localhost:6390"
echo ""
echo "   📝 Ver logs: docker compose logs -f"
echo "   🛑 Detener: ./stop.sh"
echo ""
echo "=========================================="
docker compose ps