from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(title="Novel Ignite API", version="0.1.0")
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.mount("/", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="web")
