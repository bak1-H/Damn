FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y ffmpeg libopus0 gcc pkg-config && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "bot.py"]