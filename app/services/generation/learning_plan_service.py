"""Grounded learning-plan guidance built from parse plus match outputs."""

from __future__ import annotations

from app.schemas.generation import (
    LearningPlanFocusArea,
    LearningPlanResponse,
    LearningPlanStep,
    SupportingStrength,
)
from app.services.generation.context import GroundedFlowContext
from app.services.generation.grounding import dedupe_evidence, sort_gaps, top_supported_matches


def generate_learning_plan_from_text(
    resume_text: str,
    job_description_text: str,
    resume_source_name: str | None = None,
    jd_source_name: str | None = None,
) -> LearningPlanResponse:
    """Backward-compatible convenience wrapper around the orchestrated flow."""
    from app.schemas.generation import GroundedGenerationRequest
    from app.services.orchestration_service import run_grounded_learning_plan_flow

    return run_grounded_learning_plan_flow(
        GroundedGenerationRequest(
            resume_text=resume_text,
            job_description_text=job_description_text,
            resume_source_name=resume_source_name,
            jd_source_name=jd_source_name,
        )
    )


def render_learning_plan_response(context: GroundedFlowContext) -> LearningPlanResponse:
    """Render a deterministic learning plan from grounded fit diagnostics."""
    if context.gating is None:
        raise ValueError("Grounded learning-plan rendering requires populated gating metadata.")

    focus_areas = _build_focus_areas(context, context.gating.generation_mode)
    supporting_strengths = _build_supporting_strengths(context)
    plan_steps = _build_plan_steps(
        context,
        context.gating.generation_mode,
        focus_areas,
        supporting_strengths,
    )
    blocker_cautions = _build_blocker_cautions(context)
    evidence_used = dedupe_evidence(
        [span for item in focus_areas for span in item.evidence_used]
        + [span for item in plan_steps for span in item.evidence_used]
        + [span for item in supporting_strengths for span in item.evidence_used]
    )
    if not evidence_used:
        evidence_used = context.evidence_registry[:5]

    summary = _build_learning_plan_summary(
        context,
        context.gating.generation_mode,
        focus_areas,
    )
    return LearningPlanResponse(
        summary=summary,
        focus_areas=focus_areas,
        plan_steps=plan_steps,
        supporting_strengths=supporting_strengths,
        blocker_cautions=blocker_cautions,
        evidence_used=evidence_used,
        generation_warnings=context.generation_warnings,
        gating=context.gating,
    )


def _build_focus_areas(
    context: GroundedFlowContext,
    generation_mode: str,
) -> list[LearningPlanFocusArea]:
    """Prioritize grounded gaps first, with supported strengths as a fallback."""
    focus_areas: list[LearningPlanFocusArea] = []
    limit = 2 if generation_mode == "minimal" else 4

    for priority, gap in enumerate(sort_gaps(context.match_result.gaps)[:limit], start=1):
        focus_areas.append(
            LearningPlanFocusArea(
                priority=priority,
                focus_type=(
                    "blocker"
                    if _gap_is_blocker(gap.gap_type, gap.requirement_priority, context)
                    else "gap"
                ),
                target_requirement_id=gap.requirement_id,
                target_requirement_label=gap.requirement_label,
                gap_type=gap.gap_type,
                requirement_priority=gap.requirement_priority,
                rationale=_focus_area_rationale(gap.requirement_label, gap.gap_type),
                evidence_used=dedupe_evidence(gap.resume_evidence + gap.jd_evidence),
                caution=_focus_area_caution(gap.gap_type),
            )
        )

    if focus_areas:
        return focus_areas

    for priority, match in enumerate(
        top_supported_matches(context, required_only=False)[:2],
        start=1,
    ):
        focus_areas.append(
            LearningPlanFocusArea(
                priority=priority,
                focus_type="strength_maintenance",
                target_requirement_id=match.requirement_id,
                target_requirement_label=match.requirement_label,
                rationale=(
                    "Current evidence already supports this area, so it is the safest base for "
                    "deeper growth."
                ),
                evidence_used=dedupe_evidence(match.resume_evidence + match.jd_evidence),
                caution="Deepen verified strengths before expanding into unsupported claims.",
            )
        )

    return focus_areas


def _build_supporting_strengths(context: GroundedFlowContext) -> list[SupportingStrength]:
    """Collect grounded strengths the learning plan can build on safely."""
    strengths: list[SupportingStrength] = []
    for priority, match in enumerate(
        top_supported_matches(context, required_only=False)[:3],
        start=1,
    ):
        strengths.append(
            SupportingStrength(
                priority=priority,
                label=match.requirement_label,
                explanation=(
                    f"Use verified {match.requirement_label} evidence as the foundation for "
                    "adjacent "
                    "growth instead of starting from unsupported areas."
                ),
                evidence_used=dedupe_evidence(match.resume_evidence + match.jd_evidence),
            )
        )
    return strengths


def _build_plan_steps(
    context: GroundedFlowContext,
    generation_mode: str,
    focus_areas: list[LearningPlanFocusArea],
    supporting_strengths: list[SupportingStrength],
) -> list[LearningPlanStep]:
    """Convert grounded focus areas into ordered learning actions."""
    steps: list[LearningPlanStep] = []
    priority = 1

    if context.match_result.blocker_flags.unsupported_claims:
        summary_evidence = [
            span
            for span in context.resume_parse.parsed_schema.evidence_spans
            if span.section == "summary"
        ][:1]
        steps.append(
            LearningPlanStep(
                priority=priority,
                time_horizon="now",
                step_type="address_blocker",
                action=(
                    "Trim summary claims until each one is backed by experience "
                    "or project evidence."
                ),
                reason=(
                    "Unsupported claims are an explicit blocker and will weaken "
                    "downstream guidance."
                ),
                success_signal=(
                    "Your summary mentions only capabilities that the rest of the "
                    "resume can verify."
                ),
                evidence_used=dedupe_evidence(summary_evidence),
                caution="Do not solve this blocker by inventing stronger evidence.",
            )
        )
        priority += 1

    for index, focus in enumerate(focus_areas, start=1):
        steps.append(
            LearningPlanStep(
                priority=priority,
                time_horizon=_time_horizon_for_focus(focus, index, generation_mode),
                step_type=_step_type_for_focus(focus),
                target_requirement_id=focus.target_requirement_id,
                target_requirement_label=focus.target_requirement_label,
                action=_step_action_for_focus(focus),
                reason=_step_reason_for_focus(focus),
                success_signal=_success_signal_for_focus(focus),
                evidence_used=focus.evidence_used,
                caution=_step_caution_for_focus(focus),
            )
        )
        priority += 1

    if generation_mode != "minimal" and supporting_strengths:
        strongest = supporting_strengths[0]
        steps.append(
            LearningPlanStep(
                priority=priority,
                time_horizon="later",
                step_type="maintain_strength",
                target_requirement_label=strongest.label,
                action=(
                    f"Keep building deeper, outcome-backed examples in {strongest.label} so future "
                    "applications show repeated proof instead of a single mention."
                ),
                reason=(
                    "The safest long-term learning path starts from a capability "
                    "the current resume "
                    "already supports."
                ),
                success_signal=(
                    f"You can point to multiple concrete examples of {strongest.label} work with "
                    "clear scope and results."
                ),
                evidence_used=strongest.evidence_used,
                caution=(
                    "Expand from verified strengths instead of jumping straight to unsupported "
                    "senior-level positioning."
                ),
            )
        )

    return steps[:6]


def _build_blocker_cautions(context: GroundedFlowContext) -> list[str]:
    """Translate current blockers into explicit learning-plan cautions."""
    cautions: list[str] = []
    blockers = context.match_result.blocker_flags
    if blockers.missing_required_skills:
        cautions.append(
            "Missing required skills should be closed with direct evidence before "
            "similar roles are "
            "treated as target-ready."
        )
    if blockers.seniority_mismatch:
        cautions.append(
            "Keep role targeting aligned with your current scope while you build "
            "more ownership and "
            "years-backed evidence."
        )
    if blockers.unsupported_claims:
        cautions.append(
            "Reduce unsupported claims before layering on richer recommendations "
            "or stronger resume "
            "positioning."
        )
    return cautions


def _build_learning_plan_summary(
    context: GroundedFlowContext,
    generation_mode: str,
    focus_areas: list[LearningPlanFocusArea],
) -> str:
    """Summarize the grounded learning plan in one bounded sentence."""
    if generation_mode == "minimal":
        focus_labels = [item.target_requirement_label for item in focus_areas[:2]]
        if focus_labels:
            return (
                "Learning guidance is intentionally conservative because blocker or parser risk is "
                "high; start with "
                + " and ".join(focus_labels)
                + " while keeping every claim evidence-backed."
            )
        return (
            "Learning guidance is intentionally conservative because blocker or "
            "parser risk is high; "
            "focus on verified strengths and truthful gap framing first."
        )

    top_labels = [item.target_requirement_label for item in focus_areas[:2]]
    if top_labels:
        return (
            "Focus the next learning cycle on "
            + " and ".join(top_labels)
            + ", using existing strengths as the base and keeping blocker risks explicit."
        )
    return (
        "The current fit leaves fewer explicit gaps, so the learning plan should deepen supported "
        "strengths and add adjacent evidence deliberately."
    )


def _gap_is_blocker(
    gap_type: str | None,
    requirement_priority: str | None,
    context: GroundedFlowContext,
) -> bool:
    """Map current gaps onto explicit blocker states."""
    blockers = context.match_result.blocker_flags
    if gap_type == "seniority_mismatch":
        return blockers.seniority_mismatch
    if gap_type in {"missing_skill", "domain_gap"} and requirement_priority == "required":
        return blockers.missing_required_skills
    return False


def _focus_area_rationale(requirement_label: str, gap_type: str | None) -> str:
    """Explain why a requirement belongs in the learning plan."""
    if gap_type == "missing_skill":
        return f"The current fit analysis shows no direct evidence for {requirement_label}."
    if gap_type == "missing_evidence":
        return (
            f"The resume points toward {requirement_label}, but the evidence is not strong enough "
            "yet."
        )
    if gap_type == "seniority_mismatch":
        return (
            f"The JD expects more depth or scope than the current resume shows around "
            f"{requirement_label}."
        )
    if gap_type == "education_gap":
        return (
            f"The current education evidence is weaker than the JD preference around "
            f"{requirement_label}."
        )
    return f"The current fit analysis still treats {requirement_label} as a role-relevant gap."


def _focus_area_caution(gap_type: str | None) -> str | None:
    """Attach a small guardrail to each learning focus area."""
    if gap_type == "missing_skill":
        return "Treat this as a real learning gap, not something to add to the resume today."
    if gap_type == "missing_evidence":
        return "Clarify existing work without upgrading weak mentions into stronger claims."
    if gap_type == "seniority_mismatch":
        return "Build real scope progression instead of rewriting the resume to sound more senior."
    if gap_type == "education_gap":
        return "Do not imply a stronger degree match than the resume actually supports."
    return "Keep adjacent evidence truthful and reviewable."


def _time_horizon_for_focus(
    focus: LearningPlanFocusArea,
    index: int,
    generation_mode: str,
) -> str:
    """Assign a simple time horizon that keeps blockers and required gaps first."""
    if focus.focus_type == "strength_maintenance":
        return "later"
    if focus.focus_type == "blocker":
        return "now"
    if focus.gap_type == "education_gap":
        return "later"
    if generation_mode == "minimal":
        return "now" if index == 1 else "next"
    if focus.requirement_priority == "required":
        return "now" if index <= 2 else "next"
    if focus.gap_type == "missing_evidence":
        return "next"
    return "later"


def _step_type_for_focus(focus: LearningPlanFocusArea) -> str:
    """Map a focus area into a deterministic learning-step category."""
    if focus.focus_type == "strength_maintenance":
        return "maintain_strength"
    if focus.focus_type == "blocker":
        return "address_blocker" if focus.gap_type == "seniority_mismatch" else "close_required_gap"
    if focus.gap_type == "missing_evidence":
        return "strengthen_evidence"
    if focus.gap_type == "education_gap":
        return "address_blocker"
    return "build_adjacent_project"


def _step_action_for_focus(focus: LearningPlanFocusArea) -> str:
    """Create the actionable learning step for a focus area."""
    label = focus.target_requirement_label
    if focus.focus_type == "strength_maintenance":
        return f"Keep building deeper, outcome-backed examples in {label}."
    if focus.gap_type in {"missing_skill", "domain_gap"} and focus.focus_type == "blocker":
        return (
            f"Build one direct, hands-on example in {label} before treating "
            "similar roles as target-ready."
        )
    if focus.gap_type in {"missing_skill", "domain_gap"}:
        return (
            f"Create a scoped project or practice exercise in {label} that is "
            "small enough to finish "
            "and concrete enough to discuss."
        )
    if focus.gap_type == "missing_evidence":
        return (
            f"Turn the adjacent work you already have into clearer proof for "
            f"{label} by capturing the "
            "scope, tools, and outcome in one reviewable example."
        )
    if focus.gap_type == "seniority_mismatch":
        return (
            "Target roles closer to your current scope while adding one "
            "end-to-end ownership example "
            "that stretches your level honestly."
        )
    if focus.gap_type == "education_gap":
        return (
            "Decide whether this education preference is blocking your target "
            "roles often enough to "
            "justify coursework, certification, or a narrower role list."
        )
    return f"Keep {label} explicit as a real gap and only build on verifiable adjacent work."


def _step_reason_for_focus(focus: LearningPlanFocusArea) -> str:
    """Explain why a learning action is prioritized."""
    label = focus.target_requirement_label
    if focus.focus_type == "strength_maintenance":
        return f"{label} is already supported, so it is the safest base for adjacent growth."
    if focus.focus_type == "blocker":
        return f"{label} is tied to an explicit blocker in the current fit analysis."
    if focus.gap_type == "missing_evidence":
        return (
            f"The resume already points toward {label}, so better evidence is "
            "higher leverage than broad new study."
        )
    return f"{label} remains a visible gap in the current fit analysis."


def _success_signal_for_focus(focus: LearningPlanFocusArea) -> str:
    """Define a concrete success signal for one learning step."""
    label = focus.target_requirement_label
    if focus.gap_type in {"missing_skill", "domain_gap"}:
        return (
            f"You can describe one concrete example of {label} work with scope, "
            "tools, and result."
        )
    if focus.gap_type == "missing_evidence":
        return f"A reviewer can verify {label} directly without having to infer it."
    if focus.gap_type == "seniority_mismatch":
        return "The resume shows clearer scope progression without inflating title or years."
    if focus.gap_type == "education_gap":
        return (
            "You have a deliberate plan for degree-related filtering instead of "
            "leaving it implicit."
        )
    return f"You can show repeated, outcome-backed evidence in {label}."


def _step_caution_for_focus(focus: LearningPlanFocusArea) -> str | None:
    """Carry the relevant guardrail into the learning step."""
    if focus.focus_type == "strength_maintenance":
        return (
            "Use verified strengths as the base; do not leap from them into "
            "unsupported senior-level claims."
        )
    if focus.gap_type == "missing_skill":
        return "Treat new work as new evidence, not as retroactive professional experience."
    if focus.gap_type == "missing_evidence":
        return "Clarify what is real today instead of upgrading weak mentions into stronger claims."
    if focus.gap_type == "seniority_mismatch":
        return "Do not rewrite the resume to imply more seniority than the evidence supports."
    if focus.gap_type == "education_gap":
        return "Do not imply a stronger degree match than the resume actually shows."
    return focus.caution
