# Contract: hermes_file_task MCP Tool (spec 028)

The feature adds **one** MCP tool to the sidecar's existing tool surface (Constitution I: all existing tools byte-identical). The chatflow consumes it from a new Hermes Agent node; no Dify-side code, plugins, or custom tools are involved.

## 1. Tool schema

```ts
hermes_file_task(task: string, allowed_root?: string) -> {
  status: "ok" | "blocked" | "error"
, decision?: "executed" | "blocked"            // present for ok/blocked
, result?: string                              // Hermes' final output, present when ok
, reason?: string                              // blocked/error explanation (names the active root)
, windows_path?: string                        // display form of the affected path, when applicable
}
```

## 2. Gate pipeline (invariants, in order)

1. **Normalize** every path token in `task`: Windows drive style (`C:\…`, `c:/…`) → `/mnt/<drive>/…`; `~`/`$HOME` expansion; relative → anchored; mixed/trailing separators; case-insensitive drive letters.
2. **Resolve** `..` segments on the normalized form; containment compare **after** resolution (never on raw text).
3. **Active root** = `allowed_root` argument when present, else config default `/mnt/c/temp` (freely settable — clarify Q1; containment always against the active root, FR-004).
4. **Op-set allowlist** (FR-011): `create-dir`, `write-file`, `read-file`, `list-dir` only. Delete/rename/move/bulk → `blocked` with the v1 scope named — everywhere, including inside the root.
5. **No-location** (FR-014): a file task whose target cannot be resolved to any location → `blocked` with an ask-back reason; the gate never assumes a default location.
6. **Audit**: exactly one `AuditEntry` written per attempt at the verdict point (FR-012) — executed entries post-completion with outcome (FR-013), blocked entries with reason.

## 3. Execution contract (executed verdicts only)

- `POST {hermes.api_url}/v1/responses`, Bearer `{hermes.api_key}`, body `{input: <gated task>, instructions: <containment system prompt>, store: false, model: "hermes-agent"}`, timeout `hermes.timeout_s` (default 300).
- **Stateless** (R4): no `conversation`/`previous_response_id` chaining — per-conversation isolation (FR-007) holds by construction; the Dify agent supplies full context in `input`.
- Non-200 / timeout / connection failure → `status:"error"` with an honest reason + recovery hint (FR-010); **never** a fabricated result. Errors still write their audit entry (decision `blocked`? No — failed attempts record `blocked` with reason `error:<…>`; the log never claims execution that did not complete).

## 4. Honest-envelope invariants (Constitution IV)

- `ok` implies Hermes returned and the audit entry has an outcome.
- `blocked` implies nothing reached Hermes and nothing changed on disk.
- `error` implies no fabricated success; the recovery hint names the likely cause (gateway down → start command; key rejected → config; timeout → retry smaller task).
- Blocked/error reasons always name the **active** allowed root and (for FR-011/014) the v1 scope.

## 5. Chatflow wiring (DSL, established pipeline)

- `intent_router` (question-classifier) gains a third class: local file task (examples in classifier prompt: "create a folder in C:\temp…", "list files in C:\temp", "write a file on my computer…").
- New **Hermes Agent** node: function-calling strategy, existing cloud model, tools = `[hermes_file_task]`; instructions state the lane's scope (file operations inside the active root via the tool; file-only — never claim direct disk access) and the honest-relay rule (report the tool's verdict verbatim, including blocked reasons and ask-backs).
- Answers merge into the shared answer nodes as the other lanes do; classifier regression covered by the battery.
