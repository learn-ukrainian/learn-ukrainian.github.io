"""Context guard behavior against a fake tmux (#10814)."""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.ops import context_guard as cg
from scripts.ops.driver_lanes import PANE_SCRIPT, load_registry
from tests.ops._fake_tmux import BOOT, FakePane, FakeTmux

REPO = Path(__file__).resolve().parents[2]
START = dt.datetime(2026, 10, 16, 12, 0, tzinfo=dt.UTC)
ECHO = (
    "> HANDOFF NOW (CTO automated, 2026-10-16T12:00:00Z): your context is 70%. Finish the current step only, "
    "post 'HANDOFF-DONE infra .claude/infra-epic/DRIVER-STATE.md' to Fleet Comms recipient epics, then stop."
)


def claude_text(pct: int, *lines: str, busy: bool = False) -> str:
    status = "✻ Thinking… (esc to interrupt)" if busy else ">"
    return "\n".join([*lines, status, f"  ctx: {pct * 10}K/1000K ({pct}%)"])


def codex_text(pct: int, *lines: str, ready: bool = True) -> str:
    return "\n".join([*lines, "Ready" if ready else "Working (3s)", f"Context {pct}% used"])


@dataclass
class Pane(FakePane):
    pane_start: str = BOOT  # ps lstart of the pane's own shell


@dataclass
class ShellTmux(FakeTmux):
    """The fake with each pane's own shell in the process table, as ``ps`` lists it."""

    def _ps_rows(self, *, with_start: bool) -> list[str]:
        rows = super()._ps_rows(with_start=with_start)
        shells = {pane.pane_pid: getattr(pane, "pane_start", BOOT) for pane in self.sessions.values()}
        shell_rows = [f"{pid} 1 {start} bash" if with_start else f"{pid} 1 bash" for pid, start in shells.items()]
        return rows[:1] + shell_rows + rows[1:]


class Harness:
    def __init__(self, tmp_path: Path, **panes: FakePane) -> None:
        self.fake = ShellTmux(sessions=dict(panes), now=START.timestamp())
        self.moment = START
        self.logs: list[str] = []
        self.sent: list[tuple[str, str]] = []
        self.posted: dict[str, str] = {}  # sender -> created_at of a HANDOFF-DONE post
        self.state: dict = {}
        self.guard = cg.Guard(
            registry=load_registry(),
            repo_root=tmp_path / "repo",
            tmux=cg.Tmux(run=self.fake.run, sleep=lambda _s: None, clock=lambda: self.moment.timestamp()),
            log=self.logs.append,
            send=lambda recipient, body, key: self.sent.append((recipient, body)),
            handoff_posted=lambda sender, since: sender in self.posted and self.posted[sender] >= since,
            now=lambda: self.moment,
        )

    def tick(self, *only: str) -> None:
        self.guard.run(self.state, list(only))

    def advance(self, minutes: float) -> None:
        self.moment += dt.timedelta(minutes=minutes)

    def pane(self, session: str) -> FakePane:
        return self.fake.sessions[session]


def claude_pane(pct: int, *lines: str, busy: bool = False) -> Pane:
    return Pane(text=claude_text(pct, *lines, busy=busy), agent="claude")


def codex_pane(pct: int, *lines: str, ready: bool = True) -> Pane:
    return Pane(text=codex_text(pct, *lines, ready=ready), agent="codex")


# ---- lane resolution ------------------------------------------------------------
def test_every_lane_is_resolved_by_session_name_never_by_pane_id(tmp_path: Path) -> None:
    panes = {lane.session: claude_pane(10) for lane in load_registry().lanes}
    h = Harness(tmp_path, **panes)
    h.tick()
    sessions = {lane.session for lane in load_registry().lanes}
    assert {t.strip("=").split(":")[0] for t in h.fake.targets()} == sessions
    assert all(t.startswith("=") and "%" not in t for t in h.fake.targets())
    for path in ("scripts/config/driver_lanes.json", "scripts/ops/context_guard.py", "scripts/ops/lane_relaunch.py"):
        text = (REPO / path).read_text(encoding="utf-8")
        assert re.search(r"%\d", text) is None, path
        assert '"pane"' not in text, path


def test_missing_session_is_logged_and_skipped(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    h.tick("infra-muse")
    assert h.logs == ["infra watch: tmux session infra-muse missing"]
    assert h.fake.typed() == []


# ---- Claude threshold -------------------------------------------------------------
def test_claude_lanes_share_the_70_percent_threshold(tmp_path: Path) -> None:
    assert load_registry().settings["claude_handoff_pct"] == 70
    h = Harness(tmp_path, **{"infra-muse": claude_pane(69), "devops-muse": claude_pane(69), "cto": claude_pane(69)})
    h.tick()
    assert h.fake.typed() == []
    for session in ("infra-muse", "devops-muse", "cto"):
        h.pane(session).text = claude_text(70)
    h.tick()
    typed = {s: h.fake.typed(s) for s in ("infra-muse", "devops-muse", "cto")}
    assert all(len(v) == 1 and v[0].startswith("HANDOFF NOW") for v in typed.values()), typed
    assert {h.state[s]["phase"] for s in typed} == {"handoff"}
    assert len(h.sent) == 3


# ---- HANDOFF-DONE matching ---------------------------------------------------------
@pytest.mark.parametrize(
    ("text", "count"),
    [
        (ECHO, 0),
        ("  'HANDOFF-DONE infra .claude/infra-epic/DRIVER-STATE.md' to Fleet Comms", 0),
        ("Handoff written; HANDOFF-DONE infra is next", 0),
        ("⏺ HANDOFF-DONE infra .claude/infra-epic/DRIVER-STATE.md", 1),
        ("• HANDOFF-DONE harness .claude/monitor-epic/DRIVER-STATE.md", 1),
        ("HANDOFF-DONE 0a1b2c3d .claude/epics-epic/DRIVER-STATE.md", 1),
        ("HANDOFF-DONEX", 0),
    ],
)
def test_handoff_done_counts_only_standalone_response_lines(text: str, count: int) -> None:
    assert cg.done_lines(text) == count


def test_prompt_echo_does_not_end_the_session(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"infra-muse": claude_pane(70)})
    h.tick()
    h.pane("infra-muse").text = claude_text(71, ECHO)
    h.advance(5)
    h.tick()
    assert "/exit" not in h.fake.typed("infra-muse")
    h.pane("infra-muse").text = claude_text(72, ECHO, "⏺ HANDOFF-DONE infra .claude/infra-epic/DRIVER-STATE.md")
    h.advance(5)
    h.tick()
    assert h.fake.typed("infra-muse")[-1] == "/exit"


def test_handoff_done_in_watch_phase_starts_the_exit_without_waiting_for_the_threshold(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"cto": claude_pane(65)})
    h.tick("cto")
    h.pane("cto").text = claude_text(66, "⏺ HANDOFF-DONE 0a1b2c3d .claude/epics-epic/DRIVER-STATE.md")
    h.advance(5)
    h.tick("cto")
    assert h.state["cto"]["phase"] == "handoff"
    assert h.state["cto"]["done_seen"] is True
    h.advance(5)
    h.tick("cto")
    assert h.fake.typed("cto") == ["/exit"]  # no HANDOFF NOW: the lane had already handed off


def test_handoff_done_posted_to_fleet_in_watch_phase_is_honoured(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"harness": codex_pane(40)})
    h.tick("harness")
    h.advance(5)
    h.posted["codex-monitor"] = cg.iso(h.moment)
    h.tick("harness")
    assert h.state["harness"]["phase"] == "handoff"
    h.advance(5)
    h.tick("harness")
    assert h.fake.typed("harness") == ["/quit"]


def test_previous_sessions_handoff_done_does_not_end_a_fresh_session(tmp_path: Path) -> None:
    old = "⏺ HANDOFF-DONE infra .claude/infra-epic/DRIVER-STATE.md"
    h = Harness(tmp_path, **{"infra-muse": FakePane(text=claude_text(12, old), agent="claude", agent_pid="300")})
    h.posted["claude-infra"] = cg.iso(START - dt.timedelta(minutes=1))
    h.tick("infra-muse")
    h.advance(5)
    h.tick("infra-muse")
    assert h.state["infra-muse"]["phase"] == "watch"
    assert h.fake.typed() == []


def test_new_agent_process_resets_the_fleet_watch_window(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"infra-muse": claude_pane(30)})
    h.tick("infra-muse")
    h.advance(30)
    h.posted["claude-infra"] = cg.iso(h.moment)  # the old session's handoff post
    h.pane("infra-muse").agent_pid = "201"  # a human relaunched the lane before the guard ticked
    h.advance(1)
    h.tick("infra-muse")
    assert h.state["infra-muse"]["phase"] == "watch"
    assert h.fake.typed() == []


# ---- handoff phase ----------------------------------------------------------------
def test_handoff_now_is_resent_every_15_minutes_until_done(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"devops-muse": claude_pane(70)})
    h.tick()
    for minutes in (5, 5):  # +5, +10: no reminder yet
        h.advance(minutes)
        h.tick()
    assert len(h.fake.typed("devops-muse")) == 1
    h.advance(5)  # +15
    h.tick()
    typed = h.fake.typed("devops-muse")
    assert len(typed) == 2 and typed[1].startswith("HANDOFF NOW (reminder 2,")
    assert len(h.sent) == 2
    assert any("HANDOFF NOW re-sent (reminder 2)" in line for line in h.logs)


def test_lane_in_handoff_is_listed_for_keepalive_suppression(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"devops-muse": claude_pane(70), "infra-muse": claude_pane(20)})
    h.tick()
    assert cg.sessions_in_handoff(h.state) == ["devops-muse"]
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    cg.save_state(state_dir / "state.json", h.state)
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/ops/context_guard.py"), "handoff-sessions", "--state-dir", str(state_dir)],
        capture_output=True, text=True, check=True, timeout=60,
    )
    assert json.loads(result.stdout) == ["devops-muse"]


def test_codex_quit_is_retried_when_the_first_is_swallowed(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"atlas": codex_pane(40)})
    h.tick("atlas")
    h.posted["codex-atlas"] = cg.iso(h.moment)
    h.advance(5)
    h.tick("atlas")  # watch: HANDOFF-DONE posted -> handoff (done)
    h.advance(5)
    h.tick("atlas")
    assert h.fake.typed("atlas") == ["/quit"]
    h.advance(5)
    h.tick("atlas")
    assert h.fake.typed("atlas") == ["/quit"]  # 5 minutes: not yet
    h.advance(5)
    h.tick("atlas")
    assert h.fake.typed("atlas") == ["/quit", "/quit"]
    assert h.state["atlas"]["quit_attempts"] == 2


def test_ctx_pct_is_logged_on_every_handoff_tick(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"infra-muse": claude_pane(70, busy=True)})
    h.tick("infra-muse")
    h.logs.clear()
    for pct in (73, 76):
        h.pane("infra-muse").text = claude_text(pct, busy=True)
        h.advance(5)
        h.tick("infra-muse")
    assert [line.split()[2] for line in h.logs] == ["ctx_pct=73", "ctx_pct=76"]


def test_no_input_while_a_human_is_typing_in_the_session(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"cto": claude_pane(75)})
    h.fake.clients = [("cto", int(START.timestamp()) - 30)]
    h.tick()
    assert h.fake.typed() == []
    assert h.state["cto"]["phase"] == "watch"
    h.fake.clients = [("cto", int(START.timestamp()) - 600)]
    h.tick()
    assert len(h.fake.typed("cto")) == 1


def test_unreadable_client_telemetry_fails_closed() -> None:
    fake = FakeTmux()
    fake.run = lambda argv: subprocess.CompletedProcess(argv, 1, "", "permission denied")  # type: ignore[method-assign]
    assert cg.Tmux(run=fake.run).human_activity("cto", 120) == "client telemetry unavailable (rc=1)"


def test_exited_codex_lane_is_respawned_with_shims_first(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"open-model-data": codex_pane(40)})
    h.tick()
    h.posted["codex-open-model-data"] = cg.iso(h.moment)
    h.advance(5)
    h.tick()
    h.pane("open-model-data").agent = None
    h.advance(5)
    h.tick()
    respawn = next(call for call in h.fake.calls if call[:2] == ["tmux", "respawn-pane"])
    assert respawn[respawn.index("-t") + 1] == "=open-model-data:"
    assert respawn[respawn.index("-c") + 1] == str(tmp_path / "repo")
    path = respawn[respawn.index("-e") + 1]
    assert path.startswith(f"PATH={tmp_path / 'repo' / 'scripts/agent_runtime/shims'}:")
    command = respawn[respawn.index("bash"):]
    assert command[:4] == ["bash", "-c", PANE_SCRIPT, "lane-launch"]
    assert command[4:7] == ["./start-codex-driver.sh", "--epic", "open-model-data"]
    assert ["tmux", "clear-history", "-t", "=open-model-data:"] in h.fake.calls
    assert h.state["open-model-data"]["phase"] == "watch"


def test_relaunch_waits_until_the_launcher_has_exited(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"harness": codex_pane(40)})
    h.tick("harness")
    h.posted["codex-monitor"] = cg.iso(h.moment)
    h.advance(5)
    h.tick("harness")
    pane = h.pane("harness")
    pane.agent, pane.launcher_running = None, True
    h.advance(5)
    h.tick("harness")
    assert not any(call[:2] == ["tmux", "respawn-pane"] for call in h.fake.calls)
    assert h.logs[-1].endswith("agent gone, launcher still exiting; relaunch next tick")
    pane.launcher_running = False
    h.advance(5)
    h.tick("harness")
    assert any(call[:2] == ["tmux", "respawn-pane"] for call in h.fake.calls)


def test_codex_compactions_trigger_handoff(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"harness": codex_pane(60)})
    for pct in (60, 20, 50, 10, 45, 5):
        h.pane("harness").text = codex_text(pct)
        h.tick()
        h.advance(5)
    assert h.state["harness"]["compactions"] == 3
    assert h.fake.typed("harness")[0].startswith("HANDOFF NOW")


def test_tick_main_writes_state_and_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeTmux()
    real = cg.Tmux
    monkeypatch.setattr(cg, "Tmux", lambda: real(run=fake.run, sleep=fake.sleep, clock=fake.clock))
    monkeypatch.setenv("LU_DRIVER_LANES_LOCAL", str(tmp_path / "absent.json"))
    assert cg.main(["tick", "--state-dir", str(tmp_path / "s")]) == 0
    assert (tmp_path / "s" / "state.json").is_file()
    assert "tmux session cto missing" in (tmp_path / "s" / "guard.log").read_text(encoding="utf-8")


# ---- Fleet Comms adapters ----------------------------------------------------------
def test_comms_reader_counts_only_standalone_posts_from_the_lane(tmp_path: Path) -> None:
    import sqlite3

    db = tmp_path / "comms.sqlite3"
    with sqlite3.connect(db) as con:
        con.execute("create table comms_messages (sender text, created_at text, body_inline text)")
        con.executemany(
            "insert into comms_messages values (?, ?, ?)",
            [
                ("codex-devops", "2026-10-16T12:05:00Z", "will post HANDOFF-DONE soon"),
                ("claude-infra", "2026-10-16T11:00:00Z", "HANDOFF-DONE infra .claude/infra-epic/DRIVER-STATE.md"),
                ("claude-devops", "2026-10-16T12:06:00Z", "status\nHANDOFF-DONE devops .claude/devops-epic/DRIVER-STATE.md"),
            ],
        )
    logs: list[str] = []
    posted = cg.comms_reader(db, logs.append)
    assert posted("codex-devops", "2026-10-16T12:00:00Z") is True  # claude-devops alias, standalone line
    assert posted("codex-devops", "2026-10-16T12:07:00Z") is False
    assert posted("claude-infra", "2026-10-16T12:00:00Z") is False  # before the window
    assert cg.comms_reader(tmp_path / "absent.sqlite3", logs.append)("x", "y") is False
    assert logs and logs[-1].startswith("comms read error")
    assert cg.comms_reader(None, logs.append)("x", "y") is False


def test_fleet_sender_uses_the_data_file_identity_and_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.fleet_comms import authority

    calls: list[dict] = []

    class FakeAuthority:
        def __init__(self, root=None) -> None:
            pass

        def enqueue_supervisory_request(self, **kwargs):
            calls.append(kwargs)
            if kwargs["recipient"] == "down":
                raise RuntimeError("store unavailable")
            return type("Msg", (), {"message_id": "m-1"})()

    monkeypatch.setattr(authority, "AuthorityService", FakeAuthority)
    logs: list[str] = []
    send = cg.fleet_sender(load_registry().guard_sender, logs.append)
    send("epics", "body", "key-1")
    send("down", "body", "key-2")
    assert calls[0]["sender"] == load_registry().guard_sender and calls[0]["idempotency_key"] == "key-1"
    assert logs == ["send epics ok m-1", "send down failed RuntimeError: store unavailable"]


def test_stuck_handoff_alerts_epics_once_without_killing(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"infra-muse": claude_pane(70, busy=True)})
    h.tick("infra-muse")
    for _ in range(7):  # 35 minutes, busy and never done
        h.advance(5)
        h.tick("infra-muse")
    alerts = [body for recipient, body in h.sent if recipient == "epics"]
    assert len(alerts) == 1 and alerts[0].startswith("CTO-ALERT") and "no forced kill" in alerts[0]
    assert "/exit" not in h.fake.typed("infra-muse")


def test_exit_dialog_is_answered_with_exit_and_stop_tasks(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"cto": claude_pane(70)})
    h.tick("cto")
    h.pane("cto").text = claude_text(71, "1. Exit and stop tasks", "2. Move to background and exit")
    h.advance(5)
    h.tick("cto")
    assert h.fake.typed("cto")[-1] == "1"


# ---- unknown telemetry never acts (review of 69264fbb, #10814) ---------------------
def handoff_with_agent_gone(tmp_path: Path, *, launcher_running: bool) -> Harness:
    """The harness lane in the handoff phase (done) whose agent has just exited."""
    h = Harness(tmp_path, **{"harness": codex_pane(40)})
    h.tick("harness")
    h.posted["codex-monitor"] = cg.iso(h.moment)
    h.advance(5)
    h.tick("harness")  # watch -> handoff (done)
    pane = h.pane("harness")
    pane.agent, pane.launcher_running = None, launcher_running
    h.advance(5)
    return h


def respawns(h: Harness) -> list[list[str]]:
    return [call for call in h.fake.calls if call[:2] == ["tmux", "respawn-pane"]]


@pytest.mark.parametrize(
    ("command", "answer"),
    [
        ("ps", subprocess.CompletedProcess([], 1, "", "process table unavailable")),
        ("ps", subprocess.TimeoutExpired(["ps"], 30)),
        ("ps", FileNotFoundError("ps")),
        ("ps", subprocess.CompletedProcess([], 0, "", "")),
        ("ps", subprocess.CompletedProcess([], 0, "garbage\n", "")),
        ("ps", subprocess.CompletedProcess([], 0, "1 0 Fri Oct 16 06:00:00 2026 systemd\n300 100 bash\n", "")),
        ("ps", subprocess.CompletedProcess([], 0, "1 0 Xyz Oct 16 06:00:00 2026 systemd\n", "")),
        ("display-message", subprocess.CompletedProcess([], 1, "", "can't find pane")),
        ("display-message", subprocess.CompletedProcess([], 0, "\n", "")),
        ("capture-pane", subprocess.CompletedProcess([], 1, "", "can't find pane")),
    ],
)
def test_unknown_process_telemetry_never_respawns(tmp_path: Path, command: str, answer: object) -> None:
    h = handoff_with_agent_gone(tmp_path, launcher_running=True)
    h.fake.override[command] = answer  # type: ignore[assignment]
    h.logs.clear()
    h.tick("harness")
    assert respawns(h) == []
    assert h.fake.typed() == []
    assert h.state["harness"]["phase"] == "handoff"
    assert len(h.logs) == 1 and "telemetry unavailable" in h.logs[0] and h.logs[0].endswith("retry next tick")
    # Readable telemetry again: the launcher has exited, so the pane is respawned on the next tick.
    del h.fake.override[command]
    h.pane("harness").launcher_running = False
    h.advance(5)
    h.tick("harness")
    assert len(respawns(h)) == 1


def test_unknown_process_telemetry_in_watch_types_nothing(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"cto": claude_pane(80)})
    h.fake.override["ps"] = subprocess.CompletedProcess([], 1, "", "process table unavailable")
    h.tick("cto")
    assert h.fake.typed() == [] and h.sent == []
    assert h.state["cto"]["phase"] == "watch"


def test_snapshot_reads_pane_pid_then_the_table_once_then_pane_pid_again() -> None:
    fake = ShellTmux(sessions={"cto": Pane(agent="claude", agent_pid="4242", agent_start="Fri Oct  2 09:05:01 2026")})
    tmux = cg.Tmux(run=fake.run)
    shell = "100@2026-10-16T06:00:00"
    assert tmux.snapshot("=cto:", "claude") == cg.PaneSnapshot(shell, "4242@2026-10-02T09:05:01", busy=True)
    assert tmux.snapshot("=cto:", "codex") == cg.PaneSnapshot(shell, None, busy=True)
    assert [call[1] if call[0] == "tmux" else call for call in fake.calls] == [
        "display-message",
        ["env", "LC_ALL=C", "ps", "-eo", "pid=,ppid=,lstart=,comm="],
        "display-message",
    ] * 2


# ---- a changed agent gets none of its predecessor's handoff ---------------------
@pytest.mark.parametrize(
    "replace",
    [
        {"agent_pid": "201"},  # a human relaunched the lane
        {"agent_start": "Fri Oct 16 12:07:00 2026"},  # same pid reused by a new process
    ],
)
def test_replacement_agent_gets_no_exit_from_the_previous_handoff(tmp_path: Path, replace: dict[str, str]) -> None:
    done = "⏺ HANDOFF-DONE infra .claude/infra-epic/DRIVER-STATE.md"
    h = Harness(tmp_path, **{"infra-muse": claude_pane(70)})
    h.tick("infra-muse")
    h.pane("infra-muse").text = claude_text(72, ECHO, done)
    h.advance(5)
    h.posted["claude-infra"] = cg.iso(h.moment)
    h.tick("infra-muse")
    assert h.fake.typed("infra-muse")[-1] == "/exit"
    pane = h.pane("infra-muse")
    for key, value in replace.items():
        setattr(pane, key, value)
    pane.text = claude_text(10, ECHO, done)  # the old session's lines are still in the scrollback
    h.advance(10)
    h.tick("infra-muse")
    state = h.state["infra-muse"]
    assert state["phase"] == "watch"
    assert not {"done_seen", "quit_sent", "quit_attempts", "since", "last_nudge", "nudges", "alerted"} & set(state)
    assert "agent changed" in h.logs[-1]
    for _ in range(6):  # 30 more minutes at low context: no input of any kind
        h.advance(5)
        h.tick("infra-muse")
    assert h.fake.typed("infra-muse").count("/exit") == 1
    assert len(h.fake.typed("infra-muse")) == 2  # the first HANDOFF NOW and the first /exit only
    assert h.state["infra-muse"]["phase"] == "watch"


# ---- malformed client telemetry counts as a human present -------------------------
@pytest.mark.parametrize("rows", ["cto\tUNKNOWN", "cto", "cto\t", "infra-muse\tsoon", "cto\t12a"])
def test_unparseable_client_activity_types_nothing(tmp_path: Path, rows: str) -> None:
    h = Harness(tmp_path, **{"cto": claude_pane(75)})
    h.fake.override["list-clients"] = subprocess.CompletedProcess([], 0, rows + "\n", "")
    h.tick("cto")
    assert h.fake.typed() == [] and h.sent == []
    assert h.state["cto"]["phase"] == "watch"
    assert "client telemetry unparseable" in h.logs[-1] and h.logs[-1].endswith("retry next tick")
    del h.fake.override["list-clients"]
    h.advance(5)
    h.tick("cto")
    assert h.fake.typed("cto")[0].startswith("HANDOFF NOW")


def test_client_telemetry_timeout_counts_as_a_human() -> None:
    fake = FakeTmux(override={"list-clients": subprocess.TimeoutExpired(["tmux"], 30)})
    assert cg.Tmux(run=fake.run).human_activity("cto", 120) == "client telemetry unavailable (TimeoutExpired)"


def test_refused_local_wrapper_blocks_only_that_relaunch(tmp_path: Path) -> None:
    from scripts.ops.driver_lanes import load_local_config

    local = tmp_path / "local.json"
    local.write_text(json.dumps({"lanes": {"harness": {"wrapper": "printf expected; printf INJECTED"}}}))
    local.chmod(0o600)
    h = handoff_with_agent_gone(tmp_path, launcher_running=False)
    h.guard.local = load_local_config(local)
    h.tick("harness")
    assert respawns(h) == []
    assert h.state["harness"]["phase"] == "handoff"
    assert "relaunch refused" in h.logs[-1] and "shell syntax" in h.logs[-1]


# ---- respawn or type only on one consistent pane + process snapshot (review of 0b9a61a7, #10814) ----
REPLACED = "Fri Oct 16 12:09:00 2026"  # ps lstart of a pane shell started during the handoff


def before_call(tmux: cg.Tmux, command: str, change: Callable[[], None], nth: int = 1) -> None:
    """Run ``change`` right before the ``nth`` ``command`` call (``ps`` or a tmux command) from now on."""
    run, seen = tmux.run, [0]

    def wrapped(argv: list[str]) -> subprocess.CompletedProcess:
        if (argv[1] if argv[0] == "tmux" else "ps") == command:
            seen[0] += 1
            if seen[0] == nth:
                change()
        return run(argv)

    tmux.run = wrapped


def replace_pane(pane: FakePane, *, launcher: bool) -> Callable[[], None]:
    """A new pane shell (a human respawn), optionally already running a launcher."""

    def change() -> None:
        pane.pane_pid, pane.launcher_running = "101", launcher
        pane.pane_start = REPLACED  # type: ignore[attr-defined]

    return change


def test_snapshot_of_a_pane_replaced_between_the_reads_is_unknown() -> None:
    fake = ShellTmux(sessions={"cto": Pane(agent="claude")})
    tmux = cg.Tmux(run=fake.run)
    before_call(tmux, "display-message", replace_pane(fake.sessions["cto"], launcher=False), nth=2)
    with pytest.raises(cg.TelemetryUnavailable, match="pane pid changed 100 -> 101 while reading the process table"):
        tmux.snapshot("=cto:", "claude")


def test_snapshot_of_a_pane_missing_from_the_process_table_is_unknown() -> None:
    fake = FakeTmux(sessions={"cto": FakePane(agent="claude")})  # lists the agent but not the pane's shell
    with pytest.raises(cg.TelemetryUnavailable, match="pane pid 100 not in the process table"):
        cg.Tmux(run=fake.run).snapshot("=cto:", "claude")


def test_a_tick_reads_the_process_table_once(tmp_path: Path) -> None:
    h = handoff_with_agent_gone(tmp_path, launcher_running=True)
    h.fake.calls.clear()
    h.tick("harness")
    assert h.logs[-1].endswith("agent gone, launcher still exiting; relaunch next tick")
    assert [call for call in h.fake.calls if call[0] == "env"] == [cg.PS_ARGV]


@pytest.mark.parametrize("launcher", [False, True], ids=["bare-shell", "launcher"])
@pytest.mark.parametrize(
    ("command", "nth"), [("ps", 1), ("display-message", 2)], ids=["before-table", "before-second-pid"]
)
def test_pane_replaced_during_the_snapshot_is_never_respawned(
    tmp_path: Path, command: str, nth: int, launcher: bool
) -> None:
    h = handoff_with_agent_gone(tmp_path, launcher_running=False)
    before_call(h.guard.tmux, command, replace_pane(h.pane("harness"), launcher=launcher), nth)
    h.logs.clear()
    h.tick("harness")
    assert respawns(h) == []
    assert "telemetry unavailable (pane pid changed 100 -> 101" in h.logs[0]
    h.advance(5)
    h.tick("harness")  # a consistent read now shows a pane the handoff never saw
    assert h.state["harness"]["phase"] == "watch" and "pane changed" in h.logs[-1]
    for _ in range(3):
        h.advance(5)
        h.tick("harness")
    assert respawns(h) == []


@pytest.mark.parametrize("replace", [{"pane_pid": "101"}, {"pane_start": REPLACED}], ids=["new-pid", "reused-pid"])
def test_replaced_pane_resets_the_handoff_and_is_never_respawned(tmp_path: Path, replace: dict[str, str]) -> None:
    h = handoff_with_agent_gone(tmp_path, launcher_running=False)
    pane = h.pane("harness")
    for key, value in replace.items():
        setattr(pane, key, value)
    h.tick("harness")
    assert respawns(h) == []
    state = h.state["harness"]
    assert state["phase"] == "watch" and state["agent_id"] is None
    assert state["pane_id"] == f"{pane.pane_pid}@{dt.datetime.strptime(pane.pane_start, cg.LSTART_FORMAT).isoformat()}"  # type: ignore[attr-defined]
    assert not {"done_seen", "quit_sent", "quit_attempts", "since", "nudges"} & set(state)
    assert "pane changed 100@2026-10-16T06:00:00 -> " in h.logs[-1]
    for _ in range(3):
        h.advance(5)
        h.tick("harness")
    assert respawns(h) == []


@pytest.mark.parametrize("change", ["pane-replaced", "launcher-started"])
def test_pane_changed_after_the_snapshot_is_not_respawned(tmp_path: Path, change: str) -> None:
    h = handoff_with_agent_gone(tmp_path, launcher_running=False)
    pane = h.pane("harness")
    if change == "pane-replaced":
        perturb = replace_pane(pane, launcher=True)
    else:
        perturb = lambda: setattr(pane, "launcher_running", True)  # noqa: E731
    before_call(h.guard.tmux, "list-clients", perturb)  # the human check, after the snapshot and before the re-check
    h.tick("harness")
    assert respawns(h) == []
    assert "pane changed before respawn-pane -k" in h.logs[-1] and h.logs[-1].endswith("retry next tick")
    assert h.state["harness"]["phase"] == "handoff"
    pane.launcher_running = False
    h.advance(5)
    h.tick("harness")
    if change == "pane-replaced":  # a pane the handoff never saw is a new session, never respawned
        assert h.state["harness"]["phase"] == "watch" and "pane changed" in h.logs[-1]
        assert respawns(h) == []
    else:  # the same pane, once its launcher has exited, is relaunched
        assert len(respawns(h)) == 1


def test_exit_dialog_answer_is_not_typed_into_a_replaced_agent(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"cto": claude_pane(70)})
    h.tick("cto")
    pane = h.pane("cto")
    pane.text = claude_text(71, "1. Exit and stop tasks", "2. Move to background and exit")
    h.advance(5)
    before_call(h.guard.tmux, "list-clients", lambda: setattr(pane, "agent_pid", "201"))
    h.tick("cto")
    assert h.fake.typed("cto") == [h.fake.typed("cto")[0]]  # the HANDOFF NOW only
    assert "pane changed before the exit-dialog answer" in h.logs[-1]
    assert "agent 200@2026-10-16T11:00:00 -> 201@2026-10-16T11:00:00" in h.logs[-1]


@pytest.mark.parametrize("change", ["agent-replaced", "telemetry-unavailable"])
def test_exit_is_not_typed_into_an_agent_the_tick_did_not_snapshot(tmp_path: Path, change: str) -> None:
    done = "⏺ HANDOFF-DONE infra .claude/infra-epic/DRIVER-STATE.md"
    h = Harness(tmp_path, **{"infra-muse": claude_pane(70)})
    h.tick("infra-muse")
    pane = h.pane("infra-muse")
    pane.text = claude_text(72, ECHO, done)
    h.advance(5)
    h.posted["claude-infra"] = cg.iso(h.moment)
    if change == "agent-replaced":
        perturb = lambda: setattr(pane, "agent_pid", "201")  # noqa: E731
    else:
        perturb = lambda: h.fake.override.update(ps=subprocess.CompletedProcess([], 1, "", "ps failed"))  # noqa: E731
    before_call(h.guard.tmux, "list-clients", perturb)
    h.tick("infra-muse")
    assert "/exit" not in h.fake.typed("infra-muse")
    assert h.state["infra-muse"].get("quit_sent") is None
    expected = "pane changed before /exit" if change == "agent-replaced" else "telemetry unavailable (process table"
    assert expected in h.logs[-1]
