"""本地核算：缺口、宽限、理赔材料。"""

from __future__ import annotations

from datetime import date

from .models import Audit, Claim, Finding, Member, Policy
from .rules.claims import check as claims_check
from .rules.grace import check as grace_check
from .rules.grace import state
from .rules.needs import gaps as gap_list


def audit(members: list[Member], policies: list[Policy], claims: list[Claim], today: date) -> Audit:
    a = Audit()
    a.gaps = sorted(gap_list(members, policies), key=lambda g: g.short, reverse=True)
    findings: list[Finding] = []
    for g in a.gaps:
        findings.append(
            Finding("cover.gap", f"{g.member} 的{g.kind}差 {g.short:,.0f} 元", 5, f"{g.member}/{g.kind}")
        )
    findings += grace_check(policies, today)
    findings += claims_check(claims)
    a.findings = findings
    return a


def policy_state(policy: Policy, today: date) -> str:
    return state(policy, today)


def by_member(members: list[Member], policies: list[Policy]) -> dict[str, float]:
    return {
        m.name: round(sum(p.sum_insured for p in policies if p.member_id == m.id), 2) for m in members
    }
