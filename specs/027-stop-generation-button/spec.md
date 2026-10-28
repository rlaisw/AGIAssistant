# Feature Specification: Stop Generation Button

**Feature Branch**: `027-stop-generation-button`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "add a \"Stop\" button, shows the \"Stop\" button when the AGIAssistant is thinking/running. thus lets user can stop the thinking process"

## Clarifications

### Session 2026-10-28

- Q: While the assistant is generating, how should the Stop control appear relative to the send button? → A: The send button morphs into the Stop control during generation; sending a new question is disabled until the answer stops or completes.
- Q: After a stop lands mid-answer, should the kept partial answer visibly carry a marker showing it was stopped by the user? → A: Yes — a short caption under the partial answer (e.g., "Stopped") marks the turn as user-stopped.
- Q: Should acceptance testing verify that a stop actually halts generation on the service side? → A: Yes — the acceptance battery verifies that no further answer content is generated after a user stop; backend halting is a verified behavior, not an unverified best effort.
- Q: If you switch to a different conversation while an answer is still generating, what happens to the in-flight answer? → A: It continues in the background and keeps updating its own conversation; the Stop control appears only while viewing the conversation that is generating.
- Q: After a page reload or reopening the conversation from history, should the stopped answer still carry its "Stopped" caption? → A: No — the caption is session-only (survives switching conversations, not a reload); the partial transcript itself is the durable record.
- Q: When a stop lands mid-answer, should the reasoning (thinking) content that already streamed stay visible in the reasoning panel? → A: Yes — it stays visible, frozen as-is (no further updates); nothing already received is retracted.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop an in-progress answer (Priority: P1)

As a chat user, when the assistant is thinking or streaming an answer, the send button in the input area becomes a **Stop** control. Clicking it halts the in-progress response immediately: whatever text has already arrived stays in the conversation, the progress indicator disappears, and the input box is ready for my next message.

**Why this priority**: This is the entire feature value — user control over a long, wrong, or unwanted generation. Everything else exists to make this stop trustworthy and clean.

**Independent Test**: Start any question, click Stop mid-answer, and verify the partial text remains and I can immediately ask a follow-up question.

**Acceptance Scenarios**:

1. **Given** the assistant is thinking (no answer text yet), **When** I click Stop, **Then** the thinking indicator stops, the conversation shows no stuck progress state, and I can type and send a new message right away.
2. **Given** the answer is partially streamed (some paragraphs visible), **When** I click Stop, **Then** the visible partial text remains in the chat, streaming stops, and no further text appears for that turn.
3. **Given** the assistant is idle (no generation running), **When** I look at the input area, **Then** no Stop control is shown.

---

### User Story 2 - Stopped turn stays honest and usable (Priority: P2)

As a chat user, after I stop an answer, the conversation must not look broken or lie about what happened: the stopped turn is visually terminated (no lingering spinner, no pretense that the answer completed normally), and the conversation remains fully usable — I can send the next question, reload and resume it from history, and export it.

**Why this priority**: A stop that strands the UI (stuck spinner, dead composer) or corrupts the conversation is worse than no stop button. This story makes the P1 story trustworthy.

**Independent Test**: Stop an answer, then (a) send another question in the same conversation, (b) reload the page and resume the conversation from history, (c) export the conversation — all three must work.

**Acceptance Scenarios**:

1. **Given** an answer was just stopped, **When** I send a new question in the same conversation, **Then** it answers normally with full features (reasoning panel, sources, citations).
2. **Given** an answer was stopped in a past turn, **When** I reload and resume that conversation from history, **Then** the stopped turn's partial text is present and the conversation continues normally.
3. **Given** a conversation contains a stopped turn, **When** I export it or use any existing conversation feature (delete, search, PDF export), **Then** those features behave exactly as before this feature existed.

---

### User Story 3 - Stop behaves sanely at the boundaries (Priority: P3)

As a chat user, my stop interactions must be safe at the edges: stopping before any text arrives, double-clicking Stop, or stopping exactly as the answer completes naturally must all end in a consistent, non-broken state — and stopping my chat response must never corrupt related artifacts (e.g., a deck export link that already finished).

**Why this priority**: Edge behavior is what separates a demo from a dependable control. It cannot ship broken, but it does not define the feature's value the way P1 does.

**Independent Test**: Run the edge-case matrix (stop during thinking, stop mid-stream twice in a row, stop at natural completion, stop then immediately resend) and confirm no state ends stuck or inconsistent.

**Acceptance Scenarios**:

1. **Given** Stop is clicked twice in quick succession, **When** the second click lands, **Then** it is treated as a no-op (no error, no double state change).
2. **Given** the answer completes naturally at the same moment I click Stop, **When** the click is processed, **Then** the conversation ends in the completed state with no errors (the race resolves to either outcome, never a broken one).
3. **Given** a stopped answer already produced a side artifact earlier in the turn (e.g., a deck download link), **When** I stop the remaining answer, **Then** the artifact link and everything before the stop point remain usable.

---

### Edge Cases

- What happens when Stop is clicked during the thinking phase before any answer text arrives? → The turn ends with a visibly stopped state and no fabricated empty answer (no blank assistant bubble pretending to be a response).
- What happens when the user stops and immediately sends a new question? → The new question is accepted and answered; the stopped turn is never resumed or duplicated.
- What happens if the network connection drops mid-generation (a failure, not a user stop)? → The existing watchdog/error behavior governs; the Stop control must not appear stuck or break that path.
- What happens when the user switches to another conversation mid-generation? → Nothing is disturbed: the in-flight answer continues in the background and its conversation keeps updating; the Stop control appears only when the generating conversation is being viewed (FR-010).
- What happens on a very short answer (finishes before the user can click)? → The control disappears on completion; the turn is complete, not stopped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: While a response is being generated for the active conversation (thinking or streaming), the composer's primary control MUST become a clearly labeled "Stop" control (the send control morphs into Stop), reachable without scrolling, and sending a new question MUST be disabled until the generation stops or completes.
- **FR-002**: The system MUST NOT show the Stop control when no generation is in progress, and MUST remove it (returning the input area to its normal state) when the generation ends — whether by stop or natural completion.
- **FR-003**: Activating Stop MUST halt the visible response within one second (user-perceived: input area returns to ready state in that window).
- **FR-004**: Stopping MUST preserve every piece of content that already arrived before the stop — the partial answer text and the reasoning (thinking) content already streamed, which remains visible in the reasoning panel, frozen as-is; nothing received is blanked or retracted.
- **FR-005**: After a stop, the conversation MUST return to full input-ready state: composer enabled, no residual progress indicator, no stuck "thinking" state.
- **FR-006**: A stop MUST end the generation work on the service side as well, not merely on the user's screen: after a user stop, no further answer content is generated for that turn. This halting is a verified acceptance-battery behavior, not an assumed one. If the backend cancellation path is momentarily unavailable, the visible response still stops cleanly (the turn is marked stopped and the UI returns to ready), and the failed backend halt surfaces as an acceptance defect.
- **FR-007**: The system MUST NOT present a stopped answer as if it had completed normally: the stopped partial answer carries a short visible caption (e.g., "Stopped") marking it as user-stopped, and no completion indicators (e.g., finished-source badges) appear after the stop point. The caption is a live-session affordance — it survives switching conversations but is not shown after a page reload; the partial transcript itself is the durable record.
- **FR-008**: A stopped conversation MUST remain fully compatible with all existing conversation features (follow-up questions, history resume, delete, search, PDF export) with no behavior regressions.
- **FR-009**: Rapid or repeated Stop activations MUST be safe: subsequent activations after the first are treated as no-ops, with no errors and no duplicated state changes.
- **FR-010**: Switching to a different conversation during generation MUST NOT disturb the in-flight answer: it continues and updates its own conversation. The Stop control (per FR-001) is shown only while viewing a conversation that is actively generating; viewing another conversation shows the normal ready composer.

### Key Entities

- **Generation State** (per active turn): the lifecycle of one assistant response — `running` (thinking or streaming), `stopped` (user-aborted), `complete` (finished naturally), plus the existing error state. The Stop control is visible only while `running`; the state after any stop is `stopped`, which renders and behaves identically to `complete` except for FR-007's honest-termination rule.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In every manual stop attempt, the input area returns to ready state within 1 second of the Stop click.
- **SC-002**: In 100% of stopped conversations, a follow-up question can be asked immediately after the stop, and the conversation resumes correctly from history after a page reload.
- **SC-003**: No stop ever loses already-received answer text (verified across the edge-case matrix: thinking-phase stop, mid-stream stop, double-click, completion race).
- **SC-004**: A user who has never seen the feature can find and use the Stop control within 5 seconds of their first in-progress answer, without instruction.
- **SC-005**: In every acceptance-battery stop scenario, no further answer content is generated after the stop takes effect.

## Assumptions

- "Thinking/running" is the same state that already drives the existing thinking indicator (spec 022); the Stop control's visibility reuses that state source rather than inventing a parallel one.
- The chat backend offers a way to cancel an in-progress generation and the UI uses it; backend halting is verified by the acceptance battery (FR-006). If cancellation is momentarily unavailable, the visible response still stops cleanly and the failure is reported as an acceptance defect.
- A stop during the thinking phase (no text yet) ends the turn without an empty assistant message; the user simply sees the conversation return to ready state.
- Scope is the chat conversation surface of the AGI Assistant web UI (desktop and its responsive mobile layout); stopping background jobs unrelated to the visible answer (e.g., an already-completed deck export) is out of scope.
- The control is labeled "Stop" in English, matching the UI's current language.
- Existing conversation behaviors (history, resume, delete, search, PDF export) are regression-scope for this feature; no new conversation data is introduced beyond the generation state.
