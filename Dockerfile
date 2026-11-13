FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libopus0 libsodium23 unzip \
    && rm -rf /var/lib/apt/lists/*

# copy whole repo
COPY . /repo

# unzip every .zip in repo root (alphabetical; later zip overwrites earlier), else use repo files directly
RUN set -e; mkdir -p /app /tmp/x; \
    if ls /repo/*.zip >/dev/null 2>&1; then \
        for z in $(ls /repo/*.zip | sort); do unzip -oq "$z" -d /tmp/x; done; \
        MAIN=$(find /tmp/x -name main.py -not -path '*/node_modules/*' | head -n1); \
        cp -r "$(dirname "$MAIN")"/. /app/; \
    else \
        cp -r /repo/. /app/; \
    fi

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
