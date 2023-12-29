#!/usr/bin/env bash

 aerich upgrade
 uvicorn src.server:app