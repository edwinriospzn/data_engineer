#!/usr/bin/env bash
set -euo pipefail

# Change to the airflow-learning directory where docker-compose.yml is
cd "$(dirname "${BASH_SOURCE[0]}")/airflow-learning" || exit 1

# Set Docker socket path (fix for Docker Desktop)
export DOCKER_HOST="unix:///var/run/docker.sock"

echo "🔧 Setting up Airflow connections..."

# Add fs_default connection for 05
docker compose exec -T airflow-webserver airflow connections add 'fs_default' \
    --conn-type 'fs' \
    --conn-extra '{"path": "/opt/airflow"}' 2>/dev/null || echo "✅ fs_default already exists"

# Verify it was added
echo ""
echo "📋 Verifying connections:"
docker compose exec -T airflow-webserver airflow connections list | grep fs_default || echo "❌ fs_default not found!"

echo ""
echo "✅ Connections configured:"
echo "   - fs_default (FileSensor)"