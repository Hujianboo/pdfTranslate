from __future__ import annotations

import ctypes
from dataclasses import replace
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
import pypdfium2 as pdfium

from pdftranslate.layout import (
    BBox,
    FormulaBlock,
    FormulaInfo,
    ImageBlock,
    ImageInfo,
    LayoutConfig,
    PageLayout,
    TableBlock,
    TableCellInfo,
    TableInfo,
    TextBlock,
    TextStyle,
)


def parse_pdf_layout(pdf_path: str | Path) -> LayoutConfig:
    input_path = Path(pdf_path)
    result = build_document_converter().convert(input_path)
    config = _layout_from_docling_document(result.document, source_file=str(input_path))
    print(f"config: {config}")
    return _attach_pdf_text_styles(config, input_path)


def build_pdf_pipeline_options() -> PdfPipelineOptions:
    options = PdfPipelineOptions()
    options.do_ocr = False
    return options


def build_document_converter() -> DocumentConverter:
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=build_pdf_pipeline_options(),
            )
        }
    )


def _layout_from_docling_document(document: Any, source_file: str) -> LayoutConfig:
    pages = [
        PageLayout(
            page_number=int(page_number),
            width=float(page.size.width),
            height=float(page.size.height),
        )
        for page_number, page in _iter_pages(document)
    ]
    pages_by_number = {page.page_number: page for page in pages}

    text_items = []
    for item in getattr(document, "texts", []):
        if _is_formula_item(item):
            continue
        provenance = _first_provenance(item)
        if provenance is None:
            continue

        page_number = int(provenance.page_no)
        if page_number not in pages_by_number:
            continue
        bbox = _bbox_from_provenance(provenance)
        text_items.append((page_number, bbox, item))

    text_counts_by_page: dict[int, int] = {}
    for page_number, bbox, item in sorted(
        text_items,
        key=lambda entry: (entry[0], -entry[1].y1, entry[1].x0),
    ):
        text_counts_by_page[page_number] = text_counts_by_page.get(page_number, 0) + 1
        page = pages_by_number[page_number]
        page.blocks.append(
            TextBlock(
                id=f"p{page_number}_b{text_counts_by_page[page_number]}",
                page_number=page_number,
                text=str(getattr(item, "text", None) or getattr(item, "orig", "")),
                bbox=bbox,
                style=TextStyle(),
            )
        )

    image_items = []
    for item in getattr(document, "pictures", []):
        provenance = _first_provenance(item)
        if provenance is None:
            continue

        page_number = int(provenance.page_no)
        if page_number not in pages_by_number:
            continue

        bbox = _bbox_from_provenance(provenance)
        image_items.append((page_number, bbox))

    image_counts_by_page: dict[int, int] = {}
    for page_number, bbox in sorted(
        image_items,
        key=lambda entry: (entry[0], -entry[1].y1, entry[1].x0),
    ):
        image_counts_by_page[page_number] = image_counts_by_page.get(page_number, 0) + 1
        page = pages_by_number[page_number]
        image_id = f"p{page_number}_i{image_counts_by_page[page_number]}"
        page.blocks.append(
            ImageBlock(
                id=image_id,
                page_number=page_number,
                bbox=bbox,
                image=ImageInfo(
                    ref=image_id,
                    width=bbox.x1 - bbox.x0,
                    height=bbox.y1 - bbox.y0,
                ),
            )
        )

    table_items = []
    for item in getattr(document, "tables", []):
        provenance = _first_provenance(item)
        if provenance is None:
            continue

        page_number = int(provenance.page_no)
        if page_number not in pages_by_number:
            continue

        bbox = _bbox_from_provenance(provenance)
        table_items.append((page_number, bbox, item))

    table_counts_by_page: dict[int, int] = {}
    for page_number, bbox, item in sorted(
        table_items,
        key=lambda entry: (entry[0], -entry[1].y1, entry[1].x0),
    ):
        table_counts_by_page[page_number] = (
            table_counts_by_page.get(page_number, 0) + 1
        )
        page = pages_by_number[page_number]
        table_id = f"p{page_number}_t{table_counts_by_page[page_number]}"
        page.blocks.append(
            TableBlock(
                id=table_id,
                page_number=page_number,
                bbox=bbox,
                table=_table_info_from_item(item),
            )
        )

    formula_items = []
    for item in _iter_formula_items(document):
        provenance = _first_provenance(item)
        if provenance is None:
            continue

        page_number = int(provenance.page_no)
        if page_number not in pages_by_number:
            continue

        bbox = _bbox_from_provenance(provenance)
        formula_items.append((page_number, bbox, item))

    formula_counts_by_page: dict[int, int] = {}
    for page_number, bbox, item in sorted(
        formula_items,
        key=lambda entry: (entry[0], -entry[1].y1, entry[1].x0),
    ):
        formula_counts_by_page[page_number] = (
            formula_counts_by_page.get(page_number, 0) + 1
        )
        page = pages_by_number[page_number]
        formula_id = f"p{page_number}_f{formula_counts_by_page[page_number]}"
        page.blocks.append(
            FormulaBlock(
                id=formula_id,
                page_number=page_number,
                bbox=bbox,
                formula=_formula_info_from_item(item),
            )
        )

    return LayoutConfig(source_file=source_file, pages=pages)


def _iter_pages(document: Any) -> list[tuple[int, Any]]:
    pages = getattr(document, "pages", {})
    if isinstance(pages, dict):
        return sorted((int(page_number), page) for page_number, page in pages.items())

    return sorted(
        (
            int(getattr(page, "page_no", index)),
            page,
        )
        for index, page in enumerate(pages, start=1)
    )


def _first_provenance(item: Any) -> Any | None:
    provenance = getattr(item, "prov", None) or []
    if not provenance:
        return None
    return provenance[0]


def _bbox_from_provenance(provenance: Any) -> BBox:
    bbox = provenance.bbox
    return _bbox_from_docling_bbox(bbox)


def _bbox_from_docling_bbox(bbox: Any) -> BBox:
    return BBox(
        x0=float(bbox.l),
        y0=float(bbox.b),
        x1=float(bbox.r),
        y1=float(bbox.t),
    )


def _table_info_from_item(item: Any) -> TableInfo:
    data = getattr(item, "data", None)
    if data is None:
        return TableInfo(num_rows=0, num_cols=0)

    return TableInfo(
        num_rows=int(getattr(data, "num_rows", 0) or 0),
        num_cols=int(getattr(data, "num_cols", 0) or 0),
        cells=[
            _table_cell_info_from_item(cell)
            for cell in getattr(data, "table_cells", []) or []
        ],
        ref=_optional_str(getattr(item, "self_ref", None)),
    )


def _table_cell_info_from_item(cell: Any) -> TableCellInfo:
    row_start = int(getattr(cell, "start_row_offset_idx", 0) or 0)
    col_start = int(getattr(cell, "start_col_offset_idx", 0) or 0)
    row_span = int(getattr(cell, "row_span", 1) or 1)
    col_span = int(getattr(cell, "col_span", 1) or 1)
    return TableCellInfo(
        text=str(getattr(cell, "text", "") or ""),
        row_start=row_start,
        row_end=int(getattr(cell, "end_row_offset_idx", row_start + row_span) or 0),
        col_start=col_start,
        col_end=int(getattr(cell, "end_col_offset_idx", col_start + col_span) or 0),
        row_span=row_span,
        col_span=col_span,
        column_header=bool(getattr(cell, "column_header", False)),
        row_header=bool(getattr(cell, "row_header", False)),
        bbox=_optional_bbox_from_docling_bbox(getattr(cell, "bbox", None)),
    )


def _iter_formula_items(document: Any) -> list[Any]:
    seen: set[int] = set()
    items = []
    for collection_name in ("formulas", "texts"):
        for item in getattr(document, collection_name, []) or []:
            if id(item) in seen or not _is_formula_item(item):
                continue
            seen.add(id(item))
            items.append(item)
    return items


def _is_formula_item(item: Any) -> bool:
    if item.__class__.__name__ == "FormulaItem":
        return True
    label = str(getattr(item, "label", "")).lower()
    return "formula" in label


def _formula_info_from_item(item: Any) -> FormulaInfo:
    text = _optional_str(getattr(item, "text", None)) or _optional_str(
        getattr(item, "orig", None)
    )
    ref = _optional_str(getattr(item, "self_ref", None))
    return FormulaInfo(text=text, ref=ref)


def _optional_bbox_from_docling_bbox(bbox: Any | None) -> BBox | None:
    if bbox is None:
        return None
    return _bbox_from_docling_bbox(bbox)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _attach_pdf_text_styles(config: LayoutConfig, pdf_path: Path) -> LayoutConfig:
    if not pdf_path.is_file():
        return config

    spans_by_page = _pdf_text_spans_by_page(pdf_path)
    pages = []
    for page in config.pages:
        spans = spans_by_page.get(page.page_number, [])
        if not spans:
            pages.append(page)
            continue
        pages.append(
            replace(
                page,
                blocks=[
                    _text_block_with_pdf_style(block, spans)
                    if isinstance(block, TextBlock)
                    else block
                    for block in page.blocks
                ],
            )
        )
    return replace(config, pages=pages)


def _pdf_text_spans_by_page(pdf_path: Path) -> dict[int, list[dict[str, Any]]]:
    pages: dict[int, list[dict[str, Any]]] = {}
    document = pdfium.PdfDocument(str(pdf_path))
    try:
        for page_index in range(len(document)):
            page = document[page_index]
            try:
                text_page = page.get_textpage()
                try:
                    pages[page_index + 1] = _pdfium_text_spans(text_page, ctypes)
                finally:
                    text_page.close()
            finally:
                page.close()
    finally:
        document.close()
    return pages


def _pdfium_text_spans(text_page: Any, ctypes_module: Any) -> list[dict[str, Any]]:
    raw = pdfium.raw
    spans: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for char_index in range(int(raw.FPDFText_CountChars(text_page.raw))):
        codepoint = int(raw.FPDFText_GetUnicode(text_page.raw, char_index))
        character = chr(codepoint) if codepoint else ""
        if character in {"\n", "\r"}:
            current = _flush_pdfium_span(current, spans)
            continue

        bbox = _pdfium_char_bbox(text_page, char_index, ctypes_module)
        if bbox is None:
            continue
        style = {
            "font_name": _pdfium_font_name(text_page, char_index, ctypes_module),
            "font_size": float(raw.FPDFText_GetFontSize(text_page.raw, char_index)),
            "color": _pdfium_fill_color(text_page, char_index, ctypes_module),
        }

        if current is None or _style_key(current) != _style_key(style):
            current = _flush_pdfium_span(current, spans)
            current = {"text": "", "bbox": bbox, **style}
        current["text"] += character
        current["bbox"] = _bbox_union(current["bbox"], bbox)

    _flush_pdfium_span(current, spans)
    return spans


def _flush_pdfium_span(
    span: dict[str, Any] | None,
    spans: list[dict[str, Any]],
) -> None:
    if span is not None and str(span["text"]).strip():
        spans.append(span)
    return None


def _style_key(span: dict[str, Any]) -> tuple[str | None, float | None, str | None]:
    font_size = span.get("font_size")
    return (
        span.get("font_name"),
        round(float(font_size), 2) if font_size is not None else None,
        span.get("color"),
    )


def _pdfium_char_bbox(
    text_page: Any,
    char_index: int,
    ctypes_module: Any,
) -> BBox | None:
    left = ctypes_module.c_double()
    right = ctypes_module.c_double()
    bottom = ctypes_module.c_double()
    top = ctypes_module.c_double()
    ok = pdfium.raw.FPDFText_GetCharBox(
        text_page.raw,
        char_index,
        ctypes_module.byref(left),
        ctypes_module.byref(right),
        ctypes_module.byref(bottom),
        ctypes_module.byref(top),
    )
    if not ok:
        return None
    return BBox(x0=left.value, y0=bottom.value, x1=right.value, y1=top.value)


def _pdfium_font_name(
    text_page: Any,
    char_index: int,
    ctypes_module: Any,
) -> str | None:
    flags = ctypes_module.c_int()
    size = pdfium.raw.FPDFText_GetFontInfo(
        text_page.raw,
        char_index,
        None,
        0,
        ctypes_module.byref(flags),
    )
    if size <= 0:
        return None
    buffer = ctypes_module.create_string_buffer(size)
    pdfium.raw.FPDFText_GetFontInfo(
        text_page.raw,
        char_index,
        buffer,
        size,
        ctypes_module.byref(flags),
    )
    return buffer.value.decode("utf-8", errors="replace") or None


def _pdfium_fill_color(
    text_page: Any,
    char_index: int,
    ctypes_module: Any,
) -> str | None:
    red = ctypes_module.c_uint()
    green = ctypes_module.c_uint()
    blue = ctypes_module.c_uint()
    alpha = ctypes_module.c_uint()
    ok = pdfium.raw.FPDFText_GetFillColor(
        text_page.raw,
        char_index,
        ctypes_module.byref(red),
        ctypes_module.byref(green),
        ctypes_module.byref(blue),
        ctypes_module.byref(alpha),
    )
    if not ok:
        return None
    return f"#{red.value:02x}{green.value:02x}{blue.value:02x}"


def _bbox_union(left: BBox, right: BBox) -> BBox:
    return BBox(
        x0=min(left.x0, right.x0),
        y0=min(left.y0, right.y0),
        x1=max(left.x1, right.x1),
        y1=max(left.y1, right.y1),
    )


def _text_block_with_pdf_style(
    block: TextBlock,
    spans: list[dict[str, Any]],
) -> TextBlock:
    match = _best_style_span_for_block(block, spans)
    if match is None:
        return block

    return replace(
        block,
        style=TextStyle(
            font_name=match["font_name"],
            font_size=match["font_size"],
            color=match["color"],
            rotation=block.style.rotation,
        ),
    )


def _best_style_span_for_block(
    block: TextBlock,
    spans: list[dict[str, Any]],
) -> dict[str, Any] | None:
    expected = _normalize_text(block.text)
    best: tuple[float, dict[str, Any]] | None = None
    for span in spans:
        score = _style_match_score(expected, block.bbox, span)
        if score <= 0:
            continue
        if best is None or score > best[0]:
            best = (score, span)
    return best[1] if best is not None else None


def _style_match_score(expected_text: str, bbox: BBox, span: dict[str, Any]) -> float:
    actual_text = _normalize_text(span["text"])
    if not expected_text or not actual_text:
        return 0.0

    if expected_text == actual_text:
        text_score = 1.0
    elif actual_text in expected_text or expected_text in actual_text:
        text_score = min(len(actual_text), len(expected_text)) / max(
            len(actual_text),
            len(expected_text),
        )
    else:
        return 0.0

    overlap = _bbox_intersection_area(bbox, span["bbox"])
    if overlap <= 0:
        return 0.0
    span_area = _bbox_area(span["bbox"])
    block_area = _bbox_area(bbox)
    area_score = overlap / max(min(span_area, block_area), 1.0)
    return text_score * area_score


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _bbox_intersection_area(a: BBox, b: BBox) -> float:
    width = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))
    height = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
    return width * height


def _bbox_area(bbox: BBox) -> float:
    return max(0.0, bbox.x1 - bbox.x0) * max(0.0, bbox.y1 - bbox.y0)


def _color_int_to_hex(value: Any) -> str | None:
    if value is None:
        return None
    color = int(value)
    return f"#{color & 0xFFFFFF:06x}"
