## 1. Markdown 序列化 (strict TDD)

- [x] 1.1 [RED] 编写失败测试：Markdown 序列化器会为内存中的页面记录输出有序的 `## Page N` 标题
- [x] 1.2 [GREEN] 实现 `ExtractedPage` 和带确定性页面标题的 Markdown 序列化
- [x] 1.3 [RED] 编写失败测试：页面文本出现在匹配页面标题下方，并位于下一个页面标题之前
- [x] 1.4 [GREEN] 完成序列化器的空行间距和文本位置行为
- [x] 1.5 [RED] 编写失败测试：序列化器保留源文本，并省略坐标风格的元数据
- [x] 1.6 [GREEN] 保持 Markdown 输出仅包含文本，不做翻译，也不添加版式元数据
- [x] 1.7 [REFACTOR] 保持序列化辅助函数小而独立，不依赖 PDFium 或 CLI 模块

## 2. PDFium 提取 (strict TDD)

- [x] 2.1 [RED] 编写失败集成测试：确定性的多页文本 PDF 会按顺序提取为页面记录
- [x] 2.2 [GREEN] 添加 `pypdfium2` 依赖，并实现基于 PDFium 的页面文本提取
- [x] 2.3 [RED] 编写失败冒烟测试：`assets/1603.08767v1.pdf` 至少能提取出一个非空页面
- [x] 2.4 [GREEN] 支持真实示例 PDF 提取，并在不破坏页面顺序的前提下处理空白页面文本
- [x] 2.5 [REFACTOR] 在 `pdftranslate.extract` 中隔离 PDFium 文档/页面清理和提取错误处理，并保持扫描版 PDF/OCR 不进入本阶段实现范围

## 3. CLI 提取命令 (strict TDD)

- [x] 3.1 [RED] 编写失败 CLI 测试：`extract <input.pdf> --output <output.md>` 会创建非空 Markdown 文件
- [x] 3.2 [GREEN] 实现带显式输入和输出路径的 `pdftranslate extract` 命令
- [x] 3.3 [RED] 编写失败 CLI 测试：输入路径缺失时返回非零状态，报告 `not found`，且不创建输出
- [x] 3.4 [GREEN] 添加输入路径校验，并为缺失 PDF 输出清晰的 stderr 信息
- [x] 3.5 [REFACTOR] 保持 `main.py` 作为围绕包内 CLI 入口的薄兼容包装层

## 4. 项目接线 (strict TDD)

- [x] 4.1 [RED] 为配置好的 CLI 入口编写失败的打包冒烟测试或命令调用测试
- [x] 4.2 [GREEN] 添加包元数据、console script 接线，以及测试套件所需依赖
- [x] 4.3 [REFACTOR] 移除重复的路径处理逻辑，并保持文档和测试中的公开 CLI 名称一致

## 5. 验证

- [x] 5.1 [VERIFY] 运行完整自动化测试套件，并确认所有测试通过
- [x] 5.2 [VERIFY] 对 `assets/1603.08767v1.pdf` 运行提取命令，并检查生成的 Markdown 包含页面标题和非空文本
- [x] 5.3 [VERIFY] 运行 `openspec status --change "extract-pdf-content-to-md"`，确认该变更已准备好进入 apply 阶段
