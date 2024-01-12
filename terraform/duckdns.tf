locals {
  duckdns_container_definitions = [
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
  }]
}