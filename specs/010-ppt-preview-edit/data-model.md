# Data Model — PPT Completion Experience (Phase 1)

All state is filesystem-backed; entities extend spec 009's model additively.

## Export Artifact (extended from spec 009)

| Field | Type | Rules |
|---|---|---|
| `filename` | string | `<project_id>_<HHMMSS>.pptx` in `<project>/exports/` — unchanged (frozen) |
| `url` | string | direct download URL — unchanged (frozen) |
| `page_url` | string | **new, additive**: `<exports_url_base host>/decks/<project_id>/<stem>/` where `stem` = filename without `.pptx` |
| `preview_state` | enum | `ready` \| `degraded` — determined at export time, recorded on disk |

## Preview Snapshot

Per-artifact, immutable snapshot of the pipeline's self-contained per-slide renderings.

| Field | Type | Rules |
|---|---|---|
| `project_id` | string | FK → PPT Project |
| `stem` | string | FK → Export Artifact stem; directory `<project>/previews/<stem>/` |
| `slides` | list[Path] | ordered `NN_<name>.svg` files, one per deck page, ≤ max_pages entries |
| `degraded_marker` | file? | present when preview generation failed; page renders degraded mode |
| `created_at` | timestamp | artifact export time; never mutated afterwards |

**Lifecycle**: `created` at export (snapshot success) → `degraded` (marker written when finalize/snapshot fails — the directory may be empty or partial, never silently regenerated). Snapshots are write-once; a re-export creates a NEW stem directory and never touches an existing one.

**Validation**: slide files must live inside the snapshot directory (traversal-rejected at the route layer); ordering follows the numeric prefix.

## Completion Page (served, not stored)

| Field | Type | Rules |
|---|---|---|
| `project_id` + `stem` | path params | identify one artifact's page |
| `content` | rendered HTML | slide previews (or degraded states), download control (→ `url`), edit path (→ back-to-chat pointer) |
| `http states` | — | 200 with page; 404 honest page for unknown/removed artifact; 400 malformed |

## Deck Link (Chat UI concept)

| Field | Type | Rules |
|---|---|---|
| `kind` | enum | `download` (exports URL) \| `page` (decks URL) |
| `counterpart` | derived | deterministic URL rewrite sharing project + stem (pure function, unit-tested) |

**Validation**: only the two exact URL families are recognized; everything else renders as an ordinary link (FR-012).

## Relationships

```text
PPT Project 1 ──── * Export Artifact (spec 009, unchanged + page_url)
Export Artifact 1 ─ 1 Preview Snapshot (stem-identified, write-once)
Export Artifact 1 ─ 1 Completion Page (rendered from snapshot + artifact state)
Deck Link 1 ────── 1 recognized URL (chat answer) ⇄ derived counterpart
```

## Deliberately NOT modeled

Per-slide metadata databases, preview caches (snapshots are the cache), analytics, authentication (local-trust posture), and any mutation path for issued pages (immutability is the contract).
