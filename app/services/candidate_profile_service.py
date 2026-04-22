"""Reusable candidate profile memory with explicit boundaries and auditability."""

from __future__ import annotations

import hashlib

from app.core.config import CAPABILITY_PATTERNS
from app.schemas.career import (
    CandidateMemoryItem,
    CandidateProfileAudit,
    CandidateProfileMemory,
    CandidateProfileReference,
)
from app.schemas.parse import ResumeParseResponse
from app.services.parse_service import parse_resume_text


def build_candidate_profile_memory(
    resume_text: str,
    source_name: str | None = None,
) -> CandidateProfileMemory:
    """Build reusable, request-scoped candidate context from raw resume text."""
    resume_parse = parse_resume_text(resume_text, source_name=source_name)
    return build_candidate_profile_memory_from_parse(resume_parse)


def build_candidate_profile_memory_from_parse(
    resume_parse: ResumeParseResponse,
) -> CandidateProfileMemory:
    """Create a profile-memory object from an existing parsed resume response."""
    parsed_resume = resume_parse.parsed_schema
    memory_items = _build_memory_items(resume_parse)
    strongest_capabilities = [
        item.label
        for item in memory_items
        if item.memory_type == "skill" and item.support_level == "strong"
    ][:5]
    if not strongest_capabilities:
        strongest_capabilities = [
            item.label for item in memory_items if item.memory_type in {"experience", "project"}
        ][:3]

    development_areas = [
        item.label
        for item in memory_items
        if item.memory_type == "skill" and item.support_level == "weak"
    ][:4]
    domain_signals = _derive_domain_signals(parsed_resume.normalized_text)
    profile_id = hashlib.sha1(parsed_resume.normalized_text.encode("utf-8")).hexdigest()[:12]
    audit = CandidateProfileAudit(
        source_name=resume_parse.source_name,
        audit_notes=[
            "Derived only from the provided resume input.",
            "Request-scoped only; no external profile persistence is used.",
            "Memory items remain evidence-linked and do not add unsupported candidate facts.",
        ],
    )
    return CandidateProfileMemory(
        profile_id=profile_id,
        candidate_name=parsed_resume.candidate_name,
        parser_confidence=resume_parse.parser_confidence,
        strongest_capabilities=strongest_capabilities,
        development_areas=development_areas,
        domain_signals=domain_signals,
        memory_items=memory_items[:10],
        parsed_resume=parsed_resume,
        audit=audit,
    )


def resolve_candidate_profile(reference: CandidateProfileReference) -> CandidateProfileMemory:
    """Resolve raw resume input or embedded profile memory into one profile object."""
    if reference.profile_memory is not None:
        return reference.profile_memory
    return build_candidate_profile_memory(
        reference.resume_text or "",
        source_name=reference.resume_source_name,
    )


def _build_memory_items(resume_parse: ResumeParseResponse) -> list[CandidateMemoryItem]:
    parsed_resume = resume_parse.parsed_schema
    items: list[CandidateMemoryItem] = []

    for skill in parsed_resume.skills:
        items.append(
            CandidateMemoryItem(
                label=skill.normalized_name,
                memory_type="skill",
                support_level="strong" if skill.evidence_strength == "strong" else "weak",
                note="Skill signal preserved from deterministic resume extraction.",
                evidence_used=skill.evidence_spans,
            )
        )

    for experience in parsed_resume.experience_items[:3]:
        items.append(
            CandidateMemoryItem(
                label=experience.heading,
                memory_type="experience",
                support_level="strong",
                note="Experience example available for interview and recommendation grounding.",
                evidence_used=experience.evidence_spans,
            )
        )

    for project in parsed_resume.project_items[:2]:
        items.append(
            CandidateMemoryItem(
                label=project.summary[:60],
                memory_type="project",
                support_level="strong",
                note="Project evidence can support adjacent-skill recommendations.",
                evidence_used=project.evidence_spans,
            )
        )

    for education in parsed_resume.education_items[:1]:
        items.append(
            CandidateMemoryItem(
                label=education.degree or education.summary[:60],
                memory_type="education",
                support_level="strong",
                note="Education evidence stays available for requirement checks.",
                evidence_used=education.evidence_spans,
            )
        )

    if parsed_resume.summary:
        summary_evidence = [
            span for span in parsed_resume.evidence_spans if span.section == "summary"
        ][:1]
        items.append(
            CandidateMemoryItem(
                label="summary",
                memory_type="summary",
                support_level="weak",
                note="Summary claims are preserved for audit but are not treated as strong evidence.",
                evidence_used=summary_evidence,
            )
        )

    return items


def _derive_domain_signals(normalized_text: str) -> list[str]:
    signals: list[str] = []
    lowered = normalized_text.lower()
    for label in ("healthcare", "logistics", "cloud_platform"):
        if any(pattern in lowered for pattern in CAPABILITY_PATTERNS[label]):
            signals.append(label)
    return signals
