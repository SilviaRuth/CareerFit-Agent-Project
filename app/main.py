"""FastAPI entrypoint for the CareerFit backend service."""

from fastapi import FastAPI

from app.api.routes.career import router as career_router
from app.api.routes.comparison import router as comparison_router
from app.api.routes.generation import router as generation_router
from app.api.routes.health import router as health_router
from app.api.routes.match import router as match_router
from app.api.routes.parse import router as parse_router


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    app = FastAPI(title="CareerFit Agent", version="0.1.0")
    app.include_router(health_router)
    app.include_router(match_router)
    app.include_router(parse_router)
    app.include_router(generation_router)
    app.include_router(comparison_router)
    app.include_router(career_router)
    return app


app = create_app()
