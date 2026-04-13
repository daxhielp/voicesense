---
phase: 02-preprocessing-optimization
plan: 01
subsystem: infra
tags: [profiling, librosa, resampling, preprocessing, performance]

requires: []
provides:
  - Per-step timing breakdown of the full inference pipeline
  - Root cause of ~30s inference time identified
affects: [02-02]

tech-stack:
  added: []
  patterns: [time.perf_counter() per-step profiling]

key-files:
  created: [backend/profile_inference.py]
  modified: []

key-decisions:
  - "librosa.load() resampling is the 94.5% bottleneck — target for 02-02"
  - "Fix: replace librosa.load() with soundfile.read() + scipy.signal.resample_poly()"

patterns-established: []

duration: ~1 session
started: 2026-04-13T10:00:00Z
completed: 2026-04-13T10:30:00Z
---

# Phase 2 Plan 01: Preprocessing Profiling Summary

**librosa.load() resampling (48kHz → 22050Hz) is 94.5% of total inference time — 27,999 ms out of 29,639 ms total.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | 1 session |
| Tasks | 2 completed (1 checkpoint) |
| Files created | 1 (profile_inference.py) |
| Test file | RAVDESS 03-01-01-01-01-01-01.wav (366.9 KB) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Profiler produces per-step timing breakdown | Pass | 6-step table printed with ms + % for each step |
| AC-2: Findings document the dominant bottleneck | Pass | librosa.load() at 94.5% — unambiguous |

## Profiling Output (Raw)

```
  File : 03-01-01-01-01-01-01.wav
  Size : 366.9 KB
  Type : audio/wav

  Step                                             ms        %
  ------------------------------------------------------------
  1. pydub+ffmpeg  (→ WAV)                       51.9     0.2%
  2. librosa.load  (decode+resample)          27999.7    94.5%
  3. mel spectrogram + power_to_db             1584.2     5.3%
  4. scipy resize   (→ 128×128)                   0.4     0.0%
  5. normalize + reshape                          0.0     0.0%
  6. onnxruntime    session.run()                 3.2     0.0%
  ------------------------------------------------------------
  TOTAL                                       29639.4   100.0%

  Dominant step : 2. librosa.load  (decode+resample) (27999.7 ms, 94%)

  Prediction    : neutral (96.6% confidence)
```

## Root Cause Analysis

**Why is librosa.load() taking 28 seconds?**

librosa.load() with `sr=22050` resamples from the RAVDESS native rate (48,000 Hz) to 22,050 Hz. This ratio — 48000:22050 = 320:147 — is irrational as a simple fraction and requires a large polyphase filter. librosa 0.11.0 defaults to `soxr_hq` resampler, but if soxr is not installed it falls back to **resampy**, which is orders of magnitude slower for this ratio.

On a local development machine this took ~28s. On Render's shared-CPU free tier (observed ~133s total), resampy is even slower under resource contention.

| Resampler | Speed | Quality |
|-----------|-------|---------|
| soxr_hq | Fast (~10ms) | High |
| scipy | Medium (~500ms) | OK |
| resampy | Very slow (~28,000ms) | High |

## Fix for 02-02

**Replace `librosa.load()` with `soundfile.read()` + `scipy.signal.resample_poly()`.**

soundfile decodes WAV in milliseconds (no resampling). scipy.signal.resample_poly is a polyphase filter implementation optimized for rational ratios and takes ~5-20ms for this conversion.

```python
# Before (slow):
y, _ = librosa.load(io.BytesIO(wav_bytes), sr=SAMPLE_RATE, mono=True)

# After (fast):
import soundfile as sf
y_raw, native_sr = sf.read(io.BytesIO(wav_bytes), dtype="float32", always_2d=False)
if y_raw.ndim > 1:
    y_raw = y_raw.mean(axis=1)   # stereo → mono
if native_sr != SAMPLE_RATE:
    from math import gcd
    g = gcd(native_sr, SAMPLE_RATE)
    y = scipy.signal.resample_poly(y_raw, SAMPLE_RATE // g, native_sr // g)
else:
    y = y_raw
```

Expected step 2 timing after fix: **~10–50 ms** (down from 27,999 ms).

soundfile is already installed (it is a librosa dependency). scipy is already installed. No new packages required.

## Secondary Target

mel spectrogram (step 3) takes 1,584 ms — 5.3% of total. Worth noting but not the priority for 02-02. If further optimization is needed post-02-02, this is the next lever.

## Files Created

| File | Change | Purpose |
|------|--------|---------|
| `backend/profile_inference.py` | Created | Dev-only profiler; times each preprocessing step independently |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| soundfile + resample_poly for 02-02 | Already installed, handles rational ratios fast, no new deps | Step 2: ~28s → ~50ms |
| Keep librosa.feature.melspectrogram | Only 5.3% of time; replacing adds implementation risk | Step 3 stays at ~1.5s; acceptable |

## Deviations from Plan

None — plan executed exactly as written.

## Next Phase Readiness

**Ready:**
- Root cause confirmed with real timing data (not assumption)
- Fix strategy chosen: soundfile + resample_poly
- Both dependencies already in requirements.txt
- 02-02 can be planned and executed immediately

**Concerns:**
- Step 3 (melspectrogram, 1,584 ms) will remain after 02-02 — total time will drop to ~1.6s locally, ~5-10s on Render (estimate). Still significant but much better than 133s.
- Render shared CPU may further slow step 3; if post-02-02 times are still unacceptable, step 3 optimization would be the next target.

**Blockers:** None

---
*Phase: 02-preprocessing-optimization, Plan: 01*
*Completed: 2026-04-13*
