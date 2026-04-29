## Why

Markdown 适合快速检查提取文本，但不适合作为“AI 翻译后还原原样 PDF”的核心中间格式。与其从 PDFium 低层 API 自研完整 layout parser，不如基于 Docling 的文档理解能力先产出稳定的 `LayoutConfig`，把精力放在后续翻译映射和 PDF 回填的产品核心上。

## What Changes

- 新增一个 PDF layout/config 解析能力，输出机器可读的结构化配置。
- 引入 Docling 作为主要 PDF 解析后端，将 PDF 转换为 `DoclingDocument`，再映射为项目自己的 `LayoutConfig`。
- 保留 `LayoutConfig` 作为内部稳定契约，不把业务逻辑直接绑定到 Docling 的原始数据结构。
- 为每个页面输出有序 layout blocks，包含文本块和图片块。
- 文本块包含稳定 ID、原文、bbox 坐标、页面编号，以及可获得的字号/字体等样式线索。
- 图片块包含稳定 ID、bbox 坐标、页面编号、图片尺寸和可追踪引用信息，为后续原样 PDF 重建保留非文本内容位置。
- 提供 CLI 命令将 PDF 解析为 JSON 配置文件，作为 Markdown 之外的结构化中间产物。
- 保持当前 Markdown 提取能力不变；Markdown 仍用于人工检查，不承担版式还原职责。
- 暂不实现 AI 翻译、译文排版回填、图片内容编辑、图片 OCR、PDF 重建、扫描版 PDF 或 OCR；Docling 的 OCR 能力本阶段默认关闭。

## Capabilities

### New Capabilities
- `pdf-layout-config`: 基于 Docling 将带文本层 PDF 解析为包含文本块和图片块的结构化 layout/config，供后续 AI 翻译和原样 PDF 还原流程使用。

### Modified Capabilities

无。

## Impact

- 新增 PDF layout/config 数据模型和 JSON 序列化逻辑。
- 新增 Docling adapter，将 `DoclingDocument` 映射到 `LayoutConfig`。
- 新增 Docling 依赖，并配置 PDF 解析时默认不启用 OCR。
- 扩展 CLI，新增结构化配置输出命令。
- 新增测试覆盖 schema 文档、Docling adapter、页面/文本块/图片块顺序、坐标字段、稳定 ID、CLI 输出和非目标范围。
