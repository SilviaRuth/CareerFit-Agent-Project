"""Validation tests for additive workflow trace and document schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.document import DocumentInput, DocumentSegment, NormalizedDocument
from app.schemas.parse import ParserConfidence, ParserDiagnostic
from app.schemas.workflow import WorkflowStatus, WorkflowStepTrace, WorkflowTrace


def test_workflow_trace_accepts_ordered_step_models() -> None:
    trace = WorkflowTrace(
        trace_id="trace-1",
        workflow_name="match",
        status=WorkflowStatus.SUCCEEDED,
        steps=[
            WorkflowStepTrace(
                step_name="parse_resume",
                service_name="parse_service",
                status=WorkflowStatus.SUCCEEDED,
                input_schema_version="v1",
                output_schema_version="v1",
                duration_ms=12,
            )
        ],
    )

    assert trace.steps[0].status == WorkflowStatus.SUCCEEDED
    assert trace.steps[0].duration_ms == 12


def test_workflow_step_rejects_unknown_status_and_negative_duration() -> None:
    with pytest.raises(ValidationError):
        WorkflowStepTrace.model_validate(
            {"step_name": "parse", "status": "done", "duration_ms": -1}
        )


def test_document_schemas_accept_initial_multimodal_contract_fields() -> None:
    confidence = ParserConfidence(
        score=0.82,
        level="medium",
        extraction_complete=True,
        factors=["text_input"],
    )
    diagnostic = ParserDiagnostic(
        warning_code="normalized",
        message="Whitespace normalized.",
        source="normalization",
        severity="info",
    )
    segment = DocumentSegment(
        segment_id="segment-1",
        source_type="text",
        filename="resume.txt",
        media_type="text/plain",
        text="Python backend engineer",
        start_char=0,
        end_char=23,
        diagnostics=[diagnostic],
        confidence=confidence,
        warnings=["review formatting"],
    )
    document = NormalizedDocument(
        source_type="text",
        filename="resume.txt",
        media_type="text/plain",
        text="Python backend engineer",
        segments=[segment],
        diagnostics=[diagnostic],
        confidence=confidence,
        warnings=["review formatting"],
    )

    assert document.source_type == "text"
    assert document.segments[0].confidence is not None
    assert document.diagnostics[0].source == "normalization"


def test_document_input_rejects_unknown_source_type() -> None:
    with pytest.raises(ValidationError):
        DocumentInput.model_validate({"source_type": "ocr", "text": "raw text"})
