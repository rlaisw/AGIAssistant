# Implementation Plan: PPT Completion Experience — Preview & Edit in the Browser

**Branch**: `010-ppt-preview-edit` | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-ppt-preview-edit/spec.md`

**Note**: User directive: original architecture plus explicit **test-case creation** and **error handling** as first-class deliverables.

## Summary

Extend spec 009's delivery: each export gains an immutable per-artifact **completion page** served by the sidecar (`GET /decks/<project>/<artifact>/`) — every slide previewed from a per-export snapshot of the pipeline's self-contained page renderings, a download control pointing at the unchanged direct `.pptx` URL, and the conversation-driven edit path. `ppt_export` gains one additive result field (`page_url`); the direct URL contract is frozen. The AI Chat UI renders deck links as a **deck action bar** (Download / Preview-Edit icons) via a link interceptor in the markdown renderer, with pure URL-derivation logic unit-tested and everything else covered by a contract + integration battery.

## Technical Context

**Language/Version**: Python 3.12 (sidecar bridge + routes), TypeScript/React 19 (Chat UI interceptor), HTML (static completion page).

**Primary Dependencies**: existing stack only — ppt-master's `finalize_svg.py` (self-contained per-slide renderings), Starlette routes on the sidecar wrapper, react-markdown component overrides already in `ai-chat-landing/components/markdown.tsx`. New dev-only dependency: `vitest` in `ai-chat-landing` for the URL-derivation unit tests (no new runtime services — Constitution III).

**Storage**: filesystem — per-artifact preview snapshots under `<project>/previews/<artifact-stem>/`, sibling to `exports/`.

**Testing**: pytest three-tier (sidecar) + vitest (Chat UI pure functions). Full matrix in [contracts/completion-page.md](contracts/completion-page.md), defined before implementation (Constitution II).

**Target Platform**: Linux Docker sidecar + browser (modern desktop/mobile).

**Project Type**: MCP server extension + HTTP page serving + Chat UI enhancement.

**Performance Goals**: first slide preview visible ≤ 3 s on the local network (SC-001); preview snapshot adds ≤ 10 s to export.

**Constraints**: `ppt_export` result fields `file` and `url` byte-compatible (additive `page_url` only); direct `/exports/` route unchanged; zero new runtime services; preview failure never blocks export (FR-008); local-trust unauthenticated posture.

**Scale/Scope**: single user; ≤ 5-page decks (spec 009 v1 bound).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Contract Preservation | PASS | `ppt_export` gains only the additive `page_url` field (constitution explicitly permits additive fields); `/exports/` route byte-compatible; spec 009 contract tests must stay green (verified in the matrix) |
| II. Tests-First | PASS | Contract matrix (routes, degraded states, additive-field compatibility, interceptor derivation) defined in `contracts/completion-page.md` before implementation |
| III. Minimal Dependencies | PASS | No new runtime services; previews reuse the pipeline's own renderings; only dev-only `vitest` enters the Chat UI |
| IV. Honest Answers | PASS | Degraded preview states, honest 404s, traversal rejection, no fabricated renderings (FR-005/FR-008) |
| V. Spec-Driven Replacement | N/A | Additive feature |

## Project Structure

### Documentation (this feature)

```text
specs/010-ppt-preview-edit/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── completion-page.md   # routes, additive field, interceptor contract, test matrix
└── tasks.md                 # (/speckit.tasks output — not created by /speckit.plan)
```

### Source Code (repository root)

```text
src/agentic_rag_mcp/ppt/
├── bridge.py          # export gains: preview snapshot + page_url (additive), degraded flag
├── http_exports.py     # unchanged (frozen route)
└── completion.py      # NEW: snapshot previews, render completion-page HTML, slide asset handler

dify/docker/mcp-server/server.py    # + GET /decks/<project>/<stem>/ and /decks/.../slides/<n>.svg

ai-chat-landing/
├── lib/deck-url.ts               # NEW: pure URL derivation (exports ⇄ decks) — vitest target
├── components/deck-actions.tsx   # NEW: the action bar (Download / Preview-Edit icons)
├── components/markdown.tsx      # link interceptor: recognized deck URLs → DeckActions
├── vitest.config.ts              # NEW (node env, no react renderer needed)
└── package.json                  # + vitest devDependency, "test" script

dify/ppt-master-rulebook.md       # minor: prefer the page_url in the final answer's link

tests/
├── unit/test_ppt_completion.py            # snapshot logic, degraded flag, HTML rendering
├── integration/test_ppt_completion_pipeline.py  # real exports: snapshot per artifact, re-export isolation, finalize failure
└── contract/test_ppt_completion_contract.py     # routes 200/404/400, additive field, spec-009 suite still green
```

**Structure Decision**: mirrors spec 009 — one new sidecar module (`ppt/completion.py`) plus a thin Chat UI slice; the completion page is server-rendered HTML from the sidecar (no SPA, no build step, no new service).

## Complexity Tracking

No violations to justify.
