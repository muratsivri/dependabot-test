"""!!! BILEREK GUVENSIZ ORNEK !!!

Bu DAG, CodeQL code scanning'in kod seviyesindeki sorunlari yakaladigini
gostermek icin yazildi. Gercek projelerde bu kaliplari KULLANMAYIN.

Beklenen CodeQL bulgulari:
  - py/request-without-cert-validation  (verify=False)
  - py/weak-sensitive-data-hashing      (sifre icin MD5)
"""

from __future__ import annotations

import hashlib

import pendulum
import requests
from airflow.decorators import dag, task


@dag(
    dag_id="insecure_example",
    start_date=pendulum.datetime(2026, 1, 1, tz="Europe/Istanbul"),
    schedule=None,
    catchup=False,
    tags=["ornek", "guvensiz-demo"],
    default_args={"retries": 0},
)
def insecure_example():
    @task
    def fetch_without_tls_check() -> int:
        # KOTU: TLS sertifika dogrulamasi kapali.
        response = requests.get("https://example.com", verify=False, timeout=10)
        return response.status_code

    @task
    def hash_password(password: str = "demo-sifre") -> str:
        # KOTU: Sifre saklamak icin MD5 kullaniliyor.
        return hashlib.md5(password.encode()).hexdigest()

    fetch_without_tls_check()
    hash_password()


insecure_example()
