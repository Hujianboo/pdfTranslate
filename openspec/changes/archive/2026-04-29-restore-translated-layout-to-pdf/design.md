## Context

项目已经具备 `parse-layout`、`extract-images`、`translate-layout` 和 `render-layout` 四段基础链路。当前 `render-layout` 可以绘制 `translated_text`、回填图片资产，并对译文做 bbox 内换行和缩字号，但用户仍缺少一个清晰的“翻译完成 layout.json 还原为 PDF”的正式使用契约，尤其是如何确认 layout 是否真的翻译完成。

本次设计不新增独立命令，而是在现有 `render-layout` 上补齐严格翻译覆盖校验，并把 translated layout 到 PDF 的端到端路径固化为测试和文档。

## Goals / Non-Goals

**Goals:**
- 让 `render-layout` 明确支持翻译完成 LayoutConfig JSON 到 PDF 的还原流程。
- 增加 `--require-translations`，用于要求所有可翻译文本块都包含非空 `translated_text`。
- 缺少译文时输出明确错误，包含缺失 block id，并避免创建不完整输出。
- 保持现有译文优先、文本 fit、图片回填、表格/公式占位和页面尺寸一致性。
- 提供 Attention 已翻译 layout 的最终 PDF 和 debug PDF 验收路径。

**Non-Goals:**
- 不改变翻译 provider、不重新翻译文本、不读取 `.env`。
- 不引入新的 `restore-pdf` 命令；避免和 `render-layout` 重复。
- 不实现 BabelDOC 级别段落重排、跨页续排、表格真实重绘或公式排版。
- 不改变 LayoutConfig schema。

## Decisions

### Decision 1: 复用 `render-layout` 作为还原入口

翻译完成 layout 仍然是 LayoutConfig，因此使用现有命令：

```bash
pdftranslate render-layout <translated.layout.json> --output <output.pdf>
```

原因：避免多一个语义重叠命令；用户已经通过 `render-layout` 做重建和 debug，翻译版 PDF 只是同一渲染器的更严格输入模式。

备选方案：新增 `restore-pdf` 或 `render-translated-layout`。这些名称更直观，但会制造两套 CLI 入口和重复测试。

### Decision 2: 通过 `--require-translations` 表达“翻译完成”

默认模式保持宽松：缺少译文时沿用现有回退规则。严格模式新增：

```bash
pdftranslate render-layout <layout.json> --output <output.pdf> --require-translations
```

严格模式检查所有 `TextBlock` 中 `translatable=true` 的块；若 `translated_text` 为空或缺失，则失败并报告 block id。

原因：真实流程中既需要调试半成品 layout，也需要最终导出时防止漏翻。用 flag 可以兼容两种工作方式。

备选方案：默认强制完整译文。这样会破坏现有 sample/debug 用法，不适合当前实验阶段。

### Decision 3: 校验逻辑保持纯函数

新增可测试 helper，例如 `missing_translations_for_layout(config) -> list[str]`。CLI 只负责调用 helper、打印错误和决定是否继续渲染。

原因：测试计划需要同时覆盖 helper 行为和 CLI 行为。纯函数可以用小 fixture 快速断言，不依赖 PDF 生成。

备选方案：直接在 CLI 中遍历并打印。实现更短，但后续复用和测试会比较别扭。

### Decision 4: 输出失败时不创建 PDF

严格校验失败时，CLI 在调用 `render_layout_pdf` 之前返回错误。因此输出路径不会被创建或覆盖。

原因：用户看到 PDF 文件时应该能相信它满足“翻译完成”前提。

备选方案：生成 PDF 同时打印 warning。这对最终导出不够安全。

## Test Strategy

使用现有 `pytest`、`pypdf` 和 CLI 测试工具。

自动测试：
- 在 `tests/test_pdf_renderer.py` 中验证 translated layout 到 PDF 的核心渲染行为：页数、尺寸、译文优先、图片 XObject、表格/公式占位。
- 在 renderer 或独立 helper 测试中验证缺失译文 block id 统计。
- 在 `tests/test_cli.py` 中验证 `--require-translations` 的成功、失败和默认非严格模式。

视觉验收：
- 使用 `output/layout/attention-is-all-you-need.zh.layout.json` 生成 `output/pdf/attention-is-all-you-need.zh.final.pdf`。
- 使用相同输入加 `--debug-boxes` 生成 debug PDF，并渲染第一页和正文页 PNG。
- 人工确认 PDF 可打开、中文译文显示、页面尺寸一致，debug 标记能定位仍需后续优化的区域。

不需要 mock 外部服务；本 change 不调用翻译接口。

## Risks / Trade-offs

- [Risk] `--require-translations` 只能检查 text block 是否有译文，不能判断译文质量 → Mitigation: 本阶段只做结构完整性校验，质量评估留给后续人工或模型评估。
- [Risk] 有些块本来不该翻译但被标记为 `translatable=true` → Mitigation: 用户可以修正 LayoutConfig 或后续增加 block 分类策略；严格模式按现有 schema 执行。
- [Risk] 默认非严格模式仍可能生成半翻译 PDF → Mitigation: README 明确最终导出推荐使用 `--require-translations`。
- [Risk] 现有渲染器仍不是段落级重排 → Mitigation: 本 change 聚焦“可稳定还原”，后续再做 paragraph merging 和 column-aware layout。
