## 1. Layout Image Model (strict TDD)

- [x] 1.1 [RED] Write failing test: `ImageInfo` accepts `asset_path` and serializes it under `image.asset_path`
- [x] 1.2 [GREEN] Implement optional `ImageInfo.asset_path` serialization
- [x] 1.3 [RED] Write failing test: `layout_config_from_dict` reads `image.asset_path` when present
- [x] 1.4 [GREEN] Implement optional `asset_path` deserialization in `layout_io`
- [x] 1.5 [RED] Write failing test: old image blocks without `asset_path` still round-trip successfully
- [x] 1.6 [GREEN] Preserve backward compatibility for image blocks without `asset_path`
- [x] 1.7 [REFACTOR] Keep image model tests focused on schema compatibility and avoid brittle full-JSON assertions

## 2. PDF Image Extraction and Matching (strict TDD)

- [x] 2.1 [RED] Write failing test: top-left PDF image rect converts to bottom-left `LayoutConfig` bbox
- [x] 2.2 [GREEN] Implement PDF rect to layout bbox conversion helper
- [x] 2.3 [RED] Write failing test: bbox overlap or center-distance matcher chooses the correct image block on the same page
- [x] 2.4 [GREEN] Implement page-scoped image asset to `ImageBlock` matching
- [x] 2.5 [RED] Write failing test: matched image asset filename uses the image block ID, such as `p1_i1.png`
- [x] 2.6 [GREEN] Implement stable asset filename generation from image block IDs
- [x] 2.7 [RED] Write failing test: `asset_path` written to layout is relative, not absolute
- [x] 2.8 [GREEN] Implement relative asset path calculation for layout writeback
- [x] 2.9 [RED] Write failing test: unmatched image blocks keep existing `ref`, `width`, `height`, and `mime_type`
- [x] 2.10 [GREEN] Preserve unmatched image blocks without forcing `asset_path`
- [x] 2.11 [RED] Write failing test: a small PDF with an embedded PNG writes at least one non-empty image file to assets dir
- [x] 2.12 [GREEN] Implement PyMuPDF-backed image extraction and add dependency wiring if missing
- [x] 2.13 [RED] Write failing test: extracted PNG writes back `mime_type="image/png"` to the matched image block
- [x] 2.14 [GREEN] Write extracted asset metadata back into the matched `ImageInfo`
- [x] 2.15 [REFACTOR] Split PyMuPDF IO, pure matching, and layout writeback into testable boundaries

## 3. CLI Integration (strict TDD)

- [x] 3.1 [RED] Write failing test: `main(["extract-images", ...])` creates enhanced layout JSON and assets directory
- [x] 3.2 [GREEN] Add `extract-images` parser branch and invoke the image asset extraction service
- [x] 3.3 [RED] Write failing test: missing input PDF or missing layout JSON returns non-zero and prints a useful error
- [x] 3.4 [GREEN] Implement CLI path validation for `extract-images`
- [x] 3.5 [RED] Write failing test: console script can run `pdftranslate extract-images ...`
- [x] 3.6 [GREEN] Ensure packaging exposes the new subcommand through the existing console entry point
- [x] 3.7 [REFACTOR] Keep heavy PDF imports lazy so unrelated CLI commands stay lightweight

## 4. Renderer Image Asset Use (strict TDD)

- [x] 4.1 [RED] Write failing test: `build_render_plan` emits a real image command when `image.asset_path` points to an existing file
- [x] 4.2 [GREEN] Add image asset command generation to `build_render_plan`
- [x] 4.3 [RED] Write failing test: missing `asset_path` still emits `image_placeholder`
- [x] 4.4 [GREEN] Preserve placeholder fallback when `asset_path` is absent
- [x] 4.5 [RED] Write failing test: nonexistent `asset_path` falls back to `image_placeholder`
- [x] 4.6 [GREEN] Validate image asset paths before creating real image commands
- [x] 4.7 [RED] Write failing test: `render_layout_pdf` writes a PDF containing an image resource for valid `asset_path`
- [x] 4.8 [GREEN] Draw real image assets with ReportLab inside the image block bbox
- [x] 4.9 [REFACTOR] Keep drawing command execution separate from render plan construction

## 5. Documentation and Verification (manual checks)

- [x] 5.1 [VERIFY] Update README usage examples for `extract-images` and the two-step `extract-images` -> `render-layout` workflow
- [x] 5.2 [VERIFY] Run the full pytest suite and confirm all tests pass
- [x] 5.3 [VERIFY] Run `pdftranslate extract-images assets/1603.08767v1.pdf --layout assets/1603.08767v1.layout.json --output-layout output/layout/1603.08767v1.with-images.layout.json --assets-dir output/assets/1603.08767v1/images`
- [x] 5.4 [VERIFY] Inspect the enhanced layout JSON and confirm matched image blocks contain relative `image.asset_path`
- [x] 5.5 [VERIFY] Run `pdftranslate render-layout output/layout/1603.08767v1.with-images.layout.json --output output/pdf/1603.08767v1.with-images.rebuilt.pdf --debug-boxes`
- [x] 5.6 [VERIFY] Render or open the rebuilt sample PDF and confirm page 2 image areas show real image content instead of gray placeholders where extraction succeeded
- [x] 5.7 [VERIFY] Record any remaining limitation for vector figures, formulas, tables, or unmatched image blocks before archiving
