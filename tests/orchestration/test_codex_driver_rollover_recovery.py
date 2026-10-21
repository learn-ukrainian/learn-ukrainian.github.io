"""Synthetic launcher continuity cases for Refs #10916."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.hooks import session_start_gate as gate
from scripts.orchestration import thread_handoff as th
from tests.orchestration.test_thread_handoff import sample_snapshot

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(params=["codex-infra", "codex-devops"])
def packet(tmp_path, monkeypatch, capsys, request):
    agent = request.param
    monkeypatch.setattr(th, "gather_snapshot", lambda root, _url: sample_snapshot(root))
    monkeypatch.setattr(th, "gather_git_state", lambda root: sample_snapshot(root)["git"])
    for name in ("LEARN_UKRAINIAN_CLAUDEX_RUN_ID", "LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(th, "utc_now", lambda: datetime(2026, 1, 2, tzinfo=UTC))
    handoff = Path("docs/session-state/lane-handoff.md")
    monkeypatch.setattr(th, "default_handoff_path", lambda _agent: handoff)
    assert th.main([
        "--repo-root", str(tmp_path), "prepare", "--agent", agent,
        "--active-thread-id", "synthetic-predecessor", "--harness", "codex-cli",
        "--stream-epic", "1234",
    ]) == 0
    output = json.loads(capsys.readouterr().out)
    lease = tmp_path / output["state_file"]
    state = th.load_state(lease)
    return SimpleNamespace(root=tmp_path, agent=agent, handoff=tmp_path / handoff, lease=lease, state=state)


def _launcher_detection(packet):
    # A fixture interpreter wrapper exercises the real shell parser and real
    # detector without installing an environment in the dispatch checkout.
    python = packet.root / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n")
    python.chmod(0o755)
    script = packet.root / "scripts/orchestration/thread_handoff.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(REPO)!r})\n"
        "from scripts.orchestration.thread_handoff import main\n"
        "raise SystemExit(main())\n"
    )
    # The real detector uses this agent-specific canonical role handoff path.
    canonical_handoff = packet.root / f"docs/session-state/current.{packet.agent}.md"
    if canonical_handoff != packet.handoff and packet.handoff.is_file():
        canonical_handoff.parent.mkdir(parents=True, exist_ok=True)
        canonical_handoff.write_bytes(packet.handoff.read_bytes())
        stamp = packet.handoff.stat().st_mtime
        os.utime(canonical_handoff, (stamp, stamp))
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["SESSION_STREAM_ID"] = "epic:1234"
    return subprocess.run(
        ["bash", "-c", 'source "$1"; resolve_codex_pending_rollover "$2" "$3"; '
         'rc=$?; printf "BOUND=%s\\n" "${CODEX_LAUNCHER_ROLLOVER_ID:-}"; exit "$rc"',
         "bash", str(REPO / "scripts/lib/thread_rollover_link.sh"), str(packet.root), packet.agent],
        env=env, capture_output=True, text=True, check=False, timeout=15,
    )


def _handoff_at(packet, delta):
    packet.handoff.parent.mkdir(parents=True, exist_ok=True)
    packet.handoff.write_text("Durable lane handoff\n")
    prepared = th.parse_iso_datetime(packet.state["replacement"]["prepared_at"])
    stamp = (prepared + delta).timestamp()
    os.utime(packet.handoff, (stamp, stamp))


def test_pending_packet_older_than_lane_handoff_is_not_bound(packet, capsys):
    _handoff_at(packet, timedelta(hours=1))
    before = packet.lease.read_bytes()
    assert th.main(["--repo-root", str(packet.root), "detect", "--agent", packet.agent]) == 0
    detected = json.loads(capsys.readouterr().out)
    assert detected["status"] == "none"
    assert detected["skipped_stale"][0]["newer_handoff"] == "docs/session-state/lane-handoff.md"
    launched = _launcher_detection(packet)
    assert launched.returncode == 0, launched.stderr
    assert "BOUND=\n" in launched.stdout
    started = gate.phase_rollover_detect(SimpleNamespace(
        detect=True, repo_root=str(packet.root), agent=packet.agent,
        session_id="synthetic-fresh-thread", stream="epic:1234", task_family="",
    ))
    assert started["status"] == "ok"
    assert "Pending packet predates lane handoff" in started["context"]
    assert packet.lease.read_bytes() == before


@pytest.mark.parametrize("handoff_age", [-1, 0])
def test_live_pending_packet_is_still_bound(packet, capsys, handoff_age):
    _handoff_at(packet, timedelta(hours=handoff_age))
    assert th.main(["--repo-root", str(packet.root), "detect", "--agent", packet.agent]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "pending_start"
    launched = _launcher_detection(packet)
    assert launched.returncode == 0, launched.stderr
    assert f"BOUND={packet.state['replacement']['rollover_id']}\n" in launched.stdout


def test_clean_tracked_handoff_uses_commit_time_instead_of_checkout_mtime(tmp_path):
    handoff = tmp_path / "docs/session-state/current.codex-infra.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text("Durable role handoff\n")
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_AUTHOR_DATE="2026-01-01T00:00:00Z", GIT_COMMITTER_DATE="2026-01-01T00:00:00Z")
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "docs/session-state/current.codex-infra.md"],
        ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Fixture"],
    ):
        subprocess.run(command, cwd=tmp_path, env=env, check=True, capture_output=True, timeout=10)
    assert th.newer_lane_handoff(
        tmp_path, agent="codex-infra", stream="", prepared_at="2026-01-02T00:00:00Z",
    ) is None
    handoff.write_text("New durable handoff\n")
    assert th.newer_lane_handoff(
        tmp_path, agent="codex-infra", stream="", prepared_at="2026-01-02T00:00:00Z",
    ) == "docs/session-state/current.codex-infra.md"



def test_handoff_git_probe_is_bounded_and_ignores_inherited_git_redirect(tmp_path, monkeypatch):
    handoff = tmp_path / "docs/session-state/current.codex-infra.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text("Durable role handoff\n")
    monkeypatch.setenv("GIT_DIR", "unrelated-repository")
    calls = []

    def timed_out(_args, *, cwd, timeout_s, env):
        calls.append((cwd, timeout_s, env))
        return th.CommandResult(returncode=124, stdout="", stderr="synthetic timeout")

    monkeypatch.setattr(th, "run_command", timed_out)
    with pytest.raises(ValueError, match="whether the lane handoff is tracked"):
        th.newer_lane_handoff(tmp_path, agent="codex-infra", stream="", prepared_at="2026-01-02T00:00:00Z")
    assert calls[0][0] == tmp_path
    assert calls[0][1] == 10
    assert "GIT_DIR" not in calls[0][2]
