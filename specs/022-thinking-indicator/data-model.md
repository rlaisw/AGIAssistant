# Data Model: "Thinking" Assistant Indicator

No persistence, no entities — one presentational component tied to the
existing message `streaming` state.

## `ThinkingIndicator` (presentational)

```text
row:      flex items-center gap-2 pt-2.5 text-muted-foreground, role="status"
icon:     LoaderCircle — size-4, motion-safe:animate-spin,
          text-[#82D2F6], aria-hidden="true"  (decorative)
label:    span — text-sm font-semibold, theme default color: "Thinking"
```

## Usage conditions (render logic, on the existing `m.streaming` flag)

| State | Renders |
|---|---|
| `streaming && !m.text` (waiting for first chunk) | the indicator row (replaces the three-dot block) |
| `streaming && m.text` (text arriving) | the indicator row below the content (replaces the inline caret) |
| `!streaming` (complete / error / aborted) | nothing — the message footer shows as usual |

## Removed

```text
- three pulsing dot spans (waiting block): animate-pulse rounded-full
  bg-current with [animation-delay:150ms] / [animation-delay:300ms]
- streaming caret span: ml-1 inline-block h-4 w-2 animate-pulse
  rounded-sm bg-foreground/50
```
