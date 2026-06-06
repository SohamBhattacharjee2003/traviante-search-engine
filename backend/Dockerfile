# FastAPI + CLIP backend — deploys to HuggingFace Spaces (Docker SDK) or Railway.
FROM python:3.11-slim

# System deps for Pillow / torch runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

WORKDIR /app

# Install CPU-only PyTorch FIRST from PyTorch's CPU wheel index. The default
# PyPI torch on Linux bundles ~7GB of CUDA libraries that are dead weight on a
# CPU host (HF Spaces free tier). Installing it here means requirements.txt's
# `torch>=2.6.0` is already satisfied below, so pip won't pull the CUDA build.
RUN pip install --no-cache-dir \
    torch==2.6.0 torchvision==0.21.0 \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HuggingFace Spaces expects the app on port 7860; Railway injects $PORT.
EXPOSE 7860
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
