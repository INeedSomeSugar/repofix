from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .cases import all_cases, public_case
from .config import Settings
from .engine import AgentEngine, create_run, public_state
from .schema import Limits
from .storage import RunStore


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    provider: Literal["replay", "deepseek"] = "replay"
    strategy: Literal["feedback", "single_patch"] = "feedback"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    store = RunStore(settings.data_dir / "runs")
    engine = AgentEngine(settings, store)
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="repofix")
    jobs, job_lock = {}, threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        yield
        for state in store.recent(100):
            if state.status in {"running", "queued"}:
                (store.directory(state.run_id) / "pause.request").touch()
        executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="RepoFix", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )
    static = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin and urlsplit(origin).netloc != request.url.netloc:
                return JSONResponse(
                    {"detail": "cross-origin mutation is disabled"}, status_code=403
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        )
        return response

    def load(run_id):
        try:
            return store.load(run_id)
        except (ValueError, FileNotFoundError):
            raise HTTPException(404, "run not found") from None

    def schedule(state):
        with job_lock:
            if state.run_id in jobs and not jobs[state.run_id].done():
                raise HTTPException(409, "run is already queued or running")
            if state.status in {"verified", "failed", "budget_exhausted", "invalid_task"}:
                raise HTTPException(409, "terminal run; create a new run")
            state.status = "queued"
            store.save(state)
            jobs[state.run_id] = executor.submit(engine.run, state.run_id)

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "deepseek_key_present": bool(settings.api_key),
            "configured_model": settings.model or "auto-discover",
            "runner": "trusted_builtin_local_process",
            "arbitrary_repository_upload": False,
        }

    @app.get("/api/cases")
    def cases():
        return [public_case(case) for case in all_cases()]

    @app.get("/api/runs")
    def runs():
        return [public_state(state) for state in store.recent()]

    @app.post("/api/runs", status_code=202)
    def start(body: StartRequest):
        if body.provider == "deepseek" and not settings.api_key:
            raise HTTPException(400, "DEEPSEEK_API_KEY is missing from the server environment")
        with job_lock:
            active = sum(not future.done() for future in jobs.values())
        if active >= 3:
            raise HTTPException(429, "local run queue is full")
        try:
            state = create_run(store, body.case_id, body.provider, body.strategy, Limits())
        except ValueError:
            raise HTTPException(400, "unknown case") from None
        schedule(state)
        return {"run_id": state.run_id, "status": "queued"}

    @app.get("/api/runs/{run_id}")
    def run_detail(run_id: str):
        state = load(run_id)
        patch = store.directory(run_id) / "patch.diff"
        return {
            **public_state(state),
            "patch": patch.read_text(encoding="utf-8") if patch.exists() else "",
        }

    @app.get("/api/runs/{run_id}/events")
    def events(run_id: str):
        load(run_id)
        return store.events(run_id)

    @app.post("/api/runs/{run_id}/pause")
    def pause(run_id: str):
        state = load(run_id)
        if state.status not in {"running", "queued"}:
            raise HTTPException(409, "run is not active")
        (store.directory(run_id) / "pause.request").touch()
        return {"status": "pause_requested"}

    @app.post("/api/runs/{run_id}/resume", status_code=202)
    def resume(run_id: str):
        state = load(run_id)
        schedule(state)
        return {"run_id": run_id, "status": "queued"}

    @app.get("/api/runs/{run_id}/summary")
    def summary(run_id: str):
        load(run_id)
        path = store.directory(run_id) / "summary.md"
        if not path.exists():
            raise HTTPException(409, "summary is available at a checkpoint or after completion")
        return PlainTextResponse(path.read_text(encoding="utf-8"))

    return app
