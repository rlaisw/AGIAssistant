# Research: Wide Chat Layout

## R1 — How the column width is constrained today

- **Decision**: the only chat-width constraints are two `max-w-3xl` classes —
  message column (`app/page.tsx` ~757) and composer (~868) — plus
  `max-w-[85%]` user bubbles (~761) and the empty-state `max-w-2xl` grid
  (~737, out of scope).
- **Rationale**: verified by reading the source; no other width constraints
  exist in the component tree (`components/markdown.tsx` images are
  `max-w-full`, sidebar rows are self-contained).
- **Alternatives considered**: a CSS variable / container-query redesign —
  rejected as over-engineering for a two-site class change.

## R2 — Additive `xl:` scoping vs global replacement

- **Decision**: add `xl:max-w-[min(90%,1400px)]` *alongside* the existing
  `max-w-3xl` on both sites.
- **Rationale**: measured — at 1024–1279px a global `min(90%,…)` yields
  691px vs today's 720px content width (a regression). Gating to ≥1280px
  makes the change monotonic: no viewport ever narrows. Tailwind v4 supports
  the arbitrary value (`min(90%,1400px)` — no spaces, valid CSS).
- **Alternatives considered**: global `min(90%,…)` (narrows lg screens);
  fixed `max-w-6xl/7xl` (not viewport-relative, wastes ultrawide space).

## R3 — User-bubble readability ceiling

- **Decision**: add `lg:max-w-2xl` (672px) to the user bubble alongside its
  relative `max-w-[85%]`.
- **Rationale**: 85% of a 1400px column ≈ 1190px of unbroken text — a wall.
  The absolute ceiling bounds worst-case line length while short messages
  stay compact (the relative cap still binds for small messages).
- **Alternatives considered**: leave 85% relative (readability regression
  for long pasted input); prose max-width on the text element (extra DOM
  change for the same effect).

## R4 — PDF export safety (spec 013)

- **Decision**: no changes needed; the export is structurally immune.
- **Rationale**: `lib/pdf-export/render.tsx` renders its own off-screen
  container with a hard-coded `width:744px` and inline rgb palette; it never
  measures the live DOM column.
- **Alternatives considered**: widening the PDF container — rejected; spec
  013's A4 pagination math (744px ≈ A4 @ 96dpi) would break for no user
  benefit.

## R5 — Verification approach

- **Decision**: CDP measurement script (`/tmp/kilo/cdp/wide-layout.mjs`,
  Chrome `--remote-debugging-port=9240`, target `:3000`) following the spec
  015 verification pattern, plus the standing `pnpm typecheck && pnpm lint
  && pnpm test` gate.
- **Rationale**: widths are runtime-computed values; vitest is pure-logic by
  house convention, so the honest check is a measured one.
- **Alternatives considered**: a vitest test asserting the class string
  exists — rejected as tautological (it would test the diff, not the
  behavior).
