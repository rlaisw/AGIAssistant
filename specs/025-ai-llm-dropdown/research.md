# Research: "AI LLM" Model Drop-Down Menu

Phase 0 output. All NEEDS CLARIFICATION items were resolved during the two
clarify passes (see spec Clarifications); the decisions below translate them
into a technical approach. Format per decision: Decision / Rationale /
Alternatives considered.

## D1 — How the choice reaches the chatflow

**Decision**: additive start-variable `ai_model` ("cloud" | "local",
default "cloud") sent per message in `inputs`; a new IF/ELSE node
(`model_router`) after `start` routes to either the existing cloud LLM nodes
or local copies (`intent_router_local`, `agentic_strategy_local`,
`ppt_master_local`). Answer nodes (`answer`, `ppt_answer`) are shared and
receive edges from both branches.

**Rationale**: Dify agent/question-classifier nodes have fixed per-node
model selectors — per-request model templating is not expressible in the
DSL, so a variable-gated dual-branch graph is the only declarative way to
switch per message. Shared answer nodes keep the graph minimal (6 LLM-ish
nodes total, not 10).

**Alternatives**: (a) patching the draft chatflow's node models per request
— rejected: the published app is stateless/shared, race-prone, breaks
contract stability; (b) two separate Dify apps and switching API keys —
rejected: duplicates the chatflow, splits conversation history and the
deploy surface for zero benefit.

## D2 — Local model registration in Dify

**Decision**: register Ollama as a Dify model provider pointing at the
host's bridge address `http://172.17.0.1:11434` (docker0 gateway; Ollama
already binds 0.0.0.0). Automate the one-time provider setup inside the
spec-011 deploy CLI next to chatflow publish (console API session already
exists there).

**Rationale**: Dify's containers reach host services via the compose
network's gateway; the deploy CLI already authenticates to the console
(password + CSRF patterns known), keeping DEPLOY.md one-command.

**Alternatives**: manual console click-ops documented in DEPLOY.md —
rejected (violates spec-011 automation posture); `host.docker.internal`
extra-hosts compose change — viable fallback if the gateway IP differs,
one-line compose override.

## D3 — Thinking disabled for Local (FR-009)

**Decision**: create a derived no-think model on the host:
`ollama create qwen3-8b-nothink` from a Modelfile (`FROM qwen3:8b` +
`PARAMETER think false` — supported by installed Ollama ≥ 0.9; verify the
parameter name at implementation, `ollama show --modelfile` is the check).
The local Dify nodes reference `qwen3-8b-nothink`.

**Rationale**: disabling thinking at the model level is the only option
that shortens the CPU-bound wait; it also needs no UI work and no hidden
text (Principle IV).

**Alternatives**: (a) render thinking in a collapsible block — rejected
(doubles the wait, new rendering UI); (b) `/no_think` soft switch appended
to each local node's system prompt — fallback if the Modelfile parameter
is unsupported by the installed runtime; (c) Dify provider-side think
toggle — verify availability at implementation, use if exposed.

## D4 — Selection persistence (FR-003) and badges (FR-008)

**Decision**: browser localStorage — `agi-model:selection:<conversationId>`
holds "cloud"|"local"; `agi-model:badge:<conversationId>` maps messageId →
model, written at stream time. Absence of either entry resolves to "cloud"
(the FR-008 backfill: all pre-feature replies were cloud-served). Both keys
are purged when a conversation is deleted (delete feature hook).

**Rationale**: Dify exposes no per-conversation custom metadata or
per-message model attribution, so the client is the only place the choice
and per-message provenance can live without a new server service (Principle
III). Absence→cloud is historically accurate, not a guess.

**Alternatives**: (a) server-side store in the sidecar — rejected: new
runtime surface for data the browser already owns; (b) derive badges from
`inputs` echoed by Dify — rejected: Dify does not persist per-message
inputs retrievably for advanced-chat history.

## D5 — Availability probing (FR-004, SC-002)

**Decision**: new Chat UI route `GET /api/models` probes Ollama
`/api/tags` on `127.0.0.1:11434` with a 2 s timeout and returns both
options: cloud `{available: true}` always (local-only status, clarify
decision), local `{available: <reachable && model present>}`. The dropdown
fetches on open (5 s budget, SC-002). The probe also runs at send-time when
Local is selected.

**Rationale**: the browser cannot know the host address of Ollama, and the
address must not leak to the client; the Next.js server runs on the same
host so 127.0.0.1 is correct. Send-time re-probe makes FR-004's reset
possible even if the server died after the dropdown was opened.

**Alternatives**: periodic background polling — rejected (wasted traffic,
stale anyway at send time); direct browser fetch to LAN IP — rejected
(address leak, brittle).

## D6 — Fallback + failure behavior (FR-004/FR-007)

**Decision**: send-time probe fails while Local selected → the UI inserts
an inline persistent system note, flips the stored selection to "cloud",
and sends with `ai_model: "cloud"`. Mid-stream local failure → normal
message error state, stored selection resets to "cloud" (same rule, one
code path).

**Rationale**: one reset rule for every local-failure mode keeps the state
machine honest and testable; the note persists so history never contradicts
the drop-down.

**Alternatives**: queue-and-retry on Local — rejected (hidden behavior);
auto-resume when Local returns — explicitly rejected by the user (Reset
decision, Option A).

## Test Design (per plan request)

Vitest units in `lib/models/*.test.ts`, written before implementation:

- **selection**: single-select invariant (select one → exactly one
  active); user switch applies next message; reset-on-unavailable (FR-004)
  including send-time and mid-stream triggers; new conversation → cloud.
- **badge**: map hit → that model; map miss → cloud (backfill); map entry
  written at stream completion; switch mid-conversation leaves earlier
  entries untouched.
- **availability**: probe success/timeout/malformed body/HTTP error →
  correct `available` value, ≤5 s budget honored (fake timers).
- **persistence**: get/set round-trip; absent key → "cloud"; conversation
  delete purges both keys.
- **api/models route**: unit-test the handler with stubbed fetch —
  reachable+model-present, reachable+missing model, connection refused.

Live/acceptance (CDP throwaway conversations, created then deleted):

- SC-001 switch-and-badge; SC-002 stopped-Ollama unavailable ≤5 s + cloud
  continues; SC-003 reload/resume keeps selection; FR-009 local reply
  carries no reasoning block.
- Error cases replayed live: kill Ollama mid-stream → message error +
  selection reset; delete conversation → storage keys purged.

Regression: `pnpm typecheck && pnpm lint`, full vitest suite, deploy
battery unchanged (cloud-only by design — clarify decision).

## Error Handling Matrix (per plan request)

| # | Failure | Detection | Behavior | Requirement |
|---|---------|-----------|----------|-------------|
| 1 | Ollama down when dropdown opens | `/api/models` probe (2 s timeout) | Local marked unavailable, unselectable | FR-004 |
| 2 | Ollama down at send with Local selected | send-time probe | Inline persistent note; selection resets to cloud; message sent as cloud | FR-004 |
| 3 | Ollama dies mid-stream | stream error | Standard message error; selection resets to cloud; badge/absence rules unchanged | FR-007 |
| 4 | Probe times out / malformed / HTTP error | probe client | Same as down — degrade to `available: false` (never guess) | FR-004 |
| 5 | `qwen3-8b-nothink` missing from Ollama | probe model-presence check | Local unavailable even if server reachable | FR-004 |
| 6 | Cloud outage | existing stream error path | Unchanged per-message error; drop-down does not probe cloud | Clarify A |
| 7 | localStorage unavailable (private mode) | try/catch on access | Selection treated as cloud each time; badges fall back to cloud; chat still works | FR-003/008 |
| 8 | Dify rejects `inputs.ai_model` (stale published app) | chat API error | Surface as normal send error; UI keeps local selection visible | FR-005 |
