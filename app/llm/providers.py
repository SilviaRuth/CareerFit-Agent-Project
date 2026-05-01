"""Provider adapters and test clients for optional LLM generation."""

from __future__ import annotations

from typing import Any

from app.llm.base import LLMClient
from app.llm.config import LLMSettings
from app.llm.errors import LLMConfigurationError


class FakeLLMClient:
    """Deterministic test client that never calls external APIs."""

    def __init__(self, response: dict[str, Any] | str) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def generate_json(self, prompt: str, schema_name: str) -> dict[str, Any] | str:
        """Record the call and return the configured fake response."""
        self.calls.append((prompt, schema_name))
        return self.response


class ConfiguredExternalLLMClient:
    """Placeholder for real provider adapters injected by deployment code."""

    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def generate_json(self, prompt: str, schema_name: str) -> dict[str, Any] | str:
        """Fail cleanly instead of making hidden external calls from the default app."""
        raise LLMConfigurationError(
            "No concrete external LLM client is configured for this runtime. "
            "Inject an LLMClient adapter or keep ENABLE_LLM_GENERATION=false."
        )


def build_llm_client(settings: LLMSettings) -> LLMClient:
    """Build a provider-neutral client from settings."""
    if settings.provider == "fake":
        return FakeLLMClient({})
    if not settings.api_key:
        raise LLMConfigurationError(
            f"LLM provider '{settings.provider}' is enabled but no API key is configured."
        )
    return ConfiguredExternalLLMClient(settings)

