"""
backend/inference.py
Speech Emotion Recognition inference — loads emotion_model.onnx via ONNX Runtime
and exposes predict(audio_bytes, content_type) -> dict
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

import librosa
import numpy as np
import onnxruntime as ort
import scipy.ndimage

logger = logging.getLogger(__name__)

# ── Emotion labels (must match RAVDESS training order) ───────────────────────
EMOTION_LABELS: dict[int, str] = {
    0: "neutral",
    1: "calm",
    2: "happy",
    3: "sad",
    4: "angry",
    5: "fearful",
    6: "disgust",
    7: "surprised",
}

# ── Emotion metadata for frontend display ────────────────────────────────────
EMOTION_META: dict[str, dict[str, str]] = {
    "neutral":   {"color": "#94a3b8", "emoji": "😐"},
    "calm":      {"color": "#60a5fa", "emoji": "😌"},
    "happy":     {"color": "#fbbf24", "emoji": "😄"},
    "sad":       {"color": "#818cf8", "emoji": "😢"},
    "angry":     {"color": "#f87171", "emoji": "😠"},
    "fearful":   {"color": "#a78bfa", "emoji": "😨"},
    "disgust":   {"color": "#34d399", "emoji": "🤢"},
    "surprised": {"color": "#fb923c", "emoji": "😲"},
}

# ── Preprocessing constants (must match training exactly) ────────────────────
SAMPLE_RATE = 22050
DURATION    = 3                        # seconds
TARGET_LEN  = SAMPLE_RATE * DURATION  # 66,150 samples
N_MELS      = 128
N_FFT       = 2048
HOP_LENGTH  = 512
IMG_SIZE    = (128, 128)              # (H, W) fed to model
NORM_FACTOR = 80.0                    # maps dB range [-80, 0] → [-1, 0]

MODEL_PATH = Path(__file__).parent.parent / "model" / "emotion_model.onnx"


# ── ONNX Runtime session (singleton) ─────────────────────────────────────────
_session: ort.InferenceSession | None = None


def load_model() -> ort.InferenceSession:
    """
    Load emotion_model.onnx once and cache the InferenceSession.
    onnxruntime automatically resolves emotion_model.onnx.data from the same directory.
    """
    global _session
    if _session is not None:
        return _session

    logger.info("Loading ONNX model from %s", MODEL_PATH)
    _session = ort.InferenceSession(
        str(MODEL_PATH),
        providers=["CPUExecutionProvider"],
    )
    input_name = _session.get_inputs()[0].name
    logger.info("ONNX session ready — input: %s %s", input_name, _session.get_inputs()[0].shape)
    return _session


# ── Audio preprocessing ───────────────────────────────────────────────────────
def _convert_to_wav_bytes(audio_bytes: bytes, content_type: str) -> bytes:
    """
    Convert WebM/OGG/MP4 browser audio to WAV bytes via pydub + ffmpeg.
    Returns raw WAV bytes.
    """
    from pydub import AudioSegment  # deferred import — only needed at runtime

    ct = content_type.lower()
    if "wav" in ct:
        return audio_bytes

    fmt = "webm"
    if "ogg" in ct:
        fmt = "ogg"
    elif "mp4" in ct or "m4a" in ct:
        fmt = "mp4"

    segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
    buf = io.BytesIO()
    segment.export(buf, format="wav")
    return buf.getvalue()


def preprocess_audio(audio_bytes: bytes, content_type: str) -> np.ndarray:
    """
    Full preprocessing pipeline matching RavdessSpectrogramDataset._preprocess():

      1. Convert to WAV (via pydub/ffmpeg)
      2. librosa.load(sr=22050, mono=True)
      3. Pad/truncate to exactly 66,150 samples (3 s)
      4. Mel spectrogram (n_fft=2048, hop_length=512, n_mels=128) → dB
      5. scipy.ndimage.zoom bilinear → (128, 128)
      6. Divide by 80 → [-1, 0] normalized

    Returns:
        np.ndarray of shape (1, 1, 128, 128), dtype float32, ready for ONNX session
    """
    wav_bytes = _convert_to_wav_bytes(audio_bytes, content_type)

    y, _ = librosa.load(io.BytesIO(wav_bytes), sr=SAMPLE_RATE, mono=True)

    # Pad or truncate to exactly TARGET_LEN samples
    if len(y) < TARGET_LEN:
        y = np.pad(y, (0, TARGET_LEN - len(y)), mode="constant")
    else:
        y = y[:TARGET_LEN]

    # Mel spectrogram in dB
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=SAMPLE_RATE,
        n_mels=N_MELS,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
    )
    mel_db = librosa.power_to_db(mel, ref=np.max)

    # Bilinear resize to (128, 128) — scipy order=1 matches PyTorch bilinear for this range
    h, w = mel_db.shape
    mel_resized = scipy.ndimage.zoom(mel_db, (IMG_SIZE[0] / h, IMG_SIZE[1] / w), order=1)

    # Normalize: dB range [-80, 0] → [-1, 0]; add batch + channel dims
    t = mel_resized[np.newaxis, np.newaxis, :, :].astype(np.float32) / NORM_FACTOR

    return t  # shape (1, 1, 128, 128)


# ── Public inference function ─────────────────────────────────────────────────
def predict(audio_bytes: bytes, content_type: str) -> dict:
    """
    Run full SER inference on raw audio bytes from the browser.

    Returns:
        {
            "emotion": "happy",
            "confidence": 87.3,
            "probabilities": {
                "happy": 87.3,
                "neutral": 2.1,
                ...  (sorted descending)
            },
            "color": "#fbbf24",
            "emoji": "😄"
        }
    """
    session = load_model()
    tensor  = preprocess_audio(audio_bytes, content_type)  # (1, 1, 128, 128) float32

    input_name = session.get_inputs()[0].name
    logits = session.run(None, {input_name: tensor})[0]  # (1, 8) float32

    # Numerically stable softmax
    logits = logits.squeeze()          # (8,)
    exp_l  = np.exp(logits - logits.max())
    probs  = exp_l / exp_l.sum()      # (8,)

    pred_idx  = int(probs.argmax())
    pred_name = EMOTION_LABELS[pred_idx]

    probabilities = {
        EMOTION_LABELS[i]: round(float(probs[i]) * 100, 2)
        for i in range(8)
    }
    probabilities_sorted = dict(
        sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    )

    return {
        "emotion":       pred_name,
        "confidence":    round(float(probs[pred_idx]) * 100, 2),
        "probabilities": probabilities_sorted,
        "color":         EMOTION_META[pred_name]["color"],
        "emoji":         EMOTION_META[pred_name]["emoji"],
    }
