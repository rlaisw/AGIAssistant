# Feature Specification: "AI LLM" Model Drop-Down Menu

**Feature Branch**: `025-ai-llm-dropdown`

**Created**: 2026-10-26

**Status**: Draft

**Input**: User description: "base on the above chat conversation and installed ollama and Qwen3 8B Q4_K_M. help to proceed specify task" — the feature named in the preceding conversation: an **"AI LLM" drop-down menu** in the Chat UI that lets the user pick which AI model powers the conversation. The prerequisite named there is complete: Ollama 0.40.11 is installed and serving on the host (all interfaces, port 11434), with **Qwen3 8B (Q4_K_M, 5.2 GB)** pulled and verified (tool-calling and thinking capable, 40K context, CPU-only inference — no GPU on this host). Today every assistant reply is served by the hosted DeepSeek model via the existing provider; that model remains the default.

## Clarifications

### Session 2026-10-26

- Q: How many models can be active at once, and how many entries does the
  drop-down offer? → A: **Single-select, exactly two entries** (user
  decision): the user picks ONE model — either the local model or the
  cloud model, one model on each side. Choosing either side deselects the
  other; there is never more than one active model. No multi-model mixing,
  no per-node model assignment.
- Q: When the local model is unavailable and the conversation falls back
  to the cloud model, what happens to the selection once Local becomes
  reachable again? → A: **Reset** (user decision, Option A): the fallback
  itself switches the conversation's selection to the cloud model; Local
  is never auto-resumed — the user must re-select it deliberately.
- Q: Should each assistant reply visibly show which model produced it?
  → A: **Yes — a small model badge in every assistant message footer**
  (user decision, Option B), reflecting the model that actually served
  that reply, even after fallbacks.
- Q: What form does the FR-004 fallback notice take? → A: **An inline
  system note in the chat stream** (user decision, Option A) that
  persists in the conversation history — not a transient toast.
- Q: What model badge do assistant messages from conversations created
  before this feature show? → A: **Backfill the cloud model badge**
  (user decision, Option A) — all pre-feature replies were factually
  served by the cloud model, so no "unknown" state is needed.
- Q: How is the local model's built-in reasoning trace (Qwen3 thinking,
  on by default) handled? → A: **Disabled** (user decision, Option C) —
  the local model is requested with thinking off; replies carry the
  answer only, which also cuts the CPU wait.
- Q: Does the drop-down also show the cloud model's availability status?
  → A: **No — local-only status** (user decision, Option A): cloud
  outages surface as the existing per-message error; the drop-down
  health-checks only the local model.
- Q: Should the deployment verification battery exercise the local model?
  → A: **No — the battery stays cloud-only** (user decision, Option B);
  Local is verified via the throwaway live checks (SC-001..SC-003).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pick the model and chat with it (Priority: P1)

The user opens the "AI LLM" drop-down in the chat interface and sees
exactly two entries — the cloud model (hosted DeepSeek, default) and the
local model (locally installed Qwen3 8B) — with the active one marked.
The choice is single-select: picking either entry deactivates the other,
and every subsequent assistant reply in the current conversation —
general chat and deck generation alike — runs on the one selected model.

**Why this priority**: it is the entire feature — user-visible choice of
which brain answers, between the fast hosted model and the private local
one.

**Independent Test**: switch to the local model, send "which model are
you?", and the reply identifies the selected model; switch back and the
next reply comes from the hosted model.

**Acceptance Scenarios**:

1. **Given** an open conversation, **When** the user opens the "AI LLM"
   drop-down, **Then** both models are listed and the active one is
   marked.
2. **Given** the local model selected, **When** the user sends a message,
   **Then** the reply is served by the local Qwen3 8B model.
3. **Given** a model switch mid-conversation, **When** the next message is
   sent, **Then** the newly selected model answers and earlier messages
   are unchanged.
4. **Given** one model selected, **When** the user selects the other,
   **Then** exactly one entry is active — never both, never neither while
   both are available.
5. **Given** a completed assistant reply, **When** the user looks at it,
   **Then** its footer badge names the model that produced it.

---

### User Story 2 - Honest availability of the local model (Priority: P2)

When the local model server is not running or unreachable, the drop-down
clearly marks the local model as unavailable (with a short status), and
the conversation keeps working on the hosted default. Nothing pretends:
no silent serving with the wrong model, no hanging waits.

**Why this priority**: the local model depends on a host process that can
be down or slow; the system must say so (constitution Principle IV —
honest answers) or the feature erodes trust.

**Independent Test**: stop the local model server, open the drop-down —
the local entry shows as unavailable; send a message — the hosted model
answers normally.

**Acceptance Scenarios**:

1. **Given** the local model server stopped, **When** the user opens the
   "AI LLM" drop-down, **Then** the local model is marked unavailable
   and cannot be selected.
2. **Given** the local model unavailable, **When** the user sends a
   message, **Then** the conversation switches to the hosted default with
   an explicit, visible notice — the selection itself resets to the
   hosted default, never a fabricated "local" reply.

---

### User Story 3 - The choice sticks with the conversation (Priority: P3)

Each conversation remembers its selected model: after a page reload or
resuming the conversation from history, the previously chosen model is
still active without re-selecting. Brand-new chats start on the hosted
default.

**Why this priority**: persistence makes the choice feel real rather than
a setting the user must re-apply every message.

**Independent Test**: select the local model, reload the page, reopen the
conversation from the sidebar — the drop-down still shows the local model
as active.

**Acceptance Scenarios**:

1. **Given** a conversation with the local model selected, **When** the
   page reloads and the conversation is resumed, **Then** the local model
   is still the active selection.
2. **Given** a brand-new chat, **When** it opens, **Then** the hosted
   default model is active.

---

### Edge Cases

- Local model mid-generation failure (server dies while answering): the
  message ends in the standard error state — surfaced, not silently
  retried on another model; the selection resets to the hosted default
  per FR-004.
- Local model returns after a fallback: the conversation stays on the
  hosted default until the user re-selects Local — no silent auto-resume.
- Cloud model outage: unchanged from today — the message ends in the
  standard error state; the drop-down health-checks the local model only
  and the cloud entry stays selectable.
- Local model latency: CPU inference takes minutes per reply; the
  existing "Thinking" indicator (spec 022) keeps showing progress the
  whole time — no frozen-looking UI, no hidden timeout.
- Deck generation on the local model: the same selection applies to deck
  requests; expect much slower runs — honest expectations, no blocking.
- Switching while a reply is streaming: the switch takes effect from the
  next message; the in-flight reply is untouched.
- The drop-down's controls must not collide with existing controls
  (distinct labels from the sidebar's "Conversation options" button).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The chat interface MUST offer a single-select "AI LLM"
  drop-down with exactly two entries — the cloud model (hosted DeepSeek,
  default) and the local model (Qwen3 8B) — marking the active one;
  exactly one model is active at any time, and selecting either entry
  deselects the other.
- **FR-002**: Selecting a model MUST apply to all subsequent assistant
  replies in the current conversation, general chat and deck generation
  alike.
- **FR-003**: The selected model MUST persist per conversation across
  reload and resume; new conversations MUST start on the hosted default.
- **FR-004**: When the local model is unreachable, the drop-down MUST
  mark it unavailable and unselectable, and the conversation MUST fall
  back to the hosted default with an inline system note in the chat
  stream that persists in the history; this fallback MUST reset the
  conversation's selection to the hosted default — Local is never
  auto-resumed and MUST be re-selected deliberately once available.
- **FR-005**: Switching models MUST NOT alter past messages, history,
  search, PDF export, rename, or delete behavior.
- **FR-006**: The drop-down MUST set honest expectations for the local
  model (slower, CPU-bound) via a short hint next to the local entry.
- **FR-007**: If the selected local model fails mid-generation, the
  system MUST surface the failure as a normal message error — no silent
  fallback, no fabricated reply.
- **FR-008**: Every assistant message MUST show a small badge in its
  footer naming the model that actually produced that reply — accurate
  even after switches and fallbacks; messages from conversations created
  before this feature MUST show the cloud model badge (all pre-feature
  replies were cloud-served).
- **FR-009**: The local model MUST be requested with its reasoning mode
  (thinking) disabled — assistant replies carry the answer only; no
  reasoning trace is generated, hidden, or shown.

### Key Entities

- **Model Option**: a choosable model — display name, origin (hosted
  default / local), availability status, and whether it is the default.
- **Conversation**: has an active model selection; starts on the default,
  remembers the user's choice for its lifetime.
- **Assistant Message**: carries the model that actually produced it,
  shown as its footer badge.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user switches models in at most 2 interactions (open
  drop-down, select), and the next reply's footer badge names the
  selected model (verified on a throwaway conversation, created and
  deleted afterwards).
- **SC-002**: With the local model server stopped, the drop-down shows
  its unavailable status within 5 seconds of opening, and 100% of new
  messages still complete on the hosted model.
- **SC-003**: After reload and resume, the previously selected model is
  active with no re-selection — verified on a live throwaway
  conversation (created and deleted after).
- **SC-004**: No regression: existing checks stay green (Chat UI unit
  suite, typecheck, lint; deployment verification battery passes
  unchanged — cloud-only by design, with the local model verified by
  the throwaway live checks in SC-001..SC-003).

## Assumptions

- The install prerequisite is done: Ollama 0.40.11 + Qwen3 8B Q4_K_M on
  the host, reachable from the chat backend (bound to all interfaces,
  port 11434), CPU-only inference.
- The drop-down is a two-way single-select choice with one model per
  side — cloud DeepSeek (default) and local Qwen3 8B (user decision,
  2026-10-26); adding more models per side, model lists, or model
  management UI is out of scope for v1.
- Selection is per conversation and follows the app's existing
  conversation-state patterns; no user accounts involved.
- The whole assistant follows the selection — the routing and deck
  decision points included — because a "half-switched" assistant would be
  dishonest about which model answered.
- The local model remains selectable for deck generation but runs much
  slower; the feature informs, does not block (Principle IV).
- The drop-down lives near the composer/header; its trigger gets a label
  distinct from existing controls (the header "…" demo stub is a
  pre-existing tracked issue, not part of this spec).
