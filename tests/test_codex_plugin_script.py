import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from pdftranslate.layout_io import load_layout_config
from tests.fixtures import minimal_layout_dict


SCRIPT = "plugins/pdftranslate-codex/scripts/codex_layout_translation.py"
PDF_WORKFLOW_SCRIPT = "plugins/pdftranslate-codex/scripts/translate_pdf_with_codex.py"


def _load_pdf_workflow_module():
    script_path = Path(PDF_WORKFLOW_SCRIPT)
    spec = importlib.util.spec_from_file_location(
        "translate_pdf_with_codex_for_test", script_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_codex_pdf_workflow_defaults_to_larger_batches_and_low_reasoning():
    module = _load_pdf_workflow_module()
    args = module.build_parser().parse_args(["paper.pdf"])

    assert args.batch_size == 40
    assert args.batch_chars == 12000
    assert args.codex_reasoning_effort == "low"


def test_internal_codex_exec_uses_low_reasoning_and_ephemeral(monkeypatch, tmp_path):
    module = _load_pdf_workflow_module()
    commands = []

    monkeypatch.setattr(module, "_codex_launcher", lambda codex: [codex])

    def fake_run(command, log_path):
        commands.append((command, log_path))

    monkeypatch.setattr(module, "_run", fake_run)

    module._run_codex_translation(
        "codex",
        tmp_path / "manifest.json",
        tmp_path / "codex-translation",
        tmp_path / "logs",
        None,
        "low",
        "workspace-write",
    )

    command, log_path = commands[0]
    assert "--ephemeral" in command
    assert "-c" in command
    assert 'model_reasoning_effort="low"' in command
    assert log_path == tmp_path / "logs" / "codex-exec.log"


def test_default_work_dir_is_inside_repo_tmp(monkeypatch, tmp_path):
    module = _load_pdf_workflow_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)

    work_dir, owns_work_dir = module._resolve_work_dir(
        tmp_path / "paper.pdf",
        None,
    )

    assert owns_work_dir is True
    assert work_dir.parent == tmp_path / "tmp"
    assert work_dir.name.startswith("pdftranslate-codex-paper-")


def test_relative_work_dir_is_resolved_under_repo(monkeypatch, tmp_path):
    module = _load_pdf_workflow_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)

    work_dir, owns_work_dir = module._resolve_work_dir(
        tmp_path / "paper.pdf",
        "tmp/pdftranslate-run",
    )

    assert owns_work_dir is False
    assert work_dir == tmp_path / "tmp/pdftranslate-run"


def test_workspace_write_rejects_external_work_dir(monkeypatch, tmp_path):
    module = _load_pdf_workflow_module()
    repo_root = tmp_path / "repo"
    external = tmp_path / "external"
    repo_root.mkdir()
    external.mkdir()
    monkeypatch.setattr(module, "REPO_ROOT", repo_root)

    with pytest.raises(ValueError, match="--work-dir must be inside"):
        module._validate_work_dir_for_sandbox(external, "workspace-write")


def test_external_work_dir_is_allowed_with_full_access(monkeypatch, tmp_path):
    module = _load_pdf_workflow_module()
    repo_root = tmp_path / "repo"
    external = tmp_path / "external"
    repo_root.mkdir()
    external.mkdir()
    monkeypatch.setattr(module, "REPO_ROOT", repo_root)

    module._validate_work_dir_for_sandbox(external, "danger-full-access")


def test_codex_launcher_uses_direct_codex_when_available(monkeypatch):
    module = _load_pdf_workflow_module()
    calls = []

    def fake_run(command, **kwargs):
        del kwargs
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module._codex_launcher("/usr/local/bin/codex") == ["/usr/local/bin/codex"]
    assert calls == [["/usr/local/bin/codex", "--version"]]


def test_codex_launcher_falls_back_to_arm64_on_apple_silicon(monkeypatch):
    module = _load_pdf_workflow_module()
    monkeypatch.setattr(module.sys, "platform", "darwin")

    def fake_run(command, **kwargs):
        del kwargs
        if command == ["/usr/local/bin/codex", "--version"]:
            return SimpleNamespace(returncode=1, stdout="")
        if command == ["sysctl", "-in", "hw.optional.arm64"]:
            return SimpleNamespace(returncode=0, stdout="1\n")
        if command == ["arch", "-arm64", "/usr/local/bin/codex", "--version"]:
            return SimpleNamespace(returncode=0, stdout="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module._codex_launcher("/usr/local/bin/codex") == [
        "arch",
        "-arm64",
        "/usr/local/bin/codex",
    ]
