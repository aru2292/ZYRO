FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libffi-dev libnacl-dev gcc unzip && rm -rf /var/lib/apt/lists/*
COPY . .
RUN echo "Unzipping ZYRO-Hard.zip ..." && \
    unzip -o ZYRO-Hard.zip && cp -r ZYRO-Hard/* . && rm -rf ZYRO-Hard ZYRO-Hard.zip
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p db
CMD ["python", "main.py"]
