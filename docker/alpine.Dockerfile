FROM kumatea/pyrogram:alpine

ENV PIP_PKGS="aiohttp beautifulsoup4 requests openai"

# Install packages
RUN set -ex && \
    pip install $PIP_PKGS --prefer-binary --no-cache-dir && \
    rm -rf /root/.cache || echo "No cache in .cache"


# Set entrypoint
ENTRYPOINT ["/bin/sh", "/home/kuma/bots/rbsk/docker/run-docker.sh"]
