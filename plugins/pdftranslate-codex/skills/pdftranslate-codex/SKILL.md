---
name: pdftranslate-codex
description: Translate pdfTranslate LayoutConfig files or PDFs using Codex itself instead of the project .env/OpenAI-compatible provider. Use when the user asks to translate a PDF/layout through Codex, the Codex plugin, or without model credentials.
---

# pdfTranslate Codex Workflow

Always run the workflow from the installed pdfTranslate repository root, not from
the cached plugin directory under `~/.codex/plugins/cache`.

Repository root resolution order:

1. If the current working directory contains `pyproject.toml` and
   `plugins/pdftranslate-codex`, use it.
2. Otherwise, use the configured Codex marketplace source:
   `[marketplaces.pdftranslate-local].source` in `~/.codex/config.toml`.
3. If that is unavailable, fall back to `~/pdfTranslate`.

Do not scan the whole filesystem for the repository. Once the root is resolved,
run commands with that directory as the working directory and call the scripts
through `plugins/pdftranslate-codex/scripts/...`.

## Goal

Translate pdfTranslate `LayoutConfig` JSON with Codex as the translation engine. Do not use `.env`, `--provider openai`, or external model credentials.

## One-Command PDF Translation

For a PDF input, prefer the wrapper script:

```bash
cd <pdfTranslate-repo-root>
uv run python plugins/pdftranslate-codex/scripts/translate_pdf_with_codex.py <input-pdf> \
  --output-dir output/pdf \
  --target-language zh
```

User-customizable options:

- `--output <pdf>` writes an exact PDF path.
- `--output-dir <dir>` writes `<pdf-stem>.zh.pdf` into a directory.
- `--output-layout <json>` keeps the translated `LayoutConfig` at a chosen path.
- `--work-dir <dir>` chooses where temporary layout/assets/batches/logs are stored.
- `--keep-work-dir` keeps temporary files for debugging. Without it, temporary files are deleted after the PDF is built.
- `--no-images`, `--debug-boxes`, `--batch-size`, `--batch-chars`, and `--codex-model` customize the pipeline.

## Layout Translation

Use the manual layout workflow only when the user wants to inspect or edit intermediate batch files.

1. Prepare Codex translation batches:

```bash
cd <pdfTranslate-repo-root>
uv run python plugins/pdftranslate-codex/scripts/codex_layout_translation.py prepare <layout-json> \
  --output-dir tmp/codex-translation/<layout-stem> \
  --target-language zh
```

2. Open the generated `manifest.json`. For each batch, read the `prompt` or `request` file and write the matching `response` file.

Each response file must be JSON only:

```json
{"translations":[{"id":"p1_b1","text":"译文"}]}
```

Preserve every block id exactly. It is acceptable for a response to omit a block when Codex cannot confidently translate it; the renderer can fall back to the source text for missing `translated_text`.

3. Merge responses back into a translated layout:

```bash
cd <pdfTranslate-repo-root>
uv run python plugins/pdftranslate-codex/scripts/codex_layout_translation.py apply tmp/codex-translation/<layout-stem>/manifest.json \
  --output tmp/layout/<layout-stem>.layout.zh.json
```

4. Build the translated PDF:

```bash
cd <pdfTranslate-repo-root>
uv run pdftranslate build-pdf tmp/layout/<layout-stem>.layout.zh.json \
  --output-dir tmp/pdf \
  --allow-missing-translations
```

## PDF Translation

If the user provides a PDF, first parse it:

```bash
cd <pdfTranslate-repo-root>
uv run pdftranslate parse-layout <pdf-or-directory> \
  --output tmp/layout \
  --assets-dir tmp/assets
```

Then run the layout workflow above for each generated `*.layout.json`.

## Notes

- This is a Codex-side workflow. A normal Python CLI process cannot call the current Codex conversation directly.
- The project-level adapter remains `CodexTranslationProvider(complete=...)`; this plugin supplies the practical Codex workflow around the same JSON contract.
- The one-command wrapper calls `codex exec`, so users must have the Codex CLI installed and logged in.
- Delete temporary files by default; keep them only when debugging or when the user asks.
