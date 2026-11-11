# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Secrets come from Render env vars; HF_TOKEN is needed at startup to load the
# gated dataset (script falls back gracefully if missing).
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# Gradio app with queue (Render uses healthCheckPath /; Gradio serves UI at /).
CMD ["python", "app_gradio.py"]