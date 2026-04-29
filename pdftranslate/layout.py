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

    def to_dict(self) -> dict[str, str | float | None]:
        return {
            "ref": self.ref,
            "width": self.width,
            "height": self.height,
            "mime_type": self.mime_type,
        }


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
