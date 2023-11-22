#!/usr/bin/env bash

set -ex

rm -f /tmp/rbsk.log || :

cd /home/kuma/bots/rbsk
/opt/conda/envs/rbsk/bin/python3 main.py     >> /tmp/rbsk.log 2>&1 &
/opt/conda/envs/rbsk/bin/python3 mediabot.py >> /tmp/rbsk.log 2>&1 &
sleep 1
tail -f /tmp/rbsk.log
