# Data Model: Landing Page Starts on "New Chat"

No persistence, no new entities — an initialization change to existing state.

## Initial state (after the change)

```text
conversations = [
  { id: "c-0", title: "New chat", messages: [] }
]
activeId = "c-0"
```

Identical shape to drafts created by the "New chat" button
(`{ id: "c-N", title: "New chat", messages: [] }`, N ≥ 4 via `idRef`).

## Removed

```text
initialConversations — five pre-filled demo threads
("Q3 roadmap draft", "Refactor auth flow", "Landing page copy",
"SQL query optimization", "Onboarding email sequence")
```

## Untouched (preserved by construction)

```text
cannedReplies / demoStream — the Dify-down fallback replies,
a separate mechanism used by any conversation including the initial draft.
```
