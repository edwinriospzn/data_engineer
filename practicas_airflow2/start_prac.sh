#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/airflow-learning" && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not available in PATH." >&2
  exit 1
fi

if [ -z "${DOCKER_HOST:-}" ] && [ -S /var/run/docker.sock ]; then
  export DOCKER_HOST="unix:///var/run/docker.sock"
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not reachable. Make sure Docker is running and the socket is available." >&2
  exit 1
fi

mkdir -p "$ROOT_DIR"/logs "$ROOT_DIR"/plugins "$ROOT_DIR"/dags "$ROOT_DIR"/data "$ROOT_DIR"/sql "$ROOT_DIR"/spark

docker compose up -d postgres etl-postgres pgadmin airflow-init airflow-webserver airflow-scheduler python-dev

echo ""
echo "Airflow UI: http://localhost:8080"
echo "pgAdmin: http://localhost:5050"
echo "Default Airflow login: admin / admin"
echo "pgAdmin login: admin@example.com / admin"
