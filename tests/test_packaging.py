import base64
import json
import subprocess
from pathlib import Path

from pdftranslate.layout_io import layout_config_from_dict
from tests.fixtures import minimal_layout_dict


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


def test_console_script_extracts_sample_pdf(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "sample.md"

    result = subprocess.run(
        [
            "uv",
            "run",
            "pdftranslate",
            "extract",
            "assets/1603.08767v1.pdf",
            "--output",
            str(output_path),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip()


def test_console_script_parses_layout_json(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    input_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "layout.json"
    write_text_pdf(input_path, ["Packaged layout text"])

    result = subprocess.run(
        [
            "uv",
            "run",
            "pdftranslate",
            "parse-layout",
            str(input_path),
            "--output",
            str(output_path),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["pages"]


def test_console_script_renders_layout_pdf(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    input_path = tmp_path / "sample.layout.json"
    output_path = tmp_path / "rebuilt.pdf"
    input_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "pdftranslate",
            "render-layout",
            str(input_path),
            "--output",
            str(output_path),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_console_script_extracts_pdf_images_to_assets(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    input_path = tmp_path / "with-image.pdf"
    layout_path = tmp_path / "sample.layout.json"
    output_layout = tmp_path / "sample.with-images.layout.json"
    assets_dir = tmp_path / "images"
    write_pdf_with_png(input_path)
    layout_path.write_text(
        layout_config_from_dict(minimal_layout_dict()).to_json(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "pdftranslate",
            "extract-images",
            str(input_path),
            "--layout",
            str(layout_path),
            "--output-layout",
            str(output_layout),
            "--assets-dir",
            str(assets_dir),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_layout.exists()
    assert list(assets_dir.iterdir())
