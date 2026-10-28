<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Project — AGI Chat (AgenticRAG Chat UI)

Chatbot-UI-style frontend for the Dify "AgenticRAG" chatflow. `app/api/chat/route.ts` proxies `POST /api/chat` → Dify `POST {DIFY_API_BASE_URL}/chat-messages` (streaming SSE re-emitted as line-delimited JSON: chunk · reasoning · replace · sources · ping · done). The API key lives in `.env.local` (git-ignored) and stays server-side.

- `app/page.tsx` — the whole chat app (client component): sidebar, streaming bubbles, 100 ms throttled state flushes, `parseAnswer` think-tag stripping, 120 s connection watchdog, theme switcher
- `components/markdown.tsx` — react-markdown (GFM + breaks) mapped to shadcn elements; images render inline; deck links (`/exports/…pptx` or `/decks/…/` URL families, via `lib/deck-url.ts`) render as the action bar (`components/deck-actions.tsx` — ⬇ Download / 👁 Preview-Edit)
- `app/api/conversations/` — proxies Dify `/v1/conversations*`: history list, resume messages, and delete (backend-real, spec 014–015); `lib/history/` groups sidebar rows by recency; `lib/history/search.ts` + `search.test.ts` back the sidebar case-insensitive search (spec 018); `lib/pdf-export/` renders the header ⬇ conversation PDF (spec 013; remote images are rewritten through `app/api/image-proxy` so html2canvas's CORS-mode raster keeps them — failures degrade to labeled links)
- Below md the sidebar renders as an overlay drawer (backdrop, Escape, selection closes it — spec 019); initial state is a fresh `c-0` "New chat" draft — the demo fixtures were removed (spec 020); the empty state renders six feature cards (3-col desktop grid) — body-click sends the example prompt, the label is a new-tab link (spec 021); CDP checks live in `scripts/` (wide-layout.mjs, landing-check.mjs, welcome-cards.mjs)
- `scripts/wide-layout.mjs` — CDP acceptance script for the wide chat layout: ≥1280px column `min(90%,1400px)`, 672px user-bubble ceiling; `--smoke` runs the behavioral checks (spec 016)
- No key / Dify down → canned demo replies (fallback mode)
- Validation: `pnpm typecheck && pnpm lint` — NEVER `pnpm build` while `pnpm dev` runs (shared `.next/`)
- Component conventions: follow the shadcn skill in `.agents/skills/shadcn/`
