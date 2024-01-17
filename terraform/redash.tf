resource "random_string" "redash_cookie_secret" {
  length  = 32
  special = false
}
resource "random_string" "redash_secret_key" {
  length  = 32
  special = false
}

locals {
  redash_env = {
    "REDASH_DATABASE_URL" : "postgres://${aws_db_instance.db.username}:${random_password.db_password.result}@${aws_db_instance.db.address}:${aws_db_instance.db.port}/redash",
    "REDASH_REDIS_URL" : "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}/1",
    "REDASH_COOKIE_SECRET" : random_string.redash_cookie_secret.result,
    "REDASH_SECRET_KEY" : random_string.redash_secret_key.result,
    "REDASH_GOOGLE_CLIENT_ID" : var.REDASH_GOOGLE_CLIENT_ID,
    "REDASH_GOOGLE_CLIENT_SECRET" : var.REDASH_GOOGLE_CLIENT_SECRET,
    "PYTHONUNBUFFERED" : "0",
    "REDASH_LOG_LEVEL" : "DEBUG"
  }

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
      ], [
        for k, v in local.redash_env : {
          name : k
          value : tostring(v)
        }
      ]),
      portMappings = [
        {
          containerPort = 5000
#          hostPort      = 5000
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
      ], [
        for k, v in local.redash_env : {
          name : k
          value : tostring(v)
        }
      ])
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
      ], [
        for k, v in local.redash_env : {
          name : k
          value : tostring(v)
        }
      ])
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

      ], [
        for k, v in local.redash_env : {
          name : k
          value : tostring(v)
        }
      ])
    }
  ]
}