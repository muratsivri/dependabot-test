"""!!! BILEREK GUVENSIZ ORNEK SERVIS !!!

Airflow DAG kayitlarini sorgulayan kucuk bir FastAPI servisi. CodeQL'in
gercek web kodunda hangi aciklari yakaladigini gostermek icin yazildi.
Uretimde KULLANMAYIN, internete ACMAYIN.

Beklenen CodeQL bulgulari (endpoint -> kural):
  /dags/search  -> py/sql-injection            (SQL'e f-string ile girdi)
  /logs         -> py/path-injection           (dosya yolu kullanicidan)
  /ping         -> py/command-line-injection   (shell=True + girdi)
  /hello        -> py/reflective-xss           (girdi HTML'e kacissiz)
  /config       -> py/unsafe-deserialization   (yaml.Loader ile yukleme)
  /me           -> py/jwt-missing-verification (imza dogrulanmiyor)
"""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import jwt
import yaml
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "dags.db"
LOG_DIR = BASE_DIR / "logs"

app = FastAPI(title="Airflow Demo API", version="0.1.0")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    (LOG_DIR / "hello_world.log").write_text("hello_world basariyla calisti\n")
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS dags (dag_id TEXT PRIMARY KEY, owner TEXT, schedule TEXT)"
        )
        conn.executemany(
            "INSERT OR IGNORE INTO dags VALUES (?, ?, ?)",
            [
                ("hello_world", "murat", "@daily"),
                ("etl_example", "murat", "@hourly"),
                ("insecure_example", "demo", "None"),
            ],
        )


init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/dags/search")
def search_dags(name: str) -> list[dict]:
    # KOTU: Kullanici girdisi SQL'e dogrudan ekleniyor.
    query = f"SELECT dag_id, owner, schedule FROM dags WHERE dag_id LIKE '%{name}%'"
    with get_db() as conn:
        rows = conn.execute(query).fetchall()
    return [dict(r) for r in rows]


@app.get("/logs", response_class=PlainTextResponse)
def read_log(file: str) -> str:
    # KOTU: "../../etc/passwd" gibi yollarla klasor disina cikilabilir.
    path = LOG_DIR / file
    if not path.exists():
        raise HTTPException(status_code=404, detail="Log bulunamadi")
    return path.read_text()


@app.get("/ping", response_class=PlainTextResponse)
def ping(host: str) -> str:
    # KOTU: "example.com; rm -rf /" gibi girdilerle komut calistirilabilir.
    result = subprocess.run(
        f"ping -c 1 {host}", shell=True, capture_output=True, text=True, timeout=5
    )
    return result.stdout or result.stderr


@app.get("/hello", response_class=HTMLResponse)
def hello(name: str = "misafir") -> str:
    # KOTU: Girdi HTML'e kacis yapilmadan yaziliyor (XSS).
    return f"<h1>Merhaba {name}</h1>"


@app.post("/config")
async def upload_config(file: UploadFile) -> dict:
    # KOTU: yaml.Loader ile guvenilmeyen icerik Python nesnesine donusturuluyor.
    content = await file.read()
    data = yaml.load(content, Loader=yaml.Loader)
    return {"keys": sorted(data) if isinstance(data, dict) else []}


@app.get("/me")
def whoami(token: str) -> dict:
    # KOTU: JWT imzasi dogrulanmadan icerigine guveniliyor.
    payload = jwt.decode(token, options={"verify_signature": False})
    return {"user": payload.get("sub", "bilinmiyor")}
