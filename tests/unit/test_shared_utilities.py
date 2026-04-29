"""Tests for shared deterministic helper utilities."""

from __future__ import annotations

from types import SimpleNamespace

from app.evaluation.utils import safe_ratio
from app.schemas.match import BlockerFlags
from app.services.fit_label import derive_fit_label
from app.services.tokenization import tokenize_keywords


def test_derive_fit_label_preserves_existing_thresholds() -> None:
    assert derive_fit_label(_match_result(89, BlockerFlags())) == "strong"
    assert derive_fit_label(_match_result(80, BlockerFlags(unsupported_claims=True))) == "partial"
    assert derive_fit_label(_match_result(58, BlockerFlags())) == "partial"
    assert derive_fit_label(_match_result(39, BlockerFlags())) == "poor"
    assert derive_fit_label(
        _match_result(92, BlockerFlags(missing_required_skills=True))
    ) == "poor"
    assert derive_fit_label(_match_result(92, BlockerFlags(seniority_mismatch=True))) == "poor"


def test_safe_ratio_matches_runner_rounding_contract() -> None:
    assert safe_ratio(0, 0) == 1.0
    assert safe_ratio(1, 3) == 0.333
    assert safe_ratio(2, 2) == 1.0


def test_tokenize_keywords_matches_retrieval_semantic_contract() -> None:
    assert tokenize_keywords("AI, C++, Python 3.11 and R") == {"ai", "python", "11", "and"}


def _match_result(overall_score: int, blocker_flags: BlockerFlags):
    return SimpleNamespace(overall_score=overall_score, blocker_flags=blocker_flags)
