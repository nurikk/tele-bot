variable "GOOGLE_CREDENTIALS" {
  type = string
}

variable "GOOGLE_REGION" {
  type = string
}

variable "GOOGLE_OAUTH_CLIENT_ID" {
  type = string
}

variable "GOGGLE_OAUTH_CLIENT_SECRET" {
  type = string
}

provider "google" {
  credentials = var.GOOGLE_CREDENTIALS
  region      = var.GOOGLE_REGION
}

resource "google_looker_instance" "looker-instance" {
  name             = "test-looker-instance"
  platform_edition = "LOOKER_CORE_TRIAL"
  oauth_config {
    client_id     = var.GOOGLE_OAUTH_CLIENT_ID
    client_secret = var.GOGGLE_OAUTH_CLIENT_SECRET
  }
}
