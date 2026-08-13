"""Novel Ignite FastAPI application entry point.

Serves the static prototype UI and versioned API routes.
"""
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.infrastructure.config import settings
from app.infrastructure.observability import record_request
from app.api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Novel Ignite",
        description="AI-powered novel creation platform — from idea to next chapter.",
        version="2.0.0-dev",
    )

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        from app.infrastructure.observability import log_event, record_request

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001
            log_event("request_error", method=request.method, path=request.url.path, error_type=type(exc).__name__, message=str(exc)[:500])
            response = JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
        duration_ms = (time.perf_counter() - start) * 1000
        record_request(request.method, request.url.path, response.status_code, duration_ms)
        # 开发期避免浏览器缓存过期的原型静态资源（app.js/styles.css 频繁迭代）
        if request.url.path.startswith("/prototype/"):
            response.headers["Cache-Control"] = "no-store"
        return response

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

    @app.get("/metrics")
    async def metrics():
        from app.infrastructure.observability import snapshot

        return snapshot()

    return app


app = create_app()
