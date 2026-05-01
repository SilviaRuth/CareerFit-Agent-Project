"""Integration tests for Milestone 5 career workflow endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import load_sample


def test_profile_memory_and_grounding_endpoints_work_together() -> None:
    client = TestClient(app)

    memory_response = client.post(
        "/profile-memory",
        json={
            "resume_text": load_sample("strong_fit_resume.txt"),
            "source_name": "strong_fit_resume.txt",
        },
    )

    assert memory_response.status_code == 200
    profile_memory = memory_response.json()
    assert profile_memory["memory_items"]

    retrieval_response = client.post(
        "/retrieve/evidence",
        json={
            "profile_memory": profile_memory,
            "query": "python fastapi backend",
        },
    )
    assert retrieval_response.status_code == 200
    retrieval_payload = retrieval_response.json()
    assert retrieval_payload["retrieved_items"]
    assert retrieval_payload["workflow_trace"]["workflow_name"] == "retrieve_evidence"

    semantic_response = client.post(
        "/semantic/match",
        json={
            "profile_memory": profile_memory,
            "labels": ["postgres", "api design"],
            "mode": "heuristic",
        },
    )
    assert semantic_response.status_code == 200
    semantic_payload = semantic_response.json()
    assert semantic_payload["signals"]
    assert semantic_payload["workflow_trace"]["workflow_name"] == "semantic_match"


def test_compare_jobs_endpoint_returns_ranked_cross_jd_output() -> None:
    client = TestClient(app)

    response = client.post(
        "/compare/jobs",
        json={
            "resume_text": load_sample("strong_fit_resume.txt"),
            "job_descriptions": [
                {
                    "jd_id": "strong",
                    "job_description_text": load_sample("strong_fit_jd.txt"),
                },
                {
                    "jd_id": "poor",
                    "job_description_text": load_sample("poor_fit_jd.txt"),
                },
            ],
            "semantic_mode": "heuristic",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["compared_count"] == 2
    assert payload["ranking"][0]["jd_id"] == "strong"
    assert payload["ranking"][0]["recommended_next_steps"]
    assert payload["ranking"][0]["retrieved_evidence"]
    assert payload["workflow_trace"]["workflow_name"] == "compare_jobs"
    assert [step["step_name"] for step in payload["workflow_trace"]["steps"]] == [
        "parse_resume",
        "parse_job_description",
        "score_match",
        "collect_evidence",
        "compute_blockers",
        "build_recommendations",
        "rank_jobs",
    ]
