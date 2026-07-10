import csv
import os
from datetime import datetime
from pathlib import Path

import psycopg2
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

os.environ["AIRFLOW_CONN_ETL_POSTGRES"] = "postgres://etl_user:etl_pass@etl-postgres:5432/dbdags"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "10"
DB_HOST = "etl-postgres"
DB_PORT = 5432
DB_NAME = "dbdags"
DB_USER = "etl_user"
DB_PASSWORD = "etl_pass"


def read_csv(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_data(table_name, rows, columns):
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join(columns)
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        for row in rows:
            cur.execute(sql, tuple(row[col] for col in columns))
    conn.commit()
    conn.close()


def create_tables():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        # Drop existing tables
        cur.execute("DROP TABLE IF EXISTS t10_student_performance")
        cur.execute("DROP TABLE IF EXISTS t10_enrollments")
        cur.execute("DROP TABLE IF EXISTS t10_courses")
        cur.execute("DROP TABLE IF EXISTS t10_students")
        
        # Create students table
        cur.execute("""
            CREATE TABLE t10_students (
                student_id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                major TEXT,
                year INTEGER,
                enrollment_date DATE,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create courses table
        cur.execute("""
            CREATE TABLE t10_courses (
                course_id INTEGER PRIMARY KEY,
                course_name TEXT,
                credits INTEGER,
                department TEXT,
                instructor TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create enrollments table
        cur.execute("""
            CREATE TABLE t10_enrollments (
                enrollment_id INTEGER PRIMARY KEY,
                student_id INTEGER REFERENCES t10_students(student_id),
                course_id INTEGER REFERENCES t10_courses(course_id),
                enrollment_date DATE,
                grade TEXT,
                status TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()


def load_students():
    rows = read_csv("students.csv")
    load_data("t10_students", rows, ["student_id", "name", "email", "major", "year", "enrollment_date"])


def load_courses():
    rows = read_csv("courses.csv")
    load_data("t10_courses", rows, ["course_id", "course_name", "credits", "department", "instructor"])


def load_enrollments():
    rows = read_csv("enrollments.csv")
    load_data("t10_enrollments", rows, ["enrollment_id", "student_id", "course_id", "enrollment_date", "grade", "status"])


def print_results(**context):
    """Print results from SQL queries for visibility."""
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        # Show final results
        cur.execute("""
            SELECT 
                s.name,
                s.major,
                COUNT(e.enrollment_id) as courses,
                ROUND(AVG(CASE 
                    WHEN e.grade = 'A' THEN 4.0
                    WHEN e.grade = 'A-' THEN 3.7
                    WHEN e.grade = 'B+' THEN 3.3
                    WHEN e.grade = 'B' THEN 3.0
                    WHEN e.grade = 'B-' THEN 2.7
                    WHEN e.grade = 'C+' THEN 2.3
                    WHEN e.grade = 'C' THEN 2.0
                    ELSE 0
                END)::numeric, 2) as gpa
            FROM t10_students s
            JOIN t10_enrollments e ON s.student_id = e.student_id
            GROUP BY s.name, s.major
            ORDER BY gpa DESC
            LIMIT 5
        """)
        
        print("\n🏆 TOP 5 STUDENTS BY GPA:")
        for row in cur.fetchall():
            print(f"   {row[0]} ({row[1]}) - {row[2]} courses, GPA: {row[3]}")
    conn.close()


with DAG(
    dag_id="10_sql_operator_pro",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "sql", "university"],
) as dag:
    start = EmptyOperator(task_id="start")
    
    # 1. Create tables
    create = PythonOperator(task_id="create_tables", python_callable=create_tables)
    
    # 2. Load data
    load_students = PythonOperator(task_id="load_students", python_callable=load_students)
    load_courses = PythonOperator(task_id="load_courses", python_callable=load_courses)
    load_enrollments = PythonOperator(task_id="load_enrollments", python_callable=load_enrollments)
    
    # 3. SQL Queries using PostgresOperator
    
    # Query 1: Basic SELECT - Students by major
    query_students_by_major = PostgresOperator(
        task_id="students_by_major",
        postgres_conn_id="etl_postgres",
        sql="""
            SELECT major, COUNT(*) as student_count 
            FROM t10_students 
            GROUP BY major 
            ORDER BY student_count DESC;
        """
    )
    
    # Query 2: JOIN - Student enrollment details
    query_enrollment_details = PostgresOperator(
        task_id="enrollment_details",
        postgres_conn_id="etl_postgres",
        sql="""
            SELECT s.name, c.course_name, e.grade, e.status
            FROM t10_students s
            JOIN t10_enrollments e ON s.student_id = e.student_id
            JOIN t10_courses c ON e.course_id = c.course_id
            ORDER BY s.name, c.course_name
            LIMIT 10;
        """
    )
    
    # Query 3: Aggregation - Grade distribution
    query_grade_distribution = PostgresOperator(
        task_id="grade_distribution",
        postgres_conn_id="etl_postgres",
        sql="""
            SELECT c.course_name, e.grade, COUNT(*) as count
            FROM t10_enrollments e
            JOIN t10_courses c ON e.course_id = c.course_id
            GROUP BY c.course_name, e.grade
            ORDER BY c.course_name, e.grade;
        """
    )
    
    # Query 4: Window function - Rank students by grade
    query_student_ranking = PostgresOperator(
        task_id="student_ranking",
        postgres_conn_id="etl_postgres",
        sql="""
            SELECT 
                s.name,
                c.course_name,
                e.grade,
                RANK() OVER (PARTITION BY c.course_id ORDER BY 
                    CASE 
                        WHEN e.grade = 'A' THEN 4.0
                        WHEN e.grade = 'A-' THEN 3.7
                        WHEN e.grade = 'B+' THEN 3.3
                        WHEN e.grade = 'B' THEN 3.0
                        WHEN e.grade = 'B-' THEN 2.7
                        WHEN e.grade = 'C+' THEN 2.3
                        WHEN e.grade = 'C' THEN 2.0
                        ELSE 0
                    END DESC) as rank_in_course
            FROM t10_students s
            JOIN t10_enrollments e ON s.student_id = e.student_id
            JOIN t10_courses c ON e.course_id = c.course_id
            ORDER BY c.course_name, rank_in_course;
        """
    )
    
    # Query 5: Create student performance table
    create_performance_table = PostgresOperator(
        task_id="create_performance_table",
        postgres_conn_id="etl_postgres",
        sql="""
            DROP TABLE IF EXISTS t10_student_performance;
            
            CREATE TABLE t10_student_performance AS
            SELECT 
                s.student_id,
                s.name,
                s.major,
                COUNT(e.enrollment_id) as total_courses,
                ROUND(AVG(CASE 
                    WHEN e.grade = 'A' THEN 4.0
                    WHEN e.grade = 'A-' THEN 3.7
                    WHEN e.grade = 'B+' THEN 3.3
                    WHEN e.grade = 'B' THEN 3.0
                    WHEN e.grade = 'B-' THEN 2.7
                    WHEN e.grade = 'C+' THEN 2.3
                    WHEN e.grade = 'C' THEN 2.0
                    ELSE 0
                END)::numeric, 2) as gpa
            FROM t10_students s
            JOIN t10_enrollments e ON s.student_id = e.student_id
            GROUP BY s.student_id, s.name, s.major
            ORDER BY gpa DESC;
        """
    )
    
    # Query 6: Department performance
    query_department_performance = PostgresOperator(
        task_id="department_performance",
        postgres_conn_id="etl_postgres",
        sql="""
            SELECT 
                c.department,
                COUNT(DISTINCT s.student_id) as total_students,
                COUNT(e.enrollment_id) as total_enrollments,
                ROUND(AVG(CASE 
                    WHEN e.grade = 'A' THEN 4.0
                    WHEN e.grade = 'A-' THEN 3.7
                    WHEN e.grade = 'B+' THEN 3.3
                    WHEN e.grade = 'B' THEN 3.0
                    WHEN e.grade = 'B-' THEN 2.7
                    WHEN e.grade = 'C+' THEN 2.3
                    WHEN e.grade = 'C' THEN 2.0
                    ELSE 0
                END)::numeric, 2) as avg_gpa
            FROM t10_courses c
            LEFT JOIN t10_enrollments e ON c.course_id = e.course_id
            LEFT JOIN t10_students s ON e.student_id = s.student_id
            GROUP BY c.department
            ORDER BY avg_gpa DESC;
        """
    )
    
    # Query 7: Update - Update course credits
    update_course_credits = PostgresOperator(
        task_id="update_course_credits",
        postgres_conn_id="etl_postgres",
        sql="""
            UPDATE t10_courses 
            SET credits = credits + 1 
            WHERE department = 'Physics';
            
            SELECT course_name, credits 
            FROM t10_courses 
            WHERE department = 'Physics';
        """
    )
    
    # Print results
    print_results = PythonOperator(
        task_id="print_results",
        python_callable=print_results,
        provide_context=True,
    )
    
    end = EmptyOperator(task_id="end")
    
    # Dependencies
    start >> create
    create >> [load_students, load_courses] >> load_enrollments
    load_enrollments >> [
        query_students_by_major,
        query_enrollment_details,
        query_grade_distribution,
        query_student_ranking,
        create_performance_table,
        query_department_performance,
        update_course_credits,
    ] >> print_results >> end