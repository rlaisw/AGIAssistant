# Research: Apply Selected LLM to the Chatflow (Patch-on-Select)

Phase 0 output. All NEEDS CLARIFICATION items were resolved in the two
clarify passes (cloud-only patch; sends blocked during the cycle); the
decisions below translate them into a technical approach.

## D1 — Where the cycle runs

**Decision**: the spec-011 deploy CLI gains `apply-model <model_id>`:
`model_apply.py` performs export → patch → overwrite → publish via the
console API session (`DifyConsole`, proven today for draft update +
publish). The Chat UI's new `POST /api/models/apply` spawns it and awaits
the result (≤90 s budget, matching SC-001).

**Rationale**: the deploy CLI already owns console auth and the publish
path; the user's prescribed steps map one-to-one onto it. The published
app is untouched until the publish step (draft overwrite only affects the
draft), which gives FR-004's "previous config keeps serving" for free.

**Alternatives**: (a) shell out to difyctl per the reference script —
rejected: difyctl's login state lives outside the deploy CLI's config
(fragile automation), while the console session is proven; the script
remains the documented manual equivalent; (b) doing it in TypeScript in
the Next.js route — rejected: YAML patch + console auth belong to the
Python ops layer (house layering, Principle III).

## D2 — The patch step (and the FR-005 cleanup)

**Decision**: one idempotent transformation on the exported YAML: set the
model of the three main nodes (`intent_router`, `agentic_strategy`,
`ppt_master` — matched by stable node id, not title) to the selected
cloud model (provider `langgenius/openrouter/openrouter`,
`completion_params: {}`), and remove the routing-era artifacts: the nine
`*_kimi/_glm/_qwen38` nodes, their edges, the router's `kimi/glm/qwen38`
cases, and the `cloud_model` start variable. Re-runs are no-ops.

**Rationale**: node ids are stable (titles are cosmetic); a single
transformation keeps the artifact canonical and the cycle deterministic.

**Alternatives**: keeping the extra branches as unused scaffolding —
rejected (Principle V, dead paths).

## D3 — Console mechanics per step

**Decision**: export via `GET /apps/{id}/export?include_secret=false`
(new `DifyConsole.export_app`) → write the artifact → patch →
`update_workflow_draft` (the proven console-API overwrite for chatflow
apps — replaces the draft wholesale, equivalent to the user's "OVERWRITE
import" for this app type) → existing `publish`. The draft-hash guard
behavior (concurrent-edit abort) is preserved by failing the cycle on
any console error and reporting honestly.

**Rationale**: each step is already proven in this session (draft update
+ publish) except the export endpoint, which is read-only.

**Alternatives**: `POST /apps/imports` (full-app import) — heavier
semantics than needed for advanced-chat workflow updates; noted as the
difyctl-equivalent fallback if draft update ever regresses.

## D4 — Selection state after patching (server truth)

**Decision**: the configured cloud model is read from the artifact on
load: new `GET /api/models/current` parses the three main nodes' model
from `dify/AGIAssistant/AGI_Assistant.yml` (falls back to the Deepseek
default when unreadable — and reports honestly rather than guessing a
different model). The dropdown shows: local if the per-conversation
stored selection is `"local"`, else the configured cloud model. Stored
cloud selections from the routing era are superseded (display-only
provenance). On apply success the UI stores the applied id as the
selection (ids unchanged from spec 025).

**Rationale**: the published app is the source of truth after patching;
the artifact is its honest mirror (FR-007) and cheap to parse
(server-side, never browser-exposed beyond the resolved id).

**Alternatives**: querying the live draft via console API on every load —
slower, needs console auth in the hot path; the artifact suffices.

**Resolution note (2026-10-26)**: the resolver searches **backward** from
the node id, not forward — `yaml.dump` sorts keys alphabetically, so a
node's `model:` line precedes its `id:` line. Implementation:
`app/api/models/current/route.ts`.

## D5 — Applying state and send gating (FR-003)

**Decision**: `applyingModel: ModelId | null` in page state. While set:
send button and Enter are disabled, the composer shows "Applying
<displayName>…" with the existing spinner style, and the dropdown is
inert. Cleared on completion (success or failure).

**Rationale**: the user's decision (blocked sends) maps onto the existing
busy-gate pattern; no new UI machinery.

## D6 — Fallback badge after global patching

**Decision**: badge map values gain a `"<model-id>|fallback"` form (e.g.
`"moonshotai/kimi-k3|fallback"`): the badge names the model that actually
served (the globally configured cloud model at send time) and the note
reads "Local model unavailable — answered by the cloud model instead."
`badgeModel` strips the suffix; `badgeNote` detects it; legacy
`"cloud-fallback"` still renders (badge = Deepseek default, which was
correct when written).

**Rationale**: the fallback target is the globally configured model
(assumption from clarify pass 2), so the hardcoded Deepseek resolution
would misattribute replies after a Kimi apply — provenance must follow
the actual serving id (Principle IV).

**Alternatives**: keep `"cloud-fallback"` and resolve at render time to
the CURRENT config — rejected: provenance would rewrite history when the
config later changes.

## D7 — Local model path (unchanged)

**Decision**: local keeps the spec-025 routed branch entirely: selection
`"local"` stays per-conversation in localStorage, sends carry
`ai_model: "local"`, the availability probe and instant fallback stay.
The chat route drops the `cloud_model` passthrough (superseded): cloud
sends carry no model input and hit the else branch = the configured
model.

**Rationale**: decision B from clarify — proven behavior, no republish
for local availability failures.
