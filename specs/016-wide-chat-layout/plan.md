# Implementation Plan: Wide Chat Layout

## Technical Context

- **Stack**: Next.js 16.4 + React 19.3 + Tailwind CSS v4 (shadcn/ui on Base
  UI, luma preset), app at `ai-chat-landing/`.
- **Touch points**: `ai-chat-landing/app/page.tsx` only — 3 class-string
  edits (message column ~757, composer ~868, user bubble ~761).
- **No new dependencies, no structural changes, no API/schema changes.**

## Constitution Check

- **I. Contract Preservation**: PASS — UI-only; no client-facing tool
  contract, no API shape changes.
- **II. Tests-First**: PASS — the CDP measurement script (SC-001–SC-003) is
  the runnable check; suites must stay green (SC-005).
- **III. Minimal Dependencies**: PASS — Tailwind arbitrary values only.
- **IV. Honest Answers**: PASS — the verification script fails loudly
  (missing selector, unreachable Chrome/dev server, timeout) and never
  records a fabricated pass; SC-004 forbids inventing a baseline.
- **V. Spec-Driven Replacement**: PASS — the base `max-w-3xl` remains as the
  intentional <1280px fallback (not dead code); no retired components.

## Design

Width contract (see `contracts/wide-layout.md` for the full matrix):

| Site | Class string after the change |
|---|---|
| Message column | `mx-auto w-full max-w-3xl xl:max-w-[min(90%,1400px)] space-y-6 p-4 py-6 sm:p-6` |
| Composer | `mx-auto w-full max-w-3xl xl:max-w-[min(90%,1400px)] p-3 sm:p-4` |
| User bubble | `max-w-[85%] lg:max-w-2xl rounded-2xl bg-primary px-4 py-2.5 text-sm text-primary-foreground` |

## Verification

1. `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/` (never
   `pnpm build` while `pnpm dev` runs).
2. `node ai-chat-landing/scripts/wide-layout.mjs` with Chrome on :9240 and `pnpm dev`
   on :3000 — asserts SC-001–SC-003 (T1–T8 matrix) with loud failure modes.
3. PDF export + sidebar smoke (SC-004/SC-005) at the widened layout.
