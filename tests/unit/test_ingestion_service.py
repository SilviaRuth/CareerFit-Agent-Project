"""Unit tests for bounded document ingestion."""

from __future__ import annotations

import pytest

from app.services.ingestion.file_ingestion import ingest_file
from tests.conftest import build_docx_bytes, build_pdf_bytes


def test_ingest_docx_file_extracts_paragraph_text() -> None:
    content = build_docx_bytes(
        [
            "Jordan Rivera",
            "Professional Summary",
            "Backend engineer with 5 years building Python services.",
        ]
    )

    result = ingest_file(
        content,
        filename="resume.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert result.source_type == "file"
    assert result.source_name == "resume.docx"
    assert "Jordan Rivera" in result.raw_text
    assert "Professional Summary" in result.raw_text


def test_ingest_pdf_file_extracts_text_without_ocr() -> None:
    content = build_pdf_bytes(
        [
            "Platform Backend Engineer",
            "CareBridge",
            "Required",
            "- Strong Python experience",
        ]
    )

    result = ingest_file(content, filename="jd.pdf", media_type="application/pdf")

    assert result.media_type == "application/pdf"
    assert "Platform Backend Engineer" in result.raw_text
    assert "Strong Python experience" in result.raw_text


def test_ingest_invalid_pdf_file_raises_bounded_value_error() -> None:
    with pytest.raises(ValueError, match="supported text PDF"):
        ingest_file(b"not a real pdf", filename="broken.pdf", media_type="application/pdf")


def test_ingest_invalid_docx_file_raises_bounded_value_error() -> None:
    with pytest.raises(ValueError, match="supported Word document"):
        ingest_file(b"not a real docx", filename="broken.docx")
