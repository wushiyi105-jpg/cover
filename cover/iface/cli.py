"""命令行：seed / audit / renew / explain / doctor / serve。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from ..adapters.llm import build_llm
from ..adapters.notify import WebhookNotifier
from ..adapters.store import SqliteStore
from ..app.annual import build_report as annual_report
from ..app.run import PROMPT, explain, renew_due
from ..app.run import report as audit_report
from ..config import Settings
from ..config import settings as default_settings
from ..doctor import main as doctor_main
from ..domain.catalog import query_terms

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


def _notify(settings: Settings, text: str) -> None:
    if not text or not settings.webhook_url:
        return
    ok = WebhookNotifier(settings.webhook_url).send(text)
    console.print(f"[dim]webhook {'ok' if ok else 'failed'}[/]")


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
    console.print(audit_report(store, d))


@app.command()
def report(
    out: Path = typer.Option(None, help="输出 Markdown；不填打印到终端"),
    no_llm: bool = typer.Option(False, "--no-llm"),
    db: Path = typer.Option(None),
) -> None:
    """年度保单体检：缺口、续费日历、理赔材料、条款红线。"""
    s = _settings(db)
    store = _store(s)
    extra = ""
    notes: list[str] = []
    if s.llm_enabled and not no_llm:
        llm = build_llm(s.llm_base_url, s.llm_api_key, s.llm_model, PROMPT)
        extra, notes = explain(store, s, llm)
    text = annual_report(store, date.today(), extra)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        console.print(f"[green]已写出[/] {out}（{len(text.splitlines())} 行）")
    else:
        console.print(text)
    for n in notes:
        console.print(f"  [yellow]{n}[/]")
    if not extra:
        console.print("[dim]本次为本地核算：缺口、续费、材料全部运行时计算。[/]")


@app.command("terms")
def terms_cmd(
    query: str = typer.Argument(..., help="关键词，例如 既往症 / 牙科 / 酒驾"),
    kind: str = typer.Option("", help="限定险种：医疗/重疾/意外/寿险/家财"),
) -> None:
    """查免责条款：只返回能引用原文的条目；查不到就明说。"""
    hits = query_terms(query, kind)
    if not hits:
        console.print("[yellow]没有找到可引用的原文，不能回答这个问题。[/]")
        raise typer.Exit(code=1)
    for row in hits[:8]:
        console.print(f"{row['clause_no']} {row['title']}（{'/'.join(row['kinds'])}）")
        console.print(f"  原文：{row['text']}")


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
    body: list[str] = []
    if text:
        console.print(text)
        body.append(text)
    for n in notes:
        console.print(f"  [yellow]{n}[/]")
        body.append(n)
    if not text:
        line = "模型没开，只看 audit"
        console.print(line)
        body.append(line)
    _notify(s, "\n".join(body))


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
