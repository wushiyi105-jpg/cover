"""建议保额：按收入倍数与医疗定额算，再和已买的比。"""

from __future__ import annotations

from ..models import MEDICAL_FLOOR, Gap, Member, Policy

MULTIPLES = {"寿险": 10.0, "重疾": 3.0, "意外": 5.0}


def need(member: Member, kind: str) -> float:
    if kind == "医疗":
        return MEDICAL_FLOOR
    if kind not in MULTIPLES:
        raise ValueError(f"没有这个险种：{kind}")
    return round(member.annual_income * MULTIPLES[kind], 2)


def gaps(members: list[Member], policies: list[Policy], kinds: list[str] | None = None) -> list[Gap]:
    ks = kinds or ["寿险", "重疾", "医疗", "意外"]
    out: list[Gap] = []
    for m in members:
        for k in ks:
            have = sum(
                p.sum_insured for p in policies if p.member_id == m.id and p.kind == k
            )
            g = Gap(m.name, k, have, need(m, k))
            if g.short > 0:
                out.append(g)
    return out
