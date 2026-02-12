output "raw_bucket_name" {
  value = data.aws_s3_bucket.raw.bucket
}

output "curated_bucket_name" {
  value = data.aws_s3_bucket.curated.bucket
}

output "glue_job_name" {
  value = var.glue_job_name
}

output "glue_role_arn" {
  value = data.aws_iam_role.glue_role.arn
}

output "glue_scripts_bucket_name" {
  value = data.aws_s3_bucket.glue_scripts.bucket
}

output "glue_script_s3_path" {
  value = local.glue_script_s3_path
}

output "airflow_public_ip" {
  value = aws_instance.airflow.public_ip
}

output "airflow_public_dns" {
  value = aws_instance.airflow.public_dns
}
