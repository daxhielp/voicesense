# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VoiceSense is a full-stack Speech Emotion Recognition (SER) web application. Users record their voice in the browser and receive a real-time emotion prediction from a CNN trained on the RAVDESS dataset (8 emotions, 24 actors). Prior research and model training live in the sibling `../ser-project/` directory.

## Local Development

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu
pip install fastapi uvicorn[standard] python-multipart pydub librosa numpy scipy
uvicorn main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/health`

Test predict: `curl -X POST http://localhost:8000/predict -F "audio=@file.webm;type=audio/webm"`

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # production build to dist/
```

Vite proxies `/api/*` → `http://localhost:8000` during dev (configured in `vite.config.ts`).

## Architecture

### Backend (`backend/`)

Two files — FastAPI app thin layer over inference logic:

**`inference.py`** — the core ML pipeline:
- `EmotionCNN` — PyTorch architecture (3 conv blocks + FC classifier, input `(B,1,128,128)`)
- `load_model()` — singleton loader; tries `torch.load()` first, falls back to `pickle.load()`. Handles both state_dict and full model objects.
- `preprocess_audio(bytes, content_type)` — full pipeline: pydub/ffmpeg WAV conversion → librosa mel spec → `F.interpolate` bilinear resize to (128,128) → divide by 80.0 (critical normalization)
- `predict(bytes, content_type)` → `{emotion, confidence, probabilities, color, emoji}`

**`main.py`** — FastAPI:
- `POST /predict` — multipart `audio` field → calls `predict()`
- `GET /health`
- CORS: `localhost:5173` + `ALLOWED_ORIGINS` env var (comma-separated, set to Vercel URL in prod)

### Frontend (`frontend/src/`)

State machine: `idle → recording → processing → result`

| File | Role |
|---|---|
| `App.tsx` | Root; owns state machine, orchestrates recording → API call |
| `hooks/useAudioRecorder.ts` | MediaRecorder + Web Audio `AnalyserNode` (for waveform) |
| `api/predict.ts` | `axios.post('/predict', formData)` — uses `VITE_API_URL` env var |
| `components/ParticleBackground.tsx` | 3 animated gradient orbs + grid overlay (Framer Motion) |
| `components/IdleView.tsx` | Mic button with two pulsing concentric rings |
| `components/RecordingView.tsx` | REC timer, progress bar, live waveform, stop button |
| `components/WaveformVisualizer.tsx` | Canvas 60fps — reads `AnalyserNode.getByteTimeDomainData()` |
| `components/ResultView.tsx` | Spring-animated emotion hero + staggered probability bars |

## Deployment

### Backend → Render (Docker)

- **Dockerfile path:** `./backend/Dockerfile`
- **Docker context:** `.` (repo root — needed to `COPY model/emotion_model.pkl`)
- **Env var:** `ALLOWED_ORIGINS=https://your-app.vercel.app`
- CPU-only torch (~200 MB) fits Render free tier (512 MB RAM)

### Frontend → Vercel

- **Root Directory:** `frontend`
- **Env var:** `VITE_API_URL=https://your-render-service.onrender.com`

## Critical Implementation Notes

- **Normalization:** `tensor / 80.0` maps the dB mel spectrogram from [-80,0] to [-1,0]. This must match training or predictions will be garbage.
- **Resize:** Uses `torch.nn.functional.F.interpolate(..., mode='bilinear')`, NOT `scipy.ndimage.zoom` — the training notebook used `F.interpolate`.
- **Emotion label order:** `{0:neutral, 1:calm, 2:happy, 3:sad, 4:angry, 5:fearful, 6:disgust, 7:surprised}` — must match the label encoder used during training.
- **Model file:** `model/emotion_model.pkl` is 33 MB — a PyTorch state_dict (OrderedDict). `EmotionCNN` must be defined in `inference.py` before calling `load_state_dict`.
- **Audio format:** Browser records WebM/OGG; `pydub` + system `ffmpeg` converts to WAV before `librosa.load()`. `ffmpeg` must be installed (included in Dockerfile via `apt-get`).
