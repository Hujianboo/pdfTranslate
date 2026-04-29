from pathlib import Path


def test_layout_config_schema_document_covers_required_fields():
    schema_path = (
        Path(__file__).resolve().parents[1]
        / "openspec"
        / "changes"
        / "parse-pdf-to-layout-config"
        / "layout-config-schema.md"
    )

    content = schema_path.read_text(encoding="utf-8")

    for required_term in (
        "schema_version",
        "coordinate_system",
        "pages",
        "blocks",
        "text",
        "image",
        "bbox",
        "style",
        "translated_text",
        "target_text",
        "rebuilt_pdf",
        "edited_image",
    ):
        assert required_term in content
