# Contract: Wide Chat Layout

Layout-only contract; measured via CDP (SC-001–SC-003). "Content area" =
viewport width minus the open sidebar (256px). `w` = computed width of the
column's outer box, rounded to 1px tolerance.

| # | Viewport | Sidebar | Expected width | Asserts |
|---|---|---|---|---|
| T1 | 1440×900 | open | ≈1066px (90% of 1184) | SC-001 (≥85%) |
| T2 | 1440×900 | closed | ≈1296px (90% of 1440) | FR-001 sidebar-relative |
| T3 | 1920×1080 | open | 1400px exactly (cap binds) | FR-001 cap |
| T4 | 1280×800 | open | ≈922px (xl boundary, wider than 768) | FR-001 |
| T5 | 1279×800 | open | ≤768px (xl inactive — identical to today) | FR-002 |
| T6 | 390×844 | n/a | full width minus padding, no sidebar | FR-002 mobile |
| T7 | 1440×900 | open | long user bubble ≤672px; assistant block = column width | FR-003 / SC-003 |
| T8 | 1440×900 | open | PDF export file produced; pagination vs baseline | SC-004 |
| T9 | 1440×900 | open | sidebar buckets render; Load more paginates; delete flow works | FR-005 / SC-005 |

Composer width must equal the message column width at every T1–T6 point
(the two share the same class contract).

## Script failure modes (error handling)

1. Chrome :9240 unreachable → exit 1 with the `--remote-debugging-port=9240`
   startup hint (no silent retry).
2. `:3000` not serving → exit 1 before any measurement (never measure the
   wrong app).
3. Selector missing (column/composer/bubble) → exit 1 naming the selector —
   this is the class-drift regression alarm.
4. Measurement timeout (5s) → exit 1; never record a missing measurement as
   a passing width.
5. No pre-change PDF baseline → save current output as the baseline and
   report T8 "baseline-established"; never fabricate a comparison
   (Constitution IV).
