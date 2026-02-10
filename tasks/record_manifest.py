import json
import os
from datetime import datetime, timezone
from typing import List, Union

import boto3


def record_manifest(
    raw_uris: Union[List[str], str],
    curated_bucket: str,
    curated_prefix: str,
    run_date: str,
    run_id: str,
    region: str,
) -> str:
    if isinstance(raw_uris, str):
        try:
            raw_uris = json.loads(raw_uris)
        except json.JSONDecodeError:
            raw_uris = [raw_uris]
    session = boto3.session.Session(region_name=region or os.getenv("AWS_REGION"))
    s3 = session.client("s3")

    manifest = {
        "run_date": run_date,
        "run_id": run_id,
        "raw_uris": raw_uris,
        "curated_prefix": f"s3://{curated_bucket}/{curated_prefix}",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    key = f"{curated_prefix}/manifests/run_date={run_date}/run_id={run_id}/manifest.json"
    s3.put_object(
        Bucket=curated_bucket,
        Key=key,
        Body=json.dumps(manifest, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    return f"s3://{curated_bucket}/{key}"
