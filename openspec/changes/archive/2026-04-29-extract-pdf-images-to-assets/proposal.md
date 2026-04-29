## Why

当前 `LayoutConfig` 只记录图片块的位置、尺寸和 ref，`render-layout` 只能画灰色占位框，无法生成真正可阅读的重建 PDF。为了坚持“重建 PDF”路线，下一步必须从原 PDF 中提取真实图片资源，并让 layout JSON 能引用这些图片文件。

## What Changes

- 新增 PDF 图片资源提取能力：从输入 PDF 中提取可用图片资源，保存到稳定的 assets 目录。
- 为图片资源生成稳定文件名，并尽量与现有 image block ID 关联，例如 `p2_i1.png`。
- 扩展 LayoutConfig 的 image 信息，允许记录 `asset_path` 和更准确的 `mime_type`。
- 新增 CLI 命令，将已有 `.layout.json` 与原 PDF 结合，输出带图片资产引用的新 layout JSON。
- 更新 `render-layout`：当 image block 带有 `asset_path` 时绘制真实图片；缺失时继续绘制占位框。
- 保持本阶段不处理 AI 翻译、扫描版/OCR、图片内容编辑、表格/公式重建。

## Capabilities

### New Capabilities

- `pdf-image-assets`: 从 PDF 提取图片资源，保存为本地 asset 文件，并将资源与 LayoutConfig image block 关联。

### Modified Capabilities

- `pdf-layout-config`: 图片块的 `image` 对象新增可选 `asset_path` 字段，并要求当资源已提取时记录该路径。

## Impact

- 新增图片提取模块，优先使用 PyMuPDF 或可稳定导出图片的 PDF 库。
- 更新 `ImageInfo`、LayoutConfig 序列化和反序列化，支持可选 `asset_path`。
- 更新 renderer，在存在 `asset_path` 时绘制真实图片。
- 新增 CLI 命令，例如 `extract-images <input.pdf> --layout <input.layout.json> --output-layout <output.layout.json> --assets-dir <dir>`。
- 新增测试覆盖 image asset_path 序列化、图片提取计划、CLI 输出、renderer 真图回填和 fallback 占位。
