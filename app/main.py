"""FastAPI entrypoint for the CareerFit backend MVP."""

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.match import router as match_router


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    app = FastAPI(title="CareerFit Agent", version="0.1.0")
    app.include_router(health_router)
    app.include_router(match_router)
    return app


app = create_app()
