"""Composition layer for ingestion, normalization, extraction, and parse responses."""

from __future__ import annotations

from typing import Literal

from app.schemas.jd import JDSchema
from app.schemas.parse import (
    JDParseResponse,
    ParserConfidence,
    ParserDiagnostic,
    ResumeParseResponse,
    UnsupportedSegment,
)
from app.schemas.resume import ResumeSchema
from app.services.extraction_service import analyze_jd_text, analyze_resume_text
from app.services.ingestion.file_ingestion import ingest_file, ingest_text
from app.services.text_normalizer import normalize_text_with_diagnostics


def parse_resume_text(text: str, source_name: str | None = None) -> ResumeParseResponse:
    """Parse resume text into a structured response envelope."""
    ingested = ingest_text(text, source_name=source_name)
    return _build_resume_response(
        ingested.raw_text,
        ingested.source_type,
        ingested.source_name,
        ingested.media_type,
        ingested.warnings,
    )


def parse_resume_file(
    content: bytes,
    filename: str,
    media_type: str | None = None,
) -> ResumeParseResponse:
    """Parse a supported resume file into a structured response envelope."""
    ingested = ingest_file(content, filename=filename, media_type=media_type)
    return _build_resume_response(
        ingested.raw_text,
        ingested.source_type,
        ingested.source_name,
        ingested.media_type,
        ingested.warnings,
    )


def parse_jd_text(text: str, source_name: str | None = None) -> JDParseResponse:
    """Parse JD text into a structured response envelope."""
    ingested = ingest_text(text, source_name=source_name)
    return _build_jd_response(
        ingested.raw_text,
        ingested.source_type,
        ingested.source_name,
        ingested.media_type,
        ingested.warnings,
    )


def parse_jd_file(content: bytes, filename: str, media_type: str | None = None) -> JDParseResponse:
    """Parse a supported JD file into a structured response envelope."""
    ingested = ingest_file(content, filename=filename, media_type=media_type)
    return _build_jd_response(
        ingested.raw_text,
        ingested.source_type,
        ingested.source_name,
        ingested.media_type,
        ingested.warnings,
    )


def _build_resume_response(
    raw_text: str,
    source_type: Literal["text", "file"],
    source_name: str | None,
    media_type: str | None,
    ingestion_warnings: list[ParserDiagnostic],
) -> ResumeParseResponse:
    """Build the parse response for resume-like content."""
    cleaned_text, normalization_warnings = normalize_text_with_diagnostics(
        raw_text,
        document_type="resume",
    )
    extraction_result = analyze_resume_text(cleaned_text, pre_normalized=True)
    warnings = ingestion_warnings + normalization_warnings + extraction_result.warnings
    unsupported_segments = _build_ingestion_unsupported_segments(
        ingestion_warnings
    ) + extraction_result.unsupported_segments
    parser_confidence = _build_parser_confidence(
        extraction_result.schema,
        warnings,
        unsupported_segments,
        document_type="resume",
    )
    return ResumeParseResponse(
        source_type=source_type,
        source_name=source_name,
        media_type=media_type,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        parsed_schema=extraction_result.schema,
        warnings=warnings,
        parser_confidence=parser_confidence,
        unsupported_segments=unsupported_segments,
    )


def _build_jd_response(
    raw_text: str,
    source_type: Literal["text", "file"],
    source_name: str | None,
    media_type: str | None,
    ingestion_warnings: list[ParserDiagnostic],
) -> JDParseResponse:
    """Build the parse response for JD-like content."""
    cleaned_text, normalization_warnings = normalize_text_with_diagnostics(
        raw_text,
        document_type="job_description",
    )
    extraction_result = analyze_jd_text(cleaned_text, pre_normalized=True)
    warnings = ingestion_warnings + normalization_warnings + extraction_result.warnings
    unsupported_segments = _build_ingestion_unsupported_segments(
        ingestion_warnings
    ) + extraction_result.unsupported_segments
    parser_confidence = _build_parser_confidence(
        extraction_result.schema,
        warnings,
        unsupported_segments,
        document_type="job_description",
    )
    return JDParseResponse(
        source_type=source_type,
        source_name=source_name,
        media_type=media_type,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        parsed_schema=extraction_result.schema,
        warnings=warnings,
        parser_confidence=parser_confidence,
        unsupported_segments=unsupported_segments,
    )


def _build_ingestion_unsupported_segments(
    warnings: list[ParserDiagnostic],
) -> list[UnsupportedSegment]:
    """Expose unsupported multimodal inputs separately from extraction failures."""
    unsupported_codes = {
        "image_requires_ocr": "image_requires_ocr",
        "pdf_scanned_needs_ocr": "scanned_pdf_requires_ocr",
    }
    segments: list[UnsupportedSegment] = []
    for warning in warnings:
        reason = unsupported_codes.get(warning.warning_code)
        if reason is None:
            continue
        segments.append(
            UnsupportedSegment(
                text="",
                section=None,
                reason=reason,
                source="ingestion",
            )
        )
    return segments


def _build_parser_confidence(
    schema: ResumeSchema | JDSchema,
    warnings: list[ParserDiagnostic],
    unsupported_segments: list[UnsupportedSegment],
    document_type: Literal["resume", "job_description"],
) -> ParserConfidence:
    """Compute bounded parser confidence metadata from schema completeness and warnings."""
    score = 1.0
    factors: list[str] = []

    for warning in warnings:
        if warning.severity == "error":
            score -= 0.25
            factors.append(f"error:{warning.warning_code}")
        elif warning.severity == "warning":
            score -= 0.12
            factors.append(f"warning:{warning.warning_code}")
        else:
            score -= 0.02
            factors.append(f"info:{warning.warning_code}")

    if unsupported_segments:
        score -= min(0.15, 0.05 * len(unsupported_segments))
        factors.append("unsupported_segments_present")

    if document_type == "resume":
        if not schema.candidate_name.strip():
            score -= 0.15
            factors.append("missing_candidate_name")
        if not schema.summary.strip():
            score -= 0.15
            factors.append("missing_summary")
        if not schema.skills:
            score -= 0.12
            factors.append("missing_skills")
        if not schema.experience_items:
            score -= 0.12
            factors.append("missing_experience")
        extraction_complete = bool(
            schema.candidate_name.strip()
            and schema.summary.strip()
            and schema.skills
            and schema.experience_items
        )
    else:
        if not schema.job_title.strip():
            score -= 0.15
            factors.append("missing_job_title")
        if not schema.company.strip():
            score -= 0.1
            factors.append("missing_company")
        if not schema.required_requirements:
            score -= 0.2
            factors.append("missing_required_requirements")
        extraction_complete = bool(
            schema.job_title.strip() and schema.company.strip() and schema.required_requirements
        )

    score = max(0.0, min(1.0, round(score, 2)))
    if score >= 0.85:
        level = "high"
    elif score >= 0.6:
        level = "medium"
    else:
        level = "low"

    return ParserConfidence(
        score=score,
        level=level,
        extraction_complete=extraction_complete,
        factors=factors,
    )
