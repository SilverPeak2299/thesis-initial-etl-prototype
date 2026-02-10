import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from tasks.fetch_data import fetch_data
from tasks.glue_job import submit_glue_job, wait_for_glue_job
from tasks.record_manifest import record_manifest


DAG_ID = "edgar_glue_pipeline"

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
RAW_BUCKET = os.getenv("S3_RAW_BUCKET", "")
RAW_PREFIX = os.getenv("S3_RAW_PREFIX", "raw/edgar")
CURATED_BUCKET = os.getenv("S3_CURATED_BUCKET", "")
CURATED_PREFIX = os.getenv("S3_CURATED_PREFIX", "curated/edgar")
GLUE_JOB_NAME = os.getenv("GLUE_JOB_NAME", "")
EDGAR_USER_AGENT = os.getenv("EDGAR_USER_AGENT", "")


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id=DAG_ID,
    default_args=default_args,
    description="EDGAR ingestion to S3 raw with Glue Python Shell transform to curated",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    render_template_as_native_obj=True,
    tags=["edgar", "glue"],
) as dag:
    ingest_raw = PythonOperator(
        task_id="ingest_raw",
        python_callable=fetch_data,
        op_kwargs={
            "raw_bucket": RAW_BUCKET,
            "raw_prefix": RAW_PREFIX,
            "run_date": "{{ ds }}",
            "run_id": "{{ run_id }}",
            "user_agent": EDGAR_USER_AGENT,
            "region": AWS_REGION,
        },
    )

    submit_glue = PythonOperator(
        task_id="submit_glue_job",
        python_callable=submit_glue_job,
        op_kwargs={
            "job_name": GLUE_JOB_NAME,
            "raw_bucket": RAW_BUCKET,
            "raw_prefix": RAW_PREFIX,
            "curated_bucket": CURATED_BUCKET,
            "curated_prefix": CURATED_PREFIX,
            "run_date": "{{ ds }}",
            "run_id": "{{ run_id }}",
            "region": AWS_REGION,
        },
    )

    wait_for_glue = PythonOperator(
        task_id="wait_for_glue_job",
        python_callable=wait_for_glue_job,
        op_kwargs={
            "job_name": GLUE_JOB_NAME,
            "job_run_id": "{{ ti.xcom_pull(task_ids='submit_glue_job') }}",
            "region": AWS_REGION,
        },
    )

    write_manifest = PythonOperator(
        task_id="record_manifest",
        python_callable=record_manifest,
        op_kwargs={
            "raw_uris": "{{ ti.xcom_pull(task_ids='ingest_raw') }}",
            "curated_bucket": CURATED_BUCKET,
            "curated_prefix": CURATED_PREFIX,
            "run_date": "{{ ds }}",
            "run_id": "{{ run_id }}",
            "region": AWS_REGION,
        },
    )

    ingest_raw >> submit_glue >> wait_for_glue >> write_manifest
