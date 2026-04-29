from __future__ import annotations

from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

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
    return _layout_from_docling_document(result.document, source_file=str(input_path))


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
