# backend/Dockerfile
# Build context must be voiceSense/ (repo root) so we can COPY model/
FROM python:3.11-slim

# System deps: ffmpeg for pydub audio conversion, libsndfile1 for librosa/soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (no torch — replaced by onnxruntime ~8 MB)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir \
    fastapi==0.135.3 \
    "uvicorn[standard]==0.44.0" \
    python-multipart==0.0.26 \
    pydub==0.25.1 \
    "librosa==0.11.0" \
    "numpy==2.4.4" \
    "scipy==1.17.1" \
    "onnxruntime==1.21.0"

# Copy backend source files
COPY backend/main.py .
COPY backend/inference.py .

# Copy ONNX model (external data format: .onnx graph + .onnx.data weights)
# Both files must be in the same directory for onnxruntime to resolve weights
COPY model/emotion_model.onnx /model/emotion_model.onnx
COPY model/emotion_model.onnx.data /model/emotion_model.onnx.data

# Render injects PORT; default to 8000
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
