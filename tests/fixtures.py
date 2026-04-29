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
                    {
                        "id": f"p{page_number}_b1",
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
                    },
                    {
                        "id": f"p{page_number}_i1",
                        "kind": "image",
                        "page_number": page_number,
                        "bbox": {
                            "x0": 200.0,
                            "y0": 240.0,
                            "x1": 300.0,
                            "y1": 340.0,
                        },
                        "image": {
                            "ref": f"p{page_number}_i1",
                            "width": 100.0,
                            "height": 100.0,
                            "mime_type": None,
                        },
                    },
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
