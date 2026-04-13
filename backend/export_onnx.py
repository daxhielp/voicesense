#!/usr/bin/env python3
"""
backend/export_onnx.py
One-time script: export EmotionCNN from emotion_model.pkl → model/emotion_model.onnx

Run from repo root:
    python backend/export_onnx.py

Requires torch to be installed locally. torch is NOT needed in production
after this export — the Docker image uses onnxruntime instead.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import torch
import torch.nn as nn

# ── EmotionCNN (self-contained — matches architecture in inference.py) ────────
class EmotionCNN(nn.Module):
    """
    3-block CNN for 8-class speech emotion recognition.
    Input:  (batch, 1, 128, 128) mel spectrogram
    Output: (batch, 8) raw logits
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


# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT  = Path(__file__).parent.parent
MODEL_PKL  = REPO_ROOT / "model" / "emotion_model.pkl"
MODEL_ONNX = REPO_ROOT / "model" / "emotion_model.onnx"


def _load_pkl() -> EmotionCNN:
    """Load emotion_model.pkl using the __main__ shim to resolve EmotionCNN."""
    _orig_main = sys.modules.get("__main__")
    _shim = types.ModuleType("__main__")
    _shim.EmotionCNN = EmotionCNN  # type: ignore[attr-defined]
    sys.modules["__main__"] = _shim
    try:
        obj = torch.load(MODEL_PKL, map_location=torch.device("cpu"), weights_only=False)
    finally:
        if _orig_main is not None:
            sys.modules["__main__"] = _orig_main
        else:
            sys.modules.pop("__main__", None)

    if isinstance(obj, dict):
        print("Detected state_dict — instantiating EmotionCNN and loading weights.")
        model = EmotionCNN(num_classes=8)
        model.load_state_dict(obj)
    elif isinstance(obj, nn.Module):
        print("Detected full model object.")
        model = obj
    else:
        raise RuntimeError(f"Unknown object type in pkl: {type(obj)}")

    return model


def export() -> None:
    if not MODEL_PKL.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PKL}")

    print(f"Loading {MODEL_PKL} ...")
    model = _load_pkl()
    model.eval()

    dummy_input = torch.zeros(1, 1, 128, 128)

    print(f"Exporting to {MODEL_ONNX} (opset 17) ...")
    torch.onnx.export(
        model,
        dummy_input,
        str(MODEL_ONNX),
        opset_version=17,
        input_names=["mel_spectrogram"],
        output_names=["logits"],
        dynamic_axes={
            "mel_spectrogram": {0: "batch_size"},
            "logits":          {0: "batch_size"},
        },
    )

    size_mb = MODEL_ONNX.stat().st_size / 1_000_000
    print(f"Done — {MODEL_ONNX}  ({size_mb:.1f} MB)")

    # Quick sanity check with onnxruntime if available
    try:
        import onnxruntime as ort
        import numpy as np
        session = ort.InferenceSession(str(MODEL_ONNX), providers=["CPUExecutionProvider"])
        inp = dummy_input.numpy()
        out = session.run(None, {"mel_spectrogram": inp})[0]
        assert out.shape == (1, 8), f"Unexpected output shape: {out.shape}"
        print(f"Sanity check passed — output shape {out.shape}, logits: {out[0].round(3)}")
    except ImportError:
        print("onnxruntime not installed locally — skipping sanity check.")


if __name__ == "__main__":
    export()
