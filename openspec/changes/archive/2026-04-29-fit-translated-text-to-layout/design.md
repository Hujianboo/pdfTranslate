## Context

`render-layout` 当前会优先使用 `TextBlock.translated_text`，但绘制阶段只用固定字号和简单按字符数截断换行。这个实现能证明坐标方向和 PDF 生成链路可用，却无法处理中文译文长度变化、窄栏、作者区和正文多行段落，导致 Attention 示例中文 PDF 可读性很差。

本次设计聚焦 `pdftranslate/pdf_renderer.py` 内部的文本适配层：在不改变 `LayoutConfig` schema、不重新解析 PDF、不重新翻译文本的前提下，让译文绘制前先经过可测试的 fit 计算。

## Goals / Non-Goals

**Goals:**
- 为 `translated_text` 增加中文友好的换行和 bbox 内适配。
- 在 bbox 高度不足时自动降低字号和行距。
- 在无法完整放入时输出确定性的 overflow 诊断。
- 对过窄文本块采用保守策略，避免生成不可读的逐字竖排。
- 保持图片、公式、表格占位、页面尺寸和 bottom-left 坐标行为不变。

**Non-Goals:**
- 不做全文重排、跨 block 合并、跨页续排或列级重新布局。
- 不修改翻译 provider、`.env`、`translate-layout` 或 `LayoutConfig` JSON schema。
- 不翻译图片、公式和表格内容。
- 不追求与原 PDF 字体、字重、 kerning 或 LaTeX 公式排版完全一致。

## Decisions

### Decision 1: 在 renderer 内部引入纯文本 fit 结果

新增内部数据结构，例如 `TextFitResult`，包含：
- `lines: list[str]`
- `font_size: float`
- `line_height: float`
- `overflow: bool`
- `fit_reason: str`

`DrawCommand` 增加可选字段承载这些结果，`build_render_plan` 负责计算，`_execute_command` 只负责执行绘制。

原因：测试计划需要在不生成 PDF 的情况下断言换行、字号和 overflow。把 fit 计算放进纯函数，可以用现有 pytest 直接测。

备选方案：只在 `_draw_text_in_box` 中动态计算。这个方案更少改动，但测试只能间接检查 PDF 或 mock canvas，不利于 TDD。

### Decision 2: 使用估算宽度实现第一版中文换行

第一版使用确定性字符宽度估算：
- 中文字符按 `font_size` 近似计算。
- ASCII、数字、空格按较窄宽度计算。
- 标点尽量跟随前文，避免行首出现明显孤立标点。

原因：ReportLab CID 字体真实测宽在不同字体和环境下可能更复杂；第一步目标是让译文可读且可测试，不是精确排版。

备选方案：使用 `pdfmetrics.stringWidth` 做真实测宽。后续可以替换为该方案，但当前需要先形成稳定、可断言的 fit 行为。

### Decision 3: 字号从默认值逐步降到最小字号

新增 renderer 常量：
- `DEFAULT_TEXT_FONT_SIZE`
- `MIN_TEXT_FONT_SIZE`
- `LINE_HEIGHT_RATIO`
- `NARROW_TEXT_BLOCK_WIDTH`

fit 流程从默认字号开始，按固定步长递减，重新换行并计算所需高度；若能放入 bbox，则返回成功结果。若达到最小字号仍放不下，则保留能绘制的行数并标记 overflow。

原因：固定步长能保证确定性，方便测试；也能避免中文长段落在小 bbox 中直接溢出页面。

备选方案：二分搜索字号。它更高效，但实现复杂度稍高，且当前文本块数量有限，线性递减足够。

### Decision 4: 过窄文本块不强行使用完整译文

当 bbox 宽度低于阈值时，渲染器采用保守策略：
- 如果源文本是 arXiv 边栏、邮箱、URL、短编号等，优先绘制源文本或安全截断文本。
- 记录 `fit_reason="narrow-block-source-text"` 或等价确定性原因。
- 不把完整中文译文拆成逐字竖排。

原因：原 PDF 中存在旋转边栏、窄作者字段和邮箱字段。强行中文化这些区域的可读性比保留源文本更差。

备选方案：支持旋转文本或逻辑块合并。它们是后续更高阶的版面重建能力，本次先不扩大范围。

### Decision 5: debug 模式暴露 overflow

debug PDF 继续绘制 bbox 和 block id；对 overflow 文本块增加可见标记，例如红色标签后缀、额外小字 `overflow` 或不同颜色边框。

原因：用户需要能快速判断哪里仍然放不下，而不是只看到最终 PDF 效果不好。

备选方案：只在命令行输出 warning。命令行 warning 有用，但不能直接对应页面位置；debug PDF 更适合版面验收。

## Test Strategy

使用现有 `pytest` 测试栈，主要更新 `tests/test_pdf_renderer.py`。

自动测试集中在 `build_render_plan` 和纯 fit 函数：
- 构造小型 `LayoutConfig` fixture，不依赖真实 PDF。
- 断言 `DrawCommand` 中的 `lines`、`font_size`、`overflow` 和 `fit_reason`。
- 保留既有测试：页面尺寸、图片资产、表格/公式占位、`translated_text` 优先级。

PDF 生成层只做轻量集成测试：
- 继续用 `render_layout_pdf` 创建非空 PDF。
- 不把视觉质量作为自动测试断言。

视觉验收使用 Attention 中文 layout：
- 输入 `output/layout/attention-is-all-you-need.zh.layout.json`。
- 输出 `output/pdf/attention-is-all-you-need.zh.fit.pdf`。
- 渲染第一页和正文页 PNG，人工检查正文不再大面积横向溢出，overflow 区域可定位。

不需要 mock 外部服务；本 change 不访问翻译 provider，也不读取 `.env`。

## Risks / Trade-offs

- [Risk] 字符宽度估算不等于真实 PDF 字体测宽 → Mitigation: 先保证不大面积溢出，并保留后续替换为 `pdfmetrics.stringWidth` 的内部边界。
- [Risk] 缩字号会提升放入率但降低阅读舒适度 → Mitigation: 设置最小字号，低于阈值时标记 overflow，而不是无限缩小。
- [Risk] 过窄块保留源文本会让局部内容没有中文化 → Mitigation: 记录 `fit_reason`，这是比不可读竖排更可接受的阶段性结果。
- [Risk] 不做跨 block 合并会限制作者区、摘要区和多栏正文质量 → Mitigation: 本次只解决 block 内 fit，后续再设计逻辑段落合并和列级重排。
- [Risk] debug 标记可能影响最终视觉 → Mitigation: 仅在 `--debug-boxes` 时显示 overflow 视觉标记，普通输出只使用 fit 后文本。
