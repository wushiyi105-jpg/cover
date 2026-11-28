"""FastAPI + Jinja2：缺口表、宽限状态、理赔材料。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..adapters.store import SqliteStore
from ..app.run import report
from ..config import Settings
from ..domain.engine import audit, by_member, policy_state
from ..domain.rules.claims import missing

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


def create_app(settings: Settings, store: SqliteStore | None = None) -> FastAPI:
    app = FastAPI(title="Cover", version="1.0.0")
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parents[2] / "static")),
        name="static",
    )
    store = store or SqliteStore(settings.db_path)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        today = date.today()
        a = audit(store.list_members(), store.list_policies(), store.list_claims(), today)
        policies = [(p, policy_state(p, today)) for p in store.list_policies()]
        claims = [(c, missing(c)) for c in store.list_claims()]
        return TEMPLATES.TemplateResponse(
            request, "index.html",
            {"a": a, "policies": policies, "claims": claims, "today": today.isoformat(),
             "by_member": by_member(store.list_members(), store.list_policies())},
        )

    @app.get("/audit.txt", response_class=PlainTextResponse)
    def audit_txt() -> PlainTextResponse:
        return PlainTextResponse(report(store), media_type="text/plain; charset=utf-8")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "policies": len(store.list_policies())}

    return app


def app_factory(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        from ..config import settings as default_settings

        settings = default_settings
    return create_app(settings)

