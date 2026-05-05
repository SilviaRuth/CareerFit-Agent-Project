"""Unit tests for optional LLM configuration loading."""

from __future__ import annotations

from app.llm.config import load_llm_settings, load_local_dotenv


def test_load_local_dotenv_populates_missing_values_without_overrides(
    tmp_path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "ENABLE_LLM_EXTRACTION=true",
                "LLM_EXTRACTION_DEBUG=true",
                "LLM_PROVIDER=openai",
                "LLM_MODEL=from-dotenv",
                "OPENAI_API_KEY='test-key'",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("CAREERFIT_LOAD_DOTENV", raising=False)
    monkeypatch.delenv("ENABLE_LLM_EXTRACTION", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_MODEL", "explicit-model")

    load_local_dotenv(env_file)
    settings = load_llm_settings()

    assert settings.enable_llm_extraction is True
    assert settings.enable_llm_extraction_debug is True
    assert settings.provider == "openai"
    assert settings.model == "explicit-model"
    assert settings.api_key == "test-key"
    monkeypatch.delenv("ENABLE_LLM_EXTRACTION", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_load_local_dotenv_can_be_disabled(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ENABLE_LLM_EXTRACTION=true", encoding="utf-8")
    monkeypatch.setenv("CAREERFIT_LOAD_DOTENV", "false")
    monkeypatch.delenv("ENABLE_LLM_EXTRACTION", raising=False)

    load_local_dotenv(env_file)

    assert load_llm_settings().enable_llm_extraction is False
