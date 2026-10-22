# Data Model: Wide Chat Layout

No entities, no state machines, no persistence — the feature is three
Tailwind class-string edits in `ai-chat-landing/app/page.tsx`.

The only "model" is the width contract, expressed in CSS and measured in
`contracts/wide-layout.md`:

- content area = viewport − 256px (open sidebar) or viewport (closed/mobile)
- column/composer width = `min(90% × content area, 1400px)` for ≥1280px
  viewports; `max-w-3xl` (768px) otherwise
- user bubble width = `min(85% × column, 672px)` for ≥1024px viewports;
  `85% × column` otherwise
