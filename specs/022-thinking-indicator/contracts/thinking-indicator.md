# Contract: "Thinking" Indicator (spec 022)

## Indicator contract

One component (`ThinkingIndicator`) rendering a spinning `#82D2F6`
`LoaderCircle` (decorative) + bold "Thinking" text as its own row, shown
while `m.streaming` (waiting or streaming) and gone otherwise.

## Check matrix T1–T6

| # | Check | Expected |
|---|---|---|
| T1 | Waiting state (before first chunk) | indicator row present; icon computed `animation-name: spin` and color `rgb(130, 210, 246)`; bold "Thinking" text present; the three dot spans GONE |
| T2 | Streaming state (text arriving) | indicator row present below the content; the inline caret span GONE |
| T3 | Completion | after the reply completes, the indicator is absent; the message footer (Copy response etc.) shows |
| T4 | Old-indicator grep | zero matches for the dot spans (`animate-pulse rounded-full bg-current`, `animation-delay`) and the caret span (`h-4 w-2 animate-pulse rounded-sm bg-foreground/50`) in `app/` |
| T5 | Delete mid-stream | deleting the streaming conversation (spec-015 path) clears the indicator (draft resets; nothing lingers) |
| T6 | Accessibility | icon has `aria-hidden="true"`; the row has `role="status"`; the class list contains `motion-safe:animate-spin` (reduced-motion gate) |

## Error-handling expectations (from research)

- Error/abort/watchdog/delete all clear the indicator via the `streaming`
  flag — same lifecycle as the replaced caret.
- Reduced motion shows a static ring; the bold text signals state.
- One stream at a time → at most one indicator.

## Failure modes (verification script)

Chrome :9240 unreachable → exit 1 with the startup hint; :3000 not
serving → exit 1; probe not found → exit 1 naming the probe; timeout →
exit 1 (no fabricated pass).
