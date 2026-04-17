"""Shared internal context for grounded generation orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.common import EvidenceSpan
from app.schemas.generation import GenerationGate, GenerationWarning
from app.schemas.match import MatchResult
from app.schemas.parse import JDParseResponse, ResumeParseResponse


@dataclass(slots=True)
class GroundedFlowContext:
    """Parse, match, and gating artifacts shared by grounded generation services."""

    resume_parse: ResumeParseResponse
    jd_parse: JDParseResponse
    match_result: MatchResult
    gating: GenerationGate | None = None
    generation_warnings: list[GenerationWarning] = field(default_factory=list)
    evidence_registry: list[EvidenceSpan] = field(default_factory=list)
