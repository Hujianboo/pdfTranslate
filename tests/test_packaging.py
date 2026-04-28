import subprocess
from pathlib import Path


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
