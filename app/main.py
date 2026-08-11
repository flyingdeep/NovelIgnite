"""Novel Ignite FastAPI application entry point.

Serves the static prototype UI and versioned API routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.infrastructure.config import settings
from app.api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Novel Ignite",
        description="AI-powered novel creation platform — from idea to next chapter.",
        version="2.0.0-dev",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    prototype_dir = Path(__file__).resolve().parent.parent / "prototype"
    if prototype_dir.is_dir():
        app.mount("/prototype", StaticFiles(directory=str(prototype_dir), html=True), name="prototype")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": app.version}

    return app


app = create_app()
