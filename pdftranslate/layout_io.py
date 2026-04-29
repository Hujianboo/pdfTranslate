from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pdftranslate.layout import (
    BBox,
    ImageBlock,
    ImageInfo,
    LayoutConfig,
    PageLayout,
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


def _block_from_dict(data: dict[str, Any]) -> TextBlock | ImageBlock:
    kind = data["kind"]
    if kind == "text":
        return TextBlock(
            id=str(data["id"]),
            page_number=int(data["page_number"]),
            text=str(data.get("text", "")),
            bbox=_bbox_from_dict(data["bbox"]),
            style=_text_style_from_dict(data.get("style", {})),
            translatable=bool(data.get("translatable", True)),
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
