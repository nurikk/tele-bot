resource "random_string" "redash_cookie_secret" {
  length  = 32
  special = false
}
resource "random_string" "redash_secret_key" {
  length  = 32
  special = false
}

locals {
  redash_env = [
    {
      "name" : "REDASH_DATABASE_URL",
      "value" : "postgres://${aws_db_instance.db.username}:${random_password.db_password.result}@${aws_db_instance.db.address}:${aws_db_instance.db.port}/redash"
    },
    {
      "name" : "REDASH_REDIS_URL",
      "value" : "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}/1"
    },
    {
      "name" : "REDASH_COOKIE_SECRET",
      "value" : random_string.redash_cookie_secret.result
    },
    {
      "name" : "REDASH_SECRET_KEY",
      "value" : random_string.redash_secret_key.result
    },
    {
      "name" : "REDASH_GOOGLE_CLIENT_ID",
      "value" : var.REDASH_GOOGLE_CLIENT_ID
    },
    {
      "name" : "REDASH_GOOGLE_CLIENT_SECRET",
      "value" : var.REDASH_GOOGLE_CLIENT_SECRET
    },
    {
      name : "PYTHONUNBUFFERED",
      value : "0"
    },
    {
      name : "REDASH_LOG_LEVEL",
      value : "DEBUG"
    }
  ]

  redash_logs = {
    "logDriver" : "awslogs",
    "options" : {
      "awslogs-group" : aws_cloudwatch_log_group.logs.name,
      "awslogs-region" : data.aws_region.current.name,
      "awslogs-stream-prefix" : "redash"
    }
  }


  redash_container_definitions = [
    {
      name : "redash-server",
      essential : false,
      image : "redash/redash:latest",
      logConfiguration : local.redash_logs,
      command : [
        "server"
      ],
      environment : concat([
        {
          name : "REDASH_WEB_WORKERS",
          value : "1"
        }
      ], local.redash_env),
      portMappings = [
        {
          containerPort = 5000
          hostPort      = 5000
        }
      ]
    },
    {
      name : "redash-scheduler",
      essential : false,
      image : "redash/redash:latest",
      logConfiguration : local.redash_logs,
      command : [
        "scheduler"
      ],
      environment : concat([
        {
          name : "QUEUES",
          value : "celery"
        },
        {
          name : "WORKERS_COUNT",
          value : "1"
        }
      ], local.redash_env)
    },

    {
      name : "redash-adhoc_worker",
      essential : false,
      image : "redash/redash:latest",
      logConfiguration : local.redash_logs,
      command : [
        "worker"
      ],
      environment : concat([
        {
          name : "QUEUES",
          value : "queries"
        },
        {
          name : "WORKERS_COUNT",
          value : "2"
        }
      ], local.redash_env)
    },

    {
      name : "redash-create_db",
      essential : false,
      image : "redash/redash:latest",
      logConfiguration : local.redash_logs,
      command : [
        "create_db"
      ],
      environment : concat([

      ], local.redash_env)
    }
  ]
}