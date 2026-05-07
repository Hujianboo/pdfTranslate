from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import os
from pathlib import Path
from typing import Any

from pdftranslate.layout import BBox
from pdftranslate.layout import (
    FormulaBlock,
    FormulaInfo,
    ImageBlock,
    ImageInfo,
    LayoutConfig,
    PageLayout,
    TableBlock,
    TableInfo,
)


IMAGE_RASTER_SCALE = 2.0


@dataclass(frozen=True)
class ExtractedImageAsset:
    page_number: int
    bbox: BBox
    data: bytes
    extension: str
    mime_type: str | None = None
    source_id: str | None = None


def extract_pdf_image_assets(
    pdf_path: str | Path,
    assets_dir: str | Path,
    layout_config: LayoutConfig,
    base_dir: str | Path | None = None,
) -> LayoutConfig:
    output_dir = Path(assets_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    block_assets = rasterize_image_blocks(pdf_path, layout_config)
    block_assets.update(rasterize_table_and_formula_blocks(pdf_path, layout_config))

    blocks_by_id = {
        block.id: block for block in _iter_asset_blocks(layout_config)
    }
    for block_id, asset in block_assets.items():
        block = blocks_by_id[block_id]
        output_path = output_dir / asset_filename_for_block(block, asset)
        output_path.write_bytes(asset.data)

    return attach_image_assets_to_layout(
        layout_config,
        assets_dir=output_dir,
        base_dir=base_dir,
        matches=block_assets,
    )


def rasterize_image_blocks(
    pdf_path: str | Path,
    config: LayoutConfig,
) -> dict[str, ExtractedImageAsset]:
    import pypdfium2 as pdfium  # type: ignore[import-not-found]

    rasterized: dict[str, ExtractedImageAsset] = {}

    page_sizes = {page.page_number: page.height for page in config.pages}
    blocks_by_page: dict[int, list[ImageBlock]] = {}
    for block in _iter_image_blocks(config):
        blocks_by_page.setdefault(block.page_number, []).append(block)

    if not blocks_by_page:
        return rasterized

    document = pdfium.PdfDocument(str(pdf_path))
    try:
        for page_number, blocks in blocks_by_page.items():
            page = document[page_number - 1]
            try:
                page_height = page_sizes.get(page_number, float(page.get_height()))
                for block in blocks:
                    asset = rasterize_image_block(page, block, page_height=page_height)
                    if asset is not None:
                        rasterized[block.id] = asset
            finally:
                page.close()
    finally:
        document.close()
    return rasterized


def rasterize_table_and_formula_blocks(
    pdf_path: str | Path,
    config: LayoutConfig,
) -> dict[str, ExtractedImageAsset]:
    import pypdfium2 as pdfium  # type: ignore[import-not-found]

    rasterized: dict[str, ExtractedImageAsset] = {}
    page_sizes = {page.page_number: page.height for page in config.pages}
    blocks_by_page: dict[int, list[TableBlock | FormulaBlock]] = {}
    for block in _iter_table_formula_blocks(config):
        blocks_by_page.setdefault(block.page_number, []).append(block)

    if not blocks_by_page:
        return rasterized

    document = pdfium.PdfDocument(str(pdf_path))
    try:
        for page_number, blocks in blocks_by_page.items():
            page = document[page_number - 1]
            try:
                page_height = page_sizes.get(page_number, float(page.get_height()))
                for block in blocks:
                    asset = rasterize_block_bbox(
                        page,
                        block,
                        page_height=page_height,
                        source_prefix=block.kind,
                    )
                    if asset is not None:
                        rasterized[block.id] = asset
            finally:
                page.close()
    finally:
        document.close()
    return rasterized


def asset_filename_for_block(
    block: ImageBlock | TableBlock | FormulaBlock,
    asset: ExtractedImageAsset,
) -> str:
    extension = asset.extension.lower().lstrip(".") or "png"
    return f"{block.id}.{extension}"


def relative_asset_path(path: str | Path, base_dir: str | Path | None = None) -> str:
    start = Path(base_dir) if base_dir is not None else Path.cwd()
    return os.path.relpath(Path(path), start=start)


def attach_image_assets_to_layout(
    config: LayoutConfig,
    assets_dir: str | Path,
    base_dir: str | Path | None = None,
    matches: dict[str, ExtractedImageAsset] | None = None,
) -> LayoutConfig:
    resolved_matches = matches or {}
    pages = []
    for page in config.pages:
        blocks = []
        for block in page.blocks:
            if block.id in resolved_matches:
                asset = resolved_matches[block.id]
                if isinstance(block, ImageBlock):
                    blocks.append(
                        _image_block_with_asset(
                            block,
                            asset,
                            assets_dir=Path(assets_dir),
                            base_dir=base_dir,
                        )
                    )
                elif isinstance(block, TableBlock):
                    blocks.append(
                        _table_block_with_asset(
                            block,
                            asset,
                            assets_dir=Path(assets_dir),
                            base_dir=base_dir,
                        )
                    )
                elif isinstance(block, FormulaBlock):
                    blocks.append(
                        _formula_block_with_asset(
                            block,
                            asset,
                            assets_dir=Path(assets_dir),
                            base_dir=base_dir,
                        )
                    )
                else:
                    blocks.append(block)
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


def _iter_table_formula_blocks(config: LayoutConfig) -> list[TableBlock | FormulaBlock]:
    return [
        block
        for page in config.pages
        for block in page.blocks
        if isinstance(block, (TableBlock, FormulaBlock))
    ]


def _iter_asset_blocks(
    config: LayoutConfig,
) -> list[ImageBlock | TableBlock | FormulaBlock]:
    return [
        block
        for page in config.pages
        for block in page.blocks
        if isinstance(block, (ImageBlock, TableBlock, FormulaBlock))
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


def _table_block_with_asset(
    block: TableBlock,
    asset: ExtractedImageAsset,
    assets_dir: Path,
    base_dir: str | Path | None,
) -> TableBlock:
    asset_path = assets_dir / asset_filename_for_block(block, asset)
    table = TableInfo(
        num_rows=block.table.num_rows,
        num_cols=block.table.num_cols,
        cells=list(block.table.cells),
        ref=block.table.ref,
        caption=block.table.caption,
        mime_type=asset.mime_type or block.table.mime_type,
        asset_path=relative_asset_path(asset_path, base_dir=base_dir),
    )
    return replace(block, table=table)


def _formula_block_with_asset(
    block: FormulaBlock,
    asset: ExtractedImageAsset,
    assets_dir: Path,
    base_dir: str | Path | None,
) -> FormulaBlock:
    asset_path = assets_dir / asset_filename_for_block(block, asset)
    formula = FormulaInfo(
        text=block.formula.text,
        ref=block.formula.ref,
        formula_type=block.formula.formula_type,
        mime_type=asset.mime_type or block.formula.mime_type,
        asset_path=relative_asset_path(asset_path, base_dir=base_dir),
    )
    return replace(block, formula=formula)


def _page_with_blocks(page: PageLayout, blocks: list[object]) -> PageLayout:
    return PageLayout(
        page_number=page.page_number,
        width=page.width,
        height=page.height,
        blocks=blocks,
        rotation=page.rotation,
        warnings=list(page.warnings),
    )


def _mime_type_for_extension(extension: str) -> str:
    normalized = extension.lower().lstrip(".")
    if normalized == "jpg":
        normalized = "jpeg"
    return f"image/{normalized or 'png'}"


def rasterize_image_block(
    page: Any,
    block: ImageBlock,
    *,
    page_height: float,
) -> ExtractedImageAsset | None:
    return rasterize_block_bbox(
        page,
        block,
        page_height=page_height,
        source_prefix="raster",
    )


def rasterize_block_bbox(
    page: Any,
    block: ImageBlock | TableBlock | FormulaBlock,
    *,
    page_height: float,
    source_prefix: str,
) -> ExtractedImageAsset | None:
    from io import BytesIO

    page_width = float(page.get_width())
    crop = (
        float(block.bbox.x0),
        float(block.bbox.y0),
        max(0.0, page_width - float(block.bbox.x1)),
        max(0.0, page_height - float(block.bbox.y1)),
    )
    width = float(block.bbox.x1 - block.bbox.x0)
    height = float(block.bbox.y1 - block.bbox.y0)
    if width <= 0 or height <= 0:
        return None

    bitmap = page.render(scale=IMAGE_RASTER_SCALE, crop=crop)
    try:
        image = bitmap.to_pil()
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        data = buffer.getvalue()
        if not data:
            return None
    finally:
        bitmap.close()

    return ExtractedImageAsset(
        page_number=block.page_number,
        bbox=block.bbox,
        data=data,
        extension="png",
        mime_type="image/png",
        source_id=f"{source_prefix}:{block.id}",
    )
