"""FastAPI entrypoint for the CareerFit backend service."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.career import router as career_router
from app.api.routes.comparison import router as comparison_router
from app.api.routes.generation import router as generation_router
from app.api.routes.health import router as health_router
from app.api.routes.llm_generation import router as llm_generation_router
from app.api.routes.match import router as match_router
from app.api.routes.parse import router as parse_router
from app.llm.config import load_local_dotenv


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    load_local_dotenv()
    app = FastAPI(title="CareerFit Agent", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:5174",
            "http://localhost:5174",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(match_router)
    app.include_router(parse_router)
    app.include_router(generation_router)
    app.include_router(llm_generation_router)
    app.include_router(comparison_router)
    app.include_router(career_router)
    return app


app = create_app()
