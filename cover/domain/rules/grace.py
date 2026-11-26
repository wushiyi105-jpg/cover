"""宽限期：到期后 60 天内算宽限，过了就失效。"""

from __future__ import annotations

from datetime import date

from ..models import Finding, Policy

GRACE_DAYS = 60
WARN_DAYS = 15
PENALTY_GRACE = 4
PENALTY_LAPSED = 12


def days_overdue(policy: Policy, today: date) -> int:
    return (today - policy.due_on).days


def state(policy: Policy, today: date) -> str:
    d = days_overdue(policy, today)
    if d > GRACE_DAYS:
        return "lapsed"
    if d > 0:
        return "grace"
    if d >= -WARN_DAYS:
        return "due"
    return "ok"


def check(policies: list[Policy], today: date) -> list[Finding]:
    out: list[Finding] = []
    for p in policies:
        s = state(p, today)
        if s == "lapsed":
            out.append(
                Finding(
                    "policy.lapsed",
                    f"{p.kind}（成员 {p.member_id}）逾期 {days_overdue(p, today)} 天，超过 60 天宽限，已失效",
                    PENALTY_LAPSED,
                    str(p.id),
                )
            )
        elif s == "grace":
            out.append(
                Finding(
                    "policy.grace",
                    f"{p.kind}（成员 {p.member_id}）宽限第 {days_overdue(p, today)} 天，还有 {GRACE_DAYS - days_overdue(p, today)} 天",
                    PENALTY_GRACE,
                    str(p.id),
                )
            )
    return out
