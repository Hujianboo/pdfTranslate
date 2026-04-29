import base64

from pdftranslate.image_assets import (
    ExtractedImageAsset,
    attach_image_assets_to_layout,
    asset_filename_for_block,
    bbox_from_top_left_rect,
    extract_pdf_image_assets,
    match_image_assets_to_blocks,
    relative_asset_path,
)
from pdftranslate.layout import ImageBlock
from pdftranslate.layout import BBox
from pdftranslate.layout_io import layout_config_from_dict
from tests.fixtures import minimal_layout_dict


_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def test_top_left_pdf_rect_converts_to_bottom_left_layout_bbox():
    pdf_rect = BBox(x0=100.0, y0=50.0, x1=260.0, y1=170.0)

    bbox = bbox_from_top_left_rect(pdf_rect, page_height=792.0)

    assert bbox == BBox(x0=100.0, y0=622.0, x1=260.0, y1=742.0)


def test_matcher_chooses_image_block_on_same_page_by_bbox_similarity():
    config = layout_config_from_dict(minimal_layout_dict(page_count=2))
    matching_asset = ExtractedImageAsset(
        page_number=1,
        bbox=BBox(x0=202.0, y0=242.0, x1=298.0, y1=338.0),
        data=b"fake-image",
        extension="png",
        mime_type="image/png",
        source_id="xref-1",
    )
    wrong_page_asset = ExtractedImageAsset(
        page_number=2,
        bbox=BBox(x0=202.0, y0=242.0, x1=298.0, y1=338.0),
        data=b"wrong-page",
        extension="png",
        mime_type="image/png",
        source_id="xref-2",
    )

    matches = match_image_assets_to_blocks(config, [wrong_page_asset, matching_asset])

    assert matches["p1_i1"] == matching_asset


def test_asset_filename_uses_image_block_id():
    config = layout_config_from_dict(minimal_layout_dict())
    image_block = config.pages[0].blocks[1]
    assert isinstance(image_block, ImageBlock)
    asset = ExtractedImageAsset(
        page_number=1,
        bbox=image_block.bbox,
        data=b"fake-image",
        extension="png",
        mime_type="image/png",
        source_id="xref-1",
    )

    filename = asset_filename_for_block(image_block, asset)

    assert filename == "p1_i1.png"


def test_relative_asset_path_is_not_absolute(tmp_path):
    project_root = tmp_path / "project"
    asset_path = project_root / "output" / "assets" / "sample" / "images" / "p1_i1.png"

    relative_path = relative_asset_path(asset_path, base_dir=project_root)

    assert relative_path == "output/assets/sample/images/p1_i1.png"
    assert not relative_path.startswith("/")


def test_unmatched_image_block_keeps_original_image_fields(tmp_path):
    config = layout_config_from_dict(minimal_layout_dict())

    updated = attach_image_assets_to_layout(
        config,
        [],
        assets_dir=tmp_path / "images",
        base_dir=tmp_path,
    )

    image = updated.pages[0].blocks[1].image
    assert image.ref == "p1_i1"
    assert image.width == 100.0
    assert image.height == 100.0
    assert image.mime_type is None
    assert image.asset_path is None


def test_extract_pdf_image_assets_writes_non_empty_image_file(tmp_path):
    pdf_path = tmp_path / "with-image.pdf"
    _write_pdf_with_png(pdf_path)
    assets_dir = tmp_path / "images"
    config = layout_config_from_dict(minimal_layout_dict())

    extract_pdf_image_assets(
        pdf_path,
        assets_dir=assets_dir,
        layout_config=config,
        base_dir=tmp_path,
    )

    files = list(assets_dir.iterdir())
    assert files
    assert all(path.stat().st_size > 0 for path in files)


def test_extracted_png_writes_mime_type_to_matched_image_block(tmp_path):
    pdf_path = tmp_path / "with-image.pdf"
    _write_pdf_with_png(pdf_path)
    config = layout_config_from_dict(minimal_layout_dict())

    updated = extract_pdf_image_assets(
        pdf_path,
        assets_dir=tmp_path / "images",
        layout_config=config,
        base_dir=tmp_path,
    )

    image = updated.pages[0].blocks[1].image
    assert image.mime_type == "image/png"
    assert image.asset_path == "images/p1_i1.png"


def _write_pdf_with_png(pdf_path):
    from reportlab.pdfgen import canvas

    image_path = pdf_path.with_suffix(".png")
    image_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    pdf = canvas.Canvas(str(pdf_path), pagesize=(612.0, 792.0))
    pdf.drawImage(str(image_path), 200.0, 240.0, width=100.0, height=100.0)
    pdf.save()
