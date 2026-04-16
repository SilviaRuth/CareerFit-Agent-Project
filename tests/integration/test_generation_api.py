"""Integration tests for grounded generation endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import load_sample


def test_rewrite_endpoint_returns_grounded_structured_output() -> None:
    client = TestClient(app)

    response = client.post(
        "/rewrite",
        json={
            "resume_text": load_sample("partial_fit_resume.txt"),
            "job_description_text": load_sample("partial_fit_jd.txt"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "prioritized_actions" in payload
    assert "generation_warnings" in payload
    assert "gating" in payload
    assert payload["prioritized_actions"]
    assert any(action["evidence_used"] for action in payload["prioritized_actions"])


def test_interview_prep_endpoint_returns_grounded_structured_output() -> None:
    client = TestClient(app)

    response = client.post(
        "/interview-prep",
        json={
            "resume_text": load_sample("strong_fit_resume.txt"),
            "job_description_text": load_sample("strong_fit_jd.txt"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["likely_focus_areas"]
    assert payload["interview_questions"]
    assert payload["recommended_talking_points"]
    assert payload["evidence_used"]


def test_generation_endpoints_degrade_safely_for_low_confidence_parse() -> None:
    client = TestClient(app)
    payload = {
        "resume_text": load_sample("low_confidence_resume.txt"),
        "job_description_text": load_sample("responsibility_heavy_jd.txt"),
    }

    rewrite_response = client.post("/rewrite", json=payload)
    interview_response = client.post("/interview-prep", json=payload)

    assert rewrite_response.status_code == 200
    assert interview_response.status_code == 200
    assert rewrite_response.json()["gating"]["generation_mode"] == "minimal"
    assert interview_response.json()["gating"]["generation_mode"] == "minimal"
