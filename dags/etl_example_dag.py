"""TaskFlow API ile kucuk bir ETL ornegi.

Dis servise baglanmadan calisir; jinja2 ile bir rapor uretir.
"""

from __future__ import annotations

import pendulum
from airflow.decorators import dag, task


@dag(
    dag_id="etl_example",
    start_date=pendulum.datetime(2026, 1, 1, tz="Europe/Istanbul"),
    schedule="@hourly",
    catchup=False,
    tags=["ornek", "etl"],
    default_args={"retries": 2},
)
def etl_example():
    @task
    def extract() -> list[dict]:
        return [
            {"urun": "kalem", "adet": 10, "fiyat": 12.5},
            {"urun": "defter", "adet": 4, "fiyat": 40.0},
            {"urun": "silgi", "adet": 25, "fiyat": 3.0},
        ]

    @task
    def transform(rows: list[dict]) -> dict:
        toplam = sum(r["adet"] * r["fiyat"] for r in rows)
        return {"satir_sayisi": len(rows), "toplam_ciro": round(toplam, 2)}

    @task
    def load(summary: dict) -> str:
        from jinja2 import Template

        rapor = Template(
            "{{ satir_sayisi }} urun islendi, toplam ciro: {{ toplam_ciro }} TL"
        ).render(**summary)
        print(rapor)
        return rapor

    load(transform(extract()))


etl_example()
