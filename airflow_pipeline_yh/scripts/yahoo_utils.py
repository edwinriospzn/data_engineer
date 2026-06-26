import yfinance as yf
import pandas as pd
import logging
import time
from datetime import datetime
from config import TICKERS, FUNDAMENTAL_COLUMNS

def fetch_intraday_data(frequency, **context):
    """Obtiene datos intraday (1min o 5min)"""
    interval = '1m' if frequency == '1min' else '5m'
    
    df = yf.download(
        tickers=TICKERS,
        period='5d',
        interval=interval,
        group_by='ticker'
    )
    
    if isinstance(df.columns, pd.MultiIndex):
        df = df.stack(level=0).rename_axis(index=['timestamp', 'ticker']).reset_index()
    
    records = df.to_dict('records')
    context['ti'].xcom_push(key=f'data_{frequency}', value=records)
    
    logging.info(f"✅ {frequency}: {len(records)} registros")
    return records

def fetch_fundamental_data(**context):
    """Obtiene datos fundamentales con pausa para evitar 429"""
    fundamentals = []
    
    for idx, ticker in enumerate(TICKERS):
        try:
            # Pausa entre requests para no saturar la API
            if idx > 0:
                time.sleep(2)
            
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
    
    context['ti'].xcom_push(key='fundamental_data', value=fundamentals)
    return fundamentals