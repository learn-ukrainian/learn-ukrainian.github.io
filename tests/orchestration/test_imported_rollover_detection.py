"""Launcher detection after a cross-host pending bundle import (Refs #10916)."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from agents_extensions.shared.session_streams.inventory import stream_anchor_id
from scripts.orchestration import thread_handoff as th
from tests.orchestration.test_codex_driver_rollover_recovery import _launcher_detection
from tests.orchestration.test_thread_handoff import sample_snapshot
from tests.test_rollover_bundles import _export_args, _import_args

AGENT = "codex-infra"
HANDOFF = ".claude/harness-epic/CLAUDE-DRIVER-HANDOFF.md"


@pytest.mark.parametrize("case", [
    "live", "newer_other_handoff", "missing_receipt", "legacy_receipt",
    "malformed_receipt", "wrong_agent", "wrong_lineage_id", "wrong_rollover_id",
    "wrong_stream_id", "wrong_prepared_at", "edited_handoff", "touched_handoff",
])
def test_imported_pending_packet_launcher_binding(tmp_path, monkeypatch, capsys, case):
    source = tmp_path / "source"
    target = tmp_path / "target"
    for root in (source, target):
        config = root / "scripts/config/issue_streams.yaml"
        config.parent.mkdir(parents=True)
        config.write_text(
            "schema_version: 1\nstreams:\n  infra-harness:\n"
            "    title: Synthetic infrastructure\n    epics: [1234]\n"
        )
    stream = stream_anchor_id("infra-harness", source)
    monkeypatch.setattr(th, "gather_snapshot", lambda root, _url: sample_snapshot(root))
    monkeypatch.setattr(th, "gather_git_state", lambda root: sample_snapshot(root)["git"])
    monkeypatch.setattr(th, "utc_now", lambda: datetime(2026, 1, 2, tzinfo=UTC))
    for name in ("LEARN_UKRAINIAN_CLAUDEX_RUN_ID", "LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION"):
        monkeypatch.delenv(name, raising=False)
    assert th.main([
        "--repo-root", str(source), "prepare", "--agent", AGENT,
        "--active-thread-id", "synthetic-predecessor", "--harness", "codex-cli",
        "--stream-epic", "1234",
    ]) == 0
    prepared = json.loads(capsys.readouterr().out)
    state = th.load_state(source / prepared["state_file"])
    handoff = source / HANDOFF
    handoff.parent.mkdir(parents=True)
    handoff.write_text("The pending packet's own lane handoff.\n")
    bundle = tmp_path / "pending.tgz"
    assert th.cmd_export_bundle(_export_args(source, state, bundle, stream=stream)) == 0
    capsys.readouterr()
    assert th.cmd_import_bundle(_import_args(target, bundle, agent=AGENT, stream=stream)) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "installed"
    installed = target / HANDOFF
    assert installed.stat().st_mtime > th.parse_iso_datetime(state["replacement"]["prepared_at"]).timestamp()
    receipt_path = target / f".agent/thread-rollovers/{AGENT}/_bundle-receipts/{state['lineage_id']}.json"
    receipt = json.loads(receipt_path.read_text())
    if case == "missing_receipt":
        receipt_path.unlink()
    elif case == "legacy_receipt":
        receipt_path.write_text(json.dumps({"schema": "rollover-bundle-receipt.v1", "upload_seq": 0}))
    elif case == "malformed_receipt":
        receipt_path.write_text("[]")
    elif case.startswith("wrong_"):
        receipt[case.removeprefix("wrong_")] = "different-packet"
        receipt_path.write_text(json.dumps(receipt))
    elif case == "newer_other_handoff":
        other = target / "docs/session-state/current.codex-infra.md"
        other.parent.mkdir(parents=True, exist_ok=True)
        other.write_bytes(installed.read_bytes())
    elif case == "edited_handoff":
        installed.write_text("A later same-host handoff.\n")
    elif case == "touched_handoff":
        stamp = installed.stat().st_mtime + 10
        os.utime(installed, (stamp, stamp))

    state_dir = target / ".agent/thread-rollovers"
    before = {p.relative_to(target): p.read_bytes() for p in state_dir.rglob("*") if p.is_file()}
    assert th.main([
        "--repo-root", str(target), "detect", "--agent", AGENT, "--stream", stream,
    ]) == 0
    detected = json.loads(capsys.readouterr().out)
    packet = SimpleNamespace(root=target, agent=AGENT, handoff=target / "absent-handoff.md")
    launched = _launcher_detection(packet)
    assert launched.returncode == 0, launched.stderr
    if case == "live":
        assert detected["status"] == "pending_start"
        assert detected["rollover_id"] == state["replacement"]["rollover_id"]
        assert f"BOUND={state['replacement']['rollover_id']}\n" in launched.stdout
    else:
        assert detected["status"] == "none"
        expected = "docs/session-state/current.codex-infra.md" if case == "newer_other_handoff" else HANDOFF
        assert detected["skipped_stale"][0]["newer_handoff"] == expected
        assert "BOUND=\n" in launched.stdout
    assert {p.relative_to(target): p.read_bytes() for p in state_dir.rglob("*") if p.is_file()} == before
