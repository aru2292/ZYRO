FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libopus0 libsodium23 unzip \
    && rm -rf /var/lib/apt/lists/*

# repo-r sob file (zip shoho) copy
COPY . /repo

# repo-r vitor jotogulo .zip ache sob unzip kore /app e rakho
RUN set -e; \
    mkdir -p /tmp/x /app; \
    for z in /repo/*.zip; do unzip -oq "$z" -d /tmp/x; done; \
    MAIN=$(find /tmp/x -name main.py | head -n1); \
    cp -r "$(dirname "$MAIN")"/. /app/

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
