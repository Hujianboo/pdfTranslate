# pdf-layout-rendering Specification

## Purpose
TBD - created by archiving change render-layout-config-to-pdf. Update Purpose after archive.
## Requirements
### Requirement: 从 LayoutConfig 生成 PDF
系统 SHALL 提供一个渲染能力，读取 `LayoutConfig` JSON 并生成可打开的 PDF 文件。

#### Scenario: CLI 生成 PDF 文件
- **GIVEN** 一个符合 `LayoutConfig` schema 的 JSON 文件
- **WHEN** 用户运行 `pdftranslate render-layout <input.layout.json> --output <output.pdf>`
- **THEN** 命令成功退出，并在指定路径创建一个非空 PDF 文件

#### Scenario: 输出 PDF 页数匹配 LayoutConfig
- **GIVEN** 一个包含多页 `pages` 的 `LayoutConfig`
- **WHEN** 系统将其渲染为 PDF
- **THEN** 输出 PDF 的页数等于 `LayoutConfig.pages` 数组长度

#### Scenario: 输出 PDF 页面尺寸匹配 LayoutConfig
- **GIVEN** `LayoutConfig` 中页面 `width` 为 `612.0` 且 `height` 为 `792.0`
- **WHEN** 系统将其渲染为 PDF
- **THEN** 输出 PDF 对应页面的 MediaBox 宽高分别为 `612.0` 和 `792.0`

### Requirement: 保持 bbox 坐标方向和 block 位置
系统 SHALL 按 `LayoutConfig.coordinate_system.origin = "bottom-left"` 解释 bbox，并将文本块和图片块绘制在对应页面位置。

#### Scenario: 文本块使用 bbox 左下角定位
- **GIVEN** 一个文本块 bbox 为 `{"x0": 72.0, "y0": 120.0, "x1": 180.0, "y1": 144.0}`
- **WHEN** 系统将该文本块渲染到 PDF
- **THEN** 渲染器在该页面以 `x=72.0`、`y=120.0` 作为文本绘制区域的左下定位基准

#### Scenario: 图片块使用 bbox 绘制占位区域
- **GIVEN** 一个图片块 bbox 为 `{"x0": 200.0, "y0": 240.0, "x1": 300.0, "y1": 340.0}`
- **WHEN** 系统将该图片块渲染到 PDF
- **THEN** 渲染器绘制的图片占位区域宽度为 `100.0`，高度为 `100.0`，左下角为 `(200.0, 240.0)`

#### Scenario: 调试模式绘制 block 边框和 ID
- **GIVEN** 一个包含文本块和图片块的 `LayoutConfig`
- **WHEN** 用户运行 `pdftranslate render-layout <input.layout.json> --output <output.pdf> --debug-boxes`
- **THEN** 渲染器为每个 block 绘制 bbox 边框，并绘制该 block 的 `id` 标注

### Requirement: 支持中文样本文本重建
系统 SHALL 提供中文样本文本模式，用固定中文内容替换文本块原文，帮助验证目标语言在原 bbox 内的可读性。

#### Scenario: 中文样本文本模式替换文本块内容
- **GIVEN** 一个文本块原文为英文
- **WHEN** 用户运行 `pdftranslate render-layout <input.layout.json> --output <output.pdf> --sample-text zh`
- **THEN** 渲染器使用中文样本文本绘制该文本块，而不是原始英文文本

#### Scenario: 中文样本文本保留文本块数量和 ID
- **GIVEN** 一个包含 `N` 个文本块的 `LayoutConfig`
- **WHEN** 系统使用中文样本文本模式渲染 PDF
- **THEN** 渲染计划中仍包含 `N` 个文本绘制项，并保留原文本块 `id`

### Requirement: 输出用于人工版面验收的重建 PDF
系统 SHALL 生成足够可读的重建 PDF，用于人工检查页面尺寸、坐标方向、文本位置、图片位置、多栏、标题和图注是否大体可接受。

#### Scenario: 示例 PDF 重建版面可人工检查 <!-- manual-verify -->
- **GIVEN** `assets/1603.08767v1.layout.json` 存在
- **WHEN** 用户运行 `pdftranslate render-layout assets/1603.08767v1.layout.json --output output/pdf/1603.08767v1.rebuilt.pdf --sample-text zh --debug-boxes`
- **THEN** 输出 PDF 可打开，页面尺寸与原 PDF 一致，文本落在对应区域，图片占位位置大体正确，多栏、标题和图注结构可阅读

#### Scenario: 记录重建质量限制 <!-- manual-verify -->
- **GIVEN** 示例 PDF 已重建
- **WHEN** 开发者人工查看输出 PDF
- **THEN** 开发者记录当前重建质量和明显缺口，例如字体不一致、文本溢出、图片仅占位、表格或公式不够精确

