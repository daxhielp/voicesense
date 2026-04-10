"""
backend/main.py
FastAPI application for VoiceSense Speech Emotion Recognition.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from inference import load_model, predict as run_predict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Pre-loading SER model at startup...")
    load_model()
    logger.info("Model ready — server is live")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="VoiceSense SER API",
    description="Speech Emotion Recognition — detects 8 emotions from voice audio.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_allowed: list[str] = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:4173",   # Vite preview
]
_env_origins = os.getenv("ALLOWED_ORIGINS", "")
if _env_origins:
    _allowed.extend(o.strip() for o in _env_origins.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Health check used by Render and monitoring."""
    return {"status": "ok", "model_loaded": True}


@app.post("/predict")
async def predict_emotion(audio: UploadFile = File(...)):
    """
    POST multipart/form-data with field name 'audio'.
    Accepts WebM, OGG, WAV, MP4 audio up to 50 MB.
    Returns JSON with emotion label, confidence, and per-class probabilities.
    """
    content_type = audio.content_type or "audio/webm"
    logger.info(
        "Received audio: filename=%s content_type=%s",
        audio.filename,
        content_type,
    )

    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file.")
    if len(audio_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file too large (max 50 MB).")

    try:
        result = run_predict(audio_bytes, content_type)
        logger.info(
            "Prediction: %s (%.1f%% confidence)",
            result["emotion"],
            result["confidence"],
        )
        return result
    except Exception as e:
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail=f"Inference error: {e}") from e
