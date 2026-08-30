FROM kumatea/telethon:web

ARG PIP_PKGS="openai>=1.0.0 twifork"

# Install packages
RUN set -ex && \
    pip install $PIP_PKGS --prefer-binary --no-cache-dir --extra-index-url https://ext.kmtea.eu/cdn && \
    rm -rf /root/.cache

ENTRYPOINT ["/bin/sh", "/home/kuma/bots/rbsk/docker/run-docker.sh"]
