## 1. Layout Config CLI (auto-test)

### From Spec: 解析 PDF 为 JSON 配置文件
- **Test:** CLI 能将带文本层 PDF 解析为 JSON 配置文件。
  - **Setup:** 使用确定性的文本 PDF fixture 和临时 `.json` 输出路径，Docling PDF 解析默认关闭 OCR。
  - **Action:** 运行 `pdftranslate parse-layout <input.pdf> --output <output.json>`。
  - **Assert:** 退出码为 `0`，输出文件存在，且 `json.loads` 可以成功解析。

## 2. Layout Config Schema 与序列化 (auto-test)

### From Spec: 提供 LayoutConfig schema 说明文档
- **Test:** 变更包含独立的 LayoutConfig schema 文档，并覆盖关键字段定义。
  - **Setup:** 读取 `openspec/changes/parse-pdf-to-layout-config/layout-config-schema.md`。
  - **Action:** 检查文档内容。
  - **Assert:** 文档存在，并包含 `schema_version`、`coordinate_system`、`pages`、`blocks`、`text`、`image`、`bbox`、`style` 和非目标字段说明。

### From Spec: 配置包含顶层元数据
- **Test:** JSON 配置包含固定顶层字段。
  - **Setup:** 构造一个包含单页和单个文本块的内存 layout config。
  - **Action:** 将 layout config 序列化为 dict/JSON。
  - **Assert:** 顶层包含 `schema_version`、`source_file` 和 `pages`，且 `pages` 为数组。

### From Spec: 页面按原始顺序输出
- **Test:** 页面对象按 `page_number` 升序输出。
  - **Setup:** 使用一个确定性的两页文本 PDF fixture。
  - **Action:** 通过 Docling adapter 解析为 layout config。
  - **Assert:** `pages[*].page_number` 等于 `[1, 2]`。

### From Spec: 页面包含尺寸信息
- **Test:** 页面对象包含可用于回填定位的页面尺寸。
  - **Setup:** 使用任意确定性的文本 PDF fixture。
  - **Action:** 通过 Docling adapter 解析为 layout config。
  - **Assert:** 每个页面的 `width` 和 `height` 都是数字且大于 `0`。

### From Spec: 文本块包含后续翻译所需字段
- **Test:** 文本块 schema 包含 ID、kind、页码、原文、bbox 和 style。
  - **Setup:** 使用包含可提取文本的 PDF fixture。
  - **Action:** 通过 Docling adapter 解析为 layout config。
  - **Assert:** 每个非空文本块包含 `id`、`kind`、`page_number`、`text`、`bbox` 和 `style` 字段，且 `kind` 等于 `text`。

### From Spec: 文本块 ID 稳定且可追踪
- **Test:** 同一 PDF 多次解析得到稳定文本块 ID。
  - **Setup:** 使用同一个确定性文本 PDF fixture。
  - **Action:** 通过 Docling adapter 连续解析两次。
  - **Assert:** 两次输出的文本块 ID 序列完全一致，并且每个 ID 匹配 `p<page>_b<block>` 格式。

### From Spec: bbox 使用数值坐标
- **Test:** 文本块 bbox 使用数值坐标并满足基本范围关系。
  - **Setup:** 使用包含可定位文本的 PDF fixture。
  - **Action:** 通过 Docling adapter 解析为 layout config。
  - **Assert:** 每个文本块的 `bbox.x0`、`bbox.y0`、`bbox.x1`、`bbox.y1` 都是数字，且 `x1 >= x0`、`y1 >= y0`。

### From Spec: 图片块包含后续重建所需字段
- **Test:** 图片块 schema 包含 ID、kind、页码、bbox 和 image 信息。
  - **Setup:** 使用一个确定性的、包含嵌入图片的 PDF fixture。
  - **Action:** 通过 Docling adapter 解析为 layout config。
  - **Assert:** 每个图片块包含 `id`、`kind`、`page_number`、`bbox` 和 `image` 字段，且 `kind` 等于 `image`。

### From Spec: 图片块 ID 稳定且可追踪
- **Test:** 同一含图片 PDF 多次解析得到稳定图片块 ID。
  - **Setup:** 使用同一个确定性的含图片 PDF fixture。
  - **Action:** 通过 Docling adapter 连续解析两次。
  - **Assert:** 两次输出的图片块 ID 序列完全一致，并且每个 ID 匹配 `p<page>_i<image>` 格式。

### From Spec: 图片块保留尺寸和引用信息
- **Test:** 图片块保留后续 PDF 重建所需的图片尺寸和引用。
  - **Setup:** 使用包含嵌入图片的 PDF fixture。
  - **Action:** 通过 Docling adapter 解析为 layout config。
  - **Assert:** 每个图片块的 `image.width` 和 `image.height` 都是大于 `0` 的数字，`image.ref` 是非空字符串。

## 3. 解析范围护栏 (auto-test)

### From Spec: 不翻译文本块内容
- **Test:** layout config 保留原始源文本。
  - **Setup:** 使用包含英文文本 `Original English sentence` 的 PDF fixture。
  - **Action:** 通过 Docling adapter 解析为 layout config。
  - **Assert:** 至少一个文本块的 `text` 包含 `Original English sentence`，且不会被替换为译文。

### From Spec: 不输出译文或重建结果
- **Test:** layout config 不包含本阶段以外的翻译、OCR 或 PDF 重建字段。
  - **Setup:** 使用任意确定性的文本 PDF fixture。
  - **Action:** 通过 Docling adapter 解析并序列化为 JSON 字符串。
  - **Assert:** JSON 字符串不包含 `translated_text`、`target_text`、`rebuilt_pdf`、`edited_image` 或 OCR 结果字段。

### From Spec: 不输出译文或重建结果
- **Test:** Docling PDF 解析默认关闭 OCR。
  - **Setup:** 构造或检查 Docling adapter 使用的 PDF pipeline options。
  - **Action:** 初始化 Docling adapter。
  - **Assert:** adapter 默认配置不会启用 OCR，扫描版 PDF/OCR 仍不属于本阶段范围。
