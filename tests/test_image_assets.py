import base64

from pdftranslate.image_assets import (
    ExtractedImageAsset,
    attach_image_assets_to_layout,
    asset_filename_for_block,
    extract_pdf_image_assets,
    relative_asset_path,
)
from pdftranslate.layout import ImageBlock
from pdftranslate.layout import BBox
from pdftranslate.layout_io import layout_config_from_dict
from tests.fixtures import layout_dict_with_all_block_kinds, minimal_layout_dict


_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


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
        assets_dir=tmp_path / "images",
        base_dir=tmp_path,
    )

    image = updated.pages[0].blocks[1].image
    assert image.ref == "p1_i1"
    assert image.width == 100.0
    assert image.height == 100.0
    assert image.mime_type is None
    assert image.asset_path is None


def test_attach_image_assets_to_layout_writes_table_and_formula_asset_paths(tmp_path):
    config = layout_config_from_dict(layout_dict_with_all_block_kinds())
    table_asset = ExtractedImageAsset(
        page_number=1,
        bbox=config.pages[0].blocks[2].bbox,
        data=b"table",
        extension="png",
        mime_type="image/png",
        source_id="table:p1_t1",
    )
    formula_asset = ExtractedImageAsset(
        page_number=1,
        bbox=config.pages[0].blocks[3].bbox,
        data=b"formula",
        extension="png",
        mime_type="image/png",
        source_id="formula:p1_f1",
    )

    updated = attach_image_assets_to_layout(
        config,
        assets_dir=tmp_path / "images",
        base_dir=tmp_path,
        matches={"p1_t1": table_asset, "p1_f1": formula_asset},
    )

    table = updated.pages[0].blocks[2].table
    formula = updated.pages[0].blocks[3].formula
    assert table.asset_path == "images/p1_t1.png"
    assert table.mime_type == "image/png"
    assert formula.asset_path == "images/p1_f1.png"
    assert formula.mime_type == "image/png"


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


def test_extract_pdf_image_assets_rasterizes_unmatched_image_block(tmp_path):
    pdf_path = tmp_path / "blank.pdf"
    _write_blank_pdf(pdf_path)
    config = layout_config_from_dict(minimal_layout_dict())

    updated = extract_pdf_image_assets(
        pdf_path,
        assets_dir=tmp_path / "images",
        layout_config=config,
        base_dir=tmp_path,
    )

    image = updated.pages[0].blocks[1].image
    asset_path = tmp_path / image.asset_path
    assert image.mime_type == "image/png"
    assert image.asset_path == "images/p1_i1.png"
    assert asset_path.exists()
    assert asset_path.stat().st_size > 0


def test_extract_pdf_image_assets_rasterizes_table_and_formula_blocks(tmp_path):
    pdf_path = tmp_path / "blank.pdf"
    _write_blank_pdf(pdf_path)
    config = layout_config_from_dict(layout_dict_with_all_block_kinds())

    updated = extract_pdf_image_assets(
        pdf_path,
        assets_dir=tmp_path / "images",
        layout_config=config,
        base_dir=tmp_path,
    )

    table = updated.pages[0].blocks[2].table
    formula = updated.pages[0].blocks[3].formula
    assert table.asset_path == "images/p1_t1.png"
    assert formula.asset_path == "images/p1_f1.png"
    assert (tmp_path / table.asset_path).exists()
    assert (tmp_path / formula.asset_path).exists()


def _write_pdf_with_png(pdf_path):
    from reportlab.pdfgen import canvas

    image_path = pdf_path.with_suffix(".png")
    image_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    pdf = canvas.Canvas(str(pdf_path), pagesize=(612.0, 792.0))
    pdf.drawImage(str(image_path), 200.0, 240.0, width=100.0, height=100.0)
    pdf.save()


def _write_blank_pdf(pdf_path):
    from reportlab.pdfgen import canvas

    pdf = canvas.Canvas(str(pdf_path), pagesize=(612.0, 792.0))
    pdf.showPage()
    pdf.save()
