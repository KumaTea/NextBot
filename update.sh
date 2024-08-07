#!/usr/bin/env bash


PROJECT="rbsk"

git pull
git submodule update --init --recursive
git pull --recurse-submodules
git submodule update --remote --recursive  # --force

docker stop $PROJECT
sudo bash -c "echo '' > \$(docker inspect --format='{{.LogPath}}' $PROJECT)"

docker start $PROJECT

docker logs $PROJECT -f
