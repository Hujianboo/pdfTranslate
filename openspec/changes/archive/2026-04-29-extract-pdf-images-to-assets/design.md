## Context

当前项目已经可以从 PDF 生成 `LayoutConfig`，并用 `render-layout` 按页面尺寸、坐标和文本框位置重建 PDF。这个流程验证了“原样重建”的方向，但图片块目前只有 `ref`、尺寸和 bbox，renderer 只能画灰色占位框，导致重建 PDF 的阅读体验明显不完整。

本变更承接现有的重建路线：先把原 PDF 中可提取的真实图片保存为本地资产，再把资产路径写回 `LayoutConfig`，最后让 `render-layout` 在对应 bbox 中绘制真实图片。用户当前不考虑扫描版 PDF，也明确希望先走重建方案，而不是用原 PDF 页面作为背景覆盖翻译文本。

## Goals / Non-Goals

**Goals:**

- 从原 PDF 中提取可用的嵌入图片资源，并保存到用户指定的 assets 目录。
- 将提取出的图片资产与现有 `LayoutConfig` image block 尽量匹配，写入可选 `image.asset_path`。
- 保持 `asset_path` 为兼容性字段：旧 layout JSON 没有该字段时仍能读取、渲染和回退到占位框。
- 新增 CLI 命令，把原 PDF、已有 layout JSON 和输出 assets 目录组合起来，生成带图片引用的增强版 layout JSON。
- 更新 `render-layout`，当图片块存在有效 `asset_path` 时绘制真实图片，否则继续绘制现有占位框。
- 提供自动化测试覆盖模型、提取、匹配、CLI 和 renderer 计划，并保留样例 PDF 的视觉人工验收。

**Non-Goals:**

- 不处理扫描版 PDF/OCR。
- 不接入 AI 翻译，也不翻译图片里的文字。
- 不在本阶段重建表格、公式、矢量图形或复杂路径。
- 不承诺像素级完全一致；本阶段只要求页面尺寸、坐标方向、图片大体位置和阅读体验可接受。
- 不使用原 PDF 页面作为背景来伪装重建结果。

## Decisions

### 1. 使用 PyMuPDF 作为图片提取后端

优先使用 PyMuPDF 的 `page.get_images(full=True)`、`doc.extract_image(xref)` 和 `page.get_image_rects(xref)` 提取图片字节、格式和页面位置。它能同时拿到图片内容和页面矩形，比只遍历 PDF XObject 更适合把资产写回已有 layout block。

备选方案包括 `pypdf` 和 `pypdfium2`。`pypdf` 适合读取对象结构，但图片位置恢复需要额外解析绘制矩阵；`pypdfium2` 已在项目早期抽取流程中使用，但当前代码已经以 Docling 作为 layout 主入口，继续用 PyMuPDF 做资产提取能减少坐标和图像字节处理的不确定性。

### 2. 把图片提取结果先表示为独立中间对象

新增类似 `ExtractedImageAsset` 的内部结构，保存 `page_number`、`bbox`、`mime_type`、`extension`、`bytes` 或 `source_xref`。提取层只负责“PDF 里有什么图片”，不直接修改 layout；匹配层负责“这些图片应该关联到哪个 image block”。

这样可以让匹配逻辑用 fake 数据做单元测试，不需要每个测试都生成真实 PDF，也能把 PyMuPDF 依赖隔离在很薄的一层。

### 3. 明确坐标转换：PyMuPDF top-left -> LayoutConfig bottom-left

`LayoutConfig` 的坐标系统是 pt、左下角原点；PyMuPDF 页面 rect 常用左上角原点。提取图片位置后要按页面高度转换：

```text
layout_x0 = rect.x0
layout_y0 = page_height - rect.y1
layout_x1 = rect.x1
layout_y1 = page_height - rect.y0
```

该转换需要独立纯函数测试，避免图片上下翻转或落到错误页面区域。

### 4. 按页内 bbox 相似度匹配图片资产与 image block

匹配策略按页面分组，只在同一页内比较 extracted image bbox 与 `ImageBlock.bbox`。优先使用 IoU 或中心点距离选择最佳匹配；当 bbox 差异较大但页内数量一致时，可以按从上到下、从左到右的顺序作为 fallback。匹配成功后文件名使用 image block ID，例如 `p2_i1.png`。

这个策略比直接使用 PDF xref 做 `ref` 更稳定，因为现有 layout block 的 ID 已经是 renderer 和调试输出的锚点。xref 可能跨页复用，或同一个图片在页面中出现多次，不适合作为最终文件名。

### 5. `asset_path` 是 `ImageInfo` 的可选字段

在 `ImageInfo` 中新增 `asset_path: str | None = None`。序列化时只在有值时输出，反序列化时通过 `image_data.get("asset_path")` 读取。这样旧 layout JSON 不需要迁移，未匹配到图片的 image block 也不会被迫写入空字段。

CLI 写入的路径使用相对路径，默认相对于当前工作目录计算。这样 layout JSON 更容易在项目内移动和提交，也避免把本机绝对路径写进产物。

### 6. renderer 以 asset 优先，placeholder fallback

`build_render_plan` 对 `ImageBlock` 增加分支：当 `image.asset_path` 存在且文件可读取时生成真实图片绘制命令；否则生成现有 `image_placeholder`。PDF 输出层用 ReportLab `drawImage` 在 bbox 内绘制图片，保持坐标系统不变。

这个 fallback 保留了当前调试体验：当某些 PDF 图片实际是矢量图、mask 或无法匹配的对象时，用户仍能看到占位框和 block ID，便于继续迭代。

### 7. 新增专用 CLI，而不是塞进 `parse-layout`

新增命令：

```bash
pdftranslate extract-images INPUT.pdf \
  --layout INPUT.layout.json \
  --output-layout OUTPUT.with-images.layout.json \
  --assets-dir output/assets/<name>/images
```

把图片提取作为独立步骤，可以复用已经生成的 layout JSON，也方便单独验证“图片回填”这一阶段。后续如果效果稳定，再考虑把它串进一条更高层的 pipeline 命令。

## Test Strategy

使用现有 pytest 测试体系，重点把外部 PDF 库和纯业务逻辑分层。

- 模型层测试 `ImageInfo.asset_path` 的序列化和反序列化，确保旧 JSON 不含 `asset_path` 时仍然兼容。
- 提取层用一个小型测试 PDF 验证 PyMuPDF 能写出真实图片文件、记录 mime type，并返回带 bbox 的中间对象。
- 坐标转换、IoU/中心点匹配、相对路径生成作为纯函数单测，使用 fake `ExtractedImageAsset` 与 fake `LayoutConfig`，不依赖真实 PDF。
- CLI 层通过 `main([...])` 测试参数、输出 layout JSON 和 assets 目录；console script 用较少的集成测试覆盖。
- renderer 层优先测试 `build_render_plan`：有有效 `asset_path` 时生成真实图片命令，缺失或文件不存在时生成 `image_placeholder`。PDF 文件级测试只验证可生成和资源存在，不把视觉判断全部自动化。
- 示例 PDF 用人工视觉验收：先运行 `extract-images`，再运行 `render-layout --debug-boxes`，检查 page 2 的图片区域是否由占位框变为真实图像。

PyMuPDF 相关测试只覆盖最小可控 PDF；复杂论文 PDF 的匹配质量作为手动验收记录，避免自动测试被第三方 PDF 内部结构波动拖得太脆。

## Risks / Trade-offs

- [Risk] 论文里的某些“图片”可能是矢量图、路径、表格或公式，不是可直接提取的 raster image → Mitigation: 未匹配时保留 placeholder，并在后续单独规划表格/公式/矢量图重建。
- [Risk] Docling 的 image block bbox 与 PyMuPDF 的 image rect 不完全一致 → Mitigation: 匹配逻辑使用页内 IoU/中心点距离，并保留顺序 fallback 与人工验收。
- [Risk] 同一个 PDF xref 被多次绘制或跨页复用 → Mitigation: 以页面位置和 image block ID 命名最终资产，而不是直接把 xref 当作唯一图片块。
- [Risk] PDF 图片可能带 mask、透明度或非 RGB 色彩空间 → Mitigation: 优先输出 PyMuPDF 给出的原格式；必要时转换为 PNG，并在测试中至少覆盖 PNG 基础路径。
- [Risk] 真实图片绘制后可能因长宽比和 bbox 差异出现拉伸 → Mitigation: 本阶段先填充 bbox 保证位置正确；后续可以增加 `preserve_aspect_ratio` 或裁切策略。
- [Risk] 相对路径基准不清晰会导致 renderer 找不到图片 → Mitigation: CLI 文档明确 `asset_path` 相对当前工作目录，renderer 同时支持从 layout JSON 所在目录或 cwd 解析的扩展可以作为后续增强。
