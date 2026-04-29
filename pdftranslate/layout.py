from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any


SCHEMA_VERSION = "1.0"
COORDINATE_SYSTEM = {"unit": "pt", "origin": "bottom-left"}


@dataclass(frozen=True)
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    def to_dict(self) -> dict[str, float]:
        return {
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
        }


@dataclass(frozen=True)
class TextStyle:
    font_name: str | None = None
    font_size: float | None = None
    color: str | None = None
    rotation: int = 0

    def to_dict(self) -> dict[str, str | float | int | None]:
        return {
            "font_name": self.font_name,
            "font_size": self.font_size,
            "color": self.color,
            "rotation": self.rotation,
        }


@dataclass(frozen=True)
class TextBlock:
    id: str
    page_number: int
    text: str
    bbox: BBox
    style: TextStyle = field(default_factory=TextStyle)
    translatable: bool = True
    kind: str = "text"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "page_number": self.page_number,
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "style": self.style.to_dict(),
            "translatable": self.translatable,
        }


@dataclass(frozen=True)
class ImageInfo:
    ref: str
    width: float
    height: float
    mime_type: str | None = None
    asset_path: str | None = None

    def to_dict(self) -> dict[str, str | float | None]:
        data: dict[str, str | float | None] = {
            "ref": self.ref,
            "width": self.width,
            "height": self.height,
            "mime_type": self.mime_type,
        }
        if self.asset_path is not None:
            data["asset_path"] = self.asset_path
        return data


@dataclass(frozen=True)
class ImageBlock:
    id: str
    page_number: int
    bbox: BBox
    image: ImageInfo
    kind: str = "image"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "page_number": self.page_number,
            "bbox": self.bbox.to_dict(),
            "image": self.image.to_dict(),
        }


@dataclass(frozen=True)
class TableCellInfo:
    text: str = ""
    row_start: int = 0
    row_end: int = 1
    col_start: int = 0
    col_end: int = 1
    row_span: int = 1
    col_span: int = 1
    column_header: bool = False
    row_header: bool = False
    bbox: BBox | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "text": self.text,
            "row_start": self.row_start,
            "row_end": self.row_end,
            "col_start": self.col_start,
            "col_end": self.col_end,
            "row_span": self.row_span,
            "col_span": self.col_span,
            "column_header": self.column_header,
            "row_header": self.row_header,
        }
        if self.bbox is not None:
            data["bbox"] = self.bbox.to_dict()
        return data


@dataclass(frozen=True)
class TableInfo:
    num_rows: int
    num_cols: int
    cells: list[TableCellInfo] = field(default_factory=list)
    ref: str | None = None
    caption: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "num_rows": self.num_rows,
            "num_cols": self.num_cols,
            "cells": [cell.to_dict() for cell in self.cells],
        }
        if self.ref is not None:
            data["ref"] = self.ref
        if self.caption is not None:
            data["caption"] = self.caption
        return data


@dataclass(frozen=True)
class TableBlock:
    id: str
    page_number: int
    bbox: BBox
    table: TableInfo
    kind: str = "table"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "page_number": self.page_number,
            "bbox": self.bbox.to_dict(),
            "table": self.table.to_dict(),
        }


@dataclass(frozen=True)
class FormulaInfo:
    text: str | None = None
    ref: str | None = None
    formula_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.text is not None:
            data["text"] = self.text
        if self.ref is not None:
            data["ref"] = self.ref
        if self.formula_type is not None:
            data["formula_type"] = self.formula_type
        return data


@dataclass(frozen=True)
class FormulaBlock:
    id: str
    page_number: int
    bbox: BBox
    formula: FormulaInfo
    translatable: bool = False
    kind: str = "formula"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "page_number": self.page_number,
            "bbox": self.bbox.to_dict(),
            "formula": self.formula.to_dict(),
            "translatable": self.translatable,
        }


@dataclass(frozen=True)
class PageLayout:
    page_number: int
    width: float
    height: float
    blocks: list[Any] = field(default_factory=list)
    rotation: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
            "blocks": [
                block.to_dict() if hasattr(block, "to_dict") else block
                for block in self.blocks
            ],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class LayoutConfig:
    source_file: str
    pages: list[PageLayout]
    schema_version: str = SCHEMA_VERSION
    coordinate_system: dict[str, str] = field(
        default_factory=lambda: dict(COORDINATE_SYSTEM)
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_file": self.source_file,
            "coordinate_system": dict(self.coordinate_system),
            "pages": [page.to_dict() for page in self.pages],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
