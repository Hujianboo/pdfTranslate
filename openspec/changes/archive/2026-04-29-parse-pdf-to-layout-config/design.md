## Context

项目当前已经有第一阶段能力：`pdftranslate extract <input.pdf> --output <output.md>` 可以用 PDFium 从带文本层 PDF 提取文本并输出 Markdown。这个 Markdown 输出适合人工检查，但正式走向“AI 翻译后还原原样 PDF”时，需要一个能保存页面尺寸、文本块坐标、图片块坐标、稳定 ID 和样式线索的结构化中间层。

这次变更新增 layout/config 输出，不替代现有 Markdown 提取。Markdown 继续作为调试和验收输出；layout/config 作为后续翻译和回填流程的基础数据。解析后端改为 Docling-first：让 Docling 负责 PDF 文档理解，再由项目自己的 adapter 转换为稳定的 `LayoutConfig`。

## Goals / Non-Goals

**Goals:**

- 新增 `layout-config-schema.md`，作为 LayoutConfig 的单独 schema 说明和实现契约。
- 引入 Docling，将 PDF 解析为 `DoclingDocument`。
- 新增 `DoclingDocument -> LayoutConfig` adapter。
- 为页面输出 `page_number`、`width`、`height` 和有序 layout blocks。
- 为文本块输出稳定 ID、原文、bbox 坐标和基础 style 信息。
- 为图片块输出稳定 ID、bbox 坐标、图片尺寸和可追踪引用信息。
- 提供 `pdftranslate parse-layout <input.pdf> --output <output.json>` CLI 命令。
- 让配置模型、Docling adapter 和 JSON 序列化可以通过自动化测试验证。
- 保持当前 Markdown CLI 和既有测试不回归。

**Non-Goals:**

- AI 翻译。
- 译文换行、缩放、溢出处理或排版回填。
- 生成或重建 PDF。
- OCR、扫描版 PDF、纯图片 PDF；本阶段默认关闭 Docling OCR。
- 图片内容编辑、图片 OCR 或图片语义理解。
- 直接暴露 DoclingDocument 作为业务层长期格式。

## Decisions

1. 将 layout/config 定义为独立 IR，而不是扩展 Markdown 或直接暴露 DoclingDocument。

   理由：Markdown 的优势是可读，但不适合保存坐标、页面尺寸、块 ID 和样式线索。DoclingDocument 很强，但它是外部库的数据模型，项目后续的 AI 翻译、回填、测试和版本迁移需要自己的稳定契约。`LayoutConfig` 是业务边界，Docling 是解析后端。

   备选方案：直接把 Docling JSON 作为后续管线输入。这样短期最快，但后续一旦 Docling schema 变化，或者我们需要为 PDF 回填补充自定义字段，影响面会更大。

2. 将 `layout-config-schema.md` 作为 schema 契约。

   理由：LayoutConfig 会被解析器、CLI、测试、后续 AI 翻译层和 PDF 回填层共同消费，不能只靠代码里的隐含约定。变更目录中必须新增 `layout-config-schema.md`，集中说明 schema version、坐标系、顶层字段、page、block、text block、image block、bbox、style、image、非目标字段和完整 JSON 示例。实现和测试都以这份文档为契约。

   备选方案：只把 schema 写在 `design.md` 或代码注释里。这样短期省事，但后续多模块协作时容易出现字段理解不一致。

3. 使用 Docling 作为第一版 layout 解析后端。

   理由：Docling 已经提供 PDF layout、reading order、表格、图片、OCR、Markdown/JSON 导出和 `DoclingDocument` 统一表示。当前阶段如果从 PDFium 自研 layout parser，很容易把时间花在页面对象、图片对象、表格和阅读顺序这些基础能力上。Docling adapter 能更快验证整体路线。

   备选方案：继续用 PDFium 自研 layout parser。它能给我们更低层控制，但工作量和不确定性更大；如果后续发现 Docling 不能满足“原样回填”的关键字段，再针对缺口补 PDFium fallback 更稳。

4. 使用 JSON 作为第一版配置格式。

   理由：JSON 容易被 CLI、测试、AI 调用层和后续工具消费。第一版 schema 固定为：

   ```json
   {
     "schema_version": "1.0",
     "source_file": "sample.pdf",
     "coordinate_system": {"unit": "pt", "origin": "bottom-left"},
     "pages": [
       {
         "page_number": 1,
         "width": 612.0,
         "height": 792.0,
         "rotation": 0,
         "blocks": [
           {
             "id": "p1_b1",
             "kind": "text",
             "page_number": 1,
             "text": "Original text",
             "bbox": {"x0": 72.0, "y0": 100.0, "x1": 200.0, "y1": 124.0},
             "style": {"font_size": 12.0, "font_name": null},
             "translatable": true
           },
           {
             "id": "p1_i1",
             "kind": "image",
             "page_number": 1,
             "bbox": {"x0": 72.0, "y0": 220.0, "x1": 240.0, "y1": 340.0},
             "image": {"ref": "p1_i1", "width": 168.0, "height": 120.0, "mime_type": null}
           }
         ],
         "warnings": []
       }
     ]
   }
   ```

   备选方案：直接导出 Docling JSON。它信息更完整，但不是项目自己的稳定 schema。

5. 新增 `pdftranslate.layout` 模块承载数据模型和序列化。

   理由：`LayoutConfig`、`PageLayout`、`TextBlock`、`ImageBlock`、`BBox`、`TextStyle`、`ImageInfo` 这些对象应当与 Docling 无关，便于用纯内存数据做单元测试。序列化函数只接收模型并输出 dict/JSON。

   备选方案：在 Docling adapter 中直接拼 dict。这样更快，但会把解析、模型、序列化揉在一起，后续改 schema 时风险更大。

6. 新增 `pdftranslate.docling_adapter` 模块承载 Docling 到 LayoutConfig 的转换。

   理由：adapter 是外部库边界。它负责调用 Docling、读取 `DoclingDocument` 的文本/图片/页面结构，并映射到内部模型。这样以后可以增加 `pdfium_adapter` 或其他 parser backend，而不用改 CLI 和后续翻译层。

   备选方案：把 Docling 调用直接写进 CLI。这样最短，但测试困难，也无法复用 adapter。

7. 文本块和图片块 ID 使用页面和块序号生成。

   理由：文本块使用 `p<page>_b<block>`，图片块使用 `p<page>_i<image>`。两者稳定、可读，文本 ID 可用于后续 AI 翻译请求与响应对齐，图片 ID 可用于后续 PDF 重建时关联原图对象。

   备选方案：直接使用 Docling 内部 JSON pointer 或 item ref。它们有溯源价值，但不够贴合项目自己的稳定 ID 格式；可以作为后续 `source_ref` 字段补充。

8. CLI 使用 `parse-layout` 子命令。

   理由：它和现有 `extract` 命令职责清楚区分：`extract` 输出 Markdown，`parse-layout` 输出 JSON layout/config。后续还可以增加 `translate`、`rebuild` 等命令。

   备选方案：给 `extract` 增加 `--format json`。这会让一个命令承担两种语义：调试文本输出和布局 IR 输出。

## Test Strategy

使用 `pytest`，沿用现有测试方式和 PDF fixture 辅助函数。

模块边界：

- `layout-config-schema.md`: 文档契约测试。测试应确认文件存在并覆盖关键字段，避免 LayoutConfig 只存在于代码隐含结构中。
- `pdftranslate.layout`: 纯单元测试。构造内存中的 `LayoutConfig`，断言 `schema_version`、`source_file`、`coordinate_system`、`pages`、`blocks`、文本块、图片块、bbox、style 和 image 信息序列化结果。
- `pdftranslate.docling_adapter`: adapter 测试。优先用真实 Docling 转换确定性 PDF fixture；必要时用小型 fake DoclingDocument 单元测试字段映射。断言页面顺序、文本块字段、图片块字段、bbox 数值关系、稳定 ID 和 OCR 默认关闭策略。
- `pdftranslate.cli`: CLI 测试。直接调用 `main(argv)` 验证 `parse-layout` 写出可解析 JSON；保留现有 `extract` 测试确保 Markdown 路径不回归。
- `tests/test_packaging.py`: 继续用 `uv run pdftranslate ...` 做 console script 冒烟测试。

Mock/stub 策略：

- 不 mock `pdftranslate.layout`，因为它应是纯函数/数据模型。
- 对 Docling adapter 的字段映射可使用 fake document 做快速单元测试；对真实解析路径至少保留一个小 PDF fixture 集成测试。
- CLI 测试可在必要时 stub Docling adapter，但 happy path 应覆盖真实 PDF fixture。

所有规格场景都可自动化断言，不需要视觉或手工验证。

## Risks / Trade-offs

- [Risk] Docling 输出结构和字段可能随版本变化。→ 缓解：锁定依赖版本范围，并通过 `docling_adapter` 隔离外部 schema。
- [Risk] Docling 的坐标系、页面尺寸或 reading order 与后续 PDF 回填预期不完全一致。→ 缓解：adapter 统一转换到 `layout-config-schema.md` 定义的坐标系；发现缺口时在 adapter 内修正或补 fallback。
- [Risk] Docling 依赖比 pypdfium2 更重，首次安装和解析可能更慢。→ 缓解：本阶段先用示例 PDF 做 spike 和基准；若性能不可接受，再评估轻量 PDFium fallback。
- [Risk] 图片对象可能只有引用和结构信息，不能满足未来“原图无损导出”。→ 缓解：第一版只承诺 image block 的位置、尺寸和稳定引用；原图导出放到 PDF 重建阶段评估。
- [Risk] 本阶段关闭 OCR 会让扫描版或纯图片 PDF 的文本块为空。→ 缓解：保持扫描版/OCR 为非目标，后续单独设计 OCR change。
