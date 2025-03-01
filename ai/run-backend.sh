#!/usr/bin/env bash


set -ex

HOST="0.0.0.0"
PORT="12000"

cd /home/kuma/NextBot/ai
Environment="PATH=/home/kuma/.conda/envs/ai/bin:/opt/conda/condabin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"
/home/kuma/.conda/envs/ai/bin/uvicorn v2t.main:app --host $HOST --port $PORT &
