# Implementation Plan: "AI LLM" Model Drop-Down Menu

**Branch**: `025-ai-llm-dropdown` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/025-ai-llm-dropdown/spec.md`

## Summary

Single-select "AI LLM" drop-down in the Chat UI choosing which model answers
each conversation: Cloud (DeepSeek, default) or Local (Qwen3 8B via host
Ollama). Technical approach (from research): an additive chatflow input
`inputs.ai_model` routes through a new IF/ELSE node to either the existing
cloud LLM nodes or three local-configured copies; the Chat UI gates Local
behind a host-side availability probe, persists the per-conversation choice
in localStorage, stamps every assistant message with a model badge
(message-id→model map, cloud backfill for pre-feature messages), and calls
the local model with thinking disabled. Per the plan request, test cases
and an error-handling matrix are first-class outputs (research.md §Test
Design / §Error Handling, quickstart.md).

## Technical Context

**Language/Version**: TypeScript on Next.js 16 (Chat UI); Python 3.12
(deploy CLI); Dify 1.18.0 chatflow DSL (YAML).

**Primary Dependencies**: existing only — shadcn/ui (Base UI, luma preset)
menu primitives; Dify self-hosted 1.18.0 (`http://localhost/v1`); Ollama
0.40.11 rootless on the host (`0.0.0.0:11434`, Qwen3 8B Q4_K_M); the
spec-011 deploy CLI (`src/agentic_rag_mcp/deploy/`).

**Storage**: Dify conversations (server, unchanged) + browser localStorage
(per-conversation selection, per-message badge map). No new server storage.

**Testing**: vitest units (`pnpm test` in `ai-chat-landing/`);
`pnpm typecheck && pnpm lint`; deploy verification battery (cloud-only,
unchanged, 10/10); CDP throwaway live checks for SC-001..SC-003.

**Target Platform**: Linux host; Chat UI on port 3000 (dev server — never
`pnpm build` while it runs).

**Project Type**: web app (Chat UI) + chatflow configuration.

**Performance Goals**: availability probe completes ≤5 s (SC-002); local
replies stream with the existing "Thinking" indicator for their full
(CPU-bound) duration; no UI blocking.

**Constraints**: contract preservation — `inputs.ai_model` is additive,
`ask` response fields and MCP tool schemas untouched; battery unchanged;
no new npm/pip dependencies; Ollama address never exposed to the browser.

**Scale/Scope**: exactly two model options; single-user app; 3 cloud LLM
nodes + 3 local copies + 1 router node in the DSL.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Contract Preservation | PASS | `inputs.ai_model` is a new optional start variable — absent input means cloud (today's behavior); `ask` field set, MCP tool schemas, and battery scenarios unchanged. |
| II. Tests-First | PASS | Unit suites for selection state machine, badge resolution, availability, persistence are part of tasks; error paths (FR-004/007) have explicit cases (research.md §Test Design). |
| III. Minimal Dependencies | PASS | Zero new deps; Ollama is an already-installed service integrated with graceful degradation (FR-004 fallback = degrade when absent). |
| IV. Honest Answers | PASS | The feature is built on it: per-reply badges, unavailability marking, inline persistent fallback note, no silent substitutions, no hidden reasoning. |
| V. Spec-Driven Replacement | PASS | The single-model graph is superseded by the routed graph — old edges/nodes deleted, not kept as dead paths. |

**Post-Phase-1 re-check**: design adds no new services or dependencies;
DSL change is additive plus replacement of the start→intent_router edge with
start→model_router fan-out. Still PASS.

## Project Structure

### Documentation (this feature)

```text
specs/025-ai-llm-dropdown/
├── plan.md              # This file
├── research.md          # Phase 0 output — decisions incl. test design + error matrix
├── data-model.md        # Phase 1 output — entities + selection state machine
├── quickstart.md        # Phase 1 output — runnable validation scenarios
├── contracts/
│   └── model-selection.md # HTTP, Dify input, DSL graph, storage-key contracts
└── tasks.md             # Phase 2 (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
ai-chat-landing/
├── app/
│   ├── api/models/route.ts        # NEW — local-model availability probe (host-side)
│   ├── api/chat/route.ts          # EXTEND — forward inputs.ai_model to Dify
│   └── page.tsx                   # EXTEND — dropdown trigger + badge wiring
├── components/model-dropdown.tsx  # NEW — "AI LLM" single-select menu
├── lib/models/
│   ├── options.ts                 # NEW — ModelOption catalog (cloud/local)
│   ├── selection.ts               # NEW — single-select state + FR-004 reset
│   ├── availability.ts            # NEW — probe client (5 s budget)
│   ├── persistence.ts             # NEW — per-conversation storage + cleanup
│   └── badge.ts                   # NEW — message→model resolution + backfill
└── lib/models/*.test.ts           # NEW — vitest units (tests-first)

dify/AGIAssistant/AGI_Assistant.yml  # EXTEND — ai_model start var + local branch

src/agentic_rag_mcp/deploy/          # EXTEND — Ollama provider setup + publish
```

**Structure Decision**: no new top-level layers. UI logic lives in
`ai-chat-landing/` (`components/` + `lib/models/`), backend routing in the
Dify DSL (single source of truth, published via the deploy CLI), ops in the
existing deploy package — mirroring the placement of specs 013–015.

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
