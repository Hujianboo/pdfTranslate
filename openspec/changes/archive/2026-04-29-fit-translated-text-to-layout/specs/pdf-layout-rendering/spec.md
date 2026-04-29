## ADDED Requirements

### Requirement: 译文文本适配 bbox
系统 SHALL 在渲染 `TextBlock.translated_text` 时，根据文本块 bbox 的宽度和高度计算可绘制行，优先让中文译文在原页面区域内可读，而不是简单按原字符串绘制。

#### Scenario: 译文优先使用中文换行
- **GIVEN** 一个文本块 bbox 宽度只能容纳一行短中文，且 `translated_text` 为 `这是第一句。这是第二句。`
- **WHEN** 系统构建渲染计划
- **THEN** 文本绘制项包含多行布局，且每一行的估算宽度不超过该文本块 bbox 宽度

#### Scenario: 原文在没有译文时保持现有渲染路径
- **GIVEN** 一个文本块没有 `translated_text`
- **WHEN** 系统构建渲染计划
- **THEN** 文本绘制项使用原始 `text` 字段作为绘制内容

#### Scenario: 样本文本仍低于真实译文优先级
- **GIVEN** 一个文本块同时存在 `translated_text`，且用户启用 `--sample-text zh`
- **WHEN** 系统构建渲染计划
- **THEN** 文本绘制项使用 `translated_text`，而不是中文样本文本

### Requirement: 字号和行距自动收缩
系统 SHALL 在译文按默认字号无法放入 bbox 高度时，逐步降低字号和行距，直到文本放入 bbox 或达到最小可读字号。

#### Scenario: 高度不足时降低字号
- **GIVEN** 一个文本块 bbox 高度不足以用默认字号容纳三行中文译文
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项的实际字号小于默认字号

#### Scenario: 文本可放入时不低于最小字号
- **GIVEN** 一个文本块 bbox 足以用默认字号容纳译文
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项的实际字号等于默认字号，且未标记 overflow

#### Scenario: 极小 bbox 不会生成无效字号
- **GIVEN** 一个文本块 bbox 极窄或极矮
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项的实际字号大于 `0`，且不小于渲染器定义的最小字号

### Requirement: 溢出诊断
系统 SHALL 对达到最小字号后仍无法完整放入 bbox 的译文文本块记录确定性的 overflow 诊断，供测试、debug PDF 和人工验收使用。

#### Scenario: 无法完整放入时标记 overflow
- **GIVEN** 一个文本块 bbox 无法在最小字号下容纳完整 `translated_text`
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项标记 `overflow=true`，并记录未能绘制完整文本的 block id

#### Scenario: 可完整放入时不标记 overflow
- **GIVEN** 一个文本块 bbox 可以容纳完整 `translated_text`
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项标记 `overflow=false`

#### Scenario: debug 模式显示溢出文本块 <!-- manual-verify -->
- **GIVEN** 一个包含 overflow 文本块的 LayoutConfig
- **WHEN** 用户运行 `pdftranslate render-layout <layout.json> --output <output.pdf> --debug-boxes`
- **THEN** 输出 PDF 中该文本块的 debug 标记能帮助人工定位发生溢出的区域

### Requirement: 窄文本块保守处理
系统 SHALL 对宽度不足以正常横排中文的文本块采用保守策略，避免把译文挤成不可读的逐字竖排。

#### Scenario: 过窄文本块保留源文本
- **GIVEN** 一个文本块 bbox 宽度小于渲染器定义的窄块阈值，且该文本块包含 `translated_text`
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项使用源文本或安全截断文本，而不是逐字绘制完整中文译文

#### Scenario: 过窄文本块记录适配原因
- **GIVEN** 一个文本块触发窄文本块保守处理
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项记录确定性的 fit reason，说明其未使用完整译文横排

### Requirement: 示例译文 PDF 可读性验收
系统 SHALL 能用已翻译的 LayoutConfig 生成比直接硬塞译文更可读的重建 PDF，作为后续翻译 PDF 工作的人工验收基线。

#### Scenario: Attention 示例译文重建可人工检查 <!-- manual-verify -->
- **GIVEN** `output/layout/attention-is-all-you-need.zh.layout.json` 存在
- **WHEN** 用户运行 `pdftranslate render-layout output/layout/attention-is-all-you-need.zh.layout.json --output output/pdf/attention-is-all-you-need.zh.fit.pdf --debug-boxes`
- **THEN** 输出 PDF 可打开，页面尺寸与 LayoutConfig 一致，正文译文不会大面积横向溢出页面，且 overflow 区域可被定位
