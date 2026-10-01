data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"]
}

resource "aws_instance" "pipeline" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"

  subnet_id = data.aws_subnets.default.ids[0]

  vpc_security_group_ids = [
    aws_security_group.pipeline.id
  ]

  iam_instance_profile = aws_iam_instance_profile.pipeline.name

  user_data = file("${path.module}/scripts/setup.sh")

  user_data_replace_on_change = true

  tags = {
    Name    = "football-data-pipeline-dev"
    Project = "football-data-engineering"
    Env     = "dev"
  }
}