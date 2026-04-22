"""Offline recommendation benchmark for grounded M5 outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.generation import InterviewSimulationResponse, LearningPlanResponse
from app.services.generation.interview_simulation_service import (
    generate_interview_simulation_from_text,
)
from app.services.generation.learning_plan_service import generate_learning_plan_from_text

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLES_DIR = REPO_ROOT / "data" / "samples"
DEFAULT_EVAL_DIR = REPO_ROOT / "data" / "eval"
DEFAULT_MANIFEST_PATH = DEFAULT_EVAL_DIR / "recommendation_manifest.json"


class RecommendationCase(BaseModel):
    """Manifest entry for one recommendation workflow acceptance case."""

    case_id: str
    workflow: Literal["learning_plan", "interview_simulation"]
    resume_sample: str
    jd_sample: str
    expected_eval: str


class RecommendationMetrics(BaseModel):
    """Aggregate metrics for grounded recommendation quality."""

    case_count: int
    usefulness_accuracy: float
    grounding_accuracy: float
    blocker_guardrail_accuracy: float
    hallucination_rate: float


class RecommendationCaseReport(BaseModel):
    """Detailed report for one grounded recommendation case."""

    case_id: str
    workflow: Literal["learning_plan", "interview_simulation"]
    generation_mode: str
    useful: bool
    grounded: bool
    blocker_guardrail_ok: bool
    hallucination_rate: float
    recommendation_item_count: int
    missing_expectations: list[str] = Field(default_factory=list)


class RecommendationReport(BaseModel):
    """Structured output for the recommendation benchmark."""

    manifest_path: str
    report_label: str | None = None
    generated_at: str | None = None
    metrics: RecommendationMetrics
    cases: list[RecommendationCaseReport]


def run_recommendation_benchmark(
    manifest_path: Path | None = None,
    *,
    samples_dir: Path | None = None,
    eval_dir: Path | None = None,
    report_label: str | None = None,
    generated_at: str | None = None,
) -> RecommendationReport:
    """Execute grounded recommendation acceptance checks."""
    manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
    samples_dir = samples_dir or DEFAULT_SAMPLES_DIR
    eval_dir = eval_dir or DEFAULT_EVAL_DIR

    cases = _load_manifest(manifest_path)
    case_reports: list[RecommendationCaseReport] = []
    useful_count = 0
    grounded_count = 0
    guardrail_count = 0
    total_ungrounded_items = 0
    total_items = 0

    for case in cases:
        expected = _load_json(eval_dir / case.expected_eval)
        response = _run_case(case, samples_dir)
        report = _build_case_report(case, expected, response)
        case_reports.append(report)
        useful_count += int(report.useful)
        grounded_count += int(report.grounded)
        guardrail_count += int(report.blocker_guardrail_ok)
        total_ungrounded_items += round(report.hallucination_rate * report.recommendation_item_count)
        total_items += report.recommendation_item_count

    metrics = RecommendationMetrics(
        case_count=len(case_reports),
        usefulness_accuracy=_safe_ratio(useful_count, len(case_reports)),
        grounding_accuracy=_safe_ratio(grounded_count, len(case_reports)),
        blocker_guardrail_accuracy=_safe_ratio(guardrail_count, len(case_reports)),
        hallucination_rate=_safe_ratio(total_ungrounded_items, total_items),
    )
    return RecommendationReport(
        manifest_path=str(manifest_path.relative_to(REPO_ROOT)),
        report_label=report_label,
        generated_at=generated_at,
        metrics=metrics,
        cases=case_reports,
    )


def _load_manifest(path: Path) -> list[RecommendationCase]:
    raw_manifest = _load_json(path)
    return [RecommendationCase.model_validate(item) for item in raw_manifest["cases"]]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_case(
    case: RecommendationCase,
    samples_dir: Path,
) -> LearningPlanResponse | InterviewSimulationResponse:
    resume_text = (samples_dir / case.resume_sample).read_text(encoding="utf-8")
    jd_text = (samples_dir / case.jd_sample).read_text(encoding="utf-8")
    if case.workflow == "learning_plan":
        return generate_learning_plan_from_text(resume_text, jd_text)
    return generate_interview_simulation_from_text(resume_text, jd_text)


def _build_case_report(
    case: RecommendationCase,
    expected: dict,
    response: LearningPlanResponse | InterviewSimulationResponse,
) -> RecommendationCaseReport:
    recommendation_items = _recommendation_items(response)
    grounded_item_count = sum(1 for item in recommendation_items if item.evidence_used)
    missing_expectations: list[str] = []
    expected_mode = expected["expected_generation_mode"]
    if response.gating.generation_mode != expected_mode:
        missing_expectations.append(f"generation_mode={expected_mode}")

    minimum_items = expected["minimum_recommendation_items"]
    if len(recommendation_items) < minimum_items:
        missing_expectations.append(f"minimum_recommendation_items={minimum_items}")

    require_guardrail = expected.get("expect_blocker_guardrail", False)
    guardrail_ok = _has_guardrail(response) if require_guardrail else True
    if require_guardrail and not guardrail_ok:
        missing_expectations.append("blocker_guardrail")

    grounded = grounded_item_count == len(recommendation_items) and bool(recommendation_items)
    if not grounded:
        missing_expectations.append("grounded_items")

    hallucination_rate = round(
        (len(recommendation_items) - grounded_item_count) / max(len(recommendation_items), 1),
        3,
    )
    return RecommendationCaseReport(
        case_id=case.case_id,
        workflow=case.workflow,
        generation_mode=response.gating.generation_mode,
        useful=not any(item.startswith("minimum_recommendation_items") for item in missing_expectations),
        grounded=grounded,
        blocker_guardrail_ok=guardrail_ok,
        hallucination_rate=hallucination_rate,
        recommendation_item_count=len(recommendation_items),
        missing_expectations=missing_expectations,
    )


def _recommendation_items(
    response: LearningPlanResponse | InterviewSimulationResponse,
) -> list:
    if isinstance(response, LearningPlanResponse):
        return response.plan_steps
    return response.simulation_rounds


def _has_guardrail(response: LearningPlanResponse | InterviewSimulationResponse) -> bool:
    if isinstance(response, LearningPlanResponse):
        return bool(response.blocker_cautions)
    return any(round_item.caution for round_item in response.simulation_rounds) or any(
        "blocker" in note.lower() for note in response.coach_notes
    )


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 3)


def main() -> None:
    """Run the recommendation benchmark and print a JSON report."""
    report = run_recommendation_benchmark()
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
