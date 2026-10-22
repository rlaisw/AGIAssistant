# Implementation Plan: Delete Conversation

**Branch**: `015-conversation-delete` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/015-conversation-delete/spec.md`
(user emphasis: original plan + explicit test cases and error handling)

## Summary

Delete a conversation from the grouped sidebar via a hover "…" dropdown menu
(v1: Delete only, Rename deferred) with an inline confirmation; the delete is
backend-real — one additive route handler proxies Dify's
`DELETE /conversations/{id}` with the key server-side (the proven spec-014
pattern), and the row is removed locally only after the backend succeeds.
Deleting the open conversation aborts any in-flight stream and falls back to
a fresh draft. Tests-first per the user's requirement and Constitution II:
the store's `remove` seam, the route mapper, and a per-row delete state
machine (idle → menu → confirming → in-flight → done/failed, double-submit
guard) get failing vitest before implementation — node env, injected fetch, no
network — with an explicit `delete_failed` error taxonomy (row stays, honest
inline error, never local-only removal) documented in
[data-model.md](data-model.md) and [contracts/conversation-delete.md](contracts/conversation-delete.md).

## Technical Context

**Language/Version**: TypeScript 5.x, React 19.3, Next.js 16.4 (ai-chat-landing)

**Primary Dependencies**: existing — Base UI dropdown-menu components (the
app's `DropdownMenu` family), lucide-react icons, spec 014's
`lib/history/` modules (`createHistoryState`, `ConversationRecord`,
`HistoryError`), Dify service API via `fetch` with `DIFY_API_KEY` /
`DIFY_API_BASE_URL` env, `user: "ai-chat-ui-user"`. **Zero new packages**.

**Storage**: none — deletion removes from Dify + session memory only.

**Testing**: vitest (`pnpm test`, node environment) — store seam, route
mapper, delete machine with injected fetch stub; mocks at trust boundaries.

**Target Platform**: browser (Chat UI sidebar; the sidebar is desktop-visible
per spec 014, so touch hover is out of scope).

**Project Type**: web-app frontend feature + one additive same-origin route.

**Performance Goals**: delete is a single-digit-KB round trip; row removal is
instant on success (SC-001).

**Constraints**: no key/user exposure (contracts §1); backend-first ordering —
never local-only removal (FR-005); drafts never offer Delete (FR-008).

**Scale/Scope**: one delete at a time in v1; hundreds of rows unaffected.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Evidence |
|-----------|---------|----------|
| I. Contract preservation | PASS | Additive: one new route + UI affordance; no MCP schemas, no existing route changes; spec-013/014 paths untouched (SC-003/S5·S7 regressions pinned) |
| II. Tests-first | PASS | Test matrix in data-model.md precedes implementation; failing tests first; deterministic (injected fetch, no network) |
| III. Minimal dependencies | PASS | Zero new packages — reuses dropdown components, history modules, abort machinery |
| IV. Honest answers | PASS | `delete_failed` taxonomy; backend-first ordering; row never silently dropped; confirmation copy says "cannot be undone" |
| V. Spec-driven replacement | PASS | Supersedes nothing; purely additive to spec 014's sidebar |

**Post-Phase-1 re-check**: design adds no services, packages, or storage; the
delete machine and remove seam follow the injected-seam pattern proven in
specs 013/014. Gates remain PASS.

## Project Structure

### Documentation (this feature)

```text
specs/015-conversation-delete/
├── plan.md              # This file
├── research.md          # Phase 0 output (R1–R7 decisions)
├── data-model.md        # Phase 1 output (delete machine, error code, store seam, test matrix)
├── quickstart.md        # Phase 1 output (S1–S7 validation guide)
├── contracts/
│   └── conversation-delete.md  # Route contract + pure seams + upstream assumption
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
ai-chat-landing/
├── lib/history/
│   ├── types.ts          # HistoryErrorCode += "delete_failed"
│   ├── state.ts           # remove(difyId) seam (success-only call site)
│   ├── delete.ts          # createDeleteState machine (pure)
│   └── *.test.ts         # vitest per data-model test matrix
├── app/api/conversations/
│   └── [id]/route.ts     # DELETE proxy (contracts §1)
├── components/
│   └── chat-history.tsx  # + "…" affordance per row, dropdown with inline confirm
└── app/
    └── page.tsx          # wire: deleteRequest aborts stream when active, fresh draft fallback
```

**Structure Decision**: extends spec 014's proven layout — pure state in
`lib/history/` (a new `delete.ts` keeps the delete machine separately
testable), one thin route handler (new file alongside the existing
`[id]/messages/`), the row UI grows inside `chat-history.tsx`, and the page
wiring reuses `newChat()` + the existing `abortRef` for the active-deletion
path.

## Complexity Tracking

> No Constitution violations to justify — table intentionally empty.
