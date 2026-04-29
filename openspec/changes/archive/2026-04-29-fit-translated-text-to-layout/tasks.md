## 1. Text Fit Planning (strict TDD)

- [x] 1.1 [RED] Write failing test: `translated_text` is wrapped into multiple lines whose estimated widths fit within bbox width
- [x] 1.2 [GREEN] Implement internal text fit result and wrapping logic for translated text
- [x] 1.3 [RED] Write failing test: blocks without `translated_text` still render original `text`
- [x] 1.4 [GREEN] Preserve existing original-text fallback path
- [x] 1.5 [RED] Write failing test: `translated_text` takes priority over `--sample-text zh`
- [x] 1.6 [GREEN] Ensure text selection priority is translated text, then sample text, then original text

## 2. Font Shrink And Overflow Diagnostics (strict TDD)

- [x] 2.1 [RED] Write failing test: bbox height shortage reduces actual font size below default
- [x] 2.2 [GREEN] Implement deterministic font-size shrink loop down to the minimum font size
- [x] 2.3 [RED] Write failing test: fitting text keeps default font size and marks `overflow=false`
- [x] 2.4 [GREEN] Return default-size fit result when text already fits
- [x] 2.5 [RED] Write failing test: tiny bbox never produces font size below minimum font size
- [x] 2.6 [GREEN] Clamp fit results to the renderer minimum font size
- [x] 2.7 [RED] Write failing test: unfit text at minimum font size marks `overflow=true` and keeps block id traceability
- [x] 2.8 [GREEN] Add overflow metadata to text draw commands and render plan

## 3. Narrow Block Strategy (strict TDD)

- [x] 3.1 [RED] Write failing test: over-narrow bbox does not render the full Chinese translation as one-character-per-line output
- [x] 3.2 [GREEN] Implement narrow block strategy that uses source text or safe truncated text
- [x] 3.3 [RED] Write failing test: narrow block strategy records a deterministic fit reason
- [x] 3.4 [GREEN] Add fit reason metadata to text draw commands

## 4. PDF Drawing Integration (strict TDD)

- [x] 4.1 [RED] Write failing test: `_draw_text_in_box` draws precomputed fit lines instead of recalculating naive wraps
- [x] 4.2 [GREEN] Update PDF drawing to use precomputed lines, actual font size, and line height
- [x] 4.3 [RED] Write failing test: existing image asset, image placeholder, table placeholder, and formula placeholder commands are unchanged
- [x] 4.4 [GREEN] Keep non-text render paths unchanged while integrating text fit
- [x] 4.5 [REFACTOR] Extract pure text-fit helpers and constants so renderer tests can target them without PDF generation

## 5. Debug And Documentation (visual verification)

- [x] 5.1 [UI] Add debug-box visual marker for overflow text blocks when `--debug-boxes` is enabled
- [x] 5.2 [VERIFY] Run full automated test suite with `uv run python -m pytest -q`
- [x] 5.3 [VERIFY] Generate `output/pdf/attention-is-all-you-need.zh.fit.pdf` from `output/layout/attention-is-all-you-need.zh.layout.json`
- [x] 5.4 [VERIFY] Render PNG previews for the first page and at least one正文 page; confirm body text no longer has large horizontal overflow and overflow areas are identifiable
- [x] 5.5 [REFACTOR] Update README usage notes if the render behavior or debug output changes in a user-visible way
