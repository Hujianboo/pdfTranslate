# pdf-layout-translation Specification

## Purpose
TBD - created by archiving change add-provider-based-translation. Update Purpose after archive.
## Requirements
### Requirement: 翻译 LayoutConfig 文本块
系统 SHALL 提供 layout 级翻译能力，读取 `LayoutConfig`，默认将可翻译文本块翻译为中文，并输出可序列化的增强版 layout。

#### Scenario: 默认目标语言为中文
- **GIVEN** 一个包含英文 text block 的 `LayoutConfig`
- **WHEN** 系统翻译该 layout 且用户未指定目标语言
- **THEN** 该 text block 输出 `translated_text` 字段，并且 provider 收到的目标语言为 `zh`

#### Scenario: 只翻译可翻译文本块
- **GIVEN** 一个 `LayoutConfig` 包含 `text`、`image`、`table` 和 `formula` block
- **WHEN** 系统翻译该 layout
- **THEN** 只有 `kind == "text"` 且 `translatable=true` 的 block 会调用 provider，并写入 `translated_text`

#### Scenario: 保留不可翻译 block 原样
- **GIVEN** 一个 `LayoutConfig` 包含 image block、table block、formula block 和 `translatable=false` 的 text block
- **WHEN** 系统翻译该 layout
- **THEN** 这些 block 的序列化结果不包含 `translated_text` 字段

#### Scenario: 保留原始文本
- **GIVEN** 一个 text block 的 `text` 为 `Attention is all you need`
- **WHEN** 系统翻译该 block
- **THEN** 输出 block 同时保留原始 `text` 字段，并把译文写入 `translated_text`

### Requirement: 通过 provider 适配翻译模型
系统 SHALL 定义 provider 抽象，使翻译逻辑可通过 provider 名称切换不同模型供应商，并默认使用 OpenAI-compatible provider。

#### Scenario: 默认 provider 为 openai
- **WHEN** 用户未指定 provider 创建翻译器
- **THEN** 系统选择 provider 名称 `openai`

#### Scenario: 可选择 mock provider
- **GIVEN** 用户指定 provider 名称为 `mock`
- **WHEN** 系统创建翻译器
- **THEN** 系统使用 mock provider，并返回确定性的中文样例译文

#### Scenario: 未知 provider 报错
- **GIVEN** 用户指定 provider 名称为 `unknown`
- **WHEN** 系统创建翻译器
- **THEN** 系统返回明确的 provider 不支持错误

#### Scenario: provider 接口按块批量翻译
- **GIVEN** 一个 layout 中有 3 个可翻译 text block
- **WHEN** 系统翻译该 layout
- **THEN** provider 收到 3 个带 block id 和原文的翻译输入项

### Requirement: OpenAI-compatible provider 凭据处理
系统 SHALL 通过翻译专用 `.env` 或环境变量配置调用 OpenAI-compatible API，并在没有凭据时失败为可理解错误；系统 MUST NOT 依赖 Codex Desktop、ChatGPT 或浏览器登录态作为程序化 API 凭据。

#### Scenario: OpenAI-compatible provider 读取 translation .env
- **GIVEN** 项目根目录 `.env` 包含 `BASE_URL`、`KEY` 和 `MODEL`
- **WHEN** 系统创建 OpenAI-compatible provider
- **THEN** provider 使用这些值作为翻译 API 的 base URL、API key 和模型名

#### Scenario: OpenAI-compatible provider 兼容标准 OpenAI 环境变量
- **GIVEN** 环境变量 `OPENAI_API_KEY` 存在
- **WHEN** 系统创建 OpenAI-compatible provider
- **THEN** provider 使用该 API key 准备请求

#### Scenario: 翻译配置不影响非翻译命令
- **GIVEN** 项目根目录 `.env` 包含 `BASE_URL`、`KEY` 和 `MODEL`
- **WHEN** 用户运行 `parse-layout`、`extract-images` 或 `render-layout`
- **THEN** 这些命令不读取或要求翻译 provider 配置

#### Scenario: OpenAI-compatible provider 无 key 失败
- **GIVEN** `.env` 不包含 `KEY` 且环境变量 `OPENAI_API_KEY` 不存在
- **WHEN** 用户选择 `openai` provider 执行翻译
- **THEN** 系统返回错误，说明需要设置 `KEY` 或 `OPENAI_API_KEY`，或改用 `--provider mock`

#### Scenario: 不使用 Codex 登录态
- **GIVEN** 用户当前在 Codex Desktop 中登录 OpenAI 账号
- **WHEN** 用户选择 `openai` provider 且没有 `KEY` 或 `OPENAI_API_KEY`
- **THEN** 系统仍然返回缺少 API key 错误，而不会尝试读取 Codex 登录态

### Requirement: 提供翻译 CLI
系统 SHALL 提供 `translate-layout` CLI 命令，从输入 layout JSON 生成带译文的输出 layout JSON。

#### Scenario: CLI 使用 mock provider 翻译 layout
- **GIVEN** 一个 layout JSON 文件包含一个可翻译 text block
- **WHEN** 用户运行 `pdftranslate translate-layout <input.layout.json> --output <output.layout.json> --provider mock`
- **THEN** 命令成功退出，并创建包含 `translated_text` 的输出 JSON

#### Scenario: CLI 默认目标语言为中文
- **GIVEN** 用户运行 `pdftranslate translate-layout <input.layout.json> --output <output.layout.json> --provider mock`
- **WHEN** 命令执行翻译
- **THEN** 输出 JSON 的 metadata 或 provider 调用记录表明目标语言为 `zh`

#### Scenario: CLI OpenAI-compatible 无 key 失败
- **GIVEN** `.env` 不包含 `KEY` 且环境变量 `OPENAI_API_KEY` 不存在
- **WHEN** 用户运行 `pdftranslate translate-layout <input.layout.json> --output <output.layout.json> --provider openai`
- **THEN** 命令非零退出，并在 stderr 中提示需要 `KEY` 或 `OPENAI_API_KEY`

