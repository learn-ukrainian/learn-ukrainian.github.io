"""Exercise the real shell hook without an AGY session or provider call."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import inbox_pending
from scripts.agent_runtime import agy_hook_config
from tests.test_inbox_pending import BODY_MARKER, MESSAGE_ID, add_authority, add_legacy

pytest_plugins = ("tests.test_inbox_pending",)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agy_hooks/pending_orders_inject.sh"


def run_hook(payload="{}", *, env=None, cwd=ROOT):
    proc = subprocess.run(
        ["sh", str(SCRIPT)], input=payload, text=True, capture_output=True, cwd=cwd, env=env, timeout=20
    )
    assert proc.returncode == 0
    assert proc.stderr == ""
    assert BODY_MARKER not in proc.stdout
    result = json.loads(proc.stdout)
    if result:
        line = result["injectSteps"][0]["ephemeralMessage"]
        assert len(line) <= 200
        assert "\n" not in line
    return result


@pytest.mark.parametrize(
    "state",
    [
        "legacy-unread",
        "legacy-acknowledged",
        "legacy-consumed",
        "authority-queued",
        "authority-running",
        "authority-consumed",
        "authority-expired",
        "replayed",
    ],
)
@pytest.mark.parametrize("recipient", ["gemini-infra", "gemini", "unknown"])
@pytest.mark.parametrize(
    "failure", ["none", "garbage-stdin", "missing-store", "locked-store", "unreadable-store", "missing-slot"]
)
def test_denominator_matrix(stores, state, recipient, failure, monkeypatch):
    if state.startswith("legacy") or state == "replayed":
        add_legacy(
            stores[0], acknowledged=int(state == "legacy-acknowledged"), consumed=int(state == "legacy-consumed")
        )
    else:
        add_authority(
            stores[1],
            state="running"
            if state in {"authority-running", "authority-consumed"}
            else "expired"
            if state == "authority-expired"
            else "queued",
            consumed=state == "authority-consumed",
        )
    # A different seat always has unread mail; the hook must not query it.
    add_legacy(stores[0], recipient="claude", identifier=77)
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", recipient)
    payload = "{}"
    lock = None
    if failure == "garbage-stdin":
        payload = BODY_MARKER
    elif failure == "missing-store":
        stores[0].unlink()
    elif failure == "locked-store":
        lock = sqlite3.connect(stores[0])
        lock.execute("BEGIN EXCLUSIVE")
    elif failure == "unreadable-store":
        stores[0].chmod(0)
    elif failure == "missing-slot":
        monkeypatch.delenv("SESSION_HANDOFF_AGENT")
    try:
        result = run_hook(payload)
        if failure != "none" or recipient != "gemini-infra":
            assert result == {"injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]}
        elif state in {"legacy-acknowledged", "legacy-consumed", "authority-consumed", "authority-expired"}:
            assert result == {}
        else:
            identifier = MESSAGE_ID if state.startswith("authority") else "1"
            assert result == {
                "injectSteps": [
                    {
                        "ephemeralMessage": f"PENDING ORDERS: 1 (ids {identifier}); ai_agent_bridge inbox --for gemini-infra; ack --consumed-by-live-driver"
                    }
                ]
            }
            if state == "replayed":
                assert run_hook() == result
    finally:
        if lock:
            lock.close()
        if failure == "unreadable-store":
            stores[0].chmod(0o600)


def test_next_call_arrival_replay_consumption_and_hash(stores, tmp_path):
    assert run_hook() == {}
    add_legacy(stores[0])
    add_authority(stores[1], state="running")
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in stores}
    files = set(tmp_path.iterdir())
    first = run_hook(cwd=tmp_path)
    assert "PENDING ORDERS: 2" in first["injectSteps"][0]["ephemeralMessage"]
    assert run_hook() == first
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in stores} == before
    assert set(tmp_path.iterdir()) == files
    for path in files - set(stores):
        if path.is_file():
            assert BODY_MARKER.encode() not in path.read_bytes()
    with sqlite3.connect(stores[0]) as conn:
        conn.execute("UPDATE messages SET acknowledged=1")
    with sqlite3.connect(stores[1]) as conn:
        conn.execute("UPDATE authority_deliveries SET state='acknowledged'")
    assert run_hook() == {}


@pytest.mark.parametrize("payload", ["", "[]", "null", "{", '{"value":NaN}', '{"value":Infinity}', "\x00{}", "{} {}"])
def test_invalid_payload_unknown(stores, payload):
    assert run_hook(payload) == {"injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]}


@pytest.mark.parametrize(
    "mode", ["missing", "crash", "nonzero-empty", "invalid-json", "array", "oversized", "nonascii"]
)
def test_interpreter_failure_unknown(stores, tmp_path, monkeypatch, mode):
    interpreter = tmp_path / "synthetic-interpreter"
    if mode != "missing":
        # A deterministic local child, never a provider executable.
        output = {
            "crash": "",
            "nonzero-empty": "{}",
            "invalid-json": BODY_MARKER,
            "array": "[]",
            "oversized": json.dumps({"injectSteps": [{"ephemeralMessage": "PENDING ORDERS: " + "x" * 210}]}),
            "nonascii": json.dumps({"injectSteps": [{"ephemeralMessage": "PENDING ORDERS: \u202e"}]}),
        }[mode]
        interpreter.write_text(
            f"#!{sys.executable}\nimport os, sys\nif sys.argv[1] == '-c':\n os.execv({sys.executable!r}, [{sys.executable!r}, *sys.argv[1:]])\nsys.stdin.read()\nprint({output!r})\nsys.exit({1 if mode in {'crash', 'nonzero-empty'} else 0})\n"
        )
        interpreter.chmod(0o700)
    monkeypatch.setenv("LU_DRIVER_STATE_PYTHON", str(interpreter))
    assert run_hook() == {"injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]}


def test_shared_interpreter_resolution(stores, monkeypatch):
    monkeypatch.delenv("LU_DRIVER_STATE_PYTHON")
    add_legacy(stores[0])
    assert "PENDING ORDERS: 1" in run_hook()["injectSteps"][0]["ephemeralMessage"]


def test_maximum_ids_and_line_budget(stores):
    for identifier in range(1, 9):
        add_legacy(stores[0], identifier=identifier)
    line = run_hook()["injectSteps"][0]["ephemeralMessage"]
    assert "ids 1,2,3,4,5; truncated" in line
    with sqlite3.connect(stores[0]) as conn:
        conn.execute("DELETE FROM messages")
    with sqlite3.connect(stores[1]) as conn:
        for number in range(8):
            conn.execute(
                "INSERT INTO authority_deliveries(delivery_id,message_id,recipient,state,created_at,updated_at) VALUES (?,?,?,'queued','','')",
                (f"delivery-{number}", f"authority-message_{number:032x}", "gemini-infra"),
            )
    line = run_hook()["injectSteps"][0]["ephemeralMessage"]
    assert "PENDING ORDERS: 8" in line
    assert "authority-message_00000000000000000000000000000000" in line
    assert "truncated" in line


def test_overlay_preserves_secret_guard_and_guide_names_hook(tmp_path):
    path = ROOT / "agents_extensions/agy/hooks.json"
    config = json.loads(path.read_text())
    assert config["pending-orders-announce"] == {
        "PreInvocation": [
            {"type": "command", "command": "sh ../scripts/agy_hooks/pending_orders_inject.sh", "timeout": 10}
        ]
    }
    assert config[agy_hook_config.GUARD_NAME] == {
        "PreToolUse": [
            {
                "matcher": "run_command",
                "hooks": [
                    {
                        "type": "command",
                        "command": "../.venv/bin/python ../scripts/agent_runtime/secret_print_hook.py --harness agy",
                        "timeout": 10,
                    }
                ],
            }
        ]
    }
    # Model the established dispatch installer without changing its validation.
    deployed = tmp_path / ".agents/hooks.json"
    deployed.parent.mkdir()
    config[agy_hook_config.GUARD_NAME] = agy_hook_config.guard_registration()
    deployed.write_text(json.dumps(config))
    assert agy_hook_config.check_hook_config((deployed,)).passed
    text = (ROOT / "docs/agent-runtime-guide.md").read_text()
    assert "pending-orders-announce" in text
    assert "`PreInvocation`" in text
    assert "SESSION_HANDOFF_AGENT" in text
