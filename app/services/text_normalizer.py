"""Deterministic text normalization helpers for Milestone 1 fixtures."""

from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    """Normalize whitespace and bullets while preserving section structure."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("•", "- ").replace("–", "- ").replace("—", "- ")

    cleaned_lines: list[str] = []
    previous_blank = False
    for raw_line in normalized.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue
        cleaned_lines.append(line)
        previous_blank = False

    return "\n".join(cleaned_lines).strip()
