# Feature Specification: Welcome Feature Cards

**Feature Branch**: `021-welcome-feature-cards`

**Created**: 2026-10-23

**Status**: Draft

**Input**: User description: "enhance welcome new chat page, based on the above chat conversation, adding new feature cards" — replace the four generic suggestion cards in the welcome empty state with a six-card feature showcase (title, emoji icon, one-line description, example-prompt label). The heading "How can I help you today?" and the subtext "Ask anything, or start from a suggestion." are unchanged. Decisions locked in the preceding conversation: card body click sends the example prompt; the label is a hyperlink opening in a new tab; 2×3 desktop grid, stacked on mobile; six placeholder URLs (`http://localhost/example1.html` … `example6.html`) are temporary until real help pages exist.

## Clarifications

### Session 2026-10-23

- Q: What text does a card send on body-click? → A: the example-prompt label text itself (e.g., "How to create PPT"). Cards 1–3 (PowerPoint/Infographic/Chart) map to real agent capabilities (ppt_*/antv_* tools) so those how-to prompts produce useful responses; cards 4–6 (CorpIT/AI Chatbot/Agentic RAG) are navigational — their primary affordance is the link, the send is cosmetic.
- Q: What happens to the old four suggestion prompts (Summarize a document / Write code / Brainstorm ideas / Explain a concept)? → A: fully replaced by the six feature cards — no leftover quick-prompt row; a future variant could re-add one separately.
- Q: Are the uploaded image's styling details covered? → A: the image could not be read by this model (no image input); the design follows the locked text table and the existing shadcn/luma card language — any styling visible only in the image (exact colors, hero art, gradients, footer links) may need a follow-up pass.
- Structure note (from the first pass): the card must not nest a link inside a button (invalid HTML) — the send area and the label link are siblings inside the card container, so propagation separates naturally.
- Q (post-ship, 2026-10-23): change the desktop grid from 2 columns × 3 rows to 3 columns × 2 rows? → A: yes — the grid is now `sm:grid-cols-2 lg:grid-cols-3` with the container widened `max-w-2xl → max-w-4xl` so cards keep ~290px width; mobile stays single-column. FR-002's "two-column grid" is superseded by this amendment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and launch a capability from the welcome page (Priority: P1)

On the fresh "New chat" empty state, the user sees six feature cards
arranged in a three-column grid (two rows) on desktop, a two-column grid at mid widths, and a single-column
stack on mobile. Each card shows a feature title, an emoji icon, and a
one-line description. Clicking anywhere on the card body sends that
feature's example prompt into the chat composer exactly like today's
suggestion cards. Each card's example-prompt label is also a hyperlink to
that feature's help page, opening in a new tab — clicking the label does
not send the prompt. The heading "How can I help you today?" and subtext
are unchanged.

**Why this priority**: the welcome page is the first impression; the six
cards turn it into a capability map of the app (deck generation,
infographics, charts, IT helpdesk, general Q&A, self-hosted RAG).

**Independent Test**: fresh load shows the six cards with the exact
locked titles/descriptions; clicking a card body places its example
prompt into the composer; each label is a link with the expected URL and
opens in a new tab.

**Acceptance Scenarios**:

1. **Given** a fresh load at desktop width, **When** the empty state
   renders, **Then** six cards appear in a three-column, two-row grid (desktop; two columns at mid widths)
   with the exact titles, icons, and descriptions:

   | # | Title | Icon | Description |
   |---|---|---|---|
   | 1 | Generate PowerPoint | 📊 | Create professional PowerPoint from text prompts in minutes |
   | 2 | Generate Infographic | 🎨 | Design eye-catching infographics without design skills |
   | 3 | Draw Chart Diagram | 📈 | Visualize data with interactive charts and flow diagrams |
   | 4 | Talk with CorpIT Helpdesk Chatbot | 💻 | Get instant IT support and troubleshooting guidance |
   | 5 | Ask Any Question with AI Chatbot | 🤖 | Access knowledge across domains with our intelligent assistant |
   | 6 | Create Personal Agentic RAG Document DB | 💾 | Build your own searchable knowledge base with AI-powered Agentic RAG |

2. **Given** the cards, **When** the user clicks a card's body,
   **Then** the card's example prompt is sent into the composer (the
   same send flow as today's suggestion cards) — labels: "How to create
   PPT", "How to create Infographic", "How to create chart diagram",
   "Chat with CorpIT Support", "Ask AI Chatbot", "Create Self-Hosted
   Agentic RAG".
3. **Given** a card's example-prompt label, **When** the user clicks the
   label, **Then** the URL opens in a new tab (`example1.html` …
   `example6.html` mapped 1–6 in table order) and no prompt is sent.
4. **Given** a phone-width viewport, **When** the empty state renders,
   **Then** the six cards stack in a single column and body-send still
   works.

---

### Edge Cases

- Placeholder URLs (`http://localhost/example1.html` … `example6.html`)
  intentionally point at pages that don't exist yet — they will 404
  until the real help pages are created; only the URL strings change
  later (documented temporary state).
- The CorpIT card's prompt is steered at the existing AgenticRAG agent
  (the only backend); the label links to `example4.html` as the
  placeholder for a future CorpIT-specific page.
- The label is a link nested in a clickable card — clicking the label
  must not also trigger the card's send (event propagation stopped).
- The spec-020 landing check asserts "4 suggestion cards" — this feature
  changes the count to 6; that standing check is updated, not broken
  (regression scope).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The welcome empty state MUST render the six locked feature
  cards with the exact titles, emoji icons, and descriptions (Acceptance
  table).
- **FR-002**: Cards MUST lay out as a three-column grid (two rows) at
  ≥1024px, a two-column grid at 640–1023px, and a single-column stack below.
- **FR-003**: Clicking a card's body MUST send the card's example prompt
  into the composer with the same send behavior as today's suggestion
  cards.
- **FR-004**: Each card's example-prompt label MUST be a link to its URL
  (the 1–6 mapping) that opens in a new tab, and clicking the label MUST
  NOT send the prompt.
- **FR-005**: The heading "How can I help you today?" and the subtext
  "Ask anything, or start from a suggestion." MUST be unchanged.
- **FR-006**: No new dependencies; no backend/API changes; the six
  placeholder URLs are documented as temporary.

### Key Entities

- None — a static data set of six cards (title, icon, description,
  prompt label, URL) rendered by the existing empty state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rendered check — six cards with the exact locked
  titles/descriptions; three-column × two-row grid at 1440×900,
  single-column stack at 390×844.
- **SC-002**: Body click on any card sends its example prompt into the
  composer (verified on at least two cards end-to-end).
- **SC-003**: All six labels are links with the expected URLs
  (`example1.html` … `example6.html` in order) and open in a new tab;
  clicking a label sends nothing.
- **SC-004**: Typecheck, lint, and the vitest suite (79) stay green; the
  spec-020 landing check is updated to expect 6 cards and stays green;
  the wide-layout matrix is unaffected.

## Assumptions

- Locked decisions (from the preceding conversation, accepted): body
  click sends the prompt; the label is the external link opening in a
  new tab; 2×3 desktop grid, stacked mobile; six placeholder URLs are
  temporary until real help pages exist; the CorpIT prompt goes to the
  existing AgenticRAG agent; styling stays within the existing
  shadcn/luma card language (border, hover state, icon accent) — modern
  look, no new dependencies.
- The six URLs open in a new tab so navigation never abandons the chat.
- The four old suggestion prompts are fully replaced (not kept as an extra row); cards 4–6 are navigational — their label/link is the primary affordance, and the prompt sent on body-click is the label text (a how-to question the AgenticRAG agent answers in chat).
- The uploaded image could not be read by the implementing model (no image input); the build follows the locked text table and the shadcn/luma card language — image-only styling details may need a follow-up pass.
