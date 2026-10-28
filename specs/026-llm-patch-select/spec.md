# Feature Specification: Apply Selected LLM to the Chatflow (Patch-on-Select)

**Feature Branch**: `026-llm-patch-select`

**Created**: 2026-10-26

**Status**: Draft

**Input**: User description: "implement change LLM name to dify .yml — when the user chooses an AI LLM name: (1) export the AGI Assistant app (194e1edf-2eba-442c-b10b-231bebb79c37) to /kilocode/AGIAssistant/dify/AGIAssistant/, (2) change the LLM node model name to the user-selected LLM name for these 3 LLM nodes (PPT or General?, Agentic Strategy, PPT-Master), (3) re-import the app with OVERWRITE mode into the same app, (4) publish again — referencing the existing dify/difyctl-export-reimport-publish.sh script."

## Clarifications

### Session 2026-10-26

- Q: When the user selects the LOCAL model, does the patch cycle also
  reconfigure the main nodes (single mechanism), or does local keep its
  routed branch? → A: **Cloud-only patch** (user decision, Option B):
  local keeps its existing `ai_model = "local"` routed branch from spec
  025 (instant fallback, no republish); the patch cycle applies only to
  cloud selections; only the kimi/glm/qwen38 branches and the
  `cloud_model` input are removed.
- Q: What happens if the user sends a message while a reconfiguration
  cycle is running? → A: **Sends are blocked during the cycle** (user
  decision, Option A) with a visible applying indicator naming the model
  being applied; sends resume once the new model is live — no old-model
  surprise right after an explicit choice.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choosing a model reconfigures the assistant (Priority: P1)

The user picks a cloud model in the "AI LLM" drop-down (e.g. Kimi-k3).
The system exports the AGI Assistant app, updates the three main LLM
nodes (PPT or General?, Agentic Strategy, PPT-Master) to run the selected
model, re-imports into the same app with OVERWRITE mode, and republishes.
Every subsequent assistant reply — general chat and deck generation alike —
is served by the selected model, and the per-reply badge confirms it.

**Why this priority**: it is the entire feature — the menu choice becomes
real at the chatflow level instead of a per-request route.

**Independent Test**: select Kimi-k3, wait for the cycle to finish, send
"which model are you?" — the reply comes from Kimi-k3 and its badge names
it; the exported file shows Kimi's model in the three main nodes.

**Acceptance Scenarios**:

1. **Given** a cloud model selected in the drop-down, **When** the cycle
   completes, **Then** the app is republished with the three main LLM
   nodes running that model.
2. **Given** a completed reconfiguration, **When** the user sends a
   message, **Then** the reply is served by the selected model and its
   badge names it.
3. **Given** the selection changed mid-conversation, **When** the next
   message is sent after the cycle completes, **Then** the new model
   answers and earlier messages are unchanged.

---

### User Story 2 - Honest reconfiguration lifecycle (Priority: P2)

While the export → patch → overwrite-import → publish cycle runs, the
user sees an "applying" state in the interface. If any step fails, the
previously published configuration keeps serving, the selection stays as
it was, and the user sees an honest error — never a half-applied app.

**Why this priority**: the cycle takes tens of seconds and touches the
live app; hiding it or failing silently would erode trust (constitution
Principle IV).

**Independent Test**: force one step to fail (e.g. interrupt the import)
— the error is shown, the selection reverts, and the next message still
answers on the previous model.

**Acceptance Scenarios**:

1. **Given** a selection made, **When** the cycle is running, **Then**
   the interface shows an applying indicator naming the model being
   applied and sending is disabled until it completes.
2. **Given** a cycle that fails, **When** the user next sends a message,
   **Then** the previous model answers and an error was displayed.

---

### User Story 3 - The choice persists as the app default (Priority: P3)

The selected model becomes the assistant's default configuration — it
survives restarts and new sessions because it lives in the published app
itself, not in browser storage. Every reply continues to show which
model actually produced it (per-reply badge provenance).

**Why this priority**: the global default is the honest consequence of
republishing; provenance keeps history truthful.

**Independent Test**: select a model, restart the Chat UI, open a brand
new chat — it answers on the selected model without any re-selection.

**Acceptance Scenarios**:

1. **Given** a model applied, **When** a new chat starts later, **Then**
   it runs on the applied model by default.
2. **Given** messages from before and after a switch, **When** the user
   reads the conversation, **Then** each reply's badge names the model
   that actually produced it.

---

### Edge Cases

- Selection while a reply is streaming: the switch takes effect from the
  next message after the republish completes; the in-flight reply is
  untouched.
- Local model selection: local keeps its existing routed branch from
  spec 025 (decision 2026-10-26) — selecting Local never triggers the
  patch cycle; selecting a cloud model does.
- Local model unavailable at send time: the instant fallback from spec
  025 (FR-004) still applies — no republish involved.
- The per-model branch duplicates added earlier today (kimi/glm/qwen38
  branches) are removed — the chatflow carries a single cloud path.
- The deployment verification battery must stay green on the default
  configuration; it does not prescribe which model is currently selected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: On selecting an LLM in the menu, the system exports the
  AGI Assistant app to the repo's `dify/AGIAssistant/` artifact folder,
  updates the model of the three main LLM nodes (PPT or General?,
  Agentic Strategy, PPT-Master) to the selected model, re-imports with
  OVERWRITE mode into the same app, and republishes.
- **FR-002**: After a successful cycle, subsequent assistant replies are
  served by the selected model — general chat and deck generation alike.
- **FR-003**: During the cycle the interface shows an applying indicator
  naming the model being applied, and sending MUST be disabled until the
  cycle completes — the selection takes effect for messages sent after
  completion (user decision 2026-10-26).
- **FR-004**: On failure at any step, the previously published
  configuration keeps serving, the visible selection reverts to the
  previous model, and an honest error is shown — never a half-applied app.
- **FR-005**: The chatflow carries a single cloud path — the per-model
  branch duplicates from the earlier routing approach are removed as part
  of the next patch cycle (idempotent; re-runs are no-ops).
- **FR-006**: The per-reply badge continues to name the model that
  actually produced each reply, before and after any switch.
- **FR-007**: The exported app artifact in `dify/AGIAssistant/` reflects
  the selected model in the three main LLM nodes after each successful
  cycle.

### Key Entities

- **Model Selection (global)**: the model currently configured in the
  published app; replaced wholesale on each apply.
- **Reconfigure Cycle**: export → patch → overwrite-import → publish,
  with success/failure outcome; failure leaves the prior state intact.
- **Assistant Message**: carries the model that actually produced it
  (badge provenance, unchanged from spec 025).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After selecting a cloud model, the reconfiguration
  completes in at most 90 seconds and the next reply demonstrably comes
  from the selected model (throwaway live check, badge-verified).
- **SC-002**: A deliberately broken cycle leaves the previous model
  answering and shows an error — verified by simulated failure.
- **SC-003**: After each successful cycle, the exported app artifact
  shows the selected model in all three main LLM nodes (file check).
- **SC-004**: No regression: the unit suite, typecheck, lint, and the
  deployment verification battery stay green on the default
  configuration.

## Assumptions

- The selection becomes **global** (app-level): republishing reconfigures
  the app itself, so the choice applies to every conversation — the
  single-user deployment accepts this; per-message badges keep provenance
  truthful.
- The earlier multi-branch routing (added today) is superseded by this
  patch approach: the kimi/glm/qwen38 branches and the `cloud_model`
  input are removed; the chatflow returns to a single cloud path.
- Local keeps its existing routed branch (user decision, 2026-10-26):
  the patch cycle applies only to cloud selections.
- The reference implementation for the export → overwrite-import →
  publish cycle is the existing `dify/difyctl-export-reimport-publish.sh`.
- Selection while a cycle is already running queues or disables further
  selections until it finishes (single in-flight reconfiguration).
- The dropdown's shown selection derives from the app's **configured**
  model (server truth): on load it reflects the published config, not a
  possibly-stale stored choice; stored cloud selections from the
  routing era become display-only history provenance.
- Re-selecting the already-configured model is a no-op (no cycle).
- The local-down fallback (spec 025) targets the globally configured
  cloud model, whatever it currently is — not necessarily Deepseek.
- A concurrent edit in the Dify console aborts the cycle via the
  draft-hash guard from the reference script — honest error, no clobber.
- The Dify webapp follows the same global selection (it runs the same
  published app).
- Recovery from a corrupted cycle: the repo's git-versioned app artifact
  plus the previous publish — re-import the previous export.
