# https://github.com/Rose-stack/docker-aws-ecs-using-terraform/blob/main/main.tf
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_cloudwatch_log_group" "logs" {
  name = "/ecs/tele-bot-task"
}

locals {
  task_memory = 1024
  task_cpu    = 256
  telebot_container_name = "telebot"
}

resource "aws_ecs_task_definition" "task" {
  family                = "tele-bot-task"
  container_definitions = jsonencode(concat([
    {
      name : local.telebot_container_name,
      image : aws_ecr_repository.app_ecr_repo.repository_url,
      essential : true,
      logConfiguration : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-group" : aws_cloudwatch_log_group.logs.name,
          "awslogs-region" : data.aws_region.current.name,
          "awslogs-stream-prefix" : "telebot"
        }
      },
      command : ["./bot.sh"],
      environment : [
        {
          "name" : "OPENAI_API_KEY",
          "value" : var.OPENAI_API_KEY
        },
        {
          "name" : "REPLICATE_API_TOKEN",
          "value" : var.REPLICATE_API_TOKEN
        },
        {
          "name" : "TELEGRAM_BOT_TOKEN",
          "value" : var.TELEGRAM_BOT_TOKEN
        },
        {
          "name" : "DB_URL",
          "value" : "postgres://${aws_db_instance.db.username}:${random_password.db_password.result}@${aws_db_instance.db.address}:${aws_db_instance.db.port}/${aws_db_instance.db.db_name}"
        },
        {
          "name" : "REDIS_URL",
          "value" : "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}/0"
        },

        {
          "name" : "S3_BUCKET_NAME",
          "value" : aws_s3_bucket.telebot_bucket.id
        },

        {
          "name" : "AWS_REGION",
          "value" : data.aws_region.current.name
        },
        {
          "name" : "AWS_ACCESS_KEY_ID",
          "value" : aws_iam_access_key.telebot_s3_uploader.id
        },
        {
          "name" : "AWS_SECRET_ACCESS_KEY",
          "value" : aws_iam_access_key.telebot_s3_uploader.secret
        },
        {
          "name" : "IMAGEOPTIM_ACCOUNT_ID",
          "value" : var.IMAGEOPTIM_ACCOUNT_ID
        },
        {
          "name" : "IMGPROXY_HOSTNAME",
          "value" : "${var.DUCK_DNS_DOMAIN}.duckdns.org"
        }
      ]
    },
    {
      name : "duckdns",
      image : "lscr.io/linuxserver/duckdns:latest",
      essential : false,
      logConfiguration : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-group" : aws_cloudwatch_log_group.logs.name,
          "awslogs-region" : data.aws_region.current.name,
          "awslogs-stream-prefix" : "duckdns"
        }
      },
      environment : [
        {
          "name" : "TOKEN",
          "value" : var.DUCK_DNS_TOKEN
        },
        {
          "name" : "SUBDOMAINS",
          "value" : var.DUCK_DNS_DOMAIN
        }
      ]
    },
  ],
#    local.redash_container_definitions,
    local.metabase_container_definitions
  ))

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = local.task_memory
  cpu                      = local.task_cpu
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

resource "aws_default_subnet" "default_subnet_a" {
  availability_zone = data.aws_availability_zones.available.names[0]
}

resource "aws_default_subnet" "default_subnet_b" {
  availability_zone = data.aws_availability_zones.available.names[1]
}


resource "aws_ecs_service" "app_service" {
  name            = "tele-bot-service"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.task.arn
  launch_type     = "FARGATE"
  desired_count   = 1
  network_configuration {
    subnets = [
      aws_default_subnet.default_subnet_a.id,
      aws_default_subnet.default_subnet_b.id
    ]
    assign_public_ip = true
    security_groups  = [
      data.aws_security_group.default.id,
      aws_security_group.image_proxy_sg.id
    ]
  }
}
