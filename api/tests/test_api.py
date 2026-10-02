"""API'nin temel islevlerinin testleri.

Dependabot bir paketi guncelledigi zaman (orn. fastapi/starlette) bu testler
CI'da calisir ve API'nin hala ayakta oldugunu dogrular.
"""

import sys
from pathlib import Path

import jwt
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import app  # noqa: E402

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_search_dags():
    response = client.get("/dags/search", params={"name": "etl"})
    assert response.status_code == 200
    assert [d["dag_id"] for d in response.json()] == ["etl_example"]


def test_read_log():
    response = client.get("/logs", params={"file": "hello_world.log"})
    assert "basariyla" in response.text


def test_hello():
    assert "Merhaba Murat" in client.get("/hello", params={"name": "Murat"}).text


def test_upload_config():
    files = {"file": ("config.yaml", b"retries: 3\nowner: murat\n", "application/x-yaml")}
    response = client.post("/config", files=files)
    assert response.json() == {"keys": ["owner", "retries"]}


def test_whoami():
    token = jwt.encode({"sub": "murat"}, "test-anahtari", algorithm="HS256")
    assert client.get("/me", params={"token": token}).json() == {"user": "murat"}
