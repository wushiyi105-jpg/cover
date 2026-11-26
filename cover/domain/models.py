"""领域对象：成员、保单、理赔、缺口。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# 建议倍数/定额：寿险 10 倍年收入、重疾 3 倍、意外 5 倍；医疗按定额
MEDICAL_FLOOR = 300000.0


@dataclass(frozen=True)
class Member:
    id: int
    name: str
    relation: str
    birth_year: int
    annual_income: float


@dataclass(frozen=True)
class Policy:
    id: int
    kind: str
    member_id: int
    sum_insured: float
    premium: float
    due_on: date
    clause_no: str = ""
    clause_text: str = ""


@dataclass(frozen=True)
class Claim:
    id: int
    policy_id: int
    amount: float
    filed_on: date
    docs: tuple[str, ...] = ()
    hospital: str = ""


@dataclass
class Finding:
    rule_id: str
    message: str
    penalty: int
    target: str = ""


@dataclass
class Gap:
    member: str
    kind: str
    have: float
    need: float

    @property
    def short(self) -> float:
        return max(0.0, self.need - self.have)


@dataclass
class Audit:
    gaps: list[Gap] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def penalty_total(self) -> int:
        return sum(f.penalty for f in self.findings)

    @property
    def total_short(self) -> float:
        return sum(g.short for g in self.gaps)
