## Why

这个项目需要先把 PDF 翻译 CLI 的第一步打稳：在真正做翻译或版式还原之前，先可靠地从输入 PDF 中提取可读文本。先用 PDFium 把内容提取成 Markdown，可以把范围控制得足够小，同时建立一个可测试、可迭代的基础。

## What Changes

- 新增一个 CLI 流程：接收 PDF 输入路径，并把提取出的内容写入 Markdown 文件。
- 使用基于 PDFium 的提取依赖读取 PDF 页面文本。
- 输出带有页面结构的确定性 Markdown，方便人工检查和自动化测试。
- 使用 `assets/` 目录下现有的示例 PDF 作为冒烟测试样本。
- 本阶段只支持包含可提取文本层的 PDF，暂不考虑扫描版 PDF、纯图片 PDF 或 OCR。
- 暂不实现翻译、复杂版式恢复、位置重建和 PDF 再生成，这些放到后续变更中逐步推进。

## Capabilities

### New Capabilities
- `pdf-content-extraction`: 通过 CLI 将 PDF 页面中的可读内容提取到 Markdown 文档中。

### Modified Capabilities

无。

## Impact

- `main.py` 中的 CLI 入口。
- `pyproject.toml` 中与 PDFium 提取和测试工具相关的项目依赖。
- 新增测试，覆盖 CLI 行为、输出文件生成和错误处理。
- 使用现有示例 PDF `assets/1603.08767v1.pdf` 进行验证。
