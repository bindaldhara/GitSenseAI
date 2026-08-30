FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt

# FastEmbed + ONNX Runtime — no PyTorch. Keep the image small enough for Render Free.
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /app

ENV FASTEMBED_CACHE_PATH=/tmp/fastembed
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
