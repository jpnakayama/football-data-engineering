FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pyspark==4.0.1 \
    pytest==8.4.2

WORKDIR /app

COPY processing/src/ /app/src/
COPY tests/ /app/tests/

ENV PYTHONPATH=/app

CMD ["python", "/app/src/process_matches.py"]