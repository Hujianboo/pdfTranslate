## MODIFIED Requirements

### Requirement: 配置范围保持在解析阶段
系统 SHALL 将解析命令的能力限制在 PDF 结构化解析和 source-only JSON 序列化范围内，不执行 AI 翻译、译文排版回填、图片内容编辑、PDF 重建、扫描版 PDF 或 OCR；翻译阶段 SHALL 通过单独命令输出增强版 layout。

#### Scenario: parse-layout 不翻译文本块内容
- **GIVEN** 输入 PDF 包含英文文本
- **WHEN** 系统通过 `parse-layout` 将其解析为 layout/config
- **THEN** 文本块 `text` 字段包含原始英文文本，而不是翻译后的文本

#### Scenario: parse-layout 不翻译公式块内容
- **GIVEN** 输入 PDF 包含数学公式
- **WHEN** 系统通过 `parse-layout` 将其解析为 layout/config
- **THEN** 公式块保留原始公式文本或来源引用，而不是翻译后的公式内容

#### Scenario: parse-layout 不输出译文或重建结果
- **GIVEN** 一个 PDF 输入文件
- **WHEN** 系统通过 `parse-layout` 将其解析为 layout/config
- **THEN** JSON 不包含 `translated_text`、`target_text`、`rebuilt_pdf`、`edited_image` 或 OCR 结果字段

#### Scenario: translate-layout 可以输出译文字段
- **GIVEN** 一个 source-only layout/config 中存在可翻译 text block
- **WHEN** 系统通过 `translate-layout` 输出增强版 layout/config
- **THEN** 对应 text block 可以包含 `translated_text` 字段

## ADDED Requirements

### Requirement: 增强版 LayoutConfig 保留译文
系统 SHALL 允许翻译阶段在 text block 上写入可选译文字段，同时保持原始文本、bbox、style、页面结构和非文本 block 不变。

#### Scenario: text block 可以包含 translated_text
- **GIVEN** 一个 text block 已完成翻译
- **WHEN** 系统序列化增强版 layout/config
- **THEN** 该 text block 包含字符串字段 `translated_text`

#### Scenario: 没有译文的 text block 不输出 translated_text
- **GIVEN** 一个 text block 尚未完成翻译
- **WHEN** 系统序列化 layout/config
- **THEN** 该 text block 不包含 `translated_text` 字段

#### Scenario: 反序列化保留 translated_text
- **GIVEN** 一个 layout JSON 的 text block 包含 `translated_text`
- **WHEN** 系统通过 `layout_config_from_dict` 读取该 JSON
- **THEN** 读出的 text block 保留相同的 `translated_text`
