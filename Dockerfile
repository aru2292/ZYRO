FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg unzip && rm -rf /var/lib/apt/lists/*

COPY ZYRO.zip /tmp/ZYRO.zip

RUN mkdir -p /tmp/zyro && \
    unzip -q /tmp/ZYRO.zip -d /tmp/zyro && \
    MAIN_DIR="$(dirname "$(find /tmp/zyro -name main.py -print -quit)")" && \
    test -f "$MAIN_DIR/main.py" && \
    cp -a "$MAIN_DIR"/. /app/ && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
