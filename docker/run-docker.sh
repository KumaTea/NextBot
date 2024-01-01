#!/usr/bin/env bash

set -ex

rm -f /tmp/rbsk.log || true
touch /tmp/rbsk.log
rm -f /tmp/media.log || true
touch /tmp/media.log

cd /home/kuma/bots/rbsk
# /opt/conda/envs/rbsk/bin/python3 main.py       >> /tmp/rbsk.log  2>&1 &
# sleep 1
# /opt/conda/envs/rbsk/bin/python3 mediabot.py >> /tmp/media.log 2>&1 &
# tail -f /tmp/rbsk.log /tmp/media.log
/opt/conda/envs/rbsk/bin/python3 main.py 2>&1 | tee -a /tmp/rbsk.log
