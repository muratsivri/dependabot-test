# Airflow + Dependabot Demo

GitHub'ın güvenlik araçlarını (Dependabot, CodeQL) gerçekçi bir projede test etmek için hazırlanmış, **bilerek** zafiyetli bir örnek repo. Üç parçadan oluşur: Airflow DAG'ları, bir FastAPI servisi ve bir Node.js paneli.

> ⚠️ Bu repo bilerek güvensizdir. Hiçbir parçasını üretimde kullanma veya internete açma.

## İçerik

```
.
├── Dockerfile, docker-compose.yaml   # Yerel Airflow 2.10.5 (LocalExecutor + Postgres)
├── requirements.txt                  # Airflow + DAG paketleri (eski sürümler)
├── dags/                             # 3 örnek DAG (biri bilerek güvensiz)
├── tests/                            # DAG testleri
├── api/                              # FastAPI servisi
│   ├── main.py                       # Bilerek güvensiz endpoint'ler
│   ├── requirements.txt              # Eski FastAPI, starlette, pyjwt, aiohttp...
│   └── tests/
├── dashboard/                        # Node.js / Express paneli
│   ├── server.js                     # Bilerek güvensiz endpoint'ler
│   ├── package.json + package-lock.json
│   └── test/
└── .github/
    ├── dependabot.yml                # Sadece güvenlik güncellemeleri
    └── workflows/
        ├── ci.yml                    # DAG + API + panel testleri
        ├── codeql.yml                # Python, JavaScript, Actions taraması
        └── release.yml               # Bilerek zafiyetli bir action içerir
```

## Dependabot'un bulması beklenenler

| Ekosistem | Dosya | Örnek paketler | Not |
|---|---|---|---|
| pip | `requirements.txt` | apache-airflow 2.10.5, urllib3, requests, jinja2, certifi, idna | Airflow çekirdeğinin kendi açıkları da görünür |
| pip | `api/requirements.txt` | fastapi, starlette, python-multipart, pyjwt, cryptography, pyyaml, aiohttp, gunicorn | Kod çalıştırma, DoS, request smuggling gibi farklı türler |
| npm | `dashboard/package-lock.json` | minimist (**Critical**), lodash, axios, express, jsonwebtoken, moment, node-fetch | express'in getirdiği **dolaylı** (transitive) paketler de: qs, body-parser, path-to-regexp |
| github-actions | `.github/workflows/release.yml` | actions/download-artifact 4.1.2 | CVE-2024-42471 |

Docker image'ları (`apache/airflow`, `postgres`) Dependabot güvenlik taraması kapsamında **değildir**; onlar için Trivy gibi ayrı bir araç gerekir.

## CodeQL'in bulması beklenenler

| Dosya | Endpoint / yer | Açık türü |
|---|---|---|
| `api/main.py` | `/dags/search` | SQL injection |
| `api/main.py` | `/logs` | Path traversal |
| `api/main.py` | `/ping` | Komut enjeksiyonu |
| `api/main.py` | `/hello` | Reflected XSS |
| `api/main.py` | `/config` | Güvensiz YAML yükleme |
| `api/main.py` | `/me` | İmzası doğrulanmayan JWT |
| `dashboard/server.js` | `/greet` | Reflected XSS |
| `dashboard/server.js` | `/proxy` | SSRF |
| `dashboard/server.js` | `/settings` | Prototype pollution |
| `dashboard/server.js` | `/whoami` | İmzası doğrulanmayan JWT |
| `dags/insecure_example_dag.py` | — | TLS doğrulaması kapalı, MD5 ile şifre |
| `dags/etl_example_dag.py` | — | Jinja2 autoescape kapalı |

## Dependabot yapılandırması

`dependabot.yml` sadece güvenlik odaklıdır:

- `open-pull-requests-limit: 0` ile "yeni sürüm çıktı" PR'ları kapalı.
- Her ekosistemde güvenlik düzeltmeleri tek PR'da gruplanır.
- Hangi açıklar için PR açılacağını repo ayarlarındaki **auto-triage kuralları** belirler (Settings → Advanced Security → Dependabot rules). Bu repoda: High/Critical → PR aç, Moderate/Low → otomatik kapat.

## Yerelde çalıştırma

**Airflow** (Docker gerekli):
```bash
echo "AIRFLOW_UID=$(id -u)" > .env     # sadece Linux
docker compose up airflow-init
docker compose up -d                   # http://localhost:8080  (airflow / airflow)
```

**API** (Python 3.12):
```bash
cd api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v tests/
uvicorn main:app --reload               # http://localhost:8000/docs
```

**Panel** (Node.js 20+):
```bash
cd dashboard
npm ci --ignore-scripts
npm test
npm start                               # http://localhost:3000/dags
```

## Bir PR'ı değerlendirirken

1. Uyarı sayfasında **severity**, **EPSS** ve **"Affected usages"** kısmına bak: açık senin kullandığın fonksiyonda mı?
2. PR'daki sürüm notlarında güvenlik dışı **kırıcı değişiklikleri** (örneğin bir Python sürümü desteğinin kalkması) kontrol et.
3. CI yeşil değilse merge etme; genelde sebep, birbirine bağımlı iki paketin ayrı ayrı güncellenmesidir.
