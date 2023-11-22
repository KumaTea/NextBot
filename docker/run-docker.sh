#!/usr/bin/env bash

set -ex

rm -f /tmp/rbsk.log || :

cd /home/kuma/bots/rbsk
/opt/conda/envs/rbsk/bin/python3 main.py >> /tmp/rbsk.log 2>&1 &
/opt/conda/envs/rbsk/bin/gunicorn --bind=127.0.0.1:13600 mediabot:app >> /tmp/rbsk.log 2>&1 &
tail -f /tmp/rbsk.log
