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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract":
        input_path = Path(args.input_pdf)
        output_path = Path(args.output)
        if not input_path.is_file():
            print(f"input file not found: {input_path}", file=sys.stderr)
            return 1

        pages = extract_pdf_text(input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_markdown(input_path, pages), encoding="utf-8")
        return 0

    parser.error(f"unknown command: {args.command}")
