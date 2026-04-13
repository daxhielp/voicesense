#!/usr/bin/env python3
"""
backend/profile_inference.py
Dev-only profiler — times each preprocessing step independently.

Run from repo root:
    python backend/profile_inference.py path/to/audio.wav
    python backend/profile_inference.py path/to/recording.webm

Output: per-step ms timings + percentage breakdown to identify the bottleneck.
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

import librosa
import numpy as np
import onnxruntime as ort
import scipy.ndimage

# ── Input ─────────────────────────────────────────────────────────────────────
if len(sys.argv) < 2:
    print("Usage: python backend/profile_inference.py <path/to/audio.(wav|webm|ogg)>")
    sys.exit(1)

audio_path   = Path(sys.argv[1])
audio_bytes  = audio_path.read_bytes()
content_type = (
    "audio/webm" if audio_path.suffix.lower() == ".webm"
    else "audio/ogg" if audio_path.suffix.lower() == ".ogg"
    else "audio/wav"
)

print()
print(f"  File : {audio_path.name}")
print(f"  Size : {len(audio_bytes) / 1024:.1f} KB")
print(f"  Type : {content_type}")
print()

timings: dict[str, float] = {}

# ── Step 1: pydub + ffmpeg (WebM/OGG → WAV) ──────────────────────────────────
t0 = time.perf_counter()
from pydub import AudioSegment  # noqa: E402

if "wav" in content_type:
    wav_bytes = audio_bytes
else:
    fmt = "webm" if "webm" in content_type else "ogg"
    segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
    buf = io.BytesIO()
    segment.export(buf, format="wav")
    wav_bytes = buf.getvalue()

timings["1. pydub+ffmpeg  (→ WAV)"] = time.perf_counter() - t0

# ── Step 2: soundfile.read + scipy.signal.resample_poly ──────────────────────
SAMPLE_RATE = 22050
TARGET_LEN  = SAMPLE_RATE * 3  # 66,150 samples (3 s)

import soundfile as sf
import scipy.signal
from math import gcd

t0 = time.perf_counter()
y_raw, native_sr = sf.read(io.BytesIO(wav_bytes), dtype="float32", always_2d=False)
if y_raw.ndim > 1:
    y_raw = y_raw.mean(axis=1)
if native_sr != SAMPLE_RATE:
    g = gcd(native_sr, SAMPLE_RATE)
    y = scipy.signal.resample_poly(y_raw, SAMPLE_RATE // g, native_sr // g)
else:
    y = y_raw
timings["2. soundfile+resample_poly (decode+resample)"] = time.perf_counter() - t0

# Pad / truncate (negligible, not a bottleneck candidate)
if len(y) < TARGET_LEN:
    y = np.pad(y, (0, TARGET_LEN - len(y)), mode="constant")
else:
    y = y[:TARGET_LEN]

# ── Step 3: mel spectrogram + power_to_db ────────────────────────────────────
t0 = time.perf_counter()
mel    = librosa.feature.melspectrogram(
    y=y, sr=SAMPLE_RATE, n_mels=128, n_fft=2048, hop_length=512,
)
mel_db = librosa.power_to_db(mel, ref=np.max)
timings["3. mel spectrogram + power_to_db"] = time.perf_counter() - t0

# ── Step 4: scipy bilinear resize (→ 128×128) ────────────────────────────────
t0 = time.perf_counter()
h, w      = mel_db.shape
mel_r     = scipy.ndimage.zoom(mel_db, (128 / h, 128 / w), order=1)
timings["4. scipy resize   (→ 128×128)"] = time.perf_counter() - t0

# ── Step 5: normalize + reshape ──────────────────────────────────────────────
t0 = time.perf_counter()
tensor = mel_r[np.newaxis, np.newaxis, :, :].astype(np.float32) / 80.0
timings["5. normalize + reshape"] = time.perf_counter() - t0

# ── Step 6: onnxruntime forward pass ─────────────────────────────────────────
MODEL_PATH = Path(__file__).parent.parent / "model" / "emotion_model.onnx"
session    = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
input_name = session.get_inputs()[0].name

# Warm-up call (loads .onnx.data weights into memory — not representative)
_ = session.run(None, {input_name: tensor})

# Timed call (weights already warm)
t0 = time.perf_counter()
logits = session.run(None, {input_name: tensor})[0]
timings["6. onnxruntime    session.run()"] = time.perf_counter() - t0

# ── Results ───────────────────────────────────────────────────────────────────
total_s = sum(timings.values())

print(f"  {'Step':<42} {'ms':>8}   {'%':>6}")
print("  " + "-" * 60)
for step, elapsed in timings.items():
    ms  = elapsed * 1_000
    pct = elapsed / total_s * 100 if total_s > 0 else 0.0
    print(f"  {step:<42} {ms:>8.1f}   {pct:>5.1f}%")
print("  " + "-" * 60)
print(f"  {'TOTAL':<42} {total_s * 1_000:>8.1f}   100.0%")
print()

dominant = max(timings, key=timings.get)
dom_pct  = timings[dominant] / total_s * 100
print(f"  Dominant step : {dominant.strip()} ({timings[dominant]*1000:.1f} ms, {dom_pct:.0f}%)")
print()

# Quick sanity: print predicted emotion
import numpy as np  # already imported above
lv = logits.squeeze()
exp_l = np.exp(lv - lv.max())
probs = exp_l / exp_l.sum()
labels = ["neutral","calm","happy","sad","angry","fearful","disgust","surprised"]
pred   = labels[int(probs.argmax())]
conf   = float(probs.max()) * 100
print(f"  Prediction    : {pred} ({conf:.1f}% confidence)")
print()
