#!/usr/bin/env python3
import psycopg2
import time
import sys
from db_config import SOURCE_CONFIG, TARGET_CONFIG, get_connection

class MigrationSetup:
    def __init__(self):
        self.source_conn = get_connection(SOURCE_CONFIG)
        self.target_conn = get_connection(TARGET_CONFIG)
        self.source_conn.autocommit = True
        self.target_conn.autocommit = True
        
    def setup_replication(self):
        print("🔄 Setting up logical replication...")
        print(f"Source: {SOURCE_CONFIG.host}:{SOURCE_CONFIG.port}")
        print(f"Target: {TARGET_CONFIG.host}:{TARGET_CONFIG.port}")
        print()
        
        # Check if tables exist
        with self.source_conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'orders'
                )
            """)
            if not cur.fetchone()[0]:
                print("❌ Source table 'orders' does not exist!")
                print("Please ensure the initialization script ran successfully.")
                return False
        
        # Create publication on source
        with self.source_conn.cursor() as cur:
            print("  - Creating publication on source...")
            cur.execute("DROP PUBLICATION IF EXISTS sales_pub")
            cur.execute("CREATE PUBLICATION sales_pub FOR TABLE orders")
            print("    ✅ Publication created")
        
        # Create table on target if not exists
        with self.target_conn.cursor() as cur:
            print("  - Ensuring target table exists...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id SERIAL PRIMARY KEY,
                    customer_name TEXT,
                    amount NUMERIC(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("    ✅ Target table ready")
        
        # Create subscription on target
        with self.target_conn.cursor() as cur:
            print("  - Creating subscription on target...")
            try:
                cur.execute("DROP SUBSCRIPTION IF EXISTS sales_sub")
                cur.execute("""
                    CREATE SUBSCRIPTION sales_sub
                    CONNECTION 'host=zero_downtime_source port=5432 dbname=sales user=postgres password=postgres'
                    PUBLICATION sales_pub
                    WITH (copy_data = true, create_slot = true, enabled = true)
                """)
                print("    ✅ Subscription created")
            except psycopg2.Error as e:
                print(f"    ❌ Error creating subscription: {e}")
                return False
        
        print("✅ Replication setup completed!")
        
        # Wait for initial sync
        print("⏳ Waiting for initial data sync...")
        time.sleep(5)
        
        # Check sync status
        self.check_sync_status()
        return True
        
    def check_sync_status(self):
        with self.source_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders")
            source_count = cur.fetchone()[0]
        
        with self.target_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders")
            target_count = cur.fetchone()[0]
        
        print(f"\n📊 Sync Status:")
        print(f"  Source: {source_count:,} rows")
        print(f"  Target: {target_count:,} rows")
        
        if source_count == target_count:
            print("  ✅ Initial sync complete!")
        else:
            print(f"  ⚠️  Sync in progress... {target_count:,}/{source_count:,} rows")
        
        # Check subscription status - CORRECTED for PostgreSQL 17
        with self.target_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    subname,
                    subenabled,
                    subslotname
                FROM pg_subscription
            """)
            subscriptions = cur.fetchall()
            if subscriptions:
                print("\n📋 Subscription Status:")
                for sub in subscriptions:
                    print(f"  - {sub[0]}: Enabled={sub[1]}, Slot={sub[2]}")
        
        return source_count, target_count
    
    def insert_test_data(self, num_rows=100):
        """Insert additional data to test replication"""
        print(f"\n📝 Inserting {num_rows} test rows on source...")
        
        with self.source_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders (customer_name, amount)
                SELECT 
                    'Test Customer ' || generate_series,
                    ROUND((random()*1000)::numeric, 2)
                FROM generate_series(1, %s)
            """, (num_rows,))
        
        print("✅ Test data inserted!")
        
        # Check if data is replicated
        print("⏳ Waiting for replication...")
        time.sleep(3)
        self.check_sync_status()
        
        return True
    
    def analyze_slow_query(self):
        """Analyze the slow query for performance discussion"""
        print("\n🐢 ANALYZING SLOW QUERY PERFORMANCE:")
        print("=" * 60)
        
        query = """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
            SELECT *
            FROM orders
            WHERE created_at > now() - interval '1 day'
        """
        
        print("Query:")
        print("  SELECT * FROM orders WHERE created_at > now() - interval '1 day'")
        print()
        
        with self.source_conn.cursor() as cur:
            cur.execute(query)
            explain_output = cur.fetchall()
            
        print("Execution Plan:")
        print("-" * 60)
        for row in explain_output:
            print(row[0])
        
        print("\n💡 Performance Discussion Points:")
        print("  1. Check if the query uses Index Scan or Seq Scan")
        print("  2. If Seq Scan, consider creating an index on created_at")
        print("  3. For large tables, consider partitioning by date")
        print("  4. Use covering index (INCLUDE) for better performance")
        print("  5. Consider using a materialized view for frequent queries")
        
        # Check if index is being used
        with self.source_conn.cursor() as cur:
            cur.execute("""
                EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                SELECT *
                FROM orders
                WHERE created_at > now() - interval '1 day'
            """)
            plan = cur.fetchall()
            
            plan_text = str(plan)
            uses_index = "Index Scan" in plan_text or "Index Only Scan" in plan_text
            print(f"\n  ✅ Index usage: {'Yes (Index Scan)' if uses_index else 'No (Seq Scan)'}")
        
        return query
    
    def close(self):
        self.source_conn.close()
        self.target_conn.close()

def main():
    setup = MigrationSetup()
    try:
        print("=" * 60)
        print("NEAR-ZERO DOWNTIME MIGRATION LAB - SETUP")
        print("=" * 60)
        
        # Setup replication
        success = setup.setup_replication()
        if not success:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
        
        # Insert test data
        setup.insert_test_data(100)
        
        print("\n🔍 Analyzing slow query performance...")
        setup.analyze_slow_query()
        
        print("\n" + "=" * 60)
        print("✅ Setup complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Validate data:    python3 scripts/validate_data.py")
        print("  2. Run simulator:    python3 scripts/app_simulator.py")
        print("  3. Monitor:          python3 scripts/monitor_replication.py")
        print("  4. Cutover:          python3 scripts/simulate_cutover.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        setup.close()

if __name__ == "__main__":
    main()
