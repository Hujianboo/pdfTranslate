from pathlib import Path

import pytest

from pdftranslate.translation import (
    MissingProviderCredentials,
    MockTranslationProvider,
    OpenAICompatibleTranslationProvider,
    TranslationItem,
    TranslationRequest,
    TranslationResult,
    UnsupportedTranslationProvider,
    create_translation_provider,
    translate_layout_config,
)
from pdftranslate.layout_io import layout_config_from_dict
from tests.fixtures import layout_dict_with_all_block_kinds, minimal_layout_dict


class RecordingProvider:
    name = "recording"

    def __init__(self) -> None:
        self.requests = []

    def translate(self, request: TranslationRequest):
        self.requests.append(request)
        return [
            TranslationResult(
                block_id=item.block_id,
                translated_text=f"译文:{item.text}",
            )
            for item in request.items
        ]


def test_provider_factory_defaults_to_openai_provider():
    provider = create_translation_provider(
        env={"KEY": "test-key"},
        env_path=None,
    )

    assert provider.name == "openai"
    assert isinstance(provider, OpenAICompatibleTranslationProvider)


def test_provider_factory_creates_mock_provider_with_deterministic_translation():
    provider = create_translation_provider("mock")

    results = provider.translate(
        TranslationRequest(
            target_language="zh",
            items=[TranslationItem(block_id="p1_b1", text="Hello")],
        )
    )

    assert isinstance(provider, MockTranslationProvider)
    assert provider.name == "mock"
    assert results[0].block_id == "p1_b1"
    assert results[0].translated_text == "[zh] Hello"


def test_provider_factory_rejects_unknown_provider():
    with pytest.raises(UnsupportedTranslationProvider):
        create_translation_provider("unknown")


def test_openai_compatible_provider_reads_translation_env_file(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "BASE_URL=https://example.test/v1\n"
        "KEY=test-key\n"
        "MODEL=test-model\n",
        encoding="utf-8",
    )

    provider = create_translation_provider(
        "openai",
        env={},
        env_path=env_path,
    )

    assert isinstance(provider, OpenAICompatibleTranslationProvider)
    assert provider.config.base_url == "https://example.test/v1"
    assert provider.config.api_key == "test-key"
    assert provider.config.model == "test-model"


def test_openai_compatible_provider_reads_standard_openai_environment():
    provider = create_translation_provider(
        "openai",
        env={
            "OPENAI_BASE_URL": "https://api.openai.test/v1",
            "OPENAI_API_KEY": "openai-key",
            "OPENAI_MODEL": "gpt-test",
        },
        env_path=None,
    )

    assert provider.config.base_url == "https://api.openai.test/v1"
    assert provider.config.api_key == "openai-key"
    assert provider.config.model == "gpt-test"


def test_openai_compatible_provider_without_key_raises_missing_credentials():
    with pytest.raises(MissingProviderCredentials) as error:
        create_translation_provider("openai", env={}, env_path=None)

    message = str(error.value)
    assert "KEY" in message
    assert "OPENAI_API_KEY" in message


def test_codex_environment_variables_do_not_satisfy_openai_credentials():
    with pytest.raises(MissingProviderCredentials):
        create_translation_provider(
            "openai",
            env={
                "CODEX_SHELL": "1",
                "CODEX_THREAD_ID": "thread",
                "CODEX_INTERNAL_ORIGINATOR_OVERRIDE": "Codex Desktop",
            },
            env_path=None,
        )


def test_openai_compatible_provider_can_build_translation_request_with_fake_transport():
    calls = []

    def fake_post(url, headers, payload):
        calls.append((url, headers, payload))
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"translations": [{"id": "p1_b1", "text": "你好"}]}'
                    }
                }
            ]
        }

    provider = OpenAICompatibleTranslationProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
        post_json=fake_post,
    )

    results = provider.translate(
        TranslationRequest(
            target_language="zh",
            items=[TranslationItem(block_id="p1_b1", text="Hello")],
        )
    )

    assert results[0].block_id == "p1_b1"
    assert results[0].translated_text == "你好"
    url, headers, payload = calls[0]
    assert url == "https://example.test/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test-key"
    assert payload["model"] == "test-model"
    assert "p1_b1" in payload["messages"][1]["content"]


def test_translate_layout_config_defaults_target_language_to_zh():
    provider = RecordingProvider()
    config = layout_config_from_dict(minimal_layout_dict())

    translated = translate_layout_config(config, provider)

    assert provider.requests[0].target_language == "zh"
    assert translated.pages[0].blocks[0].translated_text == "译文:Original text"


def test_translate_layout_config_sends_only_translatable_text_blocks():
    provider = RecordingProvider()
    data = layout_dict_with_all_block_kinds()
    data["pages"][0]["blocks"].append(
        {
            **data["pages"][0]["blocks"][0],
            "id": "p1_b2",
            "text": "Do not translate",
            "translatable": False,
        }
    )
    config = layout_config_from_dict(data)

    translate_layout_config(config, provider)

    assert [item.block_id for item in provider.requests[0].items] == ["p1_b1"]


def test_translate_layout_config_provider_receives_block_ids_and_original_text():
    provider = RecordingProvider()
    data = minimal_layout_dict()
    data["pages"][0]["blocks"].append(
        {
            **data["pages"][0]["blocks"][0],
            "id": "p1_b2",
            "text": "Second text",
        }
    )
    config = layout_config_from_dict(data)

    translate_layout_config(config, provider)

    assert [(item.block_id, item.text) for item in provider.requests[0].items] == [
        ("p1_b1", "Original text"),
        ("p1_b2", "Second text"),
    ]


def test_translate_layout_config_keeps_original_text_and_writes_translation():
    provider = RecordingProvider()
    data = minimal_layout_dict()
    data["pages"][0]["blocks"][0]["text"] = "Attention is all you need"
    config = layout_config_from_dict(data)

    translated = translate_layout_config(config, provider)
    text_block = translated.pages[0].blocks[0]

    assert text_block.text == "Attention is all you need"
    assert text_block.translated_text == "译文:Attention is all you need"


def test_translate_layout_config_preserves_non_eligible_blocks_without_translation():
    provider = RecordingProvider()
    data = layout_dict_with_all_block_kinds()
    data["pages"][0]["blocks"].append(
        {
            **data["pages"][0]["blocks"][0],
            "id": "p1_b2",
            "text": "Do not translate",
            "translatable": False,
        }
    )
    config = layout_config_from_dict(data)

    translated = translate_layout_config(config, provider)
    serialized = translated.to_dict()["pages"][0]["blocks"]

    assert "translated_text" not in serialized[1]
    assert "translated_text" not in serialized[2]
    assert "translated_text" not in serialized[3]
    assert "translated_text" not in serialized[4]
