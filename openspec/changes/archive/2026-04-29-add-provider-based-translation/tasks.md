## 1. TextBlock Translation Field (strict TDD)

- [x] 1.1 [RED] Write failing test: `TextBlock.to_dict()` includes `translated_text` when present
- [x] 1.2 [GREEN] Add optional `translated_text` field to `TextBlock` serialization
- [x] 1.3 [RED] Write failing test: source-only `TextBlock.to_dict()` omits `translated_text`
- [x] 1.4 [GREEN] Preserve old source-only text block serialization
- [x] 1.5 [RED] Write failing test: `layout_config_from_dict` reads and round-trips `translated_text`
- [x] 1.6 [GREEN] Add `translated_text` deserialization to `layout_io`
- [x] 1.7 [REFACTOR] Keep text block fixture helpers flexible for source-only and translated layouts

## 2. Provider Layer (strict TDD)

- [x] 2.1 [RED] Write failing test: provider factory defaults to provider name `openai`
- [x] 2.2 [GREEN] Implement `create_translation_provider` default selection
- [x] 2.3 [RED] Write failing test: provider factory creates deterministic `mock` provider
- [x] 2.4 [GREEN] Implement `MockTranslationProvider`
- [x] 2.5 [RED] Write failing test: unknown provider raises `UnsupportedTranslationProvider`
- [x] 2.6 [GREEN] Add provider error types and unknown provider handling
- [x] 2.7 [RED] Write failing test: OpenAI-compatible provider reads translation `.env` `BASE_URL`, `KEY`, and `MODEL`
- [x] 2.8 [GREEN] Implement translation-only `.env` and OpenAI-compatible provider config loading
- [x] 2.9 [RED] Write failing test: OpenAI-compatible provider reads standard `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `OPENAI_MODEL`
- [x] 2.10 [GREEN] Add OpenAI missing-key failure with actionable message
- [x] 2.11 [RED] Write failing test: OpenAI-compatible provider without `KEY` or `OPENAI_API_KEY` raises `MissingProviderCredentials`
- [x] 2.12 [GREEN] Restrict OpenAI-compatible provider credentials to explicit API key configuration
- [x] 2.13 [RED] Write failing test: Codex environment variables do not satisfy OpenAI-compatible credentials
- [x] 2.14 [GREEN] Keep Codex/ChatGPT login state out of provider credential loading
- [x] 2.15 [RED] Write failing test: non-translation CLI paths do not instantiate translation provider or require `.env`
- [x] 2.16 [GREEN] Ensure `.env` loading happens only inside translation provider creation
- [x] 2.17 [REFACTOR] Keep provider request/result/config dataclasses small and provider-neutral

## 3. Layout Translation Orchestration (strict TDD)

- [x] 3.1 [RED] Write failing test: translator defaults target language to `zh`
- [x] 3.2 [GREEN] Implement `translate_layout_config` default target language
- [x] 3.3 [RED] Write failing test: translator sends only eligible text blocks to provider
- [x] 3.4 [GREEN] Filter blocks by `TextBlock` and `translatable=True`
- [x] 3.5 [RED] Write failing test: provider receives block ids and original text for each eligible block
- [x] 3.6 [GREEN] Build batch `TranslationItem` requests from eligible text blocks
- [x] 3.7 [RED] Write failing test: translated layout keeps original `text` and writes `translated_text`
- [x] 3.8 [GREEN] Attach provider results back to copied text blocks
- [x] 3.9 [RED] Write failing test: image/table/formula/non-translatable text blocks remain without `translated_text`
- [x] 3.10 [GREEN] Preserve non-eligible blocks unchanged in translated layout
- [x] 3.11 [REFACTOR] Extract eligible block collection and result merge helpers

## 4. CLI Translation Command (strict TDD)

- [x] 4.1 [RED] Write failing test: `translate-layout --provider mock` writes translated JSON
- [x] 4.2 [GREEN] Add `translate-layout` CLI command and output writing
- [x] 4.3 [RED] Write failing test: CLI defaults target language to `zh`
- [x] 4.4 [GREEN] Add `--target-language` option defaulting to `zh`
- [x] 4.5 [RED] Write failing test: `translate-layout --provider openai` without key exits non-zero and mentions `KEY` or `OPENAI_API_KEY`
- [x] 4.6 [GREEN] Convert translation provider credential errors into CLI stderr and non-zero exit
- [x] 4.7 [REFACTOR] Keep CLI command handlers small by delegating to translation module

## 5. Renderer Translation Preference (strict TDD)

- [x] 5.1 [RED] Write failing test: `build_render_plan` uses `translated_text` before source text
- [x] 5.2 [GREEN] Update renderer text selection priority
- [x] 5.3 [RED] Write failing test: text without translation and without sample text still uses original `text`
- [x] 5.4 [GREEN] Preserve existing original text fallback
- [x] 5.5 [RED] Write failing test: sample text mode still applies to text blocks without translation
- [x] 5.6 [GREEN] Preserve `RenderOptions(sample_text="zh")` behavior for untranslated blocks
- [x] 5.7 [RED] Write failing test: sample text mode preserves text command count and block ids
- [x] 5.8 [GREEN] Keep render plan command count and ids stable
- [x] 5.9 [REFACTOR] Make `_text_for_block` selection order explicit and easy to extend

## 6. Documentation and Manual Verification

- [x] 6.1 [RED] Write failing test: README mentions `translate-layout`, provider selection, `.env` `BASE_URL`/`KEY`/`MODEL`, `OPENAI_API_KEY`, and `--provider mock`
- [x] 6.2 [GREEN] Update README translation usage and credential limitations
- [x] 6.3 [VERIFY] Run `uv run python -m pytest -q` and confirm all tests pass
- [x] 6.4 [VERIFY] Run `pdftranslate parse-layout` on a sample PDF
- [x] 6.5 [VERIFY] Run `pdftranslate translate-layout <layout.json> --output <translated.layout.json> --provider mock`
- [x] 6.6 [VERIFY] Inspect translated layout JSON and confirm text blocks include `translated_text`, while image/table/formula blocks do not
- [x] 6.7 [VERIFY] Run `pdftranslate render-layout <translated.layout.json> --output output/pdf/translated.debug.pdf --debug-boxes`
- [x] 6.8 [VERIFY] Render or open the debug PDF and confirm Chinese/mock translated text appears in text boxes
- [x] 6.9 [VERIFY] Record limitations: no real OpenAI-compatible call without API key, no Codex login reuse, `.env` only affects translation, no image/formula/table translation, no layout fitting
- [x] 6.10 [VERIFY] Run `openspec status --change "add-provider-based-translation"` and confirm all artifacts are complete
