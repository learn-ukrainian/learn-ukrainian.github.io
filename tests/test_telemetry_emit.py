"""Tests for the central JSONL telemetry emitter."""

from __future__ import annotations

import json
import socket
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


def test_current_ids_mint_once_and_export(monkeypatch):
    monkeypatch.delenv("LU_RUN_ID", raising=False)
    monkeypatch.delenv("LU_SESSION_ID", raising=False)

    run_id = emit_mod.current_run_id()
    session_id = emit_mod.current_session_id()

    assert run_id.startswith("run_")
    assert session_id.startswith("session_")
    assert emit_mod.current_run_id() == run_id
    assert emit_mod.current_session_id() == session_id
    assert run_id == emit_mod.os.environ["LU_RUN_ID"]
    assert session_id == emit_mod.os.environ["LU_SESSION_ID"]


def test_emit_event_honors_disabled_env(tmp_path, monkeypatch):
    event_dir = _use_event_dir(monkeypatch, tmp_path)
    monkeypatch.setenv("LU_TELEMETRY_DISABLED", "1")

    assert emit_mod.emit_event("unit", {"ok": True}) is None

    assert not list(event_dir.glob("*.jsonl"))


def test_emit_event_swallows_serialization_error(tmp_path, monkeypatch):
    event_dir = _use_event_dir(monkeypatch, tmp_path)

    def raise_type_error(*_args, **_kwargs):
        raise TypeError("boom")

    monkeypatch.setattr(emit_mod.json, "dumps", raise_type_error)

    assert emit_mod.emit_event("unit", {"bad": object()}) is None

    assert not list(event_dir.glob("*.jsonl"))


def test_emit_event_recursion_guard_writes_only_outer_event(tmp_path, monkeypatch):
    event_dir = _use_event_dir(monkeypatch, tmp_path)
    real_write_line = emit_mod._write_line

    def recursive_write(path: Path, line: bytes) -> None:
        emit_mod.emit_event("nested", {"ok": False})
        real_write_line(path, line)

    monkeypatch.setattr(emit_mod, "_write_line", recursive_write)

    assert emit_mod.emit_event("outer", {"ok": True}) is None

    rows = _event_lines(event_dir)
    assert [row["event_type"] for row in rows] == ["outer"]


def test_emit_event_hot_path_makes_no_network_call(tmp_path, monkeypatch):
    event_dir = _use_event_dir(monkeypatch, tmp_path)

    def fail_socket(*_args, **_kwargs):
        raise AssertionError("telemetry emit must not open sockets")

    monkeypatch.setattr(socket, "socket", fail_socket)

    assert emit_mod.emit_event("unit", {"ok": True}) is None
    assert len(_event_lines(event_dir)) == 1
