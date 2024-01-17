locals {
  metabase_env = {
    MB_DB_TYPE   = "postgres"
    MB_DB_DBNAME = "metabase"
    MB_DB_PORT   = aws_db_instance.db.port
    MB_DB_USER   = aws_db_instance.db.username
    MB_DB_PASS   = random_password.db_password.result
    MB_DB_HOST   = aws_db_instance.db.address
  }
  metabase_container_definitions = [
    {
      name : "metabase",
      essential : false,
      image : "metabase/metabase",
      logConfiguration : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-group" : aws_cloudwatch_log_group.logs.name,
          "awslogs-region" : data.aws_region.current.name,
          "awslogs-stream-prefix" : "metabase"
        }
      },
      environment : [
        for k, v in local.metabase_env : {
          name : k
          value : tostring(v)
        }
      ],
      portMappings = [
        {
          containerPort = 3000
        }
      ]
    }
  ]
}