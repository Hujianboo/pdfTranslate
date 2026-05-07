import base64

from pdftranslate.layout_io import layout_config_from_dict
from pdftranslate.pdf_renderer import (
    DEFAULT_TEXT_FONT_SIZE,
    DrawCommand,
    MIN_TEXT_FONT_SIZE,
    MAX_SEED_FONT_SIZE,
    RenderOptions,
    build_render_plan,
    render_layout_pdf,
    missing_translations_for_layout,
    _draw_text_in_box,
    _execute_command,
)
from tests.fixtures import layout_dict_with_all_block_kinds, minimal_layout_dict


_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class _FakePdf:
    def __init__(self):
        self.drawn_strings = []
        self.font_calls = []
        self.fill_colors = []

    def drawString(self, x, y, text):
        self.drawn_strings.append((x, y, text))

    def setFont(self, font_name, font_size):
        self.font_calls.append((font_name, font_size))

    def setFillColor(self, color):
        self.fill_colors.append(color)


def _only_text_command(config, options=None):
    plan = build_render_plan(config, options)
    text_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "text"
    ]
    assert len(text_commands) == 1
    return text_commands[0]


def test_text_block_bbox_maps_to_text_draw_command():
    config = layout_config_from_dict(minimal_layout_dict())

    plan = build_render_plan(config)

    text_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "text"
    ]
    assert len(text_commands) == 1
    command = text_commands[0]
    assert command.block_id == "p1_b1"
    assert command.x == 72.0
    assert command.y == 120.0
    assert command.width == 108.0
    assert command.height == 24.0
    assert command.text == "Original text"


def test_translated_text_is_wrapped_into_fit_lines_within_bbox_width():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["bbox"]["x1"] = 112.0
    data["pages"][0]["blocks"][0]["bbox"]["y1"] = 220.0
    data["pages"][0]["blocks"][0]["translated_text"] = "这是第一句。这是第二句。"
    config = layout_config_from_dict(data)

    command = _only_text_command(config)

    assert len(command.lines) > 1
    assert all(
        command.estimate_text_width(line) <= command.width
        for line in command.lines
    )


def test_translated_text_takes_priority_over_original_text():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["translated_text"] = "译文"
    config = layout_config_from_dict(data)

    plan = build_render_plan(config, RenderOptions(sample_text="zh"))

    text_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "text"
    ]
    assert text_commands[0].text == "译文"


def test_translated_text_reduces_font_size_when_bbox_height_is_short():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["bbox"] = {
        "x0": 72.0,
        "y0": 120.0,
        "x1": 132.0,
        "y1": 138.0,
    }
    data["pages"][0]["blocks"][0]["translated_text"] = "中文内容中文内容中文内容"
    config = layout_config_from_dict(data)

    command = _only_text_command(config)

    assert command.font_size < DEFAULT_TEXT_FONT_SIZE


def test_fitting_translated_text_relaxes_above_default_when_bbox_is_spacious():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["bbox"]["x1"] = 260.0
    data["pages"][0]["blocks"][0]["bbox"]["y1"] = 180.0
    data["pages"][0]["blocks"][0]["translated_text"] = "可读译文"
    config = layout_config_from_dict(data)

    command = _only_text_command(config)

    assert command.overflow is False
    assert MIN_TEXT_FONT_SIZE <= command.font_size <= MAX_SEED_FONT_SIZE
    assert command.font_size >= DEFAULT_TEXT_FONT_SIZE


def test_heading_scale_short_text_bbox_gains_larger_than_default_font():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["text"] = "Attention Is All You Need"
    data["pages"][0]["blocks"][0]["bbox"] = {
        "x0": 72.0,
        "y0": 600.0,
        "x1": 540.0,
        "y1": 630.0,
    }
    config = layout_config_from_dict(data)

    command = _only_text_command(config)

    assert command.font_size >= DEFAULT_TEXT_FONT_SIZE + 2.5


def test_text_style_font_size_color_and_font_are_carried_to_draw_command():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["text"] = "Attention Is All You Need"
    data["pages"][0]["blocks"][0]["bbox"] = {
        "x0": 210.61,
        "y0": 626.36,
        "x1": 399.89,
        "y1": 642.75,
    }
    data["pages"][0]["blocks"][0]["style"] = {
        "font_name": "NimbusRomNo9L-Medi",
        "font_size": 17.2154,
        "color": "#808080",
        "rotation": 0,
    }
    config = layout_config_from_dict(data)

    command = _only_text_command(config)

    assert command.font_size == 17.2154
    assert command.font_name == "NimbusRomNo9L-Medi"
    assert command.color == "#808080"


def test_execute_text_command_uses_mapped_font_and_style_color():
    pdf = _FakePdf()
    command = DrawCommand(
        kind="text",
        block_id="p1_b1",
        x=10.0,
        y=20.0,
        width=200.0,
        height=30.0,
        text="Styled text",
        lines=("Styled text",),
        font_size=12.5,
        line_height=14.0,
        font_name="NimbusRomNo9L-Medi",
        color="#808080",
    )

    _execute_command(pdf, command)

    assert pdf.font_calls[0] == ("Times-Bold", 12.5)
    assert pdf.fill_colors


def test_tiny_bbox_never_uses_font_size_below_minimum():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["bbox"] = {
        "x0": 72.0,
        "y0": 120.0,
        "x1": 73.0,
        "y1": 121.0,
    }
    data["pages"][0]["blocks"][0]["translated_text"] = "非常小的文本框"
    config = layout_config_from_dict(data)

    command = _only_text_command(config)

    assert command.font_size >= MIN_TEXT_FONT_SIZE
    assert command.font_size > 0


def test_unfit_translated_text_marks_overflow_and_keeps_block_id():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["bbox"] = {
        "x0": 72.0,
        "y0": 120.0,
        "x1": 112.0,
        "y1": 130.0,
    }
    data["pages"][0]["blocks"][0]["translated_text"] = (
        "这是一段非常长的中文译文，需要很多很多行才能放进文本框。"
    )
    config = layout_config_from_dict(data)

    command = _only_text_command(config)

    assert command.block_id == "p1_b1"
    assert command.overflow is True


def test_narrow_text_block_does_not_use_full_chinese_translation():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["text"] = "arXiv:1706.03762v7"
    data["pages"][0]["blocks"][0]["bbox"] = {
        "x0": 17.0,
        "y0": 236.0,
        "x1": 35.0,
        "y1": 627.0,
    }
    data["pages"][0]["blocks"][0]["translated_text"] = "这是会被挤成竖排的中文译文"
    config = layout_config_from_dict(data)

    command = _only_text_command(config)

    assert command.text != "这是会被挤成竖排的中文译文"
    assert command.text.startswith("arXiv")


def test_narrow_text_block_records_fit_reason():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["bbox"]["x1"] = 90.0
    data["pages"][0]["blocks"][0]["translated_text"] = "窄块中文译文"
    config = layout_config_from_dict(data)

    command = _only_text_command(config)

    assert command.fit_reason == "narrow-block-source-text"


def test_draw_text_in_box_uses_precomputed_fit_lines():
    pdf = _FakePdf()
    command = DrawCommand(
        kind="text",
        block_id="p1_b1",
        x=10.0,
        y=20.0,
        width=12.0,
        height=100.0,
        text="this text would be rewrapped without precomputed lines",
        lines=("预计算第一行", "预计算第二行"),
        font_size=10.0,
        line_height=12.0,
    )

    _draw_text_in_box(pdf, command)

    assert [drawn[2] for drawn in pdf.drawn_strings] == [
        "预计算第一行",
        "预计算第二行",
    ]


def test_missing_translations_for_layout_returns_translatable_text_block_ids():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"].append(
        {
            "id": "p1_b2",
            "kind": "text",
            "page_number": 1,
            "text": "Needs translation",
            "bbox": {
                "x0": 72.0,
                "y0": 160.0,
                "x1": 180.0,
                "y1": 184.0,
            },
            "style": {
                "font_name": None,
                "font_size": None,
                "color": None,
                "rotation": 0,
            },
            "translatable": True,
        }
    )
    data["pages"][0]["blocks"].append(
        {
            "id": "p1_b3",
            "kind": "text",
            "page_number": 1,
            "text": "Already translated",
            "bbox": {
                "x0": 72.0,
                "y0": 200.0,
                "x1": 180.0,
                "y1": 224.0,
            },
            "style": {
                "font_name": None,
                "font_size": None,
                "color": None,
                "rotation": 0,
            },
            "translatable": True,
            "translated_text": "已有译文",
        }
    )
    data["pages"][0]["blocks"].append(
        {
            "id": "p1_b4",
            "kind": "text",
            "page_number": 1,
            "text": "Do not translate",
            "bbox": {
                "x0": 72.0,
                "y0": 240.0,
                "x1": 180.0,
                "y1": 264.0,
            },
            "style": {
                "font_name": None,
                "font_size": None,
                "color": None,
                "rotation": 0,
            },
            "translatable": False,
        }
    )
    config = layout_config_from_dict(data)

    assert missing_translations_for_layout(config) == ["p1_b1", "p1_b2"]


def test_image_block_bbox_maps_to_placeholder_draw_command():
    config = layout_config_from_dict(minimal_layout_dict())

    plan = build_render_plan(config)

    image_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "image_placeholder"
    ]
    assert len(image_commands) == 1
    command = image_commands[0]
    assert command.block_id == "p1_i1"
    assert command.image_ref == "p1_i1"
    assert command.x == 200.0
    assert command.y == 240.0
    assert command.width == 100.0
    assert command.height == 100.0


def test_image_asset_path_maps_to_real_image_draw_command(tmp_path):
    image_path = tmp_path / "p1_i1.png"
    image_path.write_bytes(b"fake-image")
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][1]["image"]["asset_path"] = str(image_path)
    config = layout_config_from_dict(data)

    plan = build_render_plan(config)

    image_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "image_asset"
    ]
    assert len(image_commands) == 1
    assert image_commands[0].image_path == str(image_path)


def test_relative_image_asset_path_resolves_against_asset_base_dir(tmp_path):
    image_path = tmp_path / "images" / "p1_i1.png"
    image_path.parent.mkdir()
    image_path.write_bytes(b"fake-image")
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][1]["image"]["asset_path"] = "images/p1_i1.png"
    config = layout_config_from_dict(data)

    plan = build_render_plan(config, RenderOptions(asset_base_dir=tmp_path))

    image_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "image_asset"
    ]
    assert len(image_commands) == 1
    assert image_commands[0].image_path == str(image_path)


def test_nonexistent_image_asset_path_falls_back_to_placeholder(tmp_path):
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][1]["image"]["asset_path"] = str(
        tmp_path / "missing.png"
    )
    config = layout_config_from_dict(data)

    plan = build_render_plan(config)

    image_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "image_placeholder"
    ]
    assert len(image_commands) == 1
    assert image_commands[0].block_id == "p1_i1"


def test_debug_boxes_generate_box_and_label_for_each_block():
    config = layout_config_from_dict(minimal_layout_dict())

    plan = build_render_plan(config, RenderOptions(debug_boxes=True))

    commands = [command for page in plan.pages for command in page.commands]
    debug_boxes = [command for command in commands if command.kind == "debug_box"]
    debug_labels = [command for command in commands if command.kind == "debug_label"]

    assert [command.block_id for command in debug_boxes] == ["p1_b1", "p1_i1"]
    assert [command.block_id for command in debug_labels] == ["p1_b1", "p1_i1"]
    assert [command.text for command in debug_labels] == ["p1_b1", "p1_i1"]


def test_table_block_bbox_maps_to_table_placeholder_command():
    config = layout_config_from_dict(layout_dict_with_all_block_kinds())

    plan = build_render_plan(config)

    table_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "table_placeholder"
    ]
    assert len(table_commands) == 1
    command = table_commands[0]
    assert command.block_id == "p1_t1"
    assert command.x == 72.0
    assert command.y == 300.0
    assert command.width == 468.0
    assert command.height == 220.0


def test_table_asset_path_maps_to_real_image_draw_command(tmp_path):
    image_path = tmp_path / "p1_t1.png"
    image_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    data = layout_dict_with_all_block_kinds()
    data["pages"][0]["blocks"][2]["table"]["asset_path"] = str(image_path)
    config = layout_config_from_dict(data)

    plan = build_render_plan(config)

    image_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "image_asset" and command.block_id == "p1_t1"
    ]
    assert len(image_commands) == 1
    assert image_commands[0].image_path == str(image_path)


def test_formula_block_bbox_maps_to_formula_placeholder_command():
    config = layout_config_from_dict(layout_dict_with_all_block_kinds())

    plan = build_render_plan(config)

    formula_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "formula_placeholder"
    ]
    assert len(formula_commands) == 1
    command = formula_commands[0]
    assert command.block_id == "p1_f1"
    assert command.x == 180.0
    assert command.y == 420.0
    assert command.width == 252.0
    assert command.height == 36.0


def test_formula_asset_path_maps_to_real_image_draw_command(tmp_path):
    image_path = tmp_path / "p1_f1.png"
    image_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    data = layout_dict_with_all_block_kinds()
    data["pages"][0]["blocks"][3]["formula"]["asset_path"] = str(image_path)
    config = layout_config_from_dict(data)

    plan = build_render_plan(config)

    image_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "image_asset" and command.block_id == "p1_f1"
    ]
    assert len(image_commands) == 1
    assert image_commands[0].image_path == str(image_path)


def test_debug_boxes_generate_box_and_label_for_all_block_kinds():
    config = layout_config_from_dict(layout_dict_with_all_block_kinds())

    plan = build_render_plan(config, RenderOptions(debug_boxes=True))

    commands = [command for page in plan.pages for command in page.commands]
    debug_boxes = [command for command in commands if command.kind == "debug_box"]
    debug_labels = [command for command in commands if command.kind == "debug_label"]

    assert [command.block_id for command in debug_boxes] == [
        "p1_b1",
        "p1_i1",
        "p1_t1",
        "p1_f1",
    ]
    assert [command.text for command in debug_labels] == [
        "p1_b1",
        "p1_i1",
        "p1_t1",
        "p1_f1",
    ]


def test_zh_sample_text_replaces_original_text_but_keeps_block_id():
    config = layout_config_from_dict(minimal_layout_dict())

    plan = build_render_plan(config, RenderOptions(sample_text="zh"))

    text_commands = [
        command
        for page in plan.pages
        for command in page.commands
        if command.kind == "text"
    ]
    assert len(text_commands) == 1
    assert text_commands[0].block_id == "p1_b1"
    assert text_commands[0].text != "Original text"
    assert any("\u4e00" <= character <= "\u9fff" for character in text_commands[0].text)


def test_render_layout_pdf_writes_pdf_with_matching_page_count(tmp_path):
    from pypdf import PdfReader

    config = layout_config_from_dict(minimal_layout_dict(page_count=2))
    output_path = tmp_path / "rebuilt.pdf"

    render_layout_pdf(config, output_path)

    reader = PdfReader(output_path)
    assert len(reader.pages) == 2


def test_render_layout_pdf_writes_matching_media_box_size(tmp_path):
    from pypdf import PdfReader

    config = layout_config_from_dict(minimal_layout_dict())
    output_path = tmp_path / "rebuilt.pdf"

    render_layout_pdf(config, output_path)

    page = PdfReader(output_path).pages[0]
    assert float(page.mediabox.width) == 612.0
    assert float(page.mediabox.height) == 792.0


def test_render_layout_pdf_writes_text_placeholder_and_debug_content(tmp_path):
    from pypdf import PdfReader

    config = layout_config_from_dict(minimal_layout_dict())
    output_path = tmp_path / "rebuilt-debug.pdf"

    render_layout_pdf(
        config,
        output_path,
        RenderOptions(sample_text="zh", debug_boxes=True),
    )

    page_text = PdfReader(output_path).pages[0].extract_text()
    assert output_path.stat().st_size > 0
    assert "p1_b1" in page_text
    assert "p1_i1" in page_text
    assert "p1_i1" in page_text


def test_render_layout_pdf_writes_image_resource_for_asset_path(tmp_path):
    from pypdf import PdfReader

    image_path = tmp_path / "p1_i1.png"
    image_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][1]["image"]["asset_path"] = str(image_path)
    config = layout_config_from_dict(data)
    output_path = tmp_path / "rebuilt-with-image.pdf"

    render_layout_pdf(config, output_path)

    resources = PdfReader(output_path).pages[0].get("/Resources")
    assert resources is not None
    assert "/XObject" in resources


def test_render_layout_pdf_writes_table_placeholder_id(tmp_path):
    from pypdf import PdfReader

    config = layout_config_from_dict(layout_dict_with_all_block_kinds())
    output_path = tmp_path / "rebuilt-table.pdf"

    render_layout_pdf(config, output_path)

    page_text = PdfReader(output_path).pages[0].extract_text()
    assert "p1_t1" in page_text


def test_render_layout_pdf_writes_table_image_resource_for_asset_path(tmp_path):
    from pypdf import PdfReader

    image_path = tmp_path / "p1_t1.png"
    image_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    data = layout_dict_with_all_block_kinds()
    data["pages"][0]["blocks"][2]["table"]["asset_path"] = str(image_path)
    config = layout_config_from_dict(data)
    output_path = tmp_path / "rebuilt-table-image.pdf"

    render_layout_pdf(config, output_path)

    resources = PdfReader(output_path).pages[0].get("/Resources")
    assert resources is not None
    assert "/XObject" in resources


def test_render_layout_pdf_writes_formula_placeholder_id(tmp_path):
    from pypdf import PdfReader

    config = layout_config_from_dict(layout_dict_with_all_block_kinds())
    output_path = tmp_path / "rebuilt-formula.pdf"

    render_layout_pdf(config, output_path)

    page_text = PdfReader(output_path).pages[0].extract_text()
    assert "p1_f1" in page_text


def test_render_layout_pdf_writes_formula_image_resource_for_asset_path(tmp_path):
    from pypdf import PdfReader

    image_path = tmp_path / "p1_f1.png"
    image_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    data = layout_dict_with_all_block_kinds()
    data["pages"][0]["blocks"][3]["formula"]["asset_path"] = str(image_path)
    config = layout_config_from_dict(data)
    output_path = tmp_path / "rebuilt-formula-image.pdf"

    render_layout_pdf(config, output_path)

    resources = PdfReader(output_path).pages[0].get("/Resources")
    assert resources is not None
    assert "/XObject" in resources
