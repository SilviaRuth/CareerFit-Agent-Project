"""Integration tests for the public `/match` API contract."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import load_sample


def test_match_endpoint_returns_structured_json() -> None:
    client = TestClient(app)

    response = client.post(
        "/match",
        json={
            "resume_text": load_sample("strong_fit_resume.txt"),
            "job_description_text": load_sample("strong_fit_jd.txt"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "overall_score" in payload
    assert "dimension_scores" in payload
    assert "required_matches" in payload
    assert "preferred_matches" in payload
    assert "gaps" in payload
    assert "blocker_flags" in payload
    assert payload["blocker_flags"]["missing_required_skills"] is False
