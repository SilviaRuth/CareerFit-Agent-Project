"""Offline benchmark runner for fixture-backed matching regression coverage."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.schemas.match import MatchResult
from app.services.matching_service import match_resume_to_jd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLES_DIR = REPO_ROOT / "data" / "samples"
DEFAULT_EVAL_DIR = REPO_ROOT / "data" / "eval"
DEFAULT_MANIFEST_PATH = DEFAULT_EVAL_DIR / "benchmark_manifest.json"


class BenchmarkCase(BaseModel):
    """Manifest entry for one offline benchmark case."""

    pair_id: str
    resume_sample: str
    jd_sample: str
    expected_eval: str


class BenchmarkMetrics(BaseModel):
    """Aggregate metrics for the current benchmark run."""

    case_count: int
    fit_label_accuracy: float
    blocker_flag_accuracy: float
    required_match_recall: float
    preferred_match_recall: float
    top_gap_coverage: float


class BenchmarkCaseReport(BaseModel):
    """Detailed report for one benchmark case."""

    pair_id: str
    overall_score: int
    predicted_fit_label: str
    expected_fit_label: str
    fit_label_correct: bool
    blocker_flags_match: bool
    required_match_recall: float
    preferred_match_recall: float
    top_gap_coverage: float
    score_snapshot: dict[str, int]
    blocker_flags: dict[str, bool]
    missing_expected_required_matches: list[str] = Field(default_factory=list)
    missing_expected_preferred_matches: list[str] = Field(default_factory=list)
    missing_expected_top_gaps: list[str] = Field(default_factory=list)


class BenchmarkReport(BaseModel):
    """Structured output for a benchmark run."""

    manifest_path: str
    report_label: str | None = None
    generated_at: str | None = None
    metrics: BenchmarkMetrics
    cases: list[BenchmarkCaseReport]


def run_benchmark(
    manifest_path: Path | None = None,
    *,
    samples_dir: Path | None = None,
    eval_dir: Path | None = None,
    report_label: str | None = None,
    generated_at: str | None = None,
) -> BenchmarkReport:
    """Execute the fixture-backed benchmark and return a structured report."""
    manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
    samples_dir = samples_dir or DEFAULT_SAMPLES_DIR
    eval_dir = eval_dir or DEFAULT_EVAL_DIR

    cases = _load_manifest(manifest_path)
    case_reports: list[BenchmarkCaseReport] = []
    blocker_flags_total = 0
    blocker_flags_correct = 0
    expected_required_total = 0
    expected_required_found = 0
    expected_preferred_total = 0
    expected_preferred_found = 0
    expected_gaps_total = 0
    expected_gaps_found = 0

    for case in cases:
        expected = _load_json(eval_dir / case.expected_eval)
        match_result = match_resume_to_jd(
            _resolve_text_path(case.resume_sample, samples_dir).read_text(encoding="utf-8"),
            _resolve_text_path(case.jd_sample, samples_dir).read_text(encoding="utf-8"),
        )
        case_report = _build_case_report(case, expected, match_result)
        case_reports.append(case_report)

        blocker_flags_total += len(expected["blocker_flags"])
        blocker_flags_correct += sum(
            int(case_report.blocker_flags[key] == value)
            for key, value in expected["blocker_flags"].items()
        )
        expected_required_total += len(expected["required_skill_matches"])
        expected_required_found += len(expected["required_skill_matches"]) - len(
            case_report.missing_expected_required_matches
        )
        expected_preferred_total += len(expected["preferred_skill_matches"])
        expected_preferred_found += len(expected["preferred_skill_matches"]) - len(
            case_report.missing_expected_preferred_matches
        )
        expected_gaps_total += len(expected["top_gaps"])
        expected_gaps_found += len(expected["top_gaps"]) - len(
            case_report.missing_expected_top_gaps
        )

    metrics = BenchmarkMetrics(
        case_count=len(case_reports),
        fit_label_accuracy=_safe_ratio(
            sum(report.fit_label_correct for report in case_reports),
            len(case_reports),
        ),
        blocker_flag_accuracy=_safe_ratio(blocker_flags_correct, blocker_flags_total),
        required_match_recall=_safe_ratio(expected_required_found, expected_required_total),
        preferred_match_recall=_safe_ratio(expected_preferred_found, expected_preferred_total),
        top_gap_coverage=_safe_ratio(expected_gaps_found, expected_gaps_total),
    )
    return BenchmarkReport(
        manifest_path=str(manifest_path.relative_to(REPO_ROOT)),
        report_label=report_label,
        generated_at=generated_at,
        metrics=metrics,
        cases=case_reports,
    )


def _load_manifest(path: Path) -> list[BenchmarkCase]:
    raw_manifest = _load_json(path)
    return [BenchmarkCase.model_validate(item) for item in raw_manifest["cases"]]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_text_path(value: str, samples_dir: Path) -> Path:
    explicit_path = REPO_ROOT / value
    if explicit_path.exists():
        return explicit_path
    return samples_dir / value


def _build_case_report(
    case: BenchmarkCase,
    expected: dict,
    match_result: MatchResult,
) -> BenchmarkCaseReport:
    matched_required = {
        match.requirement_label
        for match in match_result.required_matches
        if match.status == "matched"
    }
    matched_preferred = {
        match.requirement_label
        for match in match_result.preferred_matches
        if match.status == "matched"
    }
    actual_gap_pairs = {
        f"{gap.requirement_label}|{gap.requirement_priority}|{gap.gap_type}"
        for gap in match_result.gaps
    }
    expected_gap_pairs = [
        f"{gap['requirement_label']}|{gap['requirement_priority']}|{gap['gap_type']}"
        for gap in expected["top_gaps"]
    ]

    missing_required = sorted(set(expected["required_skill_matches"]) - matched_required)
    missing_preferred = sorted(set(expected["preferred_skill_matches"]) - matched_preferred)
    missing_gap_pairs = sorted(set(expected_gap_pairs) - actual_gap_pairs)
    predicted_fit_label = _derive_fit_label(match_result)

    return BenchmarkCaseReport(
        pair_id=case.pair_id,
        overall_score=match_result.overall_score,
        predicted_fit_label=predicted_fit_label,
        expected_fit_label=expected["expected_fit_label"],
        fit_label_correct=predicted_fit_label == expected["expected_fit_label"],
        blocker_flags_match=match_result.blocker_flags.model_dump() == expected["blocker_flags"],
        required_match_recall=_safe_ratio(
            len(expected["required_skill_matches"]) - len(missing_required),
            len(expected["required_skill_matches"]),
        ),
        preferred_match_recall=_safe_ratio(
            len(expected["preferred_skill_matches"]) - len(missing_preferred),
            len(expected["preferred_skill_matches"]),
        ),
        top_gap_coverage=_safe_ratio(
            len(expected_gap_pairs) - len(missing_gap_pairs),
            len(expected_gap_pairs),
        ),
        score_snapshot=match_result.dimension_scores.model_dump(),
        blocker_flags=match_result.blocker_flags.model_dump(),
        missing_expected_required_matches=missing_required,
        missing_expected_preferred_matches=missing_preferred,
        missing_expected_top_gaps=missing_gap_pairs,
    )


def _derive_fit_label(match_result: MatchResult) -> str:
    """Map the current deterministic score shape into coarse benchmark labels."""
    blockers = match_result.blocker_flags
    if blockers.missing_required_skills or blockers.seniority_mismatch:
        return "poor"
    if match_result.overall_score >= 80 and not blockers.unsupported_claims:
        return "strong"
    if match_result.overall_score >= 40:
        return "partial"
    return "poor"


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 3)


def main() -> None:
    """Run the benchmark and print a JSON report."""
    report = run_benchmark()
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
