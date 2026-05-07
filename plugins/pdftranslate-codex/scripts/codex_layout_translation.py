#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from pdftranslate.layout_io import load_layout_config
from pdftranslate.translation import (
    DEFAULT_MAX_CHARS_PER_TRANSLATION_REQUEST,
    DEFAULT_MAX_ITEMS_PER_TRANSLATION_REQUEST,
    CodexTranslationProvider,
    TranslationError,
    TranslationRequest,
    _codex_translation_prompt,
    _translation_batches,
    _translation_items_for_layout,
    translate_layout_config,
)


MANIFEST_NAME = "manifest.json"


class FileBackedCodexCompletion:
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._index = 0

    @property
    def consumed_count(self) -> int:
        return self._index

    def __call__(self, prompt: str) -> str:
        del prompt
        if self._index >= len(self._responses):
            raise RuntimeError("missing Codex response for translation batch")
        response = self._responses[self._index]
        self._index += 1
        return response


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "prepare":
            prepare_batches(args)
            return 0
        if args.command == "apply":
            apply_responses(args)
            return 0
    except (OSError, ValueError, TranslationError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1

    parser.error(f"unknown command: {args.command}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex_layout_translation",
        description="Prepare/apply Codex translation batches for pdfTranslate layouts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("input_layout_json")
    prepare_parser.add_argument("--output-dir", required=True)
    prepare_parser.add_argument("--target-language", default="zh")
    prepare_parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_MAX_ITEMS_PER_TRANSLATION_REQUEST,
    )
    prepare_parser.add_argument(
        "--batch-chars",
        type=int,
        default=DEFAULT_MAX_CHARS_PER_TRANSLATION_REQUEST,
    )

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("manifest_json")
    apply_parser.add_argument("--output", required=True)
    apply_parser.add_argument(
        "--responses-dir",
        help="Directory containing response files; defaults to the manifest directory.",
    )

    return parser


def prepare_batches(args: argparse.Namespace) -> None:
    layout_path = Path(args.input_layout_json)
    config = load_layout_config(layout_path)
    items = _translation_items_for_layout(config)
    batches = _translation_batches(
        items,
        max_items_per_request=args.batch_size,
        max_chars_per_request=args.batch_chars,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_batches = []
    for batch_index, batch in enumerate(batches, start=1):
        request = TranslationRequest(
            target_language=args.target_language,
            items=batch,
        )
        stem = f"batch-{batch_index:04d}"
        request_name = f"{stem}.request.json"
        prompt_name = f"{stem}.prompt.txt"
        response_name = f"{stem}.response.json"

        _write_json(output_dir / request_name, _request_payload(request))
        (output_dir / prompt_name).write_text(
            _codex_translation_prompt(request),
            encoding="utf-8",
        )

        manifest_batches.append(
            {
                "index": batch_index,
                "item_count": len(batch),
                "request": request_name,
                "prompt": prompt_name,
                "response": response_name,
            }
        )

    manifest = {
        "layout": str(layout_path.resolve()),
        "target_language": args.target_language,
        "batch_size": args.batch_size,
        "batch_chars": args.batch_chars,
        "batch_count": len(manifest_batches),
        "batches": manifest_batches,
    }
    _write_json(output_dir / MANIFEST_NAME, manifest)

    print(f"wrote manifest: {output_dir / MANIFEST_NAME}")
    for batch in manifest_batches:
        print(
            "write Codex response: "
            f"{output_dir / batch['response']} "
            f"({batch['item_count']} text blocks)"
        )


def apply_responses(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest_json)
    manifest = _read_json(manifest_path)
    manifest_dir = manifest_path.parent
    responses_dir = Path(args.responses_dir) if args.responses_dir else manifest_dir

    responses = [
        (responses_dir / str(batch["response"])).read_text(encoding="utf-8")
        for batch in manifest.get("batches", [])
    ]

    config = load_layout_config(str(manifest["layout"]))
    completion = FileBackedCodexCompletion(responses)
    provider = CodexTranslationProvider(complete=completion)
    translated = translate_layout_config(
        config,
        provider,
        target_language=str(manifest["target_language"]),
        max_items_per_request=int(manifest["batch_size"]),
        max_chars_per_request=int(manifest["batch_chars"]),
        max_retries=0,
    )

    if completion.consumed_count != len(responses):
        raise RuntimeError(
            "Codex response count did not match generated translation batches"
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(translated.to_json(), encoding="utf-8")
    print(f"wrote translated layout: {output_path}")


def _request_payload(request: TranslationRequest) -> dict[str, Any]:
    return {
        "target_language": request.target_language,
        "items": [
            {
                "id": item.block_id,
                "text": item.text,
            }
            for item in request.items
        ],
    }


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
