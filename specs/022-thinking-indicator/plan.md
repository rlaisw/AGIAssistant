# Implementation Plan: "Thinking" Assistant Indicator

**Branch**: `022-thinking-indicator` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/022-thinking-indicator/spec.md`

## Summary

Replace the assistant's two in-progress indicators (three gray pulsing dots
while waiting, gray streaming caret while streaming) with one unified
indicator: a small local `ThinkingIndicator` component — a spinning lucide
`LoaderCircle` in `#82D2F6` plus bold "Thinking" text — shown as its own row
in both states and cleared exactly when generation ends.

## Technical Context

- **Language/Version**: TypeScript (Next.js 16.4.2, React 19.3, Tailwind v4)
- **Primary Dependencies**: none added — `lucide-react` is already installed
  (house icon library); `motion-safe:animate-spin` is built-in
- **Storage**: N/A
- **Testing**: `pnpm typecheck && pnpm lint && pnpm test` (79/79); CDP
  checks T1–T6 (contracts/thinking-indicator.md); no vitest additions
  (presentational component — house convention, research R3)
- **Target Platform**: web (both themes; decorative ring + bold text signal)
- **Constraints**: fully replaces both old indicators (grep-verified); zero
  new dependencies; lifecycle rides the existing `streaming` flag

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Contract Preservation**: PASS — presentational only.
- **II. Tests-First**: PASS — the runnable check is the CDP matrix
  (contracts/thinking-indicator.md T1–T6) defined before the edit.
- **III. Minimal Dependencies**: PASS — zero (existing lucide install).
- **IV. Honest Answers**: PASS — the decorative ring carries `aria-hidden`
  and the accessible signal is the bold text (stated, not implied); the
  reduced-motion static-ring behavior is documented.
- **V. Spec-Driven Replacement**: PASS — both old indicators fully replaced;
  no dead indicator code (grep-verified).

No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/022-thinking-indicator/
├── plan.md              # This file
├── research.md          # R1–R4 decisions + error handling
├── data-model.md        # Indicator component + usage conditions
├── contracts/
│   └── thinking-indicator.md  # T1–T6 check matrix + error handling
├── quickstart.md        # Validation guide
├── checklists/
│   └── requirements.md  # (from /speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
ai-chat-landing/app/
└── page.tsx            # add ThinkingIndicator component + lucide import;
                        # replace the waiting-dots block and the streaming
                        # caret span with it (~10 lines changed)
```

**Structure Decision**: one app file; one tiny local component used in both
spots (no duplication drift).

## Design

- **Component** (`page.tsx`, top-level):
  `ThinkingIndicator` → a row (`flex items-center gap-2 pt-2.5`,
  `role="status"`) containing `LoaderCircle`
  (`size-4 motion-safe:animate-spin text-[#82D2F6]`, `aria-hidden="true"`)
  and the bold label (`text-sm font-semibold`, theme default color).
- **Usage**:
  - Waiting (`streaming && !m.text`): replaces the three-dot block.
  - Streaming (`streaming && m.text`): replaces the inline caret — renders
    as its own row below the content (placement pin from Clarifications).
  - Complete/error/abort (`!streaming`): nothing renders (footer shows).
- **Lifecycle**: rides the existing `m.streaming` flag — no new state.

## Verification

1. Gates: typecheck, lint, 79/79 vitest.
2. CDP T1–T6 per `contracts/thinking-indicator.md`: waiting state shows the
   ring (spin computed, color `#82D2F6`, "Thinking" bold, dots gone);
   streaming state shows the same indicator below content (caret gone);
   completion clears it (footer shows); delete-mid-stream clears it;
   `aria-hidden` + `motion-safe` gate + `role="status"` present; old
   indicator grep returns zero.
