## 1. Translated PDF Rendering (strict TDD)

- [x] 1.1 [RED] Write failing CLI test: `render-layout` creates a non-empty PDF from a layout JSON containing `translated_text`
- [x] 1.2 [GREEN] Ensure existing render path supports translated layout JSON end-to-end
- [x] 1.3 [RED] Write failing renderer test: translated PDF page count and MediaBox sizes match LayoutConfig
- [x] 1.4 [GREEN] Preserve page count and page size behavior for translated layouts
- [x] 1.5 [RED] Write failing renderer test: output PDF and render plan prefer `translated_text` over `text`
- [x] 1.6 [GREEN] Preserve translated-text priority in final PDF rendering
- [x] 1.7 [RED] Write failing renderer test: translated PDF uses image asset XObject when `image.asset_path` exists
- [x] 1.8 [GREEN] Preserve image asset rendering for translated layouts
- [x] 1.9 [RED] Write failing renderer test: translated PDF keeps table and formula placeholder IDs
- [x] 1.10 [GREEN] Preserve table/formula placeholder rendering for translated layouts

## 2. Translation Coverage Validation (strict TDD)

- [x] 2.1 [RED] Write failing unit test: helper returns missing block IDs for translatable text blocks without non-empty `translated_text`
- [x] 2.2 [GREEN] Implement pure missing-translation helper
- [x] 2.3 [RED] Write failing CLI test: `--require-translations` succeeds when every translatable text block has `translated_text`
- [x] 2.4 [GREEN] Add `--require-translations` CLI argument and success path
- [x] 2.5 [RED] Write failing CLI test: `--require-translations` fails before PDF creation and reports missing block ID
- [x] 2.6 [GREEN] Add strict validation failure handling before `render_layout_pdf`
- [x] 2.7 [RED] Write failing CLI test: default non-strict mode still renders partially translated layout
- [x] 2.8 [GREEN] Keep default render mode permissive

## 3. Documentation And End-To-End Verification (visual verification)

- [x] 3.1 [REFACTOR] Update README with the recommended translated-layout-to-PDF command and `--require-translations`
- [x] 3.2 [VERIFY] Run full automated test suite with `uv run python -m pytest -q`
- [x] 3.3 [VERIFY] Generate `output/pdf/attention-is-all-you-need.zh.final.pdf` from `output/layout/attention-is-all-you-need.zh.layout.json` using `--require-translations`
- [x] 3.4 [VERIFY] Generate debug PDF with `--debug-boxes`, render PNG previews for page 1 and a正文 page, and confirm translated text, debug boxes, and overflow markers are visible
