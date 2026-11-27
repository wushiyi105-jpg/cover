"""命令行：seed / audit / renew / explain / doctor / serve。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from ..adapters.llm import build_llm
from ..adapters.store import SqliteStore
from ..app.run import PROMPT, explain, renew_due, report
from ..config import Settings
from ..config import settings as default_settings
from ..doctor import main as doctor_main

app = typer.Typer(help="家庭保单：缺口与宽限", no_args_is_help=True)
console = Console()


def _settings(db: Path | None, port: int | None = None) -> Settings:
    s = default_settings.model_copy(deep=True)
    if db:
        s.db_path = db
    if port:
        s.port = port
    return s


def _store(settings: Settings) -> SqliteStore:
    return SqliteStore(settings.db_path)


@app.command()
def seed(db: Path = typer.Option(None)) -> None:
    """写入成员、保单、理赔。"""
    s = _settings(db)
    store = _store(s)
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seed.json").read_text(encoding="utf-8")
    )
    ids = {}
    for m in data["members"]:
        ids[m["name"]] = store.add_member(m["name"], m["relation"], m["birth_year"], m["income"])
    for p in data["policies"]:
        store.add_policy(p["kind"], ids[p["member"]], p["sum_insured"], p["premium"], date.fromisoformat(p["due_on"]), p.get("clause_no", ""), p.get("clause_text", ""))
    for c in data.get("claims", []):
        store.add_claim(c["policy_id"], c["amount"], date.fromisoformat(c["on"]), c.get("docs", []), c.get("hospital", ""))
    console.print(f"已写入 {len(data['members'])} 人、{len(data['policies'])} 张保单、{len(data.get('claims', []))} 条理赔")


@app.command()
def audit(day: str = typer.Option(""), db: Path = typer.Option(None)) -> None:
    """缺口、宽限、材料。"""
    s = _settings(db)
    store = _store(s)
    d = date.fromisoformat(day) if day else date.today()
    console.print(report(store, d))


@app.command()
def renew(day: str = typer.Option(""), db: Path = typer.Option(None)) -> None:
    """30 天内到期或刚过期的保单。"""
    store = _store(_settings(db))
    d = date.fromisoformat(day) if day else date.today()
    for line in renew_due(store, d):
        console.print(line)


@app.command("explain")
def explain_cmd(db: Path = typer.Option(None)) -> None:
    """模型解读（无 key 时不编）。"""
    s = _settings(db)
    llm = build_llm(s.llm_base_url, s.llm_api_key, s.llm_model, PROMPT) if s.llm_enabled else None
    text, notes = explain(_store(s), s, llm)
    if text:
        console.print(text)
    for n in notes:
        console.print(f"  [yellow]{n}[/]")
    if not text:
        console.print("模型没开，只看 audit")




@app.command()
def doctor(db: Path = typer.Option(None)) -> None:
    """四项体检。"""
    raise typer.Exit(code=doctor_main(_settings(db)))


@app.command()
def serve(port: int = typer.Option(None), db: Path = typer.Option(None)) -> None:
    """Web 界面。"""
    import uvicorn

    from .web import create_app

    s = _settings(db, port)
    uvicorn.run(create_app(s), host="127.0.0.1", port=s.port)


if __name__ == "__main__":
    app()
