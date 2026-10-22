# Research: Rename UI Skin to AGI Chat

## R1 — Completeness of the target set

- **Decision**: the rename surface is exactly eight strings across three
  source files (`app/page.tsx` ×6, `app/layout.tsx` ×1,
  `lib/pdf-export/render.tsx` ×1).
- **Rationale**: bounded re-verification across `app/`, `components/`,
  `lib/`, and `public/` (2026-10-22, double-clarify pass) — this found the
  PDF metadata line that an `app/`-scoped grep and a capped full-repo grep
  had missed; no Next.js error/not-found/loading pages exist; no other
  component or lib file carries the names.
- **Alternatives considered**: relying on the original seven-location list
  — rejected; would have shipped PDFs still branding "AgenticRAG Chat".

## R2 — Test coupling

- **Decision**: no test changes needed.
- **Rationale**: grep of all `lib/**/*.test.ts` and snapshot files for
  "AgenticRAG" / "AI Chat" returned zero matches; vitest is pure-logic and
  never renders these strings.
- **Alternatives considered**: updating a snapshot in lockstep — unnecessary
  (no snapshot exists).

## R3 — Verification approach

- **Decision**: CDP text-content assertions on the rendered page plus one
  exported PDF, reusing the spec 016 headless-Chrome pattern (Chrome
  `--remote-debugging-port=9240`, `pnpm dev` on :3000).
- **Rationale**: the acceptance is "what the user sees" (SC-001), which is
  a rendered-document property; file-grep alone can't see the assistant
  footer or the placeholder rendering. The assistant footer needs a real
  assistant reply — the smoke flow (fresh draft → send → verify → delete)
  already exists and reuses cleanly.
- **Alternatives considered**: vitest-only — rejected (tautological string
  presence, and it can't verify the rendered page or the PDF output).

## R4 — Tab-title handling

- **Decision**: prefix-swap only: "AGI Chat — A simple, modern interface
  for AI conversations" (keep the descriptive subtitle).
- **Rationale**: satisfies FR-007 ("must begin with AGI Chat") with the
  smallest edit; the subtitle contains no brand string ("AI conversations"
  is not the renamed token).
- **Alternatives considered**: full replacement with bare "AGI Chat" —
  rejected (drops useful tab description for zero benefit).

## R5 — Scope boundary enforcement

- **Decision**: verify SC-002 via `git diff --name-only` restricted to the
  four listed files (three source files + the one README line); anything
  else changing fails acceptance.
- **Rationale**: FR-009's "backend name byte-identical" is only honest if
  the diff is confined and inspected.
- **Alternatives considered**: trust the change review — rejected
  (Constitution IV: measure, don't assume).
