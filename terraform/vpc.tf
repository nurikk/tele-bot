locals {
  subnet_count = 2
}
resource "aws_vpc" "default" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    name = "main"
  }
}



resource "aws_subnet" "public" {
  count                   = local.subnet_count
  cidr_block              = cidrsubnet(aws_vpc.default.cidr_block, 8, 2 + count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  vpc_id                  = aws_vpc.default.id
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count             = local.subnet_count
  cidr_block        = cidrsubnet(aws_vpc.default.cidr_block, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  vpc_id            = aws_vpc.default.id
}

data "aws_security_group" "default" {
  vpc_id = aws_vpc.default.id

  filter {
    name   = "group-name"
    values = ["default"]
  }
}


resource "aws_internet_gateway" "internet_gateway" {
  vpc_id = aws_vpc.default.id
}


resource "aws_route" "internet_access" {
  route_table_id         = aws_vpc.default.main_route_table_id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.internet_gateway.id
}



resource "aws_security_group" "security_group" {
  name   = "ecs-security-group"
  vpc_id = aws_vpc.default.id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    self        = "true"
    cidr_blocks = var.WHITELIST_IP
    description = "any"
    security_groups = [aws_security_group.lb.id]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["3.129.36.245/32", "3.18.79.139/32", "3.13.16.99/32"]
    description = "postgres hex.tech"
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["${google_looker_instance.looker-instance.egress_public_ip}/32"]
    description = "looker"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}




#==============
resource "aws_eip" "gateway" {
  count      = local.subnet_count
  domain     = "vpc"
  depends_on = [aws_internet_gateway.internet_gateway]
}

resource "aws_nat_gateway" "gateway" {
  count         = length(aws_subnet.public)
  subnet_id     = aws_subnet.public[count.index].id
  allocation_id = aws_eip.gateway[count.index].id
}

resource "aws_route_table" "private" {
  count  = length(aws_nat_gateway.gateway)
  vpc_id = aws_vpc.default.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.gateway[count.index].id
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}