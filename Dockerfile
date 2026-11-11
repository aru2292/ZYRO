FROM python:3.11-slim

WORKDIR /app

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    gcc \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# ZIP ফাইল কপি করে আনজিপ করা
COPY ZYRO-Bot.zip .
RUN unzip ZYRO-Bot.zip && \
    mv ZYRO-Bot/* . && \
    rm -rf ZYRO-Bot ZYRO-Bot.zip

# Dependencies ইনস্টল
RUN pip install --no-cache-dir -r requirements.txt

# db ফোল্ডার তৈরি
RUN mkdir -p db

CMD ["python", "main.py"]
