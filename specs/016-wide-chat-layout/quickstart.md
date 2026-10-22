# Quickstart: Wide Chat Layout

## Prerequisites

- `pnpm dev` running in `ai-chat-landing/` (port 3000)
- Chrome started with `--remote-debugging-port=9240`
- `--smoke` mode additionally needs the live Dify stack (it sends a real
  message and exports a PDF)

## Validate

1. **Static gates** (always):
   ```sh
   cd ai-chat-landing && pnpm typecheck && pnpm lint && pnpm test
   ```
   Expect: tsc clean, eslint clean, 71/71 vitest.

2. **Measured widths** (the feature's Definition of Done):
   ```sh
   node ai-chat-landing/scripts/wide-layout.mjs
   ```
   Expect: T1–T9 from `contracts/wide-layout.md` all pass — 1440×900
   sidebar-open ≈1066px and ≥85% of content area; 1920×1080 exactly 1400px;
   1279px and below unchanged; long user bubble ≤672px.

3. **Behavioral smoke** (specs 014/015 regression guard at the wide layout):
   ```sh
   node ai-chat-landing/scripts/wide-layout.mjs --smoke
   ```
   Creates one throwaway conversation (fresh draft, never merged into the
   demo thread), verifies bucket headers and Load more pagination, exports
   a PDF (FR-004 live check; baseline kept at `/tmp/kilo/cdp/pdf-baseline.pdf`),
   then deletes the throwaway via the spec 015 flow.

4. **Manual sanity** (30 seconds): resize the browser across 1280px and
   watch the column widen once you cross it; paste a long message and see
   the bubble stop at 672px.

## Failure triage

- "Chrome :9240 unreachable" → start Chrome with the debug port and rerun.
- "Selector not found: <name>" → the class strings drifted; re-check
  `app/page.tsx` against `plan.md`'s width table.
- Width wrong at exactly 1024–1279px → the `xl:` gate was dropped and a
  global `min(90%,…)` is narrowing the column (research R2).
- Smoke "delete flow stalled" → the 015 menu/confirm selectors drifted in
  `components/chat-history.tsx`.
