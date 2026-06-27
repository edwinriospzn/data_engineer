import psycopg2
import logging

DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'airflow',
    'user': 'airflow',
    'password': 'airflow'
}

def get_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logging.error(f"❌ Error conectando a PostgreSQL: {e}")
        raise

def insert_intraday(records, table_name):
    """Inserta datos en raw_intraday_1min o raw_intraday_5min"""
    if not records:
        logging.warning(f"⚠️ No hay registros para insertar en {table_name}")
        return
    
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        inserted = 0
        for row in records:
            try:
                # ⭐ USAR MINÚSCULAS (open, high, low, close, volume)
                cur.execute(f"""
                    INSERT INTO {table_name} (ticker, timestamp, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, timestamp) DO NOTHING
                """, (
                    row.get('ticker'),
                    row.get('timestamp'),
                    row.get('open'),      # ← minúscula
                    row.get('high'),      # ← minúscula
                    row.get('low'),       # ← minúscula
                    row.get('close'),     # ← minúscula
                    row.get('volume')     # ← minúscula
                ))
                inserted += 1
            except Exception as e:
                logging.error(f"Error insertando fila: {e}")
                logging.error(f"Row: {row}")
        
        conn.commit()
        logging.info(f"✅ Insertados {inserted} registros en {table_name}")
        
    except Exception as e:
        logging.error(f"❌ Error en insert_intraday: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def insert_fundamental(records):
    """Inserta datos fundamentales"""
    if not records:
        logging.warning("⚠️ No hay registros fundamentales para insertar")
        return
    
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        inserted = 0
        for row in records:
            try:
                cur.execute("""
                    INSERT INTO raw_fundamental 
                    (ticker, fetch_timestamp, market_cap, trailing_pe, dividend_yield, sector)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, fetch_timestamp) DO NOTHING
                """, (
                    row.get('ticker'),
                    row.get('fetch_timestamp'),
                    row.get('marketCap'),
                    row.get('trailingPE'),
                    row.get('dividendYield'),
                    row.get('sector')
                ))
                inserted += 1
            except Exception as e:
                logging.error(f"Error insertando fila fundamental: {e}")
        
        conn.commit()
        logging.info(f"✅ Insertados {inserted} registros en raw_fundamental")
        
    except Exception as e:
        logging.error(f"❌ Error en insert_fundamental: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()