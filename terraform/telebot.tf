locals {
  telebot_container_name = "telebot"
  telebot_container_definitions = [
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
    }
  ]
}

resource "aws_ecs_service" "app_service" {
  name                               = "tele-bot-service"
  cluster                            = aws_ecs_cluster.cluster.id
  task_definition                    = aws_ecs_task_definition.task.arn
  launch_type                        = "EC2"
  desired_count                      = 1
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100
  enable_execute_command             = true
}