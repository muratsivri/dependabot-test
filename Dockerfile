FROM apache/airflow:2.10.5-python3.12

COPY requirements.txt /requirements.txt

# Airflow surumunu sabitleyerek ek paketleri kur; boylece pip
# Airflow'u yanlislikla yukseltmez/dusurmez.
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt
