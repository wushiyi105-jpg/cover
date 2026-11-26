from __future__ import annotations

import pytest

from cover.domain.models import Member
from cover.domain.rules.needs import gaps, need


def test_medical_is_flat():
    assert need(Member(1, "甲", "本人", 1990, 100000), "医疗") == 300000.0


def test_life_is_ten_times_income():
    assert need(Member(1, "甲", "本人", 1990, 120000), "寿险") == 1200000.0


def test_child_no_income_still_needs_medical():
    m = Member(1, "小孩", "子女", 2019, 0)
    assert need(m, "寿险") == 0.0


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        need(Member(1, "甲", "本人", 1990, 100000), "年金")


def test_gap_when_short(store):
    mid = store.add_member("甲", "本人", 1990, 150000)
    store.add_policy("重疾", mid, 200000, 4000, __import__("datetime").date(2027, 1, 1))
    g = [x for x in gaps(store.list_members(), store.list_policies()) if x.kind == "重疾"]
    assert g[0].short == 250000.0


def test_no_gap_when_enough(store):
    mid = store.add_member("甲", "本人", 1990, 100000)
    store.add_policy("重疾", mid, 400000, 4000, __import__("datetime").date(2027, 1, 1))
    assert [x for x in gaps(store.list_members(), store.list_policies()) if x.kind == "重疾"] == []
