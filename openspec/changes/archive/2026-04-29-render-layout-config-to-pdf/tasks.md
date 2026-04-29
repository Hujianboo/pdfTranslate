## 1. LayoutConfig 读取与测试夹具 (strict TDD)

- [x] 1.1 [RED] 编写失败测试：`layout_config_from_dict` 能从最小 dict 构造包含页面、文本块和图片块的 `LayoutConfig`
- [x] 1.2 [GREEN] 实现 `pdftranslate.layout_io.layout_config_from_dict`
- [x] 1.3 [RED] 编写失败测试：`load_layout_config` 能从 `.layout.json` 路径读取 UTF-8 JSON 并返回 `LayoutConfig`
- [x] 1.4 [GREEN] 实现 `load_layout_config`，并保持 `pdftranslate.layout` 只做纯数据模型
- [x] 1.5 [REFACTOR] 抽取测试用最小 LayoutConfig fixture，供 renderer、CLI 和 packaging 测试复用

## 2. 渲染计划与坐标映射 (strict TDD)

- [x] 2.1 [RED] 编写失败测试：文本块 bbox `x0/y0/x1/y1` 映射为文本绘制命令的 `x/y/width/height`
- [x] 2.2 [GREEN] 实现 `RenderOptions`、`DrawCommand`、`RenderPlan` 和 `build_render_plan` 的文本命令
- [x] 2.3 [RED] 编写失败测试：图片块 bbox 映射为图片占位命令，左下角和宽高保持不变
- [x] 2.4 [GREEN] 实现图片占位绘制命令，保留 image ref 和 block id
- [x] 2.5 [RED] 编写失败测试：`debug_boxes=True` 时每个 block 都生成 bbox 边框和 block id 标注
- [x] 2.6 [GREEN] 实现 debug box 和 debug label 绘制命令
- [x] 2.7 [RED] 编写失败测试：`sample_text="zh"` 时文本命令使用中文样本文本而非原英文
- [x] 2.8 [GREEN] 实现中文样本文本池和替换逻辑，保留原 block id 和文本块数量
- [x] 2.9 [REFACTOR] 将坐标计算、样本文本选择和 debug 命令生成拆成小函数，保持渲染计划层无 ReportLab 依赖

## 3. PDF 写出层 (strict TDD)

- [x] 3.1 [RED] 编写失败测试：渲染包含 2 页的 LayoutConfig 后，输出 PDF 页数为 2
- [x] 3.2 [GREEN] 添加 `reportlab` 运行时依赖和 `pypdf` 测试依赖，实现 `render_layout_pdf`
- [x] 3.3 [RED] 编写失败测试：输出 PDF 第一页 MediaBox 宽高等于 LayoutConfig 的 `width` 和 `height`
- [x] 3.4 [GREEN] 使用 ReportLab 按每页 LayoutConfig 尺寸创建页面，并执行绘制计划
- [x] 3.5 [RED] 编写失败测试：PDF 写出层可以执行中文样本文本和 debug 绘制选项并生成非空 PDF
- [x] 3.6 [GREEN] 注册中文 CID 字体 `STSong-Light`，实现文本绘制、简单 bbox 内换行、图片占位和 debug 标注
- [x] 3.7 [REFACTOR] 隔离 ReportLab canvas 执行逻辑和纯渲染计划逻辑，确保单元测试不依赖 PDF 视觉解析

## 4. CLI 与打包接线 (strict TDD)

- [x] 4.1 [RED] 编写失败 CLI 测试：`pdftranslate render-layout <input.layout.json> --output <output.pdf>` 创建非空 PDF
- [x] 4.2 [GREEN] 在 `pdftranslate.cli` 添加 `render-layout` 子命令并写出 PDF
- [x] 4.3 [RED] 编写失败 CLI 测试：`--sample-text zh` 和 `--debug-boxes` 会传递到 renderer options
- [x] 4.4 [GREEN] 实现 CLI flags：`--sample-text {zh}` 和 `--debug-boxes`
- [x] 4.5 [RED] 编写失败打包冒烟测试：`uv run pdftranslate render-layout ...` 可生成 PDF
- [x] 4.6 [GREEN] 确保 console script 暴露新命令，且现有 `extract`、`parse-layout` 命令不回归
- [x] 4.7 [REFACTOR] 清理 CLI 路径处理和懒加载依赖，避免 `extract`/`parse-layout` 承担 PDF 渲染依赖导入成本

## 5. 示例重建与人工验收 (verification)

- [x] 5.1 [VERIFY] 运行完整自动化测试套件，确认所有测试通过
- [x] 5.2 [VERIFY] 使用 `assets/1603.08767v1.layout.json` 生成普通重建 PDF：`output/pdf/1603.08767v1.rebuilt.pdf`
- [x] 5.3 [VERIFY] 使用 `assets/1603.08767v1.layout.json` 生成中文样本文本 + debug box PDF：`output/pdf/1603.08767v1.rebuilt.debug.zh.pdf`
- [x] 5.4 [VERIFY] 使用 `pypdf` 检查示例重建 PDF 页数为 `12`，第一页尺寸与 LayoutConfig 一致
- [x] 5.5 [VERIFY] 人工打开或渲染前 3 页和含图片页面，检查页面尺寸、坐标方向、文本位置、图片占位、多栏、标题和图注是否大体可接受
- [x] 5.6 [VERIFY] 记录第一版重建质量和明显缺口，包括字体、换行、文本溢出、图片仅占位、表格/公式精度问题
- [x] 5.7 [VERIFY] 确认生成的 `output/` PDF 产物不会被误提交，必要时更新 `.gitignore`
- [x] 5.8 [VERIFY] 运行 `openspec status --change "render-layout-config-to-pdf"`，确认该变更 artifacts 完整且 apply-ready

## Verification Notes

- 自动化测试：`uv run python -m pytest -q` 通过，结果为 `35 passed`。
- 普通重建 PDF：`output/pdf/1603.08767v1.rebuilt.pdf`，约 `55K`。
- 中文样本文本 + debug box PDF：`output/pdf/1603.08767v1.rebuilt.debug.zh.pdf`，约 `22K`。
- `pypdf` 检查：重建 PDF 页数为 `12`，第一页 MediaBox 为 `612.0 x 792.0`，与 LayoutConfig 第一页一致。
- 视觉检查：使用 `pypdfium2` 渲染前 3 页 PNG 到 `tmp/pdfs/`。页面尺寸和 bottom-left 坐标方向正确；文本块大体落在原区域；多栏结构、标题、图注位置大体可识别；page 2 顶部图片占位框位置大体正确。
- 当前明显缺口：图片仅为灰色占位框，没有原始图片内容；文本换行是简单估算，普通重建中部分英文被截断；中文样本文本在窄框和小框里容易溢出或只显示一行；字体、字号、字距、公式和表格还不具备原样精度。
