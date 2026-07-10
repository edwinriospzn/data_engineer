# Airflow Learning Journey - DAG Summary

## Overview

This document summarizes all 10 Airflow DAGs created during the learning journey, covering essential concepts from basic DAG structure to advanced topics like dynamic task mapping and Spark integration.

---

## DAG 00: Hello World
- **File:** `00_hello_world.py`
- **Concept:** Basic DAG structure
- **Flow:** `start -> hello_world -> end`
- **Purpose:** Print "Hello, World!" to logs
- **Operators:** `EmptyOperator`, `PythonOperator`
- **Key Learning:** Basic DAG syntax, task dependencies

---

## DAG 01: Load CSV to PostgreSQL
- **File:** `01_load_csv.py`
- **Concept:** Basic ETL with `PythonOperator`
- **Flow:** `start -> read_customers -> create_table -> insert_customers -> end`
- **Purpose:** Load customer data from CSV to PostgreSQL
- **Operators:** `EmptyOperator`, `PythonOperator`
- **Key Learning:** Reading CSV, database connections, XCom push/pull

---

## DAG 02: SQL Transformations
- **File:** `02_sql_transform.py`
- **Concept:** SQL operations with `PostgresOperator`
- **Flow:** `start -> create_tables -> load_products -> load_orders -> calculate_performance -> end`
- **Purpose:** Load products, customers, orders and calculate product performance
- **Operators:** `EmptyOperator`, `PythonOperator`, `PostgresOperator`
- **Key Learning:** SQL transformations, joins, window functions (`RANK`)
- **Tables Created:** `t02_customers`, `t02_products`, `t02_orders`, `t02_product_performance`

---

## DAG 03: Parallel Execution
- **File:** `03_parallel.py`
- **Concept:** Running tasks in parallel
- **Flow:** `start -> split -> process_customers -> log_customers -> join -> end`
  - `process_orders -> log_orders ->`
  - `process_products -> log_products ->`
- **Purpose:** Process multiple CSV files in parallel
- **Operators:** `EmptyOperator`, `PythonOperator`
- **Key Learning:** Fan-out/fan-in patterns, parallel execution

---

## DAG 04: Branching
- **File:** `04_branch.py`
- **Concept:** Conditional execution with `BranchPythonOperator`
- **Flow:** `start -> load_data -> check_size -> process_small -> generate_summary -> end`
  - `process_medium ->`
  - `process_large ->`
- **Purpose:** Process orders differently based on data size (`<30`, `30-80`, `>80`)
- **Operators:** `EmptyOperator`, `PythonOperator`, `BranchPythonOperator`
- **Key Learning:** Conditional branching, `trigger_rule="all_done"`

### Branch Logic
- **Small:** `< 30` orders → light processing
- **Medium:** `30-80` orders → standard processing
- **Large:** `> 80` orders → heavy processing

---

## DAG 05: File Sensor
- **File:** `05_sensor.py`
- **Concept:** Waiting for files with `FileSensor`
- **Flow:** `start -> create_tables -> wait_for_orders -> load_customers -> load_orders -> generate_summary -> end`
- **Purpose:** Wait for `orders.csv` to appear before processing
- **Operators:** `EmptyOperator`, `PythonOperator`, `FileSensor`
- **Key Learning:** Sensors, `poke_interval`, `timeout`, event-driven workflows

### Sensor Configuration
- `FileSensor` with `poke_interval=10`, `timeout=120`, `mode="poke"`

---

## DAG 06: XCom and TaskFlow API
- **File:** `06_xcom.py`
- **Concept:** Passing data between tasks using TaskFlow API
- **Flow:** `start -> load_data -> process_data -> generate_report -> end`
- **Purpose:** Load library data and pass results via XCom
- **Operators:** `EmptyOperator`, `@task` (TaskFlow API)
- **Key Learning:** XCom push/pull, TaskFlow API, automatic data passing

### Data Flow
1. `load_data()` returns data dict → XCom
2. `process_data()` returns stats dict → XCom
3. `generate_report()` returns formatted report

### Files Used
- `members.csv`
- `books.csv`
- `loans.csv`

---

## DAG 07: Dynamic Task Mapping
- **File:** `07_dynamic_mapping.py`
- **Concept:** Dynamic task generation at runtime
- **Flow:** `start -> load_customers -> process_customer (mapped x5) -> generate_summary -> end`
- **Purpose:** Process multiple customers in parallel using dynamic mapping
- **Operators:** `EmptyOperator`, `@task`, `.expand()`
- **Key Learning:** Dynamic Task Mapping, parallel processing of lists

---

## DAG 08: Spark with PySpark
- **File:** `08_spark.py`
- **Concept:** Running Spark jobs with `PythonOperator`
- **Flow:** `start -> run_word_count -> end`
  - `run_sales_processing ->`
- **Purpose:** Run Spark jobs (word count and sales processing)
- **Operators:** `EmptyOperator`, `PythonOperator`
- **Key Learning:** PySpark integration, `SparkSession`, DataFrame operations

### Requirements
- Java installed in container
- PySpark installed via pip (`pyspark` in `requirements.txt`)

### Spark Jobs
- Word Count example
- Sales data processing: category sales, product ranking, daily trends

---

## DAG 10: SQL Operators (University)
- **File:** `10_sql_operator_pro.py`
- **Concept:** Multiple SQL operations with `PostgresOperator`
- **Flow:** `start -> create_tables -> load_students -> load_enrollments -> 7 parallel SQL queries -> print_results -> end`
  - `load_courses ->`
- **Purpose:** Process university data with multiple SQL queries
- **Operators:** `EmptyOperator`, `PythonOperator`, `PostgresOperator`
- **Key Learning:** Multiple SQL query types (`SELECT`, `CREATE`, `UPDATE`, `DELETE`)

### SQL Queries
- Students by major (`GROUP BY`)
- Enrollment details (`JOIN`)
- Grade distribution (`Aggregation`)
- Student ranking (`Window function`)
- Create performance table (`CREATE TABLE AS`)
- Department performance (`Complex query`)
- Update course credits (`UPDATE`)

### Tables
- `t10_students`
- `t10_courses`
- `t10_enrollments`
- `t10_student_performance`

---

## Quick Reference Table
- **DAG 00:** Hello World — `EmptyOperator`, `PythonOperator` — None
- **DAG 01:** Basic ETL — `PythonOperator` — Customers
- **DAG 02:** SQL Transform — `PostgresOperator` — Products, Orders
- **DAG 03:** Parallel — `PythonOperator` — Multiple CSVs
- **DAG 04:** Branching — `BranchPythonOperator` — Orders
- **DAG 05:** Sensors — `FileSensor` — Orders, Customers
- **DAG 06:** XCom — `@task` (TaskFlow) — Library (Members, Books, Loans)
- **DAG 07:** Dynamic Mapping — `@task`, `.expand()` — Customers
- **DAG 08:** Spark — `PythonOperator` — Sales data
- **DAG 10:** SQL Operators — `PostgresOperator` — University (Students, Courses, Enrollments)

---

## Key Learnings Summary

### DAG Structure
```python
with DAG(
    dag_id="dag_name",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning"],
) as dag:
    # Tasks and dependencies
```

### Operators Covered
- `EmptyOperator`: Placeholder/control flow
- `PythonOperator`: Custom Python logic
- `PostgresOperator`: SQL execution
- `BranchPythonOperator`: Conditional branching
- `FileSensor`: Wait for files
- `@task`: TaskFlow API

### Key Patterns
- Fan-out/Fan-in: Parallel execution with split/join
- Branching: Conditional execution paths
- Sensors: Event-driven workflows


Dynamic Mapping: Runtime task generation

XCom: Data sharing between tasks

Database Operations:

CREATE TABLE

INSERT with ON CONFLICT

JOIN queries

Window functions (RANK)

CREATE TABLE AS

UPDATE statements

Spark Integration:

PySpark with PythonOperator

SparkSession configuration

DataFrame operations

Reading CSV with inferSchema

PROJECT STRUCTURE

airflow-learning/
├── dags/
│ ├── 00_hello_world.py
│ ├── 01_load_csv.py
│ ├── 02_sql_transform.py
│ ├── 03_parallel.py
│ ├── 04_branch.py
│ ├── 05_sensor.py
│ ├── 06_xcom.py
│ ├── 07_dynamic_mapping.py
│ ├── 08_spark.py
│ ├── 10_sql_operator_pro.py
│ └── pycache/
├── data/
│ ├── 01/
│ ├── 02/
│ ├── 04/
│ ├── 05/
│ ├── 06/
│ ├── 07/
│ ├── 08/
│ └── 10/
├── sql/
│ ├── create_tables.sql
│ └── insert_data.sql
├── spark/
│ └── scripts/
├── logs/
├── plugins/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── start_prac.sh
├── stop_prac.sh
└── setup_connections.sh

DATA FILES USED

Exercise 01: customers.csv - Customer data
Exercise 02: customers.csv, orders.csv, products.csv - E-commerce data
Exercise 04: customers.csv, orders.csv - Branch test data
Exercise 05: customers.csv, orders.csv, products.csv - Sensor test data
Exercise 06: members.csv, books.csv, loans.csv - Library data
Exercise 07: customers.csv - Customer data
Exercise 08: sales_data.csv - Sales data for Spark
Exercise 10: students.csv, courses.csv, enrollments.csv - University data

DEPENDENCIES (requirements.txt)

pandas
psycopg2-binary
apache-airflow-providers-postgres
pyspark

RUNNING THE PROJECT

./start_prac.sh - Start everything
./stop_prac.sh - Stop everything
./setup_connections.sh - Setup connections
./debug_spark.sh - Debug issues

CONCLUSION

This learning journey covered all essential Airflow concepts:

Basic DAG structure

ETL pipelines with Python

SQL transformations

Parallel execution

Conditional branching

Sensors for event-driven workflows

XCom for data passing

TaskFlow API

Dynamic task mapping

Spark integration with PySpark

Multiple SQL operations

Total: 10 DAGs created with real-world data examples!