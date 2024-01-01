# Basic Telegram Bot Configuration

FROM kumatea/bot:latest

# Create conda environment
RUN set -ex && \
    eval "$(/opt/conda/bin/conda shell.bash hook)" && \
    conda create -n rbsk aiohttp beautifulsoup4 pyrogram uvloop requests "openai>=1.0.0" -y && \
    conda clean -afy && \
    conda activate rbsk && \
    pip install tgcrypto || wget "https://github.com/KumaTea/NextBot/releases/download/1.0/TgCrypto-1.2.5-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl" && pip install ./TgCrypto-1.2.5-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && rm ./TgCrypto-1.2.5-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    rm -rf /root/.cache/*


# Set entrypoint
ENTRYPOINT ["/bin/bash", "/home/kuma/bots/rbsk/docker/run-docker.sh"]
