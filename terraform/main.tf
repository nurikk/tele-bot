# https://github.com/Rose-stack/docker-aws-ecs-using-terraform/blob/main/main.tf
resource "aws_ecr_repository" "app_ecr_repo" {
  name = "tele-bot-repo"
}

resource "aws_ecs_cluster" "cluster" {
  name = "tele-bot-cluster"
}

resource "aws_default_subnet" "default_subnet_a" {
  # Use your own region here but reference to subnet 1a
  availability_zone = "eu-west-1a"
}

resource "aws_ecs_task_definition" "task" {
  family                   = "tele-bot-task"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "telebot",
      "image": "${aws_ecr_repository.app_ecr_repo.repository_url}",
      "essential": true,    
      "memory": 512,
      "cpu": 256
    }
  ]
  DEFINITION
  requires_compatibilities = ["FARGATE"] # use Fargate as the lauch type
  network_mode             = "awsvpc"    # add the awsvpc network mode as this is required for Fargate
  memory                   = 512         # Specify the memory the container requires
  cpu                      = 256         # Specify the CPU the container requires
  execution_role_arn       = aws_iam_role.ecsTaskExecutionRole.arn
}

resource "aws_iam_role" "ecsTaskExecutionRole" {
  name               = "ecsTaskExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_policy" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}


# Provide a reference to your default VPC
resource "aws_default_vpc" "default_vpc" {
}

resource "aws_security_group" "service_security_group" {
  egress = [{
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }]
}

resource "aws_ecs_service" "app_service" {
  name            = "tele-bot-service"               # Name the  service
  cluster         = aws_ecs_cluster.cluster.id       # Reference the created Cluster
  task_definition = aws_ecs_task_definition.task.arn # Reference the task that the service will spin up
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets          = [aws_default_subnet.default_subnet_a.id]
    assign_public_ip = true
    security_groups  = [aws_security_group.service_security_group.id] # Set up the security group
  }
}
