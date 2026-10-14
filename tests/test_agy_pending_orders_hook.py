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
from tests.helpers.agy_inbox_fixtures import (
    BODY_MARKER,
    MESSAGE_ID,
    MONITOR_PROVIDERS,
    add_authority,
    add_legacy,
    run_cli,
    snapshot,
)

pytest_plugins = ("tests.helpers.agy_inbox_fixtures",)

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


@pytest.mark.parametrize("provider", MONITOR_PROVIDERS)
@pytest.mark.parametrize("roster_kind", ["mixed", "dedicated", "empty", "missing"])
@pytest.mark.parametrize("source", ["legacy", "authority", "both"])
def test_monitor_alias_cli_and_hook_policy(stores, roster, monkeypatch, provider, roster_kind, source):
    slot = f"{provider}-monitor"
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", slot)
    if roster_kind == "dedicated":
        roster.write_text(f"assignments:\n  monitor:\n    slots: [{slot}]\n")
    elif roster_kind == "empty":
        roster.write_text("assignments:\n  monitor:\n    slots: []\n")
    elif roster_kind == "missing":
        roster.unlink()
    canonical = slot if roster_kind == "dedicated" else provider
    if source in {"legacy", "both"}:
        add_legacy(stores[0], recipient=canonical)
        # Raw alias rows are not canonical legacy mail; dedicated lanes never
        # read the bare provider, another dedicated lane, or another family.
        add_legacy(stores[0], recipient=provider if canonical == slot else slot, identifier=2)
        add_legacy(stores[0], recipient=f"{provider}-infra", identifier=3)
        add_legacy(stores[0], recipient="claude-devops", identifier=4)
        if provider == "grok" and roster_kind != "dedicated":
            add_legacy(stores[0], recipient="grok-build", identifier=5)
    if source in {"authority", "both"}:
        add_authority(stores[1], recipient=slot)
        add_authority(stores[1], recipient=provider, identifier="authority-message_" + "b" * 32, delivery_id="bare")
        add_authority(
            stores[1], recipient=f"{provider}-infra", identifier="authority-message_" + "c" * 32, delivery_id="other"
        )
    before = snapshot(stores)
    metadata = run_cli(slot)
    result = run_hook()
    assert run_hook() == result
    assert snapshot(stores) == before
    if roster_kind in {"empty", "missing"}:
        assert metadata == {
            "count": 0,
            "ids": [],
            "truncated": False,
            "stores": {"legacy": None, "authority": None},
            "probe": "unknown",
        }
        assert result == {"injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]}
        return
    legacy_count = (2 if provider == "grok" and roster_kind == "mixed" else 1) if source != "authority" else 0
    authority_count = 0 if source == "legacy" else 1
    legacy_ids = ([1, 5] if legacy_count == 2 else [1]) if legacy_count else []
    ids = [*legacy_ids, *([MESSAGE_ID] if authority_count else [])]
    assert metadata == {
        "count": legacy_count + authority_count,
        "ids": ids,
        "truncated": False,
        "stores": {"legacy": legacy_count, "authority": authority_count},
        "probe": "ok",
    }
    if source == "legacy":
        guidance = f"; legacy: ai_agent_bridge inbox --for {canonical}"
    elif source == "authority":
        guidance = "; authority: .venv/bin/python -m scripts.fleet_comms deliveries --help"
    else:
        guidance = f"; legacy: ai_agent_bridge inbox --for {canonical}; authority: .venv/bin/python -m scripts.fleet_comms deliveries --help"
    shown = ",".join(map(str, ids))
    assert result == {"injectSteps": [{"ephemeralMessage": f"PENDING ORDERS: {len(ids)} (ids {shown}){guidance}"}]}
    line = result["injectSteps"][0]["ephemeralMessage"]
    assert "ack" not in line and "claim" not in line and "consume" not in line
    # Durable consumption belongs to the fixture driver, never the hook.
    with sqlite3.connect(stores[0]) as conn:
        conn.execute("UPDATE messages SET consumed_by_live_driver=1")
    with sqlite3.connect(stores[1]) as conn:
        conn.execute("UPDATE authority_deliveries SET state='acknowledged'")
    after_consumption = snapshot(stores)
    assert run_cli(slot) == {
        "count": 0,
        "ids": [],
        "truncated": False,
        "stores": {"legacy": 0, "authority": 0},
        "probe": "ok",
    }
    assert run_hook() == {}
    assert snapshot(stores) == after_consumption


@pytest.mark.parametrize("provider", MONITOR_PROVIDERS)
@pytest.mark.parametrize("store_index", [0, 1])
@pytest.mark.parametrize("failure", ["missing", "locked", "unreadable", "corrupt", "schema"])
def test_alias_store_failure_is_unknown(stores, roster, monkeypatch, provider, store_index, failure):
    slot = f"{provider}-monitor"
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", slot)
    add_legacy(stores[0], recipient=provider)
    add_authority(stores[1], recipient=slot)
    before = {path: path.read_bytes() for path in stores}
    target = stores[store_index]
    lock = None
    if failure == "missing":
        target.unlink()
    elif failure == "locked":
        lock = sqlite3.connect(target)
        lock.execute("BEGIN EXCLUSIVE")
    elif failure == "unreadable":
        target.chmod(0)
    elif failure == "corrupt":
        target.write_bytes(BODY_MARKER.encode())
        before[target] = target.read_bytes()
    else:
        with sqlite3.connect(target) as conn:
            conn.execute("DROP TABLE messages" if store_index == 0 else "DROP TABLE authority_wake_receipts")
        before[target] = target.read_bytes()
    try:
        assert run_cli(slot) == {
            "count": 0,
            "ids": [],
            "truncated": False,
            "stores": {"legacy": None, "authority": None},
            "probe": "unknown",
        }
        assert run_hook() == {"injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]}
        if failure == "missing":
            assert not target.exists()
    finally:
        if lock:
            lock.close()
        if failure == "unreadable":
            target.chmod(0o600)
    assert {path: path.read_bytes() for path in stores if path.exists()} == {
        path: content for path, content in before.items() if path.exists()
    }


@pytest.mark.parametrize("provider", MONITOR_PROVIDERS)
@pytest.mark.parametrize("consumed_by", ["idempotency", "wake"])
def test_alias_only_supervisory_consumption_is_silent(stores, roster, monkeypatch, provider, consumed_by):
    slot = f"{provider}-monitor"
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", slot)
    add_legacy(stores[0], recipient=provider, consumed=1)
    add_authority(
        stores[1],
        recipient=slot,
        state="running",
        consumed=consumed_by == "idempotency",
        wake_consumed=consumed_by == "wake",
    )
    before = snapshot(stores)
    pending = consumed_by == "wake"
    assert run_cli(slot) == {
        "count": 1 if pending else 0,
        "ids": [MESSAGE_ID] if pending else [],
        "truncated": False,
        "stores": {"legacy": 0, "authority": 1 if pending else 0},
        "probe": "ok",
    }
    assert run_hook() == (
        {
            "injectSteps": [
                {
                    "ephemeralMessage": f"PENDING ORDERS: 1 (ids {MESSAGE_ID}); authority: .venv/bin/python -m scripts.fleet_comms deliveries --help"
                }
            ]
        }
        if pending
        else {}
    )
    assert snapshot(stores) == before


@pytest.mark.parametrize("slot", ["gemini", "gemini-no-such-lane", "kimi-monitor", ""])
def test_unknown_or_unavailable_authority_admission(stores, roster, monkeypatch, slot):
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", slot)
    add_legacy(stores[0], recipient="gemini")
    add_authority(stores[1], recipient="gemini-monitor")
    before = snapshot(stores)
    assert run_cli(slot) == {
        "count": 0,
        "ids": [],
        "truncated": False,
        "stores": {"legacy": None, "authority": None},
        "probe": "unknown",
    }
    assert run_hook() == {"injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]}
    assert snapshot(stores) == before


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
            guidance = (
                "; authority: .venv/bin/python -m scripts.fleet_comms deliveries --help"
                if state.startswith("authority")
                else "; legacy: ai_agent_bridge inbox --for gemini-infra"
            )
            assert result == {"injectSteps": [{"ephemeralMessage": f"PENDING ORDERS: 1 (ids {identifier}){guidance}"}]}
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
