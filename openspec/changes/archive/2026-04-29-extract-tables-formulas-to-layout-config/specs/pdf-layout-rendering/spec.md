## MODIFIED Requirements

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

## ADDED Requirements

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
