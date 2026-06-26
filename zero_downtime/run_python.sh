#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/home/edwin/Documents/Projects/zero_downtime"
cd "$PROJECT_DIR" || exit 1

echo -e "${BLUE}=========================================="
echo "PYTHON CONTAINER RUNNER"
echo "==========================================${NC}"

# Check if containers are running
if ! docker ps | grep -q zero_downtime_source; then
    echo -e "${YELLOW}⚠️  Databases not running. Starting them...${NC}"
    docker compose up -d source target redis
    echo -e "${BLUE}⏳ Waiting for databases...${NC}"
    sleep 10
fi

# Build the Python container if needed
if ! docker images | grep -q zero_downtime-python-runner; then
    echo -e "${BLUE}🔨 Building Python container...${NC}"
    docker compose --profile python build python-runner
fi

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./run_python.sh <script.py> [arguments]"
    echo ""
    echo -e "${BLUE}Available scripts:${NC}"
    echo "  setup_migration.py      - Setup replication"
    echo "  validate_data.py        - Validate data consistency"
    echo "  monitor_replication.py  - Monitor replication"
    echo "  simulate_cutover.py     - Simulate cutover"
    echo "  app_simulator.py        - Run application simulator"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  ./run_python.sh setup_migration.py"
    echo "  ./run_python.sh validate_data.py"
    echo "  ./run_python.sh monitor_replication.py"
    echo ""
    echo -e "${BLUE}Start interactive shell:${NC}"
    echo "  docker compose --profile python run --rm python-runner /bin/bash"
    exit 0
fi

# Run the script
echo -e "${BLUE}🐍 Running: $@${NC}"
echo -e "${YELLOW}──────────────────────────────────────────${NC}"

docker compose --profile python run --rm python-runner python /app/scripts/"$@"

EXIT_CODE=$?

echo -e "${YELLOW}──────────────────────────────────────────${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Script completed successfully${NC}"
else
    echo -e "${RED}❌ Script exited with code: $EXIT_CODE${NC}"
fi

exit $EXIT_CODE