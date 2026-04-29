# pdf-layout-config Specification

## Purpose
定义 PDF 结构化 layout/config 解析能力：将带文本层 PDF 解析为确定性的 JSON 配置文档，保留后续 AI 翻译和 PDF 回填需要的页面、文本块、图片块、坐标和基础样式线索。
## Requirements
### Requirement: 输出结构化 PDF layout 配置
系统 SHALL 提供一个结构化 layout/config 解析能力，将带文本层 PDF 输出为确定性的 JSON 配置文档。

#### Scenario: 提供 LayoutConfig schema 说明文档
- **GIVEN** 开发者需要实现或消费 layout/config JSON
- **WHEN** 查看本变更的设计产物
- **THEN** 存在 `layout-config-schema.md`，并说明 schema version、坐标系、顶层字段、页面字段、文本块字段、图片块字段、bbox、style、image 和非目标字段

#### Scenario: 解析 PDF 为 JSON 配置文件
- **GIVEN** 一个带文本层的 PDF 输入文件
- **WHEN** 用户运行 layout/config 解析命令并指定 JSON 输出路径
- **THEN** 命令成功退出，并在指定路径创建一个可解析的 JSON 文件

#### Scenario: 配置包含顶层元数据
- **GIVEN** 一个带文本层的 PDF 输入文件
- **WHEN** 系统将其解析为 layout/config
- **THEN** JSON 顶层包含 `schema_version`、`source_file` 和 `pages` 字段

### Requirement: 配置保留页面结构
系统 SHALL 在 layout/config 中保留 PDF 页面顺序和页面尺寸，使后续译文回填可以定位到原页面。

#### Scenario: 页面按原始顺序输出
- **GIVEN** 一个多页 PDF
- **WHEN** 系统将其解析为 layout/config
- **THEN** `pages` 数组按页面升序输出，并且每个页面包含从 `1` 开始的 `page_number`

#### Scenario: 页面包含尺寸信息
- **GIVEN** 一个 PDF 页面具有宽度和高度
- **WHEN** 系统将其解析为 layout/config
- **THEN** 对应页面对象包含数值型 `width` 和 `height` 字段，且二者均大于 `0`

### Requirement: 配置保留文本块定位信息
系统 SHALL 将可提取文本组织为有序文本块，并为每个文本块输出原文、稳定 ID、bbox 坐标和基础样式线索。

#### Scenario: 文本块包含后续翻译所需字段
- **GIVEN** 一个 PDF 页面包含可提取文本
- **WHEN** 系统将其解析为 layout/config
- **THEN** 页面中的每个文本块包含 `id`、`kind`、`page_number`、`text`、`bbox` 和 `style` 字段，且 `kind` 等于 `text`

#### Scenario: 文本块 ID 稳定且可追踪
- **GIVEN** 同一个 PDF 输入文件
- **WHEN** 系统连续两次解析为 layout/config
- **THEN** 两次输出中同一页面同一顺序文本块的 `id` 完全一致，并采用 `p<page>_b<block>` 格式

#### Scenario: bbox 使用数值坐标
- **GIVEN** 一个文本块来自 PDF 页面上的可定位文本
- **WHEN** 系统将其解析为 layout/config
- **THEN** 该文本块的 `bbox` 包含数值型 `x0`、`y0`、`x1`、`y1` 字段，且 `x1` 大于或等于 `x0`，`y1` 大于或等于 `y0`

### Requirement: 配置保留图片块定位信息
系统 SHALL 将 PDF 页面中的图片对象记录为图片块，并为每个图片块输出稳定 ID、bbox 坐标、页面编号、图片尺寸、可追踪引用，以及在资源已提取时可用于重建渲染的图片资产路径。

#### Scenario: 图片块包含后续重建所需字段
- **GIVEN** 一个 PDF 页面包含图片对象
- **WHEN** 系统将其解析为 layout/config
- **THEN** 页面中的每个图片块包含 `id`、`kind`、`page_number`、`bbox` 和 `image` 字段，且 `kind` 等于 `image`

#### Scenario: 图片块 ID 稳定且可追踪
- **GIVEN** 同一个包含图片的 PDF 输入文件
- **WHEN** 系统连续两次解析为 layout/config
- **THEN** 两次输出中同一页面同一顺序图片块的 `id` 完全一致，并采用 `p<page>_i<image>` 格式

#### Scenario: 图片块保留尺寸和引用信息
- **GIVEN** 一个图片块来自 PDF 页面上的图片对象
- **WHEN** 系统将其解析为 layout/config
- **THEN** 该图片块的 `image` 对象包含数值型 `width`、`height` 和字符串型 `ref` 字段，且 `width` 和 `height` 均大于 `0`

#### Scenario: 图片块记录已提取资产路径
- **GIVEN** 一个图片块已成功关联到导出的图片资产
- **WHEN** 系统输出增强版 layout/config
- **THEN** 该图片块的 `image` 对象包含字符串型 `asset_path` 字段，且该路径指向存在的本地图片文件

#### Scenario: 图片资产路径是可选字段
- **GIVEN** 一个图片块尚未关联到导出的图片资产
- **WHEN** 系统输出 layout/config
- **THEN** 该图片块的 `image` 对象可以不包含 `asset_path` 字段，并且仍然符合 LayoutConfig schema

### Requirement: 配置范围保持在解析阶段
系统 SHALL 将本次能力限制在 PDF 结构化解析和 JSON 序列化范围内，不执行 AI 翻译、译文排版回填、图片内容编辑、PDF 重建、扫描版 PDF 或 OCR。

#### Scenario: 不翻译文本块内容
- **GIVEN** 输入 PDF 包含英文文本
- **WHEN** 系统将其解析为 layout/config
- **THEN** 文本块 `text` 字段包含原始英文文本，而不是翻译后的文本

#### Scenario: 不输出译文或重建结果
- **GIVEN** 一个 PDF 输入文件
- **WHEN** 系统将其解析为 layout/config
- **THEN** JSON 不包含 `translated_text`、`target_text`、`rebuilt_pdf`、`edited_image` 或 OCR 结果字段

