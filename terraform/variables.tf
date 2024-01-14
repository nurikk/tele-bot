variable "namespace" {
  default = "telebot"
  type    = string
}

variable "environment" {
  default = "production"
  type    = string
}

variable "OPENAI_API_KEY" {
  type = string
}

variable "REPLICATE_API_TOKEN" {
  type = string
}

variable "TELEGRAM_BOT_TOKEN" {
  type = string
}

variable "IMGPROXY_KEY" {
  type = string
}

variable "IMGPROXY_SALT" {
  type = string
}

variable "DUCK_DNS_TOKEN" {
  type = string
}

variable "DUCK_DNS_DOMAIN" {
  type = string
}

variable "LETSENCRYPT_EMAIL" {
  type = string
}

variable "IMAGEOPTIM_ACCOUNT_ID" {
  type = string
}

variable "REDASH_GOOGLE_CLIENT_ID" {
  type = string
}

variable "REDASH_GOOGLE_CLIENT_SECRET" {
  type = string
}

variable "GITHUB_REPO" {
  type    = string
  default = "https://github.com/nurikk/tele-bot.git"
}

variable "CODEPIPELINE_GITHUB_REPO" {
  type    = string
  default = "nurikk/tele-bot"
}

variable "GITHUB_BRANCH" {
  type    = string
  default = "master"
}


variable "vpc_cidr_block" {
  description = "CIDR block for the VPC network"
  default     = "10.32.0.0/16"
  type        = string
}

variable "az_count" {
  description = "Describes how many availability zones are used"
  default     = 2
  type        = number
}

variable "WHITELIST_IP" {
  type = list(string)
  default = []
}