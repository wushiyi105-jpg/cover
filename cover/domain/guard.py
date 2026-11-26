"""条款守卫：引用条款必须带条款号，且原文能在保单里找到。"""

from __future__ import annotations

from .models import Finding, Policy

PENALTY = 8


def check(text: str, policies: list[Policy]) -> list[Finding]:
    """模型引用的条款号与原文必须对得上。"""
    findings: list[Finding] = []
    for p in policies:
        if not p.clause_no or not p.clause_text:
            continue
        if p.clause_no in text and p.clause_text not in text:
            findings.append(
                Finding(
                    "guard.terms",
                    f"引了 {p.clause_no} 但原文对不上，删掉这句",
                    PENALTY,
                    p.clause_no,
                )
            )
    if "条款" in text and not any(p.clause_no and p.clause_no in text for p in policies):
        findings.append(Finding("guard.terms", "提到了条款但没给条款号，删掉这句", PENALTY, "no-clause"))
    return findings
