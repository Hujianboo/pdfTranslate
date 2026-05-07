# pdfTranslate

<p align="center">
  <img src="plugins/pdftranslate-codex/assets/logo.svg" alt="pdfTranslate logo" width="360">
</p>

<p align="center">
  用 Codex 翻译 PDF，并尽量保留原 PDF 的页面结构、文本位置和图片区域。
</p>

## **安装**

一条命令安装：

```bash
curl -fsSL https://raw.githubusercontent.com/Hujianboo/pdfTranslate/main/scripts/install.sh | bash
```

如果已经 clone 了仓库：

```bash
bash scripts/install.sh
```

安装脚本会自动复用或安装 `uv`，同步 Python 依赖，并添加 `pdfTranslate Codex` 到 Codex plugin marketplace。

安装完成后：

```bash
codex login
```

然后重启 Codex 或重新打开 workspace，启用 `pdfTranslate Codex`。

## **在 Codex 中使用**

直接对 Codex 说：

```text
用 pdfTranslate Codex 翻译当前目录下的 PDF，输出到当前目录。
```

或者：

```text
Use pdfTranslate Codex to translate the PDF in the current directory and save the translated PDF in the current directory.
```

如果需要保留中间文件：

```text
用 pdfTranslate Codex 翻译当前目录下的 PDF，输出到当前目录，并保留中间文件。
```

## **命令行使用**

```bash
uv run python plugins/pdftranslate-codex/scripts/translate_pdf_with_codex.py \
  ./paper.pdf \
  --output-dir . \
  --target-language zh
```

指定完整输出路径：

```bash
uv run python plugins/pdftranslate-codex/scripts/translate_pdf_with_codex.py \
  ./paper.pdf \
  --output ./translated/paper.zh.pdf
```

保留 translated layout：

```bash
uv run python plugins/pdftranslate-codex/scripts/translate_pdf_with_codex.py \
  ./paper.pdf \
  --output-dir ./translated/pdf \
  --output-layout ./translated/paper.layout.zh.json
```

## **常用参数**

- `--output <pdf>`：指定完整输出 PDF 路径。
- `--output-dir <dir>`：指定输出目录，默认文件名为 `<pdf-name>.zh.pdf`。
- `--output-layout <json>`：保存翻译后的 layout JSON。
- `--target-language <lang>`：目标语言，默认 `zh`。
- `--work-dir <dir>`：指定中间文件目录。
- `--keep-work-dir`：保留中间文件和日志；默认完成后删除。
- `--no-images`：跳过图片/表格/公式区域截图。
- `--debug-boxes`：输出调试框，方便检查排版。
- `--batch-size` / `--batch-chars`：控制翻译批次大小。
- `--codex-model <model>`：指定 `codex exec` 使用的模型。

## **基础 CLI**

解析 PDF 为 layout：

```bash
uv run pdftranslate parse-layout ./paper.pdf \
  --output ./tmp/layout \
  --assets-dir ./tmp/assets
```

使用 mock 翻译 layout：

```bash
uv run pdftranslate translate-layout ./tmp/layout/paper.layout.json \
  --output ./tmp/layout/paper.layout.zh.json \
  --provider mock
```

从 translated layout 生成 PDF：

```bash
uv run pdftranslate build-pdf ./tmp/layout/paper.layout.zh.json \
  --output-dir ./translated/pdf \
  --allow-missing-translations
```

## **限制**

- 主要面向普通文本型 PDF。
- 扫描版 PDF/OCR 暂不支持。
- 当前不翻译图片、公式和表格内部图片内容。
- PDF 重建不是像素级复刻，复杂论文排版仍可能需要后续优化。

## **测试**

```bash
uv run python -m pytest -q
```
