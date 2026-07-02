#!/bin/bash

# ============================================
# PHYSICAL REPLICATION LAB - LAUNCHER
# Separate from logical replication lab
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}=========================================="
echo "PHYSICAL REPLICATION LAB"
echo "==========================================${NC}"
echo

# ============================================
# FUNCTIONS
# ============================================

start_physical() {
    echo -e "${BLUE}🚀 Starting physical services...${NC}"
    docker compose -f docker-compose.physical.yml up -d
    
    echo -e "${BLUE}⏳ Waiting for databases to be ready...${NC}"
    sleep 10
    
    echo -e "${GREEN}✅ Physical services started${NC}"
    echo
    echo -e "${BLUE}Connection details:${NC}"
    echo "  Primary:  postgresql://postgres:postgres@localhost:5436/physical_db"
    echo "  Standby:  postgresql://postgres:postgres@localhost:5437/physical_db"
    echo
    echo -e "${YELLOW}Next step: Run option 3 to setup replication${NC}"
}

stop_physical() {
    echo -e "${BLUE}🛑 Stopping physical services...${NC}"
    docker compose -f docker-compose.physical.yml down
    echo -e "${GREEN}✅ Physical services stopped${NC}"
}

setup_replication() {
    echo -e "${BLUE}🔄 Setting up physical replication...${NC}"
    chmod +x scripts/setup_physical_replication.sh
    ./scripts/setup_physical_replication.sh
}

check_status() {
    echo -e "${BLUE}📊 Checking physical replication status...${NC}"
    chmod +x scripts/check_physical_status.sh
    ./scripts/check_physical_status.sh
}

promote_standby() {
    echo -e "${BLUE}🔄 Promoting physical standby...${NC}"
    chmod +x scripts/promote_physical_standby.sh
    ./scripts/promote_physical_standby.sh
}

connect_primary() {
    echo -e "${BLUE}🔗 Connecting to physical primary...${NC}"
    docker exec -it zero_downtime_physical_primary psql -U postgres -d physical_db
}

connect_standby() {
    echo -e "${BLUE}🔗 Connecting to physical standby...${NC}"
    docker exec -it zero_downtime_physical_standby psql -U postgres -d physical_db
}

test_replication() {
    echo -e "${BLUE}🧪 Testing physical replication...${NC}"
    echo
    
    echo "Inserting test data on primary..."
    docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c "
        INSERT INTO employees (name, department, salary) 
        VALUES ('Physical Replication Test', 'QA', 99999.99);
    "
    
    echo "Waiting for replication..."
    sleep 3
    
    echo "Checking standby..."
    docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -c "
        SELECT COUNT(*) as total_employees,
               MAX(name) as latest_name,
               MAX(created_at) as latest_record
        FROM employees;
    "
    
    echo -e "${GREEN}✅ Physical replication test complete${NC}"
}

show_logs() {
    echo -e "${BLUE}📋 Showing logs...${NC}"
    docker compose -f docker-compose.physical.yml logs --tail=50 -f
}

reset_physical() {
    echo -e "${RED}⚠️  WARNING: This will delete all physical data!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        echo -e "${RED}🗑️  Resetting physical lab...${NC}"
        docker compose -f docker-compose.physical.yml down -v
        echo -e "${GREEN}✅ Physical lab reset complete${NC}"
    else
        echo -e "${YELLOW}Reset cancelled${NC}"
    fi
}

# ============================================
# MENU
# ============================================

show_menu() {
    echo -e "${BLUE}┌─────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}│      PHYSICAL REPLICATION LAB           │${NC}"
    echo -e "${BLUE}├─────────────────────────────────────────┤${NC}"
    echo -e "${BLUE}│  1. Start services                      │${NC}"
    echo -e "${BLUE}│  2. Stop services                       │${NC}"
    echo -e "${BLUE}│  3. Setup replication (FIRST TIME)      │${NC}"
    echo -e "${BLUE}│  4. Check status                        │${NC}"
    echo -e "${BLUE}│  5. Test replication                    │${NC}"
    echo -e "${BLUE}│  6. Connect to primary                  │${NC}"
    echo -e "${BLUE}│  7. Connect to standby                  │${NC}"
    echo -e "${BLUE}│  8. Promote standby (FAILOVER)          │${NC}"
    echo -e "${BLUE}│  9. Show logs                           │${NC}"
    echo -e "${BLUE}│  10. Reset lab (delete all data)        │${NC}"
    echo -e "${BLUE}│  0. Exit                                │${NC}"
    echo -e "${BLUE}└─────────────────────────────────────────┘${NC}"
    echo
    echo -n "Enter choice: "
}

# ============================================
# MAIN LOOP
# ============================================

while true; do
    show_menu
    read choice
    
    case $choice in
        1) start_physical ;;
        2) stop_physical ;;
        3) setup_replication ;;
        4) check_status ;;
        5) test_replication ;;
        6) connect_primary ;;
        7) connect_standby ;;
        8) promote_standby ;;
        9) show_logs ;;
        10) reset_physical ;;
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