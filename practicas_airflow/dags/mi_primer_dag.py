from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator

# 1. Definimos los argumentos por defecto del DAG
default_args = {
    'owner': 'edwin',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 2. Inicializamos el DAG
with DAG(
    'practica_pagila_operator',
    default_args=default_args,
    description='Mi primer DAG interactuando con la base de datos Pagila',
    schedule_interval=None, # Solo se ejecutará de forma manual
    catchup=False,
) as dag:

    # Tarea 1: Crear una tabla de prueba en la base de datos pagila
    crear_tabla = PostgresOperator(
        task_id='crear_tabla_sugerencias',
        postgres_conn_id='pagila_conn', # El ID de conexión que acabas de guardar
        sql="""
            CREATE TABLE IF NOT EXISTS sugerencias_peliculas (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
    )

    # Tarea 2: Insertar una película de prueba
    insertar_pelicula = PostgresOperator(
        task_id='insertar_pelicula_prueba',
        postgres_conn_id='pagila_conn',
        sql="""
            INSERT INTO sugerencias_peliculas (titulo) 
            VALUES ('Inception (Recomendada por Airflow)');
        """
    )

    # 3. Definimos el orden de ejecución (Flujo)
    crear_tabla >> insertar_pelicula
