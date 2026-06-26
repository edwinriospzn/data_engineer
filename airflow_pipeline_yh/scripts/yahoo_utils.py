import yfinance as yf
import pandas as pd
import logging
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
    
    # Convertir a formato largo
    if isinstance(df.columns, pd.MultiIndex):
        df = df.stack(level=0).rename_axis(index=['timestamp', 'ticker']).reset_index()
    
    # Agregar metadata
    records = df.to_dict('records')
    context['ti'].xcom_push(key=f'data_{frequency}', value=records)
    
    logging.info(f"✅ {frequency}: {len(records)} registros")
    return records

def fetch_fundamental_data(**context):
    """Obtiene datos fundamentales"""
    fundamentals = []
    
    for ticker in TICKERS:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        record = {
            'ticker': ticker,
            'fetch_timestamp': datetime.now().isoformat(),
            **{k: info.get(k) for k in FUNDAMENTAL_COLUMNS}
        }
        fundamentals.append(record)
    
    context['ti'].xcom_push(key='fundamental_data', value=fundamentals)
    logging.info(f"✅ Fundamental: {len(fundamentals)} registros")
    return fundamentals