# Implementation Plan: Landing Page Starts on "New Chat"

**Branch**: `020-landing-new-chat` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/020-landing-new-chat/spec.md`

## Summary

Replace the demo-fixture initialization (`initialConversations` + `activeId="q3"`)
with a single fresh empty draft (`c-0`, title "New chat", no messages) so
every fresh load opens on the "How can I help you today?" empty state.
Remove the fixture array entirely (dead data per Constitution V); the
demo-reply fallback (`cannedReplies`/`demoStream`) is a separate, untouched
mechanism.

## Technical Context

- **Language/Version**: TypeScript (Next.js 16.4, React 19.3)
- **Primary Dependencies**: none added — initialization change + fixture deletion
- **Storage**: N/A (initial React state only)
- **Testing**: `pnpm typecheck && pnpm lint && pnpm test` (79/79); CDP
  rendered checks T1–T6 (contracts/landing-checks.md); no vitest additions
  (no pure logic — house convention; research R3)
- **Target Platform**: web (desktop + mobile, local + remote)
- **Constraints**: deterministic initial state (no `window` in the
  initializer → no SSR/hydration mismatch); draft id must not collide with
  the `c-N` counter (R4)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Contract Preservation**: PASS — UI initialization only.
- **II. Tests-First**: PASS — the runnable check is the CDP rendered matrix
  (contracts/landing-checks.md T1–T6); the change itself is an initial
  state constant with no testable pure logic (house convention).
- **III. Minimal Dependencies**: PASS — zero.
- **IV. Honest Answers**: PASS — FR-003's fallback is preserved by
  construction (untouched code, grep-verified) rather than claimed via a
  simulated outage; the plan says so openly.
- **V. Spec-Driven Replacement**: PASS — removes the demo fixtures
  (dead data once nothing opens on them); no dead code left.

No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/020-landing-new-chat/
├── plan.md              # This file
├── research.md          # R1–R4 decisions
├── data-model.md        # Initial state shape
├── contracts/
│   └── landing-checks.md  # T1–T6 check matrix + error handling
├── quickstart.md        # Validation guide
├── checklists/
│   └── requirements.md  # (from /speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
ai-chat-landing/app/
└── page.tsx            # replace initializer + activeId; delete initialConversations (~90 lines)
```

**Structure Decision**: one file, ~10 lines changed + ~90 lines deleted.

## Design

- Initial state: `conversations = [{ id: "c-0", title: "New chat", messages: [] }]`,
  `activeId = "c-0"` — identical shape to `newChat()` output.
- `active = conversations.find(...) ?? conversations[0]` resolves to the
  draft by construction (id lookup plus the `[0]` fallback).
- The `c-N` counter (`idRef` starts at 3) never collides with `c-0`.
- Empty state branch (`active.messages.length === 0`) renders the
  "How can I help you today?" prompt + suggestion cards — unchanged code.
- Fixture removal: `initialConversations` (the 5 sample threads) deleted;
  `cannedReplies`/`demoStream` (the Dify-down fallback) untouched.

## Verification

1. Gates: typecheck, lint, 79/79 vitest.
2. CDP T1–T6 per `contracts/landing-checks.md`: fresh-load empty state
   (1440 + 390), header "New chat", zero bubbles, 4 suggestion cards;
   fixture-title grep zero; first-send throwaway creates the sidebar row
   (delete after); fallback preserved by construction (grep
   `cannedReplies`/`demoStream` intact); regression scope: wide-layout
   matrix + drawer-check + search-check re-run.
