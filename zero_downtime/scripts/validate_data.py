#!/usr/bin/env python3
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime
import hashlib
import sys
import os
from db_config import SOURCE_CONFIG, TARGET_CONFIG, get_connection

class DataValidator:
    def __init__(self):
        self.source_conn = get_connection(SOURCE_CONFIG)
        self.target_conn = get_connection(TARGET_CONFIG)
        self.source_conn.autocommit = True
        self.target_conn.autocommit = True
        
    def get_table_stats(self):
        """Get detailed statistics from both databases"""
        queries = {
            "total_count": "SELECT COUNT(*) as count FROM orders",
            "total_amount": "SELECT COALESCE(SUM(amount), 0) as total FROM orders",
            "avg_amount": "SELECT COALESCE(AVG(amount), 0) as avg FROM orders",
            "max_amount": "SELECT COALESCE(MAX(amount), 0) as max FROM orders",
            "min_amount": "SELECT COALESCE(MIN(amount), 0) as min FROM orders",
            "date_range": """
                SELECT 
                    COALESCE(MIN(created_at), NOW()) as oldest,
                    COALESCE(MAX(created_at), NOW()) as newest,
                    COUNT(DISTINCT DATE(created_at)) as days_with_orders
                FROM orders
            """,
            "customer_count": "SELECT COUNT(DISTINCT customer_name) as unique_customers FROM orders"
        }
        
        source_stats = {}
        target_stats = {}
        
        for name, query in queries.items():
            try:
                with self.source_conn.cursor() as cur:
                    cur.execute(query)
                    result = cur.fetchone()
                    source_stats[name] = result[0] if result else None
            except Exception as e:
                print(f"Error querying source for {name}: {e}")
                source_stats[name] = None
            
            try:
                with self.target_conn.cursor() as cur:
                    cur.execute(query)
                    result = cur.fetchone()
                    target_stats[name] = result[0] if result else None
            except Exception as e:
                print(f"Error querying target for {name}: {e}")
                target_stats[name] = None
        
        return source_stats, target_stats
    
    def get_sample_data(self, limit=100):
        """Get sample data for comparison"""
        query = """
            SELECT order_id, customer_name, amount, created_at
            FROM orders 
            ORDER BY order_id 
            LIMIT %s
        """
        
        with self.source_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, (limit,))
            source_sample = [dict(row) for row in cur.fetchall()]
        
        with self.target_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, (limit,))
            target_sample = [dict(row) for row in cur.fetchall()]
        
        return source_sample, target_sample
    
    def compute_checksum(self):
        """Compute MD5 checksum of all data for consistency check"""
        query = """
            SELECT COALESCE(MD5(STRING_AGG(
                COALESCE(order_id::text, '') || 
                COALESCE(customer_name, '') || 
                COALESCE(amount::text, '') || 
                COALESCE(created_at::text, ''), 
                '' ORDER BY order_id
            )), 'no_data')
            FROM orders
        """
        
        with self.source_conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()
            source_checksum = result[0] if result else 'no_data'
        
        with self.target_conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()
            target_checksum = result[0] if result else 'no_data'
        
        return source_checksum, target_checksum
    
    def validate_replication_lag(self):
        """Check for any replication lag by comparing latest timestamps"""
        query = "SELECT MAX(created_at) FROM orders"
        
        with self.source_conn.cursor() as cur:
            cur.execute(query)
            source_latest = cur.fetchone()[0]
        
        with self.target_conn.cursor() as cur:
            cur.execute(query)
            target_latest = cur.fetchone()[0]
        
        if source_latest and target_latest:
            lag = (source_latest - target_latest).total_seconds()
            return lag
        return None
    
    def compare_data(self):
        """Comprehensive data comparison"""
        print("=" * 60)
        print("DATA VALIDATION REPORT")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Source: {SOURCE_CONFIG.host}:{SOURCE_CONFIG.port}")
        print(f"Target: {TARGET_CONFIG.host}:{TARGET_CONFIG.port}")
        print()
        
        # Basic statistics
        source_stats, target_stats = self.get_table_stats()
        
        print("📊 STATISTICS COMPARISON:")
        print("-" * 60)
        print(f"{'Metric':<25} {'Source':<15} {'Target':<15} {'Match':<10}")
        print("-" * 60)
        
        all_match = True
        for key in source_stats:
            source_val = source_stats[key]
            target_val = target_stats[key]
            
            if source_val is None and target_val is None:
                match = "✅"
            elif source_val == target_val:
                match = "✅"
            else:
                match = "❌"
                all_match = False
            
            # Format numbers
            if isinstance(source_val, (int, float)) and source_val is not None:
                if key in ['total_amount']:
                    source_val = f"${source_val:,.2f}"
                    target_val = f"${target_val:,.2f}" if target_val is not None else "None"
                elif key in ['avg_amount']:
                    source_val = f"${source_val:.2f}"
                    target_val = f"${target_val:.2f}" if target_val is not None else "None"
                elif key in ['total_count', 'customer_count']:
                    source_val = f"{source_val:,}"
                    target_val = f"{target_val:,}" if target_val is not None else "None"
                else:
                    source_val = f"{source_val}"
                    target_val = f"{target_val}" if target_val is not None else "None"
            elif source_val is None:
                source_val = "None"
                target_val = "None" if target_val is None else str(target_val)
            
            print(f"{key.replace('_', ' ').title():<25} {str(source_val):<15} {str(target_val):<15} {match:<10}")
        
        print()
        
        # Checksum validation
        source_checksum, target_checksum = self.compute_checksum()
        checksum_match = source_checksum == target_checksum
        print("🔐 DATA INTEGRITY:")
        print("-" * 60)
        print(f"Source Checksum: {source_checksum}")
        print(f"Target Checksum: {target_checksum}")
        print(f"Checksum Match: {'✅' if checksum_match else '❌'}")
        if not checksum_match:
            all_match = False
        print()
        
        # Replication lag
        lag = self.validate_replication_lag()
        if lag is not None:
            print("⏱️ REPLICATION LAG:")
            print("-" * 60)
            if lag == 0:
                print("✨ No lag detected - Target is fully synchronized")
            else:
                print(f"⚠️  Lag detected: {abs(lag):.2f} seconds")
            print()
        
        # Sample data comparison
        print("📋 SAMPLE DATA (First 5 rows):")
        print("-" * 60)
        source_sample, target_sample = self.get_sample_data(5)
        
        if source_sample and target_sample:
            source_df = pd.DataFrame(source_sample)
            target_df = pd.DataFrame(target_sample)
            
            print("\nSource:")
            print(source_df.to_string(index=False))
            print("\nTarget:")
            print(target_df.to_string(index=False))
            
            try:
                sample_match = source_df.equals(target_df)
                if not sample_match:
                    all_match = False
            except:
                pass
        else:
            print("⚠️  No sample data available")
        
        print()
        
        # Final verdict
        print("=" * 60)
        print("🎯 FINAL VERDICT:")
        if all_match:
            print("✅ ALL CHECKS PASSED - Data is consistent!")
        else:
            print("❌ INCONSISTENCIES FOUND - Please investigate!")
        print("=" * 60)
        
        return all_match
    
    def close(self):
        self.source_conn.close()
        self.target_conn.close()

def main():
    validator = DataValidator()
    try:
        success = validator.compare_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        validator.close()

if __name__ == "__main__":
    main()