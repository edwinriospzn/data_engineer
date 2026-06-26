from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
sys.path.append('/opt/airflow/scripts')

from yahoo_utils import fetch_intraday_data, fetch_fundamental_data
from db_utils import insert_intraday, insert_fundamental

default_args = {
    'owner': 'data_engineer',
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# ============================================
# FUNCIONES LOAD (Puente entre XCom y DB)
# ============================================

def load_data_1min(**context):
    ti = context['ti']
    records = ti.xcom_pull(task_ids='fetch_1min')
    if records:
        insert_intraday(records, 'raw_intraday_1min')
    else:
        raise ValueError("No se recibieron datos de fetch_1min")

def load_data_5min(**context):
    ti = context['ti']
    records = ti.xcom_pull(task_ids='fetch_5min')
    if records:
        insert_intraday(records, 'raw_intraday_5min')
    else:
        raise ValueError("No se recibieron datos de fetch_5min")

def load_fundamental_data(**context):
    ti = context['ti']
    records = ti.xcom_pull(task_ids='fetch_fundamental')
    if records:
        insert_fundamental(records)
    else:
        raise ValueError("No se recibieron datos fundamentales")

# ============================================
# DAG
# ============================================

dag = DAG(
    'yahoo_pipeline',
    default_args=default_args,
    schedule_interval='*/5 * * * *',
    catchup=False,
    max_active_runs=1
)

# ============================================
# TAREAS FETCH
# ============================================

fetch_1min = PythonOperator(
    task_id='fetch_1min',
    python_callable=fetch_intraday_data,
    op_kwargs={'frequency': '1min'},
    dag=dag,
)

fetch_5min = PythonOperator(
    task_id='fetch_5min',
    python_callable=fetch_intraday_data,
    op_kwargs={'frequency': '5min'},
    dag=dag,
)

fetch_fund = PythonOperator(
    task_id='fetch_fundamental',
    python_callable=fetch_fundamental_data,
    dag=dag,
)

# ============================================
# TAREAS LOAD
# ============================================

load_1min = PythonOperator(
    task_id='load_1min',
    python_callable=load_data_1min,
    dag=dag,
)

load_5min = PythonOperator(
    task_id='load_5min',
    python_callable=load_data_5min,
    dag=dag,
)

load_fund = PythonOperator(
    task_id='load_fundamental',
    python_callable=load_fundamental_data,
    dag=dag,
)

# ============================================
# DEPENDENCIAS
# ============================================

fetch_1min >> load_1min
fetch_5min >> load_5min
fetch_fund >> load_fund