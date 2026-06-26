#!/usr/bin/env python3
import psycopg2
import time
import sys
from datetime import datetime
from db_config import SOURCE_CONFIG, TARGET_CONFIG, get_connection
from validate_data import DataValidator

class CutoverSimulator:
    def __init__(self):
        self.source_conn = get_connection(SOURCE_CONFIG)
        self.target_conn = get_connection(TARGET_CONFIG)
        self.source_conn.autocommit = True
        self.target_conn.autocommit = True
        
    def get_database_stats(self):
        """Get statistics from both databases"""
        stats = {}
        
        with self.source_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders")
            stats['source_count'] = cur.fetchone()[0]
            cur.execute("SELECT MAX(created_at) FROM orders")
            stats['source_latest'] = cur.fetchone()[0]
        
        with self.target_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders")
            stats['target_count'] = cur.fetchone()[0]
            cur.execute("SELECT MAX(created_at) FROM orders")
            stats['target_latest'] = cur.fetchone()[0]
        
        return stats
    
    def simulate_cutover(self):
        print("=" * 60)
        print("✂️  MIGRATION CUTOVER SIMULATION")
        print("=" * 60)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 0: Show current state
        print("📊 CURRENT STATE:")
        stats = self.get_database_stats()
        print(f"  Source: {stats['source_count']:,} rows (Last update: {stats['source_latest']})")
        print(f"  Target: {stats['target_count']:,} rows (Last update: {stats['target_latest']})")
        print()
        
        # Step 1: Stop writes to source
        print("🔴 STEP 1: Stopping writes to source...")
        with self.source_conn.cursor() as cur:
            # Terminate all other connections
            cur.execute("""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE pid <> pg_backend_pid() 
                AND datname = 'sales'
            """)
            terminated = cur.fetchone()[0]
            print(f"   ✅ Terminated {terminated} connections")
        
        time.sleep(1)
        print("   ✅ Writes stopped")
        print()
        
        # Step 2: Verify data consistency
        print("🔍 STEP 2: Validating data consistency...")
        validator = DataValidator()
        is_consistent = validator.compare_data()
        validator.close()
        
        if not is_consistent:
            print("\n⚠️  Data inconsistency detected!")
            response = input("Continue with cutover? (y/n): ")
            if response.lower() != 'y':
                print("❌ Cutover cancelled")
                return False
        else:
            print("   ✅ Data is consistent")
        print()
        
        # Step 3: Create cutover point
        print("📝 STEP 3: Creating cutover point...")
        with self.source_conn.cursor() as cur:
            cur.execute("SELECT NOW() as cutover_time")
            cutover_time = cur.fetchone()[0]
        
        print(f"   Cutover timestamp: {cutover_time}")
        print()
        
        # Step 4: Final sync check
        print("🔄 STEP 4: Final sync check...")
        time.sleep(2)
        
        final_stats = self.get_database_stats()
        print(f"   Source: {final_stats['source_count']:,} rows")
        print(f"   Target: {final_stats['target_count']:,} rows")
        
        if final_stats['source_count'] == final_stats['target_count']:
            print("   ✅ Row counts match")
        else:
            print(f"   ⚠️  Row count mismatch! Difference: {abs(final_stats['source_count'] - final_stats['target_count'])}")
            response = input("Continue with cutover? (y/n): ")
            if response.lower() != 'y':
                print("❌ Cutover cancelled")
                return False
        print()
        
        # Step 5: Switch to target
        print("🔄 STEP 5: Switching to target...")
        print("   """
        Update your application connection strings:
        
        Before cutover:
          DATABASE_URL = postgresql://postgres:postgres@localhost:5434/sales
        
        After cutover:
          DATABASE_URL = postgresql://postgres:postgres@localhost:5435/sales
        
        Or update DNS/load balancer to point to target.
        """)
        
        # Create a cutover marker
        with self.target_conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cutover_marker (
                    cutover_time TIMESTAMP DEFAULT NOW(),
                    source_row_count INTEGER,
                    target_row_count INTEGER,
                    executed_by TEXT DEFAULT CURRENT_USER
                )
            """)
            cur.execute("""
                INSERT INTO cutover_marker (cutover_time, source_row_count, target_row_count)
                VALUES (%s, %s, %s)
            """, (cutover_time, final_stats['source_count'], final_stats['target_count']))
            print("   ✅ Cutover marker created on target")
        print()
        
        # Step 6: Final validation
        print("🔍 STEP 6: Final validation on target...")
        validator2 = DataValidator()
        with validator2.target_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders")
            count = cur.fetchone()[0]
            print(f"   ✅ Target has {count:,} rows")
            
            # Check cutover marker
            cur.execute("SELECT * FROM cutover_marker ORDER BY cutover_time DESC LIMIT 1")
            marker = cur.fetchone()
            if marker:
                print(f"   ✅ Cutover recorded at: {marker[0]}")
        
        validator2.close()
        print()
        
        # Step 7: Summary
        print("=" * 60)
        print("✅ CUTOVER COMPLETE!")
        print("=" * 60)
        print(f"Cutover time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data migrated: {final_stats['source_count']:,} rows")
        print("Estimated downtime: < 5 seconds (theoretical)")
        print()
        print("📋 Next Steps:")
        print("  1. Update application to use target database (port 5435)")
        print("  2. Monitor application logs for errors")
        print("  3. Run validation script: python3 scripts/validate_data.py")
        print("  4. Keep source database available for rollback")
        print("  5. After verification, decommission source database")
        print("=" * 60)
        
        return True
    
    def rollback_simulation(self):
        """Simulate rollback to source"""
        print("=" * 60)
        print("↩️  ROLLBACK SIMULATION")
        print("=" * 60)
        print()
        
        print("To rollback:")
        print("  1. Stop writes to target")
        print("  2. Validate data consistency")
        print("  3. Update application to use source (port 5434)")
        print("  4. Resume operations")
        print()
        print("💡 Rollback is always possible if you keep both databases synchronized")
        print("   and don't drop the replication setup.")
        
        return True
    
    def close(self):
        self.source_conn.close()
        self.target_conn.close()

def main():
    simulator = CutoverSimulator()
    try:
        print("\n" + "=" * 60)
        print("NEAR-ZERO DOWNTIME MIGRATION - CUTOVER TOOL")
        print("=" * 60)
        print()
        print("1. Simulate cutover to target")
        print("2. Show rollback instructions")
        print("0. Exit")
        print()
        
        choice = input("Enter choice: ")
        
        if choice == "1":
            simulator.simulate_cutover()
        elif choice == "2":
            simulator.rollback_simulation()
        else:
            print("Exiting...")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"❌ Error during cutover: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        simulator.close()

if __name__ == "__main__":
    main()