## 1. Layout Config Schema 文档 (strict TDD)

- [x] 1.1 [RED] 编写失败测试：`layout-config-schema.md` 存在并包含 `schema_version`、`coordinate_system`、`pages`、`blocks`、`text`、`image`、`bbox`、`style` 和非目标字段说明
- [x] 1.2 [GREEN] 创建或更新 `openspec/changes/parse-pdf-to-layout-config/layout-config-schema.md`，定义 LayoutConfig schema、坐标系、字段说明和完整 JSON 示例
- [x] 1.3 [REFACTOR] 确保 `design.md`、spec、test-plan 和 schema 文档中的字段命名保持一致

## 2. Layout Config 模型与序列化 (strict TDD)

- [x] 2.1 [RED] 编写失败测试：内存中的 layout config 序列化后包含 `schema_version`、`source_file`、`coordinate_system` 和 `pages`
- [x] 2.2 [GREEN] 实现 `LayoutConfig`、`PageLayout` 基础模型和顶层 dict/JSON 序列化
- [x] 2.3 [RED] 编写失败测试：文本块序列化后包含 `id`、`kind`、`page_number`、`text`、`bbox`、`style` 和 `translatable`
- [x] 2.4 [GREEN] 实现 `TextBlock`、`BBox`、`TextStyle` 模型和文本块序列化，并为文本块输出 `kind: "text"`
- [x] 2.5 [RED] 编写失败测试：图片块序列化后包含 `id`、`kind`、`page_number`、`bbox` 和 `image`
- [x] 2.6 [GREEN] 实现 `ImageBlock`、`ImageInfo` 模型和图片块序列化，并为图片块输出 `kind: "image"`
- [x] 2.7 [RED] 编写失败测试：layout config JSON 不包含 `translated_text`、`target_text`、`rebuilt_pdf`、`edited_image` 或 OCR 结果字段
- [x] 2.8 [GREEN] 保持 layout config 仅包含解析阶段字段，不加入翻译、图片编辑、OCR 或 PDF 重建字段
- [x] 2.9 [REFACTOR] 保持 `pdftranslate.layout` 为纯数据模型和序列化层，不依赖 Docling、PDFium 或 CLI

## 3. Docling Adapter 解析 (strict TDD)

- [x] 3.1 [RED] 编写失败集成测试：Docling adapter 能将确定性多页 PDF 转成页面按 `page_number` 升序的 LayoutConfig
- [x] 3.2 [GREEN] 添加 Docling 依赖，并实现 `pdftranslate.docling_adapter` 的 PDF 转换入口
- [x] 3.3 [RED] 编写失败集成测试：Docling adapter 输出页面尺寸 `width` 和 `height`，且均为大于 `0` 的数字
- [x] 3.4 [GREEN] 将 Docling 页面尺寸映射到 `PageLayout`
- [x] 3.5 [RED] 编写失败测试：Docling 文本项映射为带 `kind: "text"`、`text`、`bbox`、`style` 的文本块
- [x] 3.6 [GREEN] 实现 Docling 文本项到 `TextBlock` 的映射，并补齐无法取得的 style 字段为 `null`
- [x] 3.7 [RED] 编写失败测试：同一 PDF 连续两次通过 Docling adapter 解析得到稳定的 `p<page>_b<block>` 文本 ID 序列
- [x] 3.8 [GREEN] 实现稳定文本块 ID 生成和确定性文本块顺序
- [x] 3.9 [RED] 编写失败测试：Docling 图片项映射为带 `kind: "image"`、bbox 和 image 信息的图片块
- [x] 3.10 [GREEN] 实现 Docling 图片项到 `ImageBlock` 的映射，并生成图片 ref、width、height 和 mime_type 占位值
- [x] 3.11 [RED] 编写失败测试：同一 PDF 连续两次通过 Docling adapter 解析得到稳定的 `p<page>_i<image>` 图片 ID 序列
- [x] 3.12 [GREEN] 实现稳定图片块 ID 生成和确定性图片块顺序
- [x] 3.13 [RED] 编写失败测试：Docling PDF pipeline 默认关闭 OCR
- [x] 3.14 [GREEN] 配置 Docling PDF 解析选项，使本阶段默认不处理扫描版 PDF/OCR
- [x] 3.15 [REFACTOR] 隔离 Docling 调用、字段映射和 LayoutConfig 生成，避免业务层直接依赖 DoclingDocument

## 4. CLI 与项目接线 (strict TDD)

- [x] 4.1 [RED] 编写失败 CLI 测试：`parse-layout <input.pdf> --output <output.json>` 会创建可解析 JSON 文件
- [x] 4.2 [GREEN] 实现 `pdftranslate parse-layout` 命令并写出 UTF-8 JSON
- [x] 4.3 [RED] 编写失败测试：`parse-layout` 输出 JSON 顶层 schema、页面、文本块和图片块字段符合 `layout-config-schema.md` 契约
- [x] 4.4 [GREEN] 将 CLI 输出接到 Docling adapter 和 layout config 序列化结果
- [x] 4.5 [RED] 编写失败打包冒烟测试：`uv run pdftranslate parse-layout ...` 可生成 JSON 配置
- [x] 4.6 [GREEN] 确保 console script 暴露新命令且现有 `extract` 命令不回归
- [x] 4.7 [REFACTOR] 清理 CLI 命令分支和路径处理，保持 `extract` 与 `parse-layout` 职责分离

## 5. 验证

- [x] 5.1 [VERIFY] 运行完整自动化测试套件，并确认所有测试通过
- [x] 5.2 [VERIFY] 对 `assets/1603.08767v1.pdf` 运行 `pdftranslate parse-layout`，检查生成 JSON 包含页面尺寸、文本块、图片块和 bbox
- [x] 5.3 [VERIFY] 对 `assets/1603.08767v1.pdf` 运行现有 `pdftranslate extract`，确认 Markdown 输出仍然可用
- [x] 5.4 [VERIFY] 检查 `layout-config-schema.md` 与实际 JSON 输出字段一致
- [x] 5.5 [VERIFY] 记录 Docling 解析示例 PDF 的耗时和输出规模，作为后续是否增加 PDFium fallback 的依据
- [x] 5.6 [VERIFY] 运行 `openspec status --change "parse-pdf-to-layout-config"`，确认该变更已准备好进入 apply 阶段

## Verification Notes

- `assets/1603.08767v1.pdf` 通过 `pdftranslate parse-layout` 解析耗时：`real 28.79s`、`user 60.52s`、`sys 5.26s`。
- 生成的 layout JSON 大小：`152433` bytes。
- 输出规模：`12` pages、`217` blocks，其中 `214` text blocks、`3` image blocks。
- 旧 `pdftranslate extract` 对同一 PDF 仍可生成 Markdown，输出大小：`47635` bytes。
