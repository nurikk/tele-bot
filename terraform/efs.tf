resource "aws_efs_file_system" "telebot" {
}

resource "aws_efs_mount_target" "mount" {
  count           = length(aws_subnet.public)
  file_system_id  = aws_efs_file_system.telebot.id
  subnet_id       = aws_subnet.public[count.index].id
  security_groups = [aws_security_group.security_group.id]
}