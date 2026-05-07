from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


def load_layout_config(path: str | Path) -> LayoutConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return layout_config_from_dict(data)


def layout_config_from_dict(data: dict[str, Any]) -> LayoutConfig:
    return LayoutConfig(
        source_file=str(data["source_file"]),
        pages=[_page_from_dict(page_data) for page_data in data.get("pages", [])],
        schema_version=str(data.get("schema_version", "1.0")),
        coordinate_system=dict(
            data.get("coordinate_system", {"unit": "pt", "origin": "bottom-left"})
        ),
    )


def _page_from_dict(data: dict[str, Any]) -> PageLayout:
    return PageLayout(
        page_number=int(data["page_number"]),
        width=float(data["width"]),
        height=float(data["height"]),
        rotation=int(data.get("rotation", 0)),
        blocks=[_block_from_dict(block_data) for block_data in data.get("blocks", [])],
        warnings=list(data.get("warnings", [])),
    )


def _block_from_dict(
    data: dict[str, Any],
) -> TextBlock | ImageBlock | TableBlock | FormulaBlock:
    kind = data["kind"]
    if kind == "text":
        return TextBlock(
            id=str(data["id"]),
            page_number=int(data["page_number"]),
            text=str(data.get("text", "")),
            bbox=_bbox_from_dict(data["bbox"]),
            style=_text_style_from_dict(data.get("style", {})),
            translatable=bool(data.get("translatable", True)),
            translated_text=data.get("translated_text"),
        )
    if kind == "image":
        image_data = data["image"]
        return ImageBlock(
            id=str(data["id"]),
            page_number=int(data["page_number"]),
            bbox=_bbox_from_dict(data["bbox"]),
            image=ImageInfo(
                ref=str(image_data["ref"]),
                width=float(image_data["width"]),
                height=float(image_data["height"]),
                mime_type=image_data.get("mime_type"),
                asset_path=image_data.get("asset_path"),
            ),
        )
    if kind == "table":
        return TableBlock(
            id=str(data["id"]),
            page_number=int(data["page_number"]),
            bbox=_bbox_from_dict(data["bbox"]),
            table=_table_info_from_dict(data.get("table", {})),
        )
    if kind == "formula":
        return FormulaBlock(
            id=str(data["id"]),
            page_number=int(data["page_number"]),
            bbox=_bbox_from_dict(data["bbox"]),
            formula=_formula_info_from_dict(data.get("formula", {})),
            translatable=bool(data.get("translatable", False)),
        )
    raise ValueError(f"unsupported block kind: {kind}")


def _bbox_from_dict(data: dict[str, Any]) -> BBox:
    return BBox(
        x0=float(data["x0"]),
        y0=float(data["y0"]),
        x1=float(data["x1"]),
        y1=float(data["y1"]),
    )


def _text_style_from_dict(data: dict[str, Any]) -> TextStyle:
    font_size = data.get("font_size")
    return TextStyle(
        font_name=data.get("font_name"),
        font_size=float(font_size) if font_size is not None else None,
        color=data.get("color"),
        rotation=int(data.get("rotation", 0)),
    )


def _table_info_from_dict(data: dict[str, Any]) -> TableInfo:
    return TableInfo(
        num_rows=int(data.get("num_rows", 0)),
        num_cols=int(data.get("num_cols", 0)),
        cells=[_table_cell_from_dict(cell) for cell in data.get("cells", [])],
        ref=data.get("ref"),
        caption=data.get("caption"),
        mime_type=data.get("mime_type"),
        asset_path=data.get("asset_path"),
    )


def _table_cell_from_dict(data: dict[str, Any]) -> TableCellInfo:
    row_start = int(data.get("row_start", 0))
    col_start = int(data.get("col_start", 0))
    row_span = int(data.get("row_span", 1))
    col_span = int(data.get("col_span", 1))
    return TableCellInfo(
        text=str(data.get("text", "")),
        row_start=row_start,
        row_end=int(data.get("row_end", row_start + row_span)),
        col_start=col_start,
        col_end=int(data.get("col_end", col_start + col_span)),
        row_span=row_span,
        col_span=col_span,
        column_header=bool(data.get("column_header", False)),
        row_header=bool(data.get("row_header", False)),
        bbox=_optional_bbox_from_dict(data.get("bbox")),
    )


def _formula_info_from_dict(data: dict[str, Any]) -> FormulaInfo:
    return FormulaInfo(
        text=data.get("text"),
        ref=data.get("ref"),
        formula_type=data.get("formula_type"),
        mime_type=data.get("mime_type"),
        asset_path=data.get("asset_path"),
    )


def _optional_bbox_from_dict(data: dict[str, Any] | None) -> BBox | None:
    if data is None:
        return None
    return _bbox_from_dict(data)
