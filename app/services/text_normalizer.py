"""Deterministic text normalization helpers for Milestone 1 fixtures."""

from __future__ import annotations

import re

from app.schemas.parse import ParserDiagnostic


UNICODE_REPLACEMENTS = str.maketrans(
    {
        "\u00a0": " ",
        "\u2002": " ",
        "\u2003": " ",
        "\u2009": " ",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\u2023": "-",
        "\u2043": "-",
        "\u2219": "-",
        "\u25aa": "-",
        "\u25cf": "-",
        "\u25e6": "-",
        "\uff1a": ":",
        "\u2026": "...",
    }
)

BULLET_LINE_PATTERN = re.compile(r"^\s*[-*+]\s*")


def normalize_text(text: str, document_type: str | None = None) -> str:
    """Normalize whitespace and bullets while preserving section structure."""
    cleaned_text, _ = normalize_text_with_diagnostics(text, document_type=document_type)
    return cleaned_text


def normalize_text_with_diagnostics(
    text: str,
    document_type: str | None = None,
) -> tuple[str, list[ParserDiagnostic]]:
    """Normalize noisy text and return structured normalization diagnostics."""
    warnings: list[ParserDiagnostic] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    translated = normalized.translate(UNICODE_REPLACEMENTS)
    if translated != normalized:
        warnings.append(
            ParserDiagnostic(
                warning_code="unicode_punctuation_normalized",
                message="Unicode punctuation and spacing were normalized to ASCII-safe forms.",
                section=None,
                severity="info",
                source="normalization",
            )
        )
        normalized = translated

    cleaned_lines: list[str] = []
    previous_blank = False
    bullet_normalized = False
    colon_headers_normalized = False
    blank_lines_collapsed = False
    for raw_line in normalized.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            elif cleaned_lines:
                blank_lines_collapsed = True
            previous_blank = True
            continue

        line, line_bullet_normalized = _normalize_bullet_prefix(line)
        bullet_normalized = bullet_normalized or line_bullet_normalized
        line, line_header_normalized = _normalize_colon_header(line, document_type=document_type)
        colon_headers_normalized = colon_headers_normalized or line_header_normalized
        cleaned_lines.append(line)
        previous_blank = False

    if bullet_normalized:
        warnings.append(
            ParserDiagnostic(
                warning_code="bullet_format_normalized",
                message="Bullet markers were normalized into deterministic dash-prefixed lines.",
                section=None,
                severity="info",
                source="normalization",
            )
        )

    if colon_headers_normalized:
        warnings.append(
            ParserDiagnostic(
                warning_code="colon_headers_normalized",
                message="Inline colon headers were split into canonical section header lines.",
                section=None,
                severity="info",
                source="normalization",
            )
        )

    if blank_lines_collapsed:
        warnings.append(
            ParserDiagnostic(
                warning_code="blank_lines_collapsed",
                message="Repeated blank lines were collapsed to stabilize parsing.",
                section=None,
                severity="info",
                source="normalization",
            )
        )

    return "\n".join(cleaned_lines).strip(), warnings


def _normalize_bullet_prefix(line: str) -> tuple[str, bool]:
    """Normalize common bullet prefixes while leaving plain text untouched."""
    if BULLET_LINE_PATTERN.match(line):
        normalized_line = BULLET_LINE_PATTERN.sub("- ", line)
        return normalized_line, normalized_line != line
    return line, False


def _normalize_colon_header(
    line: str,
    document_type: str | None = None,
) -> tuple[str, bool]:
    """Split compact `Header: content` patterns into separate lines."""
    if document_type is None or ":" not in line:
        return line, False

    header_candidate, remainder = line.split(":", 1)
    if not remainder.strip():
        return line, False

    normalized_header = header_candidate.strip().lower()
    if document_type == "resume":
        header_names = {
            "summary",
            "professional summary",
            "career summary",
            "profile",
            "skills",
            "technical skills",
            "core competencies",
        }
    else:
        header_names = {
            "responsibilities",
            "what you'll do",
            "what you will do",
            "required",
            "requirements",
            "must have",
            "preferred",
            "preferred qualifications",
            "nice to have",
            "education",
        }

    if normalized_header not in header_names:
        return line, False
    return f"{header_candidate.strip()}\n{remainder.strip()}", True
