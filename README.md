# pdfTranslate

一个实验中的 PDF 翻译工具。当前阶段先不做翻译和 PDF 回填，而是把普通文本型 PDF 解析成稳定的中间结构 `LayoutConfig`，为后续接入 AI 翻译和原样 PDF 重建做准备。

## 当前能力

- `extract`：用 PDFium 提取 PDF 文本并输出 Markdown。
- `parse-layout`：用 Docling 解析 PDF 版面，并输出 JSON 格式的 `LayoutConfig`。
- 默认不处理扫描版 PDF，也不会开启 OCR。
- 目前不会输出译文、重建 PDF 或图片编辑结果。

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
uv run pdftranslate parse-layout assets/1603.08767v1.pdf --output layout.json
```

输出文件是 JSON，里面包含页面尺寸、文本块、图片块、坐标和基础样式占位信息。后续 AI 翻译阶段会优先消费这个结构，而不是直接消费 Docling 的内部对象。

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
            "mime_type": null
          }
        }
      ],
      "warnings": []
    }
  ]
}
```

完整字段说明见：

```text
openspec/changes/parse-pdf-to-layout-config/layout-config-schema.md
```

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
- 图片目前记录位置、尺寸和稳定引用，不导出图片二进制。
- 还没有接入 AI 翻译，也没有 PDF 重建输出。

## 测试

运行完整测试：

```bash
uv run python -m pytest -q
```

当前变更验证过的样例结果：

- `assets/1603.08767v1.pdf` 可解析为 `LayoutConfig`
- 样例输出包含 `12` 页、`214` 个文本块、`3` 个图片块
- 旧 `extract` 命令仍可生成 Markdown
