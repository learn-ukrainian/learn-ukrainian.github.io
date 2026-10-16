"""Hand driver lanes to a fresh session before their context grows too large (#10814).

Runs every 5 minutes from ``learn-ukrainian-context-guard.timer``. Lanes come from
``scripts/config/driver_lanes.json`` and are resolved by tmux session name.
Per lane (state in ``$XDG_STATE_HOME/learn-ukrainian/context-guard/``):

watch
    Claude lanes: the status line ``ctx: …K/…K (N%)`` reaches
    ``claude_handoff_pct``. Codex lanes: the session compacted
    ``codex_max_compactions`` times (a ``Context N% used`` drop of at least
    ``codex_drop_pct`` points between ticks). Either way the guard types
    ``HANDOFF NOW`` (and posts it to Fleet Comms) and enters ``handoff``. A
    lane that already printed or posted ``HANDOFF-DONE`` enters ``handoff``
    at once, done, so it does not idle until the next threshold.
handoff
    ``HANDOFF NOW`` is re-sent every ``handoff_renudge_seconds`` until
    ``HANDOFF-DONE`` arrives; once it has, and the pane is idle, the guard types
    ``/exit`` (Claude) or ``/quit`` (Codex) and retries it every
    ``quit_retry_seconds``. When the agent and its launcher have exited, the pane is respawned with
    the lane's launcher (fresh session; it reads its goal file). The guard
    never kills a driver; it alerts ``epics`` once after
    ``handoff_alert_seconds``.

``HANDOFF-DONE`` counts only as a standalone response line, never as the echo
of the guard's own prompt. ``ctx_pct`` is logged on every tick in both phases.
No input is typed while a human typed into that tmux session within
``human_active_seconds``. Keep-alive tools skip lanes listed by the
``handoff-sessions`` subcommand.

Unknown never acts. Pane or process telemetry that fails, times out or does not
parse makes the tick log and retry; it never types, exits or respawns.
Unreadable client telemetry counts as a human present. Each tick reads the pane
pid, the process table once, and the pane pid again; a pane replaced in between,
or a pane pid absent from the table, is unknown. The pane's shell and its agent
are each identified by pid and start time from that one table; a different pane
or agent in a lane in ``handoff`` (for example a human relaunch) is a new
session, so the lane returns to ``watch`` with fresh timers before any further
input. Right before ``respawn-pane -k`` and before typing ``1`` at the exit
dialog or ``/exit``/``/quit``, the guard takes a fresh snapshot and acts only if
it equals the tick's. Residual (owner: Infra): tmux has no compare-and-swap, so a
pane or agent replaced after that re-check and before the tmux call itself
(about one second while text is typed) is not detected.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.readonly_sqlite import open_readonly
from scripts.ops.driver_lanes import (
    Lane,
    LaneConfigError,
    Registry,
    default_local_config_path,
    launch_plan,
    load_local_config,
    load_registry,
)

STATE_ENV = "LU_CONTEXT_GUARD_STATE_DIR"
CAPTURE_LINES = 80
AGENT_COMMANDS = {"claude": "claude", "codex": "codex"}
CLAUDE_PCT_RE = re.compile(r"ctx: [0-9.]+K/[0-9.]+K \((\d+)%\)")
CODEX_PCT_RE = re.compile(r"Context (\d+)% used")
CLAUDE_BUSY_RE = re.compile(r"esc to interrupt|ing… \(")
# A response line, optionally behind the CLI's response bullet. The guard's own
# prompt quotes the token mid-sentence, so its echo never starts a line with it.
DONE_LINE_RE = re.compile(r"^\s*(?:[●⏺•✦]\s*)?HANDOFF-DONE(?=\s|:|$)")
EXIT_DIALOG = ("Move to background and exit", "Exit and stop tasks")
# lstart is five words (``Fri Oct 16 12:10:40 2026``) only in the C locale; comm stays last.
PS_ARGV = ["env", "LC_ALL=C", "ps", "-eo", "pid=,ppid=,lstart=,comm="]
LSTART_FORMAT = "%a %b %d %H:%M:%S %Y"


class TelemetryUnavailable(RuntimeError):
    """Pane or process telemetry failed, timed out, did not parse or was inconsistent: the state is unknown."""


@dataclass(frozen=True)
class PaneSnapshot:
    """A pane and the processes under it, from one process-table read.

    ``pane`` is ``<pid>@<start time>`` of the pane's shell (``PANE_SCRIPT`` ends in
    ``exec bash``, so it outlives the launcher); ``agent`` is the same for the first
    process named after the lane's agent under that shell, or None; ``busy`` is true
    while anything runs under the shell.
    """

    pane: str
    agent: str | None
    busy: bool


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC).replace(microsecond=0)


def iso(moment: dt.datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def done_lines(text: str) -> int:
    """Count standalone HANDOFF-DONE response lines."""
    return sum(1 for line in text.splitlines() if DONE_LINE_RE.match(line))


def context_pct(kind: str, text: str) -> int | None:
    found = (CLAUDE_PCT_RE if kind == "claude" else CODEX_PCT_RE).findall(text)
    return int(found[-1]) if found else None


Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]


def default_runner(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, timeout=30, check=False)


@dataclass
class Tmux:
    """The tmux and process-table calls the guard and the relaunch need."""

    run: Runner = default_runner
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.time

    def tmux(self, *args: str) -> subprocess.CompletedProcess[str]:
        return self.run(["tmux", *args])

    def session_exists(self, session: str) -> bool:
        return self.tmux("has-session", "-t", f"={session}").returncode == 0

    def _query(self, argv: list[str], what: str) -> str:
        """Run a telemetry command; any failure raises ``TelemetryUnavailable``."""
        try:
            result = self.run(argv)
        except (subprocess.SubprocessError, OSError) as exc:
            raise TelemetryUnavailable(f"{what}: {type(exc).__name__}") from exc
        if result.returncode != 0:
            raise TelemetryUnavailable(f"{what}: rc={result.returncode} {(result.stderr or '').strip()[-120:]}")
        return result.stdout or ""

    def capture(self, target: str) -> str:
        return self._query(["tmux", "capture-pane", "-p", "-J", "-S", f"-{CAPTURE_LINES}", "-t", target], "capture-pane")

    def pane_pid(self, target: str) -> str:
        pid = self._query(["tmux", "display-message", "-p", "-t", target, "#{pane_pid}"], "pane pid").strip()
        if not pid.isdigit():
            raise TelemetryUnavailable(f"pane pid: unparseable {pid[:40]!r}")
        return pid

    def _process_table(self) -> tuple[dict[str, str], dict[str, list[tuple[str, str, str]]]]:
        """One read of the whole process table: pid -> start time, and parent pid -> [(pid, start time, comm)]."""
        rows = self._query(PS_ARGV, "process table").splitlines()
        if not rows:
            raise TelemetryUnavailable("process table: empty")
        starts: dict[str, str] = {}
        children: dict[str, list[tuple[str, str, str]]] = {}
        for row in rows:
            parts = row.split(None, 7)
            try:
                if len(parts) != 8 or not (parts[0].isdigit() and parts[1].isdigit()):
                    raise ValueError(row)
                start = dt.datetime.strptime(" ".join(parts[2:7]), LSTART_FORMAT).isoformat()
            except ValueError as exc:
                raise TelemetryUnavailable(f"process table: unparseable row {row[:80]!r}") from exc
            starts[parts[0]] = start
            children.setdefault(parts[1], []).append((parts[0], start, parts[7].strip()))
        return starts, children

    def snapshot(self, target: str, command: str) -> PaneSnapshot:
        """One consistent view of the pane: its pid, then the process table once, then its pid again.

        A pane replaced between the reads, or a pane pid missing from the table,
        raises ``TelemetryUnavailable``; it is never read as "nothing running".
        The agent and "anything running" both come from the one table.
        """
        pid = self.pane_pid(target)
        starts, children = self._process_table()
        again = self.pane_pid(target)
        if again != pid:
            raise TelemetryUnavailable(f"pane pid changed {pid} -> {again} while reading the process table")
        if pid not in starts:
            raise TelemetryUnavailable(f"pane pid {pid} not in the process table")
        agent = None
        stack = [pid]
        while stack and agent is None:
            for child, start, comm in children.get(stack.pop(), []):
                if comm == command:
                    agent = f"{child}@{start}"
                    break
                stack.append(child)
        return PaneSnapshot(pane=f"{pid}@{starts[pid]}", agent=agent, busy=bool(children.get(pid)))

    def human_activity(self, session: str, window_s: int) -> str | None:
        """Why a human may be using ``session``, or None when no client of it had input within ``window_s``.

        Failed or unparseable client telemetry counts as a human present (fail
        closed), except when no tmux server runs at all.
        """
        try:
            result = self.tmux("list-clients", "-F", "#{client_session}\t#{client_activity}")
        except (subprocess.SubprocessError, OSError) as exc:
            return f"client telemetry unavailable ({type(exc).__name__})"
        if result.returncode != 0:
            if "no server running" in (result.stderr or ""):
                return None
            return f"client telemetry unavailable (rc={result.returncode})"
        now = self.clock()
        for row in (result.stdout or "").splitlines():
            name, tab, activity = row.rpartition("\t")
            if not tab or not activity.isdigit():
                return f"client telemetry unparseable ({row[:60]!r})"
            if name == session and now - int(activity) < window_s:
                return f"input {int(now - int(activity))}s ago"
        return None

    def type_into(self, target: str, text: str) -> None:
        self.tmux("send-keys", "-t", target, "-l", text)
        self.sleep(1)
        self.tmux("send-keys", "-t", target, "Enter")


@dataclass
class Guard:
    registry: Registry
    repo_root: Path
    tmux: Tmux
    log: Callable[[str], None]
    send: Callable[[str, str, str], None]
    handoff_posted: Callable[[str, str], bool]
    local: dict[str, dict[str, Any]] = field(default_factory=dict)
    now: Callable[[], dt.datetime] = utcnow

    def setting(self, key: str) -> int:
        return self.registry.settings[key]

    # ---- helpers -------------------------------------------------------
    def _prompt(self, lane: Lane, reason: str, reminder: int) -> str:
        again = f"reminder {reminder}, " if reminder > 1 else ""
        return (
            f"HANDOFF NOW ({again}CTO automated, {iso(self.now())}): {reason} Finish the current step only, "
            f"write the top of {lane.goal} (in-flight workers with task ids, waits with nonces, PRs, holds, "
            f"orders and their status, next actions), post 'HANDOFF-DONE {lane.name} {lane.goal}' to Fleet "
            "Comms recipient epics, then stop. The guard exits and relaunches your seat; running workers keep "
            "running and the fresh session adopts them."
        )

    def _reason(self, lane: Lane, s: dict[str, Any], pct: int | None) -> str:
        if lane.kind == "claude":
            return f"your context is {pct}% (hand off at {self.setting('claude_handoff_pct')}%)."
        return (
            f"this session has compacted {s.get('compactions', 0)} times; the operator wants a fresh "
            "session instead of an ever-growing history."
        )

    def _human(self, lane: Lane) -> bool:
        reason = self.tmux.human_activity(lane.session, self.setting("human_active_seconds"))
        if reason:
            self.log(f"{lane.name} deferred: human possibly active in session {lane.session} ({reason}); retry next tick")
            return True
        return False

    def _nudge(self, lane: Lane, s: dict[str, Any], pct: int | None) -> None:
        reminder = int(s.get("nudges", 0)) + 1
        body = self._prompt(lane, self._reason(lane, s, pct), reminder)
        self.tmux.type_into(lane.target, body)
        stamp = iso(self.now())
        self.send(lane.sender, body, f"{lane.kind}-handoff-{lane.name}-{stamp}")
        s.update(nudges=reminder, last_nudge=stamp)

    def _seconds_since(self, value: str | None) -> float:
        if not value:
            return float("inf")
        return (self.now() - parse_iso(value)).total_seconds()

    def _pane_done(self, s: dict[str, Any], marks: int, snap: PaneSnapshot) -> bool:
        """A new standalone HANDOFF-DONE line from the current agent process.

        The baseline is the lowest count seen for this agent in this pane, so lines
        from a previous session, or lines that scrolled out, never count as new.
        """
        if snap.agent is None or (s.get("agent_id"), s.get("pane_id")) != (snap.agent, snap.pane):
            s.update(agent_id=snap.agent, pane_id=snap.pane, done_marks=marks)
            return False
        baseline = min(int(s.get("done_marks", marks)), marks)
        s["done_marks"] = baseline
        return marks > baseline

    def _enter_handoff(self, s: dict[str, Any], pct: int | None, *, done: bool) -> None:
        s.update(
            phase="handoff",
            since=iso(self.now()),
            pct_at_trigger=pct,
            quit_sent=None,
            quit_attempts=0,
            alerted=False,
            done_seen=done,
            nudges=0,
            last_nudge=None,
        )

    def _unchanged(self, lane: Lane, snap: PaneSnapshot, action: str, pct: int | None) -> bool:
        """Re-read pane and process table right before ``action``; True only if they still match ``snap``.

        An unreadable re-check raises ``TelemetryUnavailable``, so nothing is done.
        tmux has no compare-and-swap, so a change after this read and before the
        tmux call itself (about one second while text is typed) stays possible.
        """
        now = self.tmux.snapshot(lane.target, AGENT_COMMANDS[lane.kind])
        if now == snap:
            return True
        self.log(
            f"{lane.name} handoff ctx_pct={pct}: pane changed before {action} (pane {snap.pane} -> {now.pane}, "
            f"agent {snap.agent} -> {now.agent}, busy {snap.busy} -> {now.busy}); nothing done, retry next tick"
        )
        return False

    # ---- one lane ------------------------------------------------------
    def tick(self, lane: Lane, st: dict[str, Any]) -> None:
        s = st.setdefault(lane.session, {"phase": "watch"})
        s.setdefault("watch_since", iso(self.now()))
        if not self.tmux.session_exists(lane.session):
            self.log(f"{lane.name} {s['phase']}: tmux session {lane.session} missing")
            return
        try:
            text = self.tmux.capture(lane.target)
            pct = context_pct(lane.kind, text)
            snap = self.tmux.snapshot(lane.target, AGENT_COMMANDS[lane.kind])
            if s["phase"] == "watch":
                self._watch(lane, s, text, pct, snap)
            else:
                self._handoff(lane, st, s, text, pct, snap)
        except TelemetryUnavailable as exc:
            self.log(f"{lane.name} {s['phase']}: telemetry unavailable ({exc}); no input or respawn, retry next tick")

    def _watch(self, lane: Lane, s: dict[str, Any], text: str, pct: int | None, snap: PaneSnapshot) -> None:
        if snap.agent is None:
            self.log(f"{lane.name} watch: agent not running in session {lane.session}")
            return
        if (s.get("agent_id"), s.get("pane_id")) != (snap.agent, snap.pane):
            # A new agent process (or pane) is a new session: earlier HANDOFF-DONE posts and compactions were
            # its predecessor's.
            s["watch_since"] = iso(self.now())
            s.pop("compactions", None)
            s.pop("last_pct", None)
        extra = ""
        if lane.kind == "codex":
            prev = s.get("last_pct")
            if pct is not None and prev is not None and prev - pct >= self.setting("codex_drop_pct"):
                s["compactions"] = int(s.get("compactions", 0)) + 1
            if pct is not None:
                s["last_pct"] = pct
            extra = f" compactions={s.get('compactions', 0)} compacting_now={'Compacting context' in text}"
        self.log(f"{lane.name} watch ctx_pct={pct}{extra}")
        pane_done = self._pane_done(s, done_lines(text), snap)
        if pane_done or self.handoff_posted(lane.sender, s["watch_since"]):
            self.log(f"{lane.name} watch: HANDOFF-DONE seen before the prompt -> handoff (done)")
            self._enter_handoff(s, pct, done=True)
            return
        if lane.kind == "claude":
            due = pct is not None and pct >= self.setting("claude_handoff_pct")
        else:
            due = s.get("compactions", 0) >= self.setting("codex_max_compactions") and "Compacting context" not in text
        if not due or self._human(lane):
            return
        self._enter_handoff(s, pct, done=False)
        self._nudge(lane, s, pct)
        self.log(f"{lane.name} watch -> handoff: HANDOFF NOW sent")

    def _idle(self, lane: Lane, text: str) -> bool:
        tail = "\n".join(text.splitlines()[-8:])
        if lane.kind == "claude":
            return CLAUDE_BUSY_RE.search(tail) is None
        return "Ready" in tail and "Working" not in tail

    def _handoff(
        self, lane: Lane, st: dict[str, Any], s: dict[str, Any], text: str, pct: int | None, snap: PaneSnapshot
    ) -> None:
        waited = int(self._seconds_since(s.get("since")))
        change = ""
        if s.get("pane_id") != snap.pane:
            change = f"pane changed {s.get('pane_id')} -> {snap.pane}"
        elif snap.agent is not None and s.get("agent_id") != snap.agent:
            change = f"agent changed {s.get('agent_id')} -> {snap.agent}"
        if change:
            # A different pane or agent (a human relaunch, or a reused pid with a new start time) is a new
            # session: its predecessor's HANDOFF-DONE, exit attempts, timers and relaunch must not reach it.
            self.log(f"{lane.name} handoff ctx_pct={pct}: {change}; handoff state reset -> watch")
            st[lane.session] = {
                **{key: s[key] for key in ("last_handoff", "last_pct_at_trigger") if key in s},
                "phase": "watch",
                "watch_since": iso(self.now()),
                "agent_id": snap.agent,
                "pane_id": snap.pane,
                "done_marks": done_lines(text),
            }
            return
        if snap.agent is None:
            if snap.busy:
                # Respawning now would kill the launcher's own exit path (lease release, handoff writes).
                self.log(f"{lane.name} handoff ctx_pct={pct}: agent gone, launcher still exiting; relaunch next tick")
                return
            self._relaunch(lane, st, s, pct, snap)
            return
        tail = "\n".join(text.splitlines()[-8:])
        if lane.kind == "claude" and any(marker in tail for marker in EXIT_DIALOG):
            # "Move to background" keeps a lease-holding fork alive; always "Exit and stop tasks".
            # Delegate workers are separate tasks and keep running.
            if not self._human(lane) and self._unchanged(lane, snap, "the exit-dialog answer", pct):
                self.tmux.type_into(lane.target, "1")
                self.log(f"{lane.name} handoff ctx_pct={pct}: exit dialog -> chose Exit and stop tasks")
            return
        pane_done = self._pane_done(s, done_lines(text), snap)
        done = bool(s.get("done_seen")) or pane_done or self.handoff_posted(lane.sender, s["since"])
        s["done_seen"] = done
        idle = self._idle(lane, text)
        quit_due = not s.get("quit_sent") or self._seconds_since(s.get("quit_sent")) >= self.setting(
            "quit_retry_seconds"
        )
        if done and idle and quit_due and not self._human(lane):
            command = "/exit" if lane.kind == "claude" else "/quit"
            if not self._unchanged(lane, snap, command, pct):
                return
            self.tmux.type_into(lane.target, command)
            s["quit_sent"] = iso(self.now())
            s["quit_attempts"] = int(s.get("quit_attempts", 0)) + 1
            self.log(
                f"{lane.name} handoff ctx_pct={pct}: HANDOFF-DONE seen, pane idle -> {command} sent "
                f"(attempt {s['quit_attempts']})"
            )
            return
        renudge_due = self._seconds_since(s.get("last_nudge")) >= self.setting("handoff_renudge_seconds")
        if not done and renudge_due and not self._human(lane):
            self._nudge(lane, s, pct)
            self.log(f"{lane.name} handoff ctx_pct={pct}: HANDOFF NOW re-sent (reminder {s['nudges']})")
            return
        self.log(
            f"{lane.name} handoff ctx_pct={pct} waited={waited}s done={done} idle={idle} "
            f"quit_sent={s.get('quit_sent')} nudges={s.get('nudges', 0)}"
        )
        if waited > self.setting("handoff_alert_seconds") and not s.get("alerted"):
            self.send(
                "epics",
                f"CTO-ALERT {iso(self.now())}: {lane.name} driver still running {waited}s after HANDOFF NOW; "
                f"no forced kill. Check tmux session {lane.session}",
                f"handoff-alert-{lane.name}-{iso(self.now())}",
            )
            s["alerted"] = True

    def _relaunch(self, lane: Lane, st: dict[str, Any], s: dict[str, Any], pct: int | None, snap: PaneSnapshot) -> None:
        if self._human(lane):
            return
        try:
            plan = launch_plan(lane, repo_root=self.repo_root, local=self.local)
        except LaneConfigError as exc:
            self.log(f"{lane.name} relaunch refused ctx_pct={pct}: {exc}; pane left as is, retry next tick")
            return
        if not self._unchanged(lane, snap, "respawn-pane -k", pct):
            return
        env_args = [arg for key, value in sorted(plan.env.items()) for arg in ("-e", f"{key}={value}")]
        result = self.tmux.tmux("respawn-pane", "-k", "-t", lane.target, "-c", plan.cwd, *env_args, *plan.pane_argv())
        # Clear the old session's scrollback so its HANDOFF-DONE line cannot end the fresh session.
        self.tmux.tmux("clear-history", "-t", lane.target)
        self.log(
            f"{lane.name} relaunch ctx_pct={pct}: respawn-pane rc={result.returncode} "
            f"source={'local-wrapper' if plan.wrapper else 'generic'} {(result.stderr or '').strip()[-200:]}"
        )
        stamp = iso(self.now())
        st[lane.session] = {
            "phase": "watch",
            "watch_since": stamp,
            "last_handoff": stamp,
            "last_pct_at_trigger": s.get("pct_at_trigger"),
        }

    def run(self, st: dict[str, Any], only: list[str] | None = None) -> None:
        for lane in self.registry.lanes:
            if only and lane.session not in only and lane.name not in only:
                continue
            try:
                self.tick(lane, st)
            except Exception as exc:  # one lane must not block the others
                self.log(f"{lane.name} error {type(exc).__name__}: {exc}")


# ---- state, log, Fleet Comms ------------------------------------------------
def default_state_dir(environ: dict[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    if env.get(STATE_ENV):
        return Path(env[STATE_ENV])
    base = env.get("XDG_STATE_HOME") or str(Path(env.get("HOME", "~")).expanduser() / ".local" / "state")
    return Path(base) / "learn-ukrainian" / "context-guard"


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(path: Path, state: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def sessions_in_handoff(state: dict[str, Any]) -> list[str]:
    """Sessions in the handoff phase; keep-alive nudges must skip them."""
    return sorted(name for name, s in state.items() if isinstance(s, dict) and s.get("phase") == "handoff")


def file_logger(path: Path) -> Callable[[str], None]:
    def log(message: str) -> None:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"{iso(utcnow())} {message}\n")

    return log


def comms_reader(db: Path | None, log: Callable[[str], None]) -> Callable[[str, str], bool]:
    def handoff_posted(sender: str, since: str) -> bool:
        if db is None:
            return False
        # A lane may post as its codex-* or claude-* name.
        names = sorted({sender, sender.replace("codex-", "claude-", 1), sender.replace("claude-", "codex-", 1)})
        marks = ",".join("?" for _ in names)
        try:
            with contextlib.closing(open_readonly(db, timeout=10)) as con:
                rows = con.execute(
                    f"select body_inline from comms_messages where sender in ({marks}) and created_at>=? "
                    "and body_inline like '%HANDOFF-DONE%'",
                    (*names, since),
                ).fetchall()
        except sqlite3.Error as exc:
            log(f"comms read error {exc}")
            return False
        return any(done_lines(row[0] or "") for row in rows)

    return handoff_posted


def fleet_sender(identity: str, log: Callable[[str], None]) -> Callable[[str, str, str], None]:
    def send(recipient: str, body: str, key: str) -> None:
        try:
            from scripts.fleet_comms.authority import AuthorityService

            message_id = (
                AuthorityService(root=None)
                .enqueue_supervisory_request(
                    sender=identity, recipient=recipient, body=body, correlation_id=key, idempotency_key=key
                )
                .message_id
            )
            log(f"send {recipient} ok {message_id}")
        except Exception as exc:  # a Fleet outage must not stop the pane-side handoff
            log(f"send {recipient} failed {type(exc).__name__}: {exc}")

    return send


def comms_db(log: Callable[[str], None]) -> Path | None:
    """The Fleet Comms store of this checkout's plane (anchored at the primary checkout)."""
    try:
        from scripts.fleet_comms.paths import default_plane_root

        return default_plane_root(repo_root=REPO_ROOT) / "comms.sqlite3"
    except Exception as exc:  # the pane-side HANDOFF-DONE check still works without Fleet
        log(f"comms plane unresolved {type(exc).__name__}: {exc}")
        return None


@contextlib.contextmanager
def single_run(lock_path: Path) -> Iterator[bool]:
    with lock_path.open("a") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        yield True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Hand tmux driver lanes to a fresh session at the context threshold (one tick per run).\n"
            "Run from learn-ukrainian-context-guard.timer every 5 minutes; run by hand to check one lane."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ops.context_guard tick\n"
            "  .venv/bin/python scripts/ops/context_guard.py tick --lane infra-muse\n"
            "  .venv/bin/python -m scripts.ops.context_guard handoff-sessions\n"
            "Outputs: tick types into lane panes, posts to Fleet Comms, respawns exited lanes, and writes\n"
            "  state.json and guard.log under the state directory; handoff-sessions prints a JSON list.\n"
            "Exit codes: 0 done (or another tick holds the lock); 1 invalid lane data; 2 invalid arguments.\n"
            "Related: scripts/config/driver_lanes.json, packaging/systemd/learn-ukrainian-context-guard.timer,\n"
            "  docs/runbooks/maintenance-window.md, issue #10814."
        ),
    )
    parser.add_argument(
        "command",
        choices=("tick", "handoff-sessions"),
        help="tick: run one guard pass; handoff-sessions: print sessions in the handoff phase as JSON.",
    )
    parser.add_argument(
        "--lane",
        action="append",
        default=[],
        help="Limit tick to this session or lane name (repeatable; default: every lane), e.g. infra-muse.",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help=f"State and log directory (default: ${STATE_ENV} or $XDG_STATE_HOME/learn-ukrainian/context-guard).",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        help="Lane data file (default: scripts/config/driver_lanes.json).",
    )
    args = parser.parse_args(argv)
    state_dir = args.state_dir or default_state_dir()
    state_path = state_dir / "state.json"
    if args.command == "handoff-sessions":
        print(json.dumps(sessions_in_handoff(load_state(state_path))))
        return 0
    try:
        registry = load_registry(args.data)
        local = load_local_config(default_local_config_path())
    except LaneConfigError as exc:
        print(f"invalid lane data: {exc}", file=sys.stderr)
        return 1
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    log = file_logger(state_dir / "guard.log")
    with single_run(state_dir / "guard.lock") as acquired:
        if not acquired:
            log("skipped: another tick holds the lock")
            return 0
        state = load_state(state_path)
        guard = Guard(
            registry=registry,
            repo_root=REPO_ROOT,
            tmux=Tmux(),
            log=log,
            send=fleet_sender(registry.guard_sender, log),
            handoff_posted=comms_reader(comms_db(log), log),
            local=local,
        )
        guard.run(state, args.lane)
        save_state(state_path, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
