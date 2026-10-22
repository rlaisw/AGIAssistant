# Tasks: Mobile Sidebar Drawer

## Phase 1: Setup

- [x] T001 Create spec artifacts (spec, plan, checklist)

## Phase 2: [US1] Mobile overlay drawer (P1)

Goal: below 768px the sidebar is an on-demand overlay drawer with backdrop; closed on first load; closes via backdrop/Escape/toggle/selection. Desktop unchanged.
Independent test: CDP D1–D7 + wide-layout matrix green.

- [x] T002 [US1] In `ai-chat-landing/app/page.tsx`: wrap the sidebar in a fragment with a backdrop div (`fixed inset-0 z-40 bg-black/40 md:hidden`, click closes) and restyle the `aside` as `fixed inset-y-0 left-0 z-50` below md (`md:static` restores desktop)
- [x] T003 [US1] In `ai-chat-landing/app/page.tsx`: deferred mount close (macrotask, not synchronous setState — lint `set-state-in-effect`) + Escape key listener closing the drawer below md
- [x] T004 [US1] In `ai-chat-landing/app/page.tsx`: close the drawer on mobile when a conversation row is opened or "New chat" is clicked
- [x] T005 [US1] Update `ai-chat-landing/scripts/wide-layout.mjs`: T6 re-navigates fresh at 390×844 and asserts the drawer starts closed (spec 019 supersedes "no sidebar on mobile"); T7 section re-loads at desktop after the mobile leg
- [x] T006 [US1] Write and run the CDP drawer checks D1–D7 *(all green: closed on 390px load; toggle → fixed 256px overlay + backdrop; backdrop/Escape/New-chat close; search filters rows inside the drawer; desktop static with backdrop hidden)*

## Phase 3: Polish

- [x] T007 Run `pnpm typecheck && pnpm lint && pnpm test` — all green *(tsc, eslint, 79/79)*
- [x] T008 Run the full wide-layout matrix — all green (T1–T7, T9)
- [ ] T009 Commit spec artifacts + diff together

## Dependencies

T002–T004 same file (sequential); T005–T006 after the drawer exists; T007/T008 after implementation.

## Implementation strategy

Smallest drawer that works: existing `aside` restyled + one backdrop div + two close paths wired at the call sites — no library, no duplicated sidebar copy.
