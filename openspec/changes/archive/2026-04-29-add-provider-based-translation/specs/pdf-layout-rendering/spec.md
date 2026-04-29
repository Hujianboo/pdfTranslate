## MODIFIED Requirements

### Requirement: 支持中文样本文本重建
系统 SHALL 提供中文样本文本模式，用固定中文内容替换没有真实译文的文本块原文，帮助验证目标语言在原 bbox 内的可读性；当 text block 已包含真实译文时，渲染器 SHALL 优先使用该译文。

#### Scenario: 中文样本文本模式替换无译文文本块内容
- **GIVEN** 一个文本块原文为英文且不包含 `translated_text`
- **WHEN** 用户运行 `pdftranslate render-layout <input.layout.json> --output <output.pdf> --sample-text zh`
- **THEN** 渲染器使用中文样本文本绘制该文本块，而不是原始英文文本

#### Scenario: 中文样本文本模式保留文本块数量和 ID
- **GIVEN** 一个包含 `N` 个文本块的 `LayoutConfig`
- **WHEN** 系统使用中文样本文本模式渲染 PDF
- **THEN** 渲染计划中仍包含 `N` 个文本绘制项，并保留原文本块 `id`

#### Scenario: 渲染器优先使用真实译文
- **GIVEN** 一个 text block 包含 `text="Original"` 和 `translated_text="译文"`
- **WHEN** 系统渲染该 layout
- **THEN** 文本绘制命令的内容为 `译文`

#### Scenario: 无译文且无样本文本时使用原文
- **GIVEN** 一个 text block 包含 `text="Original"` 且不包含 `translated_text`
- **WHEN** 系统渲染该 layout 且未启用 `--sample-text`
- **THEN** 文本绘制命令的内容为 `Original`
