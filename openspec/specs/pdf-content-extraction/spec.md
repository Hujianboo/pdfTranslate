# pdf-content-extraction Specification

## Purpose
TBD - created by archiving change extract-pdf-content-to-md. Update Purpose after archive.
## Requirements
### Requirement: CLI 将 PDF 内容提取为 Markdown
系统 SHALL 提供一个提取命令，接收 PDF 输入路径，并将提取出的文本内容写入指定的 Markdown 输出路径。

#### Scenario: 将示例 PDF 提取到显式输出路径
- **GIVEN** 示例 PDF 存在于 `assets/1603.08767v1.pdf`
- **WHEN** 用户使用该 PDF 和一个显式 Markdown 输出路径运行提取命令
- **THEN** 命令成功退出，并在指定路径创建一个非空 Markdown 文件

#### Scenario: 拒绝不存在的输入 PDF
- **GIVEN** 请求的输入 PDF 路径不存在
- **WHEN** 用户使用该缺失路径运行提取命令
- **THEN** 命令以非零状态退出，并提示输入文件未找到

### Requirement: Markdown 输出保留页面边界
系统 SHALL 输出带页面标题的确定性 Markdown，使后续翻译和版式还原步骤能够基于页面顺序继续处理。

#### Scenario: 输出有序页面标题
- **GIVEN** 一个多页 PDF
- **WHEN** 用户将其提取为 Markdown
- **THEN** Markdown 按页面升序为每个提取页面包含一个 `## Page N` 标题

#### Scenario: 将提取文本放在对应页面标题下
- **GIVEN** 某个 PDF 页面包含可提取文本
- **WHEN** 用户将 PDF 提取为 Markdown
- **THEN** 该页面文本出现在对应的 `## Page N` 标题之后，并位于下一个页面标题之前

### Requirement: 提取范围仅限文本内容
系统 SHALL 将本次变更限制在带文本层 PDF 的可读文本提取和 Markdown 序列化范围内，不进行文本翻译，也不重建 PDF 版式。本阶段不承诺处理扫描版 PDF、纯图片 PDF 或 OCR。

#### Scenario: 不翻译提取内容
- **GIVEN** 输入 PDF 包含英文文本
- **WHEN** 用户将其提取为 Markdown
- **THEN** Markdown 包含原始提取出的英文文本，而不是翻译后的文本

#### Scenario: 不输出位置版式元数据
- **GIVEN** 输入 PDF 包含有位置排布的文本
- **WHEN** 用户将其提取为 Markdown
- **THEN** Markdown 不包含边界框、坐标或页面版式重建元数据

