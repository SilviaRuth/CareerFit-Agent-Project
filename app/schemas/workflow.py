"""Additive workflow tracing schemas for orchestration and frontend visibility."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Allowed lifecycle states for workflow and step traces."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStepTrace(BaseModel):
    """Trace metadata for one deterministic workflow step."""

    step_name: str
    status: WorkflowStatus
    service_name: str | None = None
    input_schema_version: str | None = None
    output_schema_version: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class WorkflowTrace(BaseModel):
    """Top-level workflow trace container.

    This schema is intentionally additive. It explains workflow execution but does
    not replace evidence spans, parser confidence, warnings, blockers, or other
    response fields.
    """

    trace_id: str
    workflow_name: str
    status: WorkflowStatus
    steps: list[WorkflowStepTrace] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class WorkflowResult(BaseModel):
    """Internal result envelope for deterministic workflow/service outputs.

    This schema is additive and is not wired into public endpoint responses yet.
    """

    workflow_name: str
    status: WorkflowStatus
    output_schema_version: str | None = None
    output: dict[str, Any] = Field(default_factory=dict)
    trace: WorkflowTrace | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recoverable_errors: list[str] = Field(default_factory=list)
