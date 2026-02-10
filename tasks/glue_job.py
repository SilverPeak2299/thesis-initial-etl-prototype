import os
import time
from typing import Dict, Optional

import boto3


def submit_glue_job(
    job_name: str,
    raw_bucket: str,
    raw_prefix: str,
    curated_bucket: str,
    curated_prefix: str,
    run_date: str,
    run_id: str,
    region: str,
    extra_args: Optional[Dict[str, str]] = None,
) -> str:
    if not job_name:
        raise ValueError("job_name is required")
    session = boto3.session.Session(region_name=region or os.getenv("AWS_REGION"))
    glue = session.client("glue")

    args = {
        "--raw_bucket": raw_bucket,
        "--raw_prefix": raw_prefix,
        "--curated_bucket": curated_bucket,
        "--curated_prefix": curated_prefix,
        "--run_date": run_date,
        "--run_id": run_id,
    }
    if extra_args:
        args.update(extra_args)

    resp = glue.start_job_run(JobName=job_name, Arguments=args)
    return resp["JobRunId"]


def wait_for_glue_job(
    job_name: str,
    job_run_id: str,
    region: str,
    poll_seconds: int = 30,
    timeout_minutes: int = 60,
) -> str:
    session = boto3.session.Session(region_name=region or os.getenv("AWS_REGION"))
    glue = session.client("glue")

    deadline = time.time() + timeout_minutes * 60
    last_state = "UNKNOWN"

    while time.time() < deadline:
        resp = glue.get_job_run(JobName=job_name, RunId=job_run_id)
        state = resp["JobRun"]["JobRunState"]
        last_state = state
        if state in {"SUCCEEDED", "FAILED", "STOPPED", "TIMEOUT"}:
            break
        time.sleep(poll_seconds)

    if last_state != "SUCCEEDED":
        raise RuntimeError(
            f"Glue job {job_name} run {job_run_id} finished with state {last_state}"
        )

    return last_state
