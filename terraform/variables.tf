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
  type = string
  default = "https://github.com/nurikk/tele-bot.git"
}