resource "aws_default_vpc" "default" {
  tags = {
    Name = "Default VPC"
  }
}

data "aws_security_group" "default" {
  vpc_id = aws_default_vpc.default.id

  filter {
    name   = "group-name"
    values = ["default"]
  }
}





