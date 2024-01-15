# https://github.com/Rose-stack/docker-aws-ecs-using-terraform/blob/main/main.tf
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_cloudwatch_log_group" "logs" {
  name = "/ecs/tele-bot-task"
}

locals {
  task_memory = 944
}


data "aws_iam_policy_document" "task_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}


data "aws_iam_policy_document" "ssmmessages" {
  statement {
    effect  = "Allow"
    actions = [
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel"
    ]
    resources = ["*"]
  }
}


resource "aws_iam_policy" "ssmmessages" {
  name        = "test-policy"
  description = "A test policy"
  policy      = data.aws_iam_policy_document.ssmmessages.json
}


resource "aws_iam_role" "ecs_task_iam_role" {
  name               = "ECS_TaskIAMRole"
  assume_role_policy = data.aws_iam_policy_document.task_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "ssmmessages-attach" {
  role       = aws_iam_role.ecs_task_iam_role.name
  policy_arn = aws_iam_policy.ssmmessages.arn
}

resource "aws_ecs_task_definition" "task" {
  family                = "tele-bot-task"
  container_definitions = jsonencode(concat(
    local.telebot_container_definitions,
    local.duckdns_container_definitions,
    local.superset_container_definitions
    #    local.redash_container_definitions,
    #    local.metabase_container_definitions
  ))

  requires_compatibilities = ["EC2"]
  network_mode             = "awsvpc"
  memory                   = local.task_memory
  execution_role_arn       = aws_iam_role.ecsTaskExecutionRole.arn
  task_role_arn            = aws_iam_role.ecs_task_iam_role.arn

  volume {
    name      = "efs"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.telebot.id
      root_directory = "/"
    }
  }
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
  launch_type                        = "EC2"
  desired_count                      = 1
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100

  enable_execute_command = true
  network_configuration {
    subnets         = aws_subnet.private.*.id
    security_groups = [
      aws_security_group.security_group.id,
      #      aws_security_group.image_proxy_sg.id
    ]
  }

  depends_on = [aws_lb_listener.hello_world]


  load_balancer {
    target_group_arn = aws_lb_target_group.hello_world.id
    container_name   = local.superset_container_name
    container_port   = 8088
  }
}