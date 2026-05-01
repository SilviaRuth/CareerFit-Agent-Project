"""Integration tests for multi-resume comparison endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import load_sample


def test_compare_resumes_endpoint_returns_ranked_output() -> None:
    client = TestClient(app)

    response = client.post(
        "/compare/resumes",
        json={
            "resumes": [
                {"resume_id": "strong", "resume_text": load_sample("strong_fit_resume.txt")},
                {"resume_id": "partial", "resume_text": load_sample("partial_fit_resume.txt")},
                {"resume_id": "poor", "resume_text": load_sample("poor_fit_resume.txt")},
            ],
            "job_description_text": load_sample("strong_fit_jd.txt"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["compared_count"] == 3
    assert payload["ranking"][0]["resume_id"] == "strong"
    assert payload["ranking"][0]["fit_label"] == "strong"
    assert payload["ranking"][0]["evidence_summary"]["total_evidence_spans"] > 0
    assert payload["ranking"][0]["adaptation_summary"]["role_focus"] == "backend_platform"
    assert payload["ranking"][2]["resume_id"] == "poor"
    assert payload["workflow_trace"]["workflow_name"] == "compare_resumes"
    assert [step["step_name"] for step in payload["workflow_trace"]["steps"]] == [
        "parse_job_description",
        "parse_resume",
        "score_match",
        "compute_blockers",
        "rank_jobs",
    ]
