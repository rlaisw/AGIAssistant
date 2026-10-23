# Quickstart: "Thinking" Assistant Indicator

## Prerequisites

- `pnpm dev` running in `ai-chat-landing/` (port 3000)
- Chrome started with `--remote-debugging-port=9240` (rendered checks)
- Live Dify stack (needed to send a real message and watch the indicator)

## Validate

1. **Static gates**:
   ```sh
   cd ai-chat-landing && pnpm typecheck && pnpm lint && pnpm test
   ```
   Expect: tsc clean, eslint clean, 79/79 vitest.

2. **Old-indicator grep** (T4):
   ```sh
   grep -rn "animate-pulse rounded-full bg-current\|animation-delay\|h-4 w-2 animate-pulse rounded-sm bg-foreground/50" ai-chat-landing/app/
   ```
   Expect: zero output (both old indicators fully replaced).

3. **Rendered checks** (T1/T2/T3/T5/T6 per
   `contracts/thinking-indicator.md`): send a message and watch — the
   blue ring + "Thinking" appear while waiting and while streaming; they
   vanish when the reply completes (footer shows); deleting mid-stream
   clears everything; the icon is `aria-hidden` and the spin is
   `motion-safe:`-gated.

4. **Manual sanity**: send any question — a blue spinning ring + bold
   "Thinking" shows in place of the old gray dots/bar, and disappears
   when the answer lands.

## Failure triage

- Gray dots or the gray bar still show → the old blocks weren't replaced
  (FR-004 — the grep should find them).
- The indicator never disappears → the render isn't gated on
  `m.streaming` (the component must render only while the flag is true).
- The ring is static for everyone → the class is `motion-safe:animate-spin`,
  which is static only under reduced-motion OS settings (expected); for a
  spinning ring use a normal-motion environment.
