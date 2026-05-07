#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from pdftranslate.layout_io import load_layout_config
from pdftranslate.pdf_renderer import RenderOptions, render_layout_pdf


REPO_ROOT = Path(__file__).resolve().parents[3]
LAYOUT_SCRIPT = REPO_ROOT / "plugins/pdftranslate-codex/scripts/codex_layout_translation.py"
DEFAULT_CODEX_BATCH_SIZE = 40
DEFAULT_CODEX_BATCH_CHARS = 12000
DEFAULT_CODEX_REASONING_EFFORT = "low"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        translate_pdf(args)
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="translate_pdf_with_codex",
        description="Translate a PDF through Codex and render a translated PDF.",
    )
    parser.add_argument("input_pdf")
    parser.add_argument("--output", help="Output PDF path.")
    parser.add_argument(
        "--output-dir",
        default="output/pdf",
        help="Output directory when --output is omitted (default: output/pdf).",
    )
    parser.add_argument(
        "--output-layout",
        help="Optional path for the translated LayoutConfig JSON.",
    )
    parser.add_argument("--target-language", default="zh")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_CODEX_BATCH_SIZE,
    )
    parser.add_argument(
        "--batch-chars",
        type=int,
        default=DEFAULT_CODEX_BATCH_CHARS,
    )
    parser.add_argument(
        "--work-dir",
        help=(
            "Temporary working directory. Relative paths are resolved under the "
            "repository root. Deleted by default unless --keep-work-dir is set."
        ),
    )
    parser.add_argument(
        "--keep-work-dir",
        action="store_true",
        help="Keep parsed layout, assets, Codex requests/responses, and logs.",
    )
    parser.add_argument("--no-images", action="store_true")
    parser.add_argument("--debug-boxes", action="store_true")
    parser.add_argument(
        "--codex-model",
        help="Optional model name passed to codex exec.",
    )
    parser.add_argument(
        "--codex-reasoning-effort",
        default=DEFAULT_CODEX_REASONING_EFFORT,
        choices=["minimal", "low", "medium", "high", "xhigh"],
        help=(
            "Reasoning effort for the internal codex exec translator "
            f"(default: {DEFAULT_CODEX_REASONING_EFFORT})."
        ),
    )
    parser.add_argument(
        "--codex-sandbox",
        default="workspace-write",
        choices=["read-only", "workspace-write", "danger-full-access"],
    )
    return parser


def translate_pdf(args: argparse.Namespace) -> None:
    input_pdf = Path(args.input_pdf)
    if not input_pdf.is_file():
        raise ValueError(f"input PDF not found: {input_pdf}")

    codex = shutil.which("codex")
    if codex is None:
        raise RuntimeError("codex CLI not found on PATH")

    output_pdf = _resolve_output_pdf(input_pdf, args.output, Path(args.output_dir))
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    work_dir, owns_work_dir = _resolve_work_dir(input_pdf, args.work_dir)
    _validate_work_dir_for_sandbox(work_dir, args.codex_sandbox)
    layout_dir = work_dir / "layout"
    assets_dir = work_dir / "assets"
    batch_dir = work_dir / "codex-translation"
    log_dir = work_dir / "logs"
    translated_layout = (
        Path(args.output_layout)
        if args.output_layout
        else layout_dir / f"{input_pdf.stem}.layout.zh.json"
    )

    try:
        for path in (layout_dir, assets_dir, batch_dir, log_dir):
            path.mkdir(parents=True, exist_ok=True)

        print(f"work dir: {work_dir}")
        _parse_layout(input_pdf, layout_dir, assets_dir, args.no_images, log_dir)

        layout_path = layout_dir / f"{input_pdf.stem}.layout.json"
        if not layout_path.is_file():
            raise RuntimeError(f"expected layout was not created: {layout_path}")

        _prepare_batches(
            layout_path,
            batch_dir,
            args.target_language,
            args.batch_size,
            args.batch_chars,
            log_dir,
        )
        _run_codex_translation(
            codex,
            batch_dir / "manifest.json",
            batch_dir,
            log_dir,
            args.codex_model,
            args.codex_reasoning_effort,
            args.codex_sandbox,
        )
        _validate_responses(batch_dir / "manifest.json", batch_dir)
        _apply_responses(batch_dir / "manifest.json", translated_layout, log_dir)
        _build_pdf(
            translated_layout,
            output_pdf,
            args.debug_boxes,
            asset_base_dir=layout_dir,
            log_dir=log_dir,
        )

        print(f"wrote pdf: {output_pdf}")
        if args.output_layout:
            print(f"wrote translated layout: {translated_layout}")
    finally:
        if args.keep_work_dir:
            print(f"kept work dir: {work_dir}")
        else:
            shutil.rmtree(work_dir, ignore_errors=True)


def _resolve_output_pdf(input_pdf: Path, output: str | None, output_dir: Path) -> Path:
    default_name = f"{input_pdf.stem}.zh.pdf"
    if output:
        candidate = Path(output)
        return candidate / default_name if candidate.is_dir() else candidate
    return output_dir / default_name


def _resolve_work_dir(input_pdf: Path, work_dir: str | None) -> tuple[Path, bool]:
    if work_dir:
        requested = Path(work_dir)
        return (requested if requested.is_absolute() else REPO_ROOT / requested), False

    tmp_root = REPO_ROOT / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    return (
        Path(
            tempfile.mkdtemp(
                prefix=f"pdftranslate-codex-{input_pdf.stem}-",
                dir=tmp_root,
            )
        ),
        True,
    )


def _validate_work_dir_for_sandbox(work_dir: Path, sandbox: str) -> None:
    if sandbox != "workspace-write":
        return
    if _is_relative_to(work_dir.resolve(), REPO_ROOT.resolve()):
        return
    raise ValueError(
        "--work-dir must be inside the pdfTranslate repository when using "
        "--codex-sandbox workspace-write. Use a relative work dir such as "
        "tmp/pdftranslate-run, or pass --codex-sandbox danger-full-access."
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _parse_layout(
    input_pdf: Path,
    layout_dir: Path,
    assets_dir: Path,
    no_images: bool,
    log_dir: Path,
) -> None:
    from pdftranslate.docling_adapter import parse_pdf_layout

    log_path = log_dir / "parse-layout.log"
    layout_path = layout_dir / f"{input_pdf.stem}.layout.json"
    with log_path.open("w", encoding="utf-8") as log_file:
        with redirect_stdout(log_file), redirect_stderr(log_file):
            config = parse_pdf_layout(input_pdf)
            if not no_images:
                from pdftranslate.image_assets import extract_pdf_image_assets

                config = extract_pdf_image_assets(
                    input_pdf,
                    assets_dir=assets_dir / input_pdf.stem / "images",
                    layout_config=config,
                    base_dir=layout_dir,
                )
    layout_path.write_text(config.to_json(), encoding="utf-8")


def _prepare_batches(
    layout_path: Path,
    batch_dir: Path,
    target_language: str,
    batch_size: int,
    batch_chars: int,
    log_dir: Path,
) -> None:
    _run(
        [
            sys.executable,
            str(LAYOUT_SCRIPT),
            "prepare",
            str(layout_path),
            "--output-dir",
            str(batch_dir),
            "--target-language",
            target_language,
            "--batch-size",
            str(batch_size),
            "--batch-chars",
            str(batch_chars),
        ],
        log_dir / "prepare.log",
    )


def _run_codex_translation(
    codex: str,
    manifest_path: Path,
    batch_dir: Path,
    log_dir: Path,
    model: str | None,
    reasoning_effort: str,
    sandbox: str,
) -> None:
    prompt = (
        "Use the pdftranslate-codex workflow to translate "
        f"{manifest_path.resolve()} to Simplified Chinese unless the manifest target_language "
        "says otherwise. Read the manifest and every batch request JSON. For every batch listed "
        "in the manifest, write the corresponding response JSON file in the same directory. "
        'Each response file must be valid JSON only with shape {"translations":[{"id":"...",'
        '"text":"..."}]}. Preserve every id exactly. Keep URLs, citations, product names, '
        "and technical acronyms such as ML-DM, SaaS, PaaS, Hadoop, CUDA, MPI, and API unchanged "
        "when appropriate. Do not modify files outside "
        f"{batch_dir.resolve()}. Validate that response ids exactly match request ids before "
        "finishing, and report omitted ids."
    )
    command = [
        *_codex_launcher(codex),
        "exec",
        "-C",
        str(REPO_ROOT),
        "-s",
        sandbox,
        "--ephemeral",
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--output-last-message",
        str(batch_dir / "codex-exec-summary.txt"),
    ]
    if model:
        command.extend(["-m", model])
    command.append(prompt)
    _run(command, log_dir / "codex-exec.log")


def _codex_launcher(codex: str) -> list[str]:
    direct = [codex]
    if _codex_version_works(direct):
        return direct

    arm64 = ["arch", "-arm64", codex]
    if sys.platform == "darwin" and _apple_silicon_host() and _codex_version_works(
        arm64
    ):
        return arm64

    return direct


def _codex_version_works(command_prefix: list[str]) -> bool:
    try:
        result = subprocess.run(
            [*command_prefix, "--version"],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _apple_silicon_host() -> bool:
    try:
        result = subprocess.run(
            ["sysctl", "-in", "hw.optional.arm64"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.stdout.strip() == "1"


def _apply_responses(manifest_path: Path, output_layout: Path, log_dir: Path) -> None:
    _run(
        [
            sys.executable,
            str(LAYOUT_SCRIPT),
            "apply",
            str(manifest_path),
            "--output",
            str(output_layout),
        ],
        log_dir / "apply.log",
    )


def _build_pdf(
    translated_layout: Path,
    output_pdf: Path,
    debug_boxes: bool,
    *,
    asset_base_dir: Path,
    log_dir: Path,
) -> None:
    log_path = log_dir / "build-pdf.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        with redirect_stdout(log_file), redirect_stderr(log_file):
            config = load_layout_config(translated_layout)
            render_layout_pdf(
                config,
                output_pdf,
                RenderOptions(
                    debug_boxes=debug_boxes,
                    asset_base_dir=asset_base_dir,
                ),
            )


def _validate_responses(manifest_path: Path, batch_dir: Path) -> None:
    manifest = _read_json(manifest_path)
    problems: list[str] = []
    total = 0
    for batch in manifest.get("batches", []):
        request_path = batch_dir / str(batch["request"])
        response_path = batch_dir / str(batch["response"])
        if not response_path.is_file():
            problems.append(f"missing response: {response_path}")
            continue
        request = _read_json(request_path)
        response = _read_json(response_path)
        request_ids = [str(item["id"]) for item in request.get("items", [])]
        response_ids = [str(item["id"]) for item in response.get("translations", [])]
        if request_ids != response_ids:
            problems.append(f"id mismatch: {response_path.name}")
        total += len(response_ids)

    if problems:
        raise RuntimeError("; ".join(problems))
    print(f"validated Codex responses: {total} text blocks")


def _run(command: list[str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print("$ " + " ".join(command))
    with log_path.open("w", encoding="utf-8") as log_file:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=False,
            text=True,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed with exit code {result.returncode}: {' '.join(command)}\n"
            f"log: {log_path}\n"
            + _tail(log_path)
        )


def _tail(path: Path, line_count: int = 40) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-line_count:])


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
