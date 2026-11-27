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
    policies = store.list_policies()
    facts = {
        "members": [m.name for m in store.list_members()],
        "gaps": [{"member": g.member, "kind": g.kind, "short": g.short} for g in a.gaps],
        "policies": [
            {
                "id": p.id,
                "kind": p.kind,
                "clause_no": p.clause_no,
                "clause_text": p.clause_text,
            }
            for p in policies
        ],
    }
    try:
        data = json.loads(llm.write(PROMPT, json.dumps(facts, ensure_ascii=False)))
    except Exception:  # noqa: BLE001
        return "", []
    if "summary" not in data:
        text = str(data.get("text", ""))
        notes = [f.message for f in check(text, policies)]
        return text, notes
    by_id = {p.id: p for p in policies}
    summary = str(data.get("summary", "")).strip()
    if summary and check(summary, policies):
        summary = ""
        notes = ["摘要提到条款但没有引用原文，已省略"]
    else:
        notes = []
    kept: list[str] = []
    for item in list(data.get("items", []))[:3]:
        try:
            policy = by_id[int(item.get("policy_id", 0))]
        except (KeyError, TypeError, ValueError):
            notes.append("模型给了一个不存在的保单号，该条已丢")
            continue
        clause_text = str(item.get("clause_text", ""))
        clause_no = str(item.get("clause_no", ""))
        if clause_text != policy.clause_text or clause_no != policy.clause_no:
            notes.append(f"保单 #{policy.id} 的条款原文对不上，已丢")
            continue
        meaning = str(item.get("meaning", "")).strip()
        if len(meaning) > 40:
            meaning = meaning[:40]
        kept.append(f"- 保单 #{policy.id}｜{policy.clause_no}：{policy.clause_text} → {meaning}")
    body = summary
    if kept:
        body += "\n" + "\n".join(kept)
    return body, notes


def renew_due(store: StorePort, today: date, days: int = 30) -> list[str]:
    out: list[str] = []
    for p in store.list_policies():
        left = (p.due_on - today).days
        if -30 <= left <= days:
            out.append(f"{p.kind}（#{p.id}）{'逾期' if left < 0 else '还有'} {abs(left)} 天")
    return out
