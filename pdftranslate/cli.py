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

    parser.error(f"unknown command: {args.command}")


def _existing_input_path(input_pdf: str) -> Path | None:
    input_path = Path(input_pdf)
    if not input_path.is_file():
        print(f"input file not found: {input_path}", file=sys.stderr)
        return None
    return input_path


def _write_text_output(output: str, content: str) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
