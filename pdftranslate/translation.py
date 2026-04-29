from __future__ import annotations

from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from urllib import request

from pdftranslate.layout import LayoutConfig, TextBlock


DEFAULT_TARGET_LANGUAGE = "zh"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class TranslationError(Exception):
    pass


class UnsupportedTranslationProvider(TranslationError):
    pass


class MissingProviderCredentials(TranslationError):
    pass


@dataclass(frozen=True)
class TranslationItem:
    block_id: str
    text: str


@dataclass(frozen=True)
class TranslationRequest:
    target_language: str
    items: list[TranslationItem]


@dataclass(frozen=True)
class TranslationResult:
    block_id: str
    translated_text: str


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    model: str


class TranslationProvider(Protocol):
    name: str

    def translate(self, request: TranslationRequest) -> list[TranslationResult]:
        ...


class MockTranslationProvider:
    name = "mock"

    def translate(self, request: TranslationRequest) -> list[TranslationResult]:
        return [
            TranslationResult(
                block_id=item.block_id,
                translated_text=f"[{request.target_language}] {item.text}",
            )
            for item in request.items
        ]


PostJson = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


class OpenAICompatibleTranslationProvider:
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_OPENAI_BASE_URL,
        model: str = DEFAULT_OPENAI_MODEL,
        post_json: PostJson | None = None,
    ) -> None:
        self.config = OpenAICompatibleConfig(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            model=model,
        )
        self._post_json = post_json or _post_json

    def translate(self, request: TranslationRequest) -> list[TranslationResult]:
        if not request.items:
            return []

        response = self._post_json(
            f"{self.config.base_url}/chat/completions",
            {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            _openai_payload(self.config.model, request),
        )
        content = response["choices"][0]["message"]["content"]
        return _parse_translation_content(str(content))


def create_translation_provider(
    name: str | None = None,
    *,
    env: Mapping[str, str] | None = None,
    env_path: str | Path | None = Path(".env"),
) -> TranslationProvider:
    provider_name = (name or "openai").lower()
    if provider_name == "mock":
        return MockTranslationProvider()
    if provider_name == "openai":
        config = _openai_config_from_env(env=env, env_path=env_path)
        return OpenAICompatibleTranslationProvider(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
        )
    raise UnsupportedTranslationProvider(f"unsupported translation provider: {name}")


def translate_layout_config(
    config: LayoutConfig,
    provider: TranslationProvider,
    target_language: str = DEFAULT_TARGET_LANGUAGE,
) -> LayoutConfig:
    items = _translation_items_for_layout(config)
    translations = {
        result.block_id: result.translated_text
        for result in provider.translate(
            TranslationRequest(target_language=target_language, items=items)
        )
    }

    return replace(
        config,
        pages=[
            replace(
                page,
                blocks=[_block_with_translation(block, translations) for block in page.blocks],
            )
            for page in config.pages
        ],
    )


def _translation_items_for_layout(config: LayoutConfig) -> list[TranslationItem]:
    return [
        TranslationItem(block_id=block.id, text=block.text)
        for page in config.pages
        for block in page.blocks
        if _is_translatable_text_block(block)
    ]


def _block_with_translation(block: object, translations: dict[str, str]) -> object:
    if isinstance(block, TextBlock) and block.id in translations:
        return replace(block, translated_text=translations[block.id])
    return block


def _is_translatable_text_block(block: object) -> bool:
    return isinstance(block, TextBlock) and block.translatable


def _openai_config_from_env(
    *,
    env: Mapping[str, str] | None,
    env_path: str | Path | None,
) -> OpenAICompatibleConfig:
    values: dict[str, str] = {}
    if env_path is not None:
        values.update(_read_env_file(Path(env_path)))
    values.update(dict(os.environ if env is None else env))

    api_key = values.get("KEY") or values.get("OPENAI_API_KEY")
    if not api_key:
        raise MissingProviderCredentials(
            "missing translation provider API key: set KEY in .env or "
            "OPENAI_API_KEY, or use --provider mock"
        )

    return OpenAICompatibleConfig(
        base_url=values.get("BASE_URL")
        or values.get("OPENAI_BASE_URL")
        or DEFAULT_OPENAI_BASE_URL,
        api_key=api_key,
        model=values.get("MODEL") or values.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL,
    )


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _openai_payload(model: str, translation_request: TranslationRequest) -> dict[str, Any]:
    items = [
        {
            "id": item.block_id,
            "text": item.text,
        }
        for item in translation_request.items
    ]
    return {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Translate PDF text blocks to the requested target language. "
                    "Return JSON only: {\"translations\":[{\"id\":\"...\",\"text\":\"...\"}]}. "
                    "Do not translate formulas, table structure, or image content."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "target_language": translation_request.target_language,
                        "items": items,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }


def _parse_translation_content(content: str) -> list[TranslationResult]:
    data = json.loads(content)
    return [
        TranslationResult(
            block_id=str(item["id"]),
            translated_text=str(item["text"]),
        )
        for item in data.get("translations", [])
    ]


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method="POST")
    with request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))
