# backend/Dockerfile
# Build context must be voiceSense/ (repo root) so we can COPY model/
FROM python:3.11-slim

# System deps: ffmpeg for pydub audio conversion, libsndfile1 for librosa/soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only PyTorch first (separate step for Docker layer caching)
# CPU wheel is ~200 MB vs ~900 MB for CUDA — critical for Render free tier
RUN pip install --no-cache-dir \
    torch==2.11.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Copy and install remaining Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir \
    fastapi==0.135.3 \
    "uvicorn[standard]==0.44.0" \
    python-multipart==0.0.26 \
    pydub==0.25.1 \
    "librosa==0.11.0" \
    "numpy==2.4.4" \
    "scipy==1.17.1"

# Copy backend source files
COPY backend/main.py .
COPY backend/inference.py .

# Copy model file (path relative to build context = voiceSense/)
COPY model/emotion_model.pkl /model/emotion_model.pkl

# Render injects PORT; default to 8000
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
