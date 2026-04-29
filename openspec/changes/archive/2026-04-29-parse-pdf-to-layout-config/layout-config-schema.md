# LayoutConfig Schema

## Purpose

`LayoutConfig` 是 PDF 结构化解析阶段的 JSON 中间格式。它用于保存后续 AI 翻译和 PDF 回填需要的页面、文本块、图片块、坐标和样式线索；它不是翻译结果，也不是重建后的 PDF 描述。

## Schema Version

- `schema_version`: 固定字符串，第一版为 `"1.0"`。
- schema 发生破坏性变化时必须提升版本。

## Coordinate System

```json
{
  "coordinate_system": {
    "unit": "pt",
    "origin": "bottom-left"
  }
}
```

- `unit`: PDF points，简称 `pt`。
- `origin`: `bottom-left`，表示坐标原点位于页面左下角。
- 所有 `bbox` 字段使用同一坐标系。

## Top-Level Object

```json
{
  "schema_version": "1.0",
  "source_file": "sample.pdf",
  "coordinate_system": {
    "unit": "pt",
    "origin": "bottom-left"
  },
  "pages": []
}
```

- `source_file`: 输入 PDF 文件名或调用方提供的相对源文件标识。
- `pages`: 页面数组，按 `page_number` 升序排列。

## Page Object

```json
{
  "page_number": 1,
  "width": 612.0,
  "height": 792.0,
  "rotation": 0,
  "blocks": [],
  "warnings": []
}
```

- `page_number`: 从 `1` 开始的页码。
- `width`: 页面宽度，单位为 `coordinate_system.unit`。
- `height`: 页面高度，单位为 `coordinate_system.unit`。
- `rotation`: 页面旋转角度。第一版可使用 `0` 作为默认值。
- `blocks`: 页面 layout block 数组。第一版支持 `text` 和 `image`。
- `warnings`: 解析警告数组，用于记录当前阶段未处理但被发现的对象或限制。

## BBox

```json
{
  "x0": 72.0,
  "y0": 100.0,
  "x1": 200.0,
  "y1": 124.0
}
```

- `x0`, `y0`: 左下角坐标。
- `x1`, `y1`: 右上角坐标。
- `x1 >= x0`，`y1 >= y0`。

## Text Block

```json
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
}
```

- `id`: 稳定文本块 ID，格式为 `p<page>_b<block>`。
- `kind`: 固定为 `"text"`。
- `text`: 原始提取文本，不包含译文。
- `style`: 基础样式线索。无法可靠提取时字段保留，值可为 `null`。
- `translatable`: 是否适合进入后续 AI 翻译流程。第一版默认为 `true`。

## Image Block

```json
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
```

- `id`: 稳定图片块 ID，格式为 `p<page>_i<image>`。
- `kind`: 固定为 `"image"`。
- `image.ref`: 可追踪图片引用。第一版可与图片块 ID 相同。
- `image.width`: 图片显示宽度或解析后端可获得的图片宽度。
- `image.height`: 图片显示高度或解析后端可获得的图片高度。
- `image.mime_type`: 图片 MIME 类型；无法可靠提取时为 `null`。

## Non-Goals and Reserved Fields

本阶段不得输出以下字段：

- `translated_text`
- `target_text`
- `rebuilt_pdf`
- `edited_image`
- OCR 结果字段

如果解析器发现暂不支持的对象，应优先写入页面 `warnings`，而不是扩展未定义字段。

## Complete Example

```json
{
  "schema_version": "1.0",
  "source_file": "sample.pdf",
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
