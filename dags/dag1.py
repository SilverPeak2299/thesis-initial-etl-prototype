from airflow.sdk import DAG
from airflow.sdk.operators.python import PythonOperator

from datetime import datetime, timedelta
import pandas as pd
import requests

default_args = {
    dag_id="api_etl_example",
    default_args=default_args,
    start_date=datetime(2025, 9, 16),
    schedule_interval="@daily",
    catchup=False,
}



