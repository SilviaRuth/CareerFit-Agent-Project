"""Offline comparison benchmark runner for multi-resume ranking regression coverage."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.evaluation.utils import safe_ratio
from app.schemas.comparison import MultiResumeComparisonRequest, ResumeComparisonInput
from app.services.comparison_service import compare_resumes_to_jd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLES_DIR = REPO_ROOT / "data" / "samples"
DEFAULT_EVAL_DIR = REPO_ROOT / "data" / "eval"
DEFAULT_MANIFEST_PATH = DEFAULT_EVAL_DIR / "comparison_manifest.json"


class ComparisonResumeCase(BaseModel):
    """One resume entry inside a comparison benchmark scenario."""

    resume_id: str
    sample_name: str
    source_name: str | None = None


class ComparisonScenario(BaseModel):
    """Manifest entry for one multi-resume ranking scenario."""

    scenario_id: str
    jd_sample: str
    resumes: list[ComparisonResumeCase] = Field(default_factory=list)
    expected_eval: str


class ComparisonMetrics(BaseModel):
    """Aggregate metrics for comparison benchmark coverage."""

    scenario_count: int
    ranking_accuracy: float
    fit_label_accuracy: float
    low_confidence_order_accuracy: float


class ComparisonScenarioReport(BaseModel):
    """Detailed report for one comparison benchmark scenario."""

    scenario_id: str
    top_resume_id: str
    top_fit_label: str
    role_focus: str
    actual_order: list[str] = Field(default_factory=list)
    expected_order: list[str] = Field(default_factory=list)
    ranking_correct: bool
    fit_label_accuracy: float
    low_confidence_order_correct: bool
    parser_levels: dict[str, str] = Field(default_factory=dict)
    fit_labels: dict[str, str] = Field(default_factory=dict)


class ComparisonReport(BaseModel):
    """Structured output for comparison benchmark scenarios."""

    manifest_path: str
    report_label: str | None = None
    generated_at: str | None = None
    metrics: ComparisonMetrics
    cases: list[ComparisonScenarioReport]


def run_comparison_benchmark(
    manifest_path: Path | None = None,
    *,
    samples_dir: Path | None = None,
    eval_dir: Path | None = None,
    report_label: str | None = None,
    generated_at: str | None = None,
) -> ComparisonReport:
    """Execute representative multi-resume comparison scenarios."""
    manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
    samples_dir = samples_dir or DEFAULT_SAMPLES_DIR
    eval_dir = eval_dir or DEFAULT_EVAL_DIR

    raw_manifest = _load_json(manifest_path)
    scenarios = [ComparisonScenario.model_validate(item) for item in raw_manifest["scenarios"]]
    reports: list[ComparisonScenarioReport] = []
    fit_label_checks = 0
    fit_label_correct = 0

    for scenario in scenarios:
        expected = _load_json(eval_dir / scenario.expected_eval)
        request = MultiResumeComparisonRequest(
            resumes=[
                ResumeComparisonInput(
                    resume_id=resume.resume_id,
                    resume_text=_resolve_text_path(resume.sample_name, samples_dir).read_text(
                        encoding="utf-8"
                    ),
                    source_name=resume.source_name,
                )
                for resume in scenario.resumes
            ],
            job_description_text=_resolve_text_path(scenario.jd_sample, samples_dir).read_text(
                encoding="utf-8"
            ),
        )
        response = compare_resumes_to_jd(request)
        report = _build_scenario_report(scenario, expected, response)
        reports.append(report)
        fit_label_checks += len(expected["expected_fit_labels"])
        fit_label_correct += round(report.fit_label_accuracy * len(expected["expected_fit_labels"]))

    metrics = ComparisonMetrics(
        scenario_count=len(reports),
        ranking_accuracy=safe_ratio(
            sum(report.ranking_correct for report in reports), len(reports)
        ),
        fit_label_accuracy=safe_ratio(fit_label_correct, fit_label_checks),
        low_confidence_order_accuracy=safe_ratio(
            sum(report.low_confidence_order_correct for report in reports),
            len(reports),
        ),
    )
    return ComparisonReport(
        manifest_path=str(manifest_path.relative_to(REPO_ROOT)),
        report_label=report_label,
        generated_at=generated_at,
        metrics=metrics,
        cases=reports,
    )


def _build_scenario_report(
    scenario: ComparisonScenario, expected: dict, response
) -> ComparisonScenarioReport:
    actual_order = [entry.resume_id for entry in response.ranking]
    parser_levels = {entry.resume_id: entry.parser_confidence.level for entry in response.ranking}
    fit_labels = {entry.resume_id: entry.fit_label for entry in response.ranking}
    expected_fit_labels = expected["expected_fit_labels"]
    fit_label_accuracy = safe_ratio(
        sum(fit_labels.get(resume_id) == label for resume_id, label in expected_fit_labels.items()),
        len(expected_fit_labels),
    )

    low_confidence_ids = expected.get("low_confidence_resume_ids", [])
    low_confidence_order_correct = (
        all(
            actual_order.index(resume_id) == len(actual_order) - index - 1
            for index, resume_id in enumerate(reversed(low_confidence_ids))
            if resume_id in actual_order
        )
        if low_confidence_ids
        else True
    )

    top_entry = response.ranking[0]
    return ComparisonScenarioReport(
        scenario_id=scenario.scenario_id,
        top_resume_id=top_entry.resume_id,
        top_fit_label=top_entry.fit_label,
        role_focus=top_entry.adaptation_summary.role_focus,
        actual_order=actual_order,
        expected_order=expected["expected_order"],
        ranking_correct=actual_order == expected["expected_order"],
        fit_label_accuracy=fit_label_accuracy,
        low_confidence_order_correct=low_confidence_order_correct,
        parser_levels=parser_levels,
        fit_labels=fit_labels,
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_text_path(value: str, samples_dir: Path) -> Path:
    explicit_path = REPO_ROOT / value
    if explicit_path.exists():
        return explicit_path
    return samples_dir / value

def main() -> None:
    """Run the comparison benchmark and print a JSON report."""
    report = run_comparison_benchmark()
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
