---
phase: 02-preprocessing-optimization
plan: 02
subsystem: infra
tags: [soundfile, resample_poly, librosa, preprocessing, performance]

requires:
  - phase: 02-01
    provides: profiling data confirming librosa.load() as 94.5% bottleneck

provides:
  - soundfile + resample_poly replaces librosa.load() in preprocess_audio()
  - Total inference time reduced from ~29,639 ms to ~1,250 ms locally (24x)
  - Step 2 reduced from 27,999 ms to 3.5 ms (8,000x)

affects: [03-cold-start-ux]

tech-stack:
  added: []
  removed: [librosa.load usage]
  patterns: [soundfile.read() + scipy.signal.resample_poly() for audio decode+resample]

key-files:
  modified: [backend/inference.py, backend/profile_inference.py]

key-decisions:
  - "soundfile + resample_poly confirmed correct — prediction matches within ±0.2% confidence"
  - "mel spectrogram is now the new dominant step at 1,232 ms (98.5% of total)"

patterns-established:
  - "Audio decode: sf.read(BytesIO, dtype=float32) → mono via mean(axis=1) if stereo"
  - "Resample: gcd-reduced resample_poly(y, target//g, native//g) for rational ratio"

duration: ~1 session
started: 2026-04-13T10:30:00Z
completed: 2026-04-13T11:00:00Z
---

# Phase 2 Plan 02: Preprocessing Optimization Summary

**Replaced librosa.load() with soundfile + resample_poly — inference time dropped 24x (29,639 ms → 1,250 ms), with step 2 improving 8,000x (27,999 ms → 3.5 ms).**

## Performance

| Metric | Value |
|--------|-------|
| Duration | 1 session |
| Tasks | 2 completed (1 checkpoint) |
| Files modified | 2 (inference.py, profile_inference.py) |
| New dependencies | None |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: preprocess_audio() uses soundfile + resample_poly | Pass | librosa.load removed; sf.read + resample_poly in place |
| AC-2: Step 2 < 500 ms | Pass | 3.5 ms (target was <500 ms; actual is 143x better) |
| AC-3: Prediction output unchanged | Pass | neutral 96.8% vs 96.6% — within ±0.2%, well within ±5% tolerance |

## Before vs. After (Profiler Output)

### Before (librosa.load, cold run)
```
  2. librosa.load  (decode+resample)          27999.7 ms   94.5%
  TOTAL                                       29639.4 ms
```

### After (soundfile + resample_poly)
```
  2. soundfile+resample_poly (decode+resample)    3.5 ms    0.3%
  3. mel spectrogram + power_to_db             1232.0 ms   98.5%
  TOTAL                                        1250.1 ms
```

## Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/inference.py` | Modified | Replace librosa.load() with soundfile.read() + resample_poly() |
| `backend/profile_inference.py` | Modified | Update step 2 to reflect actual inference.py approach |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| soundfile + resample_poly (no soxr) | Both already installed; gcd-reduced poly filter handles 48k→22050 efficiently | Step 2: 27,999ms → 3.5ms with zero new deps |
| Keep librosa.feature.melspectrogram | Still matches training exactly; 1,232ms is now acceptable on local machine | New bottleneck but within acceptable range |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Scope addition | 1 | Updated profiler (necessary for accurate validation) |

### Scope Addition

**1. Updated profile_inference.py step 2**
- **Reason:** Original profiler still used librosa.load() — results would be misleading (showing warmed-up librosa, not the actual soundfile approach)
- **Fix:** Updated step 2 in profiler to match inference.py exactly
- **Impact:** Profiler now accurately reflects production code; previous librosa baseline still in git history for comparison

## New Bottleneck

mel spectrogram (step 3) is now 98.5% of total time at 1,232 ms locally. On Render's shared CPU, estimate ~5–10s total (vs. ~133s before). This is acceptable for a free-tier demo — the UX improvement from 133s → ~10s is dramatic. If further optimization is needed, step 3 would be the next target (numpy-only FFT mel spec or cached spectrogram).

## Next Phase Readiness

**Ready:**
- Inference pipeline is now fast enough for real-world use on free-tier infrastructure
- Phase 3 (Cold-Start UX) can proceed — keep-alive ping + loading state improvements

**Concerns:**
- Render shared CPU may make step 3 (melspectrogram) take 5–10s per request — still much better than 133s but warrants a "processing..." UX indicator
- mel spectrogram optimization is deferred; could be a Phase 4 if needed

**Blockers:** None

---
*Phase: 02-preprocessing-optimization, Plan: 02*
*Completed: 2026-04-13*
