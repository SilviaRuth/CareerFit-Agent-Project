"""Unit tests for the fixture-backed benchmark runner."""

from __future__ import annotations

from app.evaluation.benchmark_runner import run_benchmark


def test_benchmark_runner_matches_current_gold_fixture_expectations() -> None:
    report = run_benchmark()

    assert report.metrics.case_count == 15
    assert report.metrics.fit_label_accuracy == 1.0
    assert report.metrics.blocker_flag_accuracy == 1.0
    assert report.metrics.required_match_recall == 1.0
    assert report.metrics.preferred_match_recall == 1.0
    assert report.metrics.top_gap_coverage == 1.0

    strong_case = next(case for case in report.cases if case.pair_id == "strong_fit")
    partial_case = next(case for case in report.cases if case.pair_id == "partial_fit")
    poor_case = next(case for case in report.cases if case.pair_id == "poor_fit")

    assert strong_case.predicted_fit_label == "strong"
    assert strong_case.overall_score == 89
    assert partial_case.predicted_fit_label == "partial"
    assert partial_case.overall_score == 58
    assert poor_case.predicted_fit_label == "poor"
    assert poor_case.overall_score == 7

    messy_jd_case = next(case for case in report.cases if case.pair_id == "strong_vs_messy_jd")
    dataset_case = next(case for case in report.cases if case.pair_id == "eng11981094_vs_backend")

    assert messy_jd_case.predicted_fit_label == "strong"
    assert messy_jd_case.overall_score == 92
    assert dataset_case.predicted_fit_label == "poor"
    assert dataset_case.overall_score == 46

    responsibility_case = next(
        case for case in report.cases if case.pair_id == "strong_vs_responsibility_heavy"
    )
    accountant_case = next(case for case in report.cases if case.pair_id == "accountant_vs_backend")

    assert responsibility_case.predicted_fit_label == "partial"
    assert responsibility_case.overall_score == 78
    assert accountant_case.predicted_fit_label == "poor"
    assert accountant_case.overall_score == 30
