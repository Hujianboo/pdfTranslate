## Why

当前项目已经能生成带 `translated_text` 的 LayoutConfig，也能用 `render-layout` 做验证性 PDF 重建，但缺少一个面向“翻译完成 layout.json”的正式还原契约。现在需要把这条链路收敛成可测试、可验收的 PDF 输出能力，确保用户拿到翻译后的 layout JSON 后可以稳定生成可打开、页数尺寸正确、译文优先显示的 PDF。

## What Changes

- 明确 `render-layout` 支持将翻译完成的 LayoutConfig JSON 还原为 PDF。
- 增加翻译覆盖校验选项，允许用户要求所有可翻译 text block 都必须包含 `translated_text`。
- 当输入缺少译文且启用严格校验时，CLI 返回非零退出并指出缺失 block。
- 保持译文优先、bbox 内文本适配、图片资产回填、表格/公式占位和页面尺寸一致性。
- 增加端到端验收样例：使用已翻译的 Attention layout 生成最终 PDF 和 debug PDF。

## Capabilities

### New Capabilities

### Modified Capabilities
- `pdf-layout-rendering`: 渲染能力需要正式支持“翻译完成 LayoutConfig 到 PDF”的还原流程，并提供可选的翻译覆盖校验。

## Impact

- 影响 `pdftranslate/cli.py` 的 `render-layout` 参数与错误处理。
- 影响 `pdftranslate/pdf_renderer.py` 或新增辅助模块，用于统计缺失译文的可翻译文本块。
- 更新 renderer/CLI 测试，覆盖严格校验、译文优先、图片回填、页面尺寸和端到端 PDF 输出。
- 更新 README，说明从 translated layout JSON 还原 PDF 的推荐命令。
