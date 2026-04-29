## 1. Translation Models and Serializer (auto-test)

### From Spec: text block 可以包含 translated_text
- **Test:** `TextBlock.to_dict()` includes `translated_text` only when a translation is present.
  - **Setup:** Construct a `TextBlock` with `translated_text="译文"`.
  - **Action:** Call `to_dict()`.
  - **Assert:** Output contains `"translated_text": "译文"` and still contains original `text`.

### From Spec: 没有译文的 text block 不输出 translated_text
- **Test:** Existing source-only text block serialization remains unchanged.
  - **Setup:** Construct a `TextBlock` without a translation.
  - **Action:** Call `to_dict()`.
  - **Assert:** Output does not contain `translated_text`.

### From Spec: 反序列化保留 translated_text
- **Test:** `layout_config_from_dict` preserves translated text.
  - **Setup:** Build layout dict with a text block containing `translated_text`.
  - **Action:** Read via `layout_config_from_dict`.
  - **Assert:** Resulting `TextBlock.translated_text == "译文"` and round-trip JSON keeps the field.

### From Spec: parse-layout 不输出译文或重建结果
- **Test:** Source-only parse output remains free of translation and rebuild fields.
  - **Setup:** Existing parse layout fixture.
  - **Action:** Serialize source-only `LayoutConfig`.
  - **Assert:** JSON does not contain `translated_text`, `target_text`, `rebuilt_pdf`, `edited_image`, or OCR fields.

## 2. Translation Provider Layer (auto-test)

### From Spec: 默认 provider 为 openai
- **Test:** Provider factory chooses OpenAI by default.
  - **Setup:** No provider name passed.
  - **Action:** Call provider factory.
  - **Assert:** Returned provider name is `openai`.

### From Spec: 可选择 mock provider
- **Test:** Provider factory can create deterministic mock provider.
  - **Setup:** Provider name `mock`.
  - **Action:** Translate one item.
  - **Assert:** Translation result is deterministic Chinese text and includes the input block id.

### From Spec: 未知 provider 报错
- **Test:** Provider factory rejects unsupported providers.
  - **Setup:** Provider name `unknown`.
  - **Action:** Call provider factory.
  - **Assert:** Raises `UnsupportedTranslationProvider`.

### From Spec: provider 接口按块批量翻译
- **Test:** Layout translator sends all eligible text blocks to provider as batch items.
  - **Setup:** Layout contains three translatable text blocks and a fake recording provider.
  - **Action:** Translate layout.
  - **Assert:** Provider receives exactly three items with block ids and original text.

### From Spec: OpenAI-compatible provider 读取 translation .env
- **Test:** OpenAI-compatible provider reads translation-only `.env` keys.
  - **Setup:** Create a temporary project `.env` with `BASE_URL`, `KEY`, and `MODEL`.
  - **Action:** Create OpenAI-compatible provider with that env path.
  - **Assert:** Provider config contains the expected base URL, key, and model without printing secret values.

### From Spec: OpenAI-compatible provider 兼容标准 OpenAI 环境变量
- **Test:** OpenAI-compatible provider reads `OPENAI_API_KEY`.
  - **Setup:** Monkeypatch `OPENAI_API_KEY="test-key"`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`.
  - **Action:** Create OpenAI provider.
  - **Assert:** Provider stores or prepares requests with those values without raising.

### From Spec: 翻译配置不影响非翻译命令
- **Test:** Non-translation CLI paths do not instantiate translation providers.
  - **Setup:** Monkeypatch translation provider factory to raise if called.
  - **Action:** Run existing `render-layout` CLI path on a fixture layout.
  - **Assert:** Command succeeds and provider factory is not called.

### From Spec: OpenAI-compatible provider 无 key 失败
- **Test:** OpenAI provider reports missing credentials.
  - **Setup:** Monkeypatch environment without `KEY` or `OPENAI_API_KEY` and use an empty/no `.env`.
  - **Action:** Create or use OpenAI provider.
  - **Assert:** Raises `MissingProviderCredentials` with message mentioning `KEY` or `OPENAI_API_KEY`.

### From Spec: 不使用 Codex 登录态
- **Test:** OpenAI provider does not use Codex environment as credentials.
  - **Setup:** Monkeypatch `CODEX_*` variables but no `KEY` or `OPENAI_API_KEY`.
  - **Action:** Create or use OpenAI provider.
  - **Assert:** Raises missing key error.

## 3. Layout Translation Orchestration (auto-test)

### From Spec: 默认目标语言为中文
- **Test:** Layout translator defaults target language to `zh`.
  - **Setup:** Layout with one translatable text block and recording provider.
  - **Action:** Translate layout without target language argument.
  - **Assert:** Provider call has `target_language == "zh"` and output includes `translated_text`.

### From Spec: 只翻译可翻译文本块
- **Test:** Translator filters eligible blocks correctly.
  - **Setup:** Layout with text/image/table/formula blocks and one `translatable=false` text block.
  - **Action:** Translate layout with recording provider.
  - **Assert:** Provider sees only `kind == "text"` and `translatable=true` blocks.

### From Spec: 保留不可翻译 block 原样
- **Test:** Non-text and non-translatable blocks do not get translated fields.
  - **Setup:** Layout with image, table, formula, and non-translatable text block.
  - **Action:** Translate layout.
  - **Assert:** Serialized output for those blocks does not contain `translated_text`.

### From Spec: 保留原始文本
- **Test:** Translation does not overwrite source text.
  - **Setup:** Text block `text="Attention is all you need"`.
  - **Action:** Translate layout with mock provider.
  - **Assert:** Output keeps `text="Attention is all you need"` and adds `translated_text`.

## 4. CLI Translation Command (auto-test)

### From Spec: CLI 使用 mock provider 翻译 layout
- **Test:** `translate-layout` writes translated layout JSON with mock provider.
  - **Setup:** Temporary input layout JSON with one translatable text block.
  - **Action:** Run CLI `translate-layout <input> --output <output> --provider mock`.
  - **Assert:** Exit code is `0`, output exists, and text block includes `translated_text`.

### From Spec: CLI 默认目标语言为中文
- **Test:** CLI defaults to Chinese target language.
  - **Setup:** Temporary input layout JSON and mock provider.
  - **Action:** Run CLI without `--target-language`.
  - **Assert:** Output metadata or deterministic mock translation indicates target `zh`.

### From Spec: CLI OpenAI-compatible 无 key 失败
- **Test:** CLI fails clearly when OpenAI key is missing.
  - **Setup:** Temporary input layout JSON, no `.env`, and environment without `KEY` or `OPENAI_API_KEY`.
  - **Action:** Run CLI with `--provider openai`.
  - **Assert:** Exit code is non-zero and stderr mentions `KEY` or `OPENAI_API_KEY`.

## 5. Rendering Translated Text (auto-test)

### From Spec: 渲染器优先使用真实译文
- **Test:** `build_render_plan` uses `translated_text` before source text.
  - **Setup:** Layout with text block containing `text="Original"` and `translated_text="译文"`.
  - **Action:** Build render plan.
  - **Assert:** Text draw command content is `译文`.

### From Spec: 无译文且无样本文本时使用原文
- **Test:** Existing render fallback remains source text.
  - **Setup:** Layout with text block without translation.
  - **Action:** Build render plan without sample text.
  - **Assert:** Text draw command content is original `text`.

### From Spec: 中文样本文本模式替换无译文文本块内容
- **Test:** Sample text still applies only when no real translation exists.
  - **Setup:** Layout with text block without translation.
  - **Action:** Build render plan with `RenderOptions(sample_text="zh")`.
  - **Assert:** Text draw command content is deterministic Chinese sample text, not source text.

### From Spec: 中文样本文本模式保留文本块数量和 ID
- **Test:** Sample text mode preserves text command count and block ids.
  - **Setup:** Layout with multiple text blocks.
  - **Action:** Build render plan with sample text.
  - **Assert:** Count and block ids match input text blocks.

## 6. Integration Verification (manual)

### From Spec: CLI 使用 mock provider 翻译 layout
- **Check:** End-to-end command chain can translate a real parsed layout offline.
  - **Steps:** Run `parse-layout` on a sample PDF, then `translate-layout --provider mock`, then inspect the output JSON.
  - **Acceptance:** Output JSON opens, contains `translated_text` on text blocks, and leaves image/table/formula blocks unchanged.

### From Spec: 渲染器优先使用真实译文
- **Check:** Debug PDF visually uses translated text in text regions.
  - **Steps:** Render translated layout with `render-layout --debug-boxes`, then render first page to PNG.
  - **Acceptance:** Text boxes contain Chinese translated/mock text and bbox positions remain inspectable.
