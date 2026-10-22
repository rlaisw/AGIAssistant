# Implementation Plan: PDF Download of Chat Conversations

**Branch**: `013-pdf-download-chat` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-pdf-download-chat/spec.md`
(user emphasis: original plan + explicit test cases and error handling)

## Summary

One-click PDF export of the current chat conversation, entirely client-side:
transform the live messages into an export model (visible turns + citations
as links, reasoning excluded), render that offscreen through the app's
existing markdown pipeline in a light print palette, rasterize with
html2canvas-pro, and assemble A4 pages with jsPDF — delivered as a native
browser download with a question-derived file name. Tests-first per the
user's requirement and Constitution II: pure-logic modules (slugify, export
state machine, transform, image-wait) are written with vitest before
implementation, and a complete error taxonomy (empty conversation, render
failure, blocked download, image-degrade-to-link) is designed in
[data-model.md](data-model.md) and [contracts/pdf-export.md](contracts/pdf-export.md).

## Technical Context

**Language/Version**: TypeScript 5.x, React 19.3, Next.js 16.4 (ai-chat-landing)

**Primary Dependencies**: existing — react-markdown 10 + remark-gfm (markdown
pipeline reused per FR-003), lucide-react (icon). New (lazy-loaded, justified
in [research.md](research.md) R1/R2): `jspdf`, `html2canvas-pro`.

**Storage**: none — export is built in memory from the live conversation; the
only output is the downloaded blob (FR-004).

**Testing**: vitest (`pnpm test`, node environment) — pure-logic unit tests +
orchestrator test with the render/rasterize/save seams injected as stubs
(deterministic, no network; mocks at trust boundaries).

**Target Platform**: browser (Chromium-class; the stack's Chat UI at
localhost:3000).

**Project Type**: web-app frontend feature (Chat UI) + one additive sidecar
header.

**Performance Goals**: 20-turn export < 10 s (SC-001, hardware-relative);
lazy `import()` keeps ~500 KB off the initial bundle.

**Constraints**: no server persistence of exports (FR-004); no new runtime
service (SC-004); light print palette always (FR-005).

**Scale/Scope**: single conversation on screen; dozens of turns typical.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Evidence |
|-----------|---------|----------|
| I. Contract preservation (client contracts frozen) | PASS | No MCP tool schema or `ask` field changes; sidecar change is one additive CORS header on media routes (contracts §3); Chat UI is additive UI |
| II. Tests-first | PASS | Test matrix defined in [data-model.md](data-model.md) before implementation; vitest green gates every task; rasterizer stubbed, deterministic |
| III. Minimal dependencies | PASS (justified) | Two new frontend deps as last resort (no stdlib/platform PDF rasterizer exists); both lazy-loaded; reuses existing markdown component instead of a parallel pipeline |
| IV. Honest answers | PASS | Error taxonomy (R6) surfaces every failure visibly; image unavailability degrades to a visible labeled link, never silent loss |
| V. Spec-driven replacement | PASS | Supersedes nothing; purely additive feature |

**Post-Phase-1 re-check**: design adds no services, no schemas, no storage;
the rasterizer seam keeps the parallel-pipeline risk at zero. Gates remain
PASS.

## Project Structure

### Documentation (this feature)

```text
specs/013-pdf-download-chat/
├── plan.md              # This file
├── research.md          # Phase 0 output (6 decisions)
├── data-model.md        # Phase 1 output (ExportModel, state machine, errors, test matrix)
├── quickstart.md        # Phase 1 output (S1–S6 validation guide)
├── contracts/
│   └── pdf-export.md    # Module interface + sidecar CORS header contract
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
ai-chat-landing/
├── lib/
│   └── pdf-export/
│       ├── types.ts          # ExportModel, ExportTurn, ImageRef, ExportError
│       ├── slugify.ts        # FR-006 filename (pure)
│       ├── transform.ts      # messages → ExportModel (pure; FR-002/009/011)
│       ├── state.ts          # ExportState machine + error taxonomy (pure; FR-007/008)
│       ├── image-wait.ts     # bounded CORS image loader → embed|link (FR-012)
│       ├── render.tsx         # offscreen light-palette container + React markdown renderer
│       ├── pagination.ts      # A4 page-slice math (pure)
│       ├── export.ts         # orchestrator: offscreen render → rasterize → jsPDF (lazy deps)
│       └── *.test.ts         # vitest per data-model test matrix
├── components/
│   └── pdf-export-button.tsx # header icon; renders from ExportState
└── app/
    └── page.tsx              # wires the button into the chat header (minimal)

src/agentic_rag_mcp/
└── dify/docker/mcp-server/server.py   # additive CORS header on media routes
```

**Structure Decision**: single-module layout inside the existing
`ai-chat-landing/lib/`, mirroring `lib/deck-url.ts` conventions; pure modules
separated from the DOM orchestrator so vitest needs no rasterizer or network.
Sidecar change is a one-line header addition on existing routes — no new
files there.

## Complexity Tracking

> No Constitution violations to justify — table intentionally empty.
