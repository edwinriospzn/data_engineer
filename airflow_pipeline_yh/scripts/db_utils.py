import psycopg2
import logging
from datetime import datetime

DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'airflow',
    'user': 'airflow',
    'password': 'airflow'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def insert_intraday(records, table_name):
    """Inserta datos en raw_intraday_1min o raw_intraday_5min"""
    conn = get_connection()
    cur = conn.cursor()
    
    for row in records:
        try:
            cur.execute(f"""
                INSERT INTO {table_name} (ticker, timestamp, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, timestamp) DO NOTHING
            """, (
                row['ticker'],
                row['timestamp'],
                row['Open'],
                row['High'],
                row['Low'],
                row['Close'],
                row['Volume']
            ))
        except Exception as e:
            logging.error(f"Error insertando: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    logging.info(f"✅ Insertados {len(records)} en {table_name}")

def insert_fundamental(records):
    """Inserta datos fundamentales"""
    conn = get_connection()
    cur = conn.cursor()
    
    for row in records:
        cur.execute("""
            INSERT INTO raw_fundamental 
            (ticker, fetch_timestamp, market_cap, trailing_pe, dividend_yield, sector)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, fetch_timestamp) DO NOTHING
        """, (
            row['ticker'],
            row['fetch_timestamp'],
            row.get('marketCap'),
            row.get('trailingPE'),
            row.get('dividendYield'),
            row.get('sector')
        ))
    
    conn.commit()
    cur.close()
    conn.close()
    logging.info(f"✅ Insertados {len(records)} en raw_fundamental")