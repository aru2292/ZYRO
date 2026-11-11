FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    gcc \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Auto unzip the bot
RUN echo "Unzipping ZYRO-Final.zip ..." && \
    unzip -o ZYRO-Final.zip && \
    cp -r ZYRO-Final/* . && \
    rm -rf ZYRO-Final ZYRO-Final.zip

RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p db

CMD ["python", "main.py"]
