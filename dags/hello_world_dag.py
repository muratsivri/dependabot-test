"""En basit ornek: bir Bash ve bir Python gorevi."""

from __future__ import annotations

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


def say_hello(**context):
    print(f"Merhaba! Calisma tarihi: {context['ds']}")


with DAG(
    dag_id="hello_world",
    start_date=pendulum.datetime(2026, 1, 1, tz="Europe/Istanbul"),
    schedule="@daily",
    catchup=False,
    tags=["ornek"],
    default_args={"retries": 1},
) as dag:
    print_date = BashOperator(task_id="print_date", bash_command="date")
    hello = PythonOperator(task_id="say_hello", python_callable=say_hello)

    print_date >> hello
