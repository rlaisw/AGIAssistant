# Research: Landing Page Starts on "New Chat"

## R1 — Initialize with one fresh draft, not an empty array

- **Decision**: `conversations` initializes to
  `[{ id: "c-0", title: "New chat", messages: [] }]`, `activeId = "c-0"`.
- **Rationale**: `active = conversations.find(...) ?? conversations[0]`
  would be `undefined` with an empty array (header renders
  `active.title` — crash). One draft uses the exact `newChat()` shape and
  hits the existing empty-state branch unchanged.
- **Alternatives considered**: empty array + optional-chaining guards —
  rejected (touches the render path for zero benefit; the draft is the
  natural "new session" object).

## R2 — Remove the demo fixtures entirely

- **Decision**: delete `initialConversations` (5 sample threads, ~90 lines).
- **Rationale**: once nothing opens on them, they are unreachable dead
  data (Constitution V). The Dify-down fallback replies are a *separate*
  constant (`cannedReplies`/`demoStream`) — untouched, still works.
- **Alternatives considered**: keep the fixtures hidden — rejected (dead
  code with no reachable UI; a one-line revert restores them if ever
  wanted for demos).

## R3 — No vitest additions; acceptance is a rendered check

- **Decision**: the CDP rendered matrix (contracts/landing-checks.md
  T1–T6) is the runnable acceptance; no new unit tests.
- **Rationale**: the change is an initial-state constant — there is no
  pure logic to cover (house convention: vitest for pure logic; the
  existing 79 stay green). Asserting "initial state is a draft" via a
  component render test would be tautological setup-assertion.
- **Alternatives considered**: a render test via Testing Library —
  rejected (adds a new dev dependency for a constant assertion).

## R4 — Draft id "c-0" cannot collide with the `c-N` counter

- **Decision**: the initial draft uses the fixed id `c-0`; `newChat()`
  keeps generating `c-4, c-5, …` (`idRef` starts at 3 and pre-increments).
- **Rationale**: disjoint id spaces — `c-0` never repeats; the counter
  family is untouched. Message ids share the same ref and are numeric —
  no interaction with the `c-` conversation ids.
- **Alternatives considered**: seed `idRef` from the draft id — rejected
  (needless coupling; a fixed literal is simpler).

## Error handling (user-requested)

| Condition | Behavior |
|---|---|
| `activeId` not found in state | `?? conversations[0]` fallback resolves to the draft (no crash) |
| SSR vs client initial state | deterministic (no `window` in the initializer) — no hydration mismatch |
| First send with Dify down | unchanged `demoStream` fallback in the initial draft (FR-003, grep-verified) |
| Delete mid-stream from the initial draft | unchanged spec-015 active-delete path switches to a fresh `newChat()` |
| Reload at any point | fresh draft again — consistent with today's no-local-persistence |
| PDF export on the empty draft | button stays disabled (no messages) — unchanged |
