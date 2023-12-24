resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "telebot-redis"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.1"
  port                 = 6379
  security_group_ids   = [data.aws_security_group.default.id]
}
