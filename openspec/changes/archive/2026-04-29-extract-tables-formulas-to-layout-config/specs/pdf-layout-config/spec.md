## MODIFIED Requirements

### Requirement: 输出结构化 PDF layout 配置
系统 SHALL 提供一个结构化 layout/config 解析能力，将带文本层 PDF 输出为确定性的 JSON 配置文档，并包含后续翻译和重建需要的文本、图片、表格和公式块。

#### Scenario: 提供 LayoutConfig schema 说明文档
- **GIVEN** 开发者需要实现或消费 layout/config JSON
- **WHEN** 查看本变更的设计产物
- **THEN** 存在 `layout-config-schema.md` 或等价 schema 说明，并说明 schema version、坐标系、顶层字段、页面字段、文本块字段、图片块字段、表格块字段、公式块字段、bbox、style、image 和非目标字段

#### Scenario: 解析 PDF 为 JSON 配置文件
- **GIVEN** 一个带文本层的 PDF 输入文件
- **WHEN** 用户运行 layout/config 解析命令并指定 JSON 输出路径
- **THEN** 命令成功退出，并在指定路径创建一个可解析的 JSON 文件

#### Scenario: 配置包含顶层元数据
- **GIVEN** 一个带文本层的 PDF 输入文件
- **WHEN** 系统将其解析为 layout/config
- **THEN** JSON 顶层包含 `schema_version`、`source_file` 和 `pages` 字段

### Requirement: 配置范围保持在解析阶段
系统 SHALL 将本次能力限制在 PDF 结构化解析和 JSON 序列化范围内，不执行 AI 翻译、译文排版回填、图片内容编辑、PDF 重建、扫描版 PDF 或 OCR。

#### Scenario: 不翻译文本块内容
- **GIVEN** 输入 PDF 包含英文文本
- **WHEN** 系统将其解析为 layout/config
- **THEN** 文本块 `text` 字段包含原始英文文本，而不是翻译后的文本

#### Scenario: 不翻译公式块内容
- **GIVEN** 输入 PDF 包含数学公式
- **WHEN** 系统将其解析为 layout/config
- **THEN** 公式块保留原始公式文本或来源引用，而不是翻译后的公式内容

#### Scenario: 不输出译文或重建结果
- **GIVEN** 一个 PDF 输入文件
- **WHEN** 系统将其解析为 layout/config
- **THEN** JSON 不包含 `translated_text`、`target_text`、`rebuilt_pdf`、`edited_image` 或 OCR 结果字段

## ADDED Requirements

### Requirement: 配置保留表格块结构信息
系统 SHALL 将 PDF 页面中的表格对象记录为表格块，并为每个表格块输出稳定 ID、bbox 坐标、页面编号、行列数量和单元格结构。

#### Scenario: 表格块包含后续重建所需字段
- **GIVEN** 一个 PDF 页面包含可识别表格对象
- **WHEN** 系统将其解析为 layout/config
- **THEN** 页面中的每个表格块包含 `id`、`kind`、`page_number`、`bbox` 和 `table` 字段，且 `kind` 等于 `table`

#### Scenario: 表格块 ID 稳定且可追踪
- **GIVEN** 同一个包含表格的 PDF 输入文件
- **WHEN** 系统连续两次解析为 layout/config
- **THEN** 两次输出中同一页面同一顺序表格块的 `id` 完全一致，并采用 `p<page>_t<table>` 格式

#### Scenario: 表格块记录行列数量
- **GIVEN** 一个表格对象具有 3 行和 2 列
- **WHEN** 系统将其解析为 layout/config
- **THEN** 该表格块的 `table` 对象包含 `num_rows=3` 和 `num_cols=2`

#### Scenario: 表格块记录单元格结构
- **GIVEN** 一个表格对象包含单元格文本、行列位置和跨行跨列信息
- **WHEN** 系统将其解析为 layout/config
- **THEN** 该表格块的 `table.cells` 数组中每个单元格包含 `text`、`row_start`、`row_end`、`col_start`、`col_end`、`row_span`、`col_span` 和可选 `bbox`

#### Scenario: 表格单元格记录表头标记
- **GIVEN** 表格对象中的某个单元格被识别为列头或行头
- **WHEN** 系统将其解析为 layout/config
- **THEN** 对应单元格包含布尔字段 `column_header` 或 `row_header`，并保留其识别值

### Requirement: 配置保留公式块定位信息
系统 SHALL 将 PDF 页面中的公式对象记录为公式块，并为每个公式块输出稳定 ID、bbox 坐标、页面编号、原始公式文本或来源引用，以及默认不翻译标记。

#### Scenario: 公式块包含后续保护所需字段
- **GIVEN** 一个 PDF 页面包含可识别公式对象
- **WHEN** 系统将其解析为 layout/config
- **THEN** 页面中的每个公式块包含 `id`、`kind`、`page_number`、`bbox`、`formula` 和 `translatable` 字段，且 `kind` 等于 `formula`

#### Scenario: 公式块 ID 稳定且可追踪
- **GIVEN** 同一个包含公式的 PDF 输入文件
- **WHEN** 系统连续两次解析为 layout/config
- **THEN** 两次输出中同一页面同一顺序公式块的 `id` 完全一致，并采用 `p<page>_f<formula>` 格式

#### Scenario: 公式块默认不参与普通文本翻译
- **GIVEN** 一个公式块来自 PDF 页面上的数学公式
- **WHEN** 系统将其解析为 layout/config
- **THEN** 该公式块的 `translatable` 字段等于 `false`

#### Scenario: 公式块记录原始文本或引用
- **GIVEN** Docling 为公式提供 `text`、`orig` 或 self reference
- **WHEN** 系统将其解析为 layout/config
- **THEN** 该公式块的 `formula` 对象包含字符串字段 `text` 或 `ref`，且至少一个字段非空
