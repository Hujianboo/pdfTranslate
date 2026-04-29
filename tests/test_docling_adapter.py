from pathlib import Path
from types import SimpleNamespace

from pdftranslate.docling_adapter import parse_pdf_layout


class FormulaItem(SimpleNamespace):
    pass


def _pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_text_pdf(path: Path, page_texts: list[str]) -> None:
    objects: list[str] = []

    def add_object(body: str) -> int:
        objects.append(body)
        return len(objects)

    catalog_id = add_object("<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object("PLACEHOLDER")
    font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []

    for text in page_texts:
        content = f"BT /F1 24 Tf 72 720 Td ({_pdf_text(text)}) Tj ET"
        content_id = add_object(
            f"<< /Length {len(content.encode('latin-1'))} >>\n"
            f"stream\n{content}\nendstream"
        )
        page_id = add_object(
            "<< /Type /Page "
            f"/Parent {pages_id} 0 R "
            "/MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    objects[pages_id - 1] = (
        f"<< /Type /Pages /Count {len(page_ids)} "
        f"/Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] >>"
    )

    chunks = ["%PDF-1.4\n"]
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(sum(len(chunk.encode("latin-1")) for chunk in chunks))
        chunks.append(f"{index} 0 obj\n{body}\nendobj\n")

    xref_offset = sum(len(chunk.encode("latin-1")) for chunk in chunks)
    chunks.append(f"xref\n0 {len(objects) + 1}\n")
    chunks.append("0000000000 65535 f \n")
    for offset in offsets[1:]:
        chunks.append(f"{offset:010d} 00000 n \n")
    chunks.append(
        "trailer\n"
        f"<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        "startxref\n"
        f"{xref_offset}\n"
        "%%EOF\n"
    )

    path.write_bytes("".join(chunks).encode("latin-1"))


def _page(width: float = 612.0, height: float = 792.0) -> SimpleNamespace:
    return SimpleNamespace(size=SimpleNamespace(width=width, height=height))


def _prov(
    page_no: int = 1,
    l: float = 72.0,
    b: float = 120.0,
    r: float = 172.0,
    t: float = 220.0,
) -> SimpleNamespace:
    return SimpleNamespace(
        page_no=page_no,
        bbox=SimpleNamespace(l=l, b=b, r=r, t=t),
    )


def _table_cell(**overrides) -> SimpleNamespace:
    values = {
        "text": "Header",
        "start_row_offset_idx": 0,
        "end_row_offset_idx": 1,
        "start_col_offset_idx": 0,
        "end_col_offset_idx": 1,
        "row_span": 1,
        "col_span": 1,
        "column_header": True,
        "row_header": False,
        "bbox": SimpleNamespace(l=72.0, b=180.0, r=172.0, t=220.0),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _table_item(page_no: int = 1, **overrides) -> SimpleNamespace:
    values = {
        "prov": [_prov(page_no=page_no, l=72.0, b=300.0, r=540.0, t=520.0)],
        "data": SimpleNamespace(
            num_rows=2,
            num_cols=2,
            table_cells=[_table_cell()],
        ),
        "self_ref": f"#/tables/{page_no}",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _formula_item(page_no: int = 1, **overrides) -> FormulaItem:
    values = {
        "text": "E=mc^2",
        "orig": "",
        "label": "formula",
        "self_ref": f"#/texts/{page_no}",
        "prov": [_prov(page_no=page_no, l=180.0, b=420.0, r=432.0, t=456.0)],
    }
    values.update(overrides)
    return FormulaItem(**values)


def test_parse_pdf_layout_preserves_page_order(tmp_path):
    pdf_path = tmp_path / "two-pages.pdf"
    write_text_pdf(pdf_path, ["First page text", "Second page text"])

    config = parse_pdf_layout(pdf_path)

    assert [page.page_number for page in config.pages] == [1, 2]


def test_parse_pdf_layout_outputs_positive_page_size(tmp_path):
    pdf_path = tmp_path / "one-page.pdf"
    write_text_pdf(pdf_path, ["Page with size"])

    config = parse_pdf_layout(pdf_path)

    assert config.pages
    for page in config.pages:
        assert isinstance(page.width, float)
        assert isinstance(page.height, float)
        assert page.width > 0
        assert page.height > 0


def test_parse_pdf_layout_maps_docling_text_items(tmp_path):
    pdf_path = tmp_path / "text-block.pdf"
    write_text_pdf(pdf_path, ["Text block mapping"])

    config = parse_pdf_layout(pdf_path)

    text_blocks = [
        block
        for page in config.pages
        for block in page.blocks
        if block.kind == "text"
    ]
    assert text_blocks

    data = text_blocks[0].to_dict()
    assert data["kind"] == "text"
    assert data["text"] == "Text block mapping"
    assert data["bbox"].keys() == {"x0", "y0", "x1", "y1"}
    assert data["style"] == {
        "font_name": None,
        "font_size": None,
        "color": None,
        "rotation": 0,
    }
    assert data["translatable"] is True


def test_parse_pdf_layout_generates_stable_text_ids(tmp_path):
    pdf_path = tmp_path / "stable-text.pdf"
    write_text_pdf(pdf_path, ["First stable text", "Second stable text"])

    first = parse_pdf_layout(pdf_path)
    second = parse_pdf_layout(pdf_path)

    first_ids = [
        block.id
        for page in first.pages
        for block in page.blocks
        if block.kind == "text"
    ]
    second_ids = [
        block.id
        for page in second.pages
        for block in page.blocks
        if block.kind == "text"
    ]

    assert first_ids == second_ids
    assert first_ids == ["p1_b1", "p2_b1"]


def test_docling_picture_items_map_to_image_blocks():
    from pdftranslate.docling_adapter import _layout_from_docling_document

    document = SimpleNamespace(
        pages={
            1: SimpleNamespace(
                size=SimpleNamespace(width=612.0, height=792.0),
            )
        },
        texts=[],
        pictures=[
            SimpleNamespace(
                prov=[
                    SimpleNamespace(
                        page_no=1,
                        bbox=SimpleNamespace(l=72.0, b=120.0, r=172.0, t=220.0),
                    )
                ],
            )
        ],
    )

    config = _layout_from_docling_document(document, source_file="fake.pdf")

    image_blocks = [
        block
        for page in config.pages
        for block in page.blocks
        if block.kind == "image"
    ]
    assert image_blocks

    data = image_blocks[0].to_dict()
    assert data["kind"] == "image"
    assert data["bbox"] == {"x0": 72.0, "y0": 120.0, "x1": 172.0, "y1": 220.0}
    assert data["image"] == {
        "ref": "p1_i1",
        "width": 100.0,
        "height": 100.0,
        "mime_type": None,
    }


def test_docling_picture_items_generate_stable_image_ids():
    from pdftranslate.docling_adapter import _layout_from_docling_document

    def make_document():
        return SimpleNamespace(
            pages={
                1: SimpleNamespace(size=SimpleNamespace(width=612.0, height=792.0)),
                2: SimpleNamespace(size=SimpleNamespace(width=612.0, height=792.0)),
            },
            texts=[],
            pictures=[
                SimpleNamespace(
                    prov=[
                        SimpleNamespace(
                            page_no=2,
                            bbox=SimpleNamespace(l=72.0, b=120.0, r=172.0, t=220.0),
                        )
                    ],
                ),
                SimpleNamespace(
                    prov=[
                        SimpleNamespace(
                            page_no=1,
                            bbox=SimpleNamespace(l=72.0, b=120.0, r=172.0, t=220.0),
                        )
                    ],
                ),
            ],
        )

    first = _layout_from_docling_document(make_document(), source_file="fake.pdf")
    second = _layout_from_docling_document(make_document(), source_file="fake.pdf")

    first_ids = [
        block.id
        for page in first.pages
        for block in page.blocks
        if block.kind == "image"
    ]
    second_ids = [
        block.id
        for page in second.pages
        for block in page.blocks
        if block.kind == "image"
    ]

    assert first_ids == second_ids
    assert first_ids == ["p1_i1", "p2_i1"]


def test_docling_pdf_pipeline_defaults_to_ocr_disabled():
    from pdftranslate.docling_adapter import build_pdf_pipeline_options

    options = build_pdf_pipeline_options()

    assert options.do_ocr is False


def test_docling_table_items_map_to_table_blocks_with_bbox():
    from pdftranslate.docling_adapter import _layout_from_docling_document

    document = SimpleNamespace(
        pages={1: _page()},
        texts=[],
        pictures=[],
        tables=[_table_item()],
    )

    config = _layout_from_docling_document(document, source_file="fake.pdf")

    table_blocks = [
        block
        for page in config.pages
        for block in page.blocks
        if block.kind == "table"
    ]
    assert len(table_blocks) == 1
    data = table_blocks[0].to_dict()
    assert data["id"] == "p1_t1"
    assert data["bbox"] == {"x0": 72.0, "y0": 300.0, "x1": 540.0, "y1": 520.0}
    assert data["table"]["num_rows"] == 2
    assert data["table"]["num_cols"] == 2


def test_docling_table_items_generate_stable_ids_by_page_and_position():
    from pdftranslate.docling_adapter import _layout_from_docling_document

    def make_document():
        return SimpleNamespace(
            pages={1: _page(), 2: _page()},
            texts=[],
            pictures=[],
            tables=[
                _table_item(page_no=2),
                _table_item(page_no=1),
            ],
        )

    first = _layout_from_docling_document(make_document(), source_file="fake.pdf")
    second = _layout_from_docling_document(make_document(), source_file="fake.pdf")

    first_ids = [
        block.id
        for page in first.pages
        for block in page.blocks
        if block.kind == "table"
    ]
    second_ids = [
        block.id
        for page in second.pages
        for block in page.blocks
        if block.kind == "table"
    ]
    assert first_ids == second_ids
    assert first_ids == ["p1_t1", "p2_t1"]


def test_docling_table_cell_fields_and_header_flags_map_to_layout_cells():
    from pdftranslate.docling_adapter import _layout_from_docling_document

    document = SimpleNamespace(
        pages={1: _page()},
        texts=[],
        pictures=[],
        tables=[
            _table_item(
                data=SimpleNamespace(
                    num_rows=3,
                    num_cols=4,
                    table_cells=[
                        _table_cell(
                            text="Total",
                            start_row_offset_idx=1,
                            end_row_offset_idx=3,
                            start_col_offset_idx=2,
                            end_col_offset_idx=4,
                            row_span=2,
                            col_span=2,
                            column_header=False,
                            row_header=True,
                        )
                    ],
                )
            )
        ],
    )

    config = _layout_from_docling_document(document, source_file="fake.pdf")
    cell = next(
        block.table.cells[0]
        for page in config.pages
        for block in page.blocks
        if block.kind == "table"
    )

    assert cell.text == "Total"
    assert cell.row_start == 1
    assert cell.row_end == 3
    assert cell.col_start == 2
    assert cell.col_end == 4
    assert cell.row_span == 2
    assert cell.col_span == 2
    assert cell.column_header is False
    assert cell.row_header is True
    assert cell.bbox is not None


def test_docling_formula_items_map_to_formula_blocks_not_translatable():
    from pdftranslate.docling_adapter import _layout_from_docling_document

    document = SimpleNamespace(
        pages={1: _page()},
        texts=[_formula_item()],
        pictures=[],
        tables=[],
    )

    config = _layout_from_docling_document(document, source_file="fake.pdf")

    formula_blocks = [
        block
        for page in config.pages
        for block in page.blocks
        if block.kind == "formula"
    ]
    assert len(formula_blocks) == 1
    data = formula_blocks[0].to_dict()
    assert data["id"] == "p1_f1"
    assert data["formula"] == {"text": "E=mc^2", "ref": "#/texts/1"}
    assert data["translatable"] is False


def test_docling_formula_items_generate_stable_ids_by_page_and_position():
    from pdftranslate.docling_adapter import _layout_from_docling_document

    def make_document():
        return SimpleNamespace(
            pages={1: _page(), 2: _page()},
            texts=[
                _formula_item(page_no=2),
                _formula_item(page_no=1),
            ],
            pictures=[],
            tables=[],
        )

    first = _layout_from_docling_document(make_document(), source_file="fake.pdf")
    second = _layout_from_docling_document(make_document(), source_file="fake.pdf")

    first_ids = [
        block.id
        for page in first.pages
        for block in page.blocks
        if block.kind == "formula"
    ]
    second_ids = [
        block.id
        for page in second.pages
        for block in page.blocks
        if block.kind == "formula"
    ]
    assert first_ids == second_ids
    assert first_ids == ["p1_f1", "p2_f1"]


def test_docling_formula_items_are_not_also_text_blocks():
    from pdftranslate.docling_adapter import _layout_from_docling_document

    document = SimpleNamespace(
        pages={1: _page()},
        texts=[
            _formula_item(),
            SimpleNamespace(text="Normal text", orig="", prov=[_prov(page_no=1)]),
        ],
        pictures=[],
        tables=[],
    )

    config = _layout_from_docling_document(document, source_file="fake.pdf")

    text_blocks = [
        block
        for page in config.pages
        for block in page.blocks
        if block.kind == "text"
    ]
    formula_blocks = [
        block
        for page in config.pages
        for block in page.blocks
        if block.kind == "formula"
    ]
    assert [block.text for block in text_blocks] == ["Normal text"]
    assert [block.formula.text for block in formula_blocks] == ["E=mc^2"]


def test_docling_formula_fallback_writes_non_empty_text_or_ref():
    from pdftranslate.docling_adapter import _layout_from_docling_document

    document = SimpleNamespace(
        pages={1: _page()},
        texts=[
            _formula_item(text="", orig=""),
            _formula_item(page_no=1, text="", orig="", self_ref="#/texts/formula-2"),
        ],
        pictures=[],
        tables=[],
    )

    config = _layout_from_docling_document(document, source_file="fake.pdf")

    formulas = [
        block.formula.to_dict()
        for page in config.pages
        for block in page.blocks
        if block.kind == "formula"
    ]
    assert formulas
    for formula in formulas:
        assert formula.get("text") or formula.get("ref")
