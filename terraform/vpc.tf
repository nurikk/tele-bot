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



data "aws_internet_gateway" "default" {
  filter {
    name   = "attachment.vpc-id"
    values = [aws_default_vpc.default.id]
  }
}

resource "aws_route_table" "route_table" {
 vpc_id = aws_default_vpc.default.id
 route {
   cidr_block = "0.0.0.0/0"
   gateway_id = data.aws_internet_gateway.default.id
 }
}


resource "aws_route_table_association" "subnet_a_route" {
 subnet_id      = aws_default_subnet.default_subnet_a.id
 route_table_id = aws_route_table.route_table.id
}

resource "aws_route_table_association" "subnet_b_route" {
 subnet_id      = aws_default_subnet.default_subnet_b.id
 route_table_id = aws_route_table.route_table.id
}
