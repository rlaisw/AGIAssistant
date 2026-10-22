# Quickstart: Landing Page Starts on "New Chat"

## Prerequisites

- `pnpm dev` running in `ai-chat-landing/` (port 3000)
- Chrome started with `--remote-debugging-port=9240` (T1/T2/T4)
- Live Dify stack (only T4's first-send throwaway needs it)

## Validate

1. **Static gates**:
   ```sh
   cd ai-chat-landing && pnpm typecheck && pnpm lint && pnpm test
   ```
   Expect: tsc clean, eslint clean, 79/79 vitest.

2. **Fixture grep** (T3):
   ```sh
   grep -rn "Q3 roadmap draft\|Refactor auth flow\|Onboarding email sequence" ai-chat-landing/app
   ```
   Expect: zero output.

3. **Rendered checks** (T1/T2 per `contracts/landing-checks.md`): fresh
   load shows header "New chat" + the empty state with 4 suggestion cards
   at 1440×900 and 390×844; zero message bubbles.

4. **First-send check** (T4): type a marker into the initial draft,
   Enter — the sidebar gains a row with the marker title and the reply
   streams; delete the throwaway.

5. **Regression scope** (T6): `node scripts/wide-layout.mjs` (structural)
   + drawer-check + search-check — all green.

6. **Manual sanity**: hard-refresh the app — you should land on "New
   chat" with "How can I help you today?", never on a pre-filled thread.

## Failure triage

- Landing shows an old demo thread → the initializer wasn't replaced
  (still using `initialConversations`).
- Header crashes on load → the initializer is an empty array (R1 forbids
  it; `active` must resolve to the draft).
- A send fails to create a sidebar row → check the throwaway flow from
  specs 014–015; the initial draft is a normal draft, so the upsert path
  must work identically.
