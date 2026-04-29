## Context

仓库当前只有一个最小化的 `main.py`、空依赖列表，以及位于 `assets/1603.08767v1.pdf` 的示例 PDF。更大的产品方向是构建 PDF 翻译 CLI，但这次变更只做第一个小切片：用 PDFium 从 PDF 中提取可读文本，并写成便于检查的 Markdown。

这个设计需要让“提取”步骤本身可用，同时为后续的翻译和版式还原工作留下扩展空间。

## Goals / Non-Goals

**Goals:**

- 提供一个用于 PDF 到 Markdown 文本提取的 CLI 命令。
- 使用基于 PDFium 的库提取页面文本。
- 生成带页面标题的确定性 Markdown。
- 将提取、序列化和 CLI 解析拆分为可独立测试的单元。
- 在实现前先用自动化测试覆盖目标行为。

**Non-Goals:**

- 翻译提取出的文本。
- 保留或重建原始视觉版式。
- 输出坐标、边界框、字体、图片、表格或其他版式元数据。
- 生成翻译后的 PDF，或生成 Markdown 以外的其他输出格式。
- 处理扫描版或纯图片 PDF 的 OCR。

## Decisions

1. 使用 `pypdfium2` 作为 PDFium 绑定。

   理由：它是 Python 可用的 PDFium 封装，符合“使用 PDFium 做提取”的方向。它也能让第一个切片聚焦在提取本身，而不是引入更高层的 PDF 解析框架。

   备选方案：使用 `pypdf` 做文本提取。它更简单，但不满足 PDFium 的要求，也会让实现偏离预期的底层引擎。

2. 引入一个小的包边界，而不是把所有逻辑都放进 `main.py`。

   理由：新增 `pdftranslate` 包，并包含 `cli.py`、`extract.py`、`markdown.py` 等模块。`main.py` 可以保留为兼容包装层，只负责委托到包内入口。这样 CLI 解析层会很薄，测试也可以直接调用纯函数。

   备选方案：把所有逻辑保留在 `main.py`。这在一开始更快，但会拖慢 TDD，因为测试不得不把参数解析、文件 I/O、PDF 提取和格式化作为一个整体来验证。

3. 将提取结果建模为页面记录。

   理由：提取层返回简单页面对象，例如 `ExtractedPage(page_number: int, text: str)`。Markdown 序列化就可以用构造出来的页面记录直接测试，不需要打开 PDF。后续变更也可以添加更丰富的版式模型，而不必改变本次第一步的 CLI 契约。

   备选方案：直接把 PDFium 输出的原始字符串流式写入文件。这很紧凑，但会隐藏页面边界，也会让 Markdown 页面顺序要求更难测试。

4. 使用显式的 `extract` 子命令。

   理由：类似 `pdftranslate extract <input.pdf> --output <output.md>` 的命令形态，可以给后续 `translate`、`inspect`、`rebuild` 等命令留出空间。命令在尝试 PDFium 提取前，应先验证输入路径是否存在。

   备选方案：做一个总是执行提取的单一命令。它对今天来说足够，但随着后续翻译步骤加入，CLI 的扩展空间会变小。

5. 让 Markdown 保持刻意朴素。

   理由：输出应该稳定，并且容易断言：

   ```markdown
   # <input filename>

   ## Page 1

   <page text>
   ```

   每个后续页面都有自己的 `## Page N` 标题。序列化器应规范化尾随空白，但不能翻译文本，也不能添加版式元数据。

   备选方案：在 Markdown 中嵌入注释或 front matter 来记录提取元数据。这以后可能有用，但会让第一个切片变复杂，也和当前“仅文本”的范围相冲突。

## Test Strategy

使用 `pytest` 编写自动化测试。为了创建确定性的 fixture，可以添加测试依赖，例如小型 PDF 生成辅助库，但不要把这些测试辅助依赖混入运行时提取逻辑。

模块边界：

- `pdftranslate.markdown`: 用内存中的页面记录对 Markdown 序列化做单元测试。无需调用 PDFium，即可覆盖有序标题、页面文本位置和无坐标元数据。
- `pdftranslate.extract`: 使用确定性的文本 PDF fixture 和示例 PDF 冒烟测试，对 PDFium 提取做集成测试。这些测试证明 PDFium 依赖可以打开真实 PDF，并返回非空文本。
- `pdftranslate.cli`: 测试 `main(argv)` 的参数解析、退出码、缺失输入处理和输出文件创建。优先在测试中直接调用 `main(argv)`；只有在新增 console script 后，才用 subprocess 做最后的打包冒烟测试。

Mock/stub 策略：

- 不 mock Markdown 序列化；保持它纯粹且确定。
- 对于聚焦校验和文件写入的 CLI 测试，可以在合适的时候 stub 提取函数，让缺失输入和输出路径行为测试保持快速。
- 对于 PDFium 集成测试，使用真实的 `pypdfium2` 跑 fixture，避免对核心依赖产生虚假的信心。

测试计划中的所有场景都可以自动化测试。本次变更不需要视觉验证或手工设备验证。

## Risks / Trade-offs

- [Risk] 在复杂论文 PDF 中，PDFium 的文本顺序可能不同于视觉阅读顺序。→ 缓解：将本切片定义为“可读文本提取”，以页面边界作为稳定契约，把感知版式的重建放到后续变更。
- [Risk] 扫描版或纯图片 PDF 可能产生空页面文本。→ 缓解：明确 OCR 是非目标，并且本次只测试文本型 PDF。
- [Risk] 新增包结构比直接编辑 `main.py` 多一些工作。→ 缓解：保持模块很小，并保留 `main.py` 作为委托包装层，让仓库仍然容易运行。
- [Risk] 后续版式还原可能需要本次 Markdown 输出中省略的位置数据。→ 缓解：现在保持页面记录简单，后续再通过单独的版式感知产物引入位置数据，而不是让 Markdown 承担过多职责。
