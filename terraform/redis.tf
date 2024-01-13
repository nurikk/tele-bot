resource "aws_elasticache_subnet_group" "redis" {
  name       = "telebot-cache-subnet"
  subnet_ids = concat(aws_subnet.public.*.id, aws_subnet.private.*.id)
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "telebot-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.1"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.security_group.id]
}
