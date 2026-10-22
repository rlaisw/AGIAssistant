# Quickstart: Sidebar Full-Text Search

## Prerequisites

- `pnpm dev` running in `ai-chat-landing/` (port 3000)
- Chrome started with `--remote-debugging-port=9240` (rendered checks C1–C6)
- Live Dify stack (only C3 needs a real reply — reuses the throwaway
  send/delete flow)

## Validate

1. **Static gates** (always):
   ```sh
   cd ai-chat-landing && pnpm typecheck && pnpm lint && pnpm test
   ```
   Expect: tsc clean, eslint clean, vitest green — including the 8 new
   `lib/history/search.test.ts` cases (T1–T8 in
   `contracts/search-filter.md`).

2. **Rendered checks** (C1–C6 per the contract): drive the page headless
   and type into the sidebar search — rows filter live, "BAR"/"bar"
   identical, a reply-only word surfaces its conversation, a nonsense
   query shows "No conversations match", × and Escape restore, and
   delete/Load more/open stay green while searching.

3. **Manual sanity** (30 seconds): type a word from a conversation title
   in mixed case — the sidebar filters; press × — the full grouped list
   returns; type gibberish — the explicit empty state appears, never a
   blank sidebar.

## Failure triage

- Filtering does nothing → the query state isn't wired to the memo
  (`page.tsx`); `ChatHistory` receives unfiltered records.
- Everything matches or nothing matches → the matcher isn't trimming or
  lowercasing (see `lib/history/search.ts`).
- "No conversations match" shows during loading → the empty state isn't
  gated on `status === "ready"` (research R5 — a claim the UI must never
  make).
- A demo/draft conversation "matches" → the corpus includes local
  drafts; the sidebar renders backend rows only (double-clarified corpus
  boundary).
