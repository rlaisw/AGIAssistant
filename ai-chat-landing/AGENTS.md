<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Project — AI Chat (AgenticRAG Chat UI)

Chatbot-UI-style frontend for the Dify "AgenticRAG" chatflow. `app/api/chat/route.ts` proxies `POST /api/chat` → Dify `POST {DIFY_API_BASE_URL}/chat-messages` (streaming SSE re-emitted as line-delimited JSON: chunk · reasoning · replace · sources · ping · done). The API key lives in `.env.local` (git-ignored) and stays server-side.

- `app/page.tsx` — the whole chat app (client component): sidebar, streaming bubbles, 100 ms throttled state flushes, `parseAnswer` think-tag stripping, 120 s connection watchdog, theme switcher
- `components/markdown.tsx` — react-markdown (GFM + breaks) mapped to shadcn elements; images render inline; deck links (`/exports/…pptx` or `/decks/…/` URL families, via `lib/deck-url.ts`) render as the action bar (`components/deck-actions.tsx` — ⬇ Download / 👁 Preview-Edit)
- No key / Dify down → canned demo replies (fallback mode)
- Validation: `pnpm typecheck && pnpm lint` — NEVER `pnpm build` while `pnpm dev` runs (shared `.next/`)
- Component conventions: follow the shadcn skill in `.agents/skills/shadcn/`
