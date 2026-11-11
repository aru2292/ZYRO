
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg unzip curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:${PATH}"

COPY ZYRO.zip /tmp/ZYRO.zip

RUN mkdir -p /tmp/zyro && \
    unzip -q /tmp/ZYRO.zip -d /tmp/zyro && \
    MAIN_DIR="$(dirname "$(find /tmp/zyro -name main.py -print -quit)")" && \
    test -f "$MAIN_DIR/main.py" && \
    cp -a "$MAIN_DIR"/. /app/ && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --upgrade yt-dlp

CMD ["python", "main.py"]
