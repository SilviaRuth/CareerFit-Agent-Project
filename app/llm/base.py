"""Provider-neutral LLM client interface."""

from __future__ import annotations

from typing import Any, Protocol


class LLMClient(Protocol):
    """Minimal JSON-generation interface implemented by provider adapters."""

    def generate_json(self, prompt: str, schema_name: str) -> dict[str, Any] | str:
        """Return provider output intended to validate against ``schema_name``."""

