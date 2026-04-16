"""Minimal internal sequencing for grounded generation workflows."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.generation import GroundedGenerationRequest
from app.schemas.match import MatchResult
from app.schemas.parse import JDParseResponse, ResumeParseResponse
from app.services.matching_service import match_schemas
from app.services.parse_service import parse_jd_text, parse_resume_text


@dataclass(slots=True)
class GenerationContext:
    """Shared generation context built from parse plus match outputs."""

    resume_parse: ResumeParseResponse
    jd_parse: JDParseResponse
    match_result: MatchResult


def build_generation_context(request: GroundedGenerationRequest) -> GenerationContext:
    """Run the minimal parse -> match sequence for generation endpoints."""
    resume_parse = parse_resume_text(
        request.resume_text,
        source_name=request.resume_source_name,
    )
    jd_parse = parse_jd_text(
        request.job_description_text,
        source_name=request.jd_source_name,
    )
    match_result = match_schemas(
        resume_parse.parsed_schema,
        jd_parse.parsed_schema,
    )
    return GenerationContext(
        resume_parse=resume_parse,
        jd_parse=jd_parse,
        match_result=match_result,
    )
