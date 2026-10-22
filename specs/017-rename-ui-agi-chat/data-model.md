# Data Model: Rename UI Skin to AGI Chat

No entities, no persistence, no state machine — the feature is eight
string-literal replacements.

The only "model" is the rename mapping (see `contracts/rename-mapping.md`):

| # | File | Current string | New string |
|---|---|---|---|
| 1 | app/page.tsx (~594) | AI Chat | AGI Chat |
| 2 | app/page.tsx (~678) | AgenticRAG | AGI Chat |
| 3 | app/page.tsx (~820) | AgenticRAG | AGI Chat |
| 4 | app/page.tsx (~872) | Message AI Chat… | Message AGI Chat… |
| 5 | app/page.tsx (~885) | AgenticRAG | AGI Chat |
| 6 | app/page.tsx (~900) | AI Chat can make mistakes. Check important info. | AGI Chat can make mistakes. Check important info. |
| 7 | app/layout.tsx (~16) | AI Chat — A simple, modern interface for AI conversations | AGI Chat — A simple, modern interface for AI conversations |
| 8 | lib/pdf-export/render.tsx (~45) | … · AgenticRAG Chat | … · AGI Chat |

Validation rule: replacement is literal, one-for-one, in-place; no other
characters on the touched lines change.
