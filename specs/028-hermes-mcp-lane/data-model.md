# Data Model: Hermes Agent Lane (Phase 1)

All new state is host-side and session-scoped; the chatflow carries no new persistent entities. Existing entities (Message, GenerationState — spec 027) are untouched.

## 1. AllowedRoot (config + per-request)

| Attribute | Rule |
|---|---|
| default | `/mnt/c/temp` (config `hermes.allowed_root`) — the Windows `C:\temp` via the drive mount |
| per-request override | tool argument `allowed_root` — freely settable (clarify Q1: trusted single-user caller); when absent, config default applies |
| normalization | expanded and canonicalized by the gate before any comparison (drive-letter style accepted) |
| containment | every normalized target path must resolve inside the active root — checked at the tool boundary, no exceptions |

## 2. NormalizedPath (derived, per path token in a task)

Lifecycle: raw token from task text → normalize (drive map `C:\…` → `/mnt/c/…`, separators, case-insensitive drive, `~` expansion, relative anchoring) → resolve `..` → canonical string → containment compare. Windows-style output for answers is derived back (`/mnt/c/temp/x` → `C:\temp\x`) for display only — never for checks.

## 3. SafetyVerdict (per attempted operation)

```text
{ decision: "executed" | "blocked"
, reason: <user-readable, names the active root>   # set when blocked
, operation: "create-dir" | "write-file" | "read-file" | "list-dir" | "unsupported"
, normalized_path: <canonical path or null when no location was named>
}
```

- `unsupported` covers delete/rename/move/bulk (FR-011) and the no-location ask-back (FR-014) — both are `blocked` decisions with scope-naming reasons.
- The verdict is the ONLY signal that reaches Hermes: blocked verdicts never produce a Hermes call.

## 4. AuditEntry (host-side, append-only JSONL — FR-012)

```text
{ ts: <ISO 8601>
, decision: "executed" | "blocked"
, reason: <string | null>
, operation: <as above>
, normalized_path: <string | null>
, allowed_root: <active root>
, outcome: <result summary when executed | null>
}
```

- One entry per attempted operation, written by the sidecar tool at the single verdict point; executed entries are written post-completion with the outcome (FR-013 stop-truth); the lane never rewrites or prunes.
- Default file `~/.config/agentic-rag-mcp/hermes-mcp/audit.jsonl` (config `hermes.audit_path`); user data — never committed, never ingested.

## 5. HermesCall (per executed operation — stateless, R4)

`{ endpoint: POST /v1/responses, body: {input: <gated task>, instructions: <containment prompt>, store: false, model: "hermes-agent"}, auth: Bearer <config key>, timeout: 300 s }` — no session/conversation chaining; per-conversation isolation (FR-007) holds by statelessness.

## Validation rules (from requirements)

- FR-002/004: root override accepted per request; containment always against the active root.
- FR-006: the Hermes key lives in sidecar config only; never in DSL, answers, logs beyond redaction.
- FR-011: op-set is an allowlist — anything not create/write/read/list is `blocked` with the scope named.
- FR-014: a file-task with no resolvable location → ask-back reason; nothing created by assumption.
