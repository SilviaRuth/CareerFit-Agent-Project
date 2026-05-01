"""Optional LLM advisory generation endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.llm.advisory import run_llm_advisory_generation
from app.schemas.generation import GroundedGenerationRequest
from app.schemas.llm_generation import LLMAdvisoryResponse

router = APIRouter(tags=["llm-generation"])


@router.post("/llm/advice", response_model=LLMAdvisoryResponse)
def llm_advice(request: GroundedGenerationRequest) -> LLMAdvisoryResponse:
    """Return deterministic match artifacts plus optional validated LLM advice."""
    return run_llm_advisory_generation(request)

