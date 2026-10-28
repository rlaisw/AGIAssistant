# Implementation Plan: Stop Generation Button

**Branch**: `027-stop-generation-button` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/027-stop-generation-button/spec.md`

## Summary

Add a Stop control to the AGI Chat composer: while a generation is in flight, the send button morphs into "Stop"; activating it (a) calls the chat backend's cancel endpoint through a new same-origin proxy route so the server halts the generation, (b) aborts the local stream, and (c) finalizes the turn honestly — partial text and reasoning stay, a session-only "Stopped" caption marks the turn, no empty bubble is left when nothing arrived. The existing silent user-abort path in `page.tsx` (which today leaves a stuck streaming state) is superseded by this first-class stop/finalize path.

## Technical Context

**Language/Version**: TypeScript 5 (Next.js 16 App Router; React 19)

**Primary Dependencies**: existing platform APIs only — `fetch` + `AbortController` (already used in `app/page.tsx`), Dify Service API via the in-repo proxy (`app/api/chat/route.ts`). No new npm packages.

**Storage**: none — all new state is in-memory/session-only (spec clarification: the "Stopped" caption is not persisted)

**Testing**: vitest (`pnpm test`, pure-logic lib tests) · CDP acceptance script (`scripts/*.mjs` pattern, Chrome `--remote-debugging-port=9240`) · deploy-battery scenario for the backend-halt assertion (SC-005)

**Target Platform**: Linux host (WSL2), browser client; Next.js dev server on :3000; Dify stack on :80/:28080 sidecar

**Project Type**: web application (Next.js frontend + thin same-origin proxy routes; server API key stays server-side per AGENTS.md)

**Performance Goals**: stop takes visible effect < 1 s (SC-001); backend halt verified (SC-005)

**Constraints**: no new dependencies (Constitution III); stream event contract changes must be additive-only (Constitution I); Dify service API key never reaches the client; never run `pnpm build` while `pnpm dev` is up

**Scale/Scope**: single-user deployment; one in-flight generation at a time (existing single-flight model preserved — see research R5)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Notes |
|---|---|---|
| I. Contract Preservation | PASS | One additive stream event type (`task`, research R2); existing events byte-identical; unknown-event-tolerant consumers unaffected. No MCP tool schema changes — the sidecar is untouched. |
| II. Tests-First | PASS | `lib/stop/state.ts` state machine gets failing-first vitest; CDP script + battery scenario written with the tasks (see quickstart). |
| III. Minimal Dependencies | PASS | Zero new packages: AbortController/fetch are platform; Dify's stop endpoint is an existing API of the deployed stack (verified live, research R1). |
| IV. Honest Answers | PASS | Stopped turns are captioned, never presented as complete; thinking-phase stop leaves no empty bubble; backend-halt is a verified battery behavior, not an assumption. |
| V. Spec-Driven Replacement | PASS | The current silent `AbortError → return` branch (which leaves `streaming: true` and `busy` stuck) is replaced by the explicit stop/finalize path; the watchdog-timeout path keeps its existing error UX (research R3). Supersedes record here. |

Post-Phase-1 re-check: design adds no entities beyond in-memory flags and one additive event — still PASS on all five.

## Project Structure

### Documentation (this feature)

```text
specs/027-stop-generation-button/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output (validation guide incl. test cases + error matrix)
├── contracts/
│   └── stop-generation.md  # stream event addition + stop route contract + lib interface
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
ai-chat-landing/
├── app/
│   ├── api/chat/route.ts        # modified: forward task_id as additive `task` event
│   ├── api/chat/stop/route.ts   # NEW: POST /api/chat/stop → Dify stop endpoint (key stays server-side)
│   └── page.tsx                 # modified: send→Stop morph, stop handler, finalize paths (incl. demo mode)
├── lib/
│   └── stop/
│       ├── state.ts             # NEW: pure stop state machine (morph decision, finalize action, no-op guard)
│       └── state.test.ts        # NEW: failing-first unit tests (vitest, node-env)
└── scripts/
    └── stop-button-check.mjs    # NEW: CDP acceptance script (morph, stop, caption, <1s ready, follow-up)

tests/ (repo root)
└── integration/test_deploy_battery.py or the battery's scenario module  # NEW scenario: stop → no further content (SC-005)
```

**Structure Decision**: single-project layout; all feature code lands in the existing `ai-chat-landing/` app plus one battery scenario — no new packages, no sidecar change.
