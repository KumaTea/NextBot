# Fallback image. docker/alpine.Dockerfile is the one deployed -- use this only
# where musl wheels are unavailable, or to avoid compiling anything at all.
#
# Debian slim rather than the old conda base: every dependency here has a
# manylinux wheel, cryptg included, so there is no build step.
FROM python:3.12-slim

# This host reaches pypi.org through a proxy that intermittently returns
# truncated index responses ("No matching distribution found" for packages
# that plainly exist). A mirror avoids it. Override for a different network:
#   docker build --build-arg PIP_INDEX=https://pypi.org/simple ...
ARG PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple

# The bot moved from pyrogram to telethon. The previous image installed
# pyrogram and tgcrypto and no telethon at all, so it could not start.
#   cryptg  -- telethon's native MTProto crypto, a large speed-up
#   twifork -- maintained twikit fork, used for the X mirror; the bot still
#              starts (with the mirror off) if it is unavailable
RUN set -ex && \
    pip install --no-cache-dir --retries 5 --timeout 60 -i "$PIP_INDEX" \
        aiohttp \
        beautifulsoup4 \
        requests \
        uvloop \
        "openai>=1.0.0" \
        telethon \
        cryptg \
        twifork && \
    rm -rf /root/.cache


# Set entrypoint
ENTRYPOINT ["/bin/sh", "/home/kuma/bots/rbsk/docker/run-docker.sh"]
