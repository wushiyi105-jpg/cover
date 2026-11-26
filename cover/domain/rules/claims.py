"""理赔：材料缺项、同保单重复索赔。"""

from __future__ import annotations

from ..models import Claim, Finding

REQUIRED = ("诊断证明", "发票", "费用清单")
PENALTY_DOCS = 4
PENALTY_DUP = 6


def missing(claim: Claim) -> list[str]:
    return [d for d in REQUIRED if d not in claim.docs]


def check(claims: list[Claim]) -> list[Finding]:
    out: list[Finding] = []
    for c in claims:
        miss = missing(c)
        if miss:
            out.append(
                Finding("claim.docs", f"理赔 #{c.id} 缺 {'、'.join(miss)}", PENALTY_DOCS, str(c.id))
            )
    seen: dict[int, int] = {}
    for c in claims:
        if c.policy_id in seen:
            out.append(
                Finding(
                    "claim.dup",
                    f"理赔 #{c.id} 与 #{seen[c.policy_id]} 是同一张保单，重复索赔",
                    PENALTY_DUP,
                    str(c.policy_id),
                )
            )
        else:
            seen[c.policy_id] = c.id
    return out
