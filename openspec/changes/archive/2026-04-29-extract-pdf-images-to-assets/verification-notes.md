## Verification Notes

### Automated Tests

- `uv run python -m pytest -q`
- Result: `51 passed`
- Warnings are from third-party libraries: pypdfium2, PyMuPDF, and Docling deprecations.

### Sample PDF Image Extraction

- Command:

```bash
uv run pdftranslate extract-images assets/1603.08767v1.pdf --layout assets/1603.08767v1.layout.json --output-layout output/layout/1603.08767v1.with-images.layout.json --assets-dir output/assets/1603.08767v1/images
```

- Result: succeeded.
- Layout image blocks: 3.
- Blocks with `image.asset_path`: 2.
- Generated assets:
  - `output/assets/1603.08767v1/images/p2_i1.png`
  - `output/assets/1603.08767v1/images/p2_i2.png`

### Sample PDF Rebuild

- Command:

```bash
uv run pdftranslate render-layout output/layout/1603.08767v1.with-images.layout.json --output output/pdf/1603.08767v1.with-images.rebuilt.pdf --debug-boxes
```

- Result: succeeded.
- Visual check: rendered page 2 with PyMuPDF because `pdftoppm` is unavailable in the local environment.
- Page 2 `p2_i1` shows the real chart image instead of a gray placeholder.
- A small unmatched image block, `p2_i3`, remains a placeholder.

### Remaining Limitations

- Some PDF visual content can be vector graphics, tables, formulas, or composed drawing commands rather than extractable raster images.
- Docling image block bbox and PyMuPDF image rect can diverge, so some blocks may remain unmatched.
- Current renderer fills the image bbox and may stretch assets if the bbox aspect ratio differs from the image.
- Table and formula layout reconstruction is still out of scope for this change.
