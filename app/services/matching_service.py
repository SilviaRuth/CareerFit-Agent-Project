"""Rule-based matching service for the Milestone 1 backend MVP."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import (
    ASSERTIVE_CLAIM_TERMS,
    CAPABILITY_PATTERNS,
    MATCH_WEIGHTS,
    NEGATION_TERMS,
    WEAK_PROJECT_TERMS,
)
from app.schemas.common import EducationItem, EvidenceSpan, RequirementItem
from app.schemas.jd import JDSchema
from app.schemas.match import (
    BlockerFlags,
    DimensionScores,
    EvidenceSummary,
    GapItem,
    MatchResult,
    RequirementMatch,
)
from app.schemas.resume import ResumeSchema
from app.services.adaptation_service import (
    build_adaptation_summary,
    order_strength_matches,
    sort_gaps_for_adaptation,
)
from app.services.extraction_service import extract_jd_schema, extract_resume_schema
from app.services.workflow_trace_service import attach_match_trace


@dataclass
class CapabilityEvidence:
    """Internal evidence buckets used by the deterministic matcher."""

    strong: list[EvidenceSpan] = field(default_factory=list)
    weak: list[EvidenceSpan] = field(default_factory=list)
    claims: list[EvidenceSpan] = field(default_factory=list)
    project_strong: list[EvidenceSpan] = field(default_factory=list)


def match_resume_to_jd(
    resume_text: str,
    job_description_text: str,
    *,
    include_trace: bool = True,
) -> MatchResult:
    """Run the deterministic parse -> extract -> match Milestone 1 pipeline."""
    resume_schema = extract_resume_schema(resume_text)
    jd_schema = extract_jd_schema(job_description_text)
    result = match_schemas(resume_schema, jd_schema)
    if not include_trace:
        return result
    return attach_match_trace(result)


def match_schemas(resume_schema: ResumeSchema, jd_schema: JDSchema) -> MatchResult:
    """Match a parsed resume schema against a parsed JD schema."""
    evidence_map = _build_resume_evidence_map(resume_schema)

    required_matches, required_gaps = _evaluate_requirements(
        jd_schema.required_requirements,
        resume_schema,
        jd_schema,
        evidence_map,
    )
    preferred_matches, preferred_gaps = _evaluate_requirements(
        jd_schema.preferred_requirements + jd_schema.education_requirements,
        resume_schema,
        jd_schema,
        evidence_map,
    )

    blocker_flags = BlockerFlags(
        missing_required_skills=any(
            match.requirement_type in {"skill", "domain"} and match.status == "missing"
            for match in required_matches
        ),
        seniority_mismatch=any(gap.gap_type == "seniority_mismatch" for gap in required_gaps),
        unsupported_claims=any(
            bucket.claims and not bucket.strong for bucket in evidence_map.values()
        ),
    )

    dimension_scores = _build_dimension_scores(
        required_matches=required_matches,
        preferred_matches=preferred_matches,
        resume_schema=resume_schema,
        jd_schema=jd_schema,
        evidence_map=evidence_map,
    )
    overall_score = _weighted_overall_score(dimension_scores)

    adaptation_summary = build_adaptation_summary(
        jd_schema=jd_schema,
        required_matches=required_matches,
        preferred_matches=preferred_matches,
        gaps=required_gaps + preferred_gaps,
    )
    all_gaps = sort_gaps_for_adaptation(required_gaps + preferred_gaps, adaptation_summary)
    strengths = [
        f"Matched {match.requirement_priority} {match.requirement_label} with resume evidence."
        for match in order_strength_matches(
            required_matches + preferred_matches, adaptation_summary
        )
    ][:3]

    explanations = [
        (
            f"Overall score is {overall_score} based on weighted rule-based matching "
            "across skills, experience, projects, domain fit, and education."
        ),
        (
            "Required matches: "
            f"{sum(match.status == 'matched' for match in required_matches)}/"
            f"{len(required_matches) or 1}."
        ),
        (
            "Blockers: "
            f"missing_required_skills={blocker_flags.missing_required_skills}, "
            f"seniority_mismatch={blocker_flags.seniority_mismatch}, "
            f"unsupported_claims={blocker_flags.unsupported_claims}."
        ),
    ]
    if adaptation_summary.explanation:
        explanations.append(adaptation_summary.explanation)

    all_evidence = _dedupe_spans(
        span
        for match in required_matches + preferred_matches
        for span in match.resume_evidence + match.jd_evidence
    )
    all_evidence.extend(
        span
        for gap in all_gaps
        for span in gap.resume_evidence + gap.jd_evidence
        if span not in all_evidence
    )

    return MatchResult(
        overall_score=overall_score,
        dimension_scores=dimension_scores,
        required_matches=required_matches,
        preferred_matches=preferred_matches,
        gaps=all_gaps,
        blocker_flags=blocker_flags,
        strengths=strengths,
        explanations=explanations,
        evidence_spans=all_evidence,
        evidence_summary=_build_evidence_summary(
            evidence_spans=all_evidence,
            required_matches=required_matches,
            preferred_matches=preferred_matches,
            gaps=all_gaps,
        ),
        adaptation_summary=adaptation_summary,
    )


def _evaluate_requirements(
    requirements: list[RequirementItem],
    resume_schema: ResumeSchema,
    jd_schema: JDSchema,
    evidence_map: dict[str, CapabilityEvidence],
) -> tuple[list[RequirementMatch], list[GapItem]]:
    """Evaluate a list of requirements and return matches plus surfaced gaps."""
    matches: list[RequirementMatch] = []
    gaps: list[GapItem] = []

    for requirement in requirements:
        if requirement.normalized_label == "years_experience":
            match, gap = _evaluate_years_requirement(requirement, resume_schema)
        elif (
            requirement.requirement_type == "education"
            or requirement.normalized_label == "computer_science_degree"
        ):
            match, gap = _evaluate_education_requirement(requirement, resume_schema.education_items)
        else:
            match, gap = _evaluate_capability_requirement(
                requirement, evidence_map, jd_schema.domain_hint
            )

        matches.append(match)
        if gap is not None:
            gaps.append(gap)

    return matches, gaps


def _evaluate_years_requirement(
    requirement: RequirementItem,
    resume_schema: ResumeSchema,
) -> tuple[RequirementMatch, GapItem | None]:
    """Evaluate a years-of-experience requirement."""
    available_years = resume_schema.total_years_experience or 0.0
    summary_evidence = [span for span in resume_schema.evidence_spans if span.section == "summary"]
    fallback_evidence = [
        span for item in resume_schema.experience_items for span in item.evidence_spans
    ]
    resume_evidence = summary_evidence or fallback_evidence[:1]

    if requirement.min_years is not None and available_years >= requirement.min_years:
        return (
            RequirementMatch(
                requirement_id=requirement.requirement_id,
                requirement_label=requirement.label,
                normalized_label=requirement.normalized_label,
                requirement_priority=requirement.priority,
                requirement_type=requirement.requirement_type,
                status="matched",
                explanation=(
                    f"Resume shows {available_years:g} years, meeting the "
                    f"{requirement.min_years:g}+ year requirement."
                ),
                resume_evidence=resume_evidence,
                jd_evidence=[requirement.evidence_span],
            ),
            None,
        )

    gap = GapItem(
        requirement_id=requirement.requirement_id,
        requirement_label=requirement.label,
        requirement_priority=requirement.priority,
        gap_type="seniority_mismatch",
        explanation=(
            f"Resume shows {available_years:g} years, below the "
            f"{requirement.min_years:g}+ year requirement."
        ),
        resume_evidence=resume_evidence,
        jd_evidence=[requirement.evidence_span],
    )
    match = RequirementMatch(
        requirement_id=requirement.requirement_id,
        requirement_label=requirement.label,
        normalized_label=requirement.normalized_label,
        requirement_priority=requirement.priority,
        requirement_type=requirement.requirement_type,
        status="missing",
        explanation=gap.explanation,
        resume_evidence=resume_evidence,
        jd_evidence=[requirement.evidence_span],
    )
    return match, gap


def _evaluate_education_requirement(
    requirement: RequirementItem,
    education_items: list[EducationItem],
) -> tuple[RequirementMatch, GapItem | None]:
    """Evaluate a simple education requirement."""
    strong_evidence: list[EvidenceSpan] = []
    weak_evidence: list[EvidenceSpan] = []
    for item in education_items:
        lower_summary = item.summary.lower()
        if "computer science" in lower_summary:
            strong_evidence.extend(item.evidence_spans)
        elif "b.s." in lower_summary or "bachelor" in lower_summary:
            weak_evidence.extend(item.evidence_spans)

    if strong_evidence:
        return (
            RequirementMatch(
                requirement_id=requirement.requirement_id,
                requirement_label=requirement.label,
                normalized_label=requirement.normalized_label,
                requirement_priority=requirement.priority,
                requirement_type="education",
                status="matched",
                explanation="Resume includes a directly relevant degree match.",
                resume_evidence=_dedupe_spans(strong_evidence),
                jd_evidence=[requirement.evidence_span],
            ),
            None,
        )

    if weak_evidence:
        gap = GapItem(
            requirement_id=requirement.requirement_id,
            requirement_label=requirement.label,
            requirement_priority=requirement.priority,
            gap_type="education_gap",
            explanation="Resume shows a degree, but not the preferred computer science field.",
            resume_evidence=_dedupe_spans(weak_evidence),
            jd_evidence=[requirement.evidence_span],
        )
        match = RequirementMatch(
            requirement_id=requirement.requirement_id,
            requirement_label=requirement.label,
            normalized_label=requirement.normalized_label,
            requirement_priority=requirement.priority,
            requirement_type="education",
            status="partial",
            explanation=gap.explanation,
            resume_evidence=gap.resume_evidence,
            jd_evidence=gap.jd_evidence,
        )
        return match, gap

    gap = GapItem(
        requirement_id=requirement.requirement_id,
        requirement_label=requirement.label,
        requirement_priority=requirement.priority,
        gap_type="education_gap",
        explanation="Resume does not provide degree evidence for this education requirement.",
        resume_evidence=[],
        jd_evidence=[requirement.evidence_span],
    )
    match = RequirementMatch(
        requirement_id=requirement.requirement_id,
        requirement_label=requirement.label,
        normalized_label=requirement.normalized_label,
        requirement_priority=requirement.priority,
        requirement_type="education",
        status="missing",
        explanation=gap.explanation,
        resume_evidence=[],
        jd_evidence=gap.jd_evidence,
    )
    return match, gap


def _evaluate_capability_requirement(
    requirement: RequirementItem,
    evidence_map: dict[str, CapabilityEvidence],
    domain_hint: str | None,
) -> tuple[RequirementMatch, GapItem | None]:
    """Evaluate a skill or domain requirement from the evidence map."""
    bucket = evidence_map.get(requirement.normalized_label, CapabilityEvidence())
    strong_evidence = _dedupe_spans(bucket.strong)
    weak_evidence = _dedupe_spans(bucket.weak + bucket.claims)

    if (
        requirement.requirement_type == "domain"
        and domain_hint
        and requirement.normalized_label != domain_hint
    ):
        if evidence_map.get(domain_hint):
            bucket = evidence_map[domain_hint]
            strong_evidence = _dedupe_spans(bucket.strong)
            weak_evidence = _dedupe_spans(bucket.weak + bucket.claims)

    if strong_evidence:
        return (
            RequirementMatch(
                requirement_id=requirement.requirement_id,
                requirement_label=requirement.label,
                normalized_label=requirement.normalized_label,
                requirement_priority=requirement.priority,
                requirement_type=requirement.requirement_type,
                status="matched",
                explanation=f"Resume provides direct evidence for {requirement.label}.",
                resume_evidence=strong_evidence,
                jd_evidence=[requirement.evidence_span],
            ),
            None,
        )

    if weak_evidence:
        gap = GapItem(
            requirement_id=requirement.requirement_id,
            requirement_label=requirement.label,
            requirement_priority=requirement.priority,
            gap_type="missing_evidence",
            explanation=(
                f"Resume mentions {requirement.label}, but the evidence is weak or unsupported."
            ),
            resume_evidence=weak_evidence,
            jd_evidence=[requirement.evidence_span],
        )
        match = RequirementMatch(
            requirement_id=requirement.requirement_id,
            requirement_label=requirement.label,
            normalized_label=requirement.normalized_label,
            requirement_priority=requirement.priority,
            requirement_type=requirement.requirement_type,
            status="partial",
            explanation=gap.explanation,
            resume_evidence=weak_evidence,
            jd_evidence=gap.jd_evidence,
        )
        return match, gap

    gap_type = "domain_gap" if requirement.requirement_type == "domain" else "missing_skill"
    gap = GapItem(
        requirement_id=requirement.requirement_id,
        requirement_label=requirement.label,
        requirement_priority=requirement.priority,
        gap_type=gap_type,
        explanation=f"Resume does not show evidence for {requirement.label}.",
        resume_evidence=[],
        jd_evidence=[requirement.evidence_span],
    )
    match = RequirementMatch(
        requirement_id=requirement.requirement_id,
        requirement_label=requirement.label,
        normalized_label=requirement.normalized_label,
        requirement_priority=requirement.priority,
        requirement_type=requirement.requirement_type,
        status="missing",
        explanation=gap.explanation,
        resume_evidence=[],
        jd_evidence=gap.jd_evidence,
    )
    return match, gap


def _build_resume_evidence_map(resume_schema: ResumeSchema) -> dict[str, CapabilityEvidence]:
    """Build capability evidence buckets from the extracted resume schema."""
    evidence_map: dict[str, CapabilityEvidence] = {}

    for skill in resume_schema.skills:
        bucket = evidence_map.setdefault(skill.normalized_name, CapabilityEvidence())
        bucket.weak.extend(skill.evidence_spans)

    summary_span = next(
        (span for span in resume_schema.evidence_spans if span.section == "summary"), None
    )
    for capability in _detect_capabilities(resume_schema.summary):
        bucket = evidence_map.setdefault(capability, CapabilityEvidence())
        if summary_span is None:
            continue
        if _is_assertive_claim(resume_schema.summary):
            bucket.claims.append(summary_span)
        else:
            bucket.weak.append(summary_span)

    for item in resume_schema.experience_items:
        lower_text = f"{item.heading} {item.summary}".lower()
        for capability in _detect_capabilities(lower_text):
            if _contains_negation(lower_text):
                continue
            bucket = evidence_map.setdefault(capability, CapabilityEvidence())
            if capability == "rest_api" and any(
                phrase in lower_text
                for phrase in (
                    "requirements",
                    "partnered with backend teams",
                    "consumed backend apis",
                )
            ):
                bucket.weak.extend(item.evidence_spans)
            else:
                bucket.strong.extend(item.evidence_spans)

    for item in resume_schema.project_items:
        lower_text = item.summary.lower()
        for capability in _detect_capabilities(lower_text):
            bucket = evidence_map.setdefault(capability, CapabilityEvidence())
            if any(term in lower_text for term in WEAK_PROJECT_TERMS):
                bucket.weak.extend(item.evidence_spans)
            else:
                bucket.strong.extend(item.evidence_spans)
                bucket.project_strong.extend(item.evidence_spans)

    for item in resume_schema.education_items:
        lower_text = item.summary.lower()
        if "computer science" in lower_text:
            evidence_map.setdefault("computer_science_degree", CapabilityEvidence()).strong.extend(
                item.evidence_spans
            )
        elif "b.s." in lower_text or "bachelor" in lower_text:
            evidence_map.setdefault("computer_science_degree", CapabilityEvidence()).weak.extend(
                item.evidence_spans
            )

    return evidence_map


def _build_dimension_scores(
    required_matches: list[RequirementMatch],
    preferred_matches: list[RequirementMatch],
    resume_schema: ResumeSchema,
    jd_schema: JDSchema,
    evidence_map: dict[str, CapabilityEvidence],
) -> DimensionScores:
    """Build the dimension-level scores required by the public contract."""
    skills_score = _score_matches(
        [match for match in required_matches if match.requirement_type == "skill"],
        [match for match in preferred_matches if match.requirement_type == "skill"],
    )
    experience_score = _score_matches(
        [match for match in required_matches if match.requirement_type == "experience"],
        [],
    )
    projects_score = _score_projects(required_matches + preferred_matches, evidence_map)
    domain_score = _score_domain(jd_schema, evidence_map)
    education_score = _score_education(preferred_matches, resume_schema)
    return DimensionScores(
        skills=skills_score,
        experience=experience_score,
        projects=projects_score,
        domain_fit=domain_score,
        education=education_score,
    )


def _score_matches(
    required_matches: list[RequirementMatch], preferred_matches: list[RequirementMatch]
) -> int:
    """Score a set of matches using deterministic status weights."""
    if not required_matches and not preferred_matches:
        return 100

    total = 0.0
    weight = 0.0
    for match in required_matches:
        total += _status_value(match.status) * 0.8
        weight += 0.8
    for match in preferred_matches:
        total += _status_value(match.status) * 0.2
        weight += 0.2
    return int(round((total / weight) * 100)) if weight else 100


def _score_projects(
    matches: list[RequirementMatch], evidence_map: dict[str, CapabilityEvidence]
) -> int:
    """Score project support for matched requirements."""
    relevant_matches = [
        match
        for match in matches
        if match.requirement_type == "skill" and match.normalized_label in evidence_map
    ]
    if not relevant_matches:
        return 0

    supported = 0.0
    for match in relevant_matches:
        bucket = evidence_map.get(match.normalized_label, CapabilityEvidence())
        if bucket.project_strong:
            supported += 1.0
        elif match.status == "partial":
            supported += 0.25
    return int(round((supported / len(relevant_matches)) * 100))


def _score_domain(jd_schema: JDSchema, evidence_map: dict[str, CapabilityEvidence]) -> int:
    """Score domain fit from the JD hint and resume evidence map."""
    if not jd_schema.domain_hint:
        return 100
    bucket = evidence_map.get(jd_schema.domain_hint, CapabilityEvidence())
    if bucket.strong:
        return 100
    if bucket.weak or bucket.claims:
        return 40
    return 0


def _score_education(preferred_matches: list[RequirementMatch], resume_schema: ResumeSchema) -> int:
    """Score education fit with neutral handling when no education requirement exists."""
    education_matches = [
        match for match in preferred_matches if match.requirement_type == "education"
    ]
    if not education_matches:
        return 100 if resume_schema.education_items else 0
    return _score_matches(education_matches, [])


def _weighted_overall_score(dimension_scores: DimensionScores) -> int:
    """Compute the overall weighted score from the configured dimensions."""
    weighted_total = (
        dimension_scores.skills * MATCH_WEIGHTS["skills"]
        + dimension_scores.experience * MATCH_WEIGHTS["experience"]
        + dimension_scores.projects * MATCH_WEIGHTS["projects"]
        + dimension_scores.domain_fit * MATCH_WEIGHTS["domain_fit"]
        + dimension_scores.education * MATCH_WEIGHTS["education"]
    )
    return int(round(weighted_total / 100))


def _build_evidence_summary(
    *,
    evidence_spans: list[EvidenceSpan],
    required_matches: list[RequirementMatch],
    preferred_matches: list[RequirementMatch],
    gaps: list[GapItem],
) -> EvidenceSummary:
    """Build grouped evidence counts for easier regression review."""
    resume_section_counts: dict[str, int] = {}
    jd_section_counts: dict[str, int] = {}
    for span in evidence_spans:
        target = resume_section_counts if span.source_document == "resume" else jd_section_counts
        target[span.section] = target.get(span.section, 0) + 1
    return EvidenceSummary(
        total_evidence_spans=len(evidence_spans),
        resume_evidence_spans=sum(1 for span in evidence_spans if span.source_document == "resume"),
        jd_evidence_spans=sum(
            1 for span in evidence_spans if span.source_document == "job_description"
        ),
        resume_section_counts=resume_section_counts,
        jd_section_counts=jd_section_counts,
        required_match_count=len(required_matches),
        preferred_match_count=len(preferred_matches),
        gap_count=len(gaps),
    )


def _status_value(status: str) -> float:
    """Map a requirement status into a deterministic score contribution."""
    if status == "matched":
        return 1.0
    if status == "partial":
        return 0.4
    if status == "unsupported":
        return 0.2
    return 0.0


def _detect_capabilities(text: str) -> list[str]:
    """Detect normalized capabilities from free text."""
    lower_text = text.lower()
    matches: list[str] = []
    for capability, patterns in CAPABILITY_PATTERNS.items():
        if any(pattern in lower_text for pattern in patterns):
            matches.append(capability)
    if "api" in lower_text and "rest_api" not in matches:
        matches.append("rest_api")
    return matches


def _is_assertive_claim(text: str) -> bool:
    """Detect unsupported-claim phrasing in summary text."""
    lower_text = text.lower()
    return any(term in lower_text for term in ASSERTIVE_CLAIM_TERMS)


def _contains_negation(text: str) -> bool:
    """Detect negation language that should suppress strong evidence."""
    lower_text = text.lower()
    return any(term in lower_text for term in NEGATION_TERMS)


def _dedupe_spans(
    spans: list[EvidenceSpan] | tuple[EvidenceSpan, ...] | object,
) -> list[EvidenceSpan]:
    """Deduplicate evidence spans while preserving order."""
    seen: set[tuple[str, str, str, int | None, int | None, str | None]] = set()
    unique: list[EvidenceSpan] = []
    for span in spans:
        key = (
            span.source_document,
            span.section,
            span.text,
            span.start_char,
            span.end_char,
            span.normalized_value,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(span)
    return unique
