import base64
import json
from pathlib import Path

from pdftranslate.cli import main
from pdftranslate.layout_io import layout_config_from_dict
from pdftranslate.layout import (
    BBox,
    ImageBlock,
    ImageInfo,
    LayoutConfig,
    PageLayout,
    TextBlock,
)
from tests.fixtures import layout_dict_with_all_block_kinds, minimal_layout_dict


_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


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


def write_pdf_with_png(path: Path) -> None:
    from reportlab.pdfgen import canvas

    image_path = path.with_suffix(".png")
    image_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    pdf = canvas.Canvas(str(path), pagesize=(612.0, 792.0))
    pdf.drawImage(str(image_path), 200.0, 240.0, width=100.0, height=100.0)
    pdf.save()


def test_extract_command_creates_non_empty_markdown(tmp_path):
    output_path = tmp_path / "sample.md"

    exit_code = main(
        [
            "extract",
            "assets/1603.08767v1.pdf",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip()


def test_extract_command_rejects_missing_input(tmp_path, capsys):
    output_path = tmp_path / "missing.md"

    exit_code = main(
        [
            "extract",
            str(tmp_path / "does-not-exist.pdf"),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "not found" in captured.err
    assert not output_path.exists()


def test_parse_layout_command_creates_json_file(tmp_path, monkeypatch):
    input_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "layout.json"
    input_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    monkeypatch.setattr(
        "pdftranslate.docling_adapter.parse_pdf_layout",
        lambda path: layout_config_from_dict(minimal_layout_dict()),
    )

    exit_code = main(
        [
            "parse-layout",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8"))


def test_parse_layout_command_outputs_layout_schema_contract(tmp_path, monkeypatch):
    input_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "layout.json"
    input_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    monkeypatch.setattr(
        "pdftranslate.docling_adapter.parse_pdf_layout",
        lambda path: LayoutConfig(
            source_file=str(path),
            pages=[
                PageLayout(
                    page_number=1,
                    width=612.0,
                    height=792.0,
                    blocks=[
                        TextBlock(
                            id="p1_b1",
                            page_number=1,
                            text="Schema text",
                            bbox=BBox(x0=72.0, y0=120.0, x1=180.0, y1=144.0),
                        ),
                        ImageBlock(
                            id="p1_i1",
                            page_number=1,
                            bbox=BBox(x0=200.0, y0=240.0, x1=300.0, y1=340.0),
                            image=ImageInfo(ref="p1_i1", width=100.0, height=100.0),
                        ),
                    ],
                )
            ],
        ),
    )

    exit_code = main(
        [
            "parse-layout",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert data["schema_version"] == "1.0"
    assert data["coordinate_system"] == {"unit": "pt", "origin": "bottom-left"}
    assert data["source_file"] == str(input_path)
    assert data["pages"][0].keys() == {
        "page_number",
        "width",
        "height",
        "rotation",
        "blocks",
        "warnings",
    }
    assert {block["kind"] for block in data["pages"][0]["blocks"]} == {
        "text",
        "image",
    }
    for block in data["pages"][0]["blocks"]:
        assert {"id", "kind", "page_number", "bbox"}.issubset(block)
    text_block = data["pages"][0]["blocks"][0]
    image_block = data["pages"][0]["blocks"][1]
    assert {"text", "style", "translatable"}.issubset(text_block)
    assert {"ref", "width", "height", "mime_type"} == set(image_block["image"])


def test_parse_layout_command_outputs_table_and_formula_blocks(tmp_path, monkeypatch):
    input_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "layout.json"
    input_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    monkeypatch.setattr(
        "pdftranslate.docling_adapter.parse_pdf_layout",
        lambda path: layout_config_from_dict(layout_dict_with_all_block_kinds()),
    )

    exit_code = main(
        [
            "parse-layout",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    data = json.loads(output_path.read_text(encoding="utf-8"))
    blocks = data["pages"][0]["blocks"]
    table_block = next(block for block in blocks if block["kind"] == "table")
    formula_block = next(block for block in blocks if block["kind"] == "formula")
    assert exit_code == 0
    assert table_block["table"]["cells"][0]["text"] == "Header"
    assert formula_block["formula"]["text"] == "E=mc^2"
    assert formula_block["translatable"] is False


def test_render_layout_command_creates_non_empty_pdf(tmp_path):
    input_path = tmp_path / "sample.layout.json"
    output_path = tmp_path / "rebuilt.pdf"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "render-layout",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_render_layout_command_creates_pdf_from_translated_layout(tmp_path):
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["translated_text"] = "译文"
    input_path = tmp_path / "sample.translated.layout.json"
    output_path = tmp_path / "translated.pdf"
    input_path.write_text(
        layout_config_from_dict(data).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "render-layout",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_render_layout_require_translations_succeeds_when_complete(tmp_path):
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["translated_text"] = "译文"
    input_path = tmp_path / "complete.translated.layout.json"
    output_path = tmp_path / "complete.pdf"
    input_path.write_text(
        layout_config_from_dict(data).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "render-layout",
            str(input_path),
            "--output",
            str(output_path),
            "--require-translations",
        ]
    )

    assert exit_code == 0
    assert output_path.exists()


def test_render_layout_require_translations_fails_with_missing_block_id(
    tmp_path,
    capsys,
):
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["id"] = "p1_b2"
    input_path = tmp_path / "incomplete.layout.json"
    output_path = tmp_path / "incomplete.pdf"
    input_path.write_text(
        layout_config_from_dict(data).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "render-layout",
            str(input_path),
            "--output",
            str(output_path),
            "--require-translations",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "p1_b2" in captured.err
    assert not output_path.exists()


def test_render_layout_default_mode_allows_partially_translated_layout(tmp_path):
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["id"] = "p1_b2"
    input_path = tmp_path / "partial.layout.json"
    output_path = tmp_path / "partial.pdf"
    input_path.write_text(
        layout_config_from_dict(data).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "render-layout",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_render_layout_command_resolves_assets_relative_to_layout_file(tmp_path):
    layout_dir = tmp_path / "layout"
    image_dir = layout_dir / "images"
    image_dir.mkdir(parents=True)
    image_path = image_dir / "p1_i1.png"
    image_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    input_path = layout_dir / "sample.layout.json"
    output_path = tmp_path / "rebuilt.pdf"
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][1]["image"]["asset_path"] = "images/p1_i1.png"
    input_path.write_text(
        layout_config_from_dict(data).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "render-layout",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_render_layout_command_passes_sample_text_and_debug_options(
    tmp_path,
    monkeypatch,
):
    input_path = tmp_path / "sample.layout.json"
    output_path = tmp_path / "rebuilt.pdf"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )
    captured = {}

    def fake_render_layout_pdf(config, output, options=None):
        captured["source_file"] = config.source_file
        captured["output"] = output
        captured["sample_text"] = options.sample_text
        captured["debug_boxes"] = options.debug_boxes
        Path(output).write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr(
        "pdftranslate.pdf_renderer.render_layout_pdf",
        fake_render_layout_pdf,
    )

    exit_code = main(
        [
            "render-layout",
            str(input_path),
            "--output",
            str(output_path),
            "--sample-text",
            "zh",
            "--debug-boxes",
        ]
    )

    assert exit_code == 0
    assert captured == {
        "source_file": "sample.pdf",
        "output": output_path,
        "sample_text": "zh",
        "debug_boxes": True,
    }


def test_translate_layout_command_with_mock_provider_writes_translated_json(tmp_path):
    input_path = tmp_path / "sample.layout.json"
    output_path = tmp_path / "sample.translated.layout.json"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "translate-layout",
            str(input_path),
            "--output",
            str(output_path),
            "--provider",
            "mock",
        ]
    )

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert data["pages"][0]["blocks"][0]["translated_text"] == "[zh] Original text"
    assert "translated_text" not in data["pages"][0]["blocks"][1]


def test_translate_layout_command_defaults_target_language_to_zh(tmp_path):
    input_path = tmp_path / "sample.layout.json"
    output_path = tmp_path / "sample.translated.layout.json"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "translate-layout",
            str(input_path),
            "--output",
            str(output_path),
            "--provider",
            "mock",
        ]
    )

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert data["pages"][0]["blocks"][0]["translated_text"].startswith("[zh]")


def test_translate_layout_command_openai_without_key_exits_nonzero(
    tmp_path,
    capsys,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    input_path = tmp_path / "sample.layout.json"
    output_path = tmp_path / "sample.translated.layout.json"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "translate-layout",
            str(input_path),
            "--output",
            str(output_path),
            "--provider",
            "openai",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "KEY" in captured.err
    assert "OPENAI_API_KEY" in captured.err
    assert not output_path.exists()


def test_non_translation_cli_commands_do_not_require_translation_env(
    tmp_path,
    monkeypatch,
):
    input_path = tmp_path / "sample.layout.json"
    output_path = tmp_path / "rebuilt.pdf"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("translation provider should not be created")

    monkeypatch.setattr(
        "pdftranslate.translation.create_translation_provider",
        fail_if_called,
    )

    exit_code = main(
        [
            "render-layout",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()


def test_extract_images_command_creates_enhanced_layout_and_assets(tmp_path):
    input_path = tmp_path / "with-image.pdf"
    layout_path = tmp_path / "sample.layout.json"
    output_layout = tmp_path / "sample.with-images.layout.json"
    assets_dir = tmp_path / "images"
    write_pdf_with_png(input_path)
    layout_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "extract-images",
            str(input_path),
            "--layout",
            str(layout_path),
            "--output-layout",
            str(output_layout),
            "--assets-dir",
            str(assets_dir),
        ]
    )

    data = json.loads(output_layout.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert output_layout.exists()
    assert assets_dir.is_dir()
    assert data["pages"][0]["blocks"][1]["image"]["asset_path"] == "images/p1_i1.png"


def test_extract_images_command_rejects_missing_layout_json(tmp_path, capsys):
    input_path = tmp_path / "with-image.pdf"
    output_layout = tmp_path / "sample.with-images.layout.json"
    write_pdf_with_png(input_path)

    exit_code = main(
        [
            "extract-images",
            str(input_path),
            "--layout",
            str(tmp_path / "missing.layout.json"),
            "--output-layout",
            str(output_layout),
            "--assets-dir",
            str(tmp_path / "images"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "layout file not found" in captured.err
    assert not output_layout.exists()


def test_prepare_layout_command_creates_layout_with_assets_for_pdf_file(
    tmp_path,
    monkeypatch,
):
    input_path = tmp_path / "paper.pdf"
    output_dir = tmp_path / "layouts"
    assets_dir = tmp_path / "assets"
    input_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    captured = {}

    def fake_parse(path):
        captured["parse_path"] = path
        return layout_config_from_dict(minimal_layout_dict())

    def fake_extract(pdf_path, assets_dir, layout_config, base_dir=None):
        captured["extract_pdf_path"] = pdf_path
        captured["extract_assets_dir"] = assets_dir
        captured["extract_base_dir"] = base_dir
        return layout_config

    monkeypatch.setattr("pdftranslate.docling_adapter.parse_pdf_layout", fake_parse)
    monkeypatch.setattr(
        "pdftranslate.image_assets.extract_pdf_image_assets",
        fake_extract,
    )

    exit_code = main(
        [
            "prepare-layout",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--assets-dir",
            str(assets_dir),
        ]
    )

    output_path = output_dir / "paper.layout.json"
    assert exit_code == 0
    assert output_path.exists()
    assert captured["parse_path"] == input_path
    assert captured["extract_pdf_path"] == input_path
    assert captured["extract_assets_dir"] == assets_dir / "paper" / "images"
    assert captured["extract_base_dir"] == output_dir


def test_prepare_layout_command_processes_pdf_directory(tmp_path, monkeypatch):
    input_dir = tmp_path / "pdfs"
    output_dir = tmp_path / "layouts"
    input_dir.mkdir()
    (input_dir / "a.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    (input_dir / "b.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    (input_dir / "notes.txt").write_text("ignore me", encoding="utf-8")

    monkeypatch.setattr(
        "pdftranslate.docling_adapter.parse_pdf_layout",
        lambda path: layout_config_from_dict(minimal_layout_dict()),
    )

    exit_code = main(
        [
            "prepare-layout",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--no-images",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "a.layout.json").exists()
    assert (output_dir / "b.layout.json").exists()
    assert not (output_dir / "notes.layout.json").exists()


def test_build_pdf_command_uses_default_output_and_requires_translations(tmp_path):
    input_path = tmp_path / "sample.zh.layout.json"
    output_dir = tmp_path / "pdf"
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["translated_text"] = "译文"
    input_path.write_text(
        layout_config_from_dict(data).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "build-pdf",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    output_path = output_dir / "sample.zh.pdf"
    assert exit_code == 0
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_build_pdf_command_fails_missing_translations_by_default(tmp_path, capsys):
    input_path = tmp_path / "sample.zh.layout.json"
    output_dir = tmp_path / "pdf"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "build-pdf",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "p1_b1" in captured.err
    assert not (output_dir / "sample.zh.pdf").exists()


def test_build_pdf_command_allows_missing_translations_when_requested(tmp_path):
    input_path = tmp_path / "sample.layout.json"
    output_dir = tmp_path / "pdf"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "build-pdf",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--allow-missing-translations",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "sample.pdf").exists()
