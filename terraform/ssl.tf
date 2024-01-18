locals {
  full_duck_dns_domain = "${var.DUCK_DNS_DOMAIN}.duckdns.org"
}
#
#resource "tls_private_key" "private_key" {
#  algorithm = "RSA"
#}
#
#
#
#resource "acme_registration" "registration" {
#  account_key_pem = tls_private_key.private_key.private_key_pem
#  email_address   = var.LETSENCRYPT_EMAIL
#}
#
#
#resource "acme_certificate" "certificate" {
#  account_key_pem = acme_registration.registration.account_key_pem
#  common_name     = local.full_duck_dns_domain
#  subject_alternative_names = [local.full_duck_dns_domain]
#
#  dns_challenge {
#    provider = "duckdns"
#    config = {
#      DUCKDNS_TOKEN = var.DUCK_DNS_TOKEN
#    }
#  }
#
#  depends_on = [acme_registration.registration]
#}
