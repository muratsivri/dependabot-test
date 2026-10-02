# Airflow + Dependabot Demo

Yerelde Airflow 2.10.5 çalıştıran, örnek DAG'lar içeren ve GitHub'ın güvenlik araçlarını (Dependabot, CodeQL) test etmek için **bilerek** eski/zafiyetli bağımlılıklar barındıran bir örnek repo.

## İçerik

```
.
├── Dockerfile                    # apache/airflow:2.10.5-python3.12 + requirements.txt
├── docker-compose.yaml           # Postgres + webserver + scheduler (LocalExecutor)
├── requirements.txt              # Bilerek eski paketler (Dependabot test)
├── dags/
│   ├── hello_world_dag.py        # Basit Bash + Python görevi
│   ├── etl_example_dag.py        # TaskFlow API ile mini ETL
│   └── insecure_example_dag.py   # Bilerek güvensiz kod (CodeQL test)
├── tests/test_dag_integrity.py   # DAG import/yapı testleri
└── .github/
    ├── dependabot.yml            # pip, docker, docker-compose, github-actions
    └── workflows/
        ├── ci.yml                # Her PR'da DAG testleri
        └── codeql.yml            # Kod taraması
```

## 1. Airflow'u yerelde çalıştır

Gereksinim: Docker Desktop (en az 4 GB RAM ayrılmış olmalı).

```bash
# Linux'ta dosya izinleri için (macOS/Windows'ta gerekmez)
echo "AIRFLOW_UID=$(id -u)" > .env

docker compose up airflow-init    # DB'yi hazırlar, kullanıcı oluşturur
docker compose up -d              # Servisleri başlatır
```

Arayüz: http://localhost:8080 — kullanıcı `airflow`, şifre `airflow`.

DAG'lar duraklatılmış başlar; arayüzden açıp ▶ ile tetikleyebilirsin.

Komut satırından tek DAG test etmek için:

```bash
docker compose exec airflow-scheduler airflow dags test etl_example
```

Kapatmak için: `docker compose down` (verileri de silmek için `-v` ekle).

## 2. Testleri yerelde çalıştır (Docker olmadan, isteğe bağlı)

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install "apache-airflow==2.10.5" pytest \
  --constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt
pip install "apache-airflow==2.10.5" -r requirements.txt
export AIRFLOW_HOME=$PWD/.airflow AIRFLOW__CORE__LOAD_EXAMPLES=false
airflow db migrate
pytest -v tests/
```

## 3. GitHub'a gönder

GitHub'da boş bir repo oluştur (README eklemeden), sonra:

```bash
git init -b main
git add .
git commit -m "Airflow + Dependabot demo"
git remote add origin https://github.com/<kullanici>/airflow-dependabot-demo.git
git push -u origin main
```

## 4. Güvenlik özelliklerini aç

Repo → **Settings → Advanced Security** (bazı hesaplarda "Code security") bölümünde:

| Özellik | Ne yapar |
|---|---|
| Dependency graph | Bağımlılıkları çıkarır (diğerlerinin ön koşulu) |
| Dependabot alerts | Zafiyetli paketler için uyarı |
| Dependabot security updates | Zafiyetler için otomatik düzeltme PR'ı |
| Grouped security updates | Güvenlik PR'larını tek PR'da toplar (isteğe bağlı) |
| Code scanning | CodeQL sonuçları (`codeql.yml` zaten bunu çalıştırır) |
| Secret scanning + Push protection | Sızan anahtarları yakalar/push'u engeller |

> `dependabot.yml` dosyası **sürüm güncellemelerini** (version updates) yönetir. Güvenlik uyarıları ve güvenlik PR'ları ise yukarıdaki ayarlardan açılır; ikisi ayrı mekanizmalardır.

## 5. Beklenen sonuçlar

**Security → Dependabot** sekmesinde `requirements.txt` için uyarılar:

| Paket | Sürüm | Örnek açık |
|---|---|---|
| requests | 2.31.0 | CVE-2024-35195 |
| jinja2 | 3.1.2 | CVE-2024-22195, CVE-2024-34064 |
| certifi | 2022.9.24 | CVE-2022-23491, CVE-2023-37920 |
| idna | 3.6 | CVE-2024-3651 |
| urllib3 | 1.26.17 | CVE-2023-45803, CVE-2024-37891 |

**Pull requests** sekmesinde Dependabot PR'ları:

- `deps(pip)`: Python paket güncellemeleri (minor/patch'ler tek grupta)
- `deps(docker)`: `apache/airflow` 2.x içindeki yeni sürümler (3.x bilerek hariç)
- `deps(compose)`: `postgres:13` → daha yeni major
- `deps(actions)`: `actions/checkout@v3`, `actions/setup-python@v4` güncellemeleri

Her PR'da **DAG testleri** çalışır; güncelleme bir DAG'ı bozarsa PR kırmızı olur.

**Security → Code scanning** sekmesinde `insecure_example_dag.py` için bulgular:

- TLS doğrulaması kapalı istek (`verify=False`)
- Şifre için zayıf hash (MD5)

## 6. Elle tetikleme ve ipuçları

- İlk taramayı beklemek istemezsen: **Insights → Dependency graph → Dependabot** sekmesinde her ekosistem için "Check for updates" butonu var.
- Bir Dependabot PR'ında yorum olarak komut yazabilirsin: `@dependabot rebase`, `@dependabot recreate`, `@dependabot ignore this major version` vb.
- Org genelinde tüm repolar için açmak: **Organization Settings → Advanced Security → Configurations** üzerinden bir güvenlik yapılandırması oluşturup tüm repolara uygula.

## Uyarı

Bu repo bilerek güvensizdir. `insecure_example_dag.py` ve `requirements.txt` içindeki sürümleri gerçek projelerde kullanma.
