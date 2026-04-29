import json

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


def test_image_info_serializes_asset_path_when_present():
    block = ImageBlock(
        id="p2_i1",
        page_number=2,
        bbox=BBox(x0=72.0, y0=220.0, x1=240.0, y1=340.0),
        image=ImageInfo(
            ref="p2_i1",
            width=168.0,
            height=120.0,
            mime_type="image/png",
            asset_path="output/assets/sample/images/p2_i1.png",
        ),
    )

    data = block.to_dict()

    assert data["image"]["asset_path"] == "output/assets/sample/images/p2_i1.png"
    assert data["image"]["mime_type"] == "image/png"


def test_table_block_serializes_table_layout_fields():
    block = TableBlock(
        id="p1_t1",
        page_number=1,
        bbox=BBox(x0=72.0, y0=300.0, x1=540.0, y1=520.0),
        table=TableInfo(num_rows=2, num_cols=2),
    )

    assert block.to_dict() == {
        "id": "p1_t1",
        "kind": "table",
        "page_number": 1,
        "bbox": {"x0": 72.0, "y0": 300.0, "x1": 540.0, "y1": 520.0},
        "table": {
            "num_rows": 2,
            "num_cols": 2,
            "cells": [],
        },
    }


def test_table_info_serializes_row_col_counts_and_cells():
    info = TableInfo(
        num_rows=3,
        num_cols=2,
        cells=[
            TableCellInfo(
                text="Header",
                row_start=0,
                row_end=1,
                col_start=0,
                col_end=1,
            )
        ],
    )

    data = info.to_dict()

    assert data["num_rows"] == 3
    assert data["num_cols"] == 2
    assert len(data["cells"]) == 1
    assert data["cells"][0]["text"] == "Header"


def test_table_cell_info_serializes_ranges_spans_headers_and_optional_bbox():
    cell = TableCellInfo(
        text="Cell text",
        row_start=1,
        row_end=3,
        col_start=2,
        col_end=4,
        row_span=2,
        col_span=2,
        column_header=True,
        row_header=True,
        bbox=BBox(x0=100.0, y0=200.0, x1=160.0, y1=230.0),
    )

    assert cell.to_dict() == {
        "text": "Cell text",
        "row_start": 1,
        "row_end": 3,
        "col_start": 2,
        "col_end": 4,
        "row_span": 2,
        "col_span": 2,
        "column_header": True,
        "row_header": True,
        "bbox": {"x0": 100.0, "y0": 200.0, "x1": 160.0, "y1": 230.0},
    }


def test_formula_block_serializes_formula_and_defaults_not_translatable():
    block = FormulaBlock(
        id="p1_f1",
        page_number=1,
        bbox=BBox(x0=180.0, y0=420.0, x1=432.0, y1=456.0),
        formula=FormulaInfo(text="E=mc^2"),
    )

    data = block.to_dict()

    assert data == {
        "id": "p1_f1",
        "kind": "formula",
        "page_number": 1,
        "bbox": {"x0": 180.0, "y0": 420.0, "x1": 432.0, "y1": 456.0},
        "formula": {"text": "E=mc^2"},
        "translatable": False,
    }


def test_formula_info_serializes_text_ref_and_formula_type_when_present():
    text_formula = FormulaInfo(text="x+y")
    ref_formula = FormulaInfo(ref="#/texts/1")
    typed_formula = FormulaInfo(text="a=b", formula_type="inline")

    assert text_formula.to_dict() == {"text": "x+y"}
    assert ref_formula.to_dict() == {"ref": "#/texts/1"}
    assert typed_formula.to_dict() == {"text": "a=b", "formula_type": "inline"}


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


def test_layout_config_json_with_table_and_formula_stays_source_only():
    config = LayoutConfig(
        source_file="sample.pdf",
        pages=[
            PageLayout(
                page_number=1,
                width=612.0,
                height=792.0,
                blocks=[
                    TableBlock(
                        id="p1_t1",
                        page_number=1,
                        bbox=BBox(x0=72.0, y0=300.0, x1=540.0, y1=520.0),
                        table=TableInfo(
                            num_rows=1,
                            num_cols=1,
                            cells=[TableCellInfo(text="Source")],
                        ),
                    ),
                    FormulaBlock(
                        id="p1_f1",
                        page_number=1,
                        bbox=BBox(x0=180.0, y0=420.0, x1=432.0, y1=456.0),
                        formula=FormulaInfo(text="E=mc^2"),
                    ),
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
