"""Unit tests for multi-resume comparison benchmark coverage."""

from __future__ import annotations

from app.evaluation.comparison_runner import run_comparison_benchmark


def test_comparison_benchmark_matches_current_multi_resume_expectations() -> None:
    report = run_comparison_benchmark()

    assert report.metrics.scenario_count == 3
    assert report.metrics.ranking_accuracy == 1.0
    assert report.metrics.fit_label_accuracy == 1.0
    assert report.metrics.low_confidence_order_accuracy == 1.0

    backend_variants = next(case for case in report.cases if case.scenario_id == "backend_variants")
    low_confidence = next(
        case for case in report.cases if case.scenario_id == "low_confidence_slate"
    )

    assert backend_variants.actual_order == ["targeted", "claimy", "general"]
    assert backend_variants.role_focus == "backend_platform"
    assert low_confidence.actual_order[-1] == "low_confidence"
    assert low_confidence.parser_levels["low_confidence"] == "low"
