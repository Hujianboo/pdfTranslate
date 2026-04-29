## 1. Text Fit Planning (auto-test)

### From Spec: 译文优先使用中文换行
- **Test:** 构建渲染计划时，中文译文按 bbox 宽度拆成多行。
  - **Setup:** 创建一个带窄 bbox 和 `translated_text="这是第一句。这是第二句。"` 的 `TextBlock`。
  - **Action:** 调用 `build_render_plan(config)`。
  - **Assert:** 生成的文本命令包含多行布局，且每行估算宽度不超过命令宽度。

### From Spec: 原文在没有译文时保持现有渲染路径
- **Test:** 没有译文时仍使用 `text`。
  - **Setup:** 创建一个只有 `text="Original"`、没有 `translated_text` 的 `TextBlock`。
  - **Action:** 调用 `build_render_plan(config)`。
  - **Assert:** 文本命令的绘制内容为 `Original`。

### From Spec: 样本文本仍低于真实译文优先级
- **Test:** 同时存在 `translated_text` 和 `sample_text="zh"` 时优先使用真实译文。
  - **Setup:** 创建一个 `text="Original"`、`translated_text="真实译文"` 的 `TextBlock`。
  - **Action:** 调用 `build_render_plan(config, RenderOptions(sample_text="zh"))`。
  - **Assert:** 文本命令的绘制内容包含 `真实译文`，不包含样本文本。

### From Spec: 高度不足时降低字号
- **Test:** 默认字号放不下多行译文时，fit 结果使用更小字号。
  - **Setup:** 创建一个 bbox 高度较小但宽度可换行的 `TextBlock`，译文需要三行以上。
  - **Action:** 调用 `build_render_plan(config)`。
  - **Assert:** 文本命令的实际字号小于默认字号。

### From Spec: 文本可放入时不低于最小字号
- **Test:** 文本可按默认字号放入时不触发收缩和 overflow。
  - **Setup:** 创建一个 bbox 足够大的 `TextBlock`。
  - **Action:** 调用 `build_render_plan(config)`。
  - **Assert:** 文本命令的实际字号等于默认字号，且 `overflow` 为 `false`。

### From Spec: 极小 bbox 不会生成无效字号
- **Test:** 极端 bbox 仍返回合法字号。
  - **Setup:** 创建一个宽高极小的 `TextBlock`。
  - **Action:** 调用 `build_render_plan(config)`。
  - **Assert:** 文本命令的实际字号大于 `0`，且大于或等于渲染器最小字号常量。

## 2. Overflow Diagnostics (auto-test)

### From Spec: 无法完整放入时标记 overflow
- **Test:** 最小字号仍放不下完整译文时记录 overflow。
  - **Setup:** 创建一个 bbox 很小、译文很长的 `TextBlock`。
  - **Action:** 调用 `build_render_plan(config)`。
  - **Assert:** 文本命令 `overflow` 为 `true`，并可追踪到该 block id。

### From Spec: 可完整放入时不标记 overflow
- **Test:** 可完整绘制的译文不产生 overflow。
  - **Setup:** 创建一个 bbox 足够大的 `TextBlock`。
  - **Action:** 调用 `build_render_plan(config)`。
  - **Assert:** 文本命令 `overflow` 为 `false`。

## 3. Narrow Text Strategy (auto-test)

### From Spec: 过窄文本块保留源文本
- **Test:** 过窄 bbox 不把完整中文译文逐字竖排。
  - **Setup:** 创建一个宽度小于窄块阈值、同时含 `text` 和 `translated_text` 的 `TextBlock`。
  - **Action:** 调用 `build_render_plan(config)`。
  - **Assert:** 文本命令使用源文本或安全截断文本，且不等于完整中文译文逐字拆行结果。

### From Spec: 过窄文本块记录适配原因
- **Test:** 触发窄块策略时记录可断言的 fit reason。
  - **Setup:** 创建一个宽度小于窄块阈值的 `TextBlock`。
  - **Action:** 调用 `build_render_plan(config)`。
  - **Assert:** 文本命令的 fit reason 等于窄块策略对应的确定性值。

## 4. Debug And Sample PDF Review (visual)

### From Spec: debug 模式显示溢出文本块
- **Check:** debug PDF 能帮助定位 overflow 文本块。
  - **How:** 用一个包含 overflow 的测试 LayoutConfig 运行 `pdftranslate render-layout <layout.json> --output <output.pdf> --debug-boxes`，渲染第一页 PNG 后人工查看。
  - **Acceptance:** overflow 文本块所在 bbox 有可见边框或标记，人工能定位问题区域。

### From Spec: Attention 示例译文重建可人工检查
- **Check:** Attention 中文译文 PDF 比直接硬塞译文更可读。
  - **How:** 运行 `pdftranslate render-layout output/layout/attention-is-all-you-need.zh.layout.json --output output/pdf/attention-is-all-you-need.zh.fit.pdf --debug-boxes`，渲染至少第一页和正文页 PNG。
  - **Acceptance:** PDF 可打开，页面尺寸保持 `612 x 792 pt`，正文译文不大面积横向溢出页面，过窄区域或放不下区域有可定位诊断。
