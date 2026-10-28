# Implementation Plan: Apply Selected LLM to the Chatflow (Patch-on-Select)

**Branch**: `026-llm-patch-select` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/026-llm-patch-select/spec.md`

## Summary

Selecting a cloud LLM in the "AI LLM" menu reconfigures the published
chatflow itself: a server-side cycle exports the AGI Assistant app to the
repo artifact, patches the three main LLM nodes (intent_router,
agentic_strategy, ppt_master) to the selected model, removes the routing-era
extra branches (FR-005), overwrites the app draft, and republishes. The
selection becomes the global app default; sends are blocked while the cycle
applies; the badge keeps per-message provenance. The cycle runs through the
proven spec-011 deploy CLI (console API equivalents of the user's prescribed
export → patch → overwrite-import → publish steps); the Chat UI gets an
apply endpoint, a current-model endpoint, and the applying state.

## Technical Context

**Language/Version**: TypeScript on Next.js 16 (Chat UI); Python 3.12
(deploy CLI); Dify 1.18.0 chatflow DSL (YAML).

**Primary Dependencies**: existing only — spec-011 deploy CLI
(`src/agentic_rag_mcp/deploy/`, console session + update/publish proven);
the exported artifact `dify/AGIAssistant/AGI_Assistant.yml`; reference
script `dify/difyctl-export-reimport-publish.sh` (documented equivalent).

**Storage**: the published app IS the store (global selection); the repo
artifact mirrors it (FR-007); browser localStorage keeps only the local
selection and badge maps (spec 025 provenance).

**Testing**: vitest units + `pytest tests/unit/test_deploy_model_apply.py`
(yml patch fn); typecheck/lint; deployment battery (default config);
live throwaway checks per quickstart.

**Target Platform**: Linux host; Chat UI on port 3000 (dev server — never
`pnpm build` while it runs).

**Project Type**: web app (Chat UI) + chatflow configuration.

**Performance Goals**: cycle completes ≤90 s (SC-001); sends blocked during
it (FR-003); failure leaves the previous published config serving (FR-004).

**Constraints**: additive-only console changes (export + draft overwrite +
publish — the published app is untouched until the publish step); console
credentials server-side only; no new npm/pip dependencies; local model
keeps its spec-025 routed branch (instant fallback, no cycle).

**Scale/Scope**: 3 patched nodes + one idempotent cleanup; 4 cloud models
catalog + local; single in-flight cycle.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Contract Preservation | PASS | `cloud_model` input and extra branches are removed cleanly (spec-driven replacement, P-V); remaining inputs (`ai_model`) unchanged; battery byte-identical on default config. |
| II. Tests-First | PASS | Python patch-function tests (model set + cleanup idempotency) and badge fallback-variant tests precede implementation (tasks.md). |
| III. Minimal Dependencies | PASS | Zero new deps — deploy CLI console session and difyctl already present; the artifact is the only new "state". |
| IV. Honest Answers | PASS | Applying indicator, blocked sends, failure keeps previous config, per-reply badge provenance, draft-hash abort on concurrent edits. |
| V. Spec-Driven Replacement | PASS | The routing-era 9-node expansion and `cloud_model` input are removed, not kept as dead paths. |

**Post-Phase-1 re-check**: design adds no new services or dependencies;
the artifact contract is additive. Still PASS.

## Project Structure

### Documentation (this feature)

```text
specs/026-llm-patch-select/
├── plan.md              # This file
├── research.md          # Phase 0 output — mechanism decisions
├── data-model.md        # Phase 1 output — selection/cycle entities
├── quickstart.md        # Phase 1 output — runnable validation scenarios
├── contracts/
│   └── apply-model.md   # Phase 1 output — apply/current endpoints + cycle contract
└── tasks.md             # Phase 2 (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/agentic_rag_mcp/deploy/
├── model_apply.py              # NEW — export → patch → overwrite → publish cycle
├── dify_console.py             # EXTEND — export_app() (yaml export endpoint)
├── __main__.py                 # EXTEND — apply-model command
tests/unit/test_deploy_model_apply.py  # NEW — patch-fn unit tests

ai-chat-landing/
├── app/api/models/current/route.ts   # NEW — configured model from artifact
├── app/api/models/apply/route.ts     # NEW — run the cycle server-side
├── app/api/chat/route.ts             # SIMPLIFY — drop cloud_model passthrough
├── app/page.tsx                      # applying state + current-model fetch + fallback
├── lib/models/badge.ts               # EXTEND — fallback-variant badge values
└── lib/models/*.test.ts              # EXTEND — updated expectations

dify/AGIAssistant/AGI_Assistant.yml   # cycle-maintained artifact (FR-007)
```

**Structure Decision**: no new top-level layers — the cycle lives in the
deploy CLI (ops), endpoints in the Chat UI API surface (server-side), UI
state in `app/page.tsx` + `lib/models/` (mirroring spec 025 placement).

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
