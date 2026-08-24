FROM kumatea/telethon

# Create conda environment
RUN set -ex && \
    pip install --no-cache-dir --retries 5 --timeout 60 \
        aiohttp \
        beautifulsoup4 \
        requests \
        "openai>=1.0.0" \
        twifork && \
    rm -rf /root/.cache


ENTRYPOINT ["/bin/sh", "/home/kuma/bots/rbsk/docker/run-docker.sh"]
