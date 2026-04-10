"""
backend/inference.py
Speech Emotion Recognition inference — loads emotion_model.pkl and exposes
predict(audio_bytes, content_type) -> dict
"""
from __future__ import annotations

import io
import logging
import pickle
from pathlib import Path

import librosa
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

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
DURATION    = 3                           # seconds
TARGET_LEN  = SAMPLE_RATE * DURATION     # 66,150 samples
N_MELS      = 128
N_FFT       = 2048
HOP_LENGTH  = 512
IMG_SIZE    = (128, 128)                  # (H, W) fed to CNN
NORM_FACTOR = 80.0                        # maps dB range [-80,0] → [-1,0]

MODEL_PATH = Path(__file__).parent.parent / "model" / "emotion_model.pkl"


# ── CNN Architecture ─────────────────────────────────────────────────────────
class EmotionCNN(nn.Module):
    """
    Exact architecture used in week2_cnn.ipynb.
    Input:  (batch, 1, 128, 128)
    Output: (batch, 8)  — raw logits, no softmax
    """

    def __init__(self, num_classes: int = 8) -> None:
        super().__init__()
        self.block1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )
        self.block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )
        self.block3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(128 * 16 * 16, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


# ── Model loading (singleton pattern) ────────────────────────────────────────
_model: EmotionCNN | None = None


def load_model() -> EmotionCNN:
    """
    Load emotion_model.pkl once and cache it.

    Strategy:
      1. torch.load() — handles both full model objects and state_dicts
      2. If result is an OrderedDict (state_dict), instantiate EmotionCNN and load_state_dict
      3. Fall back to pickle.load() if torch.load() raises
    """
    global _model
    if _model is not None:
        return _model

    logger.info("Loading model from %s", MODEL_PATH)

    obj = None

    # The model was saved from a Jupyter notebook via torch.save(model, path),
    # so pickle serialized EmotionCNN under __main__.EmotionCNN.  When loaded
    # outside a notebook (e.g. from uvicorn) __main__ is a frozen built-in
    # module and pickle can't resolve the class.  We temporarily replace
    # sys.modules['__main__'] with a lightweight module that exposes
    # EmotionCNN, then restore the original after deserialization.
    import sys
    import types

    _orig_main = sys.modules.get("__main__")
    _shim = types.ModuleType("__main__")
    _shim.EmotionCNN = EmotionCNN  # type: ignore[attr-defined]
    sys.modules["__main__"] = _shim
    try:
        obj = torch.load(
            MODEL_PATH,
            map_location=torch.device("cpu"),
            weights_only=False,
        )
        logger.info("torch.load succeeded, type=%s", type(obj).__name__)
    except Exception as e:
        logger.warning("torch.load failed: %s", e)
        obj = None
    finally:
        # Always restore the real __main__
        if _orig_main is not None:
            sys.modules["__main__"] = _orig_main
        else:
            sys.modules.pop("__main__", None)

    if obj is None:
        raise RuntimeError(
            f"Cannot load model from {MODEL_PATH}. "
            "Ensure emotion_model.pkl is a valid PyTorch model or state_dict."
        )

    # Determine if obj is a state_dict or a full model
    if isinstance(obj, dict):
        logger.info("Detected state_dict — instantiating EmotionCNN")
        model = EmotionCNN(num_classes=8)
        model.load_state_dict(obj)
    elif isinstance(obj, nn.Module):
        model = obj
    else:
        raise RuntimeError(f"Unknown model object type: {type(obj)}")

    model.eval()
    _model = model
    logger.info("Model ready (eval mode)")
    return _model


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


def preprocess_audio(audio_bytes: bytes, content_type: str) -> torch.Tensor:
    """
    Full preprocessing pipeline matching RavdessSpectrogramDataset._preprocess():

      1. Convert to WAV (via pydub/ffmpeg)
      2. librosa.load(sr=22050, mono=True)
      3. Pad/truncate to exactly 66,150 samples (3 s)
      4. Mel spectrogram (n_fft=2048, hop_length=512, n_mels=128) → dB
      5. F.interpolate bilinear → (128, 128)
      6. Divide by 80 → [-1, 0] normalized

    Returns:
        torch.Tensor of shape (1, 1, 128, 128) ready for model
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

    # Resize to (128, 128) with bilinear interpolation (matches training)
    t = torch.from_numpy(mel_db).unsqueeze(0).unsqueeze(0).float()  # (1, 1, H, W)
    t = F.interpolate(t, size=IMG_SIZE, mode="bilinear", align_corners=False)

    # Normalize: dB range [-80, 0] → [-1, 0]
    t = t / NORM_FACTOR

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
    model = load_model()
    tensor = preprocess_audio(audio_bytes, content_type)

    with torch.no_grad():
        logits = model(tensor)                              # (1, 8) raw logits
        probs  = torch.softmax(logits, dim=1).squeeze()    # (8,)

    probs_np  = probs.numpy()
    pred_idx  = int(probs_np.argmax())
    pred_name = EMOTION_LABELS[pred_idx]

    probabilities = {
        EMOTION_LABELS[i]: round(float(probs_np[i]) * 100, 2)
        for i in range(8)
    }
    probabilities_sorted = dict(
        sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    )

    return {
        "emotion":       pred_name,
        "confidence":    round(float(probs_np[pred_idx]) * 100, 2),
        "probabilities": probabilities_sorted,
        "color":         EMOTION_META[pred_name]["color"],
        "emoji":         EMOTION_META[pred_name]["emoji"],
    }
