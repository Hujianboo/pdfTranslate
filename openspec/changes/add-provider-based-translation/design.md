## Context

当前项目已经具备 `parse-layout`、`extract-images` 和 `render-layout`。`LayoutConfig` 中已有 text/image/table/formula block，其中公式和表格已被保护为非普通文本处理对象。现在需要进入内容翻译阶段。用户已在项目根目录新增 `.env`，其中包含 `BASE_URL`、`KEY` 和 `MODEL`，用于兼容 OpenAI API 的翻译服务；这些配置只用于翻译 provider，不应影响其它命令。

OpenAI 官方 API 文档要求使用 API key 做认证，并通过 `Authorization: Bearer <API_KEY>` 或 SDK 环境变量配置调用。因此默认 OpenAI-compatible provider 必须读取显式凭据；无 key 时应清晰失败。不能把 Codex Desktop 或 ChatGPT 登录态当成程序化 API 凭据。为了没有真实 key 时也能推进 TDD 和端到端链路，设计保留 `mock` provider。

## Goals / Non-Goals

**Goals:**

- 提供 `translate-layout` 命令，读取 layout JSON 并输出带中文译文的增强版 layout JSON。
- 默认目标语言为中文，内部使用 `zh` 作为目标语言代码。
- 只翻译 `TextBlock` 且 `translatable=true` 的文本块。
- 保留原始 `text`，把译文写入可选 `translated_text`。
- 建立 provider 抽象，默认 OpenAI-compatible provider，支持 mock provider 和后续更多模型 provider。
- OpenAI-compatible provider 从翻译专用 `.env` / 环境变量读取 `BASE_URL`、`KEY`、`MODEL`，并兼容 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`OPENAI_MODEL`。
- 无 `KEY` / `OPENAI_API_KEY` 时 OpenAI-compatible provider 给出明确错误，并提示可改用 `--provider mock`。
- 渲染器优先使用 `translated_text`，否则才使用中文样本文本或原文。

**Non-Goals:**

- 不翻译图片、公式和表格。
- 不做译文长度压缩、字体缩放、复杂换行优化或最终 PDF 排版质量提升。
- 不在本阶段接入真实 Codex/ChatGPT 登录态复用。
- 不把 API key 写入配置文件或 layout JSON。
- 不引入缓存、重试、并发限流、成本估算或术语表。

## Decisions

### 1. 在 `TextBlock` 上增加可选 `translated_text`

译文属于 text block 的派生内容，和原始 bbox/style 绑定最紧。把译文放在 `TextBlock` 上可以让 `layout_io`、CLI 和 renderer 都沿用现有结构，不需要新增独立 sidecar 文件。

备选方案是生成单独 translations map，例如 `{block_id: translated_text}`。它更干净，但渲染和人工检查时需要同时传两个文件；当前阶段更需要降低链路复杂度。

### 2. 解析阶段保持 source-only，翻译阶段输出增强版 layout

`parse-layout` 仍然只表达 PDF 源结构，不写 `translated_text`。`translate-layout` 负责生成增强版 layout。这样保留了现有 spec 中解析阶段不翻译的边界，也让调试时可以比较 source layout 和 translated layout。

### 3. Provider 抽象使用小而稳定的批量接口

新增 `TranslationProvider` 协议，核心方法接收 `TranslationRequest`，其中包含 `target_language` 和多个 `TranslationItem(block_id, text)`，返回 `TranslationResult` 列表。批量接口方便后续实现更高效的 API 调用，也便于测试一次性断言 provider 收到了哪些 block。

备选方案是每个 block 单独调用 provider。实现更简单，但会让真实 API 调用成本更高，也更难加入批处理、限流和上下文策略。

### 4. Provider factory 默认选择 OpenAI-compatible，但测试和无 key 开发使用 mock

`create_translation_provider(name=None)` 默认等价于 `openai`。`mock` provider 输出确定性的中文样例，例如 `"[zh] <原文>"` 或固定中文句式，并保留 block id。这样没有 API key 时仍能完成本地 TDD、CLI 和渲染验证。

OpenAI-compatible provider 不读取 Codex 或 ChatGPT 登录态；支持的 key 来源是翻译专用 `.env` 中的 `KEY`，以及标准 `OPENAI_API_KEY`。base URL 和模型名分别来自 `BASE_URL` / `OPENAI_BASE_URL`、`MODEL` / `OPENAI_MODEL`。`.env` 读取封装在 translation 模块内，只在创建翻译 provider 时发生，`parse-layout`、`extract-images`、`render-layout` 不读取这些配置。

### 5. 渲染器文本选择顺序

文本绘制内容选择顺序为：

1. `translated_text` 非空时使用真实译文。
2. 否则如果 `RenderOptions.sample_text == "zh"`，使用现有中文样本文本。
3. 否则使用原始 `text`。

这样不会破坏已有 `--sample-text zh` 调试能力，同时让真正翻译后的 layout 自然参与重建。

### 6. OpenAI-compatible 请求实现暂用标准库

第一版用标准库 HTTP 客户端调用 OpenAI-compatible Chat Completions 接口，避免立即新增 SDK 依赖。HTTP 请求封装在 provider 内部，并支持注入 transport/fake 方法，保证单元测试不发网络请求。

## Test Strategy

测试框架继续使用 `pytest`。核心设计以纯函数和依赖注入为主，避免真实外部服务进入自动化测试。

- `layout.py` / `layout_io.py`：单元测试 `translated_text` 的序列化、缺省省略和反序列化保留。
- `translation.py`：单元测试 provider factory、mock provider、`.env` 的 `BASE_URL`/`KEY`/`MODEL`、标准 OpenAI 环境变量、OpenAI-compatible 缺 key、Codex 环境变量不被当作凭据、批量调用输入项。
- `translate_layout_config`：用 recording provider 测试默认目标语言、block 过滤、原文保留和 non-text block 不变。
- `cli.py`：用临时 layout JSON 测 `translate-layout --provider mock` 成功输出；用 monkeypatch 环境测 `--provider openai` 无 key 非零退出。
- `pdf_renderer.py`：测试 `build_render_plan` 优先使用 `translated_text`，并保留原有 sample text 和 source text fallback。
- 手工验证：用真实样例跑 `parse-layout -> translate-layout --provider mock -> render-layout --debug-boxes`，确认中文/mock 文本出现在文本区域，图片/公式/表格仍按原 block 处理。

外部依赖 mock 策略：

- OpenAI-compatible provider 的配置读取、API 请求构造和凭据检查可以单测；真实网络请求不在本 change 的自动测试范围。
- mock provider 是离线端到端验证的默认工具。
- provider factory 的未知 provider、缺 key等错误路径必须可 deterministic 断言。

## Risks / Trade-offs

- [Risk] 只写 `translated_text` 不处理文本溢出，中文译文可能超出原 bbox。→ Mitigation: 本阶段只建立内容翻译链路，后续单独做排版适配和字体缩放。
- [Risk] mock provider 输出不代表真实翻译质量。→ Mitigation: mock 只用于链路验证；OpenAI provider 接入后再加入小样例人工验收。
- [Risk] 用户期望复用当前 Codex 登录账号直接翻译，但 API 认证不支持这种内部登录态复用。→ Mitigation: 明确错误信息和文档说明，提示设置 `KEY` / `OPENAI_API_KEY` 或使用 `--provider mock`。
- [Risk] `.env` 中的通用变量名可能误影响其它命令。→ Mitigation: 只在 translation provider 创建时读取 `.env`，不在模块 import 或非翻译 CLI 路径读取。
- [Risk] 后续 provider 的响应格式差异较大。→ Mitigation: provider 协议只暴露统一 `TranslationResult`，把供应商差异封装在 provider 内。
- [Risk] 大 PDF 一次性批量翻译可能超过模型上下文或请求限制。→ Mitigation: 第一版建立接口层，后续可在 translator 内加入 chunking、重试和限流，不改变 CLI 或 layout schema。
