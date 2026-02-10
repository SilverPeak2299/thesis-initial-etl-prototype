variable "aws_region" {
  type        = string
  description = "AWS region for all resources."
  default     = "ap-southeast-2"
}

variable "project_name" {
  type        = string
  description = "Project name prefix for resource naming."
  default     = "thesis-edgar-etl"
}

variable "raw_bucket_name" {
  type        = string
  description = "S3 bucket name for raw data."
  default     = null
}

variable "curated_bucket_name" {
  type        = string
  description = "S3 bucket name for curated data."
  default     = null
}

variable "glue_scripts_bucket_name" {
  type        = string
  description = "S3 bucket name for Glue job scripts."
  default     = null
}

variable "glue_job_name" {
  type        = string
  description = "Glue job name for Python Shell transform."
  default     = "edgar-python-shell-transform"
}

variable "glue_script_s3_path" {
  type        = string
  description = "S3 path to the Glue Python Shell script (s3://bucket/key)."
  default     = null
}

variable "glue_max_capacity" {
  type        = number
  description = "Max DPU for Glue Python Shell (0.0625, 0.125, 1, 2, etc)."
  default     = 1
}

variable "airflow_instance_type" {
  type        = string
  description = "EC2 instance type for Airflow host."
  default     = "t3.medium"
}

variable "airflow_key_name" {
  type        = string
  description = "EC2 key pair name for SSH access."
}

variable "airflow_ssh_cidr" {
  type        = string
  description = "CIDR allowed to SSH to the Airflow instance."
  default     = "0.0.0.0/0"
}

variable "airflow_web_cidr" {
  type        = string
  description = "CIDR allowed to access the Airflow web UI."
  default     = "0.0.0.0/0"
}

variable "airflow_instance_name" {
  type        = string
  description = "Name tag for the Airflow EC2 instance."
  default     = "airflow-ec2"
}
