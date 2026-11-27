"""真实内存 Store 跑 report：不建 SQLite，mypy 校验 StorePort。"""

from __future__ import annotations

from datetime import date

from cover.app.run import report
from cover.domain.models import Claim, Member, Policy
from cover.ports import StorePort


class InMemoryStore:
    def list_members(self) -> list[Member]:
        return []

    def list_policies(self) -> list[Policy]:
        return []

    def list_claims(self) -> list[Claim]:
        return []


def test_report_with_memory_store() -> None:
    store: StorePort = InMemoryStore()
    out = report(store, date(2026, 1, 5))
    assert "缺口" in out
