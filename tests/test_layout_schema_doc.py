from pathlib import Path


def test_layout_config_schema_document_covers_required_fields():
    project_root = Path(__file__).resolve().parents[1]
    schema_paths = sorted(
        (project_root / "openspec" / "changes").glob(
            "**/*parse-pdf-to-layout-config/layout-config-schema.md"
        )
    )
    assert schema_paths
    schema_path = schema_paths[0]

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


def test_readme_documents_table_and_formula_layout_contract():
    project_root = Path(__file__).resolve().parents[1]
    content = (project_root / "README.md").read_text(encoding="utf-8")

    for required_term in (
        "`kind`: `table`",
        "`table.num_rows`",
        "`table.num_cols`",
        "`table.cells`",
        "`kind`: `formula`",
        "`formula.text`",
        "`formula.ref`",
        "`translatable`: `false`",
    ):
        assert required_term in content


def test_readme_documents_translate_layout_provider_usage():
    project_root = Path(__file__).resolve().parents[1]
    content = (project_root / "README.md").read_text(encoding="utf-8")

    for required_term in (
        "translate-layout",
        "--provider mock",
        "--provider openai",
        "BASE_URL",
        "KEY",
        "MODEL",
        "OPENAI_API_KEY",
    ):
        assert required_term in content
