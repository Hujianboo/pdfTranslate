## 1. Layout Renderer Core (auto-test)

### From Spec: 输出 PDF 页数匹配 LayoutConfig
- **Test:** 渲染包含 2 页的最小 LayoutConfig 后，输出 PDF 页数等于 2。
  - **Setup:** 构造包含两个 `PageLayout` 的 JSON fixture，每页尺寸不同或相同均可。
  - **Action:** 调用 renderer 将 fixture 写入临时 PDF。
  - **Assert:** 使用 `pypdf.PdfReader` 读取输出 PDF，`len(reader.pages) == 2`。

### From Spec: 输出 PDF 页面尺寸匹配 LayoutConfig
- **Test:** 渲染指定页面尺寸后，PDF MediaBox 宽高匹配 LayoutConfig。
  - **Setup:** 构造一页 LayoutConfig，`width=612.0`，`height=792.0`。
  - **Action:** 调用 renderer 写入临时 PDF。
  - **Assert:** 使用 `pypdf.PdfReader` 读取第一页 MediaBox，宽高分别等于 `612.0` 和 `792.0`。

### From Spec: 文本块使用 bbox 左下角定位
- **Test:** 文本绘制计划使用 bbox 的 `x0`、`y0` 作为定位基准。
  - **Setup:** 构造一个文本块，bbox 为 `x0=72.0`、`y0=120.0`、`x1=180.0`、`y1=144.0`。
  - **Action:** 调用纯函数生成渲染计划或使用 spy canvas 捕获绘制命令。
  - **Assert:** 捕获到的文本绘制项包含 `x=72.0`、`y=120.0`、`width=108.0`、`height=24.0`。

### From Spec: 图片块使用 bbox 绘制占位区域
- **Test:** 图片块占位绘制计划使用 bbox 左下角和宽高。
  - **Setup:** 构造一个图片块，bbox 为 `x0=200.0`、`y0=240.0`、`x1=300.0`、`y1=340.0`。
  - **Action:** 调用纯函数生成渲染计划或使用 spy canvas 捕获绘制命令。
  - **Assert:** 捕获到的图片占位项包含 `x=200.0`、`y=240.0`、`width=100.0`、`height=100.0`。

### From Spec: 调试模式绘制 block 边框和 ID
- **Test:** debug 模式为每个 block 生成 bbox 边框和 id 标注绘制项。
  - **Setup:** 构造一页 LayoutConfig，包含一个文本块和一个图片块。
  - **Action:** 以 `debug_boxes=True` 生成渲染计划。
  - **Assert:** 渲染计划中每个 block 都有 `debug_box` 和 `debug_label` 项，label 文本等于 block `id`。

## 2. Chinese Sample Text Rendering (auto-test)

### From Spec: 中文样本文本模式替换文本块内容
- **Test:** `sample_text="zh"` 时文本绘制项使用中文样本文本，不使用原英文。
  - **Setup:** 构造一个文本块，原文为 `Original English text`。
  - **Action:** 以 `sample_text="zh"` 生成渲染计划。
  - **Assert:** 文本绘制项内容包含中文字符，且不等于 `Original English text`。

### From Spec: 中文样本文本保留文本块数量和 ID
- **Test:** 中文样本文本模式不改变文本块数量和 block id。
  - **Setup:** 构造包含 3 个文本块的 LayoutConfig，ID 为 `p1_b1`、`p1_b2`、`p2_b1`。
  - **Action:** 以 `sample_text="zh"` 生成渲染计划。
  - **Assert:** 文本绘制项数量为 3，绘制项 block id 序列保持为 `["p1_b1", "p1_b2", "p2_b1"]`。

## 3. CLI Rendering (auto-test)

### From Spec: CLI 生成 PDF 文件
- **Test:** `pdftranslate render-layout` 从 LayoutConfig JSON 创建非空 PDF。
  - **Setup:** 写入一个最小 LayoutConfig JSON fixture 到临时目录。
  - **Action:** 调用 `main(["render-layout", input_json, "--output", output_pdf])`。
  - **Assert:** 返回码为 `0`，输出 PDF 存在且文件大小大于 `0`。

### From Spec: CLI 生成 PDF 文件
- **Test:** console script 暴露 `render-layout` 命令。
  - **Setup:** 写入一个最小 LayoutConfig JSON fixture 到临时目录。
  - **Action:** 使用 `subprocess.run(["uv", "run", "pdftranslate", "render-layout", input_json, "--output", output_pdf])`。
  - **Assert:** 进程返回码为 `0`，输出 PDF 存在且文件大小大于 `0`。

## 4. Rebuilt PDF Visual Review (manual)

### From Spec: 示例 PDF 重建版面可人工检查
- **Check:** 示例 `assets/1603.08767v1.layout.json` 能生成用于人工验收的重建 PDF。
  - **Steps:** 运行 `pdftranslate render-layout assets/1603.08767v1.layout.json --output output/pdf/1603.08767v1.rebuilt.pdf --sample-text zh --debug-boxes`；使用 PDF 阅读器打开输出文件；必要时用 `pdftoppm` 渲染前几页为 PNG。
  - **Acceptance:** 输出 PDF 可打开；页面尺寸与原 PDF 一致；文本块大体落在原区域；图片占位大体落在原图片区域；标题、图注和多栏结构可阅读。

### From Spec: 记录重建质量限制
- **Check:** 记录第一版重建效果和缺口，供后续判断是否补充更细粒度 layout 信息。
  - **Steps:** 查看重建 PDF 的前 3 页和含图片页；记录字体、换行、溢出、图片占位、表格/公式、多栏对齐的明显问题。
  - **Acceptance:** `tasks.md` 或实现记录中包含重建质量摘要，并明确哪些问题属于后续优化范围。
