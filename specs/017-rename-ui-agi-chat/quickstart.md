# Quickstart: Rename UI Skin to AGI Chat

## Prerequisites

- `pnpm dev` running in `ai-chat-landing/` (port 3000)
- Chrome started with `--remote-debugging-port=9240` (rendered checks)
- Live Dify stack (only for the assistant-footer scenario, which needs a
  real reply — the smoke flow sends and deletes one throwaway conversation)

## Validate

1. **Static gates** (always):
   ```sh
   cd ai-chat-landing && pnpm typecheck && pnpm lint && pnpm test
   ```
   Expect: tsc clean, eslint clean, 71/71 vitest.

2. **Negative file check** (instant, proves FR-008 coverage):
   ```sh
   grep -rn "AgenticRAG\|AI Chat" ai-chat-landing/app ai-chat-landing/components ai-chat-landing/lib ai-chat-landing/public
   ```
   Expect: zero output.

3. **Rendered check** (per `contracts/rename-mapping.md`, rows 1–7):
   drive the page headless (Chrome on :9240) and assert: sidebar + header
   contain "AGI Chat"; textarea placeholder is "Message AGI Chat…";
   composer label and footer disclaimer read "AGI Chat";
   `document.title` starts with "AGI Chat". Then send a throwaway message,
   wait for the reply footer, assert "AGI Chat", and delete the throwaway
   (reuse the spec 016 smoke flow).

4. **PDF check** (row 8): export that conversation's PDF; its metadata
   line reads "… · AGI Chat".

5. **Boundary check** (FR-009): `git diff --name-only` lists only the
   three source files + `ai-chat-landing/README.md`.

6. **Manual sanity** (10 seconds): look at the sidebar, header, composer
   and tab — every label reads "AGI Chat".

## Failure triage

- Grep (2) finds a brand string → an 8th+ location exists; extend the
  mapping contract before editing.
- Rendered check shows an old label → the change wasn't hot-reloaded;
  hard-refresh the tab.
- PDF shows "AgenticRAG Chat" → `lib/pdf-export/render.tsx` line ~45 was
  missed (it lives outside `app/`).
