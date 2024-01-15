resource "random_string" "superset_secret_key" {
  length  = 32
  special = false
}

locals {
  superset_container_name = "superset"
  superset_env            = {
    "SECRET_KEY" : random_string.superset_secret_key.result,
    "SQLALCHEMY_DATABASE_URI" : "postgresql://${aws_db_instance.db.username}:${random_password.db_password.result}@${aws_db_instance.db.address}:${aws_db_instance.db.port}/superset",
    "SUPERSET_CONFIG_PATH" : "/app/superset_home/superset_config.py",
    "WTF_CSRF_ENABLED": "false",
    "ENABLE_PROXY_FIX": "true"
  }
  superset_container_definitions = [
    {
      name : local.superset_container_name,
      essential : false,
      image : "apache/superset",
      logConfiguration : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-group" : aws_cloudwatch_log_group.logs.name,
          "awslogs-region" : data.aws_region.current.name,
          "awslogs-stream-prefix" : "superset"
        }
      },
      environment : [
        for k, v in local.superset_env : {
          name : k
          value : tostring(v)
        }
      ],
      portMappings = [
        {
          containerPort = 8088
          hostPort      = 8088
        }
      ],
      "mountPoints" : [
        {
          "containerPath" : "/app/superset_home",
          "sourceVolume" : "efs"
        }
      ]
    },
  ]
}

