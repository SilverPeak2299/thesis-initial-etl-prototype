# thesis-initial-etl-prototype

Baseline EDGAR ETL with Airflow orchestration, raw data in S3, and a Glue Python Shell job to produce curated Parquet.

## Local Airflow
```bash
docker-compose up airflow-init
docker-compose up
```

Check container health:
```bash
docker ps
```

## Required Environment
Set these in `.env` (see `.env.example`) or your shell for Airflow tasks:
- `AWS_REGION`
- `S3_RAW_BUCKET`
- `S3_RAW_PREFIX` (default `raw/edgar`)
- `S3_CURATED_BUCKET`
- `S3_CURATED_PREFIX` (default `curated/edgar`)
- `GLUE_JOB_NAME`
- `EDGAR_USER_AGENT` (required by EDGAR API)

## EC2 (Airflow host)
Terraform requires:
- `airflow_key_name` (EC2 key pair name)
- `airflow_ssh_cidr` (who can SSH)
- `airflow_web_cidr` (who can access Airflow UI on port 8080)

GitHub Actions optional deploy requires secrets:
- `EC2_HOST`
- `EC2_SSH_PRIVATE_KEY`
- `REPO_SSH_URL` (SSH URL of this repo)

## Glue Job Script
The Glue Python Shell script lives at:
- `glue_jobs/transform_raw_to_curated.py`

Upload it to S3 and point the Glue job to that `s3://...` path.

## Terraform (infra)
Infrastructure lives in `infra/terraform` and provisions:
- S3 raw + curated buckets
- Glue Python Shell job
- IAM role/policy for Glue
- EC2 host for Airflow (Docker + docker-compose)

## CI/CD
GitHub Actions workflow at `.github/workflows/ci_cd.yml`:
- Uploads Glue script to S3
- Runs Terraform plan (optional apply if `TF_APPLY=true` in repo variables)
- Optional SSH deploy to EC2 (requires repo/SSH secrets)
