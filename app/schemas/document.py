"""Initial multimodal document schemas without OCR execution."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.parse import ParserConfidence, ParserDiagnostic

DocumentSourceType = Literal["text", "file", "url", "image"]
DocumentModality = Literal["text", "pdf", "docx", "image", "mixed", "unknown"]
OcrStatus = Literal["not_required", "required", "completed", "failed", "unavailable"]
SegmentType = Literal["text", "table", "image", "header", "footer", "unknown"]


class DocumentInput(BaseModel):
    """Inbound document payload metadata for future multimodal ingestion."""

    source_type: DocumentSourceType
    modality: DocumentModality = "unknown"
    filename: str | None = None
    media_type: str | None = None
    text: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    ocr_status: OcrStatus = "not_required"
    diagnostics: list[ParserDiagnostic] = Field(default_factory=list)
    confidence: ParserConfidence | None = None
    warnings: list[str] = Field(default_factory=list)


class DocumentPage(BaseModel):
    """Page-level multimodal diagnostics before OCR is available."""

    page_number: int = Field(ge=1)
    text: str = ""
    has_extractable_text: bool = False
    requires_ocr: bool = False
    diagnostics: list[ParserDiagnostic] = Field(default_factory=list)
    confidence: ParserConfidence | None = None


class DocumentSegment(BaseModel):
    """A normalized segment extracted from a document."""

    segment_id: str
    source_type: DocumentSourceType
    modality: DocumentModality = "unknown"
    segment_type: SegmentType = "text"
    text: str
    filename: str | None = None
    media_type: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    requires_ocr: bool = False
    ocr_status: OcrStatus = "not_required"
    unsupported_reason: str | None = None
    diagnostics: list[ParserDiagnostic] = Field(default_factory=list)
    confidence: ParserConfidence | None = None
    warnings: list[str] = Field(default_factory=list)


class NormalizedDocument(BaseModel):
    """Normalized document text plus segment-level metadata."""

    source_type: DocumentSourceType
    modality: DocumentModality = "unknown"
    filename: str | None = None
    media_type: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    text: str
    pages: list[DocumentPage] = Field(default_factory=list)
    segments: list[DocumentSegment] = Field(default_factory=list)
    ocr_status: OcrStatus = "not_required"
    requires_ocr: bool = False
    diagnostics: list[ParserDiagnostic] = Field(default_factory=list)
    confidence: ParserConfidence | None = None
    warnings: list[str] = Field(default_factory=list)
