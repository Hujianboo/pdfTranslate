## 1. Layout Block Models (auto-test)

### From Spec: 表格块包含后续重建所需字段
- **Test:** `TableBlock.to_dict()` 输出 `id`、`kind`、`page_number`、`bbox` 和 `table` 字段。
  - **Setup:** 构造包含一个 `TableInfo` 的 `TableBlock(id="p1_t1")`。
  - **Action:** 调用 `to_dict()`。
  - **Assert:** `kind == "table"`，并且 `table` 字段存在。

### From Spec: 表格块记录行列数量
- **Test:** `TableInfo` 序列化保留 `num_rows` 和 `num_cols`。
  - **Setup:** 构造 `TableInfo(num_rows=3, num_cols=2, cells=[])`。
  - **Action:** 调用 `TableBlock.to_dict()`。
  - **Assert:** 输出 `table.num_rows == 3` 且 `table.num_cols == 2`。

### From Spec: 表格块记录单元格结构
- **Test:** 表格单元格序列化保留文本、行列范围、span 和可选 bbox。
  - **Setup:** 构造一个 `TableCell(text="A1", row_start=0, row_end=1, col_start=0, col_end=1, row_span=1, col_span=1, bbox=BBox(...))`。
  - **Action:** 调用 `TableBlock.to_dict()`。
  - **Assert:** 输出单元格包含 `text`、`row_start`、`row_end`、`col_start`、`col_end`、`row_span`、`col_span` 和 `bbox`。

### From Spec: 表格单元格记录表头标记
- **Test:** 表格单元格序列化保留 `column_header` 和 `row_header`。
  - **Setup:** 构造 `TableCell(column_header=True, row_header=False)`。
  - **Action:** 调用 `TableBlock.to_dict()`。
  - **Assert:** 输出单元格 `column_header is True` 且 `row_header is False`。

### From Spec: 公式块包含后续保护所需字段
- **Test:** `FormulaBlock.to_dict()` 输出 `id`、`kind`、`page_number`、`bbox`、`formula` 和 `translatable`。
  - **Setup:** 构造 `FormulaBlock(id="p1_f1", formula=FormulaInfo(text="E=mc^2"))`。
  - **Action:** 调用 `to_dict()`。
  - **Assert:** `kind == "formula"`，`formula.text == "E=mc^2"`，`translatable is False`。

### From Spec: 公式块默认不参与普通文本翻译
- **Test:** `FormulaBlock` 默认 `translatable=False`。
  - **Setup:** 构造未显式传入 `translatable` 的 `FormulaBlock`。
  - **Action:** 调用 `to_dict()`。
  - **Assert:** 输出 `translatable` 等于 `False`。

### From Spec: 公式块记录原始文本或引用
- **Test:** `FormulaInfo` 至少能保存 `text` 或 `ref`。
  - **Setup:** 分别构造 `FormulaInfo(text="x+y")` 和 `FormulaInfo(ref="#/texts/1")`。
  - **Action:** 调用对应 `FormulaBlock.to_dict()`。
  - **Assert:** 第一种输出 `formula.text == "x+y"`；第二种输出 `formula.ref == "#/texts/1"`。

## 2. LayoutConfig Parsing and IO (auto-test)

### From Spec: 表格块 ID 稳定且可追踪
- **Test:** fake Docling document 中同一页面同一顺序 table item 连续映射为相同 ID。
  - **Setup:** 构造包含两页和两个 table item 的 fake Docling document。
  - **Action:** 连续两次调用 `_layout_from_docling_document`。
  - **Assert:** 两次 table block ID 相同，且格式为 `p1_t1`、`p2_t1`。

### From Spec: 公式块 ID 稳定且可追踪
- **Test:** fake Docling document 中同一页面同一顺序 formula item 连续映射为相同 ID。
  - **Setup:** 构造包含两个 formula item 的 fake Docling document。
  - **Action:** 连续两次调用 `_layout_from_docling_document`。
  - **Assert:** 两次 formula block ID 相同，且格式为 `p1_f1`、`p2_f1`。

### From Spec: 表格块包含后续重建所需字段
- **Test:** `_layout_from_docling_document` 将 Docling `tables` 映射为 `TableBlock`。
  - **Setup:** fake document 包含一个 `tables` item，带 provenance bbox 和 `data.num_rows/num_cols/table_cells`。
  - **Action:** 调用 `_layout_from_docling_document`。
  - **Assert:** 输出页面包含 `kind == "table"` 的 block，且 bbox 与 provenance 一致。

### From Spec: 表格块记录单元格结构
- **Test:** Docling table cell 映射到 LayoutConfig `table.cells`。
  - **Setup:** fake table data 包含一个 cell，带 `text`、行列 offset、span、header 标记和 bbox。
  - **Action:** 调用 `_layout_from_docling_document`。
  - **Assert:** 输出 cell 字段与 fake cell 一致。

### From Spec: 公式块包含后续保护所需字段
- **Test:** `_layout_from_docling_document` 将 Docling `FormulaItem` 映射为 `FormulaBlock`。
  - **Setup:** fake document 的 `texts` 或专用 formula collection 中包含一个 `FormulaItem` 等价对象，带 `text/orig/self_ref` 和 provenance bbox。
  - **Action:** 调用 `_layout_from_docling_document`。
  - **Assert:** 输出页面包含 `kind == "formula"` 的 block，且 `translatable is False`。

### From Spec: 公式块记录原始文本或引用
- **Test:** formula item 的 `text`、`orig` 或 `self_ref` 被写入 `FormulaInfo`。
  - **Setup:** 分别构造 text 非空、orig 非空、仅 self_ref 非空的 fake formula item。
  - **Action:** 调用 formula item 映射 helper。
  - **Assert:** 输出 formula 至少包含非空 `text` 或 `ref`。

### From Spec: 解析 PDF 为 JSON 配置文件
- **Test:** `parse-layout` CLI 仍输出可解析 JSON，且新 block 类型不会破坏现有命令。
  - **Setup:** monkeypatch `parse_pdf_layout` 返回包含 text/image/table/formula 的 `LayoutConfig`。
  - **Action:** 调用 `main(["parse-layout", input_pdf, "--output", output])`。
  - **Assert:** 返回码为 `0`，输出 JSON 可解析并包含 table/formula block。

### From Spec: 不翻译公式块内容
- **Test:** parse 阶段不会写入翻译字段或修改公式文本。
  - **Setup:** fake formula item 文本为 `E=mc^2`。
  - **Action:** 调用 `_layout_from_docling_document` 并序列化。
  - **Assert:** 输出公式文本仍为 `E=mc^2`，且不包含 `translated_text` 或 `target_text`。

### From Spec: 不输出译文或重建结果
- **Test:** 包含 table/formula 的 LayoutConfig JSON 不包含非目标字段。
  - **Setup:** 构造包含 text/image/table/formula 的 `LayoutConfig`。
  - **Action:** 调用 `to_json()`。
  - **Assert:** JSON 不包含 `translated_text`、`target_text`、`rebuilt_pdf`、`edited_image` 或 OCR 结果字段。

## 3. Layout IO Compatibility (auto-test)

### From Spec: 表格块包含后续重建所需字段
- **Test:** `layout_config_from_dict` 能读取 table block。
  - **Setup:** 构造包含 table block 的 layout dict。
  - **Action:** 调用 `layout_config_from_dict`。
  - **Assert:** 输出 block 是 `TableBlock`，字段值与输入一致。

### From Spec: 公式块包含后续保护所需字段
- **Test:** `layout_config_from_dict` 能读取 formula block。
  - **Setup:** 构造包含 formula block 的 layout dict。
  - **Action:** 调用 `layout_config_from_dict`。
  - **Assert:** 输出 block 是 `FormulaBlock`，`translatable is False`。

### From Spec: 配置包含顶层元数据
- **Test:** 新 block 类型不改变顶层 metadata。
  - **Setup:** 构造包含 table/formula block 的 layout dict。
  - **Action:** 反序列化后再 `to_dict()`。
  - **Assert:** 顶层仍包含 `schema_version`、`source_file`、`coordinate_system` 和 `pages`。

## 4. Renderer Placeholder Plan (auto-test)

### From Spec: 表格块使用 bbox 绘制占位区域
- **Test:** table block bbox 映射为 `table_placeholder` 绘制命令。
  - **Setup:** 构造 bbox 为 `72,300,540,520` 的 `TableBlock`。
  - **Action:** 调用 `build_render_plan`。
  - **Assert:** 命令 `kind == "table_placeholder"`，`x=72`、`y=300`、`width=468`、`height=220`。

### From Spec: 公式块使用 bbox 绘制占位区域
- **Test:** formula block bbox 映射为 `formula_placeholder` 绘制命令。
  - **Setup:** 构造 bbox 为 `180,420,432,456` 的 `FormulaBlock`。
  - **Action:** 调用 `build_render_plan`。
  - **Assert:** 命令 `kind == "formula_placeholder"`，`x=180`、`y=420`、`width=252`、`height=36`。

### From Spec: 调试模式绘制 block 边框和 ID
- **Test:** `debug_boxes=True` 时 table/formula 也生成 debug box 和 label。
  - **Setup:** 构造包含 text/image/table/formula 的 `LayoutConfig`。
  - **Action:** 调用 `build_render_plan(RenderOptions(debug_boxes=True))`。
  - **Assert:** debug box 和 label 的 block IDs 覆盖所有四种 block。

### From Spec: 表格块绘制带 ID 的占位框
- **Test:** PDF 写出层可执行 table placeholder 命令。
  - **Setup:** 构造包含 `p2_t1` table block 的 LayoutConfig。
  - **Action:** 调用 `render_layout_pdf`，再用 `pypdf` 抽取文本。
  - **Assert:** 输出 PDF 非空，页面文本包含 `p2_t1`。

### From Spec: 公式块绘制带 ID 的占位框
- **Test:** PDF 写出层可执行 formula placeholder 命令。
  - **Setup:** 构造包含 `p3_f1` formula block 的 LayoutConfig。
  - **Action:** 调用 `render_layout_pdf`，再用 `pypdf` 抽取文本。
  - **Assert:** 输出 PDF 非空，页面文本包含 `p3_f1`。

## 5. Sample PDF Visual Review (manual)

### From Spec: 示例 PDF 表格公式位置可人工检查
- **Check:** 用包含表格或公式的样例 PDF 验证 table/formula 占位框位置。
  - **Steps:** 准备或生成一个包含简单表格和公式的样例 PDF；运行 `pdftranslate parse-layout <sample.pdf> --output output/layout/table-formula.layout.json`；运行 `pdftranslate render-layout output/layout/table-formula.layout.json --output output/pdf/table-formula.rebuilt.debug.pdf --debug-boxes`；渲染或打开输出 PDF。
  - **Acceptance:** table/formula 占位框大体覆盖原表格和公式区域；页面尺寸、坐标方向、文本/图片渲染不回归。
