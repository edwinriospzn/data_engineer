import csv
import os
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator

os.environ["AIRFLOW_CONN_ETL_POSTGRES"] = "postgres://etl_user:etl_pass@etl-postgres:5432/dbdags"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "06"


@task
def load_data():
    data = {}
    for f in ["members", "books", "loans"]:
        with open(DATA_DIR / f"{f}.csv", "r", encoding="utf-8") as file:
            data[f] = list(csv.DictReader(file))
    return data


@task
def process_data(data):
    members = {m["member_id"]: m["name"] for m in data["members"]}
    books = {b["book_id"]: b["title"] for b in data["books"]}
    
    loans = data["loans"]
    total_fees = sum(float(l["fee"]) for l in loans)
    
    # Top member (most loans)
    member_counts = {}
    book_counts = {}
    for l in loans:
        member_counts[l["member_id"]] = member_counts.get(l["member_id"], 0) + 1
        book_counts[l["book_id"]] = book_counts.get(l["book_id"], 0) + 1
    
    top_member_id = max(member_counts, key=member_counts.get)
    top_book_id = max(book_counts, key=book_counts.get)
    
    return {
        "total_loans": len(loans),
        "total_fees": total_fees,
        "avg_fee": total_fees / len(loans) if loans else 0,
        "top_member": members.get(top_member_id, "Unknown"),
        "top_book": books.get(top_book_id, "Unknown"),
    }


@task
def generate_report(stats):
    report = f"""
═══════════════════════════════════════════
            LIBRARY REPORT                 
═══════════════════════════════════════════
╠ *Total loans:    {stats['total_loans']:>4}
╠ *Total fees:     ${stats['total_fees']:>7.2f}
╠ *Avg fee:        ${stats['avg_fee']:>7.2f}
╠ *Top member:     {stats['top_member']:<15}
╠ *Top book:       {stats['top_book']:<15}
═══════════════════════════════════════════
"""
    print(report)
    return report


with DAG(
    dag_id="06_xcom",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["learning", "xcom", "taskflow"],
) as dag:
    start = EmptyOperator(task_id="start")
    
    data = load_data()
    stats = process_data(data)
    report = generate_report(stats)
    
    end = EmptyOperator(task_id="end")
    
    start >> data >> stats >> report >> end