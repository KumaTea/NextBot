#!/bin/sh

set -ex

cd /home/kuma/bots/rbsk

# The conda-based image (docker/Dockerfile) keeps its interpreter in an env;
# the alpine image (docker/alpine.Dockerfile) uses the system one. Pick
# whichever is actually present rather than assuming either.
if [ -x /opt/conda/envs/rbsk/bin/python3 ]; then
    PYTHON=/opt/conda/envs/rbsk/bin/python3
else
    PYTHON=python3
fi

exec "$PYTHON" main.py
