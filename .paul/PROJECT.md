# VoiceSense

## What This Is

VoiceSense is a full-stack Speech Emotion Recognition (SER) web app. Users record their voice in the browser and receive a real-time emotion prediction from a CNN trained on the RAVDESS dataset (8 emotions, 24 actors). The frontend is deployed to Vercel; the backend (FastAPI + onnxruntime) is deployed to Render via Docker.

## Core Value

Users speak and get instant emotion feedback — the demo experience showcases end-to-end ML deployment skills (CNN training → FastAPI → Docker → Render/Vercel).

## Current State

| Attribute | Value |
|-----------|-------|
| Type | Application |
| Version | 1.1.0 |
| Status | Production |
| Last Updated | 2026-04-13 |

**Production URLs:**
- Frontend (Vercel): set via VITE_API_URL env var
- Backend (Render): set via ALLOWED_ORIGINS env var

## Requirements

### Core Features

- [x] Browser voice recording (MediaRecorder API + Web Audio AnalyserNode)
- [x] Real-time waveform visualization (Canvas 60fps)
- [x] Emotion prediction API (FastAPI POST /predict)
- [x] Animated result display (Framer Motion spring + staggered probability bars)
- [x] Full Docker deployment (Render backend + Vercel frontend)

### Validated (Shipped)

- [x] EmotionCNN inference pipeline — v1.0.0
- [x] Audio preprocessing (ffmpeg → librosa mel spec → F.interpolate → ÷80) — v1.0.0
- [x] __main__ shim fix for pickle deserialization — v1.0.0
- [x] Vite proxy for local dev — v1.0.0
- [x] CORS via ALLOWED_ORIGINS env var — v1.0.0

### Active (In Progress)

None.

### Validated (Shipped) — continued

- [x] ONNX model export + onnxruntime inference — v1.1 (torch removed from Docker, ~150 MB saved)
- [x] Preprocessing optimization (soundfile + resample_poly) — v1.1 (librosa.load: 28s → 3.5ms; total: 24x faster)
- [x] Cold-start UX — v1.1 (keep-alive ping, dedicated ErrorView + retry, time-aware processing messages)

### Planned (Next)

None — v1.1 milestone complete.

### Out of Scope

- Emotion history / session logging — not needed for portfolio demo
- Multi-language support — English-only (RAVDESS dataset)

## Constraints

### Technical Constraints

- Render free tier: 512 MB RAM, shared CPU, 30-60s cold starts
- onnxruntime (CPU) — torch removed from Docker; CUDA not available on free tier
- Browser records WebM/OGG; must convert via ffmpeg before soundfile
- Mel spectrogram step still ~1.2s locally (librosa); may be ~5-10s on Render shared CPU

### Business Constraints

- School project — no budget for paid infrastructure tiers
- Must remain deployable on Vercel free + Render free

## Key Decisions

| Decision | Rationale | Date | Status |
|----------|-----------|------|--------|
| CPU-only torch in Docker | Render free tier has no GPU; CPU wheel is ~200MB vs ~900MB CUDA | 2026-04-13 | Superseded by ONNX |
| __main__ shim for pickle | Model saved from Jupyter as full object; shim lets uvicorn resolve EmotionCNN | 2026-04-13 | Superseded by ONNX |
| npx for Vercel build | npm doesn't preserve .bin execute permissions on Vercel CI | 2026-04-13 | Active |
| 180s axios timeout | Render cold start + mel spec can take up to ~70s worst case | 2026-04-13 | Active |
| ONNX two-file format | PyTorch 2.11 dynamo exporter writes .onnx graph + .onnx.data weights; both must be COPYed in Dockerfile | 2026-04-13 | Active |
| soundfile + resample_poly | librosa.load() resampling was 94.5% of total preprocessing time; soundfile read + scipy resample is 8000x faster | 2026-04-13 | Active |
| Keep librosa for mel spec | Matches training exactly; replacing is high-risk for prediction accuracy | 2026-04-13 | Active |
| fetch (not axios) for keep-alive ping | No response handling needed; failures silently swallowed | 2026-04-13 | Active |
| error AppState distinct from idle | Forces user to read error before re-recording; avoids confusion on cold-start retry | 2026-04-13 | Active |

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Cold start time | < 30s | ~30-60s (keep-alive mitigates) | Improved |
| Inference time | < 30s | ~1.25s locally; ~5-15s Render | On track |
| Docker image size | < 50MB | ~100MB (torch removed, onnxruntime added) | Improved |
| Frontend build | Clean (0 errors) | Clean | On track |

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 19 + Vite 8 + TypeScript 6 | Deployed to Vercel |
| Styling | Tailwind CSS v4 + Framer Motion 12 | CSS-first config |
| API client | axios 1.15 | 180s timeout |
| Backend | FastAPI 0.135 + uvicorn 0.44 | Deployed to Render |
| ML | onnxruntime 1.21 + librosa 0.11 | torch removed; ONNX model ~33MB |
| Audio conversion | pydub + ffmpeg | ffmpeg installed via apt in Dockerfile |
| Containerization | Docker (python:3.11-slim) | Context = repo root for model COPY |

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-04-13 after Phase 3 (v1.1 milestone complete)*
