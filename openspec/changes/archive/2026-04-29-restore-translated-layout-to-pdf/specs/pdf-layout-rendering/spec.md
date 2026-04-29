## ADDED Requirements

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
