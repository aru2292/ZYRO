FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libopus0 libsodium23 unzip \
    && rm -rf /var/lib/apt/lists/*

COPY . /repo

RUN set -e; mkdir -p /app /tmp/x; \
    find /repo -maxdepth 1 -iname '*.zip' -print0 | LC_ALL=C sort -z | xargs -0 -r -I{} unzip -oq {} -d /tmp/x; \
    MAIN=$(find /tmp/x -maxdepth 2 -name main.py | head -n1); \
    if [ -n "$MAIN" ]; then cp -r "$(dirname "$MAIN")"/. /app/; else cp -r /repo/. /app/; fi; \
    test -f /app/main.py

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
