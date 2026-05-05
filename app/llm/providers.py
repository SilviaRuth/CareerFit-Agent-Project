"""Provider adapters and test clients for optional LLM generation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from app.llm.base import LLMClient
from app.llm.config import LLMSettings
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.schemas.llm_extraction import LLMNaturalLanguageExtractionOutput
from app.schemas.llm_generation import LLMRecommendationOutput

SCHEMA_BY_NAME = {
    "LLMRecommendationOutput": LLMRecommendationOutput,
    "LLMNaturalLanguageExtractionOutput": LLMNaturalLanguageExtractionOutput,
}


class FakeLLMClient:
    """Deterministic test client that never calls external APIs."""

    def __init__(self, response: dict[str, Any] | str) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def generate_json(self, prompt: str, schema_name: str) -> dict[str, Any] | str:
        """Record the call and return the configured fake response."""
        self.calls.append((prompt, schema_name))
        return self.response


class OpenAILLMClient:
    """OpenAI Responses API adapter for advisory JSON generation."""

    def __init__(self, settings: LLMSettings, client: Any | None = None) -> None:
        self.settings = settings
        if not settings.api_key:
            raise LLMConfigurationError(
                "LLM provider 'openai' is enabled but no API key is configured."
            )
        if client is not None:
            self._client = client
            return

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMConfigurationError(
                "The OpenAI SDK is required for LLM_PROVIDER=openai. "
                "Install project dependencies or keep ENABLE_LLM_GENERATION=false."
            ) from exc

        self._client = OpenAI(api_key=settings.api_key)

    def generate_json(self, prompt: str, schema_name: str) -> dict[str, Any] | str:
        """Return raw JSON text produced by OpenAI for downstream validation."""
        try:
            response = self._client.responses.create(
                model=self.settings.model,
                input=prompt,
                temperature=self.settings.temperature,
                max_output_tokens=self.settings.max_output_tokens,
                text={"format": _json_schema_format(schema_name)},
            )
        except Exception as exc:
            raise LLMProviderError(f"OpenAI provider request failed: {exc}") from exc

        return _extract_output_text(response)


def build_llm_client(settings: LLMSettings) -> LLMClient:
    """Build a provider-neutral client from settings."""
    if settings.provider == "fake":
        return FakeLLMClient({})
    if settings.provider != "openai":
        raise LLMConfigurationError(
            f"Unsupported LLM provider '{settings.provider}'. Supported providers: openai, fake."
        )
    if not settings.api_key:
        raise LLMConfigurationError(
            f"LLM provider '{settings.provider}' is enabled but no API key is configured."
        )
    return OpenAILLMClient(settings)


def _json_schema_format(schema_name: str) -> dict[str, Any]:
    schema_model = SCHEMA_BY_NAME.get(schema_name)
    if schema_model is None:
        raise LLMConfigurationError(f"Unsupported OpenAI response schema '{schema_name}'.")
    return {
        "type": "json_schema",
        "name": schema_name,
        "schema": _strip_json_schema_metadata(schema_model.model_json_schema()),
        "strict": False,
    }


def _strip_json_schema_metadata(value: Any) -> Any:
    """Remove Pydantic presentation metadata before sending schema to OpenAI."""
    if isinstance(value, dict):
        return {
            key: _strip_json_schema_metadata(inner)
            for key, inner in value.items()
            if key not in {"default", "examples", "title"}
        }
    if isinstance(value, list):
        return [_strip_json_schema_metadata(item) for item in value]
    return value


def _extract_output_text(response: Any) -> str:
    output_text = _mapping_or_attr(response, "output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output_items = _mapping_or_attr(response, "output") or []
    for item in output_items:
        content_items = _mapping_or_attr(item, "content") or []
        for content in content_items:
            text = _mapping_or_attr(content, "text")
            if isinstance(text, str) and text.strip():
                return text

    try:
        return json.dumps(response.model_dump(mode="json"))
    except AttributeError as exc:
        raise LLMProviderError("OpenAI response did not contain output text.") from exc


def _mapping_or_attr(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)
