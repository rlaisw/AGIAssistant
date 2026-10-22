# Research: PDF Download of Chat Conversations

## R1: PDF generation approach (FR-002/FR-003/FR-004)

**Decision**: Offscreen DOM render + rasterize to paginated PDF — `jspdf` +
`html2canvas-pro`, both lazy-loaded on first export click.

**Rationale**: FR-003 mandates reusing the app's existing markdown pipeline.
Rendering the conversation into a detached, print-palette container with the
app's own `react-markdown` components gives pixel-true reuse: GFM tables, code
blocks, lists, and `[image: URL]` images render identically to the chat. The
container is rasterized and sliced into A4 pages via jsPDF. No server
round-trip, nothing persisted (FR-004). Lazy `import()` keeps the ~500 KB of
libraries off the initial bundle.

**Alternatives considered**:
- `pdfmake` / text-mode jsPDF — clean selectable text, but requires a
  markdown→doc-definition mapper: exactly the "parallel pipeline" FR-003
  forbids. Rejected.
- `window.print()` + print stylesheet — zero dependencies (Constitution III
  ideal), but yields the browser's print dialog, not a click→download; fails
  FR-002's "downloads via the browser's native download mechanism". Rejected.
- Server-side rendering (headless browser) — new runtime service; violates
  SC-004/Constitution III. Rejected.

## R2: Rasterizer vs modern color functions (Tailwind 4 oklch)

**Decision**: Use the `html2canvas-pro` fork (MIT), which parses modern CSS
color functions (oklch/lab) that stock html2canvas cannot read; Tailwind 4's
palette is oklch-based and would break the stock library.

**Rationale**: html2canvas reads computed styles; Tailwind 4 utilities compute
to oklch, and stock html2canvas throws or produces black output on them. The
pro fork is a drop-in with the same API surface.

**Fallback constraint** (for tasks): if the fork is unsuitable at build time,
pin the export subtree to inline `rgb()` styles and a small plain-CSS print
sheet (no Tailwind utilities inside the export container) and use stock
html2canvas. Either way, tests must not depend on which rasterizer variant.

## R3: Cross-origin images (FR-012) — CORS + honest fallback

**Decision**: Attempt CORS image loads (`useCORS: true`) with a bounded wait
per image; failures degrade to the labeled link per FR-012. Enable the
sidecar's media routes (`/exports/`, `/decks/…/slides/`, infographics) to
send `Access-Control-Allow-Origin: *` — an additive header on the local-trust
network (same posture as the unauthenticated `/exports` route).

**Rationale**: The canvas is tainted (and export fails) if cross-origin images
without CORS are drawn; localhost:28080 media is ours to fix, remote internet
images (web research) usually aren't — for those, the link fallback is the
honest behavior FR-012 already mandates. The header is one line on existing
routes (Constitution III: reuse, don't add services).

**Alternatives considered**: Server-side image proxy route in Next.js — extra
moving part, adds a fetch surface; rejected for v1 (link fallback suffices).

## R4: File naming (FR-006)

**Decision**: Local slugify of the first user question (lowercase, strip
non-alphanumerics, hyphens, cap 40 chars) + `.pdf`; timestamp fallback
`chat-YYYYMMDD-HHmmss.pdf`. No new dependency.

## R5: Test strategy (user requirement: tests-first per Constitution II)

**Decision**: Pure-logic modules (slugify, export-state machine, message→
export-model transform, image-wait helper with stubbed `Image`) are extracted
from the React tree and unit-tested with the existing vitest setup; a node-env
test drives the export orchestrator with the render/rasterize/save seams
injected as stubs (no network, deterministic — mocks at trust boundaries). UI
wiring is covered by the quickstart manual pass.

**Rationale**: `pnpm test` (vitest) is the project's existing harness; heavy
DOM rasterization is a trust boundary we stub, keeping CI deterministic.

## R6: Error taxonomy (user requirement: explicit error handling)

**Decision**: One `ExportError` type with machine-readable `code`:
`empty_conversation` (icon disabled — FR-001), `render_failed` (rasterizer
threw → FR-007 visible error), `download_blocked` (browser refused the
blob download → FR hint), `image_unavailable` (NOT a user-facing error —
silent degrade to link per FR-012). Busy state guards re-entry (FR-008).
