"""Additive workflow tracing schemas for future orchestration visibility."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Allowed lifecycle states for workflow and step traces."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
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
    error: str | None = None


class WorkflowTrace(BaseModel):
    """Top-level workflow trace container.

    This schema is intentionally additive and is not wired into endpoint responses yet.
    """

    trace_id: str
    workflow_name: str
    status: WorkflowStatus
    steps: list[WorkflowStepTrace] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
