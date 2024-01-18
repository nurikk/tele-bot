resource "random_string" "imgproxy_secret_key" {
  length  = 32
  special = false
}

locals {
  imgproxy_container_name = "imgproxy"
  imgproxy_container_port = 8080
  imgproxy_env            = {
    "IMGPROXY_KEY" : var.IMGPROXY_KEY,
    "IMGPROXY_SALT" : var.IMGPROXY_SALT,
    "IMGPROXY_USE_S3" : true,
    "AWS_REGION" : data.aws_region.current.name,
    "AWS_ACCESS_KEY_ID" : aws_iam_access_key.telebot_s3_uploader.id
    "AWS_SECRET_ACCESS_KEY" : aws_iam_access_key.telebot_s3_uploader.secret
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
        for k, v in local.imgproxy_env : {
          name : k
          value : tostring(v)
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

