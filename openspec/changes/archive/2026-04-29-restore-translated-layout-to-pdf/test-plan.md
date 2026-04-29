## 1. Rendered PDF Output (auto-test)

### From Spec: CLI 从翻译完成 layout 生成 PDF
- **Test:** `render-layout` 能从包含 `translated_text` 的 layout JSON 创建非空 PDF。
  - **Setup:** 创建临时 layout JSON，包含一个可翻译 text block 和 `translated_text`。
  - **Action:** 通过 CLI 运行 `pdftranslate render-layout <input> --output <output>`.
  - **Assert:** 命令返回 `0`，输出 PDF 文件存在且大小大于 `0`。

### From Spec: 翻译版 PDF 页数和页面尺寸匹配 LayoutConfig
- **Test:** 翻译版 PDF 的页数和 MediaBox 尺寸等于 LayoutConfig 页面定义。
  - **Setup:** 创建两页 layout JSON，每页尺寸为 `612.0 x 792.0`。
  - **Action:** 调用 `render_layout_pdf` 或 CLI 生成 PDF。
  - **Assert:** 使用 `pypdf.PdfReader` 读取输出 PDF，断言页数为 2，且每页 MediaBox 宽高匹配。

### From Spec: 还原时优先绘制译文
- **Test:** 输出 PDF 提取文本包含 `translated_text`。
  - **Setup:** 创建 text block，`text="Original"`，`translated_text="译文"`。
  - **Action:** 调用 `render_layout_pdf` 生成 PDF。
  - **Assert:** 读取 PDF 首页文本，包含 `译文`；渲染计划中文本命令内容也为 `译文`。

### From Spec: 图片资产在翻译版 PDF 中回填
- **Test:** 翻译版 PDF 中的 image block 使用真实图片资产。
  - **Setup:** 创建包含有效 PNG asset_path 的 image block layout。
  - **Action:** 调用 `render_layout_pdf` 生成 PDF。
  - **Assert:** `PdfReader` 读取页面资源，断言存在 `/XObject`。

### From Spec: 表格和公式在翻译版 PDF 中保留占位
- **Test:** 翻译版 PDF 保留 table/formula 占位 ID。
  - **Setup:** 创建包含 table block 和 formula block 的 layout。
  - **Action:** 调用 `render_layout_pdf` 生成 PDF。
  - **Assert:** PDF 提取文本包含 table block id 和 formula block id。

## 2. Translation Coverage Validation (auto-test)

### From Spec: 严格模式下完整译文通过
- **Test:** `--require-translations` 在所有可翻译文本块都有译文时通过。
  - **Setup:** 创建所有 translatable text block 都包含非空 `translated_text` 的 layout JSON。
  - **Action:** 通过 CLI 运行 `pdftranslate render-layout <layout> --output <output> --require-translations`。
  - **Assert:** 命令返回 `0`，输出 PDF 存在。

### From Spec: 严格模式下缺少译文失败
- **Test:** `--require-translations` 在缺少译文时失败并报告 block id。
  - **Setup:** 创建 layout JSON，其中 `p1_b2` 为 `translatable=true` 且没有 `translated_text`。
  - **Action:** 通过 CLI 运行 `pdftranslate render-layout <layout> --output <output> --require-translations`。
  - **Assert:** 命令返回非零，stderr 包含 `p1_b2`，输出 PDF 不存在。

### From Spec: 非严格模式允许部分译文
- **Test:** 默认非严格模式允许缺少译文并生成 PDF。
  - **Setup:** 创建 layout JSON，其中一个可翻译 text block 缺少 `translated_text`。
  - **Action:** 通过 CLI 运行 `pdftranslate render-layout <layout> --output <output>`。
  - **Assert:** 命令返回 `0`，输出 PDF 存在。

## 3. End-To-End Sample Review (visual)

### From Spec: Attention 翻译 layout 生成最终 PDF
- **Check:** 已翻译 Attention layout 能生成最终 PDF。
  - **How:** 运行 `pdftranslate render-layout output/layout/attention-is-all-you-need.zh.layout.json --output output/pdf/attention-is-all-you-need.zh.final.pdf --require-translations`，再用 `pypdf` 检查页数和页面尺寸，并人工打开 PDF。
  - **Acceptance:** PDF 可打开，页数和页面尺寸与 LayoutConfig 一致，正文显示中文译文，图片/表格/公式区域可定位。

### From Spec: Attention 翻译 layout 生成 debug PDF
- **Check:** debug PDF 能用于人工评估版面质量。
  - **How:** 运行 `pdftranslate render-layout output/layout/attention-is-all-you-need.zh.layout.json --output output/pdf/attention-is-all-you-need.zh.debug.pdf --require-translations --debug-boxes`，渲染第一页和正文页 PNG。
  - **Acceptance:** PNG 中能看到 block 边框、ID 和 overflow 标记；正文译文位于对应页面区域内。
