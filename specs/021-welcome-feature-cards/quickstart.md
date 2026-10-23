# Quickstart: Welcome Feature Cards

## Prerequisites

- `pnpm dev` running in `ai-chat-landing/` (port 3000)
- Chrome started with `--remote-debugging-port=9240` (T1–T5)
- Live Dify stack (only T3's send needs it; T1/T2/T4/T5 are render-only)

## Validate

1. **Static gates**:
   ```sh
   cd ai-chat-landing && pnpm typecheck && pnpm lint && pnpm test
   ```
   Expect: tsc clean, eslint clean, 79/79 vitest.

2. **Rendered checks** (T1–T5 per `contracts/welcome-cards.md`): fresh
   load shows six cards with the exact titles/descriptions (3-col grid at
   1440, stacked at 390); clicking a card's button sends its label as a
   user bubble (verified on two cards: 1 and 6); all six label links carry
   `example1–6.html` hrefs with `target="_blank"`; a label click sends
   nothing. Run them via `node ai-chat-landing/scripts/welcome-cards.mjs`
   (Chrome on :9240).

3. **Regression scope** (T6): the spec-020 landing check with the
   card-count updated to 6 (`suggestions === 4` → `6`) + the wide-layout
   matrix — both green.

4. **Manual sanity**: fresh load → six feature cards under "How can I
   help you today?"; clicking a card body puts its prompt in the chat;
   clicking the small label opens the placeholder URL in a new tab (404
   expected until the real pages exist).

## Failure triage

- Only 4 cards → the old `suggestions` array wasn't replaced.
- Label click sends a message → the link is nested inside the button
  (R2 forbids it — make them siblings).
- Links 404 and that's surprising → read the spec's Edge Cases: the URLs
  are documented placeholders until the real help pages exist.
