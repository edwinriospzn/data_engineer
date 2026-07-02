#!/bin/bash

# ============================================
# PROMOTE PHYSICAL STANDBY TO PRIMARY (Failover)
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}=========================================="
echo "⚠️  PROMOTE STANDBY TO PRIMARY"
echo "==========================================${NC}"
echo -e "${RED}WARNING: This will make the standby writable!${NC}"
echo -e "${YELLOW}Only use during failover or maintenance!${NC}"
echo
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}Promotion cancelled${NC}"
    exit 0
fi

echo
echo -e "${BLUE}🔄 Promoting standby to primary...${NC}"

# ============================================
# 1. Check standby status
# ============================================
IS_STANDBY=$(docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -t -c "SELECT pg_is_in_recovery();" 2>/dev/null | tr -d ' ')

if [ "$IS_STANDBY" != "t" ]; then
    echo -e "${RED}❌ Server is already a primary!${NC}"
    exit 1
fi

# ============================================
# 2. Promote standby
# ============================================
echo -e "${BLUE}📢 Promoting...${NC}"
docker exec zero_downtime_physical_standby pg_ctl promote -D /var/lib/postgresql/data

echo -e "${GREEN}✅ Standby promoted to primary!${NC}"

# ============================================
# 3. Wait for promotion
# ============================================
sleep 5

# ============================================
# 4. Verify promotion
# ============================================
IS_STANDBY=$(docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -t -c "SELECT pg_is_in_recovery();" 2>/dev/null | tr -d ' ')

if [ "$IS_STANDBY" = "f" ]; then
    echo -e "${GREEN}✅ Promotion successful! Standby is now writable.${NC}"
else
    echo -e "${RED}❌ Promotion failed!${NC}"
    exit 1
fi

# ============================================
# 5. Show new status
# ============================================
echo
echo -e "${BLUE}📊 New primary status:${NC}"
docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -c "
    SELECT 
        'NEW PRIMARY' as role,
        current_database() as database,
        pg_is_in_recovery() as is_standby,
        pg_current_wal_lsn() as current_lsn;
"

echo
echo -e "${BLUE}=========================================="
echo -e "${GREEN}✅ Promotion complete!${NC}"
echo
echo -e "${YELLOW}New primary is now writable at:${NC}"
echo "  postgresql://postgres:postgres@localhost:5437/physical_db"
echo
echo -e "${YELLOW}To re-establish replication, you need to:${NC}"
echo "  1. Reconfigure the old primary as standby"
echo "  2. Run ./scripts/setup_physical_replication.sh again"
echo
echo -e "${BLUE}Current primary status:${NC}"
docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -c "
    SELECT 
        COUNT(*) as total_employees,
        MAX(created_at) as latest_record
    FROM employees;
"