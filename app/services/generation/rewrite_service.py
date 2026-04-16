"""Grounded resume rewrite suggestions built from parse plus match outputs."""

from __future__ import annotations

from app.schemas.generation import RewriteAction, RewrittenBullet, RewriteResponse
from app.services.generation.generation_guardrails import build_generation_gate
from app.services.generation.grounding import (
    collect_context_evidence,
    dedupe_evidence,
    extract_bullet_text,
    sort_gaps,
    top_supported_matches,
)
from app.services.generation.workflow import GenerationContext, build_generation_context


def generate_rewrite_response_from_text(
    resume_text: str,
    job_description_text: str,
    resume_source_name: str | None = None,
    jd_source_name: str | None = None,
) -> RewriteResponse:
    """Generate grounded rewrite guidance from raw text inputs."""
    from app.schemas.generation import GroundedGenerationRequest

    context = build_generation_context(
        GroundedGenerationRequest(
            resume_text=resume_text,
            job_description_text=job_description_text,
            resume_source_name=resume_source_name,
            jd_source_name=jd_source_name,
        )
    )
    return generate_rewrite_response(context)


def generate_rewrite_response(context: GenerationContext) -> RewriteResponse:
    """Generate bounded rewrite guidance from the shared generation context."""
    gating, gate_warnings = build_generation_gate(context)
    prioritized_actions = _build_prioritized_actions(context, gating.generation_mode)
    rewritten_summary = _build_rewritten_summary(context, gating.generation_mode)
    rewritten_bullets, unsupported_requests = _build_rewritten_bullets(
        context,
        gating.generation_mode,
    )
    cautions = _build_rewrite_cautions(context, gating.generation_mode)
    evidence_used = dedupe_evidence(
        [
            span
            for action in prioritized_actions
            for span in action.evidence_used
        ]
        + [
            span
            for bullet in rewritten_bullets
            for span in bullet.evidence_used
        ]
    )

    if not evidence_used:
        evidence_used = collect_context_evidence(context)[:5]

    summary = _build_rewrite_summary_text(context, gating.generation_mode, prioritized_actions)
    return RewriteResponse(
        summary=summary,
        prioritized_actions=prioritized_actions,
        rewritten_summary=rewritten_summary,
        rewritten_bullets=rewritten_bullets,
        evidence_used=evidence_used,
        unsupported_requests=unsupported_requests,
        cautions=cautions,
        generation_warnings=gate_warnings,
        gating=gating,
    )


def _build_prioritized_actions(
    context: GenerationContext,
    generation_mode: str,
) -> list[RewriteAction]:
    """Create rewrite actions grounded in current gaps and evidence."""
    actions: list[RewriteAction] = []
    for priority, gap in enumerate(sort_gaps(context.match_result.gaps)[:5], start=1):
        evidence = dedupe_evidence(gap.resume_evidence + gap.jd_evidence)
        category = _gap_category(gap.gap_type, gap.requirement_priority)
        recommendation, caution = _rewrite_guidance_for_gap(gap)
        if generation_mode == "minimal" and gap.gap_type != "missing_skill":
            recommendation = (
                "Keep this gap explicit and avoid a detailed rewrite until parsing quality improves."
            )

        actions.append(
            RewriteAction(
                priority=priority,
                category=category,
                target_requirement_id=gap.requirement_id,
                target_requirement_label=gap.requirement_label,
                explanation=gap.explanation,
                recommendation=recommendation,
                evidence_used=evidence,
                caution=caution,
            )
        )

    if not actions and generation_mode != "minimal":
        for priority, match in enumerate(top_supported_matches(context)[:3], start=1):
            actions.append(
                RewriteAction(
                    priority=priority,
                    category="weak_evidence",
                    target_requirement_id=match.requirement_id,
                    target_requirement_label=match.requirement_label,
                    explanation=(
                        f"This requirement is already matched; keep it visible and easy to verify in the resume."
                    ),
                    recommendation=(
                        f"Keep {match.requirement_label} close to the relevant experience bullets and summary so reviewers can verify it quickly."
                    ),
                    evidence_used=dedupe_evidence(match.resume_evidence + match.jd_evidence),
                    caution="Do not add stronger claims than the current evidence supports.",
                )
            )

    return actions


def _build_rewritten_summary(context: GenerationContext, generation_mode: str) -> str | None:
    """Create a bounded summary rewrite only when grounded evidence is sufficient."""
    if generation_mode == "minimal":
        return None

    resume_schema = context.resume_parse.parsed_schema
    supported_matches = top_supported_matches(context)[:3]
    capability_labels = [
        match.requirement_label
        for match in supported_matches
        if match.normalized_label not in {"years_experience", "computer_science_degree"}
    ]
    capability_labels = _unique_strings(capability_labels)

    if not resume_schema.summary.strip():
        return None

    if not capability_labels:
        return resume_schema.summary

    years_text = (
        f"{resume_schema.total_years_experience:g} years of experience"
        if resume_schema.total_years_experience is not None
        else "experience"
    )
    capability_phrase = ", ".join(capability_labels[:3])
    domain_phrase = ""
    if context.match_result.dimension_scores.domain_fit > 0 and context.jd_parse.parsed_schema.domain_hint:
        domain_phrase = f" for {context.jd_parse.parsed_schema.domain_hint.replace('_', ' ')} workflows"
    return (
        f"Backend engineer with {years_text} delivering {capability_phrase}"
        f"{domain_phrase}."
    )


def _build_rewritten_bullets(
    context: GenerationContext,
    generation_mode: str,
) -> tuple[list[RewrittenBullet], list[str]]:
    """Generate bullet suggestions only from directly supported evidence."""
    bullets: list[RewrittenBullet] = []
    unsupported_requests: list[str] = []

    if generation_mode == "minimal":
        unsupported_requests.append(
            "Detailed rewritten bullets were withheld because parser confidence is low."
        )
        return bullets, unsupported_requests

    for match in top_supported_matches(context)[:3]:
        resume_evidence = [
            span for span in match.resume_evidence if span.section in {"experience", "projects", "summary"}
        ]
        if not resume_evidence:
            continue
        span = resume_evidence[0]
        original_text = extract_bullet_text(span)
        suggested_text = _polish_supported_text(original_text)
        bullets.append(
            RewrittenBullet(
                target_section="summary" if span.section == "summary" else span.section,
                support_level="strong",
                target_requirement_id=match.requirement_id,
                target_requirement_label=match.requirement_label,
                original_text=original_text,
                suggested_text=suggested_text,
                evidence_used=dedupe_evidence(match.resume_evidence + match.jd_evidence),
                caution="This suggestion stays inside existing evidence and does not add new claims.",
            )
        )

    for gap in sort_gaps(context.match_result.gaps):
        if gap.gap_type != "missing_skill":
            continue
        unsupported_requests.append(
            f"No grounded rewrite was generated for {gap.requirement_label} because the resume does not contain supporting evidence."
        )

    if not bullets and not unsupported_requests:
        unsupported_requests.append(
            "The current evidence supports only higher-level rewrite guidance, not bullet-level revisions."
        )

    return bullets[:3], unsupported_requests[:5]


def _build_rewrite_cautions(context: GenerationContext, generation_mode: str) -> list[str]:
    """Collect high-signal rewrite cautions from blockers and low-confidence inputs."""
    cautions: list[str] = []
    blockers = context.match_result.blocker_flags
    if generation_mode == "minimal":
        cautions.append("Parsing confidence is low, so rewrite output is intentionally narrow.")
    if blockers.unsupported_claims:
        cautions.append("Unsupported summary claims should be reduced, not amplified.")
    if blockers.seniority_mismatch:
        cautions.append("Do not rewrite the resume to imply a higher seniority level than the evidence shows.")
    if blockers.missing_required_skills:
        cautions.append("Do not add missing required tools or domains unless you have direct supporting evidence.")
    return cautions


def _build_rewrite_summary_text(
    context: GenerationContext,
    generation_mode: str,
    prioritized_actions: list[RewriteAction],
) -> str:
    """Summarize the rewrite plan in one bounded sentence."""
    if generation_mode == "minimal":
        return (
            "Rewrite guidance is limited because parsing confidence is low; focus on truthful gap framing and preserve only verifiable evidence."
        )

    if prioritized_actions:
        top_labels = [
            action.target_requirement_label
            for action in prioritized_actions[:2]
            if action.target_requirement_label
        ]
        if top_labels:
            return (
                "Prioritize required gaps first, especially "
                + " and ".join(top_labels)
                + ", and only strengthen language where the resume already contains evidence."
            )

    return (
        "The current resume already aligns well; keep matched evidence explicit and avoid inflating unsupported claims."
    )


def _gap_category(gap_type: str, requirement_priority: str) -> str:
    """Map gap types into rewrite action categories."""
    if gap_type == "seniority_mismatch":
        return "seniority_gap"
    if gap_type == "education_gap":
        return "education_gap"
    if gap_type == "domain_gap":
        return "domain_gap"
    if gap_type == "missing_evidence":
        return "weak_evidence"
    return "required_gap" if requirement_priority == "required" else "preferred_gap"


def _rewrite_guidance_for_gap(gap) -> tuple[str, str | None]:
    """Return truthful rewrite guidance for each gap type."""
    if gap.gap_type == "missing_skill":
        return (
            f"Keep {gap.requirement_label} as an explicit gap. Do not add it to the resume unless you have direct project or work evidence to support it.",
            "Avoid inventing tools, project scope, or domain background.",
        )
    if gap.gap_type == "missing_evidence":
        if gap.resume_evidence:
            return (
                f"Clarify the existing resume material that points toward {gap.requirement_label}, and name that requirement more explicitly only where the evidence already supports it.",
                "Use the current evidence as-is; do not upgrade weak mentions into stronger claims.",
            )
        return (
            f"No grounded rewrite is available for {gap.requirement_label} because the resume does not contain supporting evidence.",
            "Leave this out of rewritten copy until stronger evidence exists.",
        )
    if gap.gap_type == "seniority_mismatch":
        return (
            "Keep the current years of experience explicit and emphasize proven scope instead of rewriting the resume to sound more senior.",
            "Do not claim a senior title or senior-level ownership without evidence.",
        )
    if gap.gap_type == "education_gap":
        return (
            "State the actual degree truthfully and avoid implying a computer science credential the resume does not support.",
            "Do not rewrite education into a stronger degree than the evidence shows.",
        )
    return (
        f"Treat {gap.requirement_label} as a truthful domain or background gap and highlight only adjacent experience that is already in the resume.",
        "Do not imply direct domain exposure if the resume does not show it.",
    )


def _polish_supported_text(text: str) -> str:
    """Return a lightly polished, still-grounded version of supported evidence text."""
    cleaned = text.strip().rstrip(".")
    if not cleaned:
        return text.strip()
    cleaned = cleaned[0].upper() + cleaned[1:]
    return f"{cleaned}."


def _unique_strings(values: list[str]) -> list[str]:
    """Deduplicate strings while preserving order."""
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
