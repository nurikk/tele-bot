resource "aws_db_instance" "db" {
  allocated_storage           = 20
  db_name                     = "tele-bot"
  engine                      = "postgresql"
  engine_version              = "15.5-R1"
  instance_class              = "db.t3.micro"
  username                    = "bot"
  manage_master_user_password = true
  parameter_group_name = "default.postgres15"
}
