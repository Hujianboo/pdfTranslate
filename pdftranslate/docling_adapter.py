from __future__ import annotations

from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from pdftranslate.layout import (
    BBox,
    ImageBlock,
    ImageInfo,
    LayoutConfig,
    PageLayout,
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
    return BBox(
        x0=float(bbox.l),
        y0=float(bbox.b),
        x1=float(bbox.r),
        y1=float(bbox.t),
    )
