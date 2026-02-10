data "aws_caller_identity" "current" {}

locals {
  account_id                 = data.aws_caller_identity.current.account_id
  default_raw_bucket_name    = "raw-bucket-${local.account_id}"
  default_curated_bucket_name = "curated-bucket-${local.account_id}"
  default_glue_bucket_name   = "glue-scripts-bucket-${local.account_id}"

  raw_bucket_name     = coalesce(var.raw_bucket_name, local.default_raw_bucket_name)
  curated_bucket_name = coalesce(var.curated_bucket_name, local.default_curated_bucket_name)
  glue_bucket_name    = coalesce(var.glue_scripts_bucket_name, local.default_glue_bucket_name)

  glue_script_s3_path = coalesce(
    var.glue_script_s3_path,
    "s3://${local.glue_bucket_name}/glue/transform_raw_to_curated.py"
  )
}

resource "aws_s3_bucket" "raw" {
  bucket = local.raw_bucket_name
}

resource "aws_s3_bucket" "curated" {
  bucket = local.curated_bucket_name
}

resource "aws_s3_bucket" "glue_scripts" {
  bucket = local.glue_bucket_name
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "curated" {
  bucket = aws_s3_bucket.curated.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "glue_scripts" {
  bucket = aws_s3_bucket.glue_scripts.id
  versioning_configuration {
    status = "Enabled"
  }
}

data "aws_iam_policy_document" "glue_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_role" {
  name               = "${var.project_name}-glue-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
}

data "aws_iam_policy_document" "glue_policy" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.raw.arn,
      "${aws_s3_bucket.raw.arn}/*",
      aws_s3_bucket.curated.arn,
      "${aws_s3_bucket.curated.arn}/*",
      aws_s3_bucket.glue_scripts.arn,
      "${aws_s3_bucket.glue_scripts.arn}/*",
    ]
  }

  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "glue_policy" {
  name   = "${var.project_name}-glue-policy"
  role   = aws_iam_role.glue_role.id
  policy = data.aws_iam_policy_document.glue_policy.json
}

resource "aws_glue_job" "transform" {
  name     = var.glue_job_name
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "pythonshell"
    python_version  = "3"
    script_location = local.glue_script_s3_path
  }

  max_capacity = var.glue_max_capacity
  timeout      = 60

  default_arguments = {
    "--job-language"               = "python"
    "--enable-continuous-cloudwatch-log" = "true"
    "--additional-python-modules"  = "awswrangler==3.6.0,pyarrow==14.0.2,pandas==2.2.2"
  }
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_security_group" "airflow_sg" {
  name        = "${var.project_name}-airflow-sg"
  description = "Airflow EC2 security group"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.airflow_ssh_cidr]
  }

  ingress {
    description = "Airflow Web UI"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.airflow_web_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "airflow" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.airflow_instance_type
  key_name                    = var.airflow_key_name
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.airflow_sg.id]
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash
              set -eux
              dnf update -y
              dnf install -y docker git
              systemctl enable --now docker
              usermod -aG docker ec2-user
              dnf install -y docker-compose-plugin
              mkdir -p /opt/airflow
              chown ec2-user:ec2-user /opt/airflow
              EOF

  tags = {
    Name = var.airflow_instance_name
  }
}
