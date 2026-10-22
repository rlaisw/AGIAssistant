# Research: Sidebar Full-Text Search

## R1 — Where the filter lives

- **Decision**: filter `historyRecords` in `page.tsx` via `useMemo` and
  pass the filtered array to `ChatHistory`; the query state lives in
  `page.tsx` (the input is already there).
- **Rationale**: `ChatHistory` stays a pure presentational component —
  zero intrusion into the spec-015-verified component (FR-010's
  regression guard). The filter is a data-boundary transformation.
- **Alternatives considered**: pass the query into `ChatHistory` and
  filter inside — rejected (intrudes on the 015 component's props and
  responsibilities).

## R2 — Corpus and content map

- **Decision**: match titles for all rows; content only for rows whose
  `difyId` maps to messages in the `conversations` state (open /
  previously-opened / active-after-upsert).
- **Rationale**: verified from source (double-clarify 2026-10-22): the
  sidebar renders backend rows only; demo drafts have no `difyId` and no
  row. A `difyId → message-text` memo gives O(1) content lookup per row.
- **Alternatives considered**: searching the whole `conversations` state
  — rejected (demo conversations have no sidebar rows; searching them
  would match invisible data — the exact error the double-clarify caught).

## R3 — Matcher as a pure module

- **Decision**: `lib/history/search.ts` — `matchesQuery(text, query)` and
  `filterHistory(records, getContent, query)`; no React.
- **Rationale**: house convention — pure logic gets vitest coverage
  (Constitution II); the matcher is the only non-trivial logic in the
  feature (substring rules, corpus selection, whitespace handling).
- **Alternatives considered**: inline `useMemo` in the page — rejected
  (untestable inline logic; a bug would be invisible until the CDP run).

## R4 — Debounce

- **Decision**: 200 ms debounced mirror of the input value
  (`useState` + `useEffect` timer), filter on the debounced value.
- **Rationale**: filtering a ~100-row list is microseconds — the debounce
  is for list stability (no per-keystroke reflow flicker), not
  performance; 200 ms per the spec's assumption.
- **Alternatives considered**: filter every keystroke — rejected
  (visible flicker on a per-character basis).

## R5 — Empty-state and precedence (error handling)

- **Decision**: the "no conversations match" state renders ONLY in the
  `ready` state with a non-empty trimmed query and zero matches;
  `loading` skeleton and `error` retry states take precedence (existing
  `ChatHistory` behavior); whitespace-only query counts as empty (full
  list); × (aria-label "Clear search", shown only when query non-empty)
  and Escape both reset.
- **Rationale**: searching over an empty or failed history must never
  claim "no matches" — that would misreport a loading/error condition as
  a search result (Constitution IV).
- **Alternatives considered**: always-available empty state — rejected
  (lies during loading).

## R6 — Error handling matrix (user-requested)

| Input/condition | Behavior |
|---|---|
| Query with only whitespace | treated as empty → full list |
| Query with regex metacharacters (`(`, `[`, `.*`) | literal substring — no regex, no injection |
| Query with emoji/CJK | literal Unicode substring match |
| Extremely long query | no special handling (bounded by `includes()` cost on a ~100-row list; no cap needed) |
| History loading/error while typing | skeleton/error UI takes precedence; no empty-search claim |
| Delete a row while searching | filtered list updates via existing `history.remove` + sync |
| Load more while searching | new page rows are filtered by the active query |
| New row (upsert) while searching | appears only if it matches the active query (existing upsert + filter) |
