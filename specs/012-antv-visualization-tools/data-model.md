# Data Model — AntV Visualization Tools (Phase 1)

All state is filesystem-backed or external; entities extend the deployment additively.

## Chart Request

| Field | Type | Rules |
|---|---|---|
| `chart_type` | string | must be in the curated supported list (code-level constant); geo types excluded; unknown → honest error naming the supported set |
| `data` | list | non-empty; entries are the rendering service's expected shape (objects for category/value series, etc.); size-capped (serialized ≤ 64 KB) |
| `title` | string | optional, ≤ 200 chars |

**Lifecycle**: submitted by an agent → validated → POSTed to the configured rendering service → success produces a **Chart Artifact**; any failure raises an honest `Antv*` error (never a partial result).

## Chart Artifact

| Field | Type | Rules |
|---|---|---|
| `image_url` | URL | hosted by the rendering service (public, unauthenticated — SC-002); usable directly in markdown answers |
| `type` | string | echoes the requested chart type |

**Lifecycle**: immutable once returned; retention governed by the rendering service (documented posture, FR-009); for decks, the bytes are inlined at page-write time, after which the page no longer depends on the URL.

## Infographic Request

| Field | Type | Rules |
|---|---|---|
| `description` | string | the declarative infographic syntax; non-empty, ≤ 64 KB (configurable); stored verbatim |

## Infographic Artifact

| Field | Type | Rules |
|---|---|---|
| `id` | string | URL-safe, unique per submission |
| `url` | URL | sidecar-served HTML page: `GET /infographics/<id>/` (renders via the CDN-loaded engine) |
| `stored_at` | path | `<served dir>/infographics/<id>.txt` (syntax) — served read-only by the route |

**Lifecycle**: `created` on tool call → served indefinitely (retention follows the deployment's artifact conventions); malformed syntax is rejected at creation, never stored.

## Deck Page (extended from spec 009)

| Field | Type | Rules |
|---|---|---|
| `svg` | string | unchanged contract, plus: every remote `<image href="https://…">` is fetched (≤ max_inline_image_bytes) and re-embedded as a `data:` URI at write time; fetch failure or oversize → honest named error, page not persisted (self-containment, Clarification 2026-10-20) |

## Relationships

```text
Chart Request 1 ──── 1 Chart Artifact (chat answers embed image_url)
Chart Artifact 1 ──── 0..1 Deck Page (via image href, inlined to data: at write)
Infographic Request 1 ─ 1 Infographic Artifact (browser renders from served syntax)
```

## Deliberately NOT modeled

Chart byte caching on the sidecar (hosted URLs suffice for chat; inlining covers decks), chart history/records (the service's own feature), infographic editing (future), authentication (local-trust posture).
