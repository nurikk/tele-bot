# https://github.com/Rose-stack/docker-aws-ecs-using-terraform/blob/main/main.tf
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_cloudwatch_log_group" "logs" {
  name = "/ecs/tele-bot-task"
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
    effect = "Allow"
    actions = [
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel"
    ]
    resources = ["*"]
  }
}


data "aws_iam_policy_document" "TraefikECSReadAccess" {
  statement {
    effect = "Allow"
    actions = [
      "ecs:ListClusters",
      "ecs:DescribeClusters",
      "ecs:ListTasks",
      "ecs:DescribeTasks",
      "ecs:DescribeContainerInstances",
      "ecs:DescribeTaskDefinition",
      "ec2:DescribeInstances",
      "ssm:DescribeInstanceInformation"
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

resource "aws_iam_policy" "TraefikECSReadAccess" {
  name        = "TraefikECSReadAccess-policy"
  description = "A test policy"
  policy      = data.aws_iam_policy_document.TraefikECSReadAccess.json
}


resource "aws_ecs_task_definition" "task" {
  family = "tele-bot-task"

  container_definitions = jsonencode(local.telebot_container_definitions)

  requires_compatibilities = ["EC2"]
  network_mode             = "bridge"
  memory                   = 200
  execution_role_arn       = aws_iam_role.ecsTaskExecutionRole.arn
  task_role_arn            = aws_iam_role.ecs_task_iam_role.arn
}

resource "aws_iam_role" "ecsTaskExecutionRole" {
  name               = "ecsTaskExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "TraefikECSReadAccess-attach" {
  role       = aws_iam_role.ecs_task_iam_role.name
  policy_arn = aws_iam_policy.TraefikECSReadAccess.arn
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


