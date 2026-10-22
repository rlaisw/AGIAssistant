# Contract: Landing Checks (spec 020)

## Check matrix T1–T6

| # | Check | Method | Expected |
|---|---|---|---|
| T1 | Fresh load empty state (desktop) | CDP navigate 1440×900 | header title "New chat"; "How can I help you today?" visible; 0 message bubbles; 4 suggestion cards |
| T2 | Fresh load empty state (mobile) | CDP navigate 390×844 | same as T1; drawer closed (spec 019) |
| T3 | Fixtures gone | grep `app/` for fixture titles ("Q3 roadmap draft" and the four siblings) | 0 matches |
| T4 | First send from the initial draft | CDP throwaway: type marker into the initial draft, Enter | sidebar row appears with the marker title; reply streams; delete throwaway (cleanup) |
| T5 | Fallback preserved by construction | grep `app/page.tsx` for `cannedReplies` and `demoStream` | both present (the Dify-down fallback is untouched code; an outage is not simulated) |
| T6 | Regression scope | re-run `scripts/wide-layout.mjs` (structural), drawer-check, search-check (basic) | all green |

## Error-handling expectations (from research)

- `activeId` not found → `conversations[0]` fallback (no crash).
- Deterministic SSR/client initial state (no hydration mismatch).
- Empty draft keeps PDF export disabled (no messages).
- Reload returns to a fresh draft (unchanged behavior).

## Failure modes (verification script)

Chrome :9240 unreachable → exit 1 with the startup hint; :3000 not
serving → exit 1; probe not found → exit 1 naming the probe; timeout →
exit 1 (no fabricated pass).
