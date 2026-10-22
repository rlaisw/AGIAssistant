# Contract: Rename Mapping (spec 017)

The complete, closed set of edits. "Rendered check" is the acceptance
instrument (CDP text-content assertion, per research R3); "file check" is
the edit-time anchor.

| # | File:line | Surface | Old string | New string | Rendered check |
|---|---|---|---|---|---|
| 1 | app/page.tsx:594 | sidebar brand | `AI Chat` | `AGI Chat` | sidebar text contains "AGI Chat" |
| 2 | app/page.tsx:678 | header badge | `AgenticRAG` | `AGI Chat` | header text contains "AGI Chat" |
| 3 | app/page.tsx:820 | assistant footer | `AgenticRAG` | `AGI Chat` | after a real send: reply footer shows "AGI Chat" |
| 4 | app/page.tsx:872 | composer placeholder | `Message AI Chat…` | `Message AGI Chat…` | textarea placeholder attr |
| 5 | app/page.tsx:885 | composer label | `AgenticRAG` | `AGI Chat` | composer row text |
| 6 | app/page.tsx:900 | footer disclaimer | `AI Chat can make mistakes…` | `AGI Chat can make mistakes…` | footer text |
| 7 | app/layout.tsx:16 | tab title | `AI Chat — A simple, modern interface for AI conversations` | `AGI Chat — A simple, modern interface for AI conversations` | `document.title` starts with "AGI Chat" |
| 8 | lib/pdf-export/render.tsx:45 | PDF metadata line | `Exported … · AgenticRAG Chat` | `Exported … · AGI Chat` | exported PDF text contains "· AGI Chat" |

**Negative check (FR-008/SC-001):** after the edit, a bounded grep of
`ai-chat-landing/{app,components,lib,public}` for `AgenticRAG|AI Chat`
returns zero matches, and the rendered document text contains neither
string.

**Boundary check (FR-009/SC-002):** `git diff --name-only` is limited to
the three source files above plus `ai-chat-landing/README.md` (the single
badge-description line); every other file is untouched.

**Failure modes (verification script):** same loud guards as the spec 016
script — Chrome :9240 unreachable → exit 1 with the startup hint; :3000
not serving → exit 1; selector/text probe missing → exit 1 naming the
probe; measurement timeout → exit 1 (never record a pass from a missing
measurement).
