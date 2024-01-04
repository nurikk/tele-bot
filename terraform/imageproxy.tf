resource "aws_security_group" "image_proxy_sg" {
  vpc_id = aws_default_vpc.default.id

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

#resource "aws_lb" "ecs_alb" {
#  name               = "ecs-alb"
#  internal           = false
#  load_balancer_type = "application"
#  security_groups    = [
#    aws_security_group.image_proxy_sg.id
#  ]
#  subnets = [
#    aws_default_subnet.default_subnet_a.id,
#    aws_default_subnet.default_subnet_b.id
#  ]
#}

#resource "aws_lb_listener" "ecs_alb_listener" {
#  load_balancer_arn = aws_lb.ecs_alb.arn
#  port              = 8080
#  protocol          = "HTTP"
#
#  default_action {
#    type             = "forward"
#    target_group_arn = aws_lb_target_group.ecs_tg.arn
#  }
#}
#
#resource "aws_lb_target_group" "ecs_tg" {
#  name        = "ecs-target-group"
#  port        = 8080
#  protocol    = "HTTP"
#  target_type = "ip"
#  vpc_id      = aws_default_vpc.default.id
#
#  health_check {
#    path = "/health"
#  }
#}