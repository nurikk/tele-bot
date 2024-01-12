resource "random_password" "db_password" {
  length  = 16
  special = false
}

resource "aws_db_subnet_group" "default" {
  name = "main"
  subnet_ids = concat(
    aws_subnet.public[*].id,
    aws_subnet.private[*].id
  )

}

resource "aws_db_instance" "db" {
  identifier           = "tele-bot-db"
  allocated_storage    = 20
  db_name              = "telebot"
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = "db.t3.micro"
  username             = "bot"
  password             = random_password.db_password.result
  parameter_group_name = "default.postgres16"
  publicly_accessible  = true
  deletion_protection  = true

  db_subnet_group_name   = aws_db_subnet_group.default.name
  vpc_security_group_ids = [aws_security_group.security_group.id]
}
