"""SQLite：members / policies / claims / jobs。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import Date, Float, Integer, String, inspect, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker
from sqlalchemy.orm import Session as OrmSession

from ...domain.models import Claim, Member, Policy
from .base import Base, make_engine, make_session


class MemberRow(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    relation: Mapped[str] = mapped_column(String(20))
    birth_year: Mapped[int] = mapped_column(Integer)
    annual_income: Mapped[float] = mapped_column(Float, default=0.0)


class PolicyRow(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    member_id: Mapped[int] = mapped_column(Integer)
    sum_insured: Mapped[float] = mapped_column(Float)
    premium: Mapped[float] = mapped_column(Float)
    due_on: Mapped[date] = mapped_column(Date)
    clause_no: Mapped[str] = mapped_column(String(30), default="")
    clause_text: Mapped[str] = mapped_column(String(300), default="")


class ClaimRow(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float)
    filed_on: Mapped[date] = mapped_column(Date)
    docs: Mapped[str] = mapped_column(String(200), default="")
    hospital: Mapped[str] = mapped_column(String(60), default="")


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idem_key: Mapped[str] = mapped_column(String(80), unique=True)


class SqliteStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.engine = make_engine(self.path)
        self.session: sessionmaker[OrmSession] = make_session(self.engine)
        self.init_schema()

    def init_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def schema_ok(self) -> bool:
        return {"members", "policies", "claims", "jobs"} <= set(inspect(self.engine).get_table_names())

    def summary(self) -> str:
        return f"{len(self.list_members())} 人、{len(self.list_policies())} 张保单、{len(self.list_claims())} 条理赔"

    def add_member(self, name: str, relation: str, birth_year: int, annual_income: float) -> int:
        if birth_year < 1900 or annual_income < 0:
            raise ValueError("出生年份或收入不合法")
        with self.session() as s:
            row = MemberRow(name=name, relation=relation, birth_year=birth_year, annual_income=annual_income)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_members(self) -> list[Member]:
        with self.session() as s:
            rows = s.scalars(select(MemberRow)).all()
        return [Member(r.id, r.name, r.relation, r.birth_year, float(r.annual_income)) for r in rows]

    def add_policy(self, kind: str, member_id: int, sum_insured: float, premium: float, due_on: date, clause_no: str = "", clause_text: str = "") -> int:
        if kind not in ("寿险", "重疾", "医疗", "意外"):
            raise ValueError(f"没有这个险种：{kind}")
        if sum_insured <= 0:
            raise ValueError("保额要大于 0")
        with self.session() as s:
            row = PolicyRow(kind=kind, member_id=member_id, sum_insured=sum_insured, premium=premium, due_on=due_on, clause_no=clause_no, clause_text=clause_text)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_policies(self) -> list[Policy]:
        with self.session() as s:
            rows = s.scalars(select(PolicyRow)).all()
        return [
            Policy(r.id, r.kind, r.member_id, float(r.sum_insured), float(r.premium), r.due_on, r.clause_no, r.clause_text)
            for r in rows
        ]

    def add_claim(self, policy_id: int, amount: float, filed_on: date, docs: list[str], hospital: str = "") -> int:
        if amount <= 0:
            raise ValueError("理赔金额要大于 0")
        with self.session() as s:
            row = ClaimRow(policy_id=policy_id, amount=amount, filed_on=filed_on, docs="|".join(docs), hospital=hospital)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_claims(self) -> list[Claim]:
        with self.session() as s:
            rows = s.scalars(select(ClaimRow)).all()
        return [
            Claim(r.id, r.policy_id, float(r.amount), r.filed_on, tuple(r.docs.split("|")) if r.docs else (), r.hospital)
            for r in rows
        ]

    def add_job(self, idem_key: str) -> bool:
        with self.session() as s:
            if s.scalars(select(JobRow).where(JobRow.idem_key == idem_key)).first():
                return False
            s.add(JobRow(idem_key=idem_key))
            s.commit()
            return True
