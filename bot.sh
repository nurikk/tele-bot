#!/usr/bin/env bash
SELF_IP=$(curl https://ipinfo.io/ip)
echo "Self IP: $SELF_IP"
export SELF_IP
aerich upgrade
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program python -m src.main