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
# resource "aws_security_group" "this" {
#   description = "Allow inbound on self & outbound on all"
#   vpc_id      = aws_default_vpc.default.id

#   ingress {
#     from_port = 0
#     to_port   = 0
#     protocol  = "-1"
#     self      = true
#   }

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
# }

