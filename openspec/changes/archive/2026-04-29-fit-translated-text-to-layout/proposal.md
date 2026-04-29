## Why

当前 `render-layout` 会把 `translated_text` 直接塞回原始文本块 bbox，中文译文在窄栏、作者区和正文段落中容易溢出、异常换行或变成不可读的竖排。现在已经能生成带中文译文的 `LayoutConfig`，下一步必须让译文在原页面区域内尽量可读，否则无法判断后续翻译 PDF 是否可用。

## What Changes

- 为 `render-layout` 增加译文文本适配能力：根据 bbox 宽度进行中文友好的换行。
- 在文本高度不足时自动降低字号和行距，优先保证译文不明显溢出 bbox。
- 对仍无法放入 bbox 的文本块记录 overflow warning，便于人工和测试定位问题。
- 为过窄文本块提供保守处理策略，避免 arXiv 边栏、邮箱、作者机构等内容被挤成不可读竖排。
- 保持页面尺寸、坐标方向、图片、公式和表格占位渲染行为不变。

## Capabilities

### New Capabilities

### Modified Capabilities
- `pdf-layout-rendering`: 渲染器需要在绘制 `translated_text` 时执行文本适配，输出更可读的重建 PDF，并暴露可验证的溢出信息。

## Impact

- 影响 `pdftranslate/pdf_renderer.py` 中的文本绘制、换行、字号计算和渲染计划。
- 可能需要扩展 `DrawCommand` 或相关内部结构以携带行布局、实际字号和 overflow 信息。
- 影响 `render-layout` 输出 PDF 的视觉结果，但不改变 `LayoutConfig` JSON schema。
- 需要新增或更新 renderer 单元测试，并用已翻译的 `attention-is-all-you-need.zh.layout.json` 做人工验证样例。
