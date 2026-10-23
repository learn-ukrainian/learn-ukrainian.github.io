"""Tests for the central JSONL telemetry emitter."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from telemetry import emit as emit_mod


def _use_event_dir(monkeypatch, root: Path) -> Path:
    event_dir = root / "events"

    def event_dir_fn() -> Path:
        event_dir.mkdir(parents=True, exist_ok=True)
        return event_dir

    monkeypatch.setattr(emit_mod, "_event_dir", event_dir_fn)
    return event_dir


def _event_lines(root: Path) -> list[dict]:
    files = sorted(root.glob("*.jsonl"))
    assert len(files) <= 1
    if not files:
        return []
    return [
        json.loads(line)
        for line in files[0].read_text(encoding="utf-8").splitlines()
    ]


def test_emit_event_writes_durable_jsonl(tmp_path, monkeypatch):
    event_dir = _use_event_dir(monkeypatch, tmp_path)
    monkeypatch.setenv("LU_RUN_ID", "run-test")
    monkeypatch.setenv("LU_SESSION_ID", "session-test")
    monkeypatch.setenv("LU_TELEMETRY_SOURCE", "pytest")

    assert emit_mod.emit_event("unit", {"ok": True}) is None

    rows = _event_lines(event_dir)
    assert len(rows) == 1
    assert rows[0]["schema_version"] == emit_mod.SCHEMA_VERSION
    assert rows[0]["event_type"] == "unit"
    assert rows[0]["run_id"] == "run-test"
    assert rows[0]["session_id"] == "session-test"
    assert rows[0]["source"] == "pytest"
    assert rows[0]["ok"] is True


def test_emit_event_swallows_serialization_error(tmp_path, monkeypatch):
    event_dir = _use_event_dir(monkeypatch, tmp_path)

    def raise_type_error(*_args, **_kwargs):
        raise TypeError("boom")

    monkeypatch.setattr(emit_mod.json, "dumps", raise_type_error)

    assert emit_mod.emit_event("unit", {"bad": object()}) is None

    assert not list(event_dir.glob("*.jsonl"))


def test_redirect_is_inherited_by_subprocess_and_package_import(tmp_path, monkeypatch):
    event_dir = tmp_path / "child-events"
    monkeypatch.setenv("LU_TELEMETRY_EVENTS_DIR", str(event_dir))
    result = subprocess.run(
        [sys.executable, "-c", "from scripts.telemetry.emit import emit_event; emit_event('child', {'ok': True})"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert [row["event_type"] for row in _event_lines(event_dir)] == ["child"]
