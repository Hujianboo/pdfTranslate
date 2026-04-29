import json

from pdftranslate.layout import (
    BBox,
    ImageBlock,
    ImageInfo,
    LayoutConfig,
    PageLayout,
    TextBlock,
    TextStyle,
)


def test_layout_config_serializes_top_level_fields():
    config = LayoutConfig(
        source_file="sample.pdf",
        pages=[
            PageLayout(
                page_number=1,
                width=612.0,
                height=792.0,
                blocks=[],
            )
        ],
    )

    data = config.to_dict()

    assert data["schema_version"] == "1.0"
    assert data["source_file"] == "sample.pdf"
    assert data["coordinate_system"] == {"unit": "pt", "origin": "bottom-left"}
    assert isinstance(data["pages"], list)
    assert data["pages"][0]["page_number"] == 1
    assert json.loads(config.to_json()) == data


def test_text_block_serializes_translation_ready_fields():
    block = TextBlock(
        id="p1_b1",
        page_number=1,
        text="Original text",
        bbox=BBox(x0=72.0, y0=100.0, x1=200.0, y1=124.0),
        style=TextStyle(font_name=None, font_size=None, color=None, rotation=0),
    )

    data = block.to_dict()

    assert data == {
        "id": "p1_b1",
        "kind": "text",
        "page_number": 1,
        "text": "Original text",
        "bbox": {"x0": 72.0, "y0": 100.0, "x1": 200.0, "y1": 124.0},
        "style": {
            "font_name": None,
            "font_size": None,
            "color": None,
            "rotation": 0,
        },
        "translatable": True,
    }


def test_image_block_serializes_rebuild_reference_fields():
    block = ImageBlock(
        id="p1_i1",
        page_number=1,
        bbox=BBox(x0=72.0, y0=220.0, x1=240.0, y1=340.0),
        image=ImageInfo(ref="p1_i1", width=168.0, height=120.0),
    )

    assert block.to_dict() == {
        "id": "p1_i1",
        "kind": "image",
        "page_number": 1,
        "bbox": {"x0": 72.0, "y0": 220.0, "x1": 240.0, "y1": 340.0},
        "image": {
            "ref": "p1_i1",
            "width": 168.0,
            "height": 120.0,
            "mime_type": None,
        },
    }


def test_layout_config_json_excludes_translation_rebuild_and_ocr_fields():
    config = LayoutConfig(
        source_file="sample.pdf",
        pages=[
            PageLayout(
                page_number=1,
                width=612.0,
                height=792.0,
                blocks=[
                    TextBlock(
                        id="p1_b1",
                        page_number=1,
                        text="Original text",
                        bbox=BBox(x0=72.0, y0=100.0, x1=200.0, y1=124.0),
                    )
                ],
            )
        ],
    )

    serialized = config.to_json()

    for forbidden_field in (
        "translated_text",
        "target_text",
        "rebuilt_pdf",
        "edited_image",
        "ocr_text",
    ):
        assert forbidden_field not in serialized
