def text_block_dict(page_number: int = 1, block_index: int = 1) -> dict:
    return {
        "id": f"p{page_number}_b{block_index}",
        "kind": "text",
        "page_number": page_number,
        "text": "Original text",
        "bbox": {
            "x0": 72.0,
            "y0": 120.0,
            "x1": 180.0,
            "y1": 144.0,
        },
        "style": {
            "font_name": None,
            "font_size": None,
            "color": None,
            "rotation": 0,
        },
        "translatable": True,
    }


def image_block_dict(page_number: int = 1, image_index: int = 1) -> dict:
    return {
        "id": f"p{page_number}_i{image_index}",
        "kind": "image",
        "page_number": page_number,
        "bbox": {
            "x0": 200.0,
            "y0": 240.0,
            "x1": 300.0,
            "y1": 340.0,
        },
        "image": {
            "ref": f"p{page_number}_i{image_index}",
            "width": 100.0,
            "height": 100.0,
            "mime_type": None,
        },
    }


def table_block_dict(page_number: int = 1, table_index: int = 1) -> dict:
    return {
        "id": f"p{page_number}_t{table_index}",
        "kind": "table",
        "page_number": page_number,
        "bbox": {
            "x0": 72.0,
            "y0": 300.0,
            "x1": 540.0,
            "y1": 520.0,
        },
        "table": {
            "num_rows": 2,
            "num_cols": 2,
            "cells": [
                {
                    "text": "Header",
                    "row_start": 0,
                    "row_end": 1,
                    "col_start": 0,
                    "col_end": 1,
                    "row_span": 1,
                    "col_span": 1,
                    "column_header": True,
                    "row_header": False,
                    "bbox": {
                        "x0": 72.0,
                        "y0": 480.0,
                        "x1": 180.0,
                        "y1": 520.0,
                    },
                }
            ],
        },
    }


def formula_block_dict(page_number: int = 1, formula_index: int = 1) -> dict:
    return {
        "id": f"p{page_number}_f{formula_index}",
        "kind": "formula",
        "page_number": page_number,
        "bbox": {
            "x0": 180.0,
            "y0": 420.0,
            "x1": 432.0,
            "y1": 456.0,
        },
        "formula": {
            "text": "E=mc^2",
            "formula_type": "display",
        },
        "translatable": False,
    }


def minimal_layout_dict(page_count: int = 1) -> dict:
    pages = []
    for page_number in range(1, page_count + 1):
        pages.append(
            {
                "page_number": page_number,
                "width": 612.0,
                "height": 792.0,
                "rotation": 0,
                "blocks": [
                    text_block_dict(page_number),
                    image_block_dict(page_number),
                ],
                "warnings": [],
            }
        )

    return {
        "schema_version": "1.0",
        "source_file": "sample.pdf",
        "coordinate_system": {"unit": "pt", "origin": "bottom-left"},
        "pages": pages,
    }


def layout_dict_with_all_block_kinds(page_count: int = 1) -> dict:
    data = minimal_layout_dict(page_count=page_count)
    for page in data["pages"]:
        page_number = page["page_number"]
        page["blocks"].extend(
            [
                table_block_dict(page_number),
                formula_block_dict(page_number),
            ]
        )
    return data
