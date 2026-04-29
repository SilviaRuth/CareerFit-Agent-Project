"""Grounded interview-simulation guidance built from shared parse and match context."""

from __future__ import annotations

from app.schemas.generation import InterviewSimulationResponse, InterviewSimulationRound
from app.services.generation.context import GroundedFlowContext
from app.services.generation.grounding import dedupe_evidence, sort_gaps, top_supported_matches


def generate_interview_simulation_from_text(
    resume_text: str,
    job_description_text: str,
    resume_source_name: str | None = None,
    jd_source_name: str | None = None,
) -> InterviewSimulationResponse:
    """Backward-compatible convenience wrapper around the orchestrated flow."""
    from app.schemas.generation import GroundedGenerationRequest
    from app.services.orchestration_service import run_grounded_interview_simulation_flow

    return run_grounded_interview_simulation_flow(
        GroundedGenerationRequest(
            resume_text=resume_text,
            job_description_text=job_description_text,
            resume_source_name=resume_source_name,
            jd_source_name=jd_source_name,
        )
    )


def render_interview_simulation_response(
    context: GroundedFlowContext,
) -> InterviewSimulationResponse:
    """Render a bounded interview simulation from grounded responsibilities and gaps."""
    if context.gating is None:
        raise ValueError("Grounded interview simulation requires populated gating metadata.")

    simulation_rounds = _build_simulation_rounds(context, context.gating.generation_mode)
    scenario_focus = [round_item.prompt for round_item in simulation_rounds[:2]]
    coach_notes = _build_coach_notes(context)
    evidence_used = dedupe_evidence(
        [span for round_item in simulation_rounds for span in round_item.evidence_used]
    )

    summary = _build_summary(context.gating.generation_mode, simulation_rounds)
    return InterviewSimulationResponse(
        summary=summary,
        scenario_focus=scenario_focus,
        simulation_rounds=simulation_rounds,
        coach_notes=coach_notes,
        evidence_used=evidence_used,
        generation_warnings=context.generation_warnings,
        gating=context.gating,
    )


def _build_simulation_rounds(
    context: GroundedFlowContext,
    generation_mode: str,
) -> list[InterviewSimulationRound]:
    rounds: list[InterviewSimulationRound] = []
    priority = 1

    for responsibility in context.jd_parse.parsed_schema.responsibilities[:2]:
        jd_evidence = [
            span
            for span in context.jd_parse.parsed_schema.evidence_spans
            if span.section == "responsibilities" and responsibility.lower() in span.text.lower()
        ][:1]
        related_match = next(
            (
                match
                for match in top_supported_matches(context, required_only=False)
                if any(
                    token in responsibility.lower()
                    for token in match.requirement_label.lower().split()
                )
            ),
            None,
        )
        evidence = list(jd_evidence)
        if related_match is not None:
            evidence = dedupe_evidence(
                jd_evidence + related_match.resume_evidence + related_match.jd_evidence
            )
        rounds.append(
            InterviewSimulationRound(
                priority=priority,
                round_type="responsibility_probe",
                prompt=f"Walk through a concrete example of how you handled: {responsibility}",
                intent=(
                    "Test whether the candidate can ground a JD responsibility in resume "
                    "evidence."
                ),
                answer_strategy=(
                    "Anchor the answer to one documented example, explain the scope clearly, and "
                    "avoid inflating ownership beyond the resume."
                ),
                evidence_used=evidence,
                caution=(
                    None
                    if evidence
                    else (
                        "Acknowledge limited direct evidence instead of improvising a "
                        "stronger story."
                    )
                ),
            )
        )
        priority += 1

    for match in top_supported_matches(context)[:1]:
        rounds.append(
            InterviewSimulationRound(
                priority=priority,
                round_type="strength_probe",
                prompt=(
                    f"Explain the most convincing example of your {match.requirement_label} work "
                    "and why it mattered."
                ),
                intent="Pressure-test the strongest grounded capability in the current fit result.",
                answer_strategy=(
                    "Use the exact project or experience evidence already on the resume, then add "
                    "scope and outcome without inventing new claims."
                ),
                evidence_used=dedupe_evidence(match.resume_evidence + match.jd_evidence),
                caution=(
                    "Keep the answer tied to documented evidence, not retrospective "
                    "embellishment."
                ),
            )
        )
        priority += 1

    for gap in sort_gaps(context.match_result.gaps)[:2]:
        rounds.append(
            InterviewSimulationRound(
                priority=priority,
                round_type="gap_probe",
                prompt=(
                    f"How would you discuss your current gap around {gap.requirement_label} in an "
                    "interview?"
                ),
                intent=(
                    "Practice truthful framing for weak evidence, missing skills, or "
                    "blocker gaps."
                ),
                answer_strategy=(
                    "State the current limitation directly, mention any adjacent evidence, and "
                    "describe the next concrete step without claiming direct experience."
                ),
                evidence_used=dedupe_evidence(gap.resume_evidence + gap.jd_evidence),
                caution="Do not convert an explicit gap into a claimed strength during the answer.",
            )
        )
        priority += 1

    if generation_mode == "minimal":
        return rounds[:3]
    return rounds[:5]


def _build_coach_notes(context: GroundedFlowContext) -> list[str]:
    notes = [
        "Use resume evidence before general opinions or hypothetical claims.",
        (
            "If a question lands on a real gap, answer honestly and keep the improvement "
            "plan concrete."
        ),
    ]
    if context.match_result.blocker_flags.unsupported_claims:
        notes.append(
            "Unsupported summary claims are already a blocker, so practice removing them "
            "from verbal answers too."
        )
    if context.match_result.blocker_flags.seniority_mismatch:
        notes.append(
            "Keep scope and ownership calibrated to the current resume instead of trying "
            "to sound more senior."
        )
    return notes


def _build_summary(generation_mode: str, rounds: list[InterviewSimulationRound]) -> str:
    if generation_mode == "minimal":
        return (
            "Interview simulation is intentionally conservative because the grounded flow detected "
            "elevated risk; practice only the most evidence-backed responses first."
        )
    if rounds:
        return (
            "Interview simulation prioritizes JD responsibilities first, then drills into "
            "supported strengths and explicit weak areas."
        )
    return "Interview simulation could not build enough grounded prompts from the current inputs."
