# VoiceSense — Speech Emotion Recognition

> Record your voice in the browser and get a real-time emotion prediction powered by a deep learning model trained on the RAVDESS dataset.

**Live demo:** `https://voicesense-beryl.vercel.app/` 

---

## What It Does

VoiceSense is a full-stack AI application that classifies eight emotions from short voice recordings — **neutral, calm, happy, sad, angry, fearful, disgust, and surprised** — using a convolutional neural network trained on mel spectrograms.

The user experience is intentionally minimal: press record, speak, and receive an animated breakdown of predicted emotions with confidence scores.

---

## Technical Highlights

### Machine Learning Pipeline

| Stage | Detail |
|---|---|
| Dataset | RAVDESS — 2,880 clips, 24 actors, 8 balanced emotion classes |
| Features | 128-band mel spectrogram → resized to 128×128 (matches image CNN input) |
| Architecture | 3-block CNN (Conv2D → BatchNorm → ReLU → MaxPool) + dropout + FC classifier |
| Training | Adam optimizer, SpecAugment data augmentation, early stopping on val loss |
| Inference | ~1–3 s on CPU; audio padded/truncated to 3 s before preprocessing |

The model is trained with actor-level train/test splits (actors 21–24 held out entirely) to prevent speaker identity leakage into the test set — a common pitfall in SER benchmarks.

### Backend (FastAPI + Python)

- **`/predict`** endpoint accepts raw browser audio (WebM/OGG), converts to WAV via `pydub` + `ffmpeg`, runs the exact same preprocessing as training (librosa mel spec → `F.interpolate` bilinear resize → ÷80 normalization), and returns per-class probabilities.
- Model loaded once at startup and cached as a process singleton — no cold-path overhead on subsequent requests.
- Runs CPU-only PyTorch (`torch==2.3.0+cpu`) to keep the Docker image under 500 MB, deployable on Render's free tier.

### Frontend (React + TypeScript + Vite)

- Three-state UI machine: **idle → recording → result** with `AnimatePresence` transitions.
- **Real-time waveform visualizer** — reads `AnalyserNode.getByteTimeDomainData()` at 60 fps via `requestAnimationFrame` and renders a gradient-stroked Canvas waveform.
- **Animated result view** — emotion label springs in via Framer Motion, then probability bars stagger-animate from left to right.
- **Animated background** — three large radial-gradient orbs drift continuously using Framer Motion keyframe loops, giving depth without competing with the content.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v3, Framer Motion v11 |
| Backend | Python 3.11, FastAPI, uvicorn, pydub, librosa, PyTorch (CPU) |
| ML | PyTorch, librosa, RAVDESS dataset |
| Deployment | Vercel (frontend), Render Docker (backend) |

---

## Project Structure

```
voiceSense/
├── model/
│   └── emotion_model.pkl       # Trained CNN weights (33 MB)
├── backend/
│   ├── main.py                 # FastAPI app — /predict + /health
│   ├── inference.py            # EmotionCNN architecture, preprocessing, prediction
│   ├── requirements.txt
│   └── Dockerfile              # python:3.11-slim + ffmpeg; CPU-only torch
└── frontend/
    ├── src/
    │   ├── App.tsx             # Root component + state machine
    │   ├── api/predict.ts      # Axios client for /predict
    │   ├── hooks/
    │   │   └── useAudioRecorder.ts   # MediaRecorder + Web Audio AnalyserNode
    │   └── components/
    │       ├── ParticleBackground.tsx  # Animated gradient orbs
    │       ├── IdleView.tsx            # Mic button + pulsing rings
    │       ├── RecordingView.tsx       # Live waveform + timer
    │       ├── WaveformVisualizer.tsx  # Canvas 60fps waveform
    │       └── ResultView.tsx          # Animated emotion + probability bars
    ├── package.json
    └── vercel.json
```

---

## Running Locally

**Prerequisites:** Python 3.10+, Node.js 18+, `ffmpeg` installed on your system.

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu
pip install fastapi uvicorn[standard] python-multipart pydub librosa numpy scipy
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

The Vite dev server proxies `/api/*` → `localhost:8000` automatically — no CORS issues locally.

---

## Deployment

### Backend → Render

1. Push this repo to GitHub.
2. Create a **Render Web Service** → Environment: **Docker**.
3. Set:
   - **Dockerfile Path:** `./backend/Dockerfile`
   - **Docker Context:** `.` *(repo root — needed to include `model/`)*
4. Add environment variable: `ALLOWED_ORIGINS=https://your-app.vercel.app`
5. Deploy. First build takes ~5 min (downloading CPU torch wheel).

### Frontend → Vercel

1. Import the repo → set **Root Directory** to `frontend`.
2. Add environment variable: `VITE_API_URL=https://your-render-service.onrender.com`
3. Deploy. Subsequent deploys are ~30 s.

---

## API Reference

### `POST /predict`

Accepts multipart form data with an `audio` field (WebM, OGG, or WAV).

```bash
curl -X POST https://your-api.onrender.com/predict \
  -F "audio=@recording.webm;type=audio/webm"
```

**Response:**

```json
{
  "emotion":    "happy",
  "confidence": 74.3,
  "probabilities": {
    "happy":     74.3,
    "surprised": 12.1,
    "neutral":   5.8,
    "calm":      3.2,
    "angry":     2.1,
    "sad":       1.4,
    "fearful":   0.7,
    "disgust":   0.4
  },
  "color": "#fbbf24",
  "emoji": "😄"
}
```

### `GET /health`

```json
{ "status": "ok", "model_loaded": true }
```

---

## Model Performance

The CNN achieves **~37–44% test accuracy** on RAVDESS with actor-level holdout. High-arousal emotions (surprised, angry, happy) are classified more reliably than low-arousal ones (calm, neutral). This is consistent with the SER literature — RAVDESS is a challenging benchmark and real-world accuracy improves significantly with larger, more diverse training corpora.

---

## Background: RAVDESS Dataset

The [Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS)](https://zenodo.org/record/1188976) contains 2,880 audio files from 24 professional actors (12 male, 12 female) performing scripted speech in eight emotional styles at two intensity levels. It is one of the most widely-cited benchmarks in the Speech Emotion Recognition research community.
