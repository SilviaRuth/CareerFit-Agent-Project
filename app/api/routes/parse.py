"""Parsing endpoints for Milestone 2A ingestion and extraction."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.parse import JDParseResponse, ParseTextRequest, ResumeParseResponse
from app.services.parse_service import (
    parse_jd_file,
    parse_jd_text,
    parse_resume_file,
    parse_resume_text,
)

router = APIRouter(tags=["parsing"])


@router.post("/parse/resume", response_model=ResumeParseResponse)
async def parse_resume(request: Request) -> ResumeParseResponse:
    """Parse resume text or a supported resume file into a structured schema."""
    payload = await _read_parse_request(request)
    try:
        if payload["kind"] == "text":
            return parse_resume_text(payload["text"], source_name=payload["source_name"])
        return parse_resume_file(
            payload["content"],
            filename=payload["filename"],
            media_type=payload["media_type"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/parse/jd", response_model=JDParseResponse)
async def parse_jd(request: Request) -> JDParseResponse:
    """Parse JD text or a supported JD file into a structured schema."""
    payload = await _read_parse_request(request)
    try:
        if payload["kind"] == "text":
            return parse_jd_text(payload["text"], source_name=payload["source_name"])
        return parse_jd_file(
            payload["content"],
            filename=payload["filename"],
            media_type=payload["media_type"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


async def _read_parse_request(request: Request) -> dict[str, str | bytes | None]:
    """Support JSON text inputs and multipart file uploads with one endpoint."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = ParseTextRequest.model_validate(await request.json())
        return {
            "kind": "text",
            "text": payload.text,
            "source_name": payload.source_name,
            "content": None,
            "filename": None,
            "media_type": "text/plain",
        }

    form = await request.form()
    upload = form.get("file")
    if upload is not None:
        filename = getattr(upload, "filename", None) or "upload.txt"
        media_type = getattr(upload, "content_type", None)
        content = await upload.read()
        return {
            "kind": "file",
            "text": None,
            "source_name": None,
            "content": content,
            "filename": filename,
            "media_type": media_type,
        }

    text = form.get("text")
    if isinstance(text, str):
        source_name = form.get("source_name")
        return {
            "kind": "text",
            "text": text,
            "source_name": source_name if isinstance(source_name, str) else None,
            "content": None,
            "filename": None,
            "media_type": "text/plain",
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Provide either JSON text input or a multipart `file` upload.",
    )
