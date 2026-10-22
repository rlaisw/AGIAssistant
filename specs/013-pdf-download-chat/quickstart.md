# Quickstart: Validate the PDF Download Feature

End-to-end manual validation (the runnable proof for spec scenarios); unit
coverage lives in the data-model test matrix and runs via `pnpm test`.

## Prerequisites

- Stack running: Dify + sidecar (28080) + Chat UI (`pnpm dev` in
  `ai-chat-landing/`, http://localhost:3000)
- Sidecar rebuilt after implementation (CORS headers on media routes —
  contracts §3)

## S1 — Happy path (User Story 1)

1. Ask two questions; make one answer contain a table (e.g., "summarize the
   Q3 roadmap as a table") and one a deck action bar or chart link.
2. Click the PDF icon in the chat header.
   **Expect**: busy state → browser downloads `slug-of-first-question.pdf`.
3. Open the file (browser viewer + OS viewer).
   **Expect**: title block + every turn in order; table as a grid; the deck/
   chart link as a labeled link; reasoning panel content absent; light
   palette regardless of dark mode.

## S2 — Images (FR-012)

1. Get an answer with a research `[image: …]` image or a sidecar-hosted chart
   image; export.
2. **Expect**: sidecar-hosted images embedded; an unreachable internet image
   degrades to its labeled link (no blank boxes, no user-facing error).

## S3 — File name + non-blocking (User Story 2)

1. Export a long conversation; click around while it renders.
   **Expect**: page stays interactive; icon busy; file name is the first
   question's slug (≤ 40 chars).

## S4 — Error handling (FR-001/FR-007/FR-008, edge cases)

1. **Empty conversation** → icon hidden/disabled; forcing export shows the
   "nothing to export" message, no file.
2. **Simulated render failure** (stub rasterizer to throw in dev) → visible
   error, icon returns to idle.
3. **Double-click the icon** → second trigger ignored while busy.
4. **Streaming answer in flight** → export works on completed turns + partial
   text; no duplicate turns.

## S5 — Automated checks

```bash
cd ai-chat-landing
pnpm test        # vitest: slugify, state machine, transform, image-wait, orchestrator (stubbed rasterizer)
pnpm typecheck && pnpm lint
```
**Expect**: all green; no new network dependencies in tests.

## S6 — Performance (SC-001 spot check)

Export a 20-turn conversation: target under 10 s on a typical laptop
(hardware-relative); first export may include the lazy chunk download.

**Measurement status (2026-10-21)**: an automated headless-Chrome harness
(exercising the real pipeline — 20-turn conversation, offscreen light-palette
container, html2canvas-pro rasterization, jsPDF A4 assembly) confirmed the
full pipeline completes end-to-end (rasterize → canvas → PDF → arraybuffer),
but the headless software-rasterized VM cannot produce a timing number
representative of a "typical laptop", and the rasterize stage exceeded the
harness's practical wall-clock window there. **The SC-001 number must be
recorded from an interactive browser on real hardware**:

1. Open a chat with ≥ 20 turns (or ask several questions in one session).
2. Open DevTools → Network, clear it, click the ⬇ header icon.
3. Note the wall time from click to the downloaded `.pdf` appearing.
4. Record here: *20-turn export took ___ s on (hardware description)*.
