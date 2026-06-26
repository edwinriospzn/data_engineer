#!/bin/bash

# Set colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/edwin/Documents/Projects/zero_downtime"
cd "$PROJECT_DIR" || exit 1

echo -e "${BLUE}=========================================="
echo "NEAR-ZERO DOWNTIME MIGRATION LAB"
echo "==========================================${NC}"
echo

# Function to show menu
show_menu() {
    echo -e "${BLUE}Available commands:${NC}"
    echo "1. Start all services"
    echo "2. Stop all services"
    echo "3. Show logs"
    echo "4. Setup migration (replication)"
    echo "5. Validate data"
    echo "6. Run application simulator"
    echo "7. Monitor replication"
    echo "8. Simulate cutover"
    echo "9. Connect to source database"
    echo "10. Connect to target database"
    echo "11. Show container status"
    echo "12. Reset lab (remove all data)"
    echo "0. Exit"
    echo
    echo -n "Enter choice: "
}

# Start services
start_services() {
    echo -e "${BLUE}🚀 Starting services...${NC}"
    docker-compose up -d
    
    echo "⏳ Waiting for databases to be ready..."
    sleep 10
    
    echo -e "${GREEN}✅ Services started!${NC}"
    echo
    echo -e "${BLUE}Connection Information:${NC}"
    echo -e "  Source:  ${GREEN}postgresql://postgres:postgres@localhost:5434/sales${NC}"
    echo -e "  Target:  ${GREEN}postgresql://postgres:postgres@localhost:5435/sales${NC}"
    echo
}

# Stop services
stop_services() {
    echo -e "${BLUE}🛑 Stopping services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
}

# Show logs
show_logs() {
    echo -e "${BLUE}📋 Showing logs...${NC}"
    docker-compose logs --tail=50 -f
}

# Setup migration
setup_migration() {
    echo -e "${BLUE}🔄 Setting up migration...${NC}"
    python3 scripts/setup_migration.py
}

# Validate data
validate_data() {
    echo -e "${BLUE}🔍 Validating data...${NC}"
    python3 scripts/validate_data.py
}

# Run simulator
run_simulator() {
    echo -e "${BLUE}🚀 Running application simulator...${NC}"
    python3 scripts/app_simulator.py
}

# Monitor replication
monitor_replication() {
    echo -e "${BLUE}📊 Monitoring replication...${NC}"
    python3 scripts/monitor_replication.py
}

# Simulate cutover
simulate_cutover() {
    echo -e "${BLUE}✂️  Simulating cutover...${NC}"
    python3 scripts/simulate_cutover.py
}

# Connect to source
connect_source() {
    echo -e "${BLUE}🔗 Connecting to source database...${NC}"
    docker exec -it zero_downtime_source psql -U postgres -d sales
}

# Connect to target
connect_target() {
    echo -e "${BLUE}🔗 Connecting to target database...${NC}"
    docker exec -it zero_downtime_target psql -U postgres -d sales
}

# Show status
show_status() {
    echo -e "${BLUE}📊 Container Status:${NC}"
    docker-compose ps
    echo
    echo -e "${BLUE}📊 Volume Usage:${NC}"
    docker system df -v | grep -E "(zero_downtime|VOLUME)" || echo "No volumes found"
}

# Reset lab
reset_lab() {
    echo -e "${RED}⚠️  WARNING: This will delete all data!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        echo -e "${RED}🗑️  Resetting lab...${NC}"
        docker-compose down -v
        docker system prune -f
        echo -e "${GREEN}✅ Lab reset complete${NC}"
    else
        echo -e "${YELLOW}Reset cancelled${NC}"
    fi
}

# Main loop
while true; do
    show_menu
    read choice
    
    case $choice in
        1) start_services ;;
        2) stop_services ;;
        3) show_logs ;;
        4) setup_migration ;;
        5) validate_data ;;
        6) run_simulator ;;
        7) monitor_replication ;;
        8) simulate_cutover ;;
        9) connect_source ;;
        10) connect_target ;;
        11) show_status ;;
        12) reset_lab ;;
        0) 
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
    
    echo
    echo -e "${YELLOW}Press Enter to continue...${NC}"
    read
done