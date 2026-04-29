from pdftranslate.layout import ImageBlock, LayoutConfig, TextBlock
from pdftranslate.layout_io import layout_config_from_dict, load_layout_config
from tests.fixtures import minimal_layout_dict


def test_layout_config_from_dict_builds_pages_text_and_image_blocks():
    config = layout_config_from_dict(minimal_layout_dict())

    assert isinstance(config, LayoutConfig)
    assert config.source_file == "sample.pdf"
    assert config.coordinate_system == {"unit": "pt", "origin": "bottom-left"}
    assert len(config.pages) == 1
    page = config.pages[0]
    assert page.page_number == 1
    assert page.width == 612.0
    assert page.height == 792.0
    assert isinstance(page.blocks[0], TextBlock)
    assert page.blocks[0].id == "p1_b1"
    assert page.blocks[0].text == "Original text"
    assert isinstance(page.blocks[1], ImageBlock)
    assert page.blocks[1].id == "p1_i1"
    assert page.blocks[1].image.ref == "p1_i1"


def test_load_layout_config_reads_utf8_json_file(tmp_path):
    input_path = tmp_path / "sample.layout.json"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    config = load_layout_config(input_path)

    assert isinstance(config, LayoutConfig)
    assert config.source_file == "sample.pdf"
    assert config.pages[0].blocks[0].text == "Original text"


def test_layout_config_from_dict_reads_image_asset_path():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][1]["image"]["asset_path"] = (
        "output/assets/sample/images/p1_i1.png"
    )

    config = layout_config_from_dict(data)

    image_block = config.pages[0].blocks[1]
    assert isinstance(image_block, ImageBlock)
    assert image_block.image.asset_path == "output/assets/sample/images/p1_i1.png"


def test_layout_config_from_dict_round_trips_old_image_block_without_asset_path():
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][1]["image"].pop("asset_path", None)

    config = layout_config_from_dict(data)
    serialized = config.to_dict()

    image_block = config.pages[0].blocks[1]
    assert isinstance(image_block, ImageBlock)
    assert image_block.image.asset_path is None
    assert "asset_path" not in serialized["pages"][0]["blocks"][1]["image"]
