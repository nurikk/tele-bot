#!/usr/bin/env bash

 aerich upgrade
 NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program python -m src.main