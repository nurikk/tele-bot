resource "random_password" "pgweb_password" {
  length  = 16
  special = false
}

locals {
  pgweb_container_name = "pgweb"
  pgweb_container_port = 8081
  pgweb_hostname = "pgweb.${var.DUCK_DNS_DOMAIN}.duckdns.org"
  pgweb_env            = {
    "PGWEB_AUTH_USER" : "admin",
    "PGWEB_AUTH_PASS": random_password.pgweb_password.result,
    "DATABASE_URL" : "postgres://${aws_db_instance.db.username}:${random_password.db_password.result}@${aws_db_instance.db.address}:${aws_db_instance.db.port}/${aws_db_instance.db.db_name}",

  }
  pgweb_container_definitions = [
    {
      name : local.pgweb_container_name,
      image : "sosedoff/pgweb",
      essential : true,
      logConfiguration : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-group" : aws_cloudwatch_log_group.logs.name,
          "awslogs-region" : data.aws_region.current.name,
          "awslogs-stream-prefix" : "pgweb"
        }
      },
      environment : [
        for k, v in local.pgweb_env : {
          name : k
          value : tostring(v)
        }
      ],
      portMappings = [
        {
          containerPort = local.pgweb_container_port
        }
      ],
      dockerLabels : {
        "traefik.enable" : "true",
        "traefik.http.routers.pgweb.entrypoints": "websecure",
        "traefik.http.routers.pgweb.rule": "Host(`${local.pgweb_hostname}`)",
      }
    }
  ]
}


resource "aws_ecs_task_definition" "pgweb" {
  family             = "pgweb"
  execution_role_arn = aws_iam_role.ecsTaskExecutionRole.arn
  memory             = 100

  container_definitions = jsonencode(local.pgweb_container_definitions)
}

resource "aws_ecs_service" "pgweb" {
  name                               = "pgweb"
  cluster                            = aws_ecs_cluster.cluster.name
  launch_type                        = "EC2"
  task_definition                    = aws_ecs_task_definition.pgweb.arn
  desired_count                      = 1
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100
}
