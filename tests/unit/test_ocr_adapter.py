"""Tests for OCR adapter contracts without enabling OCR runtime behavior."""

from __future__ import annotations

from app.services.ingestion.ocr import OcrInput, OcrUnavailableAdapter


def test_unavailable_ocr_adapter_returns_explicit_error_diagnostic() -> None:
    adapter = OcrUnavailableAdapter()

    result = adapter.extract_text(
        OcrInput(content=b"placeholder", filename="resume.png", media_type="image/png")
    )

    assert result.text == ""
    assert result.pages == []
    assert result.diagnostics[0].warning_code == "ocr_adapter_unavailable"
    assert result.diagnostics[0].source == "ocr"
