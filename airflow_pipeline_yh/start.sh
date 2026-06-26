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
# 6. Crear usuario admin (con webserver)
# ============================================
echo "👤 Creando usuario admin..."

# Crear usuario con el webserver (que sí está corriendo)
docker compose exec -T airflow-webserver airflow users create \
    --username admin \
    --password admin123 \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# ============================================
# 7. Verificar que el usuario se creó
# ============================================
echo "🔍 Verificando usuario en base de datos..."

USER_EXISTS=$(docker compose exec -T postgres psql -U airflow -d airflow -t -c "SELECT COUNT(*) FROM ab_user WHERE username = 'admin';" 2>/dev/null | tr -d ' ')

if [ "$USER_EXISTS" = "1" ]; then
    echo "✅ Usuario admin verificado correctamente"
else
    echo "❌ ERROR: Usuario admin NO se creó. Intentando método alternativo..."
    
    # Método alternativo: directo con psql
    docker compose exec -T postgres psql -U airflow -d airflow <<EOF
INSERT INTO ab_user (username, password, email, first_name, last_name, active, created_on, changed_on)
VALUES (
    'admin',
    'pbkdf2:sha256:600000\$fUFeNXVOVkH5Fc5WkHjqTA\$6Q1zWlYQ9VpFVn8g6Ok3vHjWlXkVCpH9j3cF7NnKjP0',
    'admin@example.com',
    'Admin',
    'User',
    true,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;
EOF

    # Asignar rol Admin
    docker compose exec -T postgres psql -U airflow -d airflow <<EOF
INSERT INTO ab_user_role (user_id, role_id)
SELECT u.id, r.id 
FROM ab_user u, ab_role r 
WHERE u.username = 'admin' AND r.name = 'Admin'
ON CONFLICT DO NOTHING;
EOF
fi

# ============================================
# 8. Mostrar usuarios
# ============================================
echo "📋 Usuarios en la base de datos:"
docker compose exec -T postgres psql -U airflow -d airflow -c "SELECT id, username, email FROM ab_user;"

# ============================================
# 9. Reiniciar webserver
# ============================================
echo "🔄 Reiniciando webserver para aplicar cambios..."
docker compose restart airflow-webserver

echo "⏳ Esperando 15 segundos para que el webserver reinicie..."
sleep 15

# ============================================
# 10. Test de conexión
# ============================================
echo "🔍 Verificando conexión a Airflow..."

MAX_RETRIES=12
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
# 11. Mostrar información final
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
echo "   📊 PostgreSQL: localhost:5455"
echo "   🔴 Redis: localhost:6390"
echo ""
echo "   📝 Ver logs: docker compose logs -f"
echo "   🛑 Detener: ./stop.sh"
echo ""
echo "=========================================="
docker compose ps