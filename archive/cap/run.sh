#!/bin/bash

set -ex

ps -A | grep gunicorn | awk '{print $1}' | xargs -n 1 kill || true

sleep 1

cd /home/kuma/cap
/home/kuma/.local/bin/gunicorn --bind=0.0.0.0:14500 main:app --timeout=240 > /tmp/cap.log 2>&1 &
