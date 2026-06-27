from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
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
    """Carga datos de 1min desde archivo JSON"""
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/1min_{run_id}.json"
    
    logging.info(f"📂 Buscando archivo: {file_path}")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            records = json.load(f)
        logging.info(f"📄 Archivo encontrado: {len(records)} registros")
        insert_intraday(records, 'raw_intraday_1min')
        logging.info(f"✅ Cargados {len(records)} registros de 1min")
        os.remove(file_path)
        logging.info(f"🗑️ Archivo eliminado: {file_path}")
    else:
        ti = context['ti']
        records = ti.xcom_pull(task_ids='fetch_1min')
        if records:
            logging.info(f"📤 Datos recuperados de XCom: {len(records)} registros")
            insert_intraday(records, 'raw_intraday_1min')
            logging.info(f"✅ Cargados {len(records)} registros de 1min desde XCom")
        else:
            raise ValueError(f"No se encontraron datos para fetch_1min (archivo: {file_path}, XCom: vacío)")

def load_data_5min(**context):
    """Carga datos de 5min desde archivo JSON"""
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/5min_{run_id}.json"
    
    logging.info(f"📂 Buscando archivo: {file_path}")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            records = json.load(f)
        logging.info(f"📄 Archivo encontrado: {len(records)} registros")
        insert_intraday(records, 'raw_intraday_5min')
        logging.info(f"✅ Cargados {len(records)} registros de 5min")
        os.remove(file_path)
        logging.info(f"🗑️ Archivo eliminado: {file_path}")
    else:
        ti = context['ti']
        records = ti.xcom_pull(task_ids='fetch_5min')
        if records:
            logging.info(f"📤 Datos recuperados de XCom: {len(records)} registros")
            insert_intraday(records, 'raw_intraday_5min')
            logging.info(f"✅ Cargados {len(records)} registros de 5min desde XCom")
        else:
            raise ValueError(f"No se encontraron datos para fetch_5min (archivo: {file_path}, XCom: vacío)")

def load_fundamental_data(**context):
    """Carga datos fundamentales desde archivo JSON"""
    run_id = context['run_id']
    file_path = f"{DATA_DIR}/fundamental_{run_id}.json"
    
    logging.info(f"📂 Buscando archivo: {file_path}")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            records = json.load(f)
        logging.info(f"📄 Archivo encontrado: {len(records)} registros")
        insert_fundamental(records)
        logging.info(f"✅ Cargados {len(records)} registros fundamentales")
        os.remove(file_path)
        logging.info(f"🗑️ Archivo eliminado: {file_path}")
    else:
        ti = context['ti']
        records = ti.xcom_pull(task_ids='fetch_fundamental')
        if records:
            logging.info(f"📤 Datos recuperados de XCom: {len(records)} registros")
            insert_fundamental(records)
            logging.info(f"✅ Cargados {len(records)} registros fundamentales desde XCom")
        else:
            raise ValueError(f"No se encontraron datos para fetch_fundamental (archivo: {file_path}, XCom: vacío)")

# ============================================
# DAG
# ============================================

dag = DAG(
    'yahoo_pipeline',
    default_args=default_args,
    schedule_interval='*/5 * * * *',
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
# DEPENDENCIAS
# ============================================

fetch_1min >> load_1min
fetch_5min >> load_5min
fetch_fund >> load_fund