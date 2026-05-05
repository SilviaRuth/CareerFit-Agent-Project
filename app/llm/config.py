"""Environment-backed configuration for optional LLM generation."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


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


def load_local_dotenv(path: str | Path | None = None) -> None:
    """Load repo-local .env values without overriding explicit environment variables."""
    if path is None and "pytest" in sys.modules:
        return
    if os.getenv("CAREERFIT_LOAD_DOTENV", "true").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return

    env_path = Path(path) if path is not None else Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if not name or name in os.environ:
            continue
        os.environ[name] = _clean_env_value(value)


def _clean_env_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1]
    return cleaned


@dataclass(frozen=True, slots=True)
class LLMSettings:
    """Runtime settings for the optional advisory generation layer."""

    enable_llm_generation: bool = False
    enable_llm_extraction: bool = False
    enable_llm_extraction_debug: bool = False
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
        enable_llm_extraction=_env_bool("ENABLE_LLM_EXTRACTION", False),
        enable_llm_extraction_debug=_env_bool("LLM_EXTRACTION_DEBUG", False),
        provider=provider,
        model=os.getenv("LLM_MODEL", "gpt-5.4-mini"),
        temperature=_env_float("LLM_TEMPERATURE", 0.0),
        max_output_tokens=_env_int("LLM_MAX_OUTPUT_TOKENS", 800),
        api_key=api_key,
    )
