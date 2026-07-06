#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/airflow-learning" && pwd)"
cd "$ROOT_DIR"

if [ -z "${DOCKER_HOST:-}" ] && [ -S /var/run/docker.sock ]; then
  export DOCKER_HOST="unix:///var/run/docker.sock"
fi

docker compose down --remove-orphans --volumes

echo "All practice containers and volumes have been stopped and removed."
