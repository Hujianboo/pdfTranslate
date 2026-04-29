## Context

当前项目已经具备普通文本型 PDF 的 `LayoutConfig` 解析、图片资产提取和基础 PDF 重建能力。`LayoutConfig` 目前表达 text/image 两类 block，其中 image 已经支持 `asset_path` 回填真实图片。下一步要解决的是表格和公式：如果它们继续被混在普通文本或图片占位里，后续 AI 翻译会把公式当文本误翻译，重建 PDF 也无法知道哪些区域需要特殊排版。

用户当前的方向仍然是“先自己做一版可控的配置层”，并借鉴 BabelDOC 这类成熟项目的思路，但不在本阶段引入完整字符级 IL、复杂 typesetting 或外部大流水线。因此本设计延续 Docling-first：先用 Docling 已经暴露的 `document.tables`、`TableItem.data` 和 `FormulaItem` 信息，把表格/公式纳入项目自己的轻量 `LayoutConfig`。

## Goals / Non-Goals

**Goals:**

- 新增 table/formula block，让表格和公式成为 `LayoutConfig.pages[].blocks[]` 中的一等结构。
- 表格块记录稳定 ID、bbox、页码、行列数量、单元格文本、单元格行列范围、span 和表头标记。
- 公式块记录稳定 ID、bbox、页码、公式文本或来源引用，并默认 `translatable=false`。
- `parse-layout` 能从 Docling document 中提取 table/formula block，并保持 text/image 解析不回归。
- `layout_io` 能反序列化 table/formula block，同时兼容旧 layout JSON。
- `render-layout` 对 table/formula block 生成可检查的占位命令，用于验证坐标、bbox 和 debug label。
- 用自动化测试覆盖模型、Docling fake document 映射、IO、renderer plan 和 CLI；用人工检查验证真实样例 PDF 的视觉位置。

**Non-Goals:**

- 不做真实表格重排、单元格边框重建或复杂表格分页。
- 不做公式 OCR、LaTeX 识别、MathML 生成或公式图片编辑。
- 不接入 AI 翻译，也不生成译文表格。
- 不处理扫描版 PDF。
- 不把 BabelDOC 的 Document IL 直接迁入本项目。
- 不承诺表格/公式渲染像素级还原；本阶段只要求配置可追踪、位置可验证。

## Decisions

### 1. 扩展现有 block 模型，而不是新建并行 schema

在 `pdftranslate.layout` 中新增 `TableBlock`、`TableInfo`、`TableCellInfo`、`FormulaBlock`、`FormulaInfo`。它们与 `TextBlock`、`ImageBlock` 一样挂在 `PageLayout.blocks` 中，依靠 `kind` 区分类型。

备选方案是新增 `page.tables` 和 `page.formulas` 顶层数组，但这会让渲染器、debug box 和后续翻译流程必须遍历多套集合。统一 blocks 数组更接近当前系统形状，也更容易保持页面内排序。

### 2. 表格 schema 优先表达结构，不表达最终排版

`TableInfo` 记录 `num_rows`、`num_cols` 和 `cells`。每个 `TableCellInfo` 记录：

- `text`
- `row_start` / `row_end`
- `col_start` / `col_end`
- `row_span` / `col_span`
- `column_header` / `row_header`
- 可选 `bbox`

这里的目标是保留后续翻译和重建所需的结构线索，而不是立即画出精确表格。Docling 的 `TableData` 已经提供行列和单元格结构，先完整承接这些确定性字段，复杂样式和边框可以后续单独扩展。

### 3. 公式 schema 默认保护而非翻译

`FormulaBlock` 使用 `translatable=False` 作为默认值，`FormulaInfo` 记录 `text`、`ref` 和可选 `formula_type`。如果 Docling 提供公式文本，就保存 `text`；如果只有 self reference，则保存 `ref`；至少保证有一个可追踪字段非空。

备选方案是把公式继续作为 `TextBlock(translatable=False)`，但这样后续无法区分普通不可译文本和数学公式，也无法为公式提供专门 renderer 或翻译保护策略。

### 4. Docling adapter 用类型/label 双通道识别公式

Docling document 暴露 `tables` 字段；公式通常表现为 `FormulaItem`，并且可能出现在 `document.texts` 中。实现上使用 helper：

- `_is_formula_item(item)`：优先检查类名或类型是否为 `FormulaItem`，再检查 `label` 是否包含 formula。
- 文本提取循环跳过 formula item，避免公式同时变成 `TextBlock` 和 `FormulaBlock`。
- 公式提取循环从 `document.texts` 中筛出 formula item。

这样比直接硬依赖某个 Docling 内部字段更稳，也方便用 fake item 做测试。

### 5. 坐标与排序沿用现有规则

所有 table/formula block 继续使用 `BBox` 和 `coordinate_system.origin = "bottom-left"`。排序仍按 `(page_number, -bbox.y1, bbox.x0)`，ID 分别为：

- table: `p<page>_t<table>`
- formula: `p<page>_f<formula>`

这与 `p1_b1`、`p1_i1` 的现有规则一致，能保证重复解析同一输入时 ID 稳定。

### 6. renderer 只做占位渲染

`build_render_plan` 对 `TableBlock` 生成 `table_placeholder`，对 `FormulaBlock` 生成 `formula_placeholder`。PDF 写出层绘制轻量占位框和 block ID。debug mode 继续为所有 block 画红框和标签。

这能满足“位置是否大体正确”的验证目标，同时避免在本阶段误以为已经完成表格/公式原样重建。真实表格线、单元格排版、公式字体和基线对齐以后再单独做。

### 7. 测试优先使用 fake Docling document

真实 PDF 的表格/公式识别受 Docling 模型和 PDF 内部结构影响，不适合作为主要单元测试。自动测试以 fake `SimpleNamespace` 或轻量对象模拟 Docling `TableItem` / `FormulaItem`，只验证我们自己的映射逻辑。

真实 PDF 样例只用于人工验收：看 table/formula bbox 是否在可接受区域，不作为 brittle 的自动断言。

## Test Strategy

测试仍使用 pytest。

- 模型层：直接构造 `TableBlock`、`TableCellInfo`、`FormulaBlock`，验证 `to_dict()` 输出字段、默认值和可选字段。
- Docling adapter：用 fake document 覆盖 `_layout_from_docling_document`，验证 table/formula ID、bbox、cell 字段、公式文本/ref 和 `translatable=false`。
- IO 层：构造 dict fixture，验证 `layout_config_from_dict` 能读取 table/formula，并确认旧 text/image fixture 不回归。
- CLI 层：monkeypatch `parse_pdf_layout` 返回包含 table/formula 的 config，验证 `parse-layout` 输出 JSON。
- renderer 层：优先测试 `build_render_plan`，断言 `table_placeholder` 和 `formula_placeholder` 的 x/y/width/height；PDF 写出层只验证非空 PDF 和可抽取 block ID。
- manual/visual：准备或生成含表格/公式的样例 PDF，运行 `parse-layout` 和 `render-layout --debug-boxes`，人工检查 bbox 是否大体覆盖原区域。

外部 Docling 行为只在少量集成/人工验证中覆盖；核心自动测试围绕本项目的数据模型和映射边界。

## Risks / Trade-offs

- [Risk] Docling 可能无法从某些 PDF 中稳定识别公式 → Mitigation: 公式 block 只在 Docling 提供可识别 item 时生成；未识别的内容暂时保留为普通文本或图片，后续再评估 BabelDOC/PDF 字符级分析。
- [Risk] 表格单元格 bbox 可能缺失或坐标体系与页面 bbox 不一致 → Mitigation: cell bbox 设为可选字段；表格整体 bbox 仍来自 provenance，单元格 bbox 只在可信时输出。
- [Risk] 公式可能同时出现在 `document.texts` 中导致重复 block → Mitigation: text loop 显式跳过 formula item，formula loop 单独处理。
- [Risk] 新 block 类型会让旧 renderer 或 IO 忽略/报错 → Mitigation: 同步更新 `layout_io` 和 `render-layout`；旧 text/image fixture 必须继续通过。
- [Risk] 占位渲染容易被误解为真实表格/公式重建 → Mitigation: README 和 verification notes 明确本阶段只做配置提取与位置验证。
- [Risk] 表格/公式样例 PDF 在不同 Docling 版本下输出不同 → Mitigation: 自动测试用 fake document；真实样例只做人工检查，不做精确自动断言。
