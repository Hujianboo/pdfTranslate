## Why

项目已经能把 PDF 解析为 `LayoutConfig` 并做调试重建，但还没有真正进入内容翻译阶段。现在需要先建立一个可测试、可替换 provider 的翻译层，让后续 PDF 回填可以消费稳定的中文译文，而不是继续依赖固定中文样本文本。

## What Changes

- 新增 layout 翻译能力：读取 `LayoutConfig`，默认把可翻译文本块翻译为中文，并输出带译文字段的增强版 layout JSON。
- 只翻译 `kind == "text"` 且 `translatable=true` 的文本块；图片、公式、表格及不可翻译文本块保持原样。
- 新增 provider 抽象层，支持通过统一接口适配不同模型供应商。
- 默认 provider 为 OpenAI-compatible，并且仅在翻译命令中读取 `.env` / 环境变量里的 `BASE_URL`、`KEY`、`MODEL`；同时兼容 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`OPENAI_MODEL`。
- 当前不复用 Codex Desktop 或 ChatGPT 登录态作为程序化 API 凭据。
- 新增 mock provider，用于没有 API key 时的本地 TDD、CLI 验证和离线开发。
- 新增 CLI 命令，用于从输入 layout JSON 生成中文翻译 layout JSON。
- 不在本阶段做译文排版压缩、PDF 最终回填、图片内容翻译、公式翻译或表格单元格翻译。

## Capabilities

### New Capabilities

- `pdf-layout-translation`: 定义 layout 级内容翻译能力、provider 行为、CLI 输入输出和无 key 开发路径。

### Modified Capabilities

- `pdf-layout-config`: 允许翻译阶段在增强版 layout JSON 中为文本块写入译文字段，同时保持解析阶段输出仍为 source-only。
- `pdf-layout-rendering`: 渲染器后续应能优先使用文本块译文字段，而不是只能使用原文或固定中文样本文本。

## Impact

- 新增 `pdftranslate.translation` 模块，包含 translator、provider 协议、OpenAI-compatible provider、mock provider、translation-only `.env` 读取和错误类型。
- 更新 `pdftranslate.cli`，增加 `translate-layout` 命令。
- 更新 `pdftranslate.layout` 或序列化逻辑，使文本块可携带可选译文字段且保持旧 JSON 兼容。
- 更新渲染逻辑，为后续使用真实译文重建 PDF 做准备。
- 可能新增 OpenAI SDK 或使用标准库 HTTP 客户端；实现时优先保持依赖轻量。
- 测试覆盖 provider 选择、无 key 行为、只翻译文本块、CLI 输出和渲染优先级。
