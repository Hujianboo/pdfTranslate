from __future__ import annotations

from dataclasses import dataclass, field
import math
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

DEFAULT_TEXT_FONT_SIZE = 10.0
MIN_TEXT_FONT_SIZE = 5.0
# Max initial guess when inferring from bbox height (no layout font_size).
MAX_SEED_FONT_SIZE = 48.0
LINE_HEIGHT_RATIO = 1.15
FONT_SIZE_STEP = 0.5
NARROW_TEXT_BLOCK_WIDTH = 24.0
PREFERRED_SINGLE_LINE_WIDTH_TOLERANCE = 1.2


@dataclass(frozen=True)
class RenderOptions:
    sample_text: str | None = None
    debug_boxes: bool = False
    asset_base_dir: Path | None = None


@dataclass(frozen=True)
class DrawCommand:
    kind: str
    block_id: str
    x: float
    y: float
    width: float
    height: float
    text: str | None = None
    lines: tuple[str, ...] = ()
    font_size: float | None = None
    line_height: float | None = None
    font_name: str | None = None
    color: str | None = None
    overflow: bool = False
    fit_reason: str = "fit"
    image_ref: str | None = None
    image_path: str | None = None

    def estimate_text_width(self, text: str) -> float:
        return _estimate_text_width(text, _font_size_for(self))


@dataclass(frozen=True)
class TextFitResult:
    lines: tuple[str, ...]
    font_size: float
    line_height: float
    overflow: bool = False
    fit_reason: str = "fit"


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
                command = _text_command(block, options)
                commands.append(command)
                if options.debug_boxes:
                    commands.extend(_debug_commands(block.id, block.bbox))
                    if command.overflow:
                        commands.append(_debug_overflow_label(block.id, block.bbox))
            elif isinstance(block, ImageBlock):
                commands.append(_image_command(block, options))
                if options.debug_boxes:
                    commands.extend(_debug_commands(block.id, block.bbox))
            elif isinstance(block, TableBlock):
                commands.append(_table_command(block, options))
                if options.debug_boxes:
                    commands.extend(_debug_commands(block.id, block.bbox))
            elif isinstance(block, FormulaBlock):
                commands.append(_formula_command(block, options))
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


def missing_translations_for_layout(config: LayoutConfig) -> list[str]:
    missing: list[str] = []
    for page in config.pages:
        for block in page.blocks:
            if (
                isinstance(block, TextBlock)
                and block.translatable
                and not (block.translated_text or "").strip()
            ):
                missing.append(block.id)
    return missing


def _execute_command(pdf, command: DrawCommand) -> None:
    from reportlab.lib.colors import blue, red

    if command.kind == "text":
        pdf.setFillColor(_text_color_for(command))
        pdf.setFont(_reportlab_font_for(command), _font_size_for(command))
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
    elif command.kind == "debug_overflow_label":
        pdf.setFillColor(red)
        pdf.setFont("Helvetica", 5)
        pdf.drawString(command.x, command.y + 1, command.text or command.block_id)


def _register_fonts() -> None:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def _text_color_for(command: DrawCommand):
    from reportlab.lib.colors import HexColor, black

    if command.color:
        try:
            return HexColor(command.color)
        except ValueError:
            return black
    return black


def _reportlab_font_for(command: DrawCommand) -> str:
    if _contains_cjk(command.text or ""):
        return "STSong-Light"

    name = (command.font_name or "").lower()
    is_bold = any(token in name for token in ("bold", "medi", "bd", "black", "demi"))
    is_italic = any(token in name for token in ("italic", "ital", "oblique", "slant"))

    if any(token in name for token in ("courier", "mono", "typewriter")):
        if is_bold and is_italic:
            return "Courier-BoldOblique"
        if is_bold:
            return "Courier-Bold"
        if is_italic:
            return "Courier-Oblique"
        return "Courier"

    if any(token in name for token in ("times", "roman", "serif", "nimbusrom")):
        if is_bold and is_italic:
            return "Times-BoldItalic"
        if is_bold:
            return "Times-Bold"
        if is_italic:
            return "Times-Italic"
        return "Times-Roman"

    if is_bold and is_italic:
        return "Helvetica-BoldOblique"
    if is_bold:
        return "Helvetica-Bold"
    if is_italic:
        return "Helvetica-Oblique"
    return "Helvetica" if command.font_name else "STSong-Light"


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in text)


def _font_size_for(command: DrawCommand) -> float:
    if command.font_size is not None:
        return command.font_size
    return _default_font_size_for_height(command.height)


def _infer_initial_font_size(
    text: str,
    width: float,
    height: float,
    preferred_font_size: float | None,
) -> float:
    box_cap = height / LINE_HEIGHT_RATIO
    if preferred_font_size is not None and preferred_font_size > 0:
        seeded = float(preferred_font_size)
        return max(MIN_TEXT_FONT_SIZE, min(MAX_SEED_FONT_SIZE, seeded))
    glyph_cap = _soft_glyph_budget_pt(text)
    return round(max(MIN_TEXT_FONT_SIZE, min(MAX_SEED_FONT_SIZE, glyph_cap, box_cap)), 2)


def _soft_glyph_budget_pt(text: str) -> float:
    """Rough upper bound from character count — avoids oversized type in tall, sparse boxes."""
    n = len("".join(text.split()))
    if n <= 0:
        return DEFAULT_TEXT_FONT_SIZE
    power = MIN_TEXT_FONT_SIZE + math.pow(float(n), 0.52) * 4.35
    return float(min(MAX_SEED_FONT_SIZE, max(DEFAULT_TEXT_FONT_SIZE, power)))


def _default_font_size_for_height(height: float) -> float:
    return round(
        max(MIN_TEXT_FONT_SIZE, min(MAX_SEED_FONT_SIZE, height / LINE_HEIGHT_RATIO)),
        2,
    )


def _draw_text_in_box(pdf, command: DrawCommand) -> None:
    if not command.text:
        return
    font_size = _font_size_for(command)
    line_height = command.line_height or font_size * LINE_HEIGHT_RATIO
    y = command.y + command.height - line_height
    lines = command.lines or tuple(_wrap_text(command.text, command.width, font_size))
    for line in lines:
        if y < command.y:
            break
        pdf.drawString(command.x, y, line)
        y -= line_height


def _wrap_text(text: str, width: float, font_size: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        current = ""
        for character in paragraph:
            candidate = f"{current}{character}"
            if current and _estimate_text_width(candidate, font_size) > width:
                lines.append(current.rstrip())
                current = "" if character.isspace() else character
            else:
                current = candidate
        if current or not lines:
            lines.append(current.rstrip())
    return lines


def _text_command(block: TextBlock, options: RenderOptions) -> DrawCommand:
    x, y, width, height = _rect_from_bbox(block.bbox)
    text, selection_reason = _text_for_block(block, options, width)
    fit = fit_text_to_box(
        text,
        width,
        height,
        preferred_font_size=block.style.font_size,
    )
    return DrawCommand(
        kind="text",
        block_id=block.id,
        x=x,
        y=y,
        width=width,
        height=height,
        text=text,
        lines=fit.lines,
        font_size=fit.font_size,
        line_height=fit.line_height,
        font_name=block.style.font_name,
        color=block.style.color,
        overflow=fit.overflow,
        fit_reason=selection_reason if selection_reason != "fit" else fit.fit_reason,
    )


def _text_for_block(
    block: TextBlock,
    options: RenderOptions,
    width: float,
) -> tuple[str, str]:
    if block.translated_text:
        if width < NARROW_TEXT_BLOCK_WIDTH:
            return block.text, "narrow-block-source-text"
        return block.translated_text, "fit"
    if options.sample_text == "zh":
        index = max(_trailing_number(block.id) - 1, 0)
        return ZH_SAMPLE_TEXTS[index % len(ZH_SAMPLE_TEXTS)], "fit"
    return block.text, "fit"


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


def _image_command(block: ImageBlock, options: RenderOptions) -> DrawCommand:
    command = _asset_draw_command(
        block_id=block.id,
        bbox=block.bbox,
        asset_path=block.image.asset_path,
        asset_base_dir=options.asset_base_dir,
        image_ref=block.image.ref,
    )
    if command is not None:
        return command
    return _image_placeholder_command(block)


def _table_command(block: TableBlock, options: RenderOptions) -> DrawCommand:
    command = _asset_draw_command(
        block_id=block.id,
        bbox=block.bbox,
        asset_path=block.table.asset_path,
        asset_base_dir=options.asset_base_dir,
    )
    if command is not None:
        return command
    return _table_placeholder_command(block)


def _formula_command(block: FormulaBlock, options: RenderOptions) -> DrawCommand:
    command = _asset_draw_command(
        block_id=block.id,
        bbox=block.bbox,
        asset_path=block.formula.asset_path,
        asset_base_dir=options.asset_base_dir,
    )
    if command is not None:
        return command
    return _formula_placeholder_command(block)


def _asset_draw_command(
    *,
    block_id: str,
    bbox: BBox,
    asset_path: str | None,
    asset_base_dir: Path | None,
    image_ref: str | None = None,
) -> DrawCommand | None:
    resolved_path = _resolve_asset_path(asset_path, asset_base_dir)
    if resolved_path is None:
        return None
    x, y, width, height = _rect_from_bbox(bbox)
    return DrawCommand(
        kind="image_asset",
        block_id=block_id,
        x=x,
        y=y,
        width=width,
        height=height,
        image_ref=image_ref,
        image_path=str(resolved_path),
    )


def _resolve_asset_path(
    asset_path: str | None,
    base_dir: str | Path | None = None,
) -> Path | None:
    if not asset_path:
        return None

    raw_path = Path(asset_path)
    if raw_path.is_absolute():
        return raw_path if raw_path.is_file() else None

    candidates: list[Path] = []
    if base_dir is not None:
        candidates.append(Path(base_dir) / raw_path)
    candidates.append(Path.cwd() / raw_path)
    candidates.append(raw_path)

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file():
            return candidate
    return None


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


def _debug_overflow_label(block_id: str, bbox: BBox) -> DrawCommand:
    x, _, width, height = _rect_from_bbox(bbox)
    return DrawCommand(
        kind="debug_overflow_label",
        block_id=block_id,
        x=x,
        y=bbox.y1 + 6,
        width=width,
        height=height,
        text=f"{block_id} overflow",
    )


def _rect_from_bbox(bbox: BBox) -> tuple[float, float, float, float]:
    return bbox.x0, bbox.y0, bbox.x1 - bbox.x0, bbox.y1 - bbox.y0


def fit_text_to_box(
    text: str,
    width: float,
    height: float,
    preferred_font_size: float | None = None,
) -> TextFitResult:
    font_size = _infer_initial_font_size(text, width, height, preferred_font_size)
    if (
        preferred_font_size is not None
        and "\n" not in text
        and _estimate_text_width(text, font_size)
        <= width * PREFERRED_SINGLE_LINE_WIDTH_TOLERANCE
    ):
        return TextFitResult(
            lines=(text,),
            font_size=font_size,
            line_height=min(font_size * LINE_HEIGHT_RATIO, max(height, MIN_TEXT_FONT_SIZE)),
        )
    last_lines: tuple[str, ...] = tuple(_wrap_text(text, width, font_size))
    while font_size >= MIN_TEXT_FONT_SIZE:
        line_height = font_size * LINE_HEIGHT_RATIO
        lines = tuple(_wrap_text(text, width, font_size))
        if preferred_font_size is not None and len(lines) == 1:
            return TextFitResult(
                lines=lines,
                font_size=font_size,
                line_height=min(line_height, max(height, MIN_TEXT_FONT_SIZE)),
            )
        if len(lines) * line_height <= height:
            return TextFitResult(
                lines=lines,
                font_size=font_size,
                line_height=line_height,
            )
        last_lines = lines
        font_size = round(font_size - FONT_SIZE_STEP, 2)

    min_line_height = MIN_TEXT_FONT_SIZE * LINE_HEIGHT_RATIO
    return TextFitResult(
        lines=last_lines,
        font_size=MIN_TEXT_FONT_SIZE,
        line_height=min_line_height,
        overflow=bool(last_lines)
        and len(last_lines) * min_line_height > max(height, 0.0),
    )


def _estimate_text_width(text: str, font_size: float) -> float:
    return sum(_estimated_character_width(character, font_size) for character in text)


def _estimated_character_width(character: str, font_size: float) -> float:
    if character.isspace():
        return font_size * 0.28
    if "\u4e00" <= character <= "\u9fff":
        return font_size
    if character.isascii():
        return font_size * 0.55
    return font_size


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
