"""Errors raised by the optional LLM advisory layer."""

from __future__ import annotations


class LLMError(Exception):
    """Base error for optional LLM generation failures."""


class LLMConfigurationError(LLMError):
    """Raised when LLM generation is enabled without usable configuration."""


class LLMProviderError(LLMError):
    """Raised when a configured provider cannot produce a response."""

