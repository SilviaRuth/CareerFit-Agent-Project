"""Grounded interview-prep guidance built from parse plus match outputs."""

from __future__ import annotations

from app.schemas.common import EvidenceSpan
from app.schemas.generation import (
    InterviewFocusArea,
    InterviewPrepResponse,
    InterviewQuestion,
    TalkingPoint,
    WeakAreaPreparation,
)
from app.services.generation.context import GroundedFlowContext
from app.services.generation.grounding import (
    dedupe_evidence,
    extract_bullet_text,
    sort_gaps,
    top_supported_matches,
)


def generate_interview_prep_from_text(
    resume_text: str,
    job_description_text: str,
    resume_source_name: str | None = None,
    jd_source_name: str | None = None,
) -> InterviewPrepResponse:
    """Backward-compatible convenience wrapper around the orchestrated flow."""
    from app.schemas.generation import GroundedGenerationRequest
    from app.services.orchestration_service import run_grounded_interview_prep_flow

    return run_grounded_interview_prep_flow(
        GroundedGenerationRequest(
            resume_text=resume_text,
            job_description_text=job_description_text,
            resume_source_name=resume_source_name,
            jd_source_name=jd_source_name,
        )
    )


def render_interview_prep_response(context: GroundedFlowContext) -> InterviewPrepResponse:
    """Render safe interview-prep guidance from an orchestrated grounded context."""
    if context.gating is None:
        raise ValueError("Grounded interview-prep rendering requires populated gating metadata.")

    focus_areas = _build_focus_areas(context)
    questions = _build_interview_questions(context)
    talking_points = _build_talking_points(context, context.gating.generation_mode)
    weak_area_preparation = _build_weak_area_preparation(context)
    evidence_used = dedupe_evidence(
        [span for item in focus_areas for span in item.evidence_used]
        + [span for item in questions for span in item.evidence_used]
        + [span for item in talking_points for span in item.evidence_used]
        + [span for item in weak_area_preparation for span in item.evidence_used]
    )

    summary = _build_interview_summary(
        context,
        context.gating.generation_mode,
        focus_areas,
    )
    return InterviewPrepResponse(
        summary=summary,
        likely_focus_areas=focus_areas,
        interview_questions=questions,
        recommended_talking_points=talking_points,
        weak_area_preparation=weak_area_preparation,
        evidence_used=evidence_used,
        generation_warnings=context.generation_warnings,
        gating=context.gating,
    )


def _build_focus_areas(context: GroundedFlowContext) -> list[InterviewFocusArea]:
    """Create likely interview focus areas from responsibilities and required matches."""
    focus_areas: list[InterviewFocusArea] = []
    priority = 1

    for responsibility in context.jd_parse.parsed_schema.responsibilities[:2]:
        jd_evidence = _find_jd_responsibility_evidence(context, responsibility)
        related_match = next(
            (
                match
                for match in top_supported_matches(context)
                if any(
                    label in responsibility.lower()
                    for label in match.requirement_label.lower().split()
                )
            ),
            None,
        )
        evidence = jd_evidence + (related_match.resume_evidence if related_match else [])
        focus_areas.append(
            InterviewFocusArea(
                priority=priority,
                focus_area=responsibility,
                reason=(
                    "JD responsibilities usually drive behavioral "
                    "and technical interview questions."
                ),
                related_requirement_id=related_match.requirement_id if related_match else None,
                evidence_used=dedupe_evidence(evidence),
                caution=(
                    None
                    if related_match
                    else (
                        "Prepare an honest response if your resume evidence "
                        "for this responsibility is sparse."
                    )
                ),
            )
        )
        priority += 1

    for match in top_supported_matches(context)[:2]:
        focus_areas.append(
            InterviewFocusArea(
                priority=priority,
                focus_area=match.requirement_label,
                reason=(
                    "This required area is already supported by resume evidence "
                    "and is likely to be probed in depth."
                ),
                related_requirement_id=match.requirement_id,
                evidence_used=dedupe_evidence(match.resume_evidence + match.jd_evidence),
                caution=None,
            )
        )
        priority += 1

    for gap in sort_gaps(context.match_result.gaps)[:2]:
        focus_areas.append(
            InterviewFocusArea(
                priority=priority,
                focus_area=gap.requirement_label,
                reason=(
                    "This gap or weak area is likely to come up as "
                    "a risk area during interviews."
                ),
                related_requirement_id=gap.requirement_id,
                evidence_used=dedupe_evidence(gap.resume_evidence + gap.jd_evidence),
                caution="Prepare a truthful explanation instead of overstating direct experience.",
            )
        )
        priority += 1

    return focus_areas[:6]


def _build_interview_questions(context: GroundedFlowContext) -> list[InterviewQuestion]:
    """Create grounded interview questions from strengths and weak areas."""
    questions: list[InterviewQuestion] = []
    priority = 1

    for match in top_supported_matches(context)[:3]:
        questions.append(
            InterviewQuestion(
                priority=priority,
                question=(
                    "Can you walk through a concrete example of your "
                    f"{match.requirement_label} work and the outcome?"
                ),
                rationale=(
                    "This question is grounded in a required or preferred area "
                    "the JD values and your resume already supports."
                ),
                related_requirement_id=match.requirement_id,
                support_level="strong",
                evidence_used=dedupe_evidence(match.resume_evidence + match.jd_evidence),
                honest_framing=None,
            )
        )
        priority += 1

    for gap in sort_gaps(context.match_result.gaps)[:3]:
        questions.append(
            InterviewQuestion(
                priority=priority,
                question=(
                    "How would you address the team's expectations around "
                    f"{gap.requirement_label} given your current background?"
                ),
                rationale=(
                    "This question prepares you for likely scrutiny around "
                    "an explicit gap or weak signal in the fit analysis."
                ),
                related_requirement_id=gap.requirement_id,
                support_level="weak" if gap.resume_evidence else "missing",
                evidence_used=dedupe_evidence(gap.resume_evidence + gap.jd_evidence),
                honest_framing=_honest_framing_for_gap(gap.requirement_label, gap.gap_type),
            )
        )
        priority += 1

    return questions[:6]


def _build_talking_points(
    context: GroundedFlowContext,
    generation_mode: str,
) -> list[TalkingPoint]:
    """Create talking points only from supported evidence."""
    if generation_mode == "minimal":
        return []

    talking_points: list[TalkingPoint] = []
    for match in top_supported_matches(context, required_only=False)[:4]:
        resume_span = next(
            (span for span in match.resume_evidence if span.source_document == "resume"), None
        )
        if resume_span is None:
            continue
        talking_points.append(
            TalkingPoint(
                topic=match.requirement_label,
                talking_point=(
                    "Use the verified example "
                    f"'{extract_bullet_text(resume_span)}' "
                    f"to explain your {match.requirement_label} experience."
                ),
                support_level="strong",
                evidence_used=dedupe_evidence(match.resume_evidence + match.jd_evidence),
                caution=(
                    "Keep the story anchored to the documented evidence "
                    "and do not add unsupported impact metrics."
                ),
            )
        )
    return talking_points[:4]


def _build_weak_area_preparation(
    context: GroundedFlowContext,
) -> list[WeakAreaPreparation]:
    """Prepare truthful framing for explicit weak areas."""
    items: list[WeakAreaPreparation] = []
    for gap in sort_gaps(context.match_result.gaps)[:4]:
        items.append(
            WeakAreaPreparation(
                requirement_label=gap.requirement_label,
                gap_type=gap.gap_type,
                honest_framing=_honest_framing_for_gap(gap.requirement_label, gap.gap_type),
                preparation_steps=_prep_steps_for_gap(
                    gap.requirement_label, gap.gap_type, bool(gap.resume_evidence)
                ),
                evidence_used=dedupe_evidence(gap.resume_evidence + gap.jd_evidence),
            )
        )
    return items


def _build_interview_summary(
    context: GroundedFlowContext,
    generation_mode: str,
    focus_areas: list[InterviewFocusArea],
) -> str:
    """Build the top-line interview prep summary."""
    if generation_mode == "minimal":
        return (
            "Interview prep is intentionally conservative because the grounded "
            "flow was downgraded to minimal mode; focus on verified resume "
            "examples and honest gap framing."
        )

    top_focus = [item.focus_area for item in focus_areas[:2]]
    if top_focus:
        return (
            "Expect the interview to center on "
            + " and ".join(top_focus)
            + ", with weaker areas handled through truthful preparation "
            "rather than invented stories."
        )
    return (
        "Use the JD responsibilities and explicit match gaps as the main "
        "preparation frame, and keep every answer anchored to existing evidence."
    )


def _find_jd_responsibility_evidence(
    context: GroundedFlowContext,
    responsibility: str,
) -> list[EvidenceSpan]:
    """Find matching JD evidence for a responsibility line."""
    return [
        span
        for span in context.jd_parse.parsed_schema.evidence_spans
        if span.section == "responsibilities" and responsibility.lower() in span.text.lower()
    ]


def _honest_framing_for_gap(requirement_label: str, gap_type: str) -> str:
    """Create truthful interview framing for a weak area."""
    if gap_type == "missing_skill":
        return (
            "State clearly that you do not yet have direct "
            f"{requirement_label} experience, then connect adjacent evidence "
            "without claiming hands-on ownership."
        )
    if gap_type == "missing_evidence":
        return (
            "Explain the related work you do have, but note that the resume "
            f"does not yet show strong direct evidence for {requirement_label}."
        )
    if gap_type == "seniority_mismatch":
        return (
            "Be explicit about your current scope and years of experience "
            "instead of trying to sound more senior than the evidence supports."
        )
    if gap_type == "education_gap":
        return (
            "State your actual education truthfully and avoid implying a "
            "stronger degree match than the resume supports."
        )
    return (
        f"Acknowledge that direct {requirement_label} background is limited "
        "and explain any adjacent experience without overstating domain depth."
    )


def _prep_steps_for_gap(
    requirement_label: str,
    gap_type: str,
    has_adjacent_evidence: bool,
) -> list[str]:
    """Provide small truthful prep steps for weak areas."""
    steps = ["Prepare a concise, honest statement about your current level of experience."]
    if has_adjacent_evidence:
        steps.append(
            "Bring one adjacent example from your actual resume that shows transferable work."
        )
    else:
        steps.append("Do not create a substitute story if no grounded example exists.")

    if gap_type == "missing_skill":
        steps.append(
            "Explain what you have done that is adjacent to "
            f"{requirement_label} and where the gap still remains."
        )
    elif gap_type == "missing_evidence":
        steps.append(
            "Review the resume wording around "
            f"{requirement_label} so you can clarify what is real and what is "
            "only loosely implied."
        )
    elif gap_type == "seniority_mismatch":
        steps.append(
            "Frame your scope accurately and emphasize growth readiness "
            "rather than higher seniority."
        )
    else:
        steps.append(
            "Keep the explanation factual and avoid upgrading the gap into a claimed strength."
        )
    return steps
