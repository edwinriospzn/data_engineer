from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator  # ← Importar ShortCircuitOperator
import sys
import json
import os
import logging
sys.path.append('/opt/airflow/scripts')

from yahoo_utils import fetch_intraday_data, fetch_fundamental_data
from db_utils import insert_intraday, insert_fundamental

DATA_DIR = '/opt/airflow/data'

default_args = {
    'owner': 'data_engineer',
    'start_date': datetime(2026, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

# ============================================
# FUNCIONES LOAD (Leer desde archivos)
# ============================================

def load_data_1min(**context):
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/1min_{run_id}.json"
    logging.info(f"📂 Buscando archivo: {file_path}")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            records = json.load(f)
        if records:
            insert_intraday(records, 'raw_intraday_1min')
            logging.info(f"✅ Cargados {len(records)} registros de 1min")
            os.remove(file_path)
        else:
            logging.warning("⚠️ Archivo vacío, sin datos para insertar")
    else:
        raise ValueError(f"Archivo no encontrado: {file_path}")

def load_data_5min(**context):
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/5min_{run_id}.json"
    logging.info(f"📂 Buscando archivo: {file_path}")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            records = json.load(f)
        if records:
            insert_intraday(records, 'raw_intraday_5min')
            logging.info(f"✅ Cargados {len(records)} registros de 5min")
            os.remove(file_path)
        else:
            logging.warning("⚠️ Archivo vacío, sin datos para insertar")
    else:
        raise ValueError(f"Archivo no encontrado: {file_path}")

def load_fundamental_data(**context):
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/fundamental_{run_id}.json"
    logging.info(f"📂 Buscando archivo: {file_path}")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            records = json.load(f)
        if records:
            insert_fundamental(records)
            logging.info(f"✅ Cargados {len(records)} registros fundamentales")
            os.remove(file_path)
        else:
            logging.warning("⚠️ Archivo vacío, sin datos para insertar")
    else:
        raise ValueError(f"Archivo no encontrado: {file_path}")

# ============================================
# FUNCIONES PARA FILTRAR POR TIEMPO (¡NUEVO!)
# ============================================

def should_run_5min(**context):
    """Solo ejecuta si el minuto actual es múltiplo de 5"""
    from datetime import datetime
    current_minute = datetime.now().minute
    should_run = current_minute % 5 == 0
    logging.info(f"🕐 Minuto {current_minute}: ejecutar 5min = {should_run}")
    return should_run

def should_run_15min(**context):
    """Solo ejecuta si el minuto actual es múltiplo de 15"""
    from datetime import datetime
    current_minute = datetime.now().minute
    should_run = current_minute % 15 == 0
    logging.info(f"🕐 Minuto {current_minute}: ejecutar fundamental = {should_run}")
    return should_run

# ============================================
# DAG
# ============================================

dag = DAG(
    'yahoo_pipeline',
    default_args=default_args,
    description='Pipeline Yahoo Finance: 1min, 5min y fundamentales',
    schedule_interval='*/1 * * * *',  # Cada 1 minuto
    catchup=False,
    max_active_runs=1,
    tags=['yahoo', 'finance']
)

# ============================================
# TAREAS FETCH
# ============================================

fetch_1min = PythonOperator(
    task_id='fetch_1min',
    python_callable=fetch_intraday_data,
    op_kwargs={'frequency': '1min'},
    provide_context=True,
    dag=dag,
)

fetch_5min = PythonOperator(
    task_id='fetch_5min',
    python_callable=fetch_intraday_data,
    op_kwargs={'frequency': '5min'},
    provide_context=True,
    dag=dag,
)

fetch_fund = PythonOperator(
    task_id='fetch_fundamental',
    python_callable=fetch_fundamental_data,
    provide_context=True,
    dag=dag,
)

# ============================================
# TAREAS LOAD
# ============================================

load_1min = PythonOperator(
    task_id='load_1min',
    python_callable=load_data_1min,
    provide_context=True,
    dag=dag,
)

load_5min = PythonOperator(
    task_id='load_5min',
    python_callable=load_data_5min,
    provide_context=True,
    dag=dag,
)

load_fund = PythonOperator(
    task_id='load_fundamental',
    python_callable=load_fundamental_data,
    provide_context=True,
    dag=dag,
)

# ============================================
# TAREAS DE CONTROL (ShortCircuit) - ¡NUEVO!
# ============================================

check_5min = ShortCircuitOperator(
    task_id='check_5min',
    python_callable=should_run_5min,
    provide_context=True,
    dag=dag,
)

check_15min = ShortCircuitOperator(
    task_id='check_15min',
    python_callable=should_run_15min,
    provide_context=True,
    dag=dag,
)

# ============================================
# DEPENDENCIAS
# ============================================

# 1min: siempre se ejecuta
fetch_1min >> load_1min

# 5min: solo si check_5min retorna True
check_5min >> fetch_5min >> load_5min

# Fundamental: solo si check_15min retorna True
check_15min >> fetch_fund >> load_fund