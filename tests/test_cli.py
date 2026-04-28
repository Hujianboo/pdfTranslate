from pathlib import Path

from pdftranslate.cli import main


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
