import argparse
import json
import os
from typing import List

import boto3
import pandas as pd
import awswrangler as wr


def _list_raw_keys(
    s3_client,
    bucket: str,
    prefix: str,
    run_date: str,
    run_id: str,
) -> List[str]:
    paginator = s3_client.get_paginator("list_objects_v2")
    run_token = f"run_date={run_date}/run_id={run_id}/"
    keys: List[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for item in page.get("Contents", []):
            key = item["Key"]
            if run_token in key:
                keys.append(key)
    return keys


def _company_from_key(key: str) -> str:
    for part in key.split("/"):
        if part.startswith("company="):
            return part.split("=", 1)[1]
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_bucket", required=True)
    parser.add_argument("--raw_prefix", required=True)
    parser.add_argument("--curated_bucket", required=True)
    parser.add_argument("--curated_prefix", required=True)
    parser.add_argument("--run_date", required=True)
    parser.add_argument("--run_id", required=True)
    args = parser.parse_args()

    session = boto3.session.Session(region_name=os.getenv("AWS_REGION"))
    s3 = session.client("s3")

    raw_keys = _list_raw_keys(
        s3,
        bucket=args.raw_bucket,
        prefix=args.raw_prefix,
        run_date=args.run_date,
        run_id=args.run_id,
    )
    if not raw_keys:
        raise RuntimeError("No raw files found for provided run_date/run_id")

    frames = []
    for key in raw_keys:
        obj = s3.get_object(Bucket=args.raw_bucket, Key=key)
        payload = json.loads(obj["Body"].read().decode("utf-8"))
        recent = payload.get("filings", {}).get("recent", {})
        if not recent:
            continue
        df = pd.DataFrame(recent)
        df["company_ticker"] = _company_from_key(key)
        df["run_date"] = args.run_date
        df["run_id"] = args.run_id
        frames.append(df)

    if not frames:
        raise RuntimeError("No filings data found in raw inputs")

    combined = pd.concat(frames, ignore_index=True)
    if "accessionNumber" in combined.columns:
        combined = combined.drop_duplicates(subset=["accessionNumber"])

    curated_path = (
        f"s3://{args.curated_bucket}/{args.curated_prefix}/"
        f"run_date={args.run_date}/run_id={args.run_id}/"
    )
    wr.s3.to_parquet(
        df=combined,
        path=curated_path,
        dataset=True,
        mode="overwrite",
    )


if __name__ == "__main__":
    main()
