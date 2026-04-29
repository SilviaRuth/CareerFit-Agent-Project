"""Shared tokenization helpers for additive career workflow services."""

from __future__ import annotations

import re

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize_keywords(text: str) -> set[str]:
    """Tokenize keyword-style labels using the existing retrieval/semantic semantics."""
    return {token for token in TOKEN_RE.findall(text.lower()) if len(token) > 1}
