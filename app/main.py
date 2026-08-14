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
        if not request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": app.version}

    @app.get("/metrics")
    async def metrics():
        from app.infrastructure.observability import snapshot

        return snapshot()

    # 前端 UI 挂在根路径 / 下，直接访问 http://127.0.0.1:8000/ 即可；
    # 文件仍组织在 prototype/ 目录，避免污染仓库根目录。
    # 注意：mount("/") 必须在所有 API/health/metrics 路由之后注册，
    # 否则会拦截这些路径。docs/openapi.json 由 FastAPI 在应用初始化时注册，不受影响。
    prototype_dir = Path(__file__).resolve().parent.parent / "prototype"
    if prototype_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(prototype_dir), html=True), name="prototype")

    return app


app = create_app()
