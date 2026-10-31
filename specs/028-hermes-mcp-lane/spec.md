# Feature Specification: Hermes Agent Lane — Windows File Tasks via Local Agent

**Feature Branch**: `028-hermes-mcp-lane`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "install Hermes Agent as MCP Tool into Dify - AGI Assistant project" — extended by the design discussion: Hermes acts as a third agent lane (like the existing Q&A and deck lanes), so a prompt typed in the AGI Assistant chat can instruct the local Hermes agent to perform file operations on the user's Windows computer (e.g. `C:\temp`), with a security gate that confines every operation to an allowed root.

## Clarifications

### Session 2026-10-31

- Q: Should the allowed-root setting be changeable from the chat request, or is it locked to what the server configures? → A: Freely settable per request (trusted single-user model — the caller is the owner). Containment is always enforced against whichever root is active.
- Q: Which file operations should the lane be allowed to perform inside the active root — specifically, is deletion included? → A: Create/write/read/list only — no deletion in v1 (destructive prompts inside the root are declined with the scope named).
- Q: Should every operation the lane executes be recorded in a persistent audit log on the host? → A: Yes — an append-only host-side log records every attempted operation with timestamp, decision (executed/blocked), and path.
- Q: If you hit the Stop button while a Windows file task is mid-flight, what should happen to the operation running on your computer? → A: The visible answer stops as usual; the in-flight disk operation may complete and is recorded in the audit log either way — the answer never claims it didn't run.
- Q: When a file-task prompt names no location at all, where should the file go? → A: Nowhere yet — the assistant asks back for a location before doing anything; no file is created by assumption.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create files on the Windows disk from chat (Priority: P1)

As a chat user, I type a natural-language file task — e.g. *"Create a folder called hello_test in C:\temp, then create hello.txt inside it and write 'Hello World' into the file"* — and the assistant performs it on my Windows computer. The answer confirms what was created and where, using Windows-style paths, and I can verify it immediately in Windows Explorer.

**Why this priority**: This is the entire feature value — chat-driven file operations on the local Windows disk, with a result I can see with my own eyes.

**Independent Test**: Ask for the hello_test/hello.txt task, then open `C:\temp` in Windows Explorer and open the file.

**Acceptance Scenarios**:

1. **Given** I send a file-task prompt naming a folder/file under `C:\temp`, **When** the assistant answers, **Then** the folder and file exist on the Windows disk with the requested content, and the answer states the Windows-style path.
2. **Given** I ask to list or read files under `C:\temp`, **When** the assistant answers, **Then** the response reflects the actual current contents of the disk.
3. **Given** I type the path Windows-style (`C:\temp\foo`) or WSL-style (`/mnt/c/temp/foo`), **When** the task runs, **Then** both refer to the same location and both work.

---

### User Story 2 - Out-of-bounds prompts are blocked, never executed (Priority: P1)

As a chat user, any prompt that targets anything outside the allowed root — *"delete my entire home folder"*, *"wipe C:\"*, *".../../etc"*, *anything on `C:\Windows` or another drive* — must be refused with a clear reason and MUST NOT reach the local agent. The security gate runs on the request before any agent processing.

**Why this priority**: The lane executes real operations on the user's real computer. The gate is the only thing standing between a chat prompt and destructive action. It is co-equal with Story 1 — a lane that executes but cannot contain is a vulnerability, not a feature.

**Independent Test**: Send the block-matrix prompts (root paths, traversal sequences, other drives, system directories, obfuscated variants like `C:\temp\..\..\Windows`) — every one must be refused with the reason; nothing may be created, changed, or deleted anywhere.

**Acceptance Scenarios**:

1. **Given** a prompt naming an absolute path outside `C:\temp` (e.g. `C:\Users\x\Documents`, `D:\`, `~/`), **When** processed, **Then** the answer is the standard block message naming the allowed root, and no operation runs.
2. **Given** a path-traversal attempt (`C:\temp\..\..\Windows\System32`), **When** normalized and checked, **Then** it is identified as outside the allowed root and blocked.
3. **Given** a destructive command phrasing inside the allowed root (e.g. *"delete C:\temp\old_notes.txt"*), **When** processed, **Then** it is declined with the v1 scope named — the lane creates, writes, reads, and lists; it never deletes. Containment remains by location for every operation that does run.
4. **Given** a prompt that tries to smuggle a second instruction ("create x in C:\temp and also run powershell"), **When** processed, **Then** the out-of-scope instruction must not execute.

---

### User Story 3 - Windows program execution is explicitly out of scope (Priority: P2)

As a chat user, I understand the lane performs **file operations only** (create folders, write/read/list files) inside the allowed root. Launching Windows programs, running shell/PowerShell commands, or driving the Windows GUI are deliberately not part of this feature and must not be reachable through prompting.

**Why this priority**: The file-task lane is safely containable by a path rule; command execution is not. Drawing the boundary explicitly is what makes the feature shippable.

**Independent Test**: Prompt for "open notepad" / "run a PowerShell command" — the answer declines and restates the lane's file-only scope.

**Acceptance Scenarios**:

1. **Given** a prompt asking to launch or execute a Windows program, **When** processed, **Then** the assistant declines, stating that only file operations inside `C:\temp` are supported.
2. **Given** any prompt, **When** processed, **Then** no Windows process is started as a side effect of the file task.

---

## Edge Cases

- Path written with mixed separators (`C:\temp/foo\bar`) → normalized consistently before the check.
- Relative paths and `~` in a prompt → expanded and checked; anything resolving outside the allowed root is blocked.
- Trailing separators, casing (`c:\TEMP`), and spaces → normalized without surprising the user.
- Task referencing a file that already exists → the behavior is reported honestly (created vs. already present); nothing is silently overwritten without the answer saying so.
- The local agent service is down or unreachable → the answer reports the failure honestly (no fabricated success), with a hint to start it.
- A blocked prompt phrased as a question (*"can you delete C:\Windows?"*) → answered as blocked-with-reason, not executed.
- A file task with no location (*"create notes.txt with hello in it"*) → the assistant asks for the location; nothing is created by assumption (FR-014).
- The user stops the chat while a file task is executing → the answer stops, but the disk operation may finish; the audit log holds the truth, and a follow-up question about the state answers from the disk's actual contents.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Prompts recognized as local file tasks MUST route to the Hermes lane; all other prompts MUST keep today's behavior (question answering, deck generation) with zero regression.
- **FR-002**: The lane's allowed root defaults to `C:\temp` (reached through the host's Windows-drive mount) and MUST be configurable as a start input (`allowed_root`) that is freely settable per request — the trusted-caller is the owner (single-user deployment); the default applies when the UI sends nothing.
- **FR-003**: Path inputs in both Windows style (`C:\temp\…`) and host style (`/mnt/c/temp/…`) MUST be accepted and normalized to the same canonical form before the containment check.
- **FR-004**: The containment check MUST run before any agent processing and MUST always be enforced against whichever allowed root is active for the request: only operations whose target paths resolve inside that root reach the local agent; everything else is refused with a reason naming the active allowed root.
- **FR-005**: Blocked prompts MUST receive an honest refusal answer (blocked + reason); the refusal MUST NOT claim the operation ran.
- **FR-006**: The local agent endpoint MUST require a secret access key; it MUST accept only authenticated calls, and the key MUST never appear in chat answers, frontend code, or logs.
- **FR-007**: Each chat conversation MUST get its own isolated local-agent session (no cross-conversation state leakage).
- **FR-008**: Successful tasks MUST be reported with the resulting path in Windows style, so the user can verify the result in Windows Explorer.
- **FR-009**: Windows program execution, shell/PowerShell commands, and GUI automation MUST NOT be reachable via this lane, including via instruction smuggling inside an allowed prompt.
- **FR-010**: If the local agent is unavailable or errors, the answer MUST report the failure honestly with a recovery hint; the chat MUST remain usable for all other lanes.
- **FR-011**: In v1 the lane's executable operations are limited to creating folders and writing, reading, and listing files inside the active root. Deletion, renaming/moving, and bulk wipes MUST be refused with the v1 scope named — everywhere, including inside the root.
- **FR-012**: Every attempted operation MUST be recorded in an append-only host-side audit log with timestamp, decision (executed or blocked, with reason), and the normalized target path. Executed operations are recorded after completion with their outcome; blocked attempts are recorded as blocked. The log is never rewritten or pruned by the lane itself.
- **FR-013**: When a chat turn is stopped mid-task (existing stop feature), the visible answer stops as usual; an in-flight disk operation MAY complete on the host. The audit log MUST record the operation's actual outcome either way, and the lane MUST NOT later claim an operation did not run when the audit shows it did.
- **FR-014**: A file-task prompt that names a target file/folder but no location MUST trigger an ask-back: the assistant requests the location before executing anything, and MUST NOT create files by assuming a default location. Once the user answers with a location, the normal containment check applies to it.

## Success Criteria *(mandatory)*

- **SC-001**: A file-creation task in `C:\temp` answers and completes within 60 seconds, and the artifact is verifiable in Windows Explorer.
- **SC-002**: 100% of the block-matrix prompts (root paths, other drives, system directories, traversal sequences, smuggled instructions) are refused with a reason; zero out-of-root side effects.
- **SC-003**: Windows-style and host-style path inputs for the same target are treated identically in both execution and blocking decisions.
- **SC-004**: The existing deploy verification battery passes unchanged after the lane is added (no regression to the Q&A, deck, or stop lanes).
- **SC-005**: For every test prompt — executed or blocked — the audit log contains one entry with timestamp, decision, and path; the log shows no entry for operations that never ran.

## Key Entities

- **AllowedRoot**: the containment boundary (default `C:\temp`); a start-input override exists but the boundary itself is always enforced regardless of prompt phrasing.
- **NormalizedPath**: every path from a prompt is expanded (`~`, relative segments, mixed separators, drive-letter style) to one canonical host-side form before any decision is made.
- **SafetyVerdict**: the gate's decision — allowed (with the sanitized task) or blocked (with a user-readable reason).
- **AgentSession**: the local agent's per-conversation execution context; isolated per chat conversation and keyed by the conversation.

## Assumptions

- Hermes Agent remains installed and operational on the host, with its gateway running and a model configured; this feature wires it into the assistant, it does not (re)install it.
- The Windows `C:` drive remains mounted on the host (`/mnt/c`) and writable by the host user; `C:\temp` exists or may be created as the default allowed root.
- The existing chat UI is unchanged — the lane is reachable by typing a file-task prompt; the `allowed_root` start input defaults server-side.
- Single-user deployment: the chat platform, the assistant, and the Windows computer belong to the same person; the secret key plus path containment are the security model (no multi-tenant isolation).
- File operations means create/mkdir, write/read, and list **inside the active root**; deletion, rename/move, and bulk operations are out of scope for v1 (FR-011) — a follow-up version may add them as a deliberately tested extension.
- The local agent endpoint stays host-local (reachable from the chat platform's containers, not published to the internet).
