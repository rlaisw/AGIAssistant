# Implementation Plan: Time-Grouped Chat History

**Branch**: `014-chat-history-groups` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/014-chat-history-groups/spec.md`
(user emphasis: original plan + explicit test cases and error handling)

## Summary

Backend-backed chat history for the sidebar: two additive Next.js route
handlers proxy Dify's conversation-list and conversation-messages endpoints
(app key stays server-side, same posture as `/api/chat`), and a pure
`lib/history/` module buckets the records — Today / Yesterday / Previous 7
days / Last month / Few months ago — by local-calendar-day boundaries with an
injected clock. First page renders instantly with an honest "Load more"
cursor control; a session-only draft enters history only when its first
message returns a conversation id. Tests-first per the user's requirement and
Constitution II: the bucket math, state machine, title derivation, and route
mappers all get failing vitest first (frozen clocks, stubbed fetch — no
network, no browser); error handling is a designed taxonomy
(`history_unavailable` / `messages_unavailable`, console-only
`invalid_timestamp`) documented in [data-model.md](data-model.md) and
[contracts/chat-history.md](contracts/chat-history.md).

## Technical Context

**Language/Version**: TypeScript 5.x, React 19.3, Next.js 16.4 (ai-chat-landing)

**Primary Dependencies**: existing — Dify service API via `fetch`
(`DIFY_API_KEY`, `DIFY_API_BASE_URL` env; `user: "ai-chat-ui-user"`),
lucide-react icons, the app's `Conversation`/`Message` types. **Zero new
packages** — date math is stdlib (reuse ladder, Constitution III).

**Storage**: none added — conversations stay in Dify; the UI holds records
in React state for the session.

**Testing**: vitest (`pnpm test`, node environment) — pure modules + route
mappers with injected fetch seams; mocks at trust boundaries, no network.

**Target Platform**: browser (Chat UI at localhost:3000).

**Project Type**: web-app frontend feature + two additive same-origin API
routes.

**Performance Goals**: first page renders within 1 s of fetch completion
(SC-003); sidebar grouping is O(n log n) per render and trivially fast for
hundreds of records.

**Constraints**: no new runtime service (SC-004); no key/user exposure in
responses (contracts §1/§2); drafts never reach the backend (FR-014).

**Scale/Scope**: dozens of conversations typical; pagination bounded by
Load more (FR-013).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Evidence |
|-----------|---------|----------|
| I. Contract preservation | PASS | Purely additive: two new same-origin routes; no MCP schema, no `ask` fields, no existing route changes; PDF export path untouched |
| II. Tests-first | PASS | Test matrix in data-model.md precedes implementation; every pure module has failing tests first; deterministic (frozen clock, stubbed fetch) |
| III. Minimal dependencies | PASS | Zero new packages (stdlib date math; existing fetch/proxy pattern reused) |
| IV. Honest answers | PASS | Error taxonomy (R6): every failure has a code + visible notice; invalid timestamps degrade loudly to the floor bucket, never silently dropped; Load more is the honest "more exists" signal |
| V. Spec-driven replacement | PASS | The hardcoded `group` string on canned conversations is superseded by computed buckets — old string-tag path deleted, not left dead |

**Post-Phase-1 re-check**: design adds no services, no packages, no
storage; all seams are injectable and tested. Gates remain PASS.

## Project Structure

### Documentation (this feature)

```text
specs/014-chat-history-groups/
├── plan.md              # This file
├── research.md          # Phase 0 output (R1–R8 decisions)
├── data-model.md        # Phase 1 output (records, buckets, state machine, error taxonomy, test matrix)
├── quickstart.md        # Phase 1 output (S1–S7 validation guide)
├── contracts/
│   └── chat-history.md  # Route contracts + pure module seams + Dify upstream assumptions
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
ai-chat-landing/
├── lib/history/
│   ├── types.ts            # ConversationRecord, BucketId, BucketedConversations, HistoryError
│   ├── buckets.ts          # bucketOf + groupConversations (pure, injected clock; FR-001–004/007)
│   ├── titles.ts            # titleFor fallback derivation (FR-012)
│   ├── state.ts             # createHistoryState: loading/ready/error + loadMore (FR-006/008/013)
│   ├── mappers.ts           # Dify list/messages responses → app shapes (route-side, tested)
│   └── *.test.ts            # vitest per data-model test matrix
├── app/api/conversations/
│   ├── route.ts             # GET list proxy (cursor/limit → Dify last_id/limit; contracts §1)
│   └── [id]/messages/route.ts  # GET history proxy (contracts §2)
├── components/
│   └── chat-history.tsx     # grouped sidebar list: loading, error notice, Load more, groups
└── app/
    └── page.tsx             # wire: fetch on open, resume on click, draft promotion (FR-011/014)
```

**Structure Decision**: mirrors spec 013's proven layout — pure modules in
`lib/` (node-testable, no React imports), thin route mappers, one presentational
component, minimal page wiring. The existing hardcoded `sidebarGroups` /
canned `group` strings are deleted with the wiring change (Constitution V).

## Complexity Tracking

> No Constitution violations to justify — table intentionally empty.
