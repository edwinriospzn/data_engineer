#!/bin/bash

# ============================================
# CHECK PHYSICAL REPLICATION STATUS - FIXED
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "PHYSICAL REPLICATION STATUS"
echo "==========================================${NC}"

# Check if containers are running
if ! docker ps | grep -q zero_downtime_physical_primary; then
    echo -e "${RED}❌ Primary container is not running!${NC}"
    exit 1
fi

if ! docker ps | grep -q zero_downtime_physical_standby; then
    echo -e "${RED}❌ Standby container is not running!${NC}"
    exit 1
fi

# ============================================
# 1. Check primary status
# ============================================
echo -e "${BLUE}📊 PRIMARY STATUS:${NC}"
docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c "
    SELECT 
        'Primary' as role,
        current_database() as database,
        pg_is_in_recovery() as is_standby,
        pg_current_wal_lsn() as current_lsn,
        NOW() as timestamp;
"

echo
echo -e "${BLUE}📊 REPLICATION SENDER STATUS:${NC}"
docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c "
    SELECT 
        pid,
        usename,
        application_name,
        client_addr,
        state,
        sync_state,
        pg_wal_lsn_diff(sent_lsn, replay_lsn) as lag_bytes,
        pg_wal_lsn_diff(sent_lsn, replay_lsn) / 1024 / 1024 as lag_mb
    FROM pg_stat_replication;
"

# ============================================
# 2. Check standby status
# ============================================
echo
echo -e "${BLUE}📊 STANDBY STATUS:${NC}"
docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -c "
    SELECT 
        'Standby' as role,
        pg_is_in_recovery() as is_standby,
        pg_last_wal_receive_lsn() as receive_lsn,
        pg_last_wal_replay_lsn() as replay_lsn,
        pg_last_xact_replay_timestamp() as last_replay,
        NOW() - pg_last_xact_replay_timestamp() as replay_lag_interval
    WHERE pg_is_in_recovery();
"

# ============================================
# 3. Check replication slots
# ============================================
echo
echo -e "${BLUE}📊 REPLICATION SLOTS:${NC}"
docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c "
    SELECT 
        slot_name,
        slot_type,
        active,
        active_pid,
        pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) / 1024 / 1024 as wal_distance_mb
    FROM pg_replication_slots;
"

# ============================================
# 4. Check data consistency
# ============================================
echo
echo -e "${BLUE}📊 DATA CONSISTENCY:${NC}"

PRIMARY_COUNT=$(docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -t -c "SELECT COUNT(*) FROM employees;" 2>/dev/null | tr -d ' ')
STANDBY_COUNT=$(docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -t -c "SELECT COUNT(*) FROM employees;" 2>/dev/null | tr -d ' ')

if [ -n "$PRIMARY_COUNT" ] && [ -n "$STANDBY_COUNT" ]; then
    echo "  Primary rows: $PRIMARY_COUNT"
    echo "  Standby rows: $STANDBY_COUNT"
    
    if [ "$PRIMARY_COUNT" = "$STANDBY_COUNT" ]; then
        echo -e "  ${GREEN}✅ Row counts match!${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Row counts differ!${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  Could not get row counts (tables may not exist yet)${NC}"
fi

# ============================================
# 5. Show latest records
# ============================================
echo
echo -e "${BLUE}📊 LATEST RECORDS (Primary):${NC}"
docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c "
    SELECT id, name, department, salary, created_at 
    FROM employees 
    ORDER BY id DESC 
    LIMIT 3;
" 2>/dev/null || echo "  Table not found or empty"

echo
echo -e "${BLUE}📊 LATEST RECORDS (Standby):${NC}"
docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -c "
    SELECT id, name, department, salary, created_at 
    FROM employees 
    ORDER BY id DESC 
    LIMIT 3;
" 2>/dev/null || echo "  Table not found or empty"

echo
echo -e "${BLUE}=========================================="
echo -e "${GREEN}✅ Status check complete${NC}"