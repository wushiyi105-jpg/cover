"""用例：缺口核算 → 模型解读条款 → 守卫 → 续保提醒。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ..config import Settings
from ..domain.engine import audit
from ..domain.guard import check
from ..ports import LLMPort, StorePort

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "terms.md").read_text(encoding="utf-8")


def report(store: StorePort, today: date | None = None) -> str:
    a = audit(store.list_members(), store.list_policies(), store.list_claims(), today or date.today())
    lines = [f"缺口 {len(a.gaps)} 项，合计 {a.total_short:,.0f} 元"]
    lines += [f"  {g.member}/{g.kind}：已有 {g.have:,.0f}，建议 {g.need:,.0f}，差 {g.short:,.0f}" for g in a.gaps[:8]]
    lines += [f"  {f.rule_id} -{f.penalty} {f.message}" for f in a.findings]
    return "\n".join(lines)


def explain(
    store: StorePort, settings: Settings, llm: LLMPort | None = None
) -> tuple[str, list[str]]:
    if llm is None:
        return "", []
    a = audit(store.list_members(), store.list_policies(), store.list_claims(), date.today())
    facts = {
        "members": [m.name for m in store.list_members()],
        "gaps": [{"member": g.member, "kind": g.kind, "short": g.short} for g in a.gaps],
        "policies": [{"id": p.id, "kind": p.kind, "clause_no": p.clause_no} for p in store.list_policies()],
    }
    try:
        data = json.loads(llm.write(PROMPT, json.dumps(facts, ensure_ascii=False)))
    except Exception:  # noqa: BLE001
        return "", []
    text = str(data.get("text", ""))
    notes = [f.message for f in check(text, store.list_policies())]
    return text, notes


def renew_due(store: StorePort, today: date, days: int = 30) -> list[str]:
    out: list[str] = []
    for p in store.list_policies():
        left = (p.due_on - today).days
        if -30 <= left <= days:
            out.append(f"{p.kind}（#{p.id}）{'逾期' if left < 0 else '还有'} {abs(left)} 天")
    return out
