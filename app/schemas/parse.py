"""Schemas for Milestone 2A parsing and ingestion responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.jd import JDSchema
from app.schemas.resume import ResumeSchema


class ParseTextRequest(BaseModel):
    """JSON text input contract for parse endpoints."""

    text: str
    source_name: str | None = None


class ParserDiagnostic(BaseModel):
    """Structured warning emitted during ingestion, normalization, or extraction."""

    warning_code: str
    message: str
    section: str | None = None
    severity: Literal["info", "warning", "error"] = "warning"
    source: Literal["ingestion", "normalization", "extraction"]


class ParserConfidence(BaseModel):
    """Confidence metadata for bounded parsing behavior."""

    score: float = Field(ge=0.0, le=1.0)
    level: Literal["high", "medium", "low"]
    extraction_complete: bool = False
    factors: list[str] = Field(default_factory=list)


class UnsupportedSegment(BaseModel):
    """A text segment the bounded parser could not confidently place."""

    text: str
    section: str | None = None
    reason: str
    source: Literal["ingestion", "extraction"]


class ParseResponseBase(BaseModel):
    """Common response fields for resume and JD parse endpoints."""

    source_type: Literal["text", "file"]
    source_name: str | None = None
    media_type: str | None = None
    raw_text: str
    cleaned_text: str
    warnings: list[ParserDiagnostic] = Field(default_factory=list)
    parser_confidence: ParserConfidence
    unsupported_segments: list[UnsupportedSegment] = Field(default_factory=list)


class ResumeParseResponse(ParseResponseBase):
    """Response contract for `POST /parse/resume`."""

    model_config = ConfigDict(populate_by_name=True)

    parsed_schema: ResumeSchema = Field(alias="schema", serialization_alias="schema")


class JDParseResponse(ParseResponseBase):
    """Response contract for `POST /parse/jd`."""

    model_config = ConfigDict(populate_by_name=True)

    parsed_schema: JDSchema = Field(alias="schema", serialization_alias="schema")
