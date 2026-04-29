## 1. Table and Formula Layout Models (strict TDD)

- [x] 1.1 [RED] Write failing test: `TableBlock.to_dict()` serializes `id`, `kind`, `page_number`, `bbox`, and `table`
- [x] 1.2 [GREEN] Implement `TableBlock`, `TableInfo`, and `TableCellInfo` serialization
- [x] 1.3 [RED] Write failing test: `TableInfo` preserves `num_rows`, `num_cols`, and `cells`
- [x] 1.4 [GREEN] Add table row/column counts and cell list fields
- [x] 1.5 [RED] Write failing test: table cell serialization preserves text, row/col ranges, spans, header flags, and optional bbox
- [x] 1.6 [GREEN] Implement full `TableCellInfo` serialization with optional bbox
- [x] 1.7 [RED] Write failing test: `FormulaBlock.to_dict()` serializes `formula` and defaults `translatable=False`
- [x] 1.8 [GREEN] Implement `FormulaBlock` and `FormulaInfo`
- [x] 1.9 [RED] Write failing test: formula info can serialize either non-empty `text` or non-empty `ref`
- [x] 1.10 [GREEN] Preserve optional formula text/ref/formula_type fields
- [x] 1.11 [REFACTOR] Keep block model serialization helpers consistent across text, image, table, and formula

## 2. Layout IO Compatibility (strict TDD)

- [x] 2.1 [RED] Write failing test: `layout_config_from_dict` reads a table block into `TableBlock`
- [x] 2.2 [GREEN] Add table block deserialization to `layout_io`
- [x] 2.3 [RED] Write failing test: `layout_config_from_dict` reads a formula block into `FormulaBlock`
- [x] 2.4 [GREEN] Add formula block deserialization to `layout_io`
- [x] 2.5 [RED] Write failing test: top-level metadata survives round-trip with text/image/table/formula blocks
- [x] 2.6 [GREEN] Preserve existing top-level metadata and old text/image fixture compatibility
- [x] 2.7 [REFACTOR] Extract shared bbox/table/formula parsing helpers in `layout_io`

## 3. Docling Table and Formula Mapping (strict TDD)

- [x] 3.1 [RED] Write failing test: fake Docling table item maps to `TableBlock` with provenance bbox
- [x] 3.2 [GREEN] Extract `document.tables` into table blocks in `docling_adapter`
- [x] 3.3 [RED] Write failing test: table block IDs are stable and use `p<page>_t<table>`
- [x] 3.4 [GREEN] Sort table items by page and bbox before assigning table IDs
- [x] 3.5 [RED] Write failing test: Docling table cell fields map to LayoutConfig table cells
- [x] 3.6 [GREEN] Map Docling `TableData.table_cells` into `TableCellInfo`
- [x] 3.7 [RED] Write failing test: Docling column/row header flags are preserved
- [x] 3.8 [GREEN] Preserve table cell `column_header` and `row_header`
- [x] 3.9 [RED] Write failing test: fake Docling formula item maps to `FormulaBlock` with `translatable=False`
- [x] 3.10 [GREEN] Extract formula items from Docling text/formula-like items
- [x] 3.11 [RED] Write failing test: formula block IDs are stable and use `p<page>_f<formula>`
- [x] 3.12 [GREEN] Sort formula items by page and bbox before assigning formula IDs
- [x] 3.13 [RED] Write failing test: formula items are not also emitted as normal `TextBlock`
- [x] 3.14 [GREEN] Skip formula items in the text block extraction loop
- [x] 3.15 [RED] Write failing test: formula text/orig/self_ref fallback writes non-empty `formula.text` or `formula.ref`
- [x] 3.16 [GREEN] Implement formula text/ref fallback helper
- [x] 3.17 [REFACTOR] Split Docling item collection, bbox conversion, table cell mapping, and formula detection into small helpers

## 4. CLI and Schema Contract (strict TDD)

- [x] 4.1 [RED] Write failing test: `parse-layout` CLI can output JSON containing table and formula blocks from a monkeypatched parser
- [x] 4.2 [GREEN] Ensure CLI output path writes table/formula LayoutConfig JSON without special casing
- [x] 4.3 [RED] Write failing test: schema/documentation contract mentions table and formula block fields
- [x] 4.4 [GREEN] Update schema documentation or README contract text for table/formula fields
- [x] 4.5 [RED] Write failing test: LayoutConfig JSON with table/formula does not include translation or OCR result fields
- [x] 4.6 [GREEN] Keep parse/config output limited to source structure only
- [x] 4.7 [REFACTOR] Update fixtures so tests can compose text/image/table/formula layouts without brittle full JSON duplication

## 5. Renderer Placeholder Support (strict TDD)

- [x] 5.1 [RED] Write failing test: `build_render_plan` maps table bbox to `table_placeholder`
- [x] 5.2 [GREEN] Add table placeholder command generation
- [x] 5.3 [RED] Write failing test: `build_render_plan` maps formula bbox to `formula_placeholder`
- [x] 5.4 [GREEN] Add formula placeholder command generation
- [x] 5.5 [RED] Write failing test: `debug_boxes=True` includes text, image, table, and formula block IDs
- [x] 5.6 [GREEN] Include table/formula blocks in debug box generation
- [x] 5.7 [RED] Write failing test: `render_layout_pdf` writes table placeholder ID text into output PDF
- [x] 5.8 [GREEN] Draw table placeholder boxes and labels in ReportLab execution
- [x] 5.9 [RED] Write failing test: `render_layout_pdf` writes formula placeholder ID text into output PDF
- [x] 5.10 [GREEN] Draw formula placeholder boxes and labels in ReportLab execution
- [x] 5.11 [REFACTOR] Share placeholder drawing code across image, table, and formula where practical

## 6. Verification and Documentation (manual checks)

- [x] 6.1 [VERIFY] Run `uv run python -m pytest -q` and confirm all tests pass
- [x] 6.2 [VERIFY] Prepare or generate a PDF sample containing a simple table and formula for visual inspection
- [x] 6.3 [VERIFY] Run `pdftranslate parse-layout <table-formula-sample.pdf> --output output/layout/table-formula.layout.json`
- [x] 6.4 [VERIFY] Inspect the layout JSON and confirm it contains at least one `table` block and one `formula` block when Docling detects them
- [x] 6.5 [VERIFY] Run `pdftranslate render-layout output/layout/table-formula.layout.json --output output/pdf/table-formula.rebuilt.debug.pdf --debug-boxes`
- [x] 6.6 [VERIFY] Render or open the debug PDF and confirm table/formula placeholders roughly cover the original regions
- [x] 6.7 [VERIFY] Record remaining limitations for formulas not detected by Docling, missing cell bbox, table border fidelity, and non-goal OCR behavior
- [x] 6.8 [VERIFY] Run `openspec status --change "extract-tables-formulas-to-layout-config"` and confirm all artifacts are complete
