## Context

项目当前已有两条输入侧能力：`pdftranslate extract` 使用 PDFium 输出 Markdown，`pdftranslate parse-layout` 使用 Docling 输出 `LayoutConfig` JSON。`LayoutConfig` 已包含页面尺寸、bottom-left 坐标系、文本块、图片块、bbox 和基础样式占位。用户现在需要验证这些字段能否支撑后续 PDF 回填，因此本变更先做不接 AI 的重建闭环：`LayoutConfig JSON -> 可阅读 PDF`。

当前目标不是像素级复刻原 PDF，而是判断页面尺寸是否正确、坐标方向是否正确、文本是否落在正确区域、图片位置是否大体正确、多栏/标题/图注结构是否可接受。目标语言先用固定中文样本文本替换，内容无所谓，重点验证中文文本在原 bbox 内的可读性和溢出风险。

## Goals / Non-Goals

**Goals:**

- 新增 `pdftranslate render-layout <input.layout.json> --output <output.pdf>`。
- 支持 `--sample-text zh`，用固定中文样本文本替换文本块内容。
- 支持 `--debug-boxes`，绘制 bbox 边框和 block id。
- 输出 PDF 页数和页面尺寸与 `LayoutConfig.pages` 一致。
- 按 bottom-left 坐标解释 bbox，不做 y 轴翻转。
- 对图片块绘制占位框和引用 ID，验证位置与尺寸。
- 生成 `output/pdf/1603.08767v1.rebuilt.pdf` 作为示例验收目标。

**Non-Goals:**

- 不接入 AI 翻译。
- 不生成最终翻译 PDF。
- 不导出或嵌入原 PDF 图片二进制。
- 不处理 OCR/扫描版 PDF。
- 不追求字体、字距、行高、公式、表格和图片的像素级一致。
- 不修改 `LayoutConfig` schema，除非实现证明现有字段无法完成基础重建。

## Decisions

### 使用 ReportLab 生成 PDF

使用 `reportlab` 作为 PDF 生成后端。它能直接按 PDF points 和 bottom-left 坐标绘制页面、文本、矩形和标签，和当前 `LayoutConfig.coordinate_system` 匹配。

备选方案是 PyMuPDF 或低层 PDF 操作。PyMuPDF 更适合基于原 PDF 做覆盖或编辑，但本阶段目标是验证 layout JSON 本身是否能独立重建，所以选择 ReportLab 更简单、可控、测试边界更清楚。

### 引入绘制计划作为纯测试接口

新增 renderer 模块时先生成纯数据结构，例如 `RenderPlan`、`PageRenderPlan` 和 `DrawCommand`。`build_render_plan(config, options)` 只负责把 `LayoutConfig` 映射为文本、图片占位、debug box、debug label 等绘制命令，不直接写 PDF。

这样文本定位、图片 bbox、中文样本文本、debug 标注都可以用普通 pytest 断言，不需要解析 PDF 内容或做截图比较。ReportLab 写 PDF 只负责执行绘制计划。

### 保持 layout 读取与渲染分离

当前 `pdftranslate.layout` 是纯数据模型和序列化层。为了避免把文件 IO 混入数据模型，新增 layout 读取 helper，例如 `pdftranslate.layout_io`，负责从 JSON dict/path 构造 `LayoutConfig`。renderer 消费 `LayoutConfig` 对象，不直接依赖 CLI。

### 中文样本文本使用固定文本池

`--sample-text zh` 不调用翻译服务，而是使用固定中文样本文本池按 block 顺序循环填充。绘制命令仍保留原 block id，确保后续翻译结果可以按 id 回填。

中文字体优先使用 ReportLab 内置 CID 字体 `STSong-Light`。如果环境无法注册该字体，实现应降级为默认字体并在 debug/验证记录中说明，但自动化测试只验证绘制计划包含中文字符，不依赖视觉字体渲染。

### 第一版文本布局采用 bbox 内简单换行

文本绘制先以 bbox 宽度为约束做简单换行，字号优先取 `style.font_size`，缺失时使用保守默认值。若文本超出 bbox 高度，第一版允许裁剪或停止绘制后续行，并可在 debug 模式中标记溢出。复杂自适应字号、跨页重排和段落级排版留到后续。

### 图片块绘制占位而非真实图片

当前 `LayoutConfig.image` 只有 ref、width、height、mime_type，没有图片二进制或源路径。因此第一版用矩形、交叉线和 ref/id 标签表示图片。这个足以验证图片 bbox 位置和尺寸是否大体正确。

### 输出目录约定

CLI 允许任意 `--output` 路径；人工验收示例使用 `output/pdf/1603.08767v1.rebuilt.pdf`。`.gitignore` 后续可继续忽略 `output/` 或生成 PDF，避免把验证产物误提交。

## Test Strategy

测试框架继续使用 pytest。

自动化测试分三层：

- `pdftranslate.layout_io`：用 dict/JSON fixture 构造 `LayoutConfig`，验证字段被正确读入。
- `pdftranslate.pdf_renderer` 的纯函数层：调用 `build_render_plan`，断言文本命令坐标、图片占位坐标、debug box、debug label、中文样本文本和 block id 保持稳定。
- PDF 输出层：调用 `render_layout_pdf` 写入临时 PDF，再用 `pypdf.PdfReader` 断言页数和 MediaBox 尺寸。

CLI 测试继续沿用现有 `pdftranslate.cli.main` 风格，新增 `render-layout` 命令测试；打包冒烟测试使用 `uv run pdftranslate render-layout ...`。

外部依赖策略：

- `reportlab` 是运行时依赖。
- `pypdf` 用于测试读取 PDF 页数和 MediaBox，可放在 dev dependencies。
- 不在自动化测试中依赖 PDF 阅读器、Poppler 或截图工具。

人工验证：

- 使用 `assets/1603.08767v1.layout.json` 生成 debug PDF。
- 查看前 3 页和包含图片的页面。
- 重点记录页面尺寸、坐标方向、文本位置、图片占位、多栏、标题、图注、中文样本文本是否可阅读。
- 若本地有 `pdftoppm`，可把前几页渲染为 PNG 辅助检查；没有则直接用 PDF 阅读器查看。

## Risks / Trade-offs

- [Risk] `LayoutConfig` 没有真实字体、字距、行内 span 信息，重建文本可能不够贴合原 PDF。 → Mitigation: 第一版只要求可阅读和位置大体正确，并记录缺口；后续必要时补充 span 级 layout。
- [Risk] 中文样本文本比英文更密或更长，容易溢出 bbox。 → Mitigation: 先实现简单换行和溢出记录，再根据人工验收决定是否做字号缩放。
- [Risk] ReportLab 中文字体在不同环境显示差异。 → Mitigation: 优先使用 `STSong-Light`，自动化测试只验证绘制计划，不把字体视觉作为硬性断言。
- [Risk] 图片只有占位，无法验证真实图片内容。 → Mitigation: 本阶段只验证图片 bbox 位置和尺寸；真实图片导出/嵌入作为后续 change。
- [Risk] debug box 和中文替换会影响视觉判断。 → Mitigation: CLI 同时支持普通重建和 debug 模式；人工验收优先用 debug 判断位置，再用普通模式判断阅读效果。
- [Risk] 生成 PDF 可能被误提交。 → Mitigation: 输出到 `output/pdf/`，并在实现阶段更新 `.gitignore` 忽略生成产物。
