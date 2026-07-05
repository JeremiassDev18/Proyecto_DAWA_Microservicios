FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir pika

CMD ["python", "-u", "backend/worker.py"]
