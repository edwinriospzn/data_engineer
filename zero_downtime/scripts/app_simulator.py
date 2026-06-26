#!/usr/bin/env python3
"""
Application simulator that generates traffic and monitors migration
"""
import time
import random
import logging
from datetime import datetime, timedelta
import sys
import os
from db_config import SOURCE_CONFIG, TARGET_CONFIG, get_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app_simulator.log') if os.path.exists('/app/logs') else logging.StreamHandler(),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ApplicationSimulator:
    def __init__(self):
        self.source_conn = get_connection(SOURCE_CONFIG)
        self.target_conn = get_connection(TARGET_CONFIG)
        self.source_conn.autocommit = True
        self.target_conn.autocommit = True
        self.is_cutover = False
        self.order_counter = 0
        
    def generate_order(self):
        """Generate a random order"""
        customers = [
            'Acme Corp', 'Globex Inc', 'Initech', 'Hooli', 'Stark Industries',
            'Wayne Enterprises', 'Cyberdyne Systems', 'Oscorp', 'S.H.I.E.L.D.', 'Hydra',
            'Umbrella Corp', 'Weyland-Yutani', 'Tyrell Corp', 'CyberLife', 'Aperture'
        ]
        products = ['Laptop', 'Phone', 'Tablet', 'Monitor', 'Keyboard', 'Mouse', 'Printer', 'Server']
        
        return {
            'customer_name': random.choice(customers),
            'amount': round(random.uniform(10, 9999.99), 2),
            'product': random.choice(products)
        }
    
    def insert_order(self, conn):
        """Insert an order into the database"""
        order = self.generate_order()
        self.order_counter += 1
        
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO orders (customer_name, amount) VALUES (%s, %s)",
                (order['customer_name'], order['amount'])
            )
        
        logger.debug(f"Order #{self.order_counter}: {order['customer_name']} - ${order['amount']:.2f}")
        return order
    
    def get_stats(self):
        """Get current statistics"""
        with self.source_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders")
            source_count = cur.fetchone()[0]
            cur.execute("SELECT MAX(created_at) FROM orders")
            source_latest = cur.fetchone()[0]
        
        with self.target_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders")
            target_count = cur.fetchone()[0]
            cur.execute("SELECT MAX(created_at) FROM orders")
            target_latest = cur.fetchone()[0]
        
        return {
            'source_count': source_count,
            'target_count': target_count,
            'source_latest': source_latest,
            'target_latest': target_latest
        }
    
    def check_replication_status(self):
        """Check replication status"""
        try:
            with self.target_conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        subname,
                        status,
                        enabled,
                        slot_name
                    FROM pg_stat_subscription
                """)
                result = cur.fetchall()
                return result
        except Exception as e:
            logger.error(f"Error checking replication: {e}")
            return None
    
    def run_traffic(self, duration=60, rate=1):
        """Run traffic generation for specified duration"""
        logger.info(f"🚀 Starting traffic generation for {duration} seconds at {rate} order/sec")
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration)
        order_count = 0
        
        while datetime.now() < end_time:
            try:
                # Insert order on source (or target after cutover)
                conn = self.target_conn if self.is_cutover else self.source_conn
                order = self.insert_order(conn)
                order_count += 1
                
                # Log progress
                if order_count % 10 == 0:
                    stats = self.get_stats()
                    logger.info(f"📊 Orders: {order_count} | Source: {stats['source_count']:,} | Target: {stats['target_count']:,}")
                    
                    # Check replication status
                    status = self.check_replication_status()
                    if status:
                        for sub in status:
                            if sub[1] != 'ready':
                                logger.warning(f"⚠️  Replication status: {sub[1]}")
                
                # Sleep based on rate
                time.sleep(1.0 / rate)
                
            except KeyboardInterrupt:
                logger.info("Traffic generation interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error inserting order: {e}")
                time.sleep(1)
        
        logger.info(f"✅ Traffic generation complete. Total orders: {order_count}")
        return order_count
    
    def perform_cutover(self):
        """Simulate cutover to target"""
        logger.info("=" * 60)
        logger.info("✂️  PERFORMING CUTOVER")
        logger.info("=" * 60)
        
        # Stop writes to source
        logger.info("Stopping writes to source...")
        try:
            with self.source_conn.cursor() as cur:
                cur.execute("""
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE pid <> pg_backend_pid() 
                    AND datname = 'sales'
                """)
                terminated = cur.fetchone()[0]
                logger.info(f"✓ Terminated {terminated} connections")
        except Exception as e:
            logger.error(f"Error stopping source writes: {e}")
            return False
        
        # Wait for replication to catch up
        logger.info("Waiting for replication to catch up...")
        time.sleep(3)
        
        # Verify data consistency
        stats = self.get_stats()
        logger.info(f"Source rows: {stats['source_count']:,}")
        logger.info(f"Target rows: {stats['target_count']:,}")
        
        if stats['source_count'] == stats['target_count']:
            logger.info("✅ Data is consistent")
        else:
            diff = stats['source_count'] - stats['target_count']
            logger.warning(f"⚠️  Data mismatch! Difference: {diff:,} rows")
            return False
        
        # Switch to target
        self.is_cutover = True
        logger.info("✅ Switched to target database")
        
        logger.info("=" * 60)
        logger.info("✅ CUTOVER COMPLETE")
        logger.info("=" * 60)
        return True
    
    def run_scenario(self):
        """Run a complete scenario"""
        logger.info("=" * 60)
        logger.info("🚀 APPLICATION SIMULATOR")
        logger.info("=" * 60)
        logger.info(f"Source: {SOURCE_CONFIG.host}:{SOURCE_CONFIG.port}")
        logger.info(f"Target: {TARGET_CONFIG.host}:{TARGET_CONFIG.port}")
        logger.info("=" * 60)
        print()
        
        try:
            # Check initial state
            stats = self.get_stats()
            logger.info(f"📊 Initial state - Source: {stats['source_count']:,}, Target: {stats['target_count']:,}")
            
            # Phase 1: Generate traffic on source
            logger.info("\n📝 Phase 1: Generating traffic on source")
            self.run_traffic(duration=20, rate=2)
            
            # Phase 2: Check replication
            logger.info("\n📊 Phase 2: Checking replication status")
            status = self.check_replication_status()
            if status:
                for sub in status:
                    logger.info(f"  Subscription: {sub[0]} - Status: {sub[1]}")
            
            # Phase 3: Continue traffic
            logger.info("\n📝 Phase 3: Continuing traffic")
            self.run_traffic(duration=15, rate=3)
            
            # Phase 4: Perform cutover
            logger.info("\n✂️  Phase 4: Performing cutover")
            if self.perform_cutover():
                # Phase 5: Traffic on target
                logger.info("\n📝 Phase 5: Generating traffic on target")
                self.run_traffic(duration=15, rate=2)
            
            # Final stats
            logger.info("\n📊 Final statistics:")
            stats = self.get_stats()
            logger.info(f"  Source: {stats['source_count']:,} rows")
            logger.info(f"  Target: {stats['target_count']:,} rows")
            
            logger.info("\n✅ Scenario complete!")
            
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Simulation interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in scenario: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def cleanup(self):
        self.source_conn.close()
        self.target_conn.close()
        logger.info("🧹 Cleanup complete")

if __name__ == "__main__":
    simulator = ApplicationSimulator()
    simulator.run_scenario()