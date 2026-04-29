# Verification Notes

## Commands

- `uv run python -m pytest -q`
- `uv run pdftranslate parse-layout assets/1603.08767v1.pdf --output output/layout/translation-sample.layout.json`
- `uv run pdftranslate translate-layout output/layout/translation-sample.layout.json --output output/layout/translation-sample.translated.layout.json --provider mock`
- `uv run pdftranslate render-layout output/layout/translation-sample.translated.layout.json --output output/pdf/translation-sample.translated.debug.pdf --debug-boxes`

## Results

- Full test suite: `96 passed`
- Parsed sample layout: `output/layout/translation-sample.layout.json`
- Mock translated layout: `output/layout/translation-sample.translated.layout.json`
- Debug PDF: `output/pdf/translation-sample.translated.debug.pdf`
- Preview PNG: `output/preview/translation-sample.translated.debug.page-1.png`
- Sample counts: `text=214`, `image=3`, `table=1`
- Text blocks with `translated_text`: `214`
- Non-text blocks with `translated_text`: `0`

## Limitations

- Real OpenAI-compatible calls require `KEY` in `.env` or `OPENAI_API_KEY`; without one, use `--provider mock`.
- Codex Desktop or ChatGPT login state is not reused as API credentials.
- `.env` variables `BASE_URL`, `KEY`, and `MODEL` are translation-provider configuration only.
- Image, formula, and table blocks are not translated in this change.
- Text fitting, overflow handling, font selection, and final PDF layout quality remain separate follow-up work.
