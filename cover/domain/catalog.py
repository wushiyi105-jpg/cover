"""30 条常见免责条款、8 类缺口公式、理赔材料模板。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import Member, Policy

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def exclusions() -> list[dict[str, Any]]:
    return json.loads((ROOT / "data" / "exclusions.json").read_text(encoding="utf-8"))["exclusions"]


@lru_cache(maxsize=1)
def formulas() -> list[dict[str, Any]]:
    return json.loads((ROOT / "data" / "gap_formulas.json").read_text(encoding="utf-8"))["formulas"]


@lru_cache(maxsize=1)
def claim_templates() -> list[dict[str, Any]]:
    return json.loads((ROOT / "data" / "claim_docs.json").read_text(encoding="utf-8"))["templates"]


def estimated_need(member: Member, row: dict[str, Any]) -> float:
    if row["basis"] == "income":
        return float(member.annual_income) * float(row["factor"])
    return float(row["default"])


def gap_table(members: list[Member], policies: list[Policy]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    first_adult = next((m for m in members if m.relation != "子女"), members[0] if members else None)
    for member in members:
        for row in formulas():
            kind = row["kind"]
            # 8 类公式是库，不是每人都套 8 条：教育金只算子女，家财只算家庭一份。
            if kind == "教育金" and member.relation != "子女":
                continue
            if kind == "家财" and (first_adult is None or member.id != first_adult.id):
                continue
            if member.relation == "子女" and kind not in {"医疗", "教育金"}:
                continue
            have = sum(
                p.sum_insured for p in policies
                if p.member_id == member.id and p.kind == kind
            )
            need = estimated_need(member, row)
            out.append(
                {
                    "member": member.name,
                    "kind": kind,
                    "formula": row["formula"],
                    "have": have,
                    "need": need,
                    "short": max(0.0, need - have),
                }
            )
    return out


def query_terms(query: str, kind: str = "") -> list[dict[str, Any]]:
    text = query.strip()
    hits: list[dict[str, Any]] = []
    for row in exclusions():
        if kind and kind not in row["kinds"]:
            continue
        haystack = f"{row['title']} {row['text']} {' '.join(row['kinds'])}"
        if text and text not in haystack:
            continue
        hits.append(row)
    return hits


def docs_for(kind: str) -> dict[str, Any]:
    return next(
        (row for row in claim_templates() if row["kind"] == kind),
        {"kind": kind, "docs": ["诊断证明", "发票", "费用清单"], "note": "按保单条款准备基础材料。"},
    )
