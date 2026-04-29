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
系统 SHALL 按 `LayoutConfig.coordinate_system.origin = "bottom-left"` 解释 bbox，并将文本块、图片块、表格块和公式块绘制在对应页面位置。

#### Scenario: 文本块使用 bbox 左下角定位
- **GIVEN** 一个文本块 bbox 为 `{"x0": 72.0, "y0": 120.0, "x1": 180.0, "y1": 144.0}`
- **WHEN** 系统将该文本块渲染到 PDF
- **THEN** 渲染器在该页面以 `x=72.0`、`y=120.0` 作为文本绘制区域的左下定位基准

#### Scenario: 图片块使用 bbox 绘制占位区域
- **GIVEN** 一个图片块 bbox 为 `{"x0": 200.0, "y0": 240.0, "x1": 300.0, "y1": 340.0}`
- **WHEN** 系统将该图片块渲染到 PDF
- **THEN** 渲染器绘制的图片占位区域宽度为 `100.0`，高度为 `100.0`，左下角为 `(200.0, 240.0)`

#### Scenario: 表格块使用 bbox 绘制占位区域
- **GIVEN** 一个表格块 bbox 为 `{"x0": 72.0, "y0": 300.0, "x1": 540.0, "y1": 520.0}`
- **WHEN** 系统将该表格块渲染到 PDF
- **THEN** 渲染计划包含一个 `table_placeholder` 命令，其 `x=72.0`、`y=300.0`、`width=468.0`、`height=220.0`

#### Scenario: 公式块使用 bbox 绘制占位区域
- **GIVEN** 一个公式块 bbox 为 `{"x0": 180.0, "y0": 420.0, "x1": 432.0, "y1": 456.0}`
- **WHEN** 系统将该公式块渲染到 PDF
- **THEN** 渲染计划包含一个 `formula_placeholder` 命令，其 `x=180.0`、`y=420.0`、`width=252.0`、`height=36.0`

#### Scenario: 调试模式绘制 block 边框和 ID
- **GIVEN** 一个包含文本块、图片块、表格块和公式块的 `LayoutConfig`
- **WHEN** 用户运行 `pdftranslate render-layout <input.layout.json> --output <output.pdf> --debug-boxes`
- **THEN** 渲染器为每个 block 绘制 bbox 边框，并绘制该 block 的 `id` 标注

### Requirement: 支持中文样本文本重建
系统 SHALL 提供中文样本文本模式，用固定中文内容替换没有真实译文的文本块原文，帮助验证目标语言在原 bbox 内的可读性；当 text block 已包含真实译文时，渲染器 SHALL 优先使用该译文。

#### Scenario: 中文样本文本模式替换无译文文本块内容
- **GIVEN** 一个文本块原文为英文且不包含 `translated_text`
- **WHEN** 用户运行 `pdftranslate render-layout <input.layout.json> --output <output.pdf> --sample-text zh`
- **THEN** 渲染器使用中文样本文本绘制该文本块，而不是原始英文文本

#### Scenario: 中文样本文本模式保留文本块数量和 ID
- **GIVEN** 一个包含 `N` 个文本块的 `LayoutConfig`
- **WHEN** 系统使用中文样本文本模式渲染 PDF
- **THEN** 渲染计划中仍包含 `N` 个文本绘制项，并保留原文本块 `id`

#### Scenario: 渲染器优先使用真实译文
- **GIVEN** 一个 text block 包含 `text="Original"` 和 `translated_text="译文"`
- **WHEN** 系统渲染该 layout
- **THEN** 文本绘制命令的内容为 `译文`

#### Scenario: 无译文且无样本文本时使用原文
- **GIVEN** 一个 text block 包含 `text="Original"` 且不包含 `translated_text`
- **WHEN** 系统渲染该 layout 且未启用 `--sample-text`
- **THEN** 文本绘制命令的内容为 `Original`

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

### Requirement: 表格和公式占位渲染
系统 SHALL 在重建 PDF 时识别 table/formula block，并在本阶段用可调试占位绘制表示其位置和类型。

#### Scenario: 表格块绘制带 ID 的占位框
- **GIVEN** LayoutConfig 中存在 ID 为 `p2_t1` 的 table block
- **WHEN** 用户运行 `pdftranslate render-layout <layout.json> --output <output.pdf>`
- **THEN** 渲染器在该表格块 bbox 中绘制表格占位框，并绘制文本 `p2_t1`

#### Scenario: 公式块绘制带 ID 的占位框
- **GIVEN** LayoutConfig 中存在 ID 为 `p3_f1` 的 formula block
- **WHEN** 用户运行 `pdftranslate render-layout <layout.json> --output <output.pdf>`
- **THEN** 渲染器在该公式块 bbox 中绘制公式占位框，并绘制文本 `p3_f1`

#### Scenario: 示例 PDF 表格公式位置可人工检查 <!-- manual-verify -->
- **GIVEN** 一个包含表格或公式的样例 PDF 已解析为增强版 LayoutConfig
- **WHEN** 用户使用 `render-layout --debug-boxes` 重建该 LayoutConfig
- **THEN** 输出 PDF 中 table/formula 占位框大体覆盖原表格和公式区域，且不破坏页面尺寸和坐标方向

### Requirement: 译文文本适配 bbox
系统 SHALL 在渲染 `TextBlock.translated_text` 时，根据文本块 bbox 的宽度和高度计算可绘制行，优先让中文译文在原页面区域内可读，而不是简单按原字符串绘制。

#### Scenario: 译文优先使用中文换行
- **GIVEN** 一个文本块 bbox 宽度只能容纳一行短中文，且 `translated_text` 为 `这是第一句。这是第二句。`
- **WHEN** 系统构建渲染计划
- **THEN** 文本绘制项包含多行布局，且每一行的估算宽度不超过该文本块 bbox 宽度

#### Scenario: 原文在没有译文时保持现有渲染路径
- **GIVEN** 一个文本块没有 `translated_text`
- **WHEN** 系统构建渲染计划
- **THEN** 文本绘制项使用原始 `text` 字段作为绘制内容

#### Scenario: 样本文本仍低于真实译文优先级
- **GIVEN** 一个文本块同时存在 `translated_text`，且用户启用 `--sample-text zh`
- **WHEN** 系统构建渲染计划
- **THEN** 文本绘制项使用 `translated_text`，而不是中文样本文本

### Requirement: 字号和行距自动收缩
系统 SHALL 在译文按默认字号无法放入 bbox 高度时，逐步降低字号和行距，直到文本放入 bbox 或达到最小可读字号。

#### Scenario: 高度不足时降低字号
- **GIVEN** 一个文本块 bbox 高度不足以用默认字号容纳三行中文译文
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项的实际字号小于默认字号

#### Scenario: 文本可放入时不低于最小字号
- **GIVEN** 一个文本块 bbox 足以用默认字号容纳译文
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项的实际字号等于默认字号，且未标记 overflow

#### Scenario: 极小 bbox 不会生成无效字号
- **GIVEN** 一个文本块 bbox 极窄或极矮
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项的实际字号大于 `0`，且不小于渲染器定义的最小字号

### Requirement: 溢出诊断
系统 SHALL 对达到最小字号后仍无法完整放入 bbox 的译文文本块记录确定性的 overflow 诊断，供测试、debug PDF 和人工验收使用。

#### Scenario: 无法完整放入时标记 overflow
- **GIVEN** 一个文本块 bbox 无法在最小字号下容纳完整 `translated_text`
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项标记 `overflow=true`，并记录未能绘制完整文本的 block id

#### Scenario: 可完整放入时不标记 overflow
- **GIVEN** 一个文本块 bbox 可以容纳完整 `translated_text`
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项标记 `overflow=false`

#### Scenario: debug 模式显示溢出文本块 <!-- manual-verify -->
- **GIVEN** 一个包含 overflow 文本块的 LayoutConfig
- **WHEN** 用户运行 `pdftranslate render-layout <layout.json> --output <output.pdf> --debug-boxes`
- **THEN** 输出 PDF 中该文本块的 debug 标记能帮助人工定位发生溢出的区域

### Requirement: 窄文本块保守处理
系统 SHALL 对宽度不足以正常横排中文的文本块采用保守策略，避免把译文挤成不可读的逐字竖排。

#### Scenario: 过窄文本块保留源文本
- **GIVEN** 一个文本块 bbox 宽度小于渲染器定义的窄块阈值，且该文本块包含 `translated_text`
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项使用源文本或安全截断文本，而不是逐字绘制完整中文译文

#### Scenario: 过窄文本块记录适配原因
- **GIVEN** 一个文本块触发窄文本块保守处理
- **WHEN** 系统构建渲染计划
- **THEN** 该文本绘制项记录确定性的 fit reason，说明其未使用完整译文横排

### Requirement: 示例译文 PDF 可读性验收
系统 SHALL 能用已翻译的 LayoutConfig 生成比直接硬塞译文更可读的重建 PDF，作为后续翻译 PDF 工作的人工验收基线。

#### Scenario: Attention 示例译文重建可人工检查 <!-- manual-verify -->
- **GIVEN** `output/layout/attention-is-all-you-need.zh.layout.json` 存在
- **WHEN** 用户运行 `pdftranslate render-layout output/layout/attention-is-all-you-need.zh.layout.json --output output/pdf/attention-is-all-you-need.zh.fit.pdf --debug-boxes`
- **THEN** 输出 PDF 可打开，页面尺寸与 LayoutConfig 一致，正文译文不会大面积横向溢出页面，且 overflow 区域可被定位

### Requirement: 翻译完成 LayoutConfig 还原为 PDF
系统 SHALL 支持从包含 `translated_text` 的 LayoutConfig JSON 生成可打开的翻译版 PDF，并在可翻译文本块存在译文时优先绘制译文。

#### Scenario: CLI 从翻译完成 layout 生成 PDF
- **GIVEN** 一个 LayoutConfig JSON 至少包含一个带 `translated_text` 的可翻译 text block
- **WHEN** 用户运行 `pdftranslate render-layout <translated.layout.json> --output <output.pdf>`
- **THEN** 命令成功退出，并在指定路径创建一个非空 PDF 文件

#### Scenario: 翻译版 PDF 页数和页面尺寸匹配 LayoutConfig
- **GIVEN** 一个翻译完成 LayoutConfig 包含 2 页，页面尺寸均为 `612.0 x 792.0`
- **WHEN** 系统将其还原为 PDF
- **THEN** 输出 PDF 页数为 2，且每页 MediaBox 宽高分别为 `612.0` 和 `792.0`

#### Scenario: 还原时优先绘制译文
- **GIVEN** 一个 text block 包含 `text="Original"` 和 `translated_text="译文"`
- **WHEN** 系统将该 layout 还原为 PDF
- **THEN** 输出 PDF 提取文本包含 `译文`，并且该文本绘制命令使用 `translated_text`

#### Scenario: 图片资产在翻译版 PDF 中回填
- **GIVEN** 一个翻译完成 LayoutConfig 包含 image block，且 `image.asset_path` 指向存在的本地图片文件
- **WHEN** 系统将该 layout 还原为 PDF
- **THEN** 输出 PDF 页面资源中包含图片 XObject

#### Scenario: 表格和公式在翻译版 PDF 中保留占位
- **GIVEN** 一个翻译完成 LayoutConfig 包含 table block 和 formula block
- **WHEN** 系统将该 layout 还原为 PDF
- **THEN** 输出 PDF 文本中包含对应 table block id 和 formula block id 作为可调试占位

### Requirement: 翻译覆盖严格校验
系统 SHALL 提供可选严格校验，使用户能够要求所有 `kind == "text"` 且 `translatable=true` 的文本块都已包含 `translated_text` 后才生成最终 PDF。

#### Scenario: 严格模式下完整译文通过
- **GIVEN** 一个 LayoutConfig 中所有可翻译 text block 都包含非空 `translated_text`
- **WHEN** 用户运行 `pdftranslate render-layout <layout.json> --output <output.pdf> --require-translations`
- **THEN** 命令成功退出并创建输出 PDF

#### Scenario: 严格模式下缺少译文失败
- **GIVEN** 一个 LayoutConfig 中存在 `kind == "text"` 且 `translatable=true` 但没有 `translated_text` 的 block，ID 为 `p1_b2`
- **WHEN** 用户运行 `pdftranslate render-layout <layout.json> --output <output.pdf> --require-translations`
- **THEN** 命令非零退出，不创建输出 PDF，并在 stderr 中包含 `p1_b2`

#### Scenario: 非严格模式允许部分译文
- **GIVEN** 一个 LayoutConfig 中部分可翻译 text block 缺少 `translated_text`
- **WHEN** 用户运行 `pdftranslate render-layout <layout.json> --output <output.pdf>`
- **THEN** 命令成功退出，并对缺少译文的文本块使用现有回退规则绘制

### Requirement: 翻译版 PDF 端到端验收
系统 SHALL 提供一个可重复的端到端验收路径，用已翻译的真实样例 layout 生成翻译版 PDF，便于人工检查可读性和仍然存在的重排缺口。

#### Scenario: Attention 翻译 layout 生成最终 PDF <!-- manual-verify -->
- **GIVEN** `output/layout/attention-is-all-you-need.zh.layout.json` 存在
- **WHEN** 用户运行 `pdftranslate render-layout output/layout/attention-is-all-you-need.zh.layout.json --output output/pdf/attention-is-all-you-need.zh.final.pdf --require-translations`
- **THEN** 输出 PDF 可打开，页数和页面尺寸与 LayoutConfig 一致，正文显示中文译文，图片/表格/公式区域可定位

#### Scenario: Attention 翻译 layout 生成 debug PDF <!-- manual-verify -->
- **GIVEN** `output/layout/attention-is-all-you-need.zh.layout.json` 存在
- **WHEN** 用户运行 `pdftranslate render-layout output/layout/attention-is-all-you-need.zh.layout.json --output output/pdf/attention-is-all-you-need.zh.debug.pdf --require-translations --debug-boxes`
- **THEN** 输出 debug PDF 可打开，并显示 block 边框、ID 和 overflow 标记，便于评估版面还原质量

