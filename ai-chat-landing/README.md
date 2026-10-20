# AI Chat — AgenticRAG Chat UI

A Chatbot-UI-style chat frontend for the **AgenticRAG** Dify chatflow, built with Next.js 16, Tailwind CSS v4, and shadcn/ui on Base UI primitives (luma preset).

Questions typed here go to the Dify chatflow's Service API, and the AgenticRAG agent's answer streams back — markdown (headings, tables, images), a reasoning panel, and source badges rendered inline.

## Quickstart

```bash
pnpm install
pnpm dev          # http://localhost:3000
```

Press `d` (or the sun/moon icon) to toggle Dark / Light / System.

## Dify configuration

Create an app API key — Dify UI → AgenticRAG app → **API Access** → Create Secret Key (format `app-…`) — and put it in `.env.local`:

```bash
DIFY_API_BASE_URL=http://localhost/v1
DIFY_API_KEY=app-xxxxxxxxxxxxxxxx
```

`next dev` watches `.env.local` and reloads it automatically; `next start` reads it at boot. Without a key (or with Dify down) the UI silently falls back to canned demo replies.

## How it works

```
Browser ── POST /api/chat ──► Next.js route (app/api/chat/route.ts)
                               │  Bearer DIFY_API_KEY — key stays server-side
                               ▼
                     Dify POST /v1/chat-messages (response_mode: streaming)
                               │  SSE: message · reasoning_chunk · message_end · ping
                               ▼
                     proxy re-emits line-delimited JSON:
                     chunk · reasoning · replace · sources · ping · done
                               ▼
Browser appends chunks to the streaming bubble (throttled to 100 ms),
stores Dify's conversation_id per chat for multi-turn context.
```

- `message_end` retriever resources → source badges; `reasoning_chunk` and ` Mohammad...` blocks → the reasoning panel
- Dify keep-alive pings are forwarded; a 120 s silent-connection watchdog aborts and shows a note instead of hanging forever
- Conversation history sidebar, static AgenticRAG badge (the chatflow's model is fixed server-side), theme dropdown; per-chat Dify `conversation_id` keeps agent memory across turns
- Deck links in answers render as an action bar (⬇ Download / 👁 Preview-Edit) opening the sidecar's completion page (`/decks/<project>/<stem>/`) with per-slide previews — URL recognition and derivation live in `lib/deck-url.ts`

## Stack

Next.js 16 (App Router, Turbopack) · React 19 · Tailwind CSS v4 · shadcn/ui (Base UI, luma preset) · react-markdown (GFM tables + images) · lucide-react icons

shadcn components installed: button, badge, card, accordion, avatar, table, separator, input, textarea, dropdown-menu. The shadcn agent skill lives in `.agents/skills/shadcn/`.

## Testing

`pnpm test` runs vitest over `lib/**/*.test.ts` (pure logic — currently the deck-URL recognition/derivation). Browser-facing behavior is covered by the deploy battery's `chat-ui-liveness` and `chat-journey` scenarios (`python -m agentic_rag_mcp.deploy verify` from the repo root).

## Notes

- `pnpm build` while `pnpm dev` is running clobbers the shared `.next/` directory and can kill in-flight streams — validate with `pnpm typecheck && pnpm lint` instead, or build in a separate checkout
- `next dev` prints "Port 3000 is in use / Another next dev server is already running" when a stale server holds the port — `kill <pid>` from the message and restart
