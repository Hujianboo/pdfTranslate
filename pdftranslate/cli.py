from argparse import ArgumentParser
from pathlib import Path
import sys

from pdftranslate.extract import extract_pdf_text
from pdftranslate.markdown import render_markdown


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="pdftranslate")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("input_pdf")
    extract_parser.add_argument("--output", required=True)

    parse_layout_parser = subparsers.add_parser("parse-layout")
    parse_layout_parser.add_argument("input_pdf")
    parse_layout_parser.add_argument("--output", required=True)

    prepare_layout_parser = subparsers.add_parser("prepare-layout")
    prepare_layout_parser.add_argument("input", help="PDF file or directory containing PDFs")
    prepare_layout_parser.add_argument("--output-dir", default="output/layout")
    prepare_layout_parser.add_argument("--assets-dir", default="output/assets")
    prepare_layout_parser.add_argument("--no-images", action="store_true")

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
    build_pdf_parser.add_argument("--output-dir", default="output/pdf")
    build_pdf_parser.add_argument("--debug-boxes", action="store_true")
    build_pdf_parser.add_argument("--allow-missing-translations", action="store_true")
    build_pdf_parser.add_argument("--asset-base-dir")

    translate_layout_parser = subparsers.add_parser("translate-layout")
    translate_layout_parser.add_argument("input_layout_json")
    translate_layout_parser.add_argument("--output", required=True)
    translate_layout_parser.add_argument("--provider", default="openai")
    translate_layout_parser.add_argument("--target-language", default="zh")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract":
        input_path = _existing_input_path(args.input_pdf)
        if input_path is None:
            return 1

        pages = extract_pdf_text(input_path)
        _write_text_output(args.output, render_markdown(input_path, pages))
        return 0

    if args.command == "parse-layout":
        input_path = _existing_input_path(args.input_pdf)
        if input_path is None:
            return 1

        from pdftranslate.docling_adapter import parse_pdf_layout

        config = parse_pdf_layout(input_path)
        _write_text_output(args.output, config.to_json())
        return 0

    if args.command == "prepare-layout":
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"input not found: {input_path}", file=sys.stderr)
            return 1

        pdf_paths = _pdf_inputs(input_path)
        if not pdf_paths:
            print(f"no PDF files found: {input_path}", file=sys.stderr)
            return 1

        from pdftranslate.docling_adapter import parse_pdf_layout
        from pdftranslate.image_assets import extract_pdf_image_assets

        output_dir = Path(args.output_dir)
        assets_root = Path(args.assets_dir)
        for pdf_path in pdf_paths:
            output_layout = _default_layout_output_path(pdf_path, output_dir)
            config = parse_pdf_layout(pdf_path)
            if not args.no_images:
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
        render_layout_pdf(
            config,
            Path(args.output),
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

        output_path = (
            Path(args.output)
            if args.output
            else _default_pdf_output_path(input_path, Path(args.output_dir))
        )
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
            )
        except MissingProviderCredentials as error:
            print(str(error), file=sys.stderr)
            return 1
        except TranslationError as error:
            print(str(error), file=sys.stderr)
            return 1

        _write_text_output(args.output, translated.to_json())
        return 0

    parser.error(f"unknown command: {args.command}")


def _existing_input_path(input_pdf: str, label: str = "input file") -> Path | None:
    input_path = Path(input_pdf)
    if not input_path.is_file():
        print(f"{label} not found: {input_path}", file=sys.stderr)
        return None
    return input_path


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


def _default_assets_dir(pdf_path: Path, assets_root: Path) -> Path:
    return assets_root / pdf_path.stem / "images"


def _default_pdf_output_path(layout_path: Path, output_dir: Path) -> Path:
    name = layout_path.name
    if name.endswith(".layout.json"):
        stem = name[: -len(".layout.json")]
    elif name.endswith(".json"):
        stem = name[: -len(".json")]
    else:
        stem = layout_path.stem
    return output_dir / f"{stem}.pdf"


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
