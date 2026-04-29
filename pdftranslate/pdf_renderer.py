from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pdftranslate.layout import (
    BBox,
    FormulaBlock,
    ImageBlock,
    LayoutConfig,
    TableBlock,
    TextBlock,
)


ZH_SAMPLE_TEXTS = (
    "这是一段用于验证版面重建的中文样本文本。",
    "中文内容用于观察文本框内的换行和可读性。",
    "当前阶段不接入真实翻译，只检查位置。",
)


@dataclass(frozen=True)
class RenderOptions:
    sample_text: str | None = None
    debug_boxes: bool = False


@dataclass(frozen=True)
class DrawCommand:
    kind: str
    block_id: str
    x: float
    y: float
    width: float
    height: float
    text: str | None = None
    image_ref: str | None = None
    image_path: str | None = None


@dataclass(frozen=True)
class PageRenderPlan:
    page_number: int
    width: float
    height: float
    commands: list[DrawCommand] = field(default_factory=list)


@dataclass(frozen=True)
class RenderPlan:
    pages: list[PageRenderPlan]


def build_render_plan(
    config: LayoutConfig,
    options: RenderOptions | None = None,
) -> RenderPlan:
    options = options or RenderOptions()
    pages = []
    for page in config.pages:
        commands: list[DrawCommand] = []
        for block in page.blocks:
            if isinstance(block, TextBlock):
                commands.append(_text_command(block, options))
                if options.debug_boxes:
                    commands.extend(_debug_commands(block.id, block.bbox))
            elif isinstance(block, ImageBlock):
                commands.append(_image_command(block))
                if options.debug_boxes:
                    commands.extend(_debug_commands(block.id, block.bbox))
            elif isinstance(block, TableBlock):
                commands.append(_table_placeholder_command(block))
                if options.debug_boxes:
                    commands.extend(_debug_commands(block.id, block.bbox))
            elif isinstance(block, FormulaBlock):
                commands.append(_formula_placeholder_command(block))
                if options.debug_boxes:
                    commands.extend(_debug_commands(block.id, block.bbox))
        pages.append(
            PageRenderPlan(
                page_number=page.page_number,
                width=page.width,
                height=page.height,
                commands=commands,
            )
        )
    return RenderPlan(pages=pages)


def render_layout_pdf(
    config: LayoutConfig,
    output_path: str | Path,
    options: RenderOptions | None = None,
) -> None:
    from reportlab.pdfgen import canvas

    plan = build_render_plan(config, options)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    _register_fonts()
    pdf = canvas.Canvas(str(output), pagesize=(1, 1))
    for page in plan.pages:
        pdf.setPageSize((page.width, page.height))
        for command in page.commands:
            _execute_command(pdf, command)
        pdf.showPage()
    pdf.save()


def _execute_command(pdf, command: DrawCommand) -> None:
    from reportlab.lib.colors import black, blue, red

    if command.kind == "text":
        pdf.setFillColor(black)
        pdf.setFont("STSong-Light", _font_size_for(command))
        _draw_text_in_box(pdf, command)
    elif command.kind == "image_asset":
        if command.image_path:
            pdf.drawImage(
                command.image_path,
                command.x,
                command.y,
                width=command.width,
                height=command.height,
                preserveAspectRatio=False,
                mask="auto",
            )
    elif command.kind in {
        "image_placeholder",
        "table_placeholder",
        "formula_placeholder",
    }:
        _draw_placeholder(pdf, command)
    elif command.kind == "debug_box":
        pdf.setStrokeColor(red)
        pdf.rect(command.x, command.y, command.width, command.height, fill=0)
    elif command.kind == "debug_label":
        pdf.setFillColor(blue)
        pdf.setFont("Helvetica", 5)
        pdf.drawString(command.x, command.y + 1, command.text or command.block_id)


def _register_fonts() -> None:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def _font_size_for(command: DrawCommand) -> float:
    return min(10.0, max(5.0, command.height * 0.8))


def _draw_text_in_box(pdf, command: DrawCommand) -> None:
    if not command.text:
        return
    font_size = _font_size_for(command)
    line_height = font_size * 1.15
    y = command.y + command.height - line_height
    for line in _wrap_text(command.text, command.width, font_size):
        if y < command.y:
            break
        pdf.drawString(command.x, y, line)
        y -= line_height


def _wrap_text(text: str, width: float, font_size: float) -> list[str]:
    max_chars = max(int(width / max(font_size * 0.55, 1)), 1)
    return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]


def _text_command(block: TextBlock, options: RenderOptions) -> DrawCommand:
    x, y, width, height = _rect_from_bbox(block.bbox)
    return DrawCommand(
        kind="text",
        block_id=block.id,
        x=x,
        y=y,
        width=width,
        height=height,
        text=_text_for_block(block, options),
    )


def _text_for_block(block: TextBlock, options: RenderOptions) -> str:
    if options.sample_text == "zh":
        index = max(_trailing_number(block.id) - 1, 0)
        return ZH_SAMPLE_TEXTS[index % len(ZH_SAMPLE_TEXTS)]
    return block.text


def _trailing_number(value: str) -> int:
    digits = ""
    for character in reversed(value):
        if not character.isdigit():
            break
        digits = character + digits
    return int(digits) if digits else 1


def _image_placeholder_command(block: ImageBlock) -> DrawCommand:
    return _placeholder_command(
        block_id=block.id,
        bbox=block.bbox,
        kind="image_placeholder",
        text=block.image.ref,
        image_ref=block.image.ref,
    )


def _table_placeholder_command(block: TableBlock) -> DrawCommand:
    return _placeholder_command(
        block_id=block.id,
        bbox=block.bbox,
        kind="table_placeholder",
        text=block.id,
    )


def _formula_placeholder_command(block: FormulaBlock) -> DrawCommand:
    return _placeholder_command(
        block_id=block.id,
        bbox=block.bbox,
        kind="formula_placeholder",
        text=block.id,
    )


def _placeholder_command(
    block_id: str,
    bbox: BBox,
    kind: str,
    text: str | None = None,
    image_ref: str | None = None,
) -> DrawCommand:
    x, y, width, height = _rect_from_bbox(bbox)
    return DrawCommand(
        kind=kind,
        block_id=block_id,
        x=x,
        y=y,
        width=width,
        height=height,
        text=text,
        image_ref=image_ref,
    )


def _image_command(block: ImageBlock) -> DrawCommand:
    if block.image.asset_path and Path(block.image.asset_path).is_file():
        x, y, width, height = _rect_from_bbox(block.bbox)
        return DrawCommand(
            kind="image_asset",
            block_id=block.id,
            x=x,
            y=y,
            width=width,
            height=height,
            image_ref=block.image.ref,
            image_path=block.image.asset_path,
        )
    return _image_placeholder_command(block)


def _debug_commands(block_id: str, bbox: BBox) -> list[DrawCommand]:
    x, y, width, height = _rect_from_bbox(bbox)
    return [
        DrawCommand(
            kind="debug_box",
            block_id=block_id,
            x=x,
            y=y,
            width=width,
            height=height,
        ),
        DrawCommand(
            kind="debug_label",
            block_id=block_id,
            x=x,
            y=bbox.y1,
            width=width,
            height=height,
            text=block_id,
        ),
    ]


def _rect_from_bbox(bbox: BBox) -> tuple[float, float, float, float]:
    return bbox.x0, bbox.y0, bbox.x1 - bbox.x0, bbox.y1 - bbox.y0


def _draw_placeholder(pdf, command: DrawCommand) -> None:
    from reportlab.lib.colors import Color, black, lightgrey

    pdf.setStrokeColor(lightgrey)
    pdf.setFillColor(Color(0.95, 0.95, 0.95))
    pdf.rect(command.x, command.y, command.width, command.height, fill=1)
    pdf.setStrokeColor(lightgrey)
    pdf.line(command.x, command.y, command.x + command.width, command.y + command.height)
    pdf.line(command.x, command.y + command.height, command.x + command.width, command.y)
    pdf.setFillColor(black)
    pdf.setFont("Helvetica", 6)
    pdf.drawString(
        command.x + 2,
        command.y + max(command.height / 2, 8),
        command.text or command.image_ref or command.block_id,
    )
