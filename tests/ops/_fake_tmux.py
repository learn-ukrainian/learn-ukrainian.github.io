"""A fake tmux/ps/systemd-run runner for the context guard and lane relaunch tests (#10814).

It answers the argv the code builds, records every call, and never runs a real
process, so no test touches a live tmux server or the user manager. ``override``
injects a failed, malformed or raising answer for one command.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

BOOT = "Fri Oct 16 06:00:00 2026"  # ps lstart (C locale) of long-running processes


@dataclass
class FakePane:
    text: str = ""
    pane_pid: str = "100"
    agent: str | None = None  # comm of the agent process under the pane, or None
    agent_pid: str = "200"
    agent_start: str = "Fri Oct 16 11:00:00 2026"
    launcher_running: bool = False  # a launcher still exiting after its agent quit


@dataclass
class FakeTmux:
    sessions: dict[str, FakePane] = field(default_factory=dict)
    clients: list[tuple[str, int]] = field(default_factory=list)
    server_running: bool = True
    exit_on_create: dict[str, int] = field(default_factory=dict)
    now: float = 1_000_000.0
    calls: list[list[str]] = field(default_factory=list)
    # Injected answers keyed by "ps" or a tmux command: a CompletedProcess to return, or an exception to raise.
    override: dict[str, subprocess.CompletedProcess | Exception] = field(default_factory=dict)

    def run(self, argv: list[str]) -> subprocess.CompletedProcess:
        self.calls.append(list(argv))
        if argv[0] == "systemd-run":
            argv = argv[argv.index("tmux"):]
        if argv[0] == "env":
            argv = argv[argv.index("ps"):]
        key = argv[0] if argv[0] == "ps" else argv[1]
        if key in self.override:
            injected = self.override[key]
            if isinstance(injected, Exception):
                raise injected
            return injected
        if argv[0] == "ps":
            return self._ok("\n".join(self._ps_rows(with_start="lstart" in argv[-1])))
        assert argv[0] == "tmux", argv
        command, args = argv[1], argv[2:]
        target = args[args.index("-t") + 1] if "-t" in args else None
        session = target.strip("=").split(":")[0] if target else ""
        pane_commands = {"has-session", "capture-pane", "display-message", "send-keys", "respawn-pane", "clear-history"}
        if command in pane_commands and session not in self.sessions:
            return self._fail(f"can't find session: {session}")
        if command == "has-session":
            return self._ok("")
        if command == "list-sessions":
            if not self.server_running or not self.sessions:
                return self._fail("no server running on /fake/socket")
            return self._ok("\n".join(self.sessions))
        if command == "capture-pane":
            return self._ok(self.sessions[session].text)
        if command == "display-message":
            return self._ok(self.sessions[session].pane_pid + "\n")
        if command == "list-clients":
            if not self.server_running:
                return self._fail("no server running on /fake/socket")
            return self._ok("\n".join(f"{name}\t{activity}" for name, activity in self.clients))
        if command == "new-session":
            name = args[args.index("-s") + 1]
            self.server_running = True
            rc = self.exit_on_create.get(name)
            text = f"\nlane-relaunch: launcher exited rc={rc}\n" if rc is not None else "launcher running\n"
            self.sessions[name] = FakePane(text=text)
            return self._ok("")
        if command in {"send-keys", "respawn-pane", "clear-history"}:
            return self._ok("")
        raise AssertionError(f"unexpected tmux call {argv}")

    def _ps_rows(self, *, with_start: bool) -> list[str]:
        """``pid ppid [lstart] comm`` rows for the format the caller asked for, pid 1 included."""
        rows = [("1", "0", BOOT, "systemd")]
        for pane in self.sessions.values():
            if pane.agent:
                rows.append((pane.agent_pid, pane.pane_pid, pane.agent_start, pane.agent))
            if pane.launcher_running:
                rows.append(("300", pane.pane_pid, BOOT, "bash"))
        return [" ".join((pid, ppid, start, comm) if with_start else (pid, ppid, comm)) for pid, ppid, start, comm in rows]

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def clock(self) -> float:
        return self.now

    @staticmethod
    def _ok(stdout: str) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess([], 0, stdout, "")

    @staticmethod
    def _fail(stderr: str) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess([], 1, "", stderr)

    # ---- assertions helpers ----
    def typed(self, session: str | None = None) -> list[str]:
        out = []
        for call in self.calls:
            if call[:2] == ["tmux", "send-keys"] and "-l" in call:
                target = call[call.index("-t") + 1]
                if session is None or target == f"={session}:":
                    out.append(call[call.index("-l") + 1])
        return out

    def targets(self) -> list[str]:
        return [call[call.index("-t") + 1] for call in self.calls if "-t" in call]
