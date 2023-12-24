variable "name" {
  description = "The name of the project, e.g. my-project"
  type        = string
  default     = "tele-bot"
}

variable "environment" {
  description = "The environment, e.g. prod"
  type        = string
  default = "prod"
}




locals {
  num_availability_zones = 3
}

locals {
  availability_zones = slice(data.aws_availability_zones.available.names, 0, local.num_availability_zones)
  public_cidrs       = [for n in range(1, local.num_availability_zones + 1) : "10.0.${n}.0/24"]
  private_cidrs      = [for n in range(local.num_availability_zones + 1, local.num_availability_zones * 2 + 1) : "10.0.${n}.0/24"]
}

resource "aws_vpc" "this" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.name}-${var.environment}"
  }
}

resource "aws_subnet" "private" {
  count             = local.num_availability_zones
  availability_zone = element(local.availability_zones, count.index)
  cidr_block        = element(local.private_cidrs, count.index)
  vpc_id            = aws_vpc.this.id

  tags = {
    Name = "${var.name}-${var.environment}-private-${count.index + 1}"
  }
}

resource "aws_default_route_table" "this" {
  default_route_table_id = aws_vpc.this.default_route_table_id
}

resource "aws_subnet" "public" {
  count             = local.num_availability_zones
  availability_zone = element(local.availability_zones, count.index)
  cidr_block        = element(local.public_cidrs, count.index)
  vpc_id            = aws_vpc.this.id

  tags = {
    Name = "${var.name}-${var.environment}-public-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name}-${var.environment}"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name = "${var.name}-${var.environment}-public-igw"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(local.public_cidrs)
  subnet_id      = element(aws_subnet.public[*].id, count.index)
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "this" {
  name        = "${var.name}-${var.environment}"
  description = "Allow inbound on self & outbound on all"
  vpc_id      = aws_vpc.this.id

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  private_dns_enabled = true
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  vpc_id              = aws_vpc.this.id

  security_group_ids = [
    aws_security_group.this.id
  ]

  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.name}-${var.environment}-privatelink-ecr-dkr"
  }
}

resource "aws_vpc_endpoint" "ecr_api" {
  private_dns_enabled = true
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.api"
  vpc_endpoint_type   = "Interface"
  vpc_id              = aws_vpc.this.id

  security_group_ids = [
    aws_security_group.this.id
  ]

  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.name}-${var.environment}-privatelink-ecr-api"
  }
}

resource "aws_vpc_endpoint" "cloudwatch" {
  private_dns_enabled = true
  service_name        = "com.amazonaws.${data.aws_region.current.name}.logs"
  vpc_endpoint_type   = "Interface"
  vpc_id              = aws_vpc.this.id

  security_group_ids = [
    aws_security_group.this.id
  ]

  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.name}-${var.environment}-privatelink-cloudwatch"
  }
}

resource "aws_vpc_endpoint" "s3_gateway" {
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  vpc_id            = aws_vpc.this.id

  route_table_ids = [aws_default_route_table.this.id]

  tags = {
    Name = "${var.name}-${var.environment}-privatelink-s3-gateway"
  }
}
