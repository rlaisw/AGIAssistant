# Quickstart: Wide Chat Layout

## Prerequisites

- `pnpm dev` running in `ai-chat-landing/` (port 3000)
- Chrome started with `--remote-debugging-port=9240`
- PDF baseline from tasks.md T002 (optional for first run — see T8)

## Validate

1. **Static gates** (always):
   ```sh
   cd ai-chat-landing && pnpm typecheck && pnpm lint && pnpm test
   ```
   Expect: tsc clean, eslint clean, 71/71 vitest.

2. **Measured widths** (the feature's Definition of Done):
   ```sh
   node /tmp/kilo/cdp/wide-layout.mjs
   ```
   Expect: T1–T9 from `contracts/wide-layout.md` all pass — 1440×900
   sidebar-open ≈1066px and ≥85% of content area; 1920×1080 exactly 1400px;
   1279px and below unchanged; long user bubble ≤672px; PDF export and
   sidebar smoke green.

3. **Manual sanity** (30 seconds): resize the browser across 1280px and
   watch the column widen once you cross it; paste a long message and see
   the bubble stop at 672px.

## Failure triage

- "Chrome :9240 unreachable" → start Chrome with the debug port and rerun.
- "Selector not found: <name>" → the class strings drifted; re-check
  `app/page.tsx` against `plan.md`'s width table.
- Width wrong at exactly 1024–1279px → the `xl:` gate was dropped and a
  global `min(90%,…)` is narrowing the column (research R2).
