"""Initial multimodal document schemas without OCR execution."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.parse import ParserConfidence, ParserDiagnostic

DocumentSourceType = Literal["text", "file", "url", "image"]


class DocumentInput(BaseModel):
    """Inbound document payload metadata for future multimodal ingestion."""

    source_type: DocumentSourceType
    filename: str | None = None
    media_type: str | None = None
    text: str | None = None
    diagnostics: list[ParserDiagnostic] = Field(default_factory=list)
    confidence: ParserConfidence | None = None
    warnings: list[str] = Field(default_factory=list)


class DocumentSegment(BaseModel):
    """A normalized segment extracted from a document."""

    segment_id: str
    source_type: DocumentSourceType
    text: str
    filename: str | None = None
    media_type: str | None = None
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    diagnostics: list[ParserDiagnostic] = Field(default_factory=list)
    confidence: ParserConfidence | None = None
    warnings: list[str] = Field(default_factory=list)


class NormalizedDocument(BaseModel):
    """Normalized document text plus segment-level metadata."""

    source_type: DocumentSourceType
    filename: str | None = None
    media_type: str | None = None
    text: str
    segments: list[DocumentSegment] = Field(default_factory=list)
    diagnostics: list[ParserDiagnostic] = Field(default_factory=list)
    confidence: ParserConfidence | None = None
    warnings: list[str] = Field(default_factory=list)
