# Verification Notes

## Commands

- `uv run python -m pytest -q`
- `uv run pdftranslate parse-layout output/samples/table-formula-sample.pdf --output output/layout/table-formula.layout.json`
- `uv run pdftranslate render-layout output/layout/table-formula.layout.json --output output/pdf/table-formula.rebuilt.debug.pdf --debug-boxes`

## Sample Results

- Generated sample: `output/samples/table-formula-sample.pdf`
- Parsed layout: `output/layout/table-formula.layout.json`
- Debug rebuild: `output/pdf/table-formula.rebuilt.debug.pdf`
- Debug preview: `output/preview/table-formula.rebuilt.debug.png`
- Parsed block counts: `text=5`, `table=1`, `formula=0`
- Docling detected the drawn table and exposed `num_rows=4`, `num_cols=3`, and table cells.
- Docling did not detect the simple formula strings as `FormulaItem`; they remained normal text blocks in this sample.

## Remaining Limitations

- Formula extraction depends on Docling emitting formula-like items. Simple PDF text such as `E = mc^2` can remain a normal text block.
- Some Docling table cells may not include a cell bbox, so `TableCellInfo.bbox` remains optional.
- Rebuild output currently draws table/formula placeholders only. It does not restore table borders, row lines, formulas fonts, or mathematical layout fidelity.
- OCR remains intentionally disabled; scanned PDFs are still out of scope.
