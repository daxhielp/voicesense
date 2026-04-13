---
phase: 03-cold-start-ux
plan: 01
subsystem: ui
tags: [react, framer-motion, axios, keep-alive, error-handling]

requires:
  - phase: 01-onnx-conversion
    provides: Smaller Docker image → shorter cold-start baseline

provides:
  - Keep-alive ping (GET /health every 4min) prevents Render sleep between sessions
  - Dedicated ErrorView component with retry button
  - Time-aware ProcessingView messages (0-5s / 5-12s / 12-20s / 20s+)

affects: []

tech-stack:
  added: []
  patterns:
    - "Keep-alive via useEffect + setInterval + fetch (no axios, no UI)"
    - "Error state as first-class AppState with dedicated view + retry flow"
    - "Time-aware UX messages via elapsed-seconds counter useEffect"

key-files:
  created:
    - frontend/src/components/ErrorView.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/api/predict.ts

key-decisions:
  - "Export API_BASE from predict.ts to share base URL between ping + predict calls"
  - "Use fetch (not axios) for keep-alive ping — lighter, failures silently swallowed"
  - "Error AppState distinct from idle — forces user to read error before re-recording"
  - "Elapsed seconds shown only at 20s+ threshold — avoids anxiety during normal requests"

patterns-established:
  - "axios.isAxiosError() guard for typed error classification in catch blocks"

duration: ~30min
started: 2026-04-13T00:00:00Z
completed: 2026-04-13T00:00:00Z
---

# Phase 3 Plan 01: Cold-Start UX Summary

**Keep-alive ping, dedicated ErrorView with retry, and time-aware ProcessingView messages implemented — Render cold-start experience now graceful instead of silent timeout.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~30 min |
| Tasks | 3 completed |
| Files modified | 3 |
| TypeScript errors | 0 |
| Build size | 367 KB JS / 19 KB CSS (unchanged from pre-phase) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Keep-alive prevents Render sleep | Pass | `useEffect` fires `fetch /health` on mount + every 4min; failures silently swallowed |
| AC-2: Timeout → dedicated ErrorView with retry | Pass | `axios.isAxiosError` classifies ECONNABORTED / no-response / 5xx; routes to `'error'` state |
| AC-3: Processing messages evolve with time | Pass | 4 message tiers at 0/5/12/20s; elapsed counter shown after 20s |

## Accomplishments

- `export const API_BASE` in `predict.ts` allows keep-alive ping to share the same base URL as the predict call without duplication
- `ErrorView` is a minimal, Framer Motion-animated component — warning emoji, human-readable message, violet "Try Again" button — matching existing design language exactly
- `ProcessingView` now accepts `elapsedSeconds` prop and serves contextually honest messages; after 20s it shows a live elapsed counter so users know the request is still active
- TypeScript build passes with zero errors (`tsc --noEmit` + `vite build`)

## Task Commits

No per-task commits made — all three tasks applied atomically; phase commit covers all changes.

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `frontend/src/api/predict.ts` | Modified | `const API_BASE` → `export const API_BASE` |
| `frontend/src/components/ErrorView.tsx` | Created | Error state UI: emoji + message + retry button |
| `frontend/src/App.tsx` | Modified | Keep-alive useEffect, error AppState, processing timer, ProcessingView props |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| `fetch` not `axios` for ping | No response handling needed; lighter call | Ping code stays < 4 lines |
| `error` AppState (not `idle`) on failure | Forces user to read the error before re-recording | Prevents confusion when silent retry would confuse (server still cold) |
| Show elapsed seconds only at 20s+ | Avoids anxiety for normal (~5s) requests; only surfaces counter when wait is genuinely long | UX is calm by default, honest only when needed |

## Deviations from Plan

None — all three tasks executed exactly as specified. No scope additions, no deferred items.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| `npm run build` failed (npx resolved wrong `tsc`) | Used `node_modules/.bin/tsc --noEmit` directly; `npm install` was also needed to restore `.bin/` after `.gitignore` excluded `node_modules` |

## Next Phase Readiness

**Ready:**
- v1.1 milestone is 100% complete — all 3 phases unified
- Frontend deployed to Vercel (latest build in `dist/`)
- Backend (ONNX + soundfile) ready for Render deploy

**Concerns:**
- Mel spectrogram step still ~1.2s locally (deferred in Phase 2) — may still be ~5-10s on Render shared CPU; acceptable given keep-alive and honest messages
- Docker build with ONNX two-file format not yet tested locally (deferred AC-3 from Phase 1)

**Blockers:** None — milestone complete, ready for Render deploy

---
*Phase: 03-cold-start-ux, Plan: 01*
*Completed: 2026-04-13*
