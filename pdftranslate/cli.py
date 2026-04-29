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

    extract_images_parser = subparsers.add_parser("extract-images")
    extract_images_parser.add_argument("input_pdf")
    extract_images_parser.add_argument("--layout", required=True)
    extract_images_parser.add_argument("--output-layout", required=True)
    extract_images_parser.add_argument("--assets-dir", required=True)

    render_layout_parser = subparsers.add_parser("render-layout")
    render_layout_parser.add_argument("input_layout_json")
    render_layout_parser.add_argument("--output", required=True)
    render_layout_parser.add_argument("--sample-text", choices=["zh"])
    render_layout_parser.add_argument("--debug-boxes", action="store_true")

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
        updated = extract_pdf_image_assets(
            input_path,
            assets_dir=Path(args.assets_dir),
            layout_config=config,
        )
        _write_text_output(args.output_layout, updated.to_json())
        return 0

    if args.command == "render-layout":
        input_path = _existing_input_path(args.input_layout_json)
        if input_path is None:
            return 1

        from pdftranslate.layout_io import load_layout_config
        from pdftranslate.pdf_renderer import RenderOptions, render_layout_pdf

        config = load_layout_config(input_path)
        render_layout_pdf(
            config,
            Path(args.output),
            RenderOptions(sample_text=args.sample_text, debug_boxes=args.debug_boxes),
        )
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


def _write_text_output(output: str, content: str) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
