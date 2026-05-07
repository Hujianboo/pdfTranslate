from argparse import ArgumentParser
from pathlib import Path
import shutil
import sys

from pdftranslate.extract import extract_pdf_text
from pdftranslate.markdown import render_markdown
from pdftranslate.translation import (
    DEFAULT_MAX_CHARS_PER_TRANSLATION_REQUEST,
    DEFAULT_MAX_ITEMS_PER_TRANSLATION_REQUEST,
    DEFAULT_TRANSLATION_MAX_RETRIES,
    DEFAULT_TRANSLATION_RETRY_DELAY_SECONDS,
)


DEFAULT_LAYOUT_DIR = "tmp/layout"
DEFAULT_ASSETS_DIR = "tmp/assets"
DEFAULT_PDF_DIR = "tmp/pdf"


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="pdftranslate")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("input_pdf")
    extract_parser.add_argument("--output", required=True)

    parse_layout_parser = subparsers.add_parser("parse-layout")
    parse_layout_parser.add_argument("input", help="PDF file or directory containing PDFs")
    parse_layout_parser.add_argument(
        "--output",
        help=(
            "Output layout JSON file for a single PDF, or output directory for "
            f"multiple PDFs (default: {DEFAULT_LAYOUT_DIR})"
        ),
    )
    parse_layout_parser.add_argument(
        "--assets-dir",
        default=DEFAULT_ASSETS_DIR,
        help=(
            "Root directory for extracted/rasterized images "
            f"(<stem>/images/; default: {DEFAULT_ASSETS_DIR})"
        ),
    )
    parse_layout_parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip extracting images (geometry-only layout)",
    )

    extract_images_parser = subparsers.add_parser("extract-images")
    extract_images_parser.add_argument("input_pdf")
    extract_images_parser.add_argument("--layout", required=True)
    extract_images_parser.add_argument("--output-layout", required=True)
    extract_images_parser.add_argument("--assets-dir", required=True)
    extract_images_parser.add_argument("--asset-base-dir")

    render_layout_parser = subparsers.add_parser("render-layout")
    render_layout_parser.add_argument("input_layout_json")
    render_layout_parser.add_argument("--output", required=True)
    render_layout_parser.add_argument("--sample-text", choices=["zh"])
    render_layout_parser.add_argument("--debug-boxes", action="store_true")
    render_layout_parser.add_argument("--require-translations", action="store_true")
    render_layout_parser.add_argument("--asset-base-dir")

    build_pdf_parser = subparsers.add_parser("build-pdf")
    build_pdf_parser.add_argument("input_layout_json")
    build_pdf_parser.add_argument("--output")
    build_pdf_parser.add_argument(
        "--output-dir",
        default=DEFAULT_PDF_DIR,
        help=f"Directory for rebuilt PDFs when --output is omitted (default: {DEFAULT_PDF_DIR})",
    )
    build_pdf_parser.add_argument("--debug-boxes", action="store_true")
    build_pdf_parser.add_argument("--allow-missing-translations", action="store_true")
    build_pdf_parser.add_argument("--asset-base-dir")

    translate_layout_parser = subparsers.add_parser("translate-layout")
    translate_layout_parser.add_argument("input_layout_json")
    translate_layout_parser.add_argument("--output", required=True)
    translate_layout_parser.add_argument("--provider", default="openai")
    translate_layout_parser.add_argument("--target-language", default="zh")
    translate_layout_parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_MAX_ITEMS_PER_TRANSLATION_REQUEST,
        help=(
            "Maximum text blocks per translation request "
            f"(default: {DEFAULT_MAX_ITEMS_PER_TRANSLATION_REQUEST})"
        ),
    )
    translate_layout_parser.add_argument(
        "--batch-chars",
        type=int,
        default=DEFAULT_MAX_CHARS_PER_TRANSLATION_REQUEST,
        help=(
            "Maximum source characters per translation request "
            f"(default: {DEFAULT_MAX_CHARS_PER_TRANSLATION_REQUEST})"
        ),
    )
    translate_layout_parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_TRANSLATION_MAX_RETRIES,
        help=(
            "Maximum retries for each failed translation batch "
            f"(default: {DEFAULT_TRANSLATION_MAX_RETRIES})"
        ),
    )
    translate_layout_parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_TRANSLATION_RETRY_DELAY_SECONDS,
        help=(
            "Initial retry delay in seconds for failed translation batches "
            f"(default: {DEFAULT_TRANSLATION_RETRY_DELAY_SECONDS})"
        ),
    )

    translate_pdf_parser = subparsers.add_parser("translate-pdf")
    translate_pdf_parser.add_argument("input_pdf")
    translate_pdf_parser.add_argument("--output")
    translate_pdf_parser.add_argument(
        "--output-dir",
        default=DEFAULT_PDF_DIR,
        help=f"Directory for generated translated PDFs (default: {DEFAULT_PDF_DIR})",
    )
    translate_pdf_parser.add_argument(
        "--work-dir",
        help="Directory for temporary layout JSON and image assets",
    )
    translate_pdf_parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary layout JSON and image assets after rendering",
    )
    translate_pdf_parser.add_argument("--provider", default="openai")
    translate_pdf_parser.add_argument("--target-language", default="zh")
    translate_pdf_parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_MAX_ITEMS_PER_TRANSLATION_REQUEST,
        help=(
            "Maximum text blocks per translation request "
            f"(default: {DEFAULT_MAX_ITEMS_PER_TRANSLATION_REQUEST})"
        ),
    )
    translate_pdf_parser.add_argument(
        "--batch-chars",
        type=int,
        default=DEFAULT_MAX_CHARS_PER_TRANSLATION_REQUEST,
        help=(
            "Maximum source characters per translation request "
            f"(default: {DEFAULT_MAX_CHARS_PER_TRANSLATION_REQUEST})"
        ),
    )
    translate_pdf_parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_TRANSLATION_MAX_RETRIES,
        help=(
            "Maximum retries for each failed translation batch "
            f"(default: {DEFAULT_TRANSLATION_MAX_RETRIES})"
        ),
    )
    translate_pdf_parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_TRANSLATION_RETRY_DELAY_SECONDS,
        help=(
            "Initial retry delay in seconds for failed translation batches "
            f"(default: {DEFAULT_TRANSLATION_RETRY_DELAY_SECONDS})"
        ),
    )
    translate_pdf_parser.add_argument("--no-images", action="store_true")
    translate_pdf_parser.add_argument("--debug-boxes", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract":
        input_path = _existing_input_path(args.input_pdf)
        if input_path is None:
            return 1

        pages = extract_pdf_text(input_path)
        out = _resolve_file_output_path(
            args.output,
            default_name=f"{input_path.stem}.md",
        )
        _write_text_output(out, render_markdown(input_path, pages))
        return 0

    if args.command == "parse-layout":
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"input not found: {input_path}", file=sys.stderr)
            return 1

        pdf_paths = _pdf_inputs(input_path)
        if not pdf_paths:
            print(f"no PDF files found: {input_path}", file=sys.stderr)
            return 1

        from pdftranslate.docling_adapter import parse_pdf_layout

        extract_pdf_image_assets = None
        if not args.no_images:
            from pdftranslate.image_assets import extract_pdf_image_assets

        output_arg = Path(args.output) if args.output else Path(DEFAULT_LAYOUT_DIR)
        assets_root = Path(args.assets_dir)
        for pdf_path in pdf_paths:
            if len(pdf_paths) == 1 and args.output:
                output_layout = _parse_layout_output_path(pdf_path, output_arg)
            else:
                output_layout = _default_layout_output_path(pdf_path, output_arg)
            config = parse_pdf_layout(pdf_path)
            if extract_pdf_image_assets is not None:
                config = extract_pdf_image_assets(
                    pdf_path,
                    assets_dir=_default_assets_dir(pdf_path, assets_root),
                    layout_config=config,
                    base_dir=output_layout.parent,
                )
            _write_text_output(output_layout, config.to_json())
            print(f"wrote layout: {output_layout}")
        return 0

    if args.command == "extract-images":
        input_path = _existing_input_path(args.input_pdf)
        if input_path is None:
            return 1
        layout_path = _existing_input_path(args.layout, label="layout file")
        if layout_path is None:
            return 1

        from pdftranslate.image_assets import extract_pdf_image_assets
        from pdftranslate.layout_io import load_layout_config

        config = load_layout_config(layout_path)
        output_layout_path = Path(args.output_layout)
        asset_base_dir = (
            Path(args.asset_base_dir) if args.asset_base_dir else output_layout_path.parent
        )
        updated = extract_pdf_image_assets(
            input_path,
            assets_dir=Path(args.assets_dir),
            layout_config=config,
            base_dir=asset_base_dir,
        )
        _write_text_output(output_layout_path, updated.to_json())
        return 0

    if args.command == "render-layout":
        input_path = _existing_input_path(args.input_layout_json)
        if input_path is None:
            return 1

        from pdftranslate.layout_io import load_layout_config
        from pdftranslate.pdf_renderer import (
            RenderOptions,
            missing_translations_for_layout,
            render_layout_pdf,
        )

        config = load_layout_config(input_path)
        if args.require_translations and not _check_required_translations(
            config,
            missing_translations_for_layout,
        ):
            return 1
        asset_base_dir = Path(args.asset_base_dir) if args.asset_base_dir else input_path.parent
        out = _resolve_file_output_path(
            args.output,
            default_name=f"{input_path.stem}.pdf",
        )
        render_layout_pdf(
            config,
            out,
            RenderOptions(
                sample_text=args.sample_text,
                debug_boxes=args.debug_boxes,
                asset_base_dir=asset_base_dir,
            ),
        )
        return 0

    if args.command == "build-pdf":
        input_path = _existing_input_path(args.input_layout_json)
        if input_path is None:
            return 1

        from pdftranslate.layout_io import load_layout_config
        from pdftranslate.pdf_renderer import (
            RenderOptions,
            missing_translations_for_layout,
            render_layout_pdf,
        )

        config = load_layout_config(input_path)
        if not args.allow_missing_translations and not _check_required_translations(
            config,
            missing_translations_for_layout,
        ):
            return 1

        if args.output:
            candidate = Path(args.output)
            output_path = (
                candidate / _default_pdf_output_path(input_path, Path(".")).name
                if candidate.is_dir()
                else candidate
            )
        else:
            output_path = _default_pdf_output_path(input_path, Path(args.output_dir))
        asset_base_dir = Path(args.asset_base_dir) if args.asset_base_dir else input_path.parent
        render_layout_pdf(
            config,
            output_path,
            RenderOptions(
                debug_boxes=args.debug_boxes,
                asset_base_dir=asset_base_dir,
            ),
        )
        print(f"wrote pdf: {output_path}")
        return 0

    if args.command == "translate-layout":
        input_path = _existing_input_path(args.input_layout_json)
        if input_path is None:
            return 1

        from pdftranslate.layout_io import load_layout_config
        from pdftranslate.translation import (
            MissingProviderCredentials,
            TranslationError,
            create_translation_provider,
            translate_layout_config,
        )

        try:
            provider = create_translation_provider(args.provider)
            config = load_layout_config(input_path)
            translated = translate_layout_config(
                config,
                provider,
                target_language=args.target_language,
                max_items_per_request=args.batch_size,
                max_chars_per_request=args.batch_chars,
                max_retries=args.max_retries,
                retry_delay_seconds=args.retry_delay,
                on_batch_complete=lambda batch_index, total_batches, item_count: print(
                    (
                        f"translated batch {batch_index}/{total_batches} "
                        f"({item_count} text blocks)"
                    ),
                    file=sys.stderr,
                ),
                on_batch_retry=lambda batch_index, total_batches, attempt, error, delay: print(
                    (
                        f"retrying batch {batch_index}/{total_batches} "
                        f"after attempt {attempt} failed ({error}); "
                        f"sleeping {delay:g}s"
                    ),
                    file=sys.stderr,
                ),
            )
        except MissingProviderCredentials as error:
            print(str(error), file=sys.stderr)
            return 1
        except TranslationError as error:
            print(str(error), file=sys.stderr)
            return 1

        out = _resolve_file_output_path(
            args.output,
            default_name=f"{input_path.stem}.translated.layout.json",
        )
        _write_text_output(out, translated.to_json())
        return 0

    if args.command == "translate-pdf":
        input_path = _existing_input_path(args.input_pdf)
        if input_path is None:
            return 1

        from pdftranslate.docling_adapter import parse_pdf_layout
        from pdftranslate.image_assets import extract_pdf_image_assets
        from pdftranslate.layout_io import load_layout_config
        from pdftranslate.pdf_renderer import (
            RenderOptions,
            render_layout_pdf,
        )
        from pdftranslate.translation import (
            MissingProviderCredentials,
            TranslationError,
            create_translation_provider,
            translate_layout_config,
        )

        work_dir = (
            Path(args.work_dir)
            if args.work_dir
            else Path("tmp") / "translate-pdf" / input_path.stem
        )
        layout_dir = work_dir / "layout"
        layout_path = layout_dir / f"{input_path.stem}.layout.json"
        translated_layout_path = layout_dir / f"{input_path.stem}.layout.zh.json"
        assets_dir = _default_assets_dir(input_path, work_dir / "assets")
        output_path = _translate_pdf_output_path(
            input_path,
            output=args.output,
            output_dir=Path(args.output_dir),
        )

        try:
            provider = create_translation_provider(args.provider)
            layout_dir.mkdir(parents=True, exist_ok=True)
            config = parse_pdf_layout(input_path)
            if not args.no_images:
                config = extract_pdf_image_assets(
                    input_path,
                    assets_dir=assets_dir,
                    layout_config=config,
                    base_dir=layout_dir,
                )
            _write_text_output(layout_path, config.to_json())

            translated = translate_layout_config(
                config,
                provider,
                target_language=args.target_language,
                max_items_per_request=args.batch_size,
                max_chars_per_request=args.batch_chars,
                max_retries=args.max_retries,
                retry_delay_seconds=args.retry_delay,
                on_batch_complete=lambda batch_index, total_batches, item_count: print(
                    (
                        f"translated batch {batch_index}/{total_batches} "
                        f"({item_count} text blocks)"
                    ),
                    file=sys.stderr,
                ),
                on_batch_retry=lambda batch_index, total_batches, attempt, error, delay: print(
                    (
                        f"retrying batch {batch_index}/{total_batches} "
                        f"after attempt {attempt} failed ({error}); "
                        f"sleeping {delay:g}s"
                    ),
                    file=sys.stderr,
                ),
            )
            _write_text_output(translated_layout_path, translated.to_json())

            render_config = load_layout_config(translated_layout_path)
            render_layout_pdf(
                render_config,
                output_path,
                RenderOptions(
                    debug_boxes=args.debug_boxes,
                    asset_base_dir=layout_dir,
                ),
            )
            print(f"wrote pdf: {output_path}")
            return 0
        except MissingProviderCredentials as error:
            print(str(error), file=sys.stderr)
            return 1
        except TranslationError as error:
            print(str(error), file=sys.stderr)
            return 1
        finally:
            if not args.keep_temp:
                shutil.rmtree(work_dir, ignore_errors=True)

    parser.error(f"unknown command: {args.command}")


def _existing_input_path(input_pdf: str, label: str = "input file") -> Path | None:
    input_path = Path(input_pdf)
    if not input_path.is_file():
        print(f"{label} not found: {input_path}", file=sys.stderr)
        return None
    return input_path


def _resolve_file_output_path(output: str | Path, *, default_name: str) -> Path:
    """If *output* is an existing directory, write *default_name* inside it."""
    path = Path(output)
    if path.is_dir():
        return path / default_name
    return path


def _write_text_output(output: str | Path, content: str) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def _pdf_inputs(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(path for path in input_path.glob("*.pdf") if path.is_file())
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]
    return []


def _default_layout_output_path(pdf_path: Path, output_dir: Path) -> Path:
    return output_dir / f"{pdf_path.stem}.layout.json"


def _parse_layout_output_path(pdf_path: Path, output: Path) -> Path:
    if output.is_dir() or output.suffix.lower() != ".json":
        return _default_layout_output_path(pdf_path, output)
    return output


def _default_assets_dir(pdf_path: Path, assets_root: Path) -> Path:
    return assets_root / pdf_path.stem / "images"


def _default_pdf_output_path(layout_path: Path, output_dir: Path) -> Path:
    name = layout_path.name
    if name.endswith(".layout.zh.json"):
        stem = name[: -len(".layout.zh.json")] + ".zh"
    elif name.endswith(".layout.json"):
        stem = name[: -len(".layout.json")]
    elif name.endswith(".json"):
        stem = name[: -len(".json")]
    else:
        stem = layout_path.stem
    return output_dir / f"{stem}.pdf"


def _translate_pdf_output_path(
    input_path: Path,
    *,
    output: str | None,
    output_dir: Path,
) -> Path:
    default_name = f"{input_path.stem}.zh.pdf"
    if output:
        candidate = Path(output)
        return candidate / default_name if candidate.is_dir() else candidate
    return output_dir / default_name


def _check_required_translations(config, missing_translations_for_layout) -> bool:
    missing = missing_translations_for_layout(config)
    if missing:
        print(
            "missing translated_text for translatable text blocks: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return False
    return True
