# Contract: Welcome Feature Cards (spec 021)

## Card mapping

The six cards render in `data-model.md` order; each card's button sends its
`label` as the prompt and its label `<a>` points at its `url` (target
`_blank`, `rel` includes `noopener`).

## Check matrix T1–T6

| # | Check | Expected |
|---|---|---|
| T1 | Render at 1440×900 | 6 cards; exact titles + descriptions (data-model table); emoji icons present; grid computes to 2 columns |
| T2 | Render at 390×844 | 6 cards; grid computes to 1 column (stacked) |
| T3 | Body click sends the label | click card 1's button → a user bubble appears containing "How to create PPT" (and the send fires normally) |
| T4 | Links correct | all 6 `<a>` elements have the expected `http://localhost/exampleN.html` hrefs in order and `target="_blank"` |
| T5 | Label click sends nothing | click card 2's link → no new user bubble (navigates; nothing sent) |
| T6 | Heading/subtext unchanged + regression | "How can I help you today?" + "Ask anything, or start from a suggestion." intact; spec-020 landing check updated to 6 cards and green; wide-layout matrix green |

## Error-handling expectations (from research)

- Placeholder URLs 404 in a new tab — accepted temporary state.
- Label click never sends (structural sibling separation).
- No nested-interactive markup; no icon library; no new dependencies.
- Old suggestion prompts are superseded (no leftover row).

## Failure modes (verification script)

Chrome :9240 unreachable → exit 1 with the startup hint; :3000 not
serving → exit 1; probe not found → exit 1 naming the probe; timeout →
exit 1 (no fabricated pass).
