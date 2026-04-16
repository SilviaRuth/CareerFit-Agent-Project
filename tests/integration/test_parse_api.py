"""Integration tests for the public parse endpoint contracts."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import build_docx_bytes, build_pdf_bytes, load_sample


def test_parse_resume_endpoint_accepts_json_text_input() -> None:
    client = TestClient(app)

    response = client.post(
        "/parse/resume",
        json={
            "text": load_sample("messy_resume.txt"),
            "source_name": "messy_resume.txt",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "text"
    assert payload["source_name"] == "messy_resume.txt"
    assert payload["schema"]["candidate_name"] == "Jordan Rivera"
    assert payload["parser_confidence"]["level"] == "medium"
    assert payload["unsupported_segments"]


def test_parse_resume_endpoint_accepts_docx_upload() -> None:
    client = TestClient(app)
    content = build_docx_bytes(load_sample("strong_fit_resume.txt").splitlines())

    response = client.post(
        "/parse/resume",
        files={
            "file": (
                "resume.docx",
                content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "file"
    assert payload["source_name"] == "resume.docx"
    assert payload["schema"]["candidate_name"] == "Alex Chen"
    assert payload["schema"]["skills"]


def test_parse_jd_endpoint_accepts_pdf_upload() -> None:
    client = TestClient(app)
    content = build_pdf_bytes(load_sample("strong_fit_jd.txt").splitlines())

    response = client.post(
        "/parse/jd",
        files={"file": ("jd.pdf", content, "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "file"
    assert payload["source_name"] == "jd.pdf"
    assert payload["schema"]["job_title"] == "Senior Backend Engineer"
    assert payload["schema"]["required_requirements"]
