# Feature Specification: Deployment Automation — One-Command Stack Deploy & Verify

**Feature Branch**: `011-deploy-automation`

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "The requirement is full automation. Generally, common settings will follow your suggestions. You should ask user as few questions as possible." — in context: eliminate the remaining manual/user-side deployment steps (Dify chatflow import/publish, MCP tool-cache refresh, validation scenarios) so the whole stack deploys and verifies without human interaction.

**Existing contracts (Constitution I)**: all existing tool schemas, routes, and app behaviors are frozen — this feature wraps deployment operations around them; it changes no runtime contract.

**Driving constraint (user directive)**: defaults-first. Common settings follow recommended defaults recorded in the Assumptions section; the system must not ask questions during execution.

## Clarifications

### Session 2026-10-19

- Q: Should the automation also perform the initial MCP-server registration in Dify (the one-time "Add Server" step), or only handle already-registered servers? → A: **Option A — full lifecycle**: the automation registers the MCP server if absent (documented name and URL) and re-syncs the tool cache if present — a fresh host needs zero Dify UI actions.
- Q (folded defaults, no user question needed): the verification battery cleans up its own test decks (unique project names + teardown — no accumulation); and the battery includes a Chat-UI liveness check (HTTP only, no process management).

## User Scenarios & Testing *(mandatory)*

### User Story 1 — One-Command Stack Redeploy (Priority: P1)

An operator (or an agent acting for one) changes the code and wants the running stack updated: one command rebuilds the sidecar image, recreates the container with the correct mounts and networks, and re-syncs Dify's MCP tool cache so new tools appear immediately — no manual Update clicks, no hand-typed docker commands.

**Why this priority**: This is the mechanical half of full automation — everything after "code changed" until "stack serves the new code" happens unattended.

**Independent Test**: run the command after a tool-count change; `tools/list` reflects the new count and Dify's tool cache matches it, without any UI action.

**Acceptance Scenarios**:

1. **Given** code changes in the sidecar source, **When** the redeploy command runs, **Then** the image is rebuilt, the container is recreated with the documented mounts and networks, and health checks pass.
2. **Given** the MCP tool set changed (tools added or renamed), **When** the redeploy command runs, **Then** Dify's cached tool list is re-synced to match the live server (working around the known platform update-path limitation), verified by comparing the cached list to the served list.
3. **Given** a Dify workspace where the MCP server has never been registered, **When** the redeploy command runs, **Then** the server is registered with the documented name and URL, and its tools appear in Dify — no UI action required.
4. **Given** a healthy, already-current stack, **When** the redeploy command runs again, **Then** it completes without destructive side effects (idempotent).

---

### User Story 2 — One-Command Dify Chatflow Update (Priority: P1)

The chatflow DSL or agent rulebook changes; one command imports (or updates) the app in Dify from the repo's DSL file and publishes it, using stored console credentials — no browser, no UI walkthrough.

**Why this priority**: The chatflow import/publish was the single recurring manual step left after specs 009/010.

**Independent Test**: modify a comment in the DSL, run the command, then call the app's chat service and confirm the published version answers with the new behavior.

**Acceptance Scenarios**:

1. **Given** valid stored console credentials and the repo's chatflow DSL, **When** the chatflow-update command runs, **Then** the app is created or updated in Dify and published, without any UI interaction.
2. **Given** an app with the same name already exists, **When** the command runs, **Then** the existing app is updated rather than duplicated (or the collision is resolved by the documented default), and the outcome is reported honestly.
3. **Given** missing or invalid credentials, **When** the command runs, **Then** it fails fast with a precise setup instruction — never a partial, silent, or destructive result.

---

### User Story 3 — One-Command Verification Battery (Priority: P1)

One command runs every scriptable end-to-end check unattended: server health, tool surface, the full deck round trip (init → write → check → export), completion-page and download routes, honest error responses, and a real chat-level round trip (send a deck prompt through the chatflow's service API and verify the answer contains a working link). Each scenario reports pass/fail with evidence.

**Why this priority**: This replaces the manual browser scenarios that closed specs 009/010 — full automation means the machine verifies itself.

**Independent Test**: run the battery against a freshly deployed stack; every scenario passes with no human input.

**Acceptance Scenarios**:

1. **Given** a deployed stack, **When** the verification command runs, **Then** every scriptable quickstart scenario executes headlessly and reports per-scenario pass/fail with evidence (HTTP codes, artifact paths, answer fragments).
2. **Given** the chatflow's service credentials, **When** the battery sends a real deck-generation prompt, **Then** it receives a streamed answer, extracts the deck link, and verifies the link serves the completion page and the file.
3. **Given** any failing scenario, **When** the battery completes, **Then** the failure is reported with the specific step, expected vs actual, and a nonzero exit code — no silent skips.

---

### User Story 4 — Honest, Quiet Automation (Priority: P2)

The automation reports clearly (one summary, per-step outcomes, failures first) and never asks questions mid-run: all configuration is read from files/environment before the run, with recommended defaults.

**Why this priority**: The user directive — common settings follow recommendations; ask nothing during execution.

**Independent Test**: run the full pipeline with default configuration only; zero interactive prompts appear; the run's configuration is echoed at start.

**Acceptance Scenarios**:

1. **Given** default configuration, **When** any automation command runs, **Then** it executes start-to-finish with no interactive prompt and prints a final summary.
2. **Given** a platform-version-specific workaround (e.g. the tool-cache re-sync path tied to a Dify version range), **When** the automation detects an unsupported version, **Then** it reports the limitation honestly and continues with the supported path or fails with instructions.

---

### Edge Cases

- Dify version drift makes the tool-cache workaround inapplicable — detect and degrade honestly (report; skip only that step with an explicit notice).
- Console credentials expired/rotated mid-pipeline — fail fast at the step that needs them with renewal instructions.
- The chatflow import collides with an existing app name — documented default: update in place; never delete other apps.
- An MCP-server registration already exists with a different name or URL — the automation reports the discrepancy and updates in place per its documented defaults; it never creates a duplicate server entry.
- Verification artifacts from a crashed battery run — unique project naming plus a best-effort sweep on the next run; leftovers are reported, never silently ignored.
- The sidecar is mid-restart when verification starts — the battery waits for readiness with a bounded timeout, then fails honestly if it never comes up.
- A deck-generation chat prompt exceeds the run's patience budget — the battery reports a timeout with partial evidence, never fabricates success.
- Concurrent automation runs — a lock or lock-free idempotency keeps two runs from corrupting the tool cache or duplicate-importing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a single command that rebuilds and redeploys the sidecar (image build, container recreation with documented mounts/networks, health wait) from the current source.
- **FR-002**: The system MUST provide a single command that ensures the MCP server is registered in Dify — registering it with the documented name and URL when absent, and re-syncing the cached tool list to match the live server when present — using the platform-version-appropriate path, and MUST report the before/after tool counts (or the registration outcome on first run).
- **FR-003**: The system MUST provide a single command that imports or updates the chatflow app from the repo's DSL file and publishes it, using stored console credentials.
- **FR-004**: The system MUST provide a single command that executes the full headless verification battery — health, tool surface, deck round trip, completion-page and download routes, honest-error checks, Chat-UI liveness, and a real chat-level deck prompt through the chatflow's service API — reporting per-scenario pass/fail with evidence and a nonzero exit on any failure.
- **FR-005**: The chat-level verification MUST prove the end-to-end user journey without a browser: prompt in → answer contains a deck link → the link serves the completion experience → the file downloads.
- **FR-006**: All credentials MUST be supplied via configuration or environment, never committed to the repository, and the automation MUST fail fast with setup instructions when they are absent or invalid.
- **FR-007**: Every command MUST be non-interactive: no prompts during execution; the effective configuration is reported at start; recommended defaults apply for anything unset.
- **FR-008**: All commands MUST be idempotent — a second run on an up-to-date stack makes no destructive changes (no app deletion, no container churn beyond what redeploy inherently does, no duplicate imports or registrations).
- **FR-009**: Failures MUST be honest and specific: the failing step, expected vs actual, and remediation guidance — never partial success reported as success.
- **FR-010**: The automation MUST keep the platform-version-specific workaround paths detectable and replaceable (version detection with honest degradation), not silently version-coupled.
- **FR-011**: The verification battery MUST clean up its own test artifacts (uniquely named projects, removed on completion) so repeated runs never accumulate decks or projects.

### Key Entities

- **Deployment Run**: one execution of a command (steps, outcomes, timing); reported as a summary.
- **Verification Scenario**: one named headless check (id, action, expected, actual, pass/fail) — the battery's unit.
- **Console Credential**: Dify console identity (email + secret) supplied via config/environment; never persisted in the repo.
- **Tool Cache Snapshot**: the before/after view of Dify's cached MCP tool list around a re-sync.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A code change reaches a fully deployed, published, verified stack via a single command sequence with zero interactive prompts and zero UI actions.
- **SC-002**: 100% of the scriptable quickstart scenarios across the deployed features run headlessly in the battery, each with a pass/fail verdict and evidence.
- **SC-003**: The chat-level round trip (real deck prompt → answer link → page serves → file downloads) verifies without a browser in ≥ 95% of runs on a healthy stack (remainder = honest timeouts with evidence, never false success).
- **SC-004**: A redeploy after a tool-count change reflects the new tool count in Dify's cache within the same command, with before/after counts reported.
- **SC-005**: No credential ever appears in the repository or in command logs; the battery's output redacts secrets.

## Assumptions

*(defaults chosen per the user directive: common settings follow recommendations; no clarifying questions)*

- Dify console credentials are supplied as environment variables or a gitignored config file; the operator sets them once.
- The tool-cache re-sync uses the database path validated during spec 009 deployment (the platform's Update flow is known-broken for tool re-sync in 1.17); version detection chooses the path and reports which one it took.
- Chat-level verification uses the existing chatflow service API key already used by the Chat UI.
- The automation is an operator/agent-run command-line tool in the repository (not a new MCP tool, not a new runtime service — Constitution III).
- The verification battery includes a Chat-UI liveness check (HTTP reachability only) but does not start, stop, or manage the Chat UI process.
- Chatflow updates are in-place for an existing app of the same name; nothing else is deleted.
- Browser-only visual checks (theme, pixel layout) remain out of scope; everything else is automated.
- The single-user, local-trust deployment posture carries over; the automation runs on the host.
