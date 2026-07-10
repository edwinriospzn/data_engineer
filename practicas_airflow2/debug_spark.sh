#!/usr/bin/env bash
set -euo pipefail

# Change to the airflow-learning directory
cd "$(dirname "${BASH_SOURCE[0]}")/airflow-learning" || exit 1

# Set Docker socket path
if [ -z "${DOCKER_HOST:-}" ] && [ -S /var/run/docker.sock ]; then
  export DOCKER_HOST="unix:///var/run/docker.sock"
fi

# Create debug directory
mkdir -p ./debug_logs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="./debug_logs/spark_debug_${TIMESTAMP}.txt"

echo "🔍 Starting Spark Debug Collection..."
echo "========================================" | tee "$LOG_FILE"
echo "Spark Debug Logs - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 1. Check if containers are running
echo "📦 1. CONTAINER STATUS:" | tee -a "$LOG_FILE"
docker compose ps | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 2. Check if Spark is installed in webserver
echo "📦 2. CHECKING SPARK IN WEBSERVER:" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

echo "→ Checking if /opt/spark exists:" | tee -a "$LOG_FILE"
docker compose exec -T airflow-webserver ls -la /opt/spark 2>&1 | tee -a "$LOG_FILE" || echo "❌ /opt/spark NOT FOUND!" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "→ Checking spark-submit location:" | tee -a "$LOG_FILE"
docker compose exec -T airflow-webserver which spark-submit 2>&1 | tee -a "$LOG_FILE" || echo "❌ spark-submit NOT FOUND in PATH!" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "→ Checking Spark version:" | tee -a "$LOG_FILE"
docker compose exec -T airflow-webserver spark-submit --version 2>&1 | tee -a "$LOG_FILE" || echo "❌ spark-submit command failed!" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "→ Checking Java version:" | tee -a "$LOG_FILE"
docker compose exec -T airflow-webserver java -version 2>&1 | tee -a "$LOG_FILE" || echo "❌ Java not found!" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 3. Check environment variables
echo "🔧 3. ENVIRONMENT VARIABLES:" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

echo "→ SPARK_HOME:" | tee -a "$LOG_FILE"
docker compose exec -T airflow-webserver echo \$SPARK_HOME 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "→ JAVA_HOME:" | tee -a "$LOG_FILE"
docker compose exec -T airflow-webserver echo \$JAVA_HOME 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "→ PATH:" | tee -a "$LOG_FILE"
docker compose exec -T airflow-webserver echo \$PATH 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 4. Check Python packages
echo "🐍 4. PYTHON PACKAGES:" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
docker compose exec -T airflow-webserver pip list | grep -i spark | tee -a "$LOG_FILE" || echo "❌ PySpark not installed!" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 5. Check webserver logs for Spark errors
echo "📋 5. WEBSERVER LOGS (Spark errors):" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
docker compose logs --tail=100 airflow-webserver 2>&1 | grep -i "spark\|java\|error\|exception" | tee -a "$LOG_FILE" || echo "No Spark-related errors found" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 6. Check scheduler logs for Spark errors
echo "📋 6. SCHEDULER LOGS (Spark errors):" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
docker compose logs --tail=100 airflow-scheduler 2>&1 | grep -i "spark\|java\|error\|exception" | tee -a "$LOG_FILE" || echo "No Spark-related errors found" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 7. Check Docker image build details
echo "🖼️  7. DOCKER IMAGE INFO:" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
docker images | grep -E "airflow|spark" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 8. Test spark-submit with a simple command
echo "🧪 8. TESTING SPARK-SUBMIT:" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
docker compose exec -T airflow-webserver bash -c "spark-submit --version 2>&1 | head -5" | tee -a "$LOG_FILE" || echo "❌ spark-submit test failed!" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 9. Check if Dockerfile exists
echo "📄 9. DOCKERFILE CHECK:" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
if [ -f "./Dockerfile" ]; then
  echo "✅ Dockerfile exists" | tee -a "$LOG_FILE"
  echo "→ Content (first 20 lines):" | tee -a "$LOG_FILE"
  head -20 ./Dockerfile | tee -a "$LOG_FILE"
else
  echo "❌ Dockerfile NOT FOUND!" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# 10. Check docker-compose.yml for Spark config
echo "📝 10. DOCKER-COMPOSE SPARK CONFIG:" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
grep -A 5 -B 5 "SPARK_HOME\|JAVA_HOME\|build:" ./docker-compose.yml | tee -a "$LOG_FILE" || echo "No Spark config found in docker-compose.yml" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 11. Check disk space
echo "💾 11. DISK SPACE:" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
df -h | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "========================================" | tee -a "$LOG_FILE"
echo "✅ Debug collection complete!" | tee -a "$LOG_FILE"
echo "📄 Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
echo ""
echo "Quick summary of issues found:"
echo "----------------------------------------"
grep -i "❌\|error\|not found\|failed" "$LOG_FILE" | head -20 || echo "No obvious errors detected"