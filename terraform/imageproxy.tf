resource "random_string" "imgproxy_secret_key" {
  length  = 32
  special = false
}

locals {
  imgproxy_container_name = "imgproxy"
  imgproxy_container_port = 8080
  imgproxy_env            = {
  }
  imgproxy_container_definitions = [
    {
      name : local.imgproxy_container_name,
      image : "darthsim/imgproxy:latest",
      essential : false,
      logConfiguration : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-group" : aws_cloudwatch_log_group.logs.name,
          "awslogs-region" : data.aws_region.current.name,
          "awslogs-stream-prefix" : "imgproxy"
        }
      },
      environment : [
        {
          "name" : "IMGPROXY_KEY",
          "value" : var.IMGPROXY_KEY
        },
        {
          "name" : "IMGPROXY_SALT",
          "value" : var.IMGPROXY_SALT
        },
        {
          "name" : "IMGPROXY_USE_S3",
          "value" : "true"
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
        }
      ],
      portMappings = [
        {
          containerPort = local.imgproxy_container_port
        }
      ]
    }
  ]
}

