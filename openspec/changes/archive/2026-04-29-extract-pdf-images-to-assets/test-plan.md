## 1. Layout Image Model (auto-test)

### From Spec: 图片块记录已提取资产路径
- **Test:** `ImageInfo` 支持可选 `asset_path` 并能序列化到 JSON。
  - **Setup:** 构造 `ImageInfo(ref="p2_i1", width=100.0, height=80.0, mime_type="image/png", asset_path="assets/extracted/sample/images/p2_i1.png")`。
  - **Action:** 调用 `ImageBlock.to_dict()` 或 `LayoutConfig.to_json()`。
  - **Assert:** 输出 `image.asset_path` 等于给定相对路径，且 `mime_type` 等于 `image/png`。

### From Spec: 图片资产路径是可选字段
- **Test:** 没有 asset_path 的旧 image block 仍可序列化和反序列化。
  - **Setup:** 使用当前不含 `asset_path` 的最小 LayoutConfig fixture。
  - **Action:** 调用 `layout_config_from_dict` 后再 `to_dict()`。
  - **Assert:** image 对象保留 `ref`、`width`、`height`、`mime_type`，且不要求存在 `asset_path`。

## 2. Image Asset Extraction (auto-test)

### From Spec: 提取图片到指定 assets 目录
- **Test:** 图片提取器能把 PDF 中的图片写入指定目录。
  - **Setup:** 构造一个带嵌入 PNG 图片的一页测试 PDF，准备临时 assets 目录。
  - **Action:** 调用 `extract_pdf_image_assets(pdf_path, assets_dir, layout_config)`。
  - **Assert:** assets 目录中存在至少一个图片文件，文件大小大于 `0`。

### From Spec: 图片文件名与 LayoutConfig image block ID 对齐
- **Test:** 提取出的图片文件名包含对应 image block ID，并写回 `image.asset_path`。
  - **Setup:** 构造带一个 image block `p1_i1` 的 LayoutConfig 和一个带图片的测试 PDF。
  - **Action:** 调用图片资产关联函数。
  - **Assert:** 更新后的 LayoutConfig 中 `image.asset_path` 文件名包含 `p1_i1`，并且路径存在。

### From Spec: 图片资产记录 mime_type
- **Test:** PNG 图片资产写回 `mime_type="image/png"`。
  - **Setup:** 构造带 PNG 图片的测试 PDF 和对应 image block。
  - **Action:** 调用图片资产关联函数。
  - **Assert:** 更新后的 image block `image.mime_type == "image/png"`。

### From Spec: 未匹配到资产的图片块保留原字段
- **Test:** 当提取器返回空资产列表时，image block 不强制写入 asset_path。
  - **Setup:** 构造包含 image block 的 LayoutConfig，并用 fake extractor 返回空列表。
  - **Action:** 调用增强 LayoutConfig 函数。
  - **Assert:** 输出 image block 的 `ref`、`width`、`height`、`mime_type` 保持不变，且无 `asset_path` 或值为 `None`。

### From Spec: 图片资产路径使用相对路径
- **Test:** 写入 LayoutConfig 的 asset_path 是相对路径。
  - **Setup:** 使用项目内相对 assets 目录和一个提取成功的图片资产。
  - **Action:** 调用资产路径写回逻辑。
  - **Assert:** `Path(asset_path).is_absolute()` 为 `False`。

## 3. CLI Image Extraction (auto-test)

### From Spec: CLI 生成增强版 layout JSON
- **Test:** `pdftranslate extract-images` 创建增强版 layout JSON 和 assets 目录。
  - **Setup:** 写入带 image block 的 layout fixture，准备一个带图片的测试 PDF。
  - **Action:** 调用 `main(["extract-images", pdf_path, "--layout", layout_path, "--output-layout", output_layout, "--assets-dir", assets_dir])`。
  - **Assert:** 返回码为 `0`，增强版 layout JSON 存在，assets 目录存在。

### From Spec: CLI 生成增强版 layout JSON
- **Test:** console script 暴露 `extract-images` 命令。
  - **Setup:** 写入带 image block 的 layout fixture，准备一个带图片的测试 PDF。
  - **Action:** 使用 `subprocess.run(["uv", "run", "pdftranslate", "extract-images", ...])`。
  - **Assert:** 返回码为 `0`，增强版 layout JSON 存在。

## 4. Renderer Image Asset Use (auto-test)

### From Spec: render-layout 绘制真实图片资产
- **Test:** renderer 遇到有效 `image.asset_path` 时生成真实图片绘制命令。
  - **Setup:** 构造包含 image block 且 image.asset_path 指向测试 PNG 的 LayoutConfig。
  - **Action:** 调用 `build_render_plan` 或 `render_layout_pdf`。
  - **Assert:** 渲染计划中该 block 的命令类型为真实图片命令，且不再是 `image_placeholder`。

### From Spec: asset_path 缺失时保留占位 fallback
- **Test:** renderer 对缺少 asset_path 的 image block 继续生成占位命令。
  - **Setup:** 使用当前无 asset_path 的 image block fixture。
  - **Action:** 调用 `build_render_plan`。
  - **Assert:** 渲染计划包含 `image_placeholder` 命令。

## 5. Sample PDF Visual Review (manual)

### From Spec: 示例 PDF 图片回填可人工检查
- **Check:** 示例 PDF 提取图片后，重建 PDF 中 page 2 顶部图片从占位框变成真实图片。
  - **Steps:** 运行 `pdftranslate extract-images assets/1603.08767v1.pdf --layout assets/1603.08767v1.layout.json --output-layout output/layout/1603.08767v1.with-images.layout.json --assets-dir output/assets/1603.08767v1/images`；再运行 `pdftranslate render-layout output/layout/1603.08767v1.with-images.layout.json --output output/pdf/1603.08767v1.with-images.rebuilt.pdf --debug-boxes`；打开或渲染 page 2。
  - **Acceptance:** page 2 顶部图片区域出现真实图像内容；若仍为占位框，记录匹配失败原因。
