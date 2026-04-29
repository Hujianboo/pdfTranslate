# pdf-image-assets Specification

## Purpose
TBD - created by archiving change extract-pdf-images-to-assets. Update Purpose after archive.
## Requirements
### Requirement: 从 PDF 提取图片资产
系统 SHALL 能从输入 PDF 中提取图片资源，并将图片保存为稳定、可被重建渲染器读取的本地 asset 文件。

#### Scenario: 提取图片到指定 assets 目录
- **GIVEN** 一个包含至少一张图片的 PDF 和一个输出 assets 目录
- **WHEN** 用户运行图片提取能力
- **THEN** 系统在 assets 目录中创建至少一个图片文件，且文件大小大于 `0`

#### Scenario: 图片文件名与 LayoutConfig image block ID 对齐
- **GIVEN** LayoutConfig 中存在图片块 ID `p2_i1`
- **WHEN** 系统将 PDF 图片资产与该图片块关联
- **THEN** 生成的图片文件名包含 `p2_i1`，并且对应 image block 的 `image.asset_path` 指向该文件

#### Scenario: 图片资产记录 mime_type
- **GIVEN** 系统成功导出一个 PNG 图片资产
- **WHEN** 系统更新 LayoutConfig image 信息
- **THEN** 对应 image block 的 `image.mime_type` 等于 `image/png`

### Requirement: 生成带图片资产引用的 LayoutConfig
系统 SHALL 能读取原始 PDF 和已有 LayoutConfig，输出一个带 `image.asset_path` 的增强版 LayoutConfig JSON。

#### Scenario: CLI 生成增强版 layout JSON
- **GIVEN** 原始 PDF、已有 `.layout.json` 和 assets 输出目录
- **WHEN** 用户运行 `pdftranslate extract-images <input.pdf> --layout <input.layout.json> --output-layout <output.layout.json> --assets-dir <assets-dir>`
- **THEN** 命令成功退出，创建增强版 layout JSON，并创建图片资产目录

#### Scenario: 未匹配到资产的图片块保留原字段
- **GIVEN** LayoutConfig 中存在图片块，但提取器未能找到对应图片资产
- **WHEN** 系统输出增强版 LayoutConfig
- **THEN** 该图片块仍保留原有 `ref`、`width`、`height`、`mime_type` 字段，并且不强制写入 `asset_path`

#### Scenario: 图片资产路径使用相对路径
- **GIVEN** assets 目录位于项目工作目录内
- **WHEN** 系统将图片 asset path 写入 LayoutConfig
- **THEN** `image.asset_path` 是相对路径，而不是绝对路径

### Requirement: 渲染器使用真实图片资产
系统 SHALL 在重建 PDF 时优先使用 image block 的 `image.asset_path` 绘制真实图片；当资产缺失时继续使用占位框。

#### Scenario: render-layout 绘制真实图片资产
- **GIVEN** LayoutConfig 中某个 image block 包含有效 `image.asset_path`
- **WHEN** 用户运行 `pdftranslate render-layout <layout.json> --output <output.pdf>`
- **THEN** 渲染器在该图片块 bbox 中绘制 asset_path 指向的图片，而不是灰色占位框

#### Scenario: asset_path 缺失时保留占位 fallback
- **GIVEN** LayoutConfig 中某个 image block 没有 `image.asset_path`
- **WHEN** 用户运行 `pdftranslate render-layout <layout.json> --output <output.pdf>`
- **THEN** 渲染器继续在该图片块 bbox 中绘制占位框和图片 ID

#### Scenario: 示例 PDF 图片回填可人工检查 <!-- manual-verify -->
- **GIVEN** `assets/1603.08767v1.pdf` 和 `assets/1603.08767v1.layout.json` 存在
- **WHEN** 用户提取图片资产并使用增强版 layout JSON 重建 PDF
- **THEN** 输出 PDF 中 page 2 顶部图片位置出现真实图片内容，而不是灰色占位框

