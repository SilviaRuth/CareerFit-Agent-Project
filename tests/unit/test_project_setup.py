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
        SAMPLES_DIR / "low_confidence_resume.txt",
        SAMPLES_DIR / "responsibility_heavy_jd.txt",
        SAMPLES_DIR / "alex_targeted_resume.txt",
        SAMPLES_DIR / "alex_general_resume.txt",
        SAMPLES_DIR / "alex_claimy_resume.txt",
        SAMPLES_DIR / "scanned_resume_placeholder.pdf",
        SAMPLES_DIR / "scanned_resume_image.png",
        SAMPLES_DIR / "clean_text_resume.pdf",
        EVAL_DIR / "strong_fit_expected.json",
        EVAL_DIR / "partial_fit_expected.json",
        EVAL_DIR / "poor_fit_expected.json",
        EVAL_DIR / "comparison_manifest.json",
        EVAL_DIR / "benchmark_manifest.json",
        EVAL_DIR / "extraction_manifest.json",
        EVAL_DIR / "multimodal_manifest.json",
        EVAL_DIR / "scanned_pdf_resume_ingestion_expected.json",
        EVAL_DIR / "image_resume_ingestion_expected.json",
        EVAL_DIR / "clean_text_pdf_resume_ingestion_expected.json",
    ]

    assert SAMPLES_DIR.is_dir()
    assert EVAL_DIR.is_dir()
    assert all(path.exists() for path in expected_paths)
