# https://github.com/Rose-stack/docker-aws-ecs-using-terraform/blob/main/main.tf
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}



resource "aws_cloudwatch_log_group" "logs" {
  name = "/ecs/tele-bot-task"
}


locals {
  env = [
    {
      "name" : "OPENAI_API_KEY",
      "value" : var.OPENAI_API_KEY
    },
    {
      "name" : "TELEGRAM_BOT_TOKEN",
      "value" : var.TELEGRAM_BOT_TOKEN
    },
    {
      "name" : "DB_URL",
      "value" : "postgresql+asyncpg://${aws_db_instance.db.username}:${random_password.db_password.result}@${aws_db_instance.db.address}:${aws_db_instance.db.port}/${aws_db_instance.db.db_name}"
    }
  ]
}
resource "aws_ecs_task_definition" "task" {
  family = "tele-bot-task"
  container_definitions = jsonencode([
    {
      "name" : "telebot",
      "image" : aws_ecr_repository.app_ecr_repo.repository_url,
      "essential" : true,
      "memory" : 512,
      "cpu" : 256,
      "logConfiguration" : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-group" : aws_cloudwatch_log_group.logs.name,
          "awslogs-region" : data.aws_region.current.name,
          "awslogs-stream-prefix" : "ecs"
        }
      },
      "environment" : local.env
    }
  ])

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = 512
  cpu                      = 256
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




resource "aws_ecs_service" "app_service" {
  name                               = "tele-bot-service"
  cluster                            = aws_ecs_cluster.cluster.id
  task_definition                    = aws_ecs_task_definition.task.arn
  launch_type                        = "FARGATE"
  desired_count                      = 1
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100


  network_configuration {
    subnets = concat(aws_subnet.private[*].id, aws_subnet.public[*].id)
    assign_public_ip = true
    security_groups = [
      aws_security_group.this.id
    ]
  }
}
