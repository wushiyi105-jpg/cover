from __future__ import annotations

from datetime import date

from cover.domain.models import Claim, Policy
from cover.domain.rules.claims import check as claims_check
from cover.domain.rules.claims import missing
from cover.domain.rules.grace import check, days_overdue, state


def _p(due: date) -> Policy:
    return Policy(1, "寿险", 1, 1000000, 4000, due, "3.2", "原文")


def test_state_ok_far_out():
    assert state(_p(date(2027, 3, 1)), date(2026, 11, 27)) == "ok"


def test_state_due_within_fifteen_days():
    assert state(_p(date(2026, 12, 6)), date(2026, 11, 27)) == "due"


def test_state_grace_inside_sixty():
    assert state(_p(date(2026, 10, 20)), date(2026, 11, 27)) == "grace"
    assert days_overdue(_p(date(2026, 10, 20)), date(2026, 11, 27)) == 38


def test_state_lapsed_after_sixty():
    assert state(_p(date(2026, 9, 1)), date(2026, 11, 27)) == "lapsed"


def test_grace_finding_penalty():
    findings = check([_p(date(2026, 11, 15))], date(2026, 11, 27))
    assert findings[0].rule_id == "policy.grace"
    assert findings[0].penalty == 4


def test_lapsed_finding_penalty():
    findings = check([_p(date(2026, 9, 1))], date(2026, 11, 27))
    assert findings[0].penalty == 12


def test_missing_docs():
    assert missing(Claim(1, 1, 100, date(2026, 11, 1), ("发票",))) == ["诊断证明", "费用清单"]


def test_duplicate_policy_claim():
    claims = [
        Claim(1, 3, 100, date(2026, 11, 1), ("诊断证明", "发票", "费用清单")),
        Claim(2, 3, 200, date(2026, 11, 2), ("诊断证明", "发票", "费用清单")),
    ]
    findings = claims_check(claims)
    assert [f.rule_id for f in findings] == ["claim.dup"]
