from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from cover.doctor import run_doctor
from cover.iface.cli import app
from cover.iface.web import create_app


def _seed(store):
    mid = store.add_member("甲", "本人", 1990, 180000)
    store.add_policy("寿险", mid, 500000, 4000, date(2026, 12, 6))
    store.add_claim(1, 3000, date(2026, 11, 20), ["发票"])


def test_index(store, settings):
    _seed(store)
    client = TestClient(create_app(settings, store))
    body = client.get("/").text
    assert client.get("/").status_code == 200
    assert "保额缺口" in body


def test_audit_txt(store, settings):
    _seed(store)
    r = TestClient(create_app(settings, store)).get("/audit.txt")
    assert r.status_code == 200
    assert "缺口" in r.text


def test_cli_audit_and_bad_kind(tmp_path):
    runner = CliRunner()
    db = str(tmp_path / "c.db")
    assert runner.invoke(app, ["audit", "--db", db, "--day", "2026-11-27"]).exit_code == 0
    assert runner.invoke(app, ["audit", "--db", db, "--day", "2026-02-30"]).exit_code != 0


def test_doctor_green(settings):
    checks, ok = run_doctor(settings)
    assert ok is True
