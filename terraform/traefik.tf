resource "random_password" "traefik_dashboard_password" {
  length  = 32
  special = false
}


locals {

  traefik_image      = "traefik:v2.11"

  traefik_dashboard_username = "admin"
  duck_dns_container_name    = "duckdns"

}


resource "aws_security_group" "traefik_group" {
  name   = "traefik-security-group"
  vpc_id = aws_vpc.default.id


  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "http"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "https"
  }
}


resource "aws_ecs_task_definition" "traefik" {
  family             = "traefik"
  execution_role_arn = aws_iam_role.ecsTaskExecutionRole.arn
  task_role_arn      = aws_iam_role.ecs_task_iam_role.arn
  memory             = 100

  volume {
    name      = "letsencrypt"
    host_path = "/letsencrypt"
  }

  container_definitions = jsonencode([
    {
      name : local.duck_dns_container_name,
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
    },
    {
      dependsOn : [
        {
          "containerName" : local.duck_dns_container_name,
          "condition" : "START"
        }
      ],
      name : "traefik",
      image : local.traefik_image,
      logConfiguration : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-group" : aws_cloudwatch_log_group.logs.name,
          "awslogs-region" : data.aws_region.current.name,
          "awslogs-stream-prefix" : "traefik"
        }
      },
      portMappings : [
        {
          "containerPort" : 80,
          "hostPort" : 80,
          "protocol" : "tcp"
        },
        {
          "containerPort" : 443,
          "hostPort" : 443,
          "protocol" : "tcp"
        },
        {
          "containerPort" : 8080,
          "hostPort" : 8080,
          "protocol" : "tcp"
        }
      ],
      essential : true,
      command : [
#        "--log.level=DEBUG",

        "--api.insecure", # Don't do that in production#
        "--api.dashboard=true",
        "--providers.ecs.autoDiscoverClusters=true",
        "--providers.ecs.exposedByDefault=false",

        "--entrypoints.web.address=:80",
        "--entryPoints.websecure.address=:443",


        "--entrypoints.web.http.redirections.entryPoint.to=websecure",
        "--entrypoints.web.http.redirections.entryPoint.scheme=https",
        "--entrypoints.web.http.redirections.entrypoint.permanent=true",

        "--entrypoints.websecure.http.tls.certresolver=lets-encr",
        "--entrypoints.websecure.http.tls.domains[0].main=${var.DUCK_DNS_DOMAIN}.duckdns.org",
        "--entrypoints.websecure.http.tls.domains[0].sans=*.${var.DUCK_DNS_DOMAIN}.duckdns.org",

        "--certificatesresolvers.lets-encr.acme.email=${var.LETSENCRYPT_EMAIL}",
        "--certificatesresolvers.lets-encr.acme.storage=/letsencrypt/acme.json",

        "--certificatesresolvers.lets-encr.acme.dnschallenge=true",
        "--certificatesresolvers.lets-encr.acme.dnschallenge.provider=duckdns",
        "--certificatesresolvers.lets-encr.acme.dnschallenge.resolvers=1.1.1.1:53,8.8.8.8:53",
#        "--certificatesresolvers.lets-encr.acme.caServer=https://acme-staging-v02.api.letsencrypt.org/directory"
      ],
      environment : [
        {
          "name" : "DUCKDNS_TOKEN",
          "value" : var.DUCK_DNS_TOKEN
        }
      ],
      mountPoints : [
        {
          "sourceVolume" : "letsencrypt",
          "containerPath" : "/letsencrypt",
          "readOnly" : false
        }
      ],
      dockerLabels : {
      }
    }
  ])
}

resource "aws_ecs_service" "traefik" {
  enable_execute_command             = true
  name                               = "traefik"
  cluster                            = aws_ecs_cluster.cluster.name
  launch_type                        = "EC2"
  task_definition                    = aws_ecs_task_definition.traefik.arn
  desired_count                      = 1
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100
}
