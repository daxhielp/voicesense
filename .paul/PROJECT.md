# VoiceSense

## What This Is

VoiceSense is a full-stack Speech Emotion Recognition (SER) web app. Users record their voice in the browser and receive a real-time emotion prediction from a CNN trained on the RAVDESS dataset (8 emotions, 24 actors). The frontend is deployed to Vercel; the backend (FastAPI + PyTorch) is deployed to Render via Docker.

## Core Value

Users speak and get instant emotion feedback — the demo experience showcases end-to-end ML deployment skills (CNN training → FastAPI → Docker → Render/Vercel).

## Current State

| Attribute | Value |
|-----------|-------|
| Type | Application |
| Version | 1.0.0 |
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

### Planned (Next)

- [ ] Preprocessing bottleneck investigation — ffmpeg + librosa is the slow step (~2m13s on Render free tier)
- [ ] Cold-start UX improvement — loading state, retry logic, or keep-alive ping

### Out of Scope

- Emotion history / session logging — not needed for portfolio demo
- Multi-language support — English-only (RAVDESS dataset)

## Constraints

### Technical Constraints

- Render free tier: 512 MB RAM, shared CPU, 30-60s cold starts
- CPU-only torch (~200 MB Docker layer) — CUDA not available on free tier
- Browser records WebM/OGG; must convert via ffmpeg before librosa
- Preprocessing (not model inference) is the bottleneck: ~2m13s total on shared CPU

### Business Constraints

- School project — no budget for paid infrastructure tiers
- Must remain deployable on Vercel free + Render free

## Key Decisions

| Decision | Rationale | Date | Status |
|----------|-----------|------|--------|
| CPU-only torch in Docker | Render free tier has no GPU; CPU wheel is ~200MB vs ~900MB CUDA | 2026-04-13 | Active |
| __main__ shim for pickle | Model saved from Jupyter as full object; shim lets uvicorn resolve EmotionCNN | 2026-04-13 | Active |
| npx for Vercel build | npm doesn't preserve .bin execute permissions on Vercel CI | 2026-04-13 | Active |
| 180s axios timeout | Preprocessing takes ~2m13s on Render shared CPU | 2026-04-13 | Active |

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Cold start time | < 30s | ~60s | At risk |
| Inference time | < 30s | ~133s | At risk |
| Docker image size | < 50MB | ~250MB | At risk |
| Frontend build | Clean (0 errors) | Clean | On track |

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 19 + Vite 8 + TypeScript 6 | Deployed to Vercel |
| Styling | Tailwind CSS v4 + Framer Motion 12 | CSS-first config |
| API client | axios 1.15 | 180s timeout |
| Backend | FastAPI 0.135 + uvicorn 0.44 | Deployed to Render |
| ML | PyTorch 2.11 (CPU) + librosa 0.11 | ~200MB Docker layer |
| Audio conversion | pydub + ffmpeg | ffmpeg installed via apt in Dockerfile |
| Containerization | Docker (python:3.11-slim) | Context = repo root for model COPY |

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-04-13*
