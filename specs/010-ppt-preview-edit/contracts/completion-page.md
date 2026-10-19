# Contract — Completion Page & In-Chat Deck Actions (Phase 1)

External interfaces for spec 010. **Constitution I: `ppt_export`'s `file`/`url` and the `/exports/` route are byte-frozen; the only tool change is the additive `page_url` field.**

## 1. `ppt_export` result (additive)

```json
{ "file": "exports/<stem>.pptx",                     // unchanged (spec 009)
  "url": "http://host:28080/exports/<project>/<stem>.pptx",   // unchanged (spec 009)
  "page_url": "http://host:28080/decks/<project>/<stem>/" }  // NEW, always present
```

Preview failure does **not** remove `page_url` — the page then renders degraded mode (FR-008).

## 2. Sidecar HTTP routes (wrapper server)

| Route | Success | Errors |
|---|---|---|
| `GET /decks/<project_id>/<stem>/` | 200 `text/html` — completion page: ordered slide previews, download control (href = the frozen `/exports/` URL), edit path (back-to-chat pointer) | 404 honest page (unknown project/stem or removed artifact); 400 malformed ids |
| `GET /decks/<project_id>/<stem>/slides/<file>` | 200 `image/svg+xml` — one snapshot slide | 404 unknown slide; 400 traversal/malformed |

Both routes validate ids against the same charset as `/exports/` and resolve within the projects root (traversal-safe). Degraded artifacts render each slide as an explicit "preview unavailable" state with the download control still present. No authentication (local-trust posture, FR-009).

## 3. Preview snapshot layout (filesystem contract)

```text
<project>/previews/<stem>/NN_<name>.svg   # ordered, one per page, write-once
<project>/previews/<stem>/.degraded      # marker file when preview generation failed
```

Snapshots are created only by the export flow; a re-export never writes into an existing stem directory (FR-007).

## 4. Chat UI link recognition (deck-url helper)

Pure function, both directions:

```text
http://H/exports/<project>/<stem>.pptx  ⇄  http://H/decks/<project>/<stem>/
```

- Recognizes exactly these two URL families (same host as the deployment); everything else → null (ordinary link, FR-012)
- `DeckActions` component: Download action → `.pptx` URL; Preview/Edit action → page URL; visible icon + label on each; keyboard-focusable links
- Renders in dark/light themes; no layout shift to surrounding markdown

## 5. Test-case matrix (Constitution II — defined before implementation)

Legend: U = unit (`test_ppt_completion.py`), I = integration (`test_ppt_completion_pipeline.py`, real toolchain), C = contract (`test_ppt_completion_contract.py`), V = vitest (`ai-chat-landing`, `deck-url.test.ts`).

| # | Case | Tier | Expected |
|---|------|------|----------|
| D01 | export returns page_url alongside unchanged file+url | I+C | all three fields; `file`/`url` byte-identical to spec 009 shape |
| D02 | export creates snapshot dir with ordered slide SVGs | I | one per written page, numeric order |
| D03 | re-export: second artifact gets its own snapshot; first artifact's page + snapshot unchanged | I | FR-007 isolation (file mtimes/hashes stable) |
| D04 | forced finalize failure: export succeeds, page_url returned, degraded marker written | I | FR-008 |
| D05 | degraded artifact's completion page renders honest unavailable states + working download | U+C | no blank/fabricated slide renderings |
| D06 | completion page HTML contains download href (frozen URL), slide count, edit pointer | U | deterministic fields present |
| D07 | `/decks/<p>/<stem>/` unknown project / stem | C | 404 honest page |
| D08 | `/decks/…/slides/<file>` traversal (`..%2F`, absolute, subdirectory escapes) | C | 400/404; nothing outside the snapshot served |
| D09 | slide asset content-type | C | `image/svg+xml` |
| D10 | malformed ids on decks routes (charset violations) | C | 400 |
| D11 | spec 009 contract suite re-runs green after changes | C | 12/12 existing ppt contract tests + full 274 suite |
| D12 | ppt_export result on missing project | C | unchanged `PPT_INVALID_PROJECT` envelope (no regression) |
| D13 | derivation: exports URL → page URL | V | exact counterpart |
| D14 | derivation: page URL → exports URL | V | exact counterpart |
| D15 | non-deck URLs (google.com, relative paths, other localhost routes) | V | null — ordinary link |
| D16 | malformed deck-family URLs (missing stem, wrong extension) | V | null |
| D17 | snapshot ordering with >1 page (multi-page deck) | I | previews match page order of the deck |
| D18 | completion page on mobile-width viewport | quickstart | readable (browser scenario) |

Fixtures: the spec 009 passing SVG fixture plus a two-page variant under `tests/fixtures/ppt/`.
