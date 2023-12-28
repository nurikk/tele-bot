resource "aws_iam_user" "telebot_s3_uploader" {
  name = "telebot_s3_uploader"
  path = "/"
}

resource "aws_iam_access_key" "telebot_s3_uploader" {
  user = aws_iam_user.telebot_s3_uploader.name
}
