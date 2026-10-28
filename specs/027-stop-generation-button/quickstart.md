# Quickstart: Validate the Stop Generation Button (Phase 1)

A validation guide — implementation details live in `tasks.md` (Phase 2). Contracts: [stop-generation.md](contracts/stop-generation.md) · state model: [data-model.md](data-model.md).

## Prerequisites

1. Dify stack up (`docker ps` — 16 containers incl. nginx/api) and the sidecar `agentic-rag` healthy; a model is serving (cloud selection works out of the box).
2. Chat UI dev server: `pnpm dev` inside `ai-chat-landing/` (port 3000) with `.env.local` (real mode). Kill `DIFY_API_KEY` to test demo mode.
3. Chrome with `--remote-debugging-port=9240` for the CDP script (same as `wide-layout.mjs`).
4. From repo root: `bash .specify/scripts/bash/check-prerequisites.sh` sanity — feature dir resolves.

## Test cases

### A. Unit — pure state machine (failing-first, before implementation)

`cd ai-chat-landing && pnpm test` — `lib/stop/state.test.ts` must cover:

| # | Case | Asserts |
|---|------|---------|
| A1 | morph visibility | `composerMode` = "stop" only while viewing the generating conversation; "send" otherwise, incl. demo/idle |
| A2 | double stop | second activation → `"noop"`; state unchanged, no duplicate finalize |
| A3 | completion race | `done` arrives after stop latch → outcome resolves to stopped *or* complete, never stuck-streaming |
| A4 | thinking-phase stop | no answer text → `remove-empty-turn` (no assistant bubble, no caption) |
| A5 | mid-stream stop | partial text → `finalize-stopped`; text and reasoning survive, `streaming:false`, `stopped:true` |
| A6 | session-only caption | caption derives from in-memory `stopped` flag; no persistence anywhere |
| A7 | backend-call decision | `shouldCallBackendStop` false for demo mode and missing taskId; true otherwise |

Also green: `pnpm typecheck && pnpm lint`.

### B. Live UI — CDP acceptance (`node scripts/stop-button-check.mjs`)

| # | Scenario | Expected (evidence for SC-001/002/004) |
|---|----------|----------------------------------------|
| B1 | ask a long question; observe composer during generation | button shows Stop; typing stays enabled, sending disabled |
| B2 | click Stop mid-stream, measure | composer back to ready **< 1 s**; partial text kept + "Stopped" caption; no source badges after stop |
| B3 | immediately send a follow-up | answered normally (sources/citations intact) |
| B4 | stop during thinking (before text) | no empty assistant bubble; conversation ready |
| B5 | double-click Stop | single stop, no errors |
| B6 | switch conversation mid-generation, switch back | generation continued; Stop visible only in the owning view; returned conversation kept updating |
| B7 | demo mode (no key) | Stop works on the canned stream: caption + ready composer |

### C. Backend halt — battery scenario (SC-005, FR-006)

Ask a long question → stop → **wait a fixed interval (≥ 5 s)** → re-fetch the conversation messages via the history API → assert the stopped answer's text **has not grown** (no further content generated). A growth = acceptance defect.

### D. Error-handling matrix (per spec input "add error handling")

| # | Injected failure | Expected behavior | Result (2026-10-28, `scripts/stop-button-check.mjs`) |
|---|------------------|-------------------|---|
| D1 | stop route unreachable (devtools: block/abort the `/api/chat/stop` request) | UI still stops cleanly < 1 s (client abort path); console warn recorded; partial text + caption intact | ✓ PASS — client stopped in 19–22 ms with caption under an injected 502 |
| D2 | backend stop for an unknown task (completion race) | treated as success — turn finalizes consistently | ✓ PASS — unknown UUID → 200 `ok` (Dify 200s unknown stops; the route's `no-task` mapping stays defensive) |
| D3 | stop route 502 (upstream failed) | same as D1: client stops cleanly; battery counts persistent 502s as defects | ✓ PASS (same injection as D1) |
| D4 | watchdog timeout mid-generation (no events for 120 s) | existing error UX unchanged — regression check only | NOT RUN (needs a 120 s silent generation) — the watchdog path is untouched by the change; run manually by pointing the proxy at a stalling upstream |
| D5 | reload after a stopped turn | partial text intact; **no** "Stopped" caption (session-only); conversation resumes and answers follow-ups | ✓ PASS — reloaded turn keeps partial text (333 chars), caption gone |
| D6 | stop right as `done` arrives | race resolves to complete or stopped, never stuck streaming (A3 live form) | ✓ by wiring guard + unit A3 (live race not deterministically reproducible; the stop-latch precedence in the catch makes both orders safe) |

Additional live evidence: `stop-generation` battery scenario passed — `stop=200 halted backend (stored=392 vs delivered=392, delta=0)` — and B7 (demo mode) was not run (needs a key-less dev server; the script documents it).

## Expected end state

All of A green in vitest; B script exits 0; C battery scenario passes; D matrix shows clean client stops under every failure injection. The existing suites stay green (regression scope: history, delete, PDF export, model dropdown).

## Convergence results (Phase 7, 2026-10-28)

- **T024 / B7 (demo-mode stop): PASS** — via 503-injected `/api/chat` (the same fallback path a key-less server drives): the canned stream was caught mid-flight (14 chars) and stopped in 31 ms with the caption and partial text kept. Prerequisite learned the hard way: the demo fallback requires the local model UP (`localModelFailed()` must be false) — Ollama had died and was restarted first.
- **T025 / D4 (watchdog regression): verified by analysis, not live injection** — three injection strategies are structurally impossible in a browser: a synthetic `Response(ReadableStream)` ignores the AbortController (un-abortable by platform design); a real cross-origin dribble server stalls at the CORS preflight before the reader/watchdog ever arms; a real Dify stream re-arms the watchdog with every ping event (by design). The regression claim rests on: the `timedOut` guard precedes both new lines in the catch, unit tests A2/A3 pin the latch semantics, and the abort-on-real-fetch path is proven live by every mid-stream stop (B2/B5/D1).
- **T026 / US3-AC3 (artifact survives a mid-answer stop): PASS** — an infographic-generation answer was stopped right after its `http://localhost:28080/infographics/<id>/` link appeared: caption shown, the link anchor survived the stopped partial text, and the URL served HTTP 200. Honest substitution: the deck pipeline was not usable for this check because the PPT-Master node is currently failing upstream with `object of type 'NoneType' has no len()` (sidecar logs clean — a separate Dify-side issue to investigate, not a spec-027 regression).
