import yfinance as yf
import pandas as pd
import logging
import time
import json
import os
from datetime import datetime, timedelta
from config import TICKERS, FUNDAMENTAL_COLUMNS

DATA_DIR = '/opt/airflow/data'

def fetch_intraday_data(frequency, **context):
    """
    Obtiene el ÚLTIMO registro de cada ticker para la frecuencia indicada.
    
    frequency: '1min' o '5min'
    """
    interval = '1m' if frequency == '1min' else '5m'
    
    logging.info(f"📊 Descargando ÚLTIMO dato {frequency} para {TICKERS}")
    
    try:
        # Descargar datos del día
        df = yf.download(
            tickers=TICKERS,
            period='1d',           # Mínimo período permitido
            interval=interval,
            group_by='ticker',
            progress=False,
            auto_adjust=False
        )
        
        if df.empty:
            logging.warning(f"⚠️ No se descargaron datos para {frequency}")
            records = []
        else:
            # Convertir a formato largo con columna 'ticker'
            if isinstance(df.columns, pd.MultiIndex):
                df = df.stack(level=0).rename_axis(index=['timestamp', 'ticker']).reset_index()
            else:
                # Si solo es un ticker, agregar columna
                df = df.reset_index()
                df['ticker'] = TICKERS[0] if TICKERS else 'AAPL'
            
            # ⭐ FILTRAR: QUEDARSE SOLO CON EL ÚLTIMO REGISTRO POR TICKER ⭐
            df = df.groupby('ticker').tail(1).reset_index(drop=True)
            
            logging.info(f"✅ {frequency}: {len(df)} registros (últimos por ticker)")
            
            # Convertir timestamps a string para JSON
            df['timestamp'] = df['timestamp'].astype(str)
            
            # Renombrar columnas para consistencia
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            records = df.to_dict('records')
            
    except Exception as e:
        logging.error(f"❌ Error descargando {frequency}: {e}")
        records = []
    
    # Guardar en archivo JSON
    os.makedirs(DATA_DIR, exist_ok=True)
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/{frequency}_{run_id}.json"
    
    with open(file_path, 'w') as f:
        json.dump(records, f, default=str)
    
    logging.info(f"📁 Archivo guardado: {file_path} ({len(records)} registros)")
    
    # XCom para respaldo
    try:
        context['ti'].xcom_push(key=f'data_{frequency}', value=records)
    except Exception as e:
        logging.warning(f"⚠️ No se pudo enviar a XCom: {e}")
    
    return records


def fetch_fundamental_data(**context):
    """Obtiene datos fundamentales para cada ticker"""
    fundamentals = []
    os.makedirs(DATA_DIR, exist_ok=True)
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/fundamental_{run_id}.json"
    
    logging.info(f"📊 Descargando datos fundamentales para {TICKERS}")
    
    for idx, ticker in enumerate(TICKERS):
        try:
            if idx > 0:
                time.sleep(2)  # Pausa para evitar rate limiting
            
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
    
    logging.info(f"✅ Fundamental: {len(fundamentals)} registros guardados")
    return fundamentals