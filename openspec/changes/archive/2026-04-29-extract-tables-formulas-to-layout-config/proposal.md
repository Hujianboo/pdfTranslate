## Why

当前 `LayoutConfig` 已经能表达文本块、图片块和图片资产路径，但表格与公式仍然被混在普通文本或图片占位中，后续翻译和原样重建无法知道哪些内容需要特殊处理。现在需要先把表格和公式作为一等结构进入配置层，为后续表格翻译、公式保护和更可靠的 PDF 重建打基础。

## What Changes

- 扩展 `LayoutConfig`，新增 `table` 和 `formula` 两类 block，保持稳定 ID、页面编号、bbox 和来源引用。
- 表格块记录行列数、单元格文本、单元格行列范围、表头/行头标记，以及可选 caption/ref 信息。
- 公式块记录公式文本、bbox、公式类型占位字段和 `translatable=false`，默认用于保护公式不被普通文本翻译破坏。
- `parse-layout` 从 Docling document 的 `tables` 和 `formula` item 中提取结构化配置。
- `layout_io` 支持新 block 类型的反序列化，同时继续兼容旧 text/image-only layout JSON。
- `render-layout` 对 table/formula block 至少生成可调试的占位绘制命令，帮助人工检查 bbox、坐标方向和阅读位置。
- 本阶段不做真实表格重排、公式 LaTeX 识别、公式 OCR、扫描版 PDF、AI 翻译或像素级渲染。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `pdf-layout-config`: 新增 table/formula block 的 schema 要求，表格和公式需要作为结构化配置输出。
- `pdf-layout-rendering`: 渲染器需要识别 table/formula block，并提供占位或 debug 绘制能力以验证位置。

## Impact

- 更新 `pdftranslate.layout`，新增 `TableBlock`、`TableCell`、`FormulaBlock` 等数据模型。
- 更新 `pdftranslate.docling_adapter`，从 Docling `document.tables` 和 `FormulaItem` 提取结构。
- 更新 `pdftranslate.layout_io`，支持 table/formula block 反序列化。
- 更新 `pdftranslate.pdf_renderer`，让 table/formula block 生成占位/调试命令。
- 更新测试夹具、schema 文档测试、CLI/packaging 冒烟测试和样例 PDF 人工验证记录。
