"""Environment-backed configuration for optional LLM generation."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class LLMSettings:
    """Runtime settings for the optional advisory generation layer."""

    enable_llm_generation: bool = False
    provider: str = "openai"
    model: str = "gpt-5.4-mini"
    temperature: float = 0.0
    max_output_tokens: int = 800
    api_key: str | None = None


def load_llm_settings() -> LLMSettings:
    """Load LLM settings without requiring any provider credentials."""
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower() or "openai"
    api_key = os.getenv("LLM_API_KEY")
    if provider == "openai":
        api_key = api_key or os.getenv("OPENAI_API_KEY")
    return LLMSettings(
        enable_llm_generation=_env_bool("ENABLE_LLM_GENERATION", False),
        provider=provider,
        model=os.getenv("LLM_MODEL", "gpt-5.4-mini"),
        temperature=_env_float("LLM_TEMPERATURE", 0.0),
        max_output_tokens=_env_int("LLM_MAX_OUTPUT_TOKENS", 800),
        api_key=api_key,
    )

