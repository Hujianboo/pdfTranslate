## Why

当前项目已经可以把带文本层 PDF 解析为 `LayoutConfig` JSON，但还没有验证这些页面尺寸、bbox 坐标、文本块和图片块是否足够支撑后续 PDF 回填。现在需要先完成一个不依赖 AI 翻译的重建闭环，用已有 layout JSON 生成可阅读的 PDF，验证坐标方向、页面尺寸、文本位置、图片位置、多栏结构、标题和图注是否大体可接受。

## What Changes

- 新增一个从 `LayoutConfig` JSON 渲染 PDF 的能力，输入 `.layout.json`，输出 `.pdf`。
- 支持使用中文样本文本替换原文文本块，用来提前观察目标语言文本在原 bbox 内的可读性和溢出问题。
- 保持页面尺寸、坐标系和 block bbox 映射，验证 bottom-left 坐标是否能直接用于 PDF 绘制。
- 对图片块先绘制占位框和图片 ID，不要求导出或嵌入原始图片二进制。
- 增加 debug 渲染模式，绘制文本框、图片框、block id 和简单标注，辅助判断坐标和版面问题。
- 不接入 AI 翻译，不做扫描版/OCR，不追求像素级原样复制。

## Capabilities

### New Capabilities

- `pdf-layout-rendering`: 从 `LayoutConfig` JSON 重建可阅读 PDF，并提供中文样本文本替换和 debug 版面验证能力。

### Modified Capabilities

- 无。

## Impact

- 新增 PDF 渲染模块，用于读取 `LayoutConfig` 并输出 PDF。
- 新增 CLI 命令，例如 `render-layout <input.layout.json> --output <output.pdf>`。
- 可能新增 PDF 生成依赖，优先使用 `reportlab`。
- 新增自动化测试覆盖页面尺寸、坐标方向、文本定位、图片占位、中文样本文本和 CLI 输出。
- 后续 AI 翻译和原样 PDF 回填将基于本次重建结果判断 `LayoutConfig` 是否需要补充更细粒度字段。
