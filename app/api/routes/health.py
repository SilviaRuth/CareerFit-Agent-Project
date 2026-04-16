"""Health endpoint for basic service sanity checks."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    """Return a simple health response."""
    return {"status": "ok"}
