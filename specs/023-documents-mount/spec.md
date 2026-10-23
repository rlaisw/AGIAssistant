# Feature Specification: Dedicated Documents Mount

**Feature Branch**: `023-documents-mount`

**Created**: 2026-10-23

**Status**: Draft

**Input**: User description: "add new source-list, based on the above chat conversation, help to implement Option 2" — a dedicated, honestly-named documents folder for RAG ingestion. Today the only working source location is a borrowed folder inside the ppt-master tree (`ppt-master/rag-docs`), which misleads users; documents placed under the app's config dir (`~/.config/...`) are silently invisible to the scanner (hidden-directory filter). Option 2 (locked in the preceding conversation): create host `~/agentic-rag-docs/`, mount it into the sidecar at `/data/rag-docs` **in the deployment's own container spec** so it survives redeploys, migrate the existing document there, re-register the source, and verify ingestion end-to-end.

## Clarifications

### Session 2026-10-23

- Q: Can a sqlite database also live in the new documents folder and be added to the source list? → A: yes — sqlite is a first-class source type; a `.db` placed in the mounted folder is invisible to the *folder* scanner (by design — `.db` is not a scanned extension) and registers instead as its own `sqlite` source pointing at the same container path (config: `db_path`, `table`, optional `template`; one table per source; read-only; row-per-document; auto-synced by the same 5-minute watcher). No database exists yet on this deployment, so sqlite stays **out of 023's acceptance scope** — the mount's verification covers the folder source; a sqlite registration is one `sources_add` call whenever a real db arrives.
- Q (double-clarify): is documenting the new folder part of the feature? → A: yes — the deployment runbook (DEPLOY.md Step 6 and the deploy skill) must document the documents folder (host path, supported types, auto-sync, one-time registration), otherwise the answer to "where do documents go" lives only in chat history. Added as FR-006.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Drop documents into an obviously-named folder and have them ingested (Priority: P1)

An operator copies documents into `~/agentic-rag-docs/` on the host — a
folder whose name says exactly what it is. The deployment mounts it into
the RAG sidecar at `/data/rag-docs`, it is registered as a source, and the
watcher auto-ingests supported files within ~5 minutes. The mount is part
of the deployment's container definition, so redeploys keep it. The
misleading `ppt-master/rag-docs` source is removed and its document
migrated.

**Why this priority**: it is the entire feature — one honest documents
location that survives redeploys.

**Independent Test**: copy a supported document into `~/agentic-rag-docs/`
on the host; within the sync window (or after an explicit sync) the index
document/chunk count increases; recreating the container from the
deployment tooling keeps the folder visible to the RAG.

**Acceptance Scenarios**:

1. **Given** the host folder `~/agentic-rag-docs/`, **When** the
   deployment recreates the sidecar, **Then** the folder is mounted inside
   the container at `/data/rag-docs` (no manual `docker run` flags
   involved — the deployment's own container spec carries the mount).
2. **Given** the mounted folder registered as a source, **When** a
   supported document is copied there, **Then** it is ingested and
   searchable (index counts increase; asking about its content cites it).
3. **Given** the existing `reset password.pdf`, **When** migration runs,
   **Then** it lives in `~/agentic-rag-docs/`, the old `ppt-master/rag-docs`
   source and folder are gone, and the document still answers questions.
4. **Given** a future `redeploy` or `all`, **When** the container is
   recreated from the deployment spec, **Then** the documents mount is
   still present and the source keeps working.

---

### Edge Cases

- Host folder absent at container creation: the deployment creates it
  before starting the container (never rely on Docker's root-owned
  auto-create).
- The brief recreate window (~1 minute): in-flight chat requests may
  fail once; the health check gates further steps.
- Documents of unsupported extensions (e.g. `.md`, `.txt`) remain silently
  ignored — unchanged scanner behavior, out of scope here.
- The hidden-dir scanner limitation stays: sources under dot-directories
  (e.g. `~/.config/...`) remain unusable; the new mount sidesteps it by
  living at a dot-free path. The scanner fix itself is out of scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The deployment's container definition MUST include a
  documents volume mapping the host's home-level `agentic-rag-docs`
  folder (created if absent) to `/data/rag-docs` in the container.
- **FR-002**: The running sidecar MUST be recreated with the new mount
  (brief downtime), returning to a healthy state before any further step.
- **FR-003**: The existing document MUST be migrated: `reset password.pdf`
  moves from the ppt-master tree to the new host folder; the old
  `rag-docs` source is removed; the new `/data/rag-docs` source is
  registered; ingestion verified (document present, chunks > 0).
- **FR-004**: A container recreated later by the deployment tooling
  (redeploy/all) MUST retain the documents mount without manual steps.
- **FR-005**: No other behavior changes: existing config/state/volumes
  untouched, the Dify chatflow and tool registration unaffected, health
  checks green after recreate.
- **FR-006**: The deployment runbook (DEPLOY.md Step 6 and the deploy skill)
  MUST document the documents folder: the host path, supported file types,
  the ≤5-minute auto-sync, and the one-time source registration — verifiable
  by the folder appearing in both docs.

### Key Entities

- A deployment-owned volume mapping: host `~/agentic-rag-docs` ⇄
  container `/data/rag-docs`; one registered local-folder source pointing
  at the container path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After recreate, a file written to the host folder is
  readable at `/data/rag-docs` inside the container (mount verified
  both directions).
- **SC-002**: After migration + sync, the index shows the migrated
  document (documents ≥ 1, chunks ≥ 1, zero skipped) and the old source
  is gone from the source list.
- **SC-003**: After a second recreate driven by the deployment tooling,
  the mount is still present and the source still syncs (the spec — not
  a manual flag — owns the mount).
- **SC-004**: Health check green after each recreate; no unrelated
  regression (config dir, models cache, ppt-master mounts unchanged).

## Assumptions

- Paths locked in conversation: host `~/agentic-rag-docs/` (i.e.
  `/home/administrator/agentic-rag-docs/`), container `/data/rag-docs`.
- The deployment CLI recreates the container itself; adding the volume to
  its run spec is the durable way to own the mount (a manual `docker run`
  flag would be lost on the next redeploy).
- Brief downtime during recreate is acceptable (single-user deployment).
- Supported file types unchanged (pdf/docx/xlsx/pptx ingest; audio scanned
  but skipped; md/txt not scanned) — extensions are out of scope.
- The hidden-dir scanner fix stays out of scope; the new mount avoids the
  problem by design.
