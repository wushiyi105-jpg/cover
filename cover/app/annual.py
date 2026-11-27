"""年度保单体检：一页 Markdown，缺口 + 续费日历 + 理赔材料。"""

from __future__ import annotations

from datetime import date

from ..domain.catalog import claim_templates, docs_for, exclusions, formulas, gap_table
from ..domain.engine import audit, policy_state
from ..ports import StorePort


def _money(x: float) -> str:
    return f"{x:,.0f}"


def _state(raw: str) -> str:
    return {"grace": "宽限期", "due": "30 天内到期", "lapsed": "已失效", "ok": "正常"}.get(raw, raw)


def build_report(store: StorePort, today: date, extra: str = "") -> str:
    members = store.list_members()
    policies = store.list_policies()
    claims = store.list_claims()
    a = audit(members, policies, claims, today)
    gaps = [g for g in gap_table(members, policies) if g["short"] > 0]
    policy_by_id = {p.id: p for p in policies}
    member_by_id = {m.id: m for m in members}

    lines = [
        f"# 家庭保单年度体检 · {today.isoformat()}",
        "",
        f"> {len(members)} 位家庭成员、{len(policies)} 张保单；"
        f"8 类缺口公式合计缺口 **{_money(sum(g['short'] for g in gaps))} 元**。"
        " 条款引用只认保单原文，引不到就不答。",
        "",
        "## 一、保障缺口（只列有缺口的）",
        "",
        "| 成员 | 险种 | 公式 | 已有保额 | 建议保额 | 缺口 |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for g in gaps:
        lines.append(
            f"| {g['member']} | {g['kind']} | {g['formula']} | {_money(g['have'])} | "
            f"{_money(g['need'])} | **{_money(g['short'])}** |"
        )
    if not gaps:
        lines.append("| - | - | - | - | - | 暂无缺口 |")
    lines += [
        "",
        "## 二、续费日历",
        "",
        "| 到期日 | 保单 | 被保人 | 保费 | 状态 |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for p in sorted(policies, key=lambda x: x.due_on):
        member = member_by_id.get(p.member_id)
        lines.append(
            f"| {p.due_on.isoformat()} | #{p.id} {p.kind} | {member.name if member else '-'} | "
            f"{_money(p.premium)} | {_state(policy_state(p, today))} |"
        )
    lines += ["", "## 三、理赔材料（按现有报案）", ""]
    if not claims:
        lines.append("当前没有在途理赔。")
        lines.append("")
    for c in claims:
        policy = policy_by_id.get(c.policy_id)
        kind = policy.kind if policy else "医疗"
        template = docs_for(kind)
        missing_docs = [d for d in template["docs"] if d not in c.docs]
        lines += [
            f"### 报案 #{c.id} · {kind} · {_money(c.amount)} 元",
            "",
            f"- 医院：{c.hospital or '未填'}",
            f"- 必备材料：{'、'.join(template['docs'])}",
            f"- 还缺：{'、'.join(missing_docs) if missing_docs else '材料齐全'}",
            f"- 提醒：{template['note']}",
            "",
        ]
    lines += [
        "## 四、30 条免责条款里最该先看的",
        "",
    ]
    policy_kinds = {p.kind for p in policies}
    relevant = [e for e in exclusions() if policy_kinds & set(e["kinds"])][:5]
    for e in relevant:
        lines.append(f"- **{e['clause_no']} {e['title']}**：{e['text']}")
    if not relevant:
        lines.append("- 还没有保单，先录入后再做条款核对。")
    lines += [
        "",
        "## 五、下一步",
        "",
    ]
    if a.findings:
        for f in a.findings[:4]:
            lines.append(f"- {f.message}")
    expired = [p for p in policies if (p.due_on - today).days < 0]
    if expired:
        lines.append(f"- 有 {len(expired)} 张保单已过续费日，先确认宽限期是否还在。")
    else:
        lines.append("- 续费日历里 30 天内到期的保单，提前 7 天缴费，别等宽限期。")
    lines += [f"- 缺口优先补：{gaps[0]['member']} 的 {gaps[0]['kind']}。" if gaps else "- 当前没有硬缺口。"]
    if extra:
        lines += ["", "## 六、条款解读（模型结论已逐条核对原文）", "", extra]
    lines += [
        "",
        "---",
        "",
        f"口径：{len(formulas())} 类缺口公式、{len(exclusions())} 条免责条款、"
        f"{len(claim_templates())} 类理赔材料模板；最终以保单原文与保险公司核定为准。",
        "",
    ]
    return "\n".join(lines)
