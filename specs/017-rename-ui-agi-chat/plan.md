# Implementation Plan: Rename UI Skin to AGI Chat

**Branch**: `017-rename-ui-agi-chat` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-rename-ui-agi-chat/spec.md`

## Summary

Replace the eight user-visible brand strings "AgenticRAG" / "AI Chat" with
"AGI Chat" across the Chat UI surface — seven in the live page (sidebar
brand, header badge, assistant footer, composer placeholder + label, footer
disclaimer, tab title) plus the exported-PDF metadata line — with a hard
scope boundary: the backend system name stays untouched everywhere else.

## Technical Context

- **Language/Version**: TypeScript (Next.js 16.4, React 19.3, Tailwind v4)
- **Primary Dependencies**: none added — static string edits only
- **Storage**: N/A
- **Testing**: `pnpm typecheck && pnpm lint && pnpm test` (vitest 71/71);
  rendered verification via CDP (Chrome `--remote-debugging-port=9240`,
  `pnpm dev` on :3000) — text-content assertions on the rendered document,
  following the spec 016 pattern
- **Target Platform**: web (desktop/mobile responsive), Chat UI at :3000
- **Project Type**: web frontend (Next.js App Router)
- **Performance Goals**: N/A (cosmetic)
- **Constraints**: no change outside the eight enumerated strings (plus one
  README accuracy line); backend artifacts byte-identical
- **Scale/Scope**: 8 strings across 3 source files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Contract Preservation**: PASS — no API, tool schema, or response
  shape changes; pure presentation-layer text.
- **II. Tests-First**: PASS — the change is trivial (string literals); the
  runnable check is the CDP rendered-page brand assertion (SC-001) written
  alongside the diff; the full gates must stay green (SC-003).
- **III. Minimal Dependencies**: PASS — zero new dependencies.
- **IV. Honest Answers**: PASS — verification reports what was actually
  measured (rendered text vs. file content); no claimed "rebrand" beyond
  the enumerated surfaces.
- **V. Spec-Driven Replacement**: PASS — supersedes the old label strings;
  no dead code (icons/imports unchanged, all seven site edits are
  in-place).

No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/017-rename-ui-agi-chat/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (no entities — mapping table)
├── quickstart.md        # Phase 1 output (validation guide)
├── contracts/           # Phase 1 output (rename mapping contract)
│   └── rename-mapping.md
├── checklists/
│   └── requirements.md  # (from /speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
ai-chat-landing/
├── app/
│   ├── page.tsx            # 6 strings: 594 brand, 678 badge, 820 assistant
│   │                       #   footer, 872 placeholder, 885 composer, 900 disclaimer
│   └── layout.tsx          # 1 string: metadata title (16)
├── lib/pdf-export/
│   └── render.tsx          # 1 string: exported-PDF metadata line (45)
└── README.md               # 1 line: badge-text description touch-up (45)
```

**Structure Decision**: single Next.js app; the three source files above
are the entire change surface. `README.md` is documentation, not shipped
UI — its edit is the accuracy touch-up permitted by FR-009.

## Verification

1. `pnpm typecheck && pnpm lint && pnpm test` — all green (no test
  references the brand strings — verified at plan time).
2. CDP brand check at 1440×900: document text contains "AGI Chat" and zero
  occurrences of "AgenticRAG"/"AI Chat" across sidebar, header, composer,
  footer; assistant footer verified with a live throwaway conversation
  (reuses the smoke script's send/delete flow, or a manual send).
3. Export a PDF from the same conversation; the metadata line reads
  "… · AGI Chat".
4. `git diff --name-only` restricted to the four files listed above
  (3 source + README) — nothing else changes (SC-002).
