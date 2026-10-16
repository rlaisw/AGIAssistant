# Feature Specification: OneDrive On-Demand Embedding with Staleness Reminder

**Feature Branch**: `007-onedrive-on-demand`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "Revise one-drive files source design. Based on the last conversation, use one-drive on-demand update embedding + staleness reminder (prompt user with reminder, not auto-download)."

**Supersedes**: The automatic-sync design of `specs/006-onedrive-ingestion` (initial full sync, post-auth sync, 5-minute watcher polling, delta-link continuous sync). Per Constitution V, the superseded code paths are deleted, not deprecated; the client contract is preserved field-for-field (Constitution I).

## Clarifications

### Session 2026-10-11

- Q: Should OneDrive files be synced automatically like local files? → A: **No.** OneDrive content is embedded **on demand, one-time** — the user names specific files; only those files are downloaded and embedded. The user's OneDrive is never scanned, listed wholesale, or embedded in bulk by any automatic process.
- Q: What happens to local host files? → A: **Unchanged.** All files in local storage keep the current automatic update behavior (periodic watcher embeds new/changed local files, evicts deleted ones). On-demand applies to OneDrive sources only.
- Q: When a OneDrive file changes in the cloud after embedding, should the system update it automatically? → A: **Reminder, not auto-download.** When an answer cites OneDrive-embedded content and the cloud copy is newer, the system prompts the user that the embedded copy may be outdated and offers to update it now. Content is re-downloaded only on the user's explicit command.
- Q: How does the user pick files? → A: Browse file names (metadata-only listing with an optional name filter), review the matches, then embed the exact files chosen. The user always sees what will be embedded before it happens.
- Q: How long may the freshness check hold an answer before giving up? → A: **≤5-second total budget** (user decision, 2026-10-11). Cited files are checked in parallel within a 5-second window; on timeout the answer returns immediately without a reminder. Detection reliability is prioritized over response speed, and the budget makes the bound testable.
- Q: If the cloud service throttles or errors partway through a multi-file embed, what happens to unprocessed files? → A: **Continue the batch** (user decision, 2026-10-11). Completed files keep their progress; each file that could not be processed gets an honest per-file reason suggesting a re-run of the embed command for that file.
- Q: How should the staleness check treat OneDrive files embedded by the old auto-sync design, which carry no freshness snapshot? → A: **One-time migration re-embed at upgrade** (user decision, 2026-10-11). At first startup under this design, every previously embedded OneDrive document lacking a snapshot is re-embedded once — refreshing its content and establishing its snapshot. After the migration, all OneDrive content is on-demand only. The migration never touches drive files that were not already in the knowledge base.
- Q: Should a single embed command have a per-command file-count maximum? → A: **No cap** (user decision, 2026-10-11). The named list is processed sequentially with honest per-file results; no artificial limit is imposed.
- Q: (double-clarify scan findings) What neglected matters were found? → A: The freshness probe identifies cited files by their **cloud-stable item identifier** (renames/moves never masquerade as deletions; an identifier that cannot be found genuinely means deleted); the staleness reminder is exposed as an **additive structured response field** in addition to the answer text; and embed/listing commands issued with an expired token return an honest sign-in-required error with the source marked degraded — no partial or fabricated results.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect OneDrive with zero automatic ingestion (Priority: P1)

A user adds a OneDrive source and completes Microsoft sign-in (device code flow). The source is registered and authenticated — and **nothing else happens**: no file listing, no download, no embedding. Unlike the superseded design, completing sign-in does not trigger any sync, and a newly connected source with 50 supported files in the drive still embeds zero files until the user explicitly names some.

**Why this priority**: This is the foundational guarantee of the on-demand model — the user's OneDrive is never touched wholesale. If connection triggers ingestion, every other requirement is violated.

**Independent Test**: Connect a source whose drive contains files → wait any period with no explicit embed command → `sources_list` shows the source healthy and the knowledge base contains zero documents from it.

**Acceptance Scenarios**:

1. **Given** no OneDrive source exists, **When** the user adds one, **Then** the source is registered with a needs-sign-in status and zero Graph file requests are made beyond registration.
2. **Given** a newly added source, **When** the user completes device sign-in, **Then** the source becomes healthy and no file is listed, downloaded, or embedded by the sign-in itself.
3. **Given** a connected, authenticated source with files in the drive, **When** any waiting period passes (watcher cycles included), **Then** no document from that source appears in the knowledge base.
4. **Given** a manual sync request against a OneDrive source, **When** it is invoked, **Then** the system returns an honest notice that this is an on-demand source and embedding happens per-file by explicit command — it never performs a drive sync.

---

### User Story 2 - Browse files and embed only what the user picks, one-time (Priority: P1)

The user asks to add a file from OneDrive. The system lists matching file metadata (path, name, size, modified time, whether it is embeddable) — names only, no content is downloaded. The user reviews the matches and confirms; the system downloads and embeds **exactly the named files** through the same pipeline as local files, and reports per-file outcomes with honest reasons for any skip. Other files in the drive are never touched.

**Why this priority**: This is the core value delivery — chosen cloud files become searchable, on the user's explicit instruction only.

**Independent Test**: List files with a name filter → embed 3 named files → exactly those 3 are searchable; a question about a different drive file's content finds nothing.

**Acceptance Scenarios**:

1. **Given** a connected source, **When** the user browses files, **Then** the listing shows file metadata (name, path, size, modified time, embeddable flag) from all nested folders, and no file content is downloaded.
2. **Given** a listing, **When** the user names 3 files to embed, **Then** only those 3 files are downloaded and embedded, each becomes searchable with citations, and the result reports per-file outcomes.
3. **Given** an embed request naming an unsupported-format file (e.g., PNG) or an oversized file, **When** embedding runs, **Then** that file is skipped with an explicit reason and the other named files still embed.
4. **Given** an embed request naming a file that does not exist, **When** embedding runs, **Then** the result states the file was not found — no partial guessing by name similarity, no fabricated content.
5. **Given** an embed request naming the same file twice (or re-embedding identical content), **When** embedding runs, **Then** no duplicate is created.

---

### User Story 3 - Staleness reminder when cited files changed in the cloud (Priority: P1)

The user asks a question whose answer cites OneDrive-embedded content. Before returning the answer, the system (best-effort, metadata-only) checks the cloud copies of the cited OneDrive files against the freshness snapshot recorded at embed time. If the cloud copy changed after embedding, the answer carries a reminder showing both timestamps and prompting the user that they may want to update the embedding now. The system never downloads or re-embeds on its own — the reminder is a prompt, and updating happens only by explicit user command.

**Why this priority**: One-time embedding trades freshness for control; without this reminder the user can unknowingly read stale content. The reminder restores freshness-awareness while preserving the no-auto-download invariant.

**Independent Test**: Embed a file → modify it in the cloud → ask a question answered from that file → the answer includes a staleness reminder naming the file and both timestamps; the answer content itself still comes from the embedded copy.

**Acceptance Scenarios**:

1. **Given** an embedded file whose cloud copy is unchanged, **When** an answer cites it, **Then** no reminder appears and the answer is returned normally.
2. **Given** an embedded file modified in the cloud after embedding, **When** an answer cites it, **Then** the answer includes a staleness reminder with the embedded-at and cloud-modified timestamps and an offer to update now.
3. **Given** a staleness reminder, **When** the user does nothing, **Then** the system performs no download or re-embed — subsequent answers continue to use the embedded copy with the reminder repeated while the file remains stale.
4. **Given** an embedded file that was deleted from the cloud, **When** an answer cites it, **Then** the answer notes the embedded copy is the last available version.
5. **Given** a question whose answer cites only local files, **When** the answer is returned, **Then** no freshness check runs against OneDrive and no reminder appears (local sources are always current by their automatic sync).

---

### User Story 4 - One-command explicit refresh (Priority: P2)

Following a staleness reminder (or at any time), the user says "update it". The system re-embeds the named file: downloads the latest content, replaces the old embedded copy (old chunks evicted, never duplicated), and refreshes the freshness snapshot. A repeated question then reflects the new content only.

**Why this priority**: The reminder creates the intent; this story completes the loop. It is a re-application of the embed command from US2 and needs no new machinery beyond honest reporting.

**Independent Test**: Embed → change cloud copy → ask (reminder appears) → issue the update command → ask again → the answer reflects the new content, the old content no longer appears, and no reminder remains.

**Acceptance Scenarios**:

1. **Given** a stale embedded file, **When** the user issues an explicit update command for it, **Then** the new content is embedded, the old chunks are evicted, and the freshness snapshot is refreshed.
2. **Given** an updated file, **When** the same question is asked again, **Then** the answer reflects only the new content and no staleness reminder appears.
3. **Given** an update command for a file whose cloud content is identical to the embedded copy, **When** the update runs, **Then** the result honestly reports no change rather than re-embedding.

---

### User Story 5 - Local sources keep automatic updates, untouched (Priority: P2)

All files in local storage (local folders and SQLite sources) continue their current behavior: the periodic watcher automatically embeds new files, re-embeds changed files, and evicts deleted ones. OneDrive sources are excluded from the watcher entirely; the two policies coexist without interaction.

**Why this priority**: The on-demand revision must not regress the existing automatic-embedding design for local storage — that behavior is the product's status quo and stays exactly as-is.

**Independent Test**: With both a local folder source and a connected OneDrive source registered, add a file to the local folder and change a file in OneDrive → within one watcher cycle the local file is embedded; the OneDrive change is not embedded and no reminder exists until a question citing it is asked.

**Acceptance Scenarios**:

1. **Given** a registered local folder source, **When** a new file appears in the folder, **Then** it is embedded automatically within one watcher cycle (existing behavior, unchanged).
2. **Given** a registered OneDrive source, **When** the watcher cycle runs, **Then** the OneDrive source is skipped entirely — no Graph requests, no downloads, no health changes.
3. **Given** a OneDrive source whose token has expired, **When** the watcher cycle runs, **Then** the source's health is untouched by the watcher (staleness/auth of on-demand sources is surfaced by user-initiated actions, not background polling).

---

### Edge Cases

- What if the OneDrive is empty or a browse filter matches nothing? → An honest empty listing — no error, no fabricated matches.
- What if the freshness probe cannot reach the cloud service or times out (transient)? → No reminder, no error surfaced on the answer; the answer returns after at most the 5-second probe budget, and citations continue to show when the copy was embedded so age is visible. The probe must never break the answer.
- What if the freshness probe fails due to an expired token? → The source is marked degraded with a sign-in-required reason per existing behavior and appears in the answer's degraded-source reporting; no reminder is fabricated.
- What if a file changes in the cloud between the embed command and the snapshot record? → The snapshot reflects the content actually embedded (the bytes that were downloaded); the next staleness check compares against that snapshot.
- What if the same file exists both locally and in OneDrive? → Existing content-hash dedup applies: embedded once, cited with both origins (spec 001 behavior, unchanged).
- What if the user has multiple OneDrive sources? → They are independent, each with its own token cache, config, and embedded files.
- What if an embedded file is renamed or moved in the cloud? → The freshness check still finds it by its stable identifier (a rename never masquerades as a deletion), though a rename updates the item's modified time and may trigger a reminder; the old path becomes unresolvable for the update command, so the system reports the path not found honestly, and the newly browsed path can be embedded to refresh it.
- What if the user issues an embed or listing command while the token is expired? → An honest sign-in-required error is returned and the source is marked degraded per existing behavior; after re-authentication the user re-issues the command. No partial or fabricated results are ever produced.
- What if a browse listing is very large? → The listing is paginated and bounded; the user filters or pages — no unbounded enumeration is forced into a single response.
- What if unsupported or oversized files are named alongside valid ones? → Valid files embed; invalid ones are skipped with per-file reasons (identical to local-source honesty rules).
- What if the cloud service throttles or errors partway through a multi-file embed? → The batch continues; completed files keep their progress and each unprocessed file is reported with an honest per-file reason suggesting a re-run (e.g., "cloud rate-limited — re-run embed for this file"). Never all-or-nothing, never silent.
- What if a legacy embedded file no longer exists in the cloud at migration time? → Honest per-file migration reason; the existing embedded copy is kept as the last available version, cited with its embedded-at time, and remains unverifiable (no snapshot, no reminder) until the user embeds a different file.
- What if the token is expired when the migration runs? → The migration reports honestly that sign-in is required (source degraded per existing behavior); the migration is idempotent and retries affected files on the next startup after re-authentication.

## Requirements *(mandatory)*

### Functional Requirements

**Connection (US1)**

- **FR-001**: Adding a OneDrive source MUST register it and, when no valid token exists, return a needs-sign-in status — and MUST NOT list, download, or embed any file as part of registration.
- **FR-002**: Completing sign-in MUST transition the source to healthy WITHOUT triggering any file sync, listing, or ingestion (supersedes the spec-006 post-auth sync).
- **FR-003**: The periodic watcher MUST NOT sync OneDrive sources — no background Graph requests of any kind for them — while local_folder and sqlite sources continue their existing automatic sync unchanged.
- **FR-004**: A manual sync request against a OneDrive source MUST return an honest on-demand notice directing the user to the per-file embed command; it MUST NOT perform a drive sync.

**On-demand browse and embed (US2)**

- **FR-005**: The system MUST provide a metadata-only file listing capability for a connected OneDrive source: file name, path, size, modified time, and embeddable flag, across nested folders, with pagination and an optional name filter — without downloading any file content.
- **FR-006**: The system MUST provide an embed-files capability that takes an explicit list of files (paths and/or item identifiers) and downloads and embeds ONLY those files, one-time per call, through the existing parse → dedup → chunk → embed pipeline used for local files. There is no per-command file-count limit; the list is processed sequentially with per-file outcomes.
- **FR-007**: Embed results MUST report per-file outcomes with explicit skip reasons (unsupported format, oversized, not found, no download URL, cloud throttling or error) — never silent skips, never fabricated content (Constitution IV). A mid-batch cloud throttling or error MUST NOT abort the remaining files: the batch continues and each unprocessed file gets an honest per-file reason suggesting a re-run; completed files keep their progress.
- **FR-008**: Re-embedding identical content MUST NOT create duplicates; changed content MUST replace the old embedding (evict old chunks first) per the existing dedup/eviction machinery.

**Staleness reminder (US3/US4)**

- **FR-009**: At embed time the system MUST record a freshness snapshot for each embedded file — the cloud-stable item identifier, the cloud last-modified timestamp (and/or change token), and the embed time — representing the content actually embedded. The stable identifier ensures later freshness checks survive cloud renames and moves.
- **FR-010**: When an answer cites OneDrive-embedded content, the system MUST perform a best-effort, metadata-only freshness check of the cited OneDrive files — identifying each file by its recorded cloud-stable identifier, so a rename or move never masquerades as a deletion (an identifier that cannot be found genuinely means the file was deleted) — and, when a cloud copy is newer than its snapshot, append a staleness reminder to the answer naming the file, both timestamps, and an offer to update now. The reminder MUST also be exposed as an additive structured response field for programmatic consumers. The check MUST complete within a **5-second total budget** (cited files checked in parallel); on timeout the answer MUST return immediately without a reminder.
- **FR-011**: The staleness reminder MUST NOT cause any automatic download or re-embed; content updates happen only via the user's explicit embed command (the reminder is a prompt, not an action).
- **FR-012**: If a cited file no longer exists in the cloud, the answer MUST note that the embedded copy is the last available version.
- **FR-013**: Freshness-probe failures MUST be non-blocking and honest: transient failures produce no reminder and no answer-level error (citations continue to carry the embedded-at time); authentication failures mark the source degraded and surface through the existing degraded-source reporting.

**Migration (upgrade path)**

- **FR-016**: At first startup under this design, the system MUST perform a one-time migration that re-embeds every previously embedded OneDrive document lacking a freshness snapshot — refreshing its content and recording its snapshot — and MUST NOT scan or embed any drive file that was not already in the knowledge base. The migration MUST report per-file outcomes honestly and MUST be idempotent (a legacy document only leaves the migration set once it has a snapshot; unfetchable or failed files are retried on the next startup, never silently dropped).

**Constitution compliance**

- **FR-014**: All existing tool response shapes MUST remain unchanged; new capabilities and any new response fields are purely additive (Constitution I).
- **FR-015**: The superseded automatic-sync behaviors for OneDrive (post-auth sync, watcher sync, full-drive delta sync) MUST be removed from the codebase, with this spec carrying the Supersedes record (Constitution V — no dead code).

### Key Entities

- **OneDriveSourceConfig**: connection configuration — Azure app client id, optional folder scope for listings, optional size bound (unchanged from spec 006 minus sync-only fields).
- **FileListingEntry**: metadata-only description of a drive file — name, path, size, last-modified time, embeddable flag, item identifier. Never carries content.
- **EmbedRequest**: the user's explicit list of files to embed (paths and/or item identifiers), submitted once per call.
- **FreshnessSnapshot**: per embedded file — the cloud-stable item identifier, the cloud last-modified timestamp (and/or change token) of the content that was actually embedded, plus the embed time. Used solely for staleness comparison.
- **StalenessReminder**: an answer-level notice — file identity, embedded-at time, cloud-modified time, message prompting an update, and the path/identifier to use for the update command.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Connecting a OneDrive source that contains 50 supported files results in 0 embedded documents after any waiting period, unless the user explicitly embeds files.
- **SC-002**: Embedding 3 named files makes exactly those 3 files searchable with citations within one command; no other drive file's content is ever returned from that source.
- **SC-003**: When a cited OneDrive file changed in the cloud after embedding, the answer includes a staleness reminder naming the file and both timestamps, on the same conversation turn the question was asked; the freshness check never exceeds its 5-second budget and skips the reminder honestly on timeout.
- **SC-004**: A staleness reminder never updates content by itself; after the user's explicit update command, the same question yields only the new content and no reminder.
- **SC-005**: Local folder and SQLite automatic-update behavior is regression-free: all existing tests for these sources pass unchanged.
- **SC-006**: The full test suite passes with the superseded sync tests replaced by on-demand tests (Constitution I/V); new tests are additive.
- **SC-007**: 100% of embed skips (unsupported, oversized, not found) produce explicit per-file reasons in results — verified by tests, never silent.
- **SC-008**: On upgrade with N legacy embedded OneDrive documents, the one-time migration re-embeds exactly those N documents (zero not-already-embedded drive files are touched) and records snapshots for every successfully fetched one; a system with no legacy documents performs a no-op migration.

## Assumptions

- Microsoft device-code sign-in, per-source token caching, and silent refresh (spec 006 auth layer) are reused unchanged; only what happens *after* authentication changes.
- The existing parsers (PDF, Word, Excel, PowerPoint), content-hash dedup, chunking, embedding, and vector store are reused unchanged for OneDrive embeds.
- The freshness check runs only for OneDrive documents actually cited in the current answer (typically 1–3 files), is metadata-only, and has a short bounded timeout.
- The chat agent (Dify) is updated additively with the new browse/embed capabilities and guidance to relay staleness reminders verbatim, including "never embed the whole drive" instruction.
- Existing authenticated OneDrive sources, if any, transition to the on-demand model via the one-time migration (FR-016): previously embedded documents are re-embedded once at first startup, refreshing content and establishing snapshots; afterwards no automatic syncing ever occurs. A system with no legacy embedded OneDrive documents (including the current deployment) is a no-op migration.
- Out of scope: SharePoint (separate source type, unchanged); shared-with-me files (own drive only); file upload/write-back to OneDrive; automatic or scheduled re-embedding of any OneDrive content.
