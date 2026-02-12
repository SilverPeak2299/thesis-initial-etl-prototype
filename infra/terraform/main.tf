locals {
  raw_bucket_name     = var.raw_bucket_name
  curated_bucket_name = var.curated_bucket_name
  glue_bucket_name    = var.glue_scripts_bucket_name

  glue_script_s3_path = coalesce(
    var.glue_script_s3_path,
    "s3://${local.glue_bucket_name}/glue/transform_raw_to_curated.py"
  )
}

data "aws_s3_bucket" "raw" {
  bucket = local.raw_bucket_name
}

data "aws_s3_bucket" "curated" {
  bucket = local.curated_bucket_name
}

data "aws_s3_bucket" "glue_scripts" {
  bucket = local.glue_bucket_name
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

data "aws_iam_role" "glue_role" {
  name = "${var.project_name}-glue-role"
}

data "aws_iam_policy_document" "glue_policy" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]
    resources = [
      data.aws_s3_bucket.raw.arn,
      "${data.aws_s3_bucket.raw.arn}/*",
      data.aws_s3_bucket.curated.arn,
      "${data.aws_s3_bucket.curated.arn}/*",
      data.aws_s3_bucket.glue_scripts.arn,
      "${data.aws_s3_bucket.glue_scripts.arn}/*",
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
  role   = data.aws_iam_role.glue_role.id
  policy = data.aws_iam_policy_document.glue_policy.json
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

data "aws_security_group" "airflow_sg" {
  name   = "${var.project_name}-airflow-sg"
  vpc_id = data.aws_vpc.default.id
}

resource "aws_instance" "airflow" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.airflow_instance_type
  key_name                    = var.airflow_key_name
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [data.aws_security_group.airflow_sg.id]
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
