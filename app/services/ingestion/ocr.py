"""OCR adapter contracts without a runtime OCR dependency."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.schemas.parse import ParserDiagnostic


@dataclass(frozen=True, slots=True)
class OcrInput:
    """Bytes and source metadata passed to a future OCR implementation."""

    content: bytes
    filename: str
    media_type: str | None = None
    page_number: int | None = None


@dataclass(frozen=True, slots=True)
class OcrPageResult:
    """One page or image result returned by an OCR adapter."""

    page_number: int
    text: str
    confidence_score: float
    diagnostics: list[ParserDiagnostic] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class OcrResult:
    """Full OCR result with text, confidence, and diagnostics kept together."""

    text: str
    pages: list[OcrPageResult] = field(default_factory=list)
    diagnostics: list[ParserDiagnostic] = field(default_factory=list)


class OcrAdapter(Protocol):
    """Interface for optional OCR providers added after the M7 foundation."""

    adapter_name: str

    def extract_text(self, request: OcrInput) -> OcrResult:
        """Extract text from an image or scanned PDF input."""
        ...


class OcrUnavailableAdapter:
    """Default adapter that makes the missing OCR runtime explicit."""

    adapter_name = "unavailable"

    def extract_text(self, request: OcrInput) -> OcrResult:
        """Return no text and a diagnostic instead of attempting hidden OCR."""
        return OcrResult(
            text="",
            diagnostics=[
                ParserDiagnostic(
                    warning_code="ocr_adapter_unavailable",
                    message=(
                        f"OCR adapter is not configured for '{request.filename}'; "
                        "the document remains a needs-OCR input."
                    ),
                    section=None,
                    severity="error",
                    source="ocr",
                )
            ],
        )
