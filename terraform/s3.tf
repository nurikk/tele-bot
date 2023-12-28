resource "aws_s3_bucket" "telebot_bucket" {
  bucket = "telebot-images"
}


data "aws_iam_policy_document" "allow_access_from_internet_to_docs" {
  statement {
    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      aws_s3_bucket.telebot_bucket.arn,
      "${aws_s3_bucket.telebot_bucket.arn}/*"
    ]
  }
}

resource "aws_s3_bucket_policy" "allow_access_from_internet_to_docs" {
  bucket = aws_s3_bucket.telebot_bucket.id
  policy = data.aws_iam_policy_document.allow_access_from_internet_to_docs.json
}

resource "aws_s3_object" "object" {
  bucket = aws_s3_bucket.telebot_bucket.id
  key    = "index.html"
  source = "./index.html"
  etag = filemd5("./index.html")
}

resource "aws_s3_bucket_website_configuration" "telebot_static" {
  bucket = aws_s3_bucket.telebot_bucket.id
   index_document {
    suffix = aws_s3_object.object.key
  }
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket = aws_s3_bucket.telebot_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_ownership_controls" "site" {
  bucket = aws_s3_bucket.telebot_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "site" {
  depends_on = [
    aws_s3_bucket_public_access_block.site,
    aws_s3_bucket_ownership_controls.site,
  ]

  bucket = aws_s3_bucket.telebot_bucket.id
  acl    = "public-read"
}