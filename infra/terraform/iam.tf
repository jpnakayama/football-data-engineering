# IAM Role assumida pela EC2
resource "aws_iam_role" "pipeline_ec2" {
  name = "football-data-pipeline-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "ec2.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project = "football-data-engineering"
    Env     = "dev"
  }
}


# Permissões necessárias para a instância funcionar com Systems Manager
resource "aws_iam_role_policy_attachment" "ssm" {
  role = aws_iam_role.pipeline_ec2.name

  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}


# Instance Profile usado para entregar a IAM Role à EC2
resource "aws_iam_instance_profile" "pipeline" {
  name = "football-data-pipeline-ec2-profile"
  role = aws_iam_role.pipeline_ec2.name
}

# Policy de acesso da EC2 aos dados do projeto no S3
data "aws_iam_policy_document" "pipeline_s3" {

  # Permite listar os objetos do bucket
  statement {
    sid    = "ListBucket"
    effect = "Allow"

    actions = [
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.football_data.arn
    ]
  }

  # Permite ler os dados de entrada
  statement {
    sid    = "ReadRawData"
    effect = "Allow"

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.football_data.arn}/raw/*"
    ]
  }

  # Permite gravar os dados processados
  statement {
    sid    = "WriteProcessedData"
    effect = "Allow"

    actions = [
      "s3:PutObject"
    ]

    resources = [
      "${aws_s3_bucket.football_data.arn}/processed/*"
    ]
  }
}

resource "aws_iam_policy" "pipeline_s3" {
  name        = "football-data-pipeline-s3-policy"
  description = "Allows the EC2 pipeline to read raw data and write processed data in S3"

  policy = data.aws_iam_policy_document.pipeline_s3.json
}

resource "aws_iam_role_policy_attachment" "pipeline_s3" {
  role       = aws_iam_role.pipeline_ec2.name
  policy_arn = aws_iam_policy.pipeline_s3.arn
}
