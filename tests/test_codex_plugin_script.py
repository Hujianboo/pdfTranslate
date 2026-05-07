import json
import subprocess
import sys

from pdftranslate.layout_io import load_layout_config
from tests.fixtures import minimal_layout_dict


SCRIPT = "plugins/pdftranslate-codex/scripts/codex_layout_translation.py"
PDF_WORKFLOW_SCRIPT = "plugins/pdftranslate-codex/scripts/translate_pdf_with_codex.py"


def test_codex_plugin_script_prepares_and_applies_translation_batches(tmp_path):
    layout_path = tmp_path / "sample.layout.json"
    layout_path.write_text(
        json.dumps(minimal_layout_dict(page_count=2), ensure_ascii=False),
        encoding="utf-8",
    )
    batch_dir = tmp_path / "codex-batches"

    prepare = subprocess.run(
        [
            sys.executable,
            SCRIPT,
            "prepare",
            str(layout_path),
            "--output-dir",
            str(batch_dir),
            "--target-language",
            "zh",
            "--batch-size",
            "1",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert prepare.returncode == 0, prepare.stderr
    manifest = json.loads((batch_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_count"] == 2
    assert (batch_dir / "batch-0001.prompt.txt").is_file()
    assert (batch_dir / "batch-0001.request.json").is_file()

    (batch_dir / "batch-0001.response.json").write_text(
        '{"translations":[{"id":"p1_b1","text":"第一页译文"}]}',
        encoding="utf-8",
    )
    (batch_dir / "batch-0002.response.json").write_text(
        '{"translations":[{"id":"p2_b1","text":"第二页译文"}]}',
        encoding="utf-8",
    )

    output_path = tmp_path / "sample.layout.zh.json"
    apply = subprocess.run(
        [
            sys.executable,
            SCRIPT,
            "apply",
            str(batch_dir / "manifest.json"),
            "--output",
            str(output_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert apply.returncode == 0, apply.stderr
    translated = load_layout_config(output_path)
    assert translated.pages[0].blocks[0].translated_text == "第一页译文"
    assert translated.pages[1].blocks[0].translated_text == "第二页译文"


def test_codex_pdf_workflow_script_exposes_customizable_io_options():
    result = subprocess.run(
        [
            sys.executable,
            PDF_WORKFLOW_SCRIPT,
            "--help",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "--output" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--work-dir" in result.stdout
    assert "--keep-work-dir" in result.stdout
