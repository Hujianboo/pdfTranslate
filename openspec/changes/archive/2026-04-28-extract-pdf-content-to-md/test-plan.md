## 1. CLI 提取命令 (auto-test)

### From Spec: 将示例 PDF 提取到显式输出路径
- **Test:** CLI 能将仓库中的示例 PDF 写成 Markdown。
  - **Setup:** 使用 `assets/1603.08767v1.pdf` 作为输入，并准备一个临时 `.md` 输出路径。
  - **Action:** 使用示例输入和显式输出路径运行提取命令。
  - **Assert:** 退出码为 `0`，输出文件存在，且去除首尾空白后的内容长度大于 `0`。

### From Spec: 拒绝不存在的输入 PDF
- **Test:** 当输入 PDF 路径不存在时，CLI 会给出清晰失败结果。
  - **Setup:** 选择一个不存在的临时输入路径，并准备一个临时输出路径。
  - **Action:** 使用缺失输入路径运行提取命令。
  - **Assert:** 退出码非零，stderr 包含 `not found`，且不会创建输出文件。

## 2. Markdown 序列化 (auto-test)

### From Spec: 输出有序页面标题
- **Test:** Markdown 输出按页面顺序为每页包含一个标题。
  - **Setup:** 使用一个确定性的多页文本 PDF fixture，不使用扫描版或纯图片 PDF。
  - **Action:** 将该 fixture 提取到临时 Markdown 输出路径。
  - **Assert:** Markdown 中 `## Page 1` 位于 `## Page 2` 之前，并且每个 fixture 页面恰好有一个页面标题。

### From Spec: 将提取文本放在对应页面标题下
- **Test:** 页面文本会被序列化到匹配的页面标题下方。
  - **Setup:** 使用一个确定性的两页 fixture，其中第 1 页包含 `First page text`，第 2 页包含 `Second page text`。
  - **Action:** 将该 fixture 提取为 Markdown。
  - **Assert:** `First page text` 出现在 `## Page 1` 之后、`## Page 2` 之前；`Second page text` 出现在 `## Page 2` 之后。

## 3. 提取范围护栏 (auto-test)

### From Spec: 不翻译提取内容
- **Test:** 提取过程保留原始源文本。
  - **Setup:** 使用包含英文文本 `Original English sentence` 的 fixture。
  - **Action:** 将该 fixture 提取为 Markdown。
  - **Assert:** Markdown 精确保留 `Original English sentence`，不会将其替换为翻译文本。

### From Spec: 不输出位置版式元数据
- **Test:** Markdown 保持文本导向，不输出版式坐标。
  - **Setup:** 使用任意确定性的、带文本层的 PDF fixture。
  - **Action:** 将该 fixture 提取为 Markdown。
  - **Assert:** Markdown 不包含 `bbox`、`x0`、`y0`、`x1`、`y1` 等坐标风格的元数据键。
