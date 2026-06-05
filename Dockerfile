FROM apache/airflow:2.8.1-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

USER airflow

# Install extra python dependencies on top of airflow image
COPY requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

# Copy dags and dbt project
COPY dags/ /opt/airflow/dags/
COPY dbt_project/ /opt/airflow/dbt_project/

EXPOSE 8080
