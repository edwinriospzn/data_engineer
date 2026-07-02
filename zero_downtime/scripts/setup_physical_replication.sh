#!/bin/bash

# ============================================
# PHYSICAL REPLICATION SETUP - FINAL CORRECTED
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "PHYSICAL REPLICATION SETUP"
echo "==========================================${NC}"

# ============================================
# 1. Check primary
# ============================================
echo -e "${BLUE}🔍 Checking primary...${NC}"
if ! docker ps | grep -q zero_downtime_physical_primary; then
    echo -e "${RED}❌ Primary is not running!${NC}"
    exit 1
fi

for i in {1..30}; do
    if docker exec zero_downtime_physical_primary pg_isready -U postgres -d physical_db > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Primary is ready${NC}"
        break
    fi
    sleep 2
done

# ============================================
# 2. Create replication user
# ============================================
echo -e "${BLUE}🔧 Creating replication user...${NC}"
docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c "
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'replica_user') THEN
            CREATE ROLE replica_user WITH LOGIN REPLICATION PASSWORD 'replica_password';
        END IF;
    END
    \$\$;
"

# ============================================
# 3. Configure pg_hba.conf
# ============================================
echo -e "${BLUE}🔧 Configuring pg_hba.conf...${NC}"
docker exec zero_downtime_physical_primary bash -c "
    if ! grep -q 'replica_user' /var/lib/postgresql/data/pg_hba.conf; then
        echo 'host    replication     replica_user     all                 md5' >> /var/lib/postgresql/data/pg_hba.conf
        echo 'host    all             all             all                 md5' >> /var/lib/postgresql/data/pg_hba.conf
    fi
"

docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c "SELECT pg_reload_conf();"

# ============================================
# 4. Create replication slot
# ============================================
echo -e "${BLUE}🔧 Creating replication slot...${NC}"
docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c "
    SELECT pg_create_physical_replication_slot('standby_slot', true);
" 2>/dev/null || echo "  Slot already exists"

# ============================================
# 5. Create employees table
# ============================================
echo -e "${BLUE}🔍 Creating employees table...${NC}"
docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c "
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        department VARCHAR(50),
        salary NUMERIC(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    INSERT INTO employees (name, department, salary)
    SELECT 
        'Employee ' || g,
        (ARRAY['Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'IT'])[floor(random() * 6 + 1)],
        ROUND((random() * 50000 + 40000)::numeric, 2)
    FROM generate_series(1, 100) g
    ON CONFLICT DO NOTHING;
    
    SELECT COUNT(*) as total FROM employees;
"

# ============================================
# 6. STOP standby FIRST (critical!)
# ============================================
echo -e "${BLUE}🛑 Stopping standby...${NC}"
docker stop zero_downtime_physical_standby 2>/dev/null
sleep 5  # Wait for container to fully stop

# ============================================
# 7. Clean data directory (while container is STOPPED)
# ============================================
echo -e "${BLUE}🗑️  Cleaning data directory...${NC}"
docker run --rm -v zero_downtime_physical_standby_data:/var/lib/postgresql/data alpine sh -c "find /var/lib/postgresql/data -mindepth 1 -maxdepth 1 -exec rm -rf {} + && echo '  Data directory cleaned'"
sleep 2

# ============================================
# 8. Take base backup into the standby volume
# ============================================
echo -e "${BLUE}📦 Taking base backup...${NC}"

docker run --rm --network physical_network --user postgres \
    -e PGPASSWORD=replica_password \
    -v zero_downtime_physical_standby_data:/var/lib/postgresql/data \
    postgres:17-alpine sh -c "find /var/lib/postgresql/data -mindepth 1 -maxdepth 1 -exec rm -rf {} + && pg_basebackup -h physical_primary -U replica_user -D /var/lib/postgresql/data -R --wal-method=stream"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Backup failed.${NC}"
    echo -e "${YELLOW}Try: ./stop_phy.sh → 2 (reset) then start fresh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backup complete${NC}"

# ============================================
# 10. Configure standby
# ============================================
echo -e "${BLUE}🔧 Configuring standby...${NC}"
docker exec zero_downtime_physical_standby bash -c "
    touch /var/lib/postgresql/data/standby.signal 2>/dev/null || true
    if ! grep -q 'primary_conninfo' /var/lib/postgresql/data/postgresql.auto.conf 2>/dev/null; then
        echo '' >> /var/lib/postgresql/data/postgresql.auto.conf
        echo \"primary_conninfo = 'host=physical_primary port=5432 user=replica_user password=replica_password'\" >> /var/lib/postgresql/data/postgresql.auto.conf
        echo \"primary_slot_name = 'standby_slot'\" >> /var/lib/postgresql/data/postgresql.auto.conf
    fi
" 2>/dev/null || true

docker exec zero_downtime_physical_standby chown -R postgres:postgres /var/lib/postgresql/data 2>/dev/null || true

# ============================================
# 11. Restart standby
# ============================================
echo -e "${BLUE}🔄 Restarting standby...${NC}"
docker restart zero_downtime_physical_standby

# ============================================
# 12. Wait for sync
# ============================================
echo -e "${BLUE}⏳ Waiting for standby to sync...${NC}"
for i in {1..30}; do
    if docker exec zero_downtime_physical_standby pg_isready -U postgres -d physical_db > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Standby is ready${NC}"
        break
    fi
    sleep 2
done

# ============================================
# 13. Verify
# ============================================
echo -e "${BLUE}📊 Verification:${NC}"

PRIMARY_COUNT=$(docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -t -c "SELECT COUNT(*) FROM employees;" 2>/dev/null | tr -d ' ')
echo "  Primary rows: $PRIMARY_COUNT"

sleep 5

STANDBY_COUNT=$(docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -t -c "SELECT COUNT(*) FROM employees;" 2>/dev/null | tr -d ' ')
echo "  Standby rows: $STANDBY_COUNT"

if [ "$PRIMARY_COUNT" = "$STANDBY_COUNT" ] && [ -n "$PRIMARY_COUNT" ]; then
    echo -e "  ${GREEN}✅ Replication working! Row counts match${NC}"
else
    echo -e "  ${YELLOW}⚠️  Replication may still be catching up...${NC}"
    echo -e "  ${YELLOW}   Run option 4 (Check status) in a few seconds${NC}"
fi

echo
echo -e "${GREEN}=========================================="
echo "✅ SETUP COMPLETE!"
echo "==========================================${NC}"
echo
echo -e "${BLUE}Connection details:${NC}"
echo "  Primary:  postgresql://postgres:postgres@localhost:5436/physical_db"
echo "  Standby:  postgresql://postgres:postgres@localhost:5437/physical_db"
echo
echo -e "${YELLOW}To test replication:${NC}"
echo "  docker exec zero_downtime_physical_primary psql -U postgres -d physical_db -c \"INSERT INTO employees (name, department, salary) VALUES ('Test', 'IT', 100000);\""
echo "  docker exec zero_downtime_physical_standby psql -U postgres -d physical_db -c \"SELECT COUNT(*) FROM employees;\""