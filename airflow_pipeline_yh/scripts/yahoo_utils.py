import yfinance as yf
import pandas as pd
import logging
import time
import json
import os
from datetime import datetime
from config import TICKERS, FUNDAMENTAL_COLUMNS

DATA_DIR = '/opt/airflow/data'

def fetch_intraday_data(frequency, **context):
    """Obtiene datos intraday y los guarda en archivo JSON"""
    interval = '1m' if frequency == '1min' else '5m'
    
    logging.info(f"📊 Descargando datos {frequency} para {TICKERS}")
    
    df = yf.download(
        tickers=TICKERS,
        period='5d',
        interval=interval,
        group_by='ticker',
        progress=False
    )
    
    logging.info(f"📊 Datos descargados: {len(df)} filas")
    
    # Convertir a formato largo
    if isinstance(df.columns, pd.MultiIndex):
        df = df.stack(level=0).rename_axis(index=['timestamp', 'ticker']).reset_index()
    
    # Convertir timestamps a string para JSON
    df['timestamp'] = df['timestamp'].astype(str)
    
    records = df.to_dict('records')
    
    # Guardar en archivo JSON
    os.makedirs(DATA_DIR, exist_ok=True)
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/{frequency}_{run_id}.json"
    
    with open(file_path, 'w') as f:
        json.dump(records, f, default=str)
    
    logging.info(f"✅ {frequency}: {len(records)} registros guardados en {file_path}")
    
    # También intentar XCom (por si acaso)
    try:
        context['ti'].xcom_push(key=f'data_{frequency}', value=records)
        logging.info(f"📤 {frequency}: datos enviados a XCom")
    except Exception as e:
        logging.warning(f"⚠️ No se pudo enviar a XCom: {e}")
    
    return records

def fetch_fundamental_data(**context):
    """Obtiene datos fundamentales y los guarda en archivo JSON"""
    fundamentals = []
    os.makedirs(DATA_DIR, exist_ok=True)
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/fundamental_{run_id}.json"
    
    logging.info(f"📊 Descargando datos fundamentales para {TICKERS}")
    
    for idx, ticker in enumerate(TICKERS):
        try:
            if idx > 0:
                time.sleep(2)  # Pausa para evitar 429
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            record = {
                'ticker': ticker,
                'fetch_timestamp': datetime.now().isoformat(),
                **{k: info.get(k) for k in FUNDAMENTAL_COLUMNS}
            }
            fundamentals.append(record)
            logging.info(f"✅ Fundamental: {ticker}")
            
        except Exception as e:
            logging.error(f"❌ Error con {ticker}: {e}")
    
    # Guardar en archivo JSON
    with open(file_path, 'w') as f:
        json.dump(fundamentals, f, default=str)
    
    logging.info(f"✅ Fundamental: {len(fundamentals)} registros guardados en {file_path}")
    
    # También intentar XCom
    try:
        context['ti'].xcom_push(key='fundamental_data', value=fundamentals)
        logging.info(f"📤 Fundamental: datos enviados a XCom")
    except Exception as e:
        logging.warning(f"⚠️ No se pudo enviar a XCom: {e}")
    
    return fundamentals