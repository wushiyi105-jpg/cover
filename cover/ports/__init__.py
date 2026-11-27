"""端口：app 实际调用的方法集合，实现见 adapters。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..domain.models import Claim, Member, Policy


@runtime_checkable
class StorePort(Protocol):
    def list_members(self) -> list[Member]: ...

    def list_policies(self) -> list[Policy]: ...

    def list_claims(self) -> list[Claim]: ...


@runtime_checkable
class LLMPort(Protocol):
    def write(self, system: str, facts: str) -> str: ...
