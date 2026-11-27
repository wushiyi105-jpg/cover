"""新功能：年度保单体检与条款原文检索。"""

from __future__ import annotations

from typer.testing import CliRunner

from cover.domain.catalog import claim_templates, exclusions, formulas
from cover.iface.cli import app


def test_catalog_counts() -> None:
    assert len(exclusions()) == 30
    assert len(formulas()) == 8
    assert len(claim_templates()) >= 7


def test_report_cli_writes_markdown(tmp_path) -> None:
    runner = CliRunner()
    db = str(tmp_path / "cover.db")
    assert runner.invoke(app, ["seed", "--db", db]).exit_code == 0
    out = tmp_path / "保单体检.md"
    result = runner.invoke(app, ["report", "--db", db, "--no-llm", "--out", str(out)])
    assert result.exit_code == 0
    body = out.read_text(encoding="utf-8")
    assert "# 家庭保单年度体检" in body
    assert "保障缺口" in body
    assert "续费日历" in body
    assert "理赔材料" in body
    assert "30 条免责条款" in body


def test_terms_returns_original_or_refuses() -> None:
    runner = CliRunner()
    hit = runner.invoke(app, ["terms", "既往症"])
    assert hit.exit_code == 0
    assert "2.1" in hit.output and "合同生效前已患有" in hit.output
    miss = runner.invoke(app, ["terms", "外星人绑架"])
    assert miss.exit_code == 1
    assert "没有找到可引用的原文" in miss.output
