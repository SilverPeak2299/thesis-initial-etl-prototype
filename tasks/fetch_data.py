import json
import os
from typing import Dict, List, Tuple

import boto3
import requests


EDGAR_COMPANIES: Dict[str, str] = {
    "AAPL": "0000320193",  # Apple
    "MSFT": "0000789019",  # Microsoft
    "AMZN": "0001018724",  # Amazon
    "GOOG": "0001652044",  # Alphabet
    "TSLA": "0001318605",  # Tesla
}


def _s3_uri(bucket: str, key: str) -> str:
    return f"s3://{bucket}/{key}"


def fetch_data(
    raw_bucket: str,
    raw_prefix: str,
    run_date: str,
    run_id: str,
    user_agent: str,
    region: str,
) -> List[str]:
    """
    Fetch EDGAR submissions JSON for a fixed set of companies and upload to S3.
    Returns a list of S3 URIs for the raw files written.
    """
    if not raw_bucket:
        raise ValueError("raw_bucket is required")
    if not user_agent:
        raise ValueError("user_agent is required for EDGAR requests")

    session = boto3.session.Session(region_name=region or os.getenv("AWS_REGION"))
    s3 = session.client("s3")

    headers = {"User-Agent": user_agent}
    written: List[str] = []

    for ticker, cik in EDGAR_COMPANIES.items():
        resp = requests.get(
            url=f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()

        key = (
            f"{raw_prefix}/company={ticker}/run_date={run_date}/"
            f"run_id={run_id}/submissions.json"
        )
        s3.put_object(
            Bucket=raw_bucket,
            Key=key,
            Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json",
        )
        written.append(_s3_uri(raw_bucket, key))

    return written


if __name__ == "__main__":
    # Basic local sanity check; expects AWS creds configured in your environment.
    fetch_data(
        raw_bucket=os.getenv("S3_RAW_BUCKET", ""),
        raw_prefix=os.getenv("S3_RAW_PREFIX", "raw/edgar"),
        run_date=os.getenv("RUN_DATE", "1970-01-01"),
        run_id=os.getenv("RUN_ID", "manual"),
        user_agent=os.getenv("EDGAR_USER_AGENT", ""),
        region=os.getenv("AWS_REGION", "us-east-1"),
    )
