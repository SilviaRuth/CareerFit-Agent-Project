"""Integration tests for the public parse endpoint contracts."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.routes import parse as parse_route
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


def test_parse_resume_endpoint_returns_needs_ocr_for_image_upload() -> None:
    client = TestClient(app)

    response = client.post(
        "/parse/resume",
        files={"file": ("resume.png", b"placeholder", "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    warning_codes = {warning["warning_code"] for warning in payload["warnings"]}
    unsupported_reasons = {segment["reason"] for segment in payload["unsupported_segments"]}
    assert payload["source_type"] == "file"
    assert payload["source_name"] == "resume.png"
    assert payload["raw_text"] == ""
    assert "image_requires_ocr" in warning_codes
    assert "image_requires_ocr" in unsupported_reasons
    assert payload["parser_confidence"]["level"] == "low"


def test_parse_resume_endpoint_returns_400_for_invalid_pdf_upload() -> None:
    client = TestClient(app)

    response = client.post(
        "/parse/resume",
        files={"file": ("broken.pdf", b"not a real pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert "could not be parsed" in response.json()["detail"]


def test_parse_resume_endpoint_returns_413_for_oversized_upload(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(parse_route, "MAX_INGESTION_FILE_BYTES", 16)

    response = client.post(
        "/parse/resume",
        files={"file": ("resume.txt", b"x" * 32, "text/plain")},
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"]
