"""Unit tests for optional LLM provider adapters."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.llm.config import LLMSettings
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.llm.providers import FakeLLMClient, OpenAILLMClient, build_llm_client


class _FakeResponses:
    def __init__(self, response: object) -> None:
        self.response = response
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        return self.response


class _FakeOpenAIClient:
    def __init__(self, response: object) -> None:
        self.responses = _FakeResponses(response)


def test_openai_client_uses_responses_api_with_structured_output() -> None:
    raw_json = '{"summary":"ok","recommendations":[],"limitations":[]}'
    fake_client = _FakeOpenAIClient(SimpleNamespace(output_text=raw_json))
    settings = LLMSettings(
        enable_llm_generation=True,
        provider="openai",
        model="test-model",
        temperature=0.0,
        max_output_tokens=123,
        api_key="test-key",
    )

    client = OpenAILLMClient(settings, client=fake_client)
    result = client.generate_json("prompt text", "LLMRecommendationOutput")

    assert result == raw_json
    assert fake_client.responses.kwargs is not None
    assert fake_client.responses.kwargs["model"] == "test-model"
    assert fake_client.responses.kwargs["input"] == "prompt text"
    assert fake_client.responses.kwargs["temperature"] == 0.0
    assert fake_client.responses.kwargs["max_output_tokens"] == 123
    text_config = fake_client.responses.kwargs["text"]
    assert isinstance(text_config, dict)
    assert text_config["format"]["type"] == "json_schema"
    assert text_config["format"]["name"] == "LLMRecommendationOutput"
    assert "schema" in text_config["format"]


def test_openai_client_supports_extraction_schema() -> None:
    raw_json = (
        '{"resume":{"candidate_name":"","summary":"","skills":[],"experience_items":[],'
        '"project_items":[],"education_items":[],"total_years_experience":null},'
        '"job_description":{"job_title":"","company":"","responsibilities":[],'
        '"required_requirements":[],"preferred_requirements":[],"education_requirements":[],'
        '"seniority_hint":null,"domain_hint":null}}'
    )
    fake_client = _FakeOpenAIClient(SimpleNamespace(output_text=raw_json))
    settings = LLMSettings(enable_llm_extraction=True, api_key="test-key")

    result = OpenAILLMClient(settings, client=fake_client).generate_json(
        "prompt text",
        "LLMNaturalLanguageExtractionOutput",
    )

    assert result == raw_json
    assert fake_client.responses.kwargs is not None
    text_config = fake_client.responses.kwargs["text"]
    assert isinstance(text_config, dict)
    assert text_config["format"]["name"] == "LLMNaturalLanguageExtractionOutput"


def test_openai_client_extracts_text_from_output_items() -> None:
    response = {
        "output": [
            {
                "content": [
                    {
                        "type": "output_text",
                        "text": '{"summary":"ok","recommendations":[],"limitations":[]}',
                    }
                ]
            }
        ]
    }
    fake_client = _FakeOpenAIClient(response)
    settings = LLMSettings(enable_llm_generation=True, api_key="test-key")

    result = OpenAILLMClient(settings, client=fake_client).generate_json(
        "prompt text",
        "LLMRecommendationOutput",
    )

    assert result == '{"summary":"ok","recommendations":[],"limitations":[]}'


def test_openai_client_wraps_provider_errors() -> None:
    class FailingResponses:
        def create(self, **kwargs: object) -> object:
            raise RuntimeError("rate limited")

    fake_client = SimpleNamespace(responses=FailingResponses())
    settings = LLMSettings(enable_llm_generation=True, api_key="test-key")

    with pytest.raises(LLMProviderError, match="OpenAI provider request failed"):
        OpenAILLMClient(settings, client=fake_client).generate_json(
            "prompt text",
            "LLMRecommendationOutput",
        )


def test_build_llm_client_dispatches_supported_providers() -> None:
    assert isinstance(build_llm_client(LLMSettings(provider="fake")), FakeLLMClient)

    with pytest.raises(LLMConfigurationError, match="Unsupported LLM provider"):
        build_llm_client(
            LLMSettings(enable_llm_generation=True, provider="unknown", api_key="test-key")
        )


def test_openai_client_requires_api_key() -> None:
    with pytest.raises(LLMConfigurationError, match="no API key"):
        OpenAILLMClient(LLMSettings(enable_llm_generation=True, api_key=None))
