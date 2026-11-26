from __future__ import annotations

from datetime import date

from cover.domain.engine import audit, by_member
from cover.domain.guard import check


def _setup(store):
    mid = store.add_member("甲", "本人", 1990, 180000)
    store.add_policy("寿险", mid, 500000, 4000, date(2026, 12, 6), "3.2", "按基本保额给付。")
    return mid


def test_guard_flags_clause_without_text(store):
    _setup(store)
    findings = check("按 3.2 条可以赔", store.list_policies())
    assert findings[0].rule_id == "guard.terms"


def test_guard_accepts_clause_with_text(store):
    _setup(store)
    assert check("按 3.2 条：按基本保额给付。", store.list_policies()) == []


def test_guard_flags_bare_word_clause(store):
    _setup(store)
    assert any(f.target == "no-clause" for f in check("条款里写得很清楚", store.list_policies()))


def test_audit_total_short_and_penalty(store):
    _setup(store)
    a = audit(store.list_members(), store.list_policies(), [], date(2026, 11, 27))
    assert a.total_short > 0
    assert a.penalty_total >= 5


def test_audit_sorted_by_short_desc(store):
    mid = store.add_member("乙", "配偶", 1991, 150000)
    store.add_policy("寿险", mid, 1000000, 3000, date(2027, 1, 1))
    a = audit(store.list_members(), store.list_policies(), [], date(2026, 11, 27))
    shorts = [g.short for g in a.gaps]
    assert shorts == sorted(shorts, reverse=True)


def test_by_member_sums(store):
    _setup(store)
    assert by_member(store.list_members(), store.list_policies())["甲"] == 500000.0
