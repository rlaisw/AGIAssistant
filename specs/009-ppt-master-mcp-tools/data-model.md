# Data Model — PPT-Master MCP Tools (Phase 1)

Entities from the spec, mapped to their concrete fields and validation rules. All state is filesystem-backed (no database — Principle III).

## PPT Project

The unit of one generation (or same-conversation revision) session.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Directory name: `<slug>_<YYYYMMDD>_<short-random>` — unique, URL-safe, unguessable enough for the export link (R5) |
| `name` | string | 1–64 chars, from the agent's project name or derived from the topic |
| `workspace` | path | `<projects_root>/<id>/` — contains `sources/`, `icons/`, `svg_output/`, `exports/`, `notes/` |
| `created_at` | timestamp | From init time |
| `max_pages` | int | From config (default 5); `ppt_write_page` refuses page numbers beyond it |

**Lifecycle**: `created` (init) → `authored` (≥ 1 page written) → `checked` (check run, may oscillate authored↔checked during repair) → `exported` (export produced artifact). Terminal states reachable from any state: `abandoned` (conversation ends without export; files remain per retention).

**Validation**: init rejects empty/non-URL-safe slugs; write rejects unknown `project_id`, page numbers outside `1..max_pages`, and SVG that fails sanitization (see Slide Page).

## Slide Page

One authored page of a project.

| Field | Type | Rules |
|---|---|---|
| `project_id` | string | FK → PPT Project |
| `page_number` | int | 1..max_pages, unique within project |
| `name` | string | URL-safe slug, used in the filename `<NN>_<name>.svg` |
| `svg` | string | Complete page SVG document (the agent-authored content) |
| `check_status` | enum | `unchecked` \| `passing` \| `failing` — recomputed by `ppt_check`; `passing` requires zero blocking errors |

**Validation (sanitization before persisting)**: SVG must be well-formed XML; root must declare the project's viewBox; rejects forbidden constructs (`<script>`, event attributes, `<foreignObject>`, `<style>`, `class`, external references, non-`data:`/`https:` `href` on `<image>`); size cap 256 KB per page.

## Export Artifact

A generated deck file.

| Field | Type | Rules |
|---|---|---|
| `project_id` | string | FK → PPT Project |
| `filename` | string | `<project_id>_<HHMMSS>.pptx` inside `<workspace>/exports/` |
| `url` | string | `<exports_url_base>/<project_id>/<filename>` — absolute, returned to the agent |
| `gate_result` | enum | `passing` at export time (export is refused otherwise — FR-006) |
| `created_at` | timestamp | Export time |

**Lifecycle**: immutable once written; a re-export (revision flow, FR-015) creates a new artifact with a fresh timestamp — old links keep resolving (retention `keep` default).

## Agent Rulebook

The distilled authoring instructions for the PPT-Master Dify node.

| Field | Type | Rules |
|---|---|---|
| `content` | markdown | Repo file `dify/ppt-master-rulebook.md`; embedded copy lives in the chatflow DSL |
| `covers` | — | Tool-call protocol, SVG contract subset, error-envelope handling, honest-failure rules |

**Lifecycle**: versioned with the repo; the chatflow embeds a snapshot, so a rulebook edit requires re-importing the DSL (documented in quickstart).

## Relationships

```text
PPT Project 1 ──── * Slide Page      (pages belong to exactly one project)
PPT Project 1 ──── * Export Artifact (re-exports append; artifacts immutable)
Agent Rulebook 1 ─── 1 chatflow node (snapshot embed)
```

## State that is deliberately NOT modeled

Cross-conversation project registry (out of scope v1 — Clarifications), user accounts (single local user), quotas/rate limits (single-user deployment; Dify's own agent limits bound abuse).
