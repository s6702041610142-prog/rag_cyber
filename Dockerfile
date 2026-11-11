# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Secrets come from Render env vars; HF_TOKEN is needed at startup to load the
# gated dataset (app falls back gracefully if missing).
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Chainlit app (run it directly as the container command).
CMD ["chainlit", "run", "app_chainlit.py", "--host", "0.0.0.0", "--port", "8000"]