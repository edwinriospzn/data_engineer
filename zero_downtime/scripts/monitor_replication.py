#!/usr/bin/env python3
import psycopg2
import time
import sys
from datetime import datetime, timedelta
from db_config import SOURCE_CONFIG, TARGET_CONFIG, get_connection

class ReplicationMonitor:
    def __init__(self):
        self.source_conn = get_connection(SOURCE_CONFIG)
        self.target_conn = get_connection(TARGET_CONFIG)
        self.source_conn.autocommit = True
        self.target_conn.autocommit = True
        
    def monitor_replication_status(self, duration=30, interval=5):
        """Monitor replication status for a given duration"""
        print("📊 REPLICATION MONITOR")
        print("=" * 60)
        print(f"Monitoring for {duration} seconds...")
        print(f"Source: {SOURCE_CONFIG.host}:{SOURCE_CONFIG.port}")
        print(f"Target: {TARGET_CONFIG.host}:{TARGET_CONFIG.port}")
        print()
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration)
        
        sample_count = 0
        
        while datetime.now() < end_time:
            sample_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"📋 Sample {sample_count} at {timestamp}")
            print("-" * 40)
            
            try:
                # Check source stats
                with self.source_conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM orders")
                    source_count = cur.fetchone()[0]
                    cur.execute("SELECT MAX(created_at) FROM orders")
                    source_latest = cur.fetchone()[0]
                
                # Check target stats
                with self.target_conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM orders")
                    target_count = cur.fetchone()[0]
                    cur.execute("SELECT MAX(created_at) FROM orders")
                    target_latest = cur.fetchone()[0]
                
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
                
                # Display results
                print(f"  Source rows: {source_count:,}")
                print(f"  Target rows: {target_count:,}")
                print(f"  Difference: {source_count - target_count:,}")
                
                if source_latest and target_latest:
                    lag = (source_latest - target_latest).total_seconds()
                    if lag == 0:
                        print(f"  Replication lag: ✨ 0 seconds")
                    elif lag < 1:
                        print(f"  Replication lag: ✅ {lag:.2f} seconds")
                    else:
                        print(f"  Replication lag: ⚠️  {lag:.2f} seconds")
                
                if subscriptions:
                    print(f"\n  Subscription Status:")
                    for sub in subscriptions:
                        print(f"    - {sub[0]}: Enabled={sub[1]}, Slot={sub[2]}")
                        
                        # Get replication slot lag - using subslotname
                        slot_name = sub[2]
                        if slot_name:
                            with self.target_conn.cursor() as cur2:
                                cur2.execute("""
                                    SELECT 
                                        pg_wal_lsn_diff(
                                            pg_current_wal_lsn(),
                                            confirmed_flush_lsn
                                        ) as lag_bytes
                                    FROM pg_replication_slots
                                    WHERE slot_name = %s
                                """, (slot_name,))
                                lag_result = cur2.fetchone()
                                if lag_result and lag_result[0]:
                                    lag_bytes = lag_result[0]
                                    lag_mb = lag_bytes / (1024 * 1024)
                                    print(f"    - WAL Lag: {lag_mb:.2f} MB")
                
                # Check for any errors - CORRECTED for PostgreSQL 17
                with self.target_conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            subname,
                            subenabled
                        FROM pg_subscription
                        WHERE NOT subenabled
                    """)
                    disabled = cur.fetchall()
                    if disabled:
                        print(f"\n  ⚠️  Disabled subscriptions:")
                        for sub in disabled:
                            print(f"    - {sub[0]} is disabled")
                
            except Exception as e:
                print(f"  ⚠️  Error checking status: {e}")
            
            print("-" * 40)
            print()
            
            if datetime.now() < end_time:
                time.sleep(interval)
        
        print("✅ Monitoring complete")
        print("=" * 60)
    
    def show_replication_stats(self):
        """Show detailed replication statistics"""
        print("📊 REPLICATION DETAILED STATISTICS")
        print("=" * 60)
        
        # Source publication info
        with self.source_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    pubname,
                    pubowner::regrole,
                    puballtables,
                    pubinsert,
                    pubupdate,
                    pubdelete,
                    pubtruncate
                FROM pg_publication
            """)
            publications = cur.fetchall()
            if publications:
                print("\n📋 Publications on Source:")
                for pub in publications:
                    print(f"  - {pub[0]}:")
                    print(f"      Owner: {pub[1]}")
                    print(f"      All tables: {pub[2]}")
                    print(f"      INSERT: {pub[3]}, UPDATE: {pub[4]}, DELETE: {pub[5]}, TRUNCATE: {pub[6]}")
        
        # Target subscription info - CORRECTED for PostgreSQL 17
        with self.target_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    subname,
                    subowner::regrole,
                    subenabled,
                    subslotname,
                    subpublications
                FROM pg_subscription
            """)
            subscriptions = cur.fetchall()
            if subscriptions:
                print("\n📋 Subscriptions on Target:")
                for sub in subscriptions:
                    print(f"  - {sub[0]}:")
                    print(f"      Owner: {sub[1]}")
                    print(f"      Enabled: {sub[2]}")
                    print(f"      Slot: {sub[3]}")
                    print(f"      Publications: {sub[4]}")
        
        # Replication slots
        with self.source_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    slot_name,
                    slot_type,
                    active,
                    active_pid,
                    xmin,
                    catalog_xmin,
                    restart_lsn
                FROM pg_replication_slots
            """)
            slots = cur.fetchall()
            if slots:
                print("\n📋 Replication Slots on Source:")
                for slot in slots:
                    print(f"  - {slot[0]}:")
                    print(f"      Type: {slot[1]}")
                    print(f"      Active: {slot[2]}")
                    print(f"      PID: {slot[3]}")
                    print(f"      Xmin: {slot[4]}")
                    print(f"      Catalog Xmin: {slot[5]}")
        
        print("=" * 60)
    
    def close(self):
        self.source_conn.close()
        self.target_conn.close()

def main():
    monitor = ReplicationMonitor()
    try:
        print("\n" + "=" * 60)
        print("NEAR-ZERO DOWNTIME MIGRATION - REPLICATION MONITOR")
        print("=" * 60)
        print()
        print("1. Monitor replication (continuous)")
        print("2. Show detailed statistics")
        print("0. Exit")
        print()
        
        choice = input("Enter choice: ")
        
        if choice == "1":
            duration = input("Monitoring duration in seconds (default 30): ")
            duration = int(duration) if duration else 30
            interval = input("Interval between checks in seconds (default 5): ")
            interval = int(interval) if interval else 5
            monitor.monitor_replication_status(duration, interval)
        elif choice == "2":
            monitor.show_replication_stats()
        else:
            print("Exiting...")
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        monitor.close()

if __name__ == "__main__":
    main()
