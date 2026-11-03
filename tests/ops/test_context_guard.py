"""Context guard behavior against a fake tmux (#10814)."""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from scripts.ops import context_guard as cg
from scripts.ops.driver_lanes import EXIT_MARKER, PANE_SCRIPT, START_MARKER, load_registry
from tests.ops._fake_tmux import BOOT, FakePane, FakeTmux

REPO = Path(__file__).resolve().parents[2]
START = dt.datetime(2026, 10, 16, 12, 0, tzinfo=dt.UTC)
ECHO = (
    "> HANDOFF NOW (CTO automated, 2026-10-16T12:00:00Z): your context is 70% (hand off at 70%). "
    "Finish the current step only, write the top of .claude/infra-epic/DRIVER-STATE.md "
    "(in-flight workers with task ids, waits with nonces, PRs, holds, orders and their status, next actions), "
    "stop every background task you started (background Bash tasks and Monitor streams), "
    "post 'HANDOFF-DONE infra .claude/infra-epic/DRIVER-STATE.md' to Fleet Comms recipient epics, then stop. "
    "The guard exits and relaunches your seat; running workers keep running and the fresh session adopts them."
)


def claude_text(pct: int, *lines: str, busy: bool = False) -> str:
    status = "✻ Thinking… (esc to interrupt)" if busy else ">"
    return "\n".join([*lines, status, f"  ctx: {pct * 10}K/1000K ({pct}%)"])


def codex_text(pct: int, *lines: str, ready: bool = True) -> str:
    return "\n".join([*lines, "Ready" if ready else "Working (3s)", f"Context {pct}% used"])


SCOPE = "lu-driver-claude-epics-05592eda-1b2c-4d3e-8f4a-5b6c7d8e9f01.scope"
CGROUP = f"0::/user.slice/user-1000.slice/user@1000.service/lu.slice/lu-driver.slice/{SCOPE}/tools\n"


@dataclass
class Pane(FakePane):
    pane_start: str = BOOT  # ps lstart of the pane's own shell
    scope: str | None = SCOPE  # the agent's lu-driver scope; None means it runs outside one
    exit_after_stop: float | None = 0  # seconds the agent outlives a scope stop; None means it never exits
    launcher_lag: float = 0  # seconds the pane's launcher keeps running after the agent has exited
    stop_age: float | None = None  # seconds since the scope stop was queued


@dataclass
class ShellTmux(FakeTmux):
    """The fake with each pane's own shell in the process table, as ``ps`` lists it.

    It also answers the systemd calls of a forced relaunch: the agent's cgroup, a scope's state
    and ``systemctl stop``. A stopped scope's agent survives ``exit_after_stop`` seconds of fake
    ``sleep`` (the 2026-11-02 sequence: the old process exits after the respawn used to start),
    and a respawn records whether a predecessor was still running at that moment.
    """

    live_scopes: set[str] = field(default_factory=set)  # scopes that stay active with no agent in a pane
    call_cost: float = 0  # seconds of the monotonic clock each runner call takes
    mono: float = 5_000.0
    stopped_at: list[float] = field(default_factory=list)  # monotonic time of each scope stop
    respawned_over_live_agent: list[bool] = field(default_factory=list)

    def _ps_rows(self, *, with_start: bool) -> list[str]:
        rows = super()._ps_rows(with_start=with_start)
        shells = {pane.pane_pid: getattr(pane, "pane_start", BOOT) for pane in self.sessions.values()}
        shell_rows = [f"{pid} 1 {start} bash" if with_start else f"{pid} 1 bash" for pid, start in shells.items()]
        return rows[:1] + shell_rows + rows[1:]

    def _scope_state(self, unit: str) -> str:
        if unit in self.live_scopes:
            return "active"
        for pane in self.sessions.values():
            if getattr(pane, "scope", None) == unit and pane.agent:
                return "active" if pane.stop_age is None else "deactivating"
        return "inactive"

    def monotonic(self) -> float:
        return self.mono

    def run(self, argv: list[str]) -> subprocess.CompletedProcess:
        self.mono += self.call_cost
        self._age(self.call_cost)
        if argv[0] == "cat":
            self.calls.append(list(argv))
            if "cat" in self.override:
                return self.override["cat"]  # type: ignore[return-value]
            pid = argv[1].split("/")[2]
            for pane in self.sessions.values():
                if pane.agent and pane.agent_pid == pid:
                    return self._ok(CGROUP if pane.scope == SCOPE else "0::/user.slice/user-1000.slice/session-3.scope\n")
            return self._fail("No such file or directory")
        if argv[0] == "systemctl":
            self.calls.append(list(argv))
            if argv[2] == "is-active":
                return subprocess.CompletedProcess(argv, 0, self._scope_state(argv[3]) + "\n", "")
            assert argv[2:4] == ["stop", "--no-block"], argv
            self.stopped_at.append(self.mono)
            for pane in self.sessions.values():
                if pane.scope == argv[4] and pane.agent and pane.stop_age is None:
                    pane.stop_age = 0.0
                    self._age(0.0)
            return self._ok("")
        if argv[:2] == ["tmux", "respawn-pane"]:
            result = super().run(argv)
            pane = self.sessions[argv[argv.index("-t") + 1].strip("=:")]
            alive = pane.agent is not None
            self.respawned_over_live_agent.append(alive)
            occurrence = next(a.split("=", 1)[1] for a in argv if a.startswith("LU_LANE_RELAUNCH_ID="))
            if alive:  # the successor's single-instance check meets the predecessor
                pane.agent, pane.stop_age = None, None
                pane.text = launcher_output(occurrence, 3, "refused: a CTO process is still running")
            else:
                pane.agent, pane.agent_pid, pane.agent_start = "claude", "400", "Fri Oct 16 12:30:00 2026"
                pane.text = claude_text(1)
            return result
        return super().run(argv)

    def _age(self, seconds: float) -> None:
        for pane in self.sessions.values():
            if pane.stop_age is not None and pane.agent:
                pane.stop_age += seconds
                if pane.exit_after_stop is not None and pane.stop_age >= pane.exit_after_stop:
                    pane.agent, pane.stop_age = None, None
                    pane.launcher_running = pane.launcher_lag > 0
            elif pane.launcher_running and pane.launcher_lag > 0:
                pane.launcher_lag -= seconds
                pane.launcher_running = pane.launcher_lag > 0

    def sleep(self, seconds: float) -> None:
        super().sleep(seconds)
        self.mono += seconds
        self._age(seconds)


def launcher_output(occurrence: str, rc: int, tail: str) -> str:
    """What the fixed pane script prints around a launcher run (scripts/ops/driver_lanes.py)."""
    return f"\n{START_MARKER}{occurrence}\n{tail}\n\n{EXIT_MARKER}{rc} id={occurrence}\n"


class Harness:
    def __init__(self, tmp_path: Path, **panes: FakePane) -> None:
        self.fake = ShellTmux(sessions=dict(panes), now=START.timestamp())
        self.moment = START
        self.logs: list[str] = []
        self.sent: list[tuple[str, str]] = []
        self.posted: dict[str, str] = {}  # sender -> created_at of a HANDOFF-DONE post
        self.state: dict = {}
        self.proc_root = tmp_path / "proc"
        self.rollouts = tmp_path / "rollouts"
        self.rollouts.mkdir(exist_ok=True)
        for session, pane in panes.items():
            if pane.agent == "codex":
                self.compactions(session, 0)
        self.guard = cg.Guard(
            registry=load_registry(),
            repo_root=tmp_path / "repo",
            tmux=cg.Tmux(
                run=self.fake.run,
                sleep=self.fake.sleep,
                clock=lambda: self.moment.timestamp(),
                monotonic=self.fake.monotonic,
            ),
            log=self.logs.append,
            send=lambda recipient, body, key: self.sent.append((recipient, body)),
            handoff_posted=lambda sender, since: sender in self.posted and self.posted[sender] >= since,
            now=lambda: self.moment,
        )
        self.guard.tmux.proc_root = self.proc_root

    def tick(self, *only: str) -> None:
        self.guard.run(self.state, list(only))

    def advance(self, minutes: float) -> None:
        self.moment += dt.timedelta(minutes=minutes)

    def pane(self, session: str) -> FakePane:
        return self.fake.sessions[session]

    def compactions(self, session: str, count: int) -> Path:
        """The fake agent holds its own rollout open, independently of the pane percent."""
        pid = self.pane(session).agent_pid
        path = self.rollouts / f"rollout-{pid}.jsonl"
        records = [{"type": "session_meta", "payload": {"id": "01234567-89ab-4cde-8fab-0123456789ab"}}]
        records += [{"type": "compacted", "payload": {}} for _ in range(count)]
        path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
        fd = self.proc_root / pid / "fd" / "3"
        fd.parent.mkdir(parents=True, exist_ok=True)
        if not fd.is_symlink():
            fd.symlink_to(path)
        return path


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


def missing_lead_alert_times(h: Harness, minutes: int) -> list[int]:
    """Tick every 5 minutes for ``minutes``; return the minutes at which claude-cto was alerted."""
    times = []
    for minute in range(0, minutes + 1, 5):
        before = len(h.sent)
        h.tick()
        times += [minute] * sum(recipient == "claude-cto" for recipient, _ in h.sent[before:])
        h.advance(5)
    return times


def test_missing_lead_lane_alerts_claude_cto_after_15_minutes_then_hourly(tmp_path: Path) -> None:
    """Defect class: silent dead seat. The CTO session was missing for 13 hours and the guard only logged it."""
    h = Harness(tmp_path)  # no session at all: every lane is missing
    assert missing_lead_alert_times(h, 135) == [15, 75, 135]
    assert {recipient for recipient, _ in h.sent} == {"claude-cto"}  # non-lead lanes only log
    assert "lead lane cto has no tmux session cto for 15 min" in h.sent[0][1]
    assert h.fake.typed() == []
    assert not any(call[:2] in (["tmux", "new-session"], ["tmux", "respawn-pane"]) for call in h.fake.calls)
    h.fake.sessions["cto"] = claude_pane(10)
    h.tick("cto")
    assert "missing_since" not in h.state["cto"]
    del h.fake.sessions["cto"]
    h.sent.clear()
    assert missing_lead_alert_times(h, 15) == [15]  # a fresh absence waits its own 15 minutes


def test_missing_lead_lane_alert_names_a_removed_socket_under_a_running_server(tmp_path: Path) -> None:
    """Defect class: unreachable live tmux server. The socket file was deleted, the server kept running and
    attached clients worked, but the guard's ``has-session`` could not connect and said only "missing"."""
    (tmp_path / "tmux").mkdir()  # an existing prefix of a path with a space must not hide the removed socket
    socket = tmp_path / "tmux space" / "tmux-1000" / "default"
    h = Harness(tmp_path)
    h.fake.servers = ["2793205 tmux new -s cto"]
    h.fake.override["has-session"] = subprocess.CompletedProcess(
        [], 1, "", f"error connecting to {socket} (No such file or directory)\n"
    )
    assert missing_lead_alert_times(h, 15) == [15]
    body = h.sent[-1][1]
    assert f"The socket file {socket} is gone while tmux server processes still run (2793205 tmux new -s cto)" in body
    assert "kill -USR1" in body and f"parent directory of {socket} is missing" in body
    assert "The guard sends no signal." in body
    assert not any(call[0] in ("kill", "systemd-run") for call in h.fake.calls)
    h.fake.override["pgrep"] = subprocess.CompletedProcess([], 2, "", "pgrep: cannot read the process table")
    h.state.clear()
    missing_lead_alert_times(h, 15)
    assert "tmux server processes unknown (pgrep rc=2)" in h.sent[-1][1]  # a failed probe is not "no server"
    del h.fake.override["pgrep"]
    socket.parent.mkdir(parents=True)
    socket.touch()  # a socket file that still exists is not the removed-socket case
    h.state.clear()
    h.sent.clear()
    missing_lead_alert_times(h, 15)
    assert "is gone" not in h.sent[-1][1] and str(socket) in h.sent[-1][1]


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
    assert h.fake.typed("infra-muse") == [ECHO.removeprefix("> ")]
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
    h.guard.tmux.proc_root = tmp_path / "unavailable-proc"
    h.tick("harness")
    assert h.state["harness"]["compactions"] is None
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
    h.tick("devops-muse")  # the other lanes are absent; the absent lead lane would alert at +15
    for minutes in (5, 5):  # +5, +10: no reminder yet
        h.advance(minutes)
        h.tick("devops-muse")
    assert len(h.fake.typed("devops-muse")) == 1
    h.advance(5)  # +15
    h.tick("devops-muse")
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
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert json.loads(result.stdout) == ["devops-muse"]


def test_codex_quit_is_retried_when_the_first_is_swallowed(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"codex-atlas": codex_pane(40)})
    h.tick("codex-atlas")
    h.posted["codex-atlas"] = cg.iso(h.moment)
    h.advance(5)
    h.tick("codex-atlas")  # watch: HANDOFF-DONE posted -> handoff (done)
    h.advance(5)
    h.tick("codex-atlas")
    assert h.fake.typed("codex-atlas") == ["/quit"]
    h.advance(5)
    h.tick("codex-atlas")
    assert h.fake.typed("codex-atlas") == ["/quit"]  # 5 minutes: not yet
    h.advance(5)
    h.tick("codex-atlas")
    assert h.fake.typed("codex-atlas") == ["/quit", "/quit"]
    assert h.state["codex-atlas"]["quit_attempts"] == 2


def test_agent_surviving_two_exits_after_handoff_done_is_relaunched(tmp_path: Path) -> None:
    """Defect class: a swallowed Claude /exit leaves a completed handoff stuck forever."""
    h = Harness(tmp_path, **{"cto": claude_pane(70)})
    h.tick("cto")
    h.advance(5)
    h.tick("cto")
    assert h.fake.typed("cto")[-1].startswith("HANDOFF NOW")
    assert respawns(h) == []

    secret = "sk-" + "testcredential" * 4
    h.pane("cto").text = claude_text(71, "HANDOFF-DONE cto", "exit stayed open", f"API_KEY={secret}")
    h.tick("cto")
    assert h.fake.typed("cto")[-1] == "/exit"
    assert respawns(h) == []

    # The timer tick can be 299 seconds after a command typed a second into the previous tick.
    h.advance(299 / 60)
    h.tick("cto")
    assert h.fake.typed("cto").count("/exit") == 2
    assert any("exit stayed open" in line for line in h.logs)
    assert secret not in "\n".join(h.logs)
    assert respawns(h) == []  # the second attempt gets its own tick to exit

    h.advance(5)
    h.fake.clients = [("cto", int(h.moment.timestamp()))]
    h.tick("cto")
    assert respawns(h) == []
    h.fake.clients.clear()
    h.pane("cto").text = claude_text(71, "HANDOFF-DONE cto", busy=True)
    h.tick("cto")
    assert respawns(h) == []
    h.pane("cto").text = claude_text(71, "HANDOFF-DONE cto", "exit stayed open", f"API_KEY={secret}")
    h.tick("cto")
    assert len(respawns(h)) == 1
    assert respawns(h)[0][respawns(h)[0].index("-t") + 1] == "=cto:"
    assert "./start-claude-cto.sh" in respawns(h)[0]
    assert h.state["cto"]["phase"] == "watch"
    alerts = [body for recipient, body in h.sent if recipient == "claude-cto"]
    assert len(alerts) == 1 and "exit stayed open" in alerts[0]
    assert secret not in alerts[0]
    h.tick("cto")
    assert len(respawns(h)) == 1
    assert len([body for recipient, body in h.sent if recipient == "claude-cto"]) == 1


def stuck_exit_harness(tmp_path: Path, **pane_fields: object) -> Harness:
    """A cto lane whose idle agent has swallowed two ``/exit`` after HANDOFF-DONE: the next tick is the forced relaunch."""
    h = Harness(tmp_path, **{"cto": Pane(text=claude_text(70), agent="claude", **pane_fields)})
    h.tick("cto")
    h.advance(5)
    h.tick("cto")
    h.pane("cto").text = claude_text(71, "HANDOFF-DONE cto")
    h.tick("cto")
    h.advance(5)
    h.tick("cto")
    assert h.fake.typed("cto").count("/exit") == 2
    assert respawns(h) == []
    h.advance(5)
    return h


def systemctl(h: Harness, verb: str) -> list[list[str]]:
    return [call for call in h.fake.calls if call[:2] == ["systemctl", "--user"] and verb in call]


def cto_alerts(h: Harness) -> list[str]:
    return [body for recipient, body in h.sent if recipient == "claude-cto"]


def test_forced_relaunch_stops_the_scope_and_waits_for_the_agent_before_respawning(tmp_path: Path) -> None:
    """AC-01/AC-03: the 2026-11-02 agent outlives its pane by seconds; the successor must not start before it is gone."""
    h = stuck_exit_harness(tmp_path, exit_after_stop=8, launcher_lag=3)
    h.tick("cto")
    assert systemctl(h, "stop") == [["systemctl", "--user", "stop", "--no-block", SCOPE]]
    assert h.fake.calls.index(systemctl(h, "stop")[0]) < h.fake.calls.index(respawns(h)[0])
    assert h.fake.respawned_over_live_agent == [False]  # nothing of the predecessor was running at the respawn
    pane = h.pane("cto")
    assert pane.agent == "claude" and pane.agent_pid == "400"  # the successor started
    assert "refused" not in pane.text
    assert h.state["cto"]["phase"] == "watch" and h.state["cto"]["predecessor_scope"] == SCOPE
    assert len(cto_alerts(h)) == 1 and "survived two /exit attempts" in cto_alerts(h)[0]


def test_old_scope_leftover_that_never_exits_blocks_the_respawn_and_alerts_once(tmp_path: Path) -> None:
    h = stuck_exit_harness(tmp_path, exit_after_stop=None)
    h.tick("cto")
    assert respawns(h) == []
    assert h.state["cto"]["phase"] == "handoff"
    assert len(systemctl(h, "stop")) == 1
    alerts = cto_alerts(h)
    assert len(alerts) == 1 and "relaunch held" in alerts[0] and SCOPE in alerts[0] and "60s" in alerts[0]
    h.advance(5)
    h.tick("cto")
    assert respawns(h) == [] and len(cto_alerts(h)) == 1  # one alert per handoff phase, still no respawn
    h.pane("cto").agent = None  # it finally exits: the ordinary relaunch takes over
    h.advance(5)
    h.tick("cto")
    assert len(respawns(h)) == 1 and h.fake.respawned_over_live_agent == [False]


def test_forced_relaunch_never_stops_an_agent_it_cannot_place_in_a_driver_scope(tmp_path: Path) -> None:
    h = stuck_exit_harness(tmp_path, scope=None)
    h.tick("cto")
    assert systemctl(h, "stop") == [] and respawns(h) == []
    assert len(cto_alerts(h)) == 1 and "not in a lu-driver scope" in cto_alerts(h)[0]


def test_forced_relaunch_waits_while_the_launcher_is_still_exiting_after_the_agent_is_gone(tmp_path: Path) -> None:
    h = stuck_exit_harness(tmp_path, launcher_lag=70)
    h.tick("cto")
    assert respawns(h) == [] and len(cto_alerts(h)) == 1 and "launcher is still exiting" in cto_alerts(h)[0]


def test_unreadable_agent_cgroup_never_stops_or_respawns(tmp_path: Path) -> None:
    h = stuck_exit_harness(tmp_path)
    h.fake.override["cat"] = subprocess.CompletedProcess([], 1, "", "No such file or directory")
    h.tick("cto")
    assert systemctl(h, "stop") == [] and respawns(h) == []
    assert any("telemetry unavailable" in line and "agent cgroup" in line for line in h.logs)


def test_human_activity_blocks_the_scope_stop(tmp_path: Path) -> None:
    """AC-04: the human-activity guard also covers the new stop."""
    h = stuck_exit_harness(tmp_path)
    h.fake.clients = [("cto", int(h.moment.timestamp()))]
    h.tick("cto")
    assert systemctl(h, "stop") == [] and respawns(h) == []


def test_agent_is_never_stopped_before_handoff_done(tmp_path: Path) -> None:
    """AC-04: no forced kill without HANDOFF-DONE, however long the handoff takes."""
    h = Harness(tmp_path, **{"cto": claude_pane(70)})
    h.tick("cto")
    for _ in range(30):
        h.advance(5)
        h.tick("cto")
    assert systemctl(h, "stop") == [] and respawns(h) == []


def test_replaced_agent_during_the_wait_is_never_respawned_over(tmp_path: Path) -> None:
    h = stuck_exit_harness(tmp_path, exit_after_stop=None)
    original_sleep = h.fake.sleep

    def replace_then_sleep(seconds: float) -> None:
        h.pane("cto").agent_pid, h.pane("cto").agent_start = "555", "Fri Oct 16 12:20:00 2026"  # a human relaunch
        original_sleep(seconds)

    h.guard.tmux.sleep = replace_then_sleep
    h.tick("cto")
    assert respawns(h) == []
    assert any("replaced while waiting for the predecessor" in line for line in h.logs)


def test_a_scope_kept_alive_by_background_tasks_still_blocks_the_next_ticks_respawn(tmp_path: Path) -> None:
    """The recorded scope outlives the agent: an empty pane is not proof that the predecessor is gone."""
    h = stuck_exit_harness(tmp_path)
    h.fake.live_scopes.add(SCOPE)
    h.tick("cto")  # the agent exits on the stop, the scope stays active: the wait expires
    assert respawns(h) == [] and h.pane("cto").agent is None
    assert h.state["cto"]["predecessor_scope"] == SCOPE and len(cto_alerts(h)) == 1
    h.advance(5)
    h.tick("cto")  # agent gone and pane idle, but the recorded scope is still active
    assert respawns(h) == [] and len(cto_alerts(h)) == 1
    h.fake.live_scopes.clear()
    h.advance(5)
    h.tick("cto")
    assert len(respawns(h)) == 1 and h.fake.respawned_over_live_agent == [False]


class Killed(BaseException):
    """The service timeout ending the pass: not an ``Exception``, so no lane handler catches it."""


def test_the_scope_is_saved_before_its_stop_so_a_killed_pass_still_holds_the_next_tick(tmp_path: Path) -> None:
    """The service timeout can end a pass before the end-of-run save; the next process must still hold."""
    state_path = tmp_path / "state.json"
    h = stuck_exit_harness(tmp_path)
    h.guard.checkpoint = lambda state: cg.save_state(state_path, state)
    h.fake.live_scopes.add(SCOPE)  # background tasks keep the scope active after the agent exits

    def killed(_seconds: float) -> None:
        raise Killed

    h.guard.tmux.sleep = killed
    with pytest.raises(Killed):
        h.tick("cto")  # killed mid-wait: the end-of-run save never ran
    assert systemctl(h, "stop") != [] and respawns(h) == []
    assert cg.load_state(state_path)["cto"]["predecessor_scope"] == SCOPE

    h.guard.tmux.sleep = h.fake.sleep
    h.state = cg.load_state(state_path)  # a new process starts from disk
    h.advance(5)
    h.tick("cto")
    assert respawns(h) == []  # the agent is gone and the pane idle, but the scope is not
    h.fake.live_scopes.clear()
    h.advance(5)
    h.tick("cto")
    assert len(respawns(h)) == 1 and h.fake.respawned_over_live_agent == [False]


def test_nothing_is_stopped_when_the_scope_record_cannot_be_saved(tmp_path: Path) -> None:
    h = stuck_exit_harness(tmp_path)

    def refuse_to_save(_state: dict) -> None:
        raise OSError("disk full")

    h.guard.checkpoint = refuse_to_save
    h.tick("cto")
    assert systemctl(h, "stop") == [] and respawns(h) == []
    assert any("error OSError" in line for line in h.logs)


def test_a_reused_pid_never_lends_its_scope_to_the_predecessor(tmp_path: Path) -> None:
    """The agent exits between the snapshot and the cgroup read and another process takes its pid."""
    h = stuck_exit_harness(tmp_path)

    def reuse_pid() -> None:
        h.pane("cto").agent_start = "Fri Oct 16 12:20:00 2026"  # same pid, a different process

    before_call(h.guard.tmux, "cat", reuse_pid)
    h.tick("cto")
    assert systemctl(h, "stop") == [] and respawns(h) == []
    assert "predecessor_scope" not in h.state["cto"]
    assert any("pid was reused" in line for line in h.logs)


def test_scope_that_stays_active_at_the_pending_retry_blocks_it(tmp_path: Path) -> None:
    h = relaunched(tmp_path)
    refuse(h)
    h.advance(5)
    h.tick("cto")  # a refusal with nothing of the predecessor left: the retry is scheduled
    h.fake.live_scopes.add(SCOPE)
    h.advance(5)
    h.tick("cto")
    assert len(respawns(h)) == 1


def test_pending_retry_is_cancelled_when_a_person_replaces_the_pane(tmp_path: Path) -> None:
    h = relaunched(tmp_path)
    refuse(h)
    h.advance(5)
    h.tick("cto")
    pane = h.pane("cto")
    pane.pane_pid, pane.text = "777", "$ "  # a person opens their own shell in the lane
    h.advance(5)
    h.tick("cto")
    assert len(respawns(h)) == 1
    assert "relaunch_retry" not in h.state["cto"]
    assert any("pending retry cancelled" in line for line in h.logs)
    for _ in range(2):
        h.advance(5)
        h.tick("cto")
    assert len(respawns(h)) == 1


def test_the_wait_is_bounded_by_the_clock_including_slow_telemetry(tmp_path: Path) -> None:
    """Each runner call takes 5 s: the deadline still ends the wait 60 s after the stop, plus at most one polling pass."""
    h = stuck_exit_harness(tmp_path, exit_after_stop=None)
    h.fake.call_cost = 5
    alerted_at: list[float] = []
    h.guard.send = lambda recipient, body, key: alerted_at.append(h.fake.mono)
    h.tick("cto")
    assert respawns(h) == [] and len(alerted_at) == 1
    polling_pass = 5 * 5 + 1  # the snapshot (3 reads), the scope state and the process table, plus the sleep
    assert alerted_at[0] - h.fake.stopped_at[0] <= cg.PREDECESSOR_EXIT_SECONDS + polling_pass + 5


def relaunched(tmp_path: Path) -> Harness:
    """A cto lane relaunched by the forced path, with the successor's launcher then reporting its output."""
    h = stuck_exit_harness(tmp_path)
    h.tick("cto")
    assert len(respawns(h)) == 1
    return h


def refuse(h: Harness, rc: int = 3, tail: str = "refused: a CTO process is still running") -> None:
    pane = h.pane("cto")
    pane.agent = None
    pane.text = launcher_output(h.state["cto"]["relaunch_id"], rc, tail)


def test_single_instance_refusal_is_retried_exactly_once_on_the_next_tick(tmp_path: Path) -> None:
    """AC-02: one retry, a tick later; the second refusal alerts and stays down."""
    h = relaunched(tmp_path)
    refuse(h)
    h.advance(5)
    h.tick("cto")  # the refusal is seen; the retry waits for the next tick
    assert len(respawns(h)) == 1
    assert [body for recipient, body in h.sent if recipient == "epics"] == []
    h.advance(5)
    h.tick("cto")
    assert len(respawns(h)) == 2 and h.state["cto"]["relaunch_retried"] is True
    refuse(h)
    h.advance(5)
    h.tick("cto")
    alerts = [body for recipient, body in h.sent if recipient == "epics"]
    assert len(alerts) == 1 and "rc=3" in alerts[0] and "still running" in alerts[0]
    for _ in range(3):
        h.advance(5)
        h.tick("cto")
    assert len(respawns(h)) == 2 and len([1 for r, _b in h.sent if r == "epics"]) == 1


def test_a_successful_retry_clears_the_retry_marker(tmp_path: Path) -> None:
    h = relaunched(tmp_path)
    refuse(h)
    h.advance(5)
    h.tick("cto")
    h.advance(5)
    h.tick("cto")
    assert len(respawns(h)) == 2  # the fake's new launcher starts an agent
    h.advance(5)
    h.tick("cto")
    state = h.state["cto"]
    assert not any(key in state for key in ("relaunch_retried", "relaunch_retry", "relaunch_hold", "predecessor_scope"))


@pytest.mark.parametrize(
    ("rc", "tail"),
    [
        (1, "refused: a CTO process is still running"),  # another rc
        (3, "project interpreter not found: /x/.venv/bin/python"),  # rc 3 for another reason
        (6, "DRIVER_SCOPE_REFUSED reason=slice-not-installed"),
    ],
)
def test_any_other_launcher_failure_stays_terminal(tmp_path: Path, rc: int, tail: str) -> None:
    h = relaunched(tmp_path)
    refuse(h, rc, tail)
    for _ in range(3):
        h.advance(5)
        h.tick("cto")
    assert len(respawns(h)) == 1
    assert len([1 for r, _b in h.sent if r == "epics"]) == 1


def test_refusal_with_the_predecessor_scope_still_active_is_terminal(tmp_path: Path) -> None:
    h = relaunched(tmp_path)
    h.fake.live_scopes.add(SCOPE)
    refuse(h)
    for _ in range(3):
        h.advance(5)
        h.tick("cto")
    assert len(respawns(h)) == 1
    assert len([1 for r, _b in h.sent if r == "epics"]) == 1
    assert any("the predecessor may remain" in line for line in h.logs)


def test_retry_is_deferred_not_spent_while_a_human_is_active(tmp_path: Path) -> None:
    h = relaunched(tmp_path)
    refuse(h)
    h.advance(5)
    h.tick("cto")
    h.advance(5)
    h.fake.clients = [("cto", int(h.moment.timestamp()))]
    h.tick("cto")
    assert len(respawns(h)) == 1
    h.advance(5)
    h.fake.clients.clear()
    h.tick("cto")
    assert len(respawns(h)) == 2


def tmux_with(answers: dict[str, subprocess.CompletedProcess]) -> cg.Tmux:
    return cg.Tmux(run=lambda argv: answers[argv[0] if argv[0] == "cat" else argv[2]])


def ok(stdout: str, rc: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], rc, stdout, "")


def test_agent_scope_is_the_unit_under_lu_driver_slice_even_from_a_sub_cgroup() -> None:
    assert tmux_with({"cat": ok(CGROUP)}).agent_scope("200@x") == SCOPE
    direct = CGROUP.replace("/tools", "")
    assert tmux_with({"cat": ok(direct)}).agent_scope("200@x") == SCOPE


@pytest.mark.parametrize(
    "line",
    [
        "0::/user.slice/user-1000.slice/session-3.scope\n",
        "0::/user.slice/user-1000.slice/user@1000.service/lu.slice/lu-dispatch.slice/lu-dispatch-x.scope\n",
        "0::/user.slice/user-1000.slice/user@1000.service/lu.slice/lu-driver.slice/lu-driver-x.service\n",
        "1:name=systemd:/user.slice\n",
    ],
)
def test_agent_outside_a_driver_scope_has_none(line: str) -> None:
    assert tmux_with({"cat": ok(line)}).agent_scope("200@x") is None


def test_unreadable_agent_cgroup_is_unknown() -> None:
    with pytest.raises(cg.TelemetryUnavailable):
        tmux_with({"cat": ok("", 1)}).agent_scope("200@x")


@pytest.mark.parametrize(("state", "active"), [("active", True), ("deactivating", True), ("inactive", False), ("failed", False)])
def test_scope_state_reads_systemctl_is_active(state: str, active: bool) -> None:
    assert tmux_with({"is-active": ok(state + "\n", 0 if active else 3)}).scope_active(SCOPE) is active


@pytest.mark.parametrize("answer", [ok("", 1), ok("unknown\n", 4), ok("Failed to connect to bus\n", 1)])
def test_unknown_scope_state_is_never_read_as_gone(answer: subprocess.CompletedProcess) -> None:
    with pytest.raises(cg.TelemetryUnavailable):
        tmux_with({"is-active": answer}).scope_active(SCOPE)


def test_process_exists_requires_the_same_start_time() -> None:
    rows = "1 0 Fri Oct 16 06:00:00 2026 systemd\n200 100 Fri Oct 16 11:00:00 2026 claude\n"
    tmux = cg.Tmux(run=lambda argv: ok(rows))
    start = dt.datetime(2026, 10, 16, 11, 0).isoformat()
    assert tmux.process_exists(f"200@{start}") is True
    assert tmux.process_exists("200@" + dt.datetime(2026, 10, 16, 11, 5).isoformat()) is False  # a reused pid
    assert tmux.process_exists(f"201@{start}") is False


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
    command = respawn[respawn.index("bash") :]
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


def test_codex_compactions_counted_from_session_record_not_percent_drops(tmp_path: Path) -> None:
    """Defect class: compactions missed when the context percent does not drop between ticks."""
    h = Harness(tmp_path, **{"harness": codex_pane(55)})
    h.tick("harness")
    assert h.fake.typed() == []
    h.compactions("harness", 9)
    h.advance(5)
    h.tick("harness")  # context refilled to the same percent between ticks
    assert h.state["harness"]["compactions"] == 9
    assert h.state["harness"]["phase"] == "handoff"
    assert len(h.fake.typed("harness")) == 1
    assert "HANDOFF NOW" in h.fake.typed("harness")[0]
    assert "compacted 9 times" in h.sent[0][1]


def test_codex_compactions_trigger_handoff(tmp_path: Path) -> None:
    h = Harness(tmp_path, **{"harness": codex_pane(60)})
    h.tick("harness")
    h.pane("harness").text = codex_text(20)  # a percent drop is not a compaction
    h.advance(5)
    h.tick("harness")
    assert h.state["harness"]["compactions"] == 0
    assert h.fake.typed() == []
    threshold = h.guard.setting("codex_max_compactions")
    path = h.compactions("harness", threshold)
    h.pane("harness").text = codex_text(20, "Compacting context")
    h.advance(5)
    h.tick("harness")
    assert h.state["harness"]["compactions"] == threshold
    assert h.fake.typed() == []
    path.write_text(path.read_text(encoding="utf-8") + '{"type":', encoding="utf-8")
    h.pane("harness").text = codex_text(20)
    h.advance(5)
    h.tick("harness")
    assert h.state["harness"]["compactions"] is None
    assert h.fake.typed() == [] and h.sent == []
    assert "compactions unknown" in h.logs[-1]
    h.compactions("harness", threshold)
    h.advance(5)
    h.tick("harness")
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
                (
                    "claude-devops",
                    "2026-10-16T12:06:00Z",
                    "status\nHANDOFF-DONE devops .claude/devops-epic/DRIVER-STATE.md",
                ),
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


@pytest.mark.parametrize(
    ("scenario", "sessions"),
    [
        ("next-tick", ("cto",)),
        ("same-tick", ("cto",)),
        ("delayed-dialog", ("cto",)),
        ("no-dialog", ("cto",)),
        ("no-dialog", ("infra-muse", "cto")),
        ("slow-capture", ("infra-muse", "cto")),
        ("agent-gone", ("cto",)),
        ("human-active", ("cto",)),
        ("client-unknown", ("cto",)),
        ("agent-replaced", ("cto",)),
        ("snapshot-unknown", ("cto",)),
        ("capture-unknown", ("cto",)),
    ],
)
def test_exit_dialog_is_answered_with_exit_and_stop_tasks(
    tmp_path: Path, scenario: str, sessions: tuple[str, ...]
) -> None:
    """Defect class: exit polling multiplies lane delays, waits after exit or bypasses a safety guard."""
    h = Harness(tmp_path, **{session: claude_pane(70) for session in sessions})
    h.tick(*sessions)
    dialog = claude_text(71, "1. Exit and stop tasks", "2. Move to background and exit")
    waits: list[float] = []
    elapsed = 0.0
    h.guard.tmux.monotonic = lambda: elapsed
    if scenario != "next-tick":
        for session in sessions:
            h.pane(session).text = claude_text(71, "⏺ HANDOFF-DONE cto .claude/epics-epic/DRIVER-STATE.md")

        def wait(seconds: float) -> None:
            nonlocal elapsed
            waits.append(seconds)
            elapsed += seconds

        h.guard.tmux.sleep = wait

        def show_dialog() -> None:
            h.pane("cto").text = dialog
            if scenario == "human-active":
                h.fake.clients = [("cto", int(h.moment.timestamp()))]
            elif scenario == "client-unknown":
                h.fake.override["list-clients"] = subprocess.CompletedProcess([], 1, "", "clients unavailable")
            elif scenario == "agent-replaced":
                h.pane("cto").agent_pid = "201"
            elif scenario == "snapshot-unknown":
                h.fake.override["ps"] = subprocess.CompletedProcess([], 1, "", "ps unavailable")
            elif scenario == "capture-unknown":
                h.fake.override["capture-pane"] = subprocess.CompletedProcess([], 1, "", "capture unavailable")

        if scenario == "slow-capture":

            def slow_capture() -> None:
                nonlocal elapsed
                elapsed += 10
                h.pane(sessions[0]).text = dialog

            before_call(h.guard.tmux, "capture-pane", slow_capture, nth=2)
        elif scenario == "agent-gone":
            before_call(h.guard.tmux, "ps", lambda: setattr(h.pane("cto"), "agent", None), nth=3)
        elif scenario != "no-dialog":
            before_call(h.guard.tmux, "capture-pane", show_dialog, nth=4 if scenario == "delayed-dialog" else 2)
    else:
        h.pane("cto").text = dialog
    h.advance(5)
    h.tick(*sessions)
    answered = scenario in {"next-tick", "same-tick", "delayed-dialog"}
    expected = [] if scenario == "next-tick" else ["/exit"]
    for session in sessions:
        assert h.fake.typed(session)[1:] == [*expected, *(["1"] if answered else [])]
    if answered:
        assert h.logs[-1] == "cto handoff ctx_pct=71: exit dialog -> chose Exit and stop tasks"
    if scenario != "next-tick":
        # Each command submission sleeps once; only the additional polling shares ten seconds.
        poll_wait = sum(waits) - len(sessions) - int(answered)
        assert 0 <= poll_wait <= 10
        if scenario == "agent-gone":
            assert poll_wait == 0
        elif scenario == "slow-capture":
            assert poll_wait == 1
            h.tick(*sessions)
            assert h.fake.typed(sessions[0])[-1] == "1"  # budget spent: answer on the next tick


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
    """Run ``change`` right before the ``nth`` ``command`` call (``ps``, ``cat``, ``systemctl`` or a tmux command) from now on."""
    run, seen = tmux.run, [0]

    def wrapped(argv: list[str]) -> subprocess.CompletedProcess:
        if (argv[1] if argv[0] == "tmux" else ("ps" if "ps" in argv[:3] else argv[0])) == command:
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
