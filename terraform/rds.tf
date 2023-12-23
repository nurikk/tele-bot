resource "aws_db_instance" "db" {
  identifier                  = "tele-bot-db"
  allocated_storage           = 20
  db_name                     = "telebot"
  engine                      = "postgres"
  engine_version              = "16.1"
  instance_class              = "db.t3.micro"
  username                    = "bot"
  manage_master_user_password = true
  parameter_group_name        = "default.postgres16"
}
