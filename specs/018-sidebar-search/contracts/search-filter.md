# Contract: Sidebar Search Filter (spec 018)

## Match rules

| Rule | Behavior |
|---|---|
| Title match (all rows) | case-insensitive substring on `record.title` |
| Content match (loaded rows only) | case-insensitive substring on loaded message texts via `getContent(difyId)`; unopened rows have no content → title-only |
| Empty/whitespace query | no filtering — full list |
| Matching style | literal Unicode substring (`toLowerCase().includes()`); never regex |
| Grouping | existing `groupConversations` over filtered rows — empty buckets hidden |

## Vitest matrix (T1–T8, `lib/history/search.test.ts`)

| # | Case | Input | Expected |
|---|---|---|---|
| T1 | Empty query | `""` | all records returned |
| T2 | Whitespace-only query | `"   "` | all records returned |
| T3 | Case-insensitivity | "BAR" / "bar" / "Bar" | identical result sets |
| T4 | Content hit | query in a loaded message, not in title | row included |
| T5 | Title-only fallback (honesty boundary) | query in an unopened row's would-be body only | row NOT included (FR-009 pinned) |
| T6 | Unicode/emoji literal | "📊" in title | literal match, no crash |
| T7 | Regex metacharacters literal | ".*" | no match (treated as literal, not wildcard) |
| T8 | Bucket collapse | query matching rows in only one recency bucket | only that bucket's header + rows |

## States & error handling (from research R5/R6)

| Condition | Rendered |
|---|---|
| loading / error | existing skeleton / error-retry — the search-empty state MUST NOT appear |
| ready + empty query | full grouped list |
| ready + query + matches | filtered list |
| ready + query + zero matches | "No conversations match ‹query›" |
| × (aria-label "Clear search", shown only when query non-empty) or Escape | query reset → full list |

## CDP acceptance checks (C1–C6)

| # | Check | Expected |
|---|---|---|
| C1 | Type a title substring | rows filter live to matches |
| C2 | "BAR" then "bar" | identical row sets (SC-002) |
| C3 | Send a throwaway; search a word from the reply not in the title | row visible (SC-003, US2) |
| C4 | Search a nonsense string | "No conversations match" empty state; no skeleton/error confusion |
| C5 | × and Escape | full list restored |
| C6 | Delete + Load more + open while searching | spec 014/015 behaviors green (FR-010 subset); throwaway deleted at the end |

**Failure modes (verification script):** Chrome :9240 unreachable → exit 1
with the startup hint; :3000 not serving → exit 1; probe not found →
exit 1 naming the probe; measurement timeout → exit 1 (no fabricated
pass).
