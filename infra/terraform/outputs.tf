output "s3_bucket_name" {
  description = "Nome do bucket S3 criado"
  value       = aws_s3_bucket.football_data.bucket
}

output "s3_bucket_arn" {
  description = "ARN do bucket S3"
  value       = aws_s3_bucket.football_data.arn
}

output "aws_region" {
  description = "Região AWS utilizada"
  value       = var.aws_region
}

output "ubuntu_ami_id" {
  description = "AMI Ubuntu utilizada pela EC2"
  value       = data.aws_ami.ubuntu.id
}
