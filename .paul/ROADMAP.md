# Roadmap: VoiceSense

## Overview

VoiceSense v1.0 is shipped. The roadmap now focuses on performance and infrastructure: cutting inference time, reducing Docker image size, and improving the cold-start user experience. All phases target Render free-tier bottlenecks.

## Current Milestone

**v1.1 Performance & Infrastructure**
Status: Complete
Phases: 3 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | ONNX Conversion | 1 | Complete | 2026-04-13 |
| 2 | Preprocessing Optimization | 2 | Complete | 2026-04-13 |
| 3 | Cold-Start UX | 1 | Complete | 2026-04-13 |

## Phase Details

### Phase 1: ONNX Conversion

**Goal:** Export EmotionCNN to ONNX and replace torch inference with onnxruntime — shrinks Docker image ~200MB → ~15MB and cuts cold-start load time.
**Depends on:** Nothing (model is already trained)
**Research:** Likely (ONNX export, onnxruntime mel spec replacement)
**Research topics:** torch.onnx.export opset compatibility, onnxruntime session options, numpy-only mel spec to replace librosa

**Scope:**
- Export model to ONNX (one-time script run locally)
- Replace torch in inference.py with onnxruntime session
- Update requirements.txt and Dockerfile (remove torch, add onnxruntime)
- Verify prediction parity with original model

**Plans:**
- [x] 01-01: Export EmotionCNN to ONNX + rewrite inference pipeline (combined research + impl)

### Phase 2: Preprocessing Optimization

**Goal:** Reduce the ~2m13s inference time — the bottleneck is ffmpeg + librosa, not the model forward pass.
**Depends on:** Phase 1 (measure onnxruntime baseline before optimizing preprocessing)
**Research:** Likely (ffmpeg alternatives, librosa vs numpy mel spec, audio decoding speed)

**Scope:**
- Profile which step takes longest (ffmpeg convert vs librosa load vs mel spec computation)
- Evaluate soundfile or scipy.io.wavfile as faster WAV decoder
- Evaluate numpy-only mel spec vs librosa
- Implement fastest viable pipeline

**Plans:**
- [x] 02-01: Profile preprocessing — identified librosa.load() resampling as 94.5% bottleneck
- [x] 02-02: Replace with soundfile + resample_poly — step 2: 28,000ms → 3.5ms, total: 24x faster

### Phase 3: Cold-Start UX

**Goal:** Make the 30-60s Render cold start invisible (or at least acceptable) to users.
**Depends on:** Phase 1 (smaller image means faster cold start baseline)
**Research:** Unlikely (internal frontend patterns + standard keep-alive technique)

**Scope:**
- Keep-alive ping on app load (GET /health every 4 min to prevent Render sleep)
- Improved loading state: "warming up model..." message during cold start
- Retry logic for timeout errors with user-visible feedback

**Plans:**
- [x] 03-01: Implement keep-alive + improved cold-start UX

---
*Roadmap created: 2026-04-13*
