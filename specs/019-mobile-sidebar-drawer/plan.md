# Implementation Plan: Mobile Sidebar Drawer

**Branch**: `019-mobile-sidebar-drawer` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/019-mobile-sidebar-drawer/spec.md`

## Summary

Make the sidebar reachable on mobile: below 768px the existing `aside`
becomes a fixed left overlay (with a dim backdrop) opened by the sidebar
toggle and closed by backdrop tap, Escape, toggle, or picking a
conversation/New chat. Desktop (≥768px) keeps today's static column.
Spec 016's "no sidebar on mobile" edge case is superseded; the persisted
layout script's T6 asserts the new intent (drawer closed on fresh load).

## Technical Context

- **Language/Version**: TypeScript (Next.js 16.4, React 19.3, Tailwind v4)
- **Primary Dependencies**: none added (no drawer library — the shadcn
  luma preset has no Sheet primitive; verified)
- **Storage**: N/A (presentational state only)
- **Testing**: `pnpm typecheck && pnpm lint && pnpm test` (79/79); CDP
  drawer checks D1–D7 + the full wide-layout matrix re-run (regression)
- **Constraints**: desktop behavior byte-identical; zero new deps; the
  deferred mount-close must not synchronously setState in an effect
  (`react-hooks/set-state-in-effect` — caught by lint, deferred via
  macrotask)

## Constitution Check

- **I. Contract Preservation**: PASS — UI-only.
- **II. Tests-First**: PASS — the CDP D1–D7 runnable check plus the full
  wide-layout matrix (spec 016 regression) both executed green.
- **III. Minimal Dependencies**: PASS — zero (no Sheet/Drawer library).
- **IV. Honest Answers**: PASS — the D7 backdrop check initially asserted
  presence instead of visibility (the `md:hidden` element exists in the
  desktop DOM); fixed and reported.
- **V. Spec-Driven Replacement**: PASS — supersedes the hidden-only mobile
  behavior deliberately (016's edge case amended in the spec).

## Design

- Overlay: `aside` gets `fixed inset-y-0 left-0 z-50` below md, and
  `md:static` restores the static column (same width/bg as today).
- Backdrop: sibling `div` `fixed inset-0 z-40 bg-black/40 md:hidden`,
  click closes.
- Close paths: backdrop, Escape (window keydown listener), toggle, and
  selecting a conversation row or "New chat" (mobile-width check at the
  call site).
- Mount close: deferred `setTimeout(0)` closes the drawer below md on
  load (avoids `react-hooks/set-state-in-effect`; the ~1-frame flash is
  accepted per spec Assumptions).

## Verification

1. Gates: typecheck, lint, 79/79 vitest — green.
2. CDP `drawer-check.mjs` D1–D7: closed on 390px load; toggle → fixed
   left overlay (256px) + backdrop; backdrop click closes; Escape closes;
   New chat closes; search filters rows inside the drawer; desktop static
   with backdrop hidden — all green.
3. Wide-layout matrix T1–T9 re-run — all green (T6 updated to the new
   intent; T7 section re-loads at desktop after the mobile leg).
