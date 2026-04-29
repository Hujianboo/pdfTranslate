# pdfTranslate

一个实验中的 PDF 翻译工具。当前阶段先不做 AI 翻译，而是把普通文本型 PDF 解析成稳定的中间结构 `LayoutConfig`，并逐步验证原样 PDF 重建能力，为后续接入 AI 翻译做准备。

## 当前能力

- `extract`：用 PDFium 提取 PDF 文本并输出 Markdown。
- `parse-layout`：用 Docling 解析 PDF 版面，并输出 JSON 格式的 `LayoutConfig`；当 Docling 检出表格或公式时，会输出 `table` / `formula` block。
- `extract-images`：从原 PDF 提取可用图片资产，并把 `image.asset_path` 写回增强版 `LayoutConfig`。
- `render-layout`：用 `LayoutConfig` 重建 PDF；图片块有有效 `asset_path` 时会回填真实图片，否则保留占位框；表格和公式当前以可调试占位框渲染。
- 默认不处理扫描版 PDF，也不会开启 OCR。
- 目前不会输出译文，也不会处理图片内容编辑。

## 安装依赖

项目使用 `uv` 管理依赖：

```bash
uv sync
```

如果是第一次运行 Docling，它可能会下载模型文件，首轮解析会慢一些。

## 使用方式

### 1. 提取 Markdown 文本

```bash
uv run pdftranslate extract assets/1603.08767v1.pdf --output sample.md
```

输出文件是普通 Markdown，适合快速查看 PDF 里的文本内容。

### 2. 解析 LayoutConfig

```bash
uv run pdftranslate parse-layout assets/1603.08767v1.pdf --output assets/1603.08767v1.layout.json
```

输出文件是 JSON，里面包含页面尺寸、文本块、图片块、表格块、公式块、坐标和基础样式占位信息。后续 AI 翻译阶段会优先消费这个结构，而不是直接消费 Docling 的内部对象。

一个简化后的输出形状如下：

```json
{
  "schema_version": "1.0",
  "source_file": "assets/1603.08767v1.pdf",
  "coordinate_system": {
    "unit": "pt",
    "origin": "bottom-left"
  },
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
          "bbox": {
            "x0": 72.0,
            "y0": 100.0,
            "x1": 200.0,
            "y1": 124.0
          },
          "style": {
            "font_name": null,
            "font_size": null,
            "color": null,
            "rotation": 0
          },
          "translatable": true
        },
        {
          "id": "p1_i1",
          "kind": "image",
          "page_number": 1,
          "bbox": {
            "x0": 72.0,
            "y0": 220.0,
            "x1": 240.0,
            "y1": 340.0
          },
          "image": {
            "ref": "p1_i1",
            "width": 168.0,
            "height": 120.0,
            "mime_type": null,
            "asset_path": "output/assets/1603.08767v1/images/p1_i1.png"
          }
        },
        {
          "id": "p1_t1",
          "kind": "table",
          "page_number": 1,
          "bbox": {
            "x0": 72.0,
            "y0": 300.0,
            "x1": 540.0,
            "y1": 520.0
          },
          "table": {
            "num_rows": 2,
            "num_cols": 2,
            "cells": [
              {
                "text": "Header",
                "row_start": 0,
                "row_end": 1,
                "col_start": 0,
                "col_end": 1,
                "row_span": 1,
                "col_span": 1,
                "column_header": true,
                "row_header": false
              }
            ]
          }
        },
        {
          "id": "p1_f1",
          "kind": "formula",
          "page_number": 1,
          "bbox": {
            "x0": 180.0,
            "y0": 420.0,
            "x1": 432.0,
            "y1": 456.0
          },
          "formula": {
            "text": "E=mc^2",
            "ref": "#/texts/1"
          },
          "translatable": false
        }
      ],
      "warnings": []
    }
  ]
}
```

表格和公式字段约定：

- `kind`: `table` 表示表格块，bbox 覆盖 Docling 识别到的表格区域。
- `table.num_rows` / `table.num_cols` 保存表格行列数。
- `table.cells` 保存单元格文本、行列范围、跨行跨列、表头标记和可选单元格 bbox。
- `kind`: `formula` 表示公式块，默认保护为非普通翻译文本。
- `formula.text` 保存 Docling 提供的公式文本；如果没有可用文本，`formula.ref` 保存来源引用。
- `translatable`: `false` 表示公式块不会被当作普通文本块翻译。

完整字段说明见：

```text
openspec/changes/parse-pdf-to-layout-config/layout-config-schema.md
```

### 3. 提取图片资产并写回 LayoutConfig

`parse-layout` 只负责发现图片块的位置。要让重建 PDF 回填真实图片，需要再运行图片资产提取：

```bash
uv run pdftranslate extract-images assets/1603.08767v1.pdf \
  --layout assets/1603.08767v1.layout.json \
  --output-layout output/layout/1603.08767v1.with-images.layout.json \
  --assets-dir output/assets/1603.08767v1/images
```

这个命令会：

- 从原 PDF 中提取可用的嵌入图片。
- 保存到 `--assets-dir` 指定的目录。
- 尽量按页面和 bbox 与现有 image block 匹配。
- 在增强版 layout JSON 中写入相对路径 `image.asset_path`。

如果某个图片块没有匹配到可提取图片，会保留原有 `ref`、尺寸和 `mime_type`，后续渲染时仍显示占位框。

### 4. 用 LayoutConfig 重建 PDF

```bash
uv run pdftranslate render-layout output/layout/1603.08767v1.with-images.layout.json \
  --output output/pdf/1603.08767v1.with-images.rebuilt.pdf \
  --debug-boxes
```

调试中文样本文本可以加：

```bash
uv run pdftranslate render-layout output/layout/1603.08767v1.with-images.layout.json \
  --output output/pdf/1603.08767v1.with-images.rebuilt.zh.pdf \
  --sample-text zh \
  --debug-boxes
```

当前重建目标是验证页面尺寸、坐标方向、文本块位置、图片大体位置，以及表格/公式占位框是否覆盖正确区域。表格边框、公式排版、矢量图形和复杂排版还没有进入稳定重建阶段。

## 当前设计为什么代码不多

这一步已经改成 Docling-first。也就是说，PDF 解析、版面识别、文本块和图片项发现这些复杂能力主要由 Docling 完成，本项目现在只做几件很关键但很薄的事情：

- 配置 Docling，并默认关闭 OCR。
- 把 DoclingDocument 映射成自己的 `LayoutConfig`。
- 生成稳定 ID，例如 `p1_b1`、`p2_i1`。
- 固定坐标系和 JSON 契约，避免后续翻译、排版、PDF 重建直接依赖 Docling 内部结构。
- 保留旧的 PDFium Markdown 提取命令，方便快速调试文本。

所以代码少不是缺功能，而是把当前阶段的边界收窄了：先拿到可靠的结构化 layout，再继续做 AI 翻译和原样 PDF 回填。

## 当前限制

- 只面向普通文本型 PDF。
- 扫描版 PDF/OCR 暂不支持。
- style 目前只保留字段占位，无法可靠取得的值为 `null`。
- 图片资产提取只覆盖 PDF 中可直接提取的 raster image；矢量图仍可能显示为占位或普通文本块。
- 表格和公式依赖 Docling 的识别结果；当前会进入 `LayoutConfig`，但重建 PDF 时仍以占位框表示，还不会恢复表格边框、公式字体或数学排版细节。
- 还没有接入 AI 翻译；当前 PDF 重建仍是验证性输出，不保证像素级一致。

## 测试

运行完整测试：

```bash
uv run python -m pytest -q
```

当前变更验证过的样例结果：

- `assets/1603.08767v1.pdf` 可解析为 `LayoutConfig`
- 样例输出包含 `12` 页、`214` 个文本块、`3` 个图片块
- 旧 `extract` 命令仍可生成 Markdown
