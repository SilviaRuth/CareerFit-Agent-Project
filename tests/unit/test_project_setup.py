"""Project setup tests for the Milestone 1 developer workflow layer."""

from __future__ import annotations

from app.core.config import MATCH_WEIGHTS
from tests.conftest import EVAL_DIR, SAMPLES_DIR


def test_match_weights_sum_to_100() -> None:
    """The documented Milestone 1 weights should stay normalized."""
    assert sum(MATCH_WEIGHTS.values()) == 100


def test_sample_and_eval_directories_exist_with_seed_fixtures() -> None:
    """Milestone 1 relies on the starter strong, partial, and poor fit fixtures."""
    expected_paths = [
        SAMPLES_DIR / "strong_fit_resume.txt",
        SAMPLES_DIR / "strong_fit_jd.txt",
        SAMPLES_DIR / "partial_fit_resume.txt",
        SAMPLES_DIR / "partial_fit_jd.txt",
        SAMPLES_DIR / "poor_fit_resume.txt",
        SAMPLES_DIR / "poor_fit_jd.txt",
        SAMPLES_DIR / "messy_resume.txt",
        SAMPLES_DIR / "messy_jd.txt",
        EVAL_DIR / "strong_fit_expected.json",
        EVAL_DIR / "partial_fit_expected.json",
        EVAL_DIR / "poor_fit_expected.json",
    ]

    assert SAMPLES_DIR.is_dir()
    assert EVAL_DIR.is_dir()
    assert all(path.exists() for path in expected_paths)
