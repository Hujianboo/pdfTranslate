import base64

from pdftranslate.layout_io import layout_config_from_dict
from pdftranslate.pdf_renderer import RenderOptions, build_render_plan, render_layout_pdf
from tests.fixtures import minimal_layout_dict


_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


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
