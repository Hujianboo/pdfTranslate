from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import os
from pathlib import Path
from typing import Any

from pdftranslate.layout import BBox
from pdftranslate.layout import ImageBlock, ImageInfo, LayoutConfig, PageLayout


@dataclass(frozen=True)
class ExtractedImageAsset:
    page_number: int
    bbox: BBox
    data: bytes
    extension: str
    mime_type: str | None = None
    source_id: str | None = None


def bbox_from_top_left_rect(rect: Any, page_height: float) -> BBox:
    return BBox(
        x0=float(rect.x0),
        y0=page_height - float(rect.y1),
        x1=float(rect.x1),
        y1=page_height - float(rect.y0),
    )


def extract_pdf_image_assets(
    pdf_path: str | Path,
    assets_dir: str | Path,
    layout_config: LayoutConfig,
    base_dir: str | Path | None = None,
) -> LayoutConfig:
    assets = extract_images_from_pdf(pdf_path)
    output_dir = Path(assets_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    matches = match_image_assets_to_blocks(layout_config, assets)
    blocks_by_id = {block.id: block for block in _iter_image_blocks(layout_config)}
    for block_id, asset in matches.items():
        block = blocks_by_id[block_id]
        output_path = output_dir / asset_filename_for_block(block, asset)
        output_path.write_bytes(asset.data)

    return attach_image_assets_to_layout(
        layout_config,
        assets,
        assets_dir=output_dir,
        base_dir=base_dir,
    )


def extract_images_from_pdf(pdf_path: str | Path) -> list[ExtractedImageAsset]:
    import fitz

    assets: list[ExtractedImageAsset] = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            page_height = float(page.rect.height)
            for image_tuple in page.get_images(full=True):
                xref = int(image_tuple[0])
                image_data = document.extract_image(xref)
                data = image_data.get("image")
                if not data:
                    continue

                extension = str(image_data.get("ext") or "png").lower()
                for rect in page.get_image_rects(xref):
                    assets.append(
                        ExtractedImageAsset(
                            page_number=page_index,
                            bbox=bbox_from_top_left_rect(rect, page_height),
                            data=bytes(data),
                            extension=extension,
                            mime_type=_mime_type_for_extension(extension),
                            source_id=str(xref),
                        )
                    )
    return assets


def match_image_assets_to_blocks(
    config: LayoutConfig,
    assets: list[ExtractedImageAsset],
) -> dict[str, ExtractedImageAsset]:
    matches: dict[str, ExtractedImageAsset] = {}
    used_asset_indexes: set[int] = set()

    for block in _iter_image_blocks(config):
        best_index: int | None = None
        best_score: float | None = None
        for index, asset in enumerate(assets):
            if index in used_asset_indexes or asset.page_number != block.page_number:
                continue

            score = _match_score(block.bbox, asset.bbox)
            if best_score is None or score < best_score:
                best_score = score
                best_index = index

        if best_index is not None:
            used_asset_indexes.add(best_index)
            matches[block.id] = assets[best_index]

    return matches


def asset_filename_for_block(block: ImageBlock, asset: ExtractedImageAsset) -> str:
    extension = asset.extension.lower().lstrip(".") or "png"
    return f"{block.id}.{extension}"


def relative_asset_path(path: str | Path, base_dir: str | Path | None = None) -> str:
    start = Path(base_dir) if base_dir is not None else Path.cwd()
    return os.path.relpath(Path(path), start=start)


def attach_image_assets_to_layout(
    config: LayoutConfig,
    assets: list[ExtractedImageAsset],
    assets_dir: str | Path,
    base_dir: str | Path | None = None,
) -> LayoutConfig:
    matches = match_image_assets_to_blocks(config, assets)
    pages = []
    for page in config.pages:
        blocks = []
        for block in page.blocks:
            if isinstance(block, ImageBlock) and block.id in matches:
                blocks.append(
                    _image_block_with_asset(
                        block,
                        matches[block.id],
                        assets_dir=Path(assets_dir),
                        base_dir=base_dir,
                    )
                )
            else:
                blocks.append(block)
        pages.append(_page_with_blocks(page, blocks))

    return LayoutConfig(
        source_file=config.source_file,
        pages=pages,
        schema_version=config.schema_version,
        coordinate_system=dict(config.coordinate_system),
    )


def _iter_image_blocks(config: LayoutConfig) -> list[ImageBlock]:
    return [
        block
        for page in config.pages
        for block in page.blocks
        if isinstance(block, ImageBlock)
    ]


def _image_block_with_asset(
    block: ImageBlock,
    asset: ExtractedImageAsset,
    assets_dir: Path,
    base_dir: str | Path | None,
) -> ImageBlock:
    asset_path = assets_dir / asset_filename_for_block(block, asset)
    image = ImageInfo(
        ref=block.image.ref,
        width=block.image.width,
        height=block.image.height,
        mime_type=asset.mime_type or block.image.mime_type,
        asset_path=relative_asset_path(asset_path, base_dir=base_dir),
    )
    return replace(block, image=image)


def _page_with_blocks(page: PageLayout, blocks: list[object]) -> PageLayout:
    return PageLayout(
        page_number=page.page_number,
        width=page.width,
        height=page.height,
        blocks=blocks,
        rotation=page.rotation,
        warnings=list(page.warnings),
    )


def _match_score(left: BBox, right: BBox) -> float:
    iou = _bbox_iou(left, right)
    return (1.0 - iou) + (_center_distance(left, right) / 10000.0)


def _bbox_iou(left: BBox, right: BBox) -> float:
    x0 = max(left.x0, right.x0)
    y0 = max(left.y0, right.y0)
    x1 = min(left.x1, right.x1)
    y1 = min(left.y1, right.y1)
    intersection = max(x1 - x0, 0.0) * max(y1 - y0, 0.0)
    if intersection == 0:
        return 0.0

    left_area = max(left.x1 - left.x0, 0.0) * max(left.y1 - left.y0, 0.0)
    right_area = max(right.x1 - right.x0, 0.0) * max(right.y1 - right.y0, 0.0)
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def _center_distance(left: BBox, right: BBox) -> float:
    left_x = (left.x0 + left.x1) / 2
    left_y = (left.y0 + left.y1) / 2
    right_x = (right.x0 + right.x1) / 2
    right_y = (right.y0 + right.y1) / 2
    return ((left_x - right_x) ** 2 + (left_y - right_y) ** 2) ** 0.5


def _mime_type_for_extension(extension: str) -> str:
    normalized = extension.lower().lstrip(".")
    if normalized == "jpg":
        normalized = "jpeg"
    return f"image/{normalized or 'png'}"
