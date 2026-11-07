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
from tests.launcher_sandbox import launcher_environment
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
    env = launcher_environment(SESSION_STREAM_ID="epic:1234")
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
    env = launcher_environment()
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


# --- #12567: one rollover namespace per Codex lane, and a DB-first canary ---


def _rollover_fixture(monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda r, _url: sample_snapshot(r))
    monkeypatch.setattr(th, "gather_git_state", lambda r: sample_snapshot(r)["git"])
    for name in (
        "LEARN_UKRAINIAN_CLAUDEX_RUN_ID", "LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION",
        "SESSION_HANDOFF_AGENT", "SESSION_EPIC", "SESSION_STREAM_ID",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(th, "utc_now", lambda: datetime(2026, 11, 2, 20, 23, tzinfo=UTC))
    monkeypatch.setattr(th, "default_handoff_path", lambda _agent: Path("docs/session-state/lane-handoff.md"))


def _prepare(root, capsys, agent, thread):
    assert th.main([
        "--repo-root", str(root), "prepare", "--agent", agent, "--active-thread-id", thread,
        "--harness", "codex-cli", "--stream-epic", "1001",
    ]) == 0
    return json.loads(capsys.readouterr().out)


def _launcher_prelease(root, slot, stream):
    """The launcher's pre-lease call: explicit stream, no SESSION_STREAM_ID yet."""
    python = root / ".venv/bin/python"
    python.parent.mkdir(parents=True, exist_ok=True)
    python.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n")
    python.chmod(0o755)
    script = root / "scripts/orchestration/thread_handoff.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(REPO)!r})\n"
        "from scripts.orchestration.thread_handoff import main\n"
        "raise SystemExit(main())\n"
    )
    env = launcher_environment()
    return subprocess.run(
        ["bash", "-c", 'source "$1"; resolve_codex_pending_rollover "$2" "$3" "$4"; rc=$?; '
         'printf "BOUND=%s %s %s\\n" "${CODEX_LAUNCHER_ROLLOVER_AGENT:-}" '
         '"${CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID:-}" "${CODEX_LAUNCHER_ROLLOVER_ID:-}"; exit "$rc"',
         "bash", str(REPO / "scripts/lib/thread_rollover_link.sh"), str(root), slot, stream],
        env=env, capture_output=True, text=True, check=False, timeout=60,
    )


def test_bare_codex_prepare_inside_a_lane_uses_the_launcher_slot(tmp_path, monkeypatch, capsys):
    _rollover_fixture(monkeypatch)
    legacy = _prepare(tmp_path, capsys, "codex", "legacy-thread")
    assert legacy["state_file"].startswith(".agent/thread-rollovers/codex/")

    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "codex-core")
    lane = _prepare(tmp_path, capsys, "codex", "lane-thread")
    assert lane["state_file"].startswith(".agent/thread-rollovers/codex-core/")

    # A lineage that exists only under the bare namespace stays addressable there.
    legacy_lineage = th.load_state(tmp_path / legacy["state_file"])["lineage_id"]
    lane_lineage = th.load_state(tmp_path / lane["state_file"])["lineage_id"]
    assert th.resolve_rollover_agent("codex", state_root=tmp_path, lineage_id=legacy_lineage) == "codex"
    assert th.resolve_rollover_agent("codex", state_root=tmp_path, lineage_id=lane_lineage) == "codex-core"
    assert th.resolve_rollover_agent("codex-atlas", state_root=tmp_path) == "codex-atlas"
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "claude-core")
    assert th.resolve_rollover_agent("codex", state_root=tmp_path) == "codex"


def test_2026_11_02_relaunch_resumes_the_lane_packet_and_mints_ten_anchors(tmp_path, monkeypatch, capsys):
    """Packet under the lane slot, older bare-namespace packets, empty markdown, DB handoff present."""
    from scripts.session_canary import codex_lane, grok_lane, handoff_select

    _rollover_fixture(monkeypatch)
    for index in range(5):  # The lane's earlier, never-resumed packets under `codex`.
        earlier = datetime(2026, 10, 31, 21, tzinfo=UTC) + timedelta(hours=7 * index)
        monkeypatch.setattr(th, "utc_now", lambda earlier=earlier: earlier)
        _prepare(tmp_path, capsys, "codex", f"earlier-predecessor-{index}")
    monkeypatch.setattr(th, "utc_now", lambda: datetime(2026, 11, 2, 20, 23, tzinfo=UTC))
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "codex-core")  # Exported by the launcher.
    prepared = _prepare(tmp_path, capsys, "codex", "ninth-compaction-predecessor")
    lease = th.load_state(tmp_path / prepared["state_file"])
    rollover_id = lease["replacement"]["rollover_id"]
    monkeypatch.delenv("SESSION_HANDOFF_AGENT")

    launched = _launcher_prelease(tmp_path, "codex-core", "epic:1001")
    assert launched.returncode == 0, launched.stderr
    assert f"BOUND=codex-core {lease['lineage_id']} {rollover_id}\n" in launched.stdout
    assert "left unchanged (never deleted): 5 bare provider namespace" in launched.stdout
    assert len(list((tmp_path / ".agent/thread-rollovers/codex").glob("*/lease.json"))) == 5

    # SessionStart binds and resumes exactly the exported packet.
    common = ["--agent", "codex-core", "--lineage-id", lease["lineage_id"], "--rollover-id", rollover_id]
    assert th.main(["--repo-root", str(tmp_path), "bind-replacement", *common,
                    "--replacement-task-id", "fresh-codex-task", "--evidence", "launcher binding"]) == 0
    assert th.main(["--repo-root", str(tmp_path), "resume", *common,
                    "--replacement-thread-id", "fresh-codex-task"]) == 0
    capsys.readouterr()
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex-core", "--stream", "epic:1001",
                    "--current-thread-id", "fresh-codex-task"]) == 0
    resumed = json.loads(capsys.readouterr().out)
    assert (resumed["status"], resumed["rollover_id"], resumed["resumed_thread_id"]) == (
        "resumed", rollover_id, "fresh-codex-task",
    )

    # The canary: stale markdown sections, the lane's newest DB handoff_note.
    epic = tmp_path / ".claude/curriculum-upgrade-epic"
    epic.mkdir(parents=True)
    (epic / "INTERIM-DRIVER-HANDOFF.md").write_text("# Interim\n\n## Next drive order\n\n## Hands-off\n")
    stream = [{"type": "binding_order", "body": f"Binding order {i} stays in force."} for i in range(1, 4)] + [
        {"type": "negative_constraint", "body": f"Negative constraint {i} stays in force."} for i in range(1, 3)
    ]
    note = {
        "id": "C-4170", "kind": "handoff_note", "lane": "curriculum-upgrade", "owner": "codex-core",
        "status": "open", "created_utc": "2026-11-02 20:23:39.965370+00:00",
        "statement": "FINAL FULL-CONTENT DB HANDOFF.\n1. Render then check first.\n"
                     "2. Settle the held review.\n3. Dispatch the next ready module.\n",
        "done_when": "The successor verifies the exact lineage and rollover.",
        "source_ref": "message_663911947591427db15cc10b3d612fe5",
    }
    reads = []
    monkeypatch.setattr(grok_lane, "_load_stream_entries", lambda *_a, **_k: list(stream))
    monkeypatch.setattr(grok_lane.subprocess, "run", lambda command, **_k: subprocess.CompletedProcess(command, 0, "", ""))
    monkeypatch.setattr(handoff_select, "_driver_state_cli", lambda: "lu-driver-state")
    monkeypatch.setattr(handoff_select, "codex_lane_slot", lambda epic_name: "codex-core")
    monkeypatch.setattr(handoff_select, "fetch_newest_handoff_note", lambda lane, owner: reads.append((lane, owner)))
    mint = ["--repo", str(tmp_path), "mint", "--epic", "curriculum-upgrade", "--stream", "epic:1001"]
    assert codex_lane.main(mint) == 1
    assert "could only derive 7/10 durable anchors" in capsys.readouterr().err

    monkeypatch.setattr(handoff_select, "fetch_newest_handoff_note", lambda lane, owner: reads.append((lane, owner)) or note)
    assert codex_lane.main(mint) == 0
    assert reads == [("curriculum-upgrade", "codex-core")] * 2
    facts = json.loads((epic / "canary/facts.json").read_text())
    assert len(facts) == 10
    assert any("C-4170" in fact["a"] for fact in facts)


def test_a_newer_bare_namespace_packet_still_competes_with_the_lane_packet(tmp_path, monkeypatch, capsys):
    _rollover_fixture(monkeypatch)
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "codex-core")
    _prepare(tmp_path, capsys, "codex", "lane-predecessor")
    monkeypatch.delenv("SESSION_HANDOFF_AGENT")
    monkeypatch.setattr(th, "utc_now", lambda: datetime(2026, 11, 2, 21, 0, tzinfo=UTC))
    _prepare(tmp_path, capsys, "codex", "later-bare-predecessor")

    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex-core", "--stream", "epic:1001"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "ambiguous"


def test_a_claude_slot_keeps_its_ambiguity_refusal(tmp_path, monkeypatch, capsys):
    """Review F1: only Codex lanes let their own packet win over the bare namespace."""
    _rollover_fixture(monkeypatch)
    monkeypatch.setattr(th, "utc_now", lambda: datetime(2026, 11, 1, 9, tzinfo=UTC))
    _prepare(tmp_path, capsys, "claude", "older-bare-predecessor")
    monkeypatch.setattr(th, "utc_now", lambda: datetime(2026, 11, 2, 9, tzinfo=UTC))
    _prepare(tmp_path, capsys, "claude-core", "lane-predecessor")

    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "claude-core", "--stream", "epic:1001"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "ambiguous"


@pytest.mark.parametrize(
    ("argv", "agent"),
    [
        (["prepare", "--agent", "codex"], "codex-core"),
        (["prepare", "--agent", "codex", "--state-file", ".agent/thread-rollovers/codex/lineage-x/lease.json"], "codex"),
        (["import-bundle", "--agent", "codex", "--file", "legacy.tgz"], "codex"),
        (["export-bundle", "--agent", "codex"], "codex"),
        (["claim-thread-lease", "--agent", "codex", "--current-thread-id", "t"], "codex"),
    ],
)
def test_explicit_packet_selectors_keep_their_namespace(tmp_path, monkeypatch, argv, agent):
    """Review F2: an explicit state file or bundle keeps the namespace it names."""
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "codex-core")
    args = th.build_parser().parse_args(["--repo-root", str(tmp_path), *argv])
    th.apply_lane_slot(args)
    assert args.agent == agent
