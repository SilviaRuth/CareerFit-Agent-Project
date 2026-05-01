"""Validation tests for additive workflow trace and document schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.document import DocumentInput, DocumentPage, DocumentSegment, NormalizedDocument
from app.schemas.parse import ParserConfidence, ParserDiagnostic
from app.schemas.workflow import WorkflowResult, WorkflowStatus, WorkflowStepTrace, WorkflowTrace


def test_workflow_trace_accepts_ordered_step_models() -> None:
    trace = WorkflowTrace(
        trace_id="trace-1",
        workflow_name="match",
        status=WorkflowStatus.COMPLETED,
        steps=[
            WorkflowStepTrace(
                step_name="parse_resume",
                service_name="parse_service",
                status=WorkflowStatus.COMPLETED,
                input_schema_version="v1",
                output_schema_version="v1",
                duration_ms=12,
            )
        ],
    )

    assert trace.steps[0].status == WorkflowStatus.COMPLETED
    assert trace.steps[0].duration_ms == 12


def test_workflow_step_rejects_unknown_status_and_negative_duration() -> None:
    with pytest.raises(ValidationError):
        WorkflowStepTrace.model_validate(
            {"step_name": "parse", "status": "done", "duration_ms": -1}
        )


def test_workflow_result_wraps_internal_output_and_trace() -> None:
    trace = WorkflowTrace(
        trace_id="trace-2",
        workflow_name="learning_plan",
        status=WorkflowStatus.COMPLETED,
        steps=[
            WorkflowStepTrace(
                step_name="render_plan",
                service_name="learning_plan_service",
                status=WorkflowStatus.COMPLETED,
            )
        ],
    )

    result = WorkflowResult(
        workflow_name="learning_plan",
        status=WorkflowStatus.COMPLETED,
        output_schema_version="v1",
        output={"summary": "Focus on backend evidence gaps."},
        trace=trace,
        confidence_score=0.91,
        evidence_refs=["resume:skills:python"],
        warnings=["internal contract only"],
    )

    assert result.output["summary"] == "Focus on backend evidence gaps."
    assert result.trace is not None
    assert result.trace.steps[0].service_name == "learning_plan_service"
    assert result.recoverable_errors == []


def test_workflow_result_rejects_unknown_status_and_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        WorkflowResult.model_validate(
            {
                "workflow_name": "match",
                "status": "done",
                "confidence_score": 1.2,
            }
        )


def test_workflow_and_document_schemas_serialize_to_json_ready_dicts() -> None:
    trace = WorkflowTrace(
        trace_id="trace-serialize",
        workflow_name="match",
        status=WorkflowStatus.COMPLETED,
        steps=[
            WorkflowStepTrace(
                step_name="score",
                service_name="matching_service",
                status=WorkflowStatus.COMPLETED,
                duration_ms=8,
            )
        ],
    )
    result = WorkflowResult(
        workflow_name="match",
        status=WorkflowStatus.COMPLETED,
        output_schema_version="v1",
        output={"fit_label": "strong"},
        trace=trace,
        confidence_score=0.99,
        evidence_refs=["resume:experience:backend"],
    )
    document = NormalizedDocument(
        source_type="text",
        filename="resume.txt",
        media_type="text/plain",
        text="Backend engineer",
        segments=[
            DocumentSegment(
                segment_id="segment-serialize",
                source_type="text",
                text="Backend engineer",
                start_char=0,
                end_char=16,
            )
        ],
    )

    result_payload = result.model_dump(mode="json")
    document_payload = document.model_dump(mode="json")

    assert result_payload["status"] == "completed"
    assert result_payload["trace"]["steps"][0]["status"] == "completed"
    assert result_payload["output"]["fit_label"] == "strong"
    assert document_payload["source_type"] == "text"
    assert document_payload["segments"][0]["segment_id"] == "segment-serialize"


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
        modality="text",
        filename="resume.txt",
        media_type="text/plain",
        text="Python backend engineer",
        page_number=1,
        start_char=0,
        end_char=23,
        diagnostics=[diagnostic],
        confidence=confidence,
        warnings=["review formatting"],
    )
    document = NormalizedDocument(
        source_type="text",
        modality="text",
        filename="resume.txt",
        media_type="text/plain",
        page_count=1,
        text="Python backend engineer",
        pages=[
            DocumentPage(
                page_number=1,
                text="Python backend engineer",
                has_extractable_text=True,
                diagnostics=[diagnostic],
                confidence=confidence,
            )
        ],
        segments=[segment],
        ocr_status="not_required",
        diagnostics=[diagnostic],
        confidence=confidence,
        warnings=["review formatting"],
    )

    assert document.source_type == "text"
    assert document.pages[0].has_extractable_text is True
    assert document.segments[0].page_number == 1
    assert document.segments[0].confidence is not None
    assert document.diagnostics[0].source == "normalization"


def test_document_schemas_represent_image_needs_ocr_without_text() -> None:
    diagnostic = ParserDiagnostic(
        warning_code="image_requires_ocr",
        message="Image needs OCR before extraction.",
        source="ingestion",
        severity="error",
    )
    document = NormalizedDocument(
        source_type="image",
        modality="image",
        filename="resume.png",
        media_type="image/png",
        page_count=1,
        text="",
        pages=[
            DocumentPage(
                page_number=1,
                text="",
                has_extractable_text=False,
                requires_ocr=True,
                diagnostics=[diagnostic],
            )
        ],
        segments=[
            DocumentSegment(
                segment_id="image-1",
                source_type="image",
                modality="image",
                segment_type="image",
                text="",
                filename="resume.png",
                media_type="image/png",
                page_number=1,
                requires_ocr=True,
                ocr_status="required",
                unsupported_reason="image_requires_ocr",
                diagnostics=[diagnostic],
            )
        ],
        ocr_status="required",
        requires_ocr=True,
        diagnostics=[diagnostic],
    )

    payload = document.model_dump(mode="json")
    assert payload["requires_ocr"] is True
    assert payload["pages"][0]["requires_ocr"] is True
    assert payload["segments"][0]["unsupported_reason"] == "image_requires_ocr"


def test_document_input_rejects_unknown_source_type() -> None:
    with pytest.raises(ValidationError):
        DocumentInput.model_validate({"source_type": "ocr", "text": "raw text"})
