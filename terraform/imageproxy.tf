locals {
  imgproxy_container_name = "imgproxy"
  imgproxy_container_port = 8081
  imgproxy_env            = {
    "IMGPROXY_KEY" : var.IMGPROXY_KEY,
    "IMGPROXY_SALT" : var.IMGPROXY_SALT,
    "IMGPROXY_USE_S3" : true,
    "AWS_REGION" : data.aws_region.current.name,
    "AWS_ACCESS_KEY_ID" : aws_iam_access_key.telebot_s3_uploader.id
    "AWS_SECRET_ACCESS_KEY" : aws_iam_access_key.telebot_s3_uploader.secret,
    "IMGPROXY_BIND" : ":${local.imgproxy_container_port}"
  }
  imgproxy_container_definitions = [
    {
      name : local.imgproxy_container_name,
      image : "darthsim/imgproxy:latest",
      essential : true,
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
      ],
      dockerLabels : {
        "traefik.enable" : "true",
        "traefik.http.routers.img.entrypoints": "websecure",
        "traefik.http.routers.img.rule": "Host(`img.${local.full_duck_dns_domain}`)"
      }
    }
  ]
}


resource "aws_ecs_task_definition" "imgproxy" {
  family             = "imgproxy"
  execution_role_arn = aws_iam_role.ecsTaskExecutionRole.arn
  memory             = 300



  container_definitions = jsonencode(local.imgproxy_container_definitions)
}

resource "aws_ecs_service" "imgproxy" {
  name                               = "imgproxy"
  cluster                            = aws_ecs_cluster.cluster.name
  launch_type                        = "EC2"
  task_definition                    = aws_ecs_task_definition.imgproxy.arn
  desired_count                      = 1
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100
}
