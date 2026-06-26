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

dag = DAG(
    'yahoo_pipeline',
    default_args=default_args,
    schedule_interval='*/1 * * * *',
    catchup=False,
    max_active_runs=1
)

# ============================================
# TAREAS
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

load_1min = PythonOperator(
    task_id='load_1min',
    python_callable=insert_intraday,
    op_kwargs={'table_name': 'raw_intraday_1min'},
    dag=dag,
)

load_5min = PythonOperator(
    task_id='load_5min',
    python_callable=insert_intraday,
    op_kwargs={'table_name': 'raw_intraday_5min'},
    dag=dag,
)

load_fund = PythonOperator(
    task_id='load_fundamental',
    python_callable=insert_fundamental,
    dag=dag,
)

# ============================================
# DEPENDENCIAS
# ============================================

fetch_1min >> load_1min
fetch_5min >> load_5min
fetch_fund >> load_fund