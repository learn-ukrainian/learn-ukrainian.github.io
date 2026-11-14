"""Muse launcher admission after MUSE-RETIRE-1112: the retired Wonder pin refuses, with no provider/model calls."""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from tests.launcher_sandbox import launcher_environment

REPO = Path(__file__).resolve().parents[1]
CORE = REPO / "scripts/lib/launcher_core.sh"
ADAPTER = REPO / "scripts/launchers/muse.sh"
pytestmark = pytest.mark.usefixtures("hermetic_monitor")


@pytest.fixture
def muse_env(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name, body in {
        "muse": 'printf "muse-started\\n" >> "$MUSE_TEST_CALLS"; exit 99',
        "gh": (
            '[ "${MUSE_TEST_GH_RC:-0}" = 0 ] || exit "$MUSE_TEST_GH_RC"\n'
            '[ -z "${GH_REPO:-}${GITHUB_REPOSITORY:-}" ] || exit 98\n'
            '[ "$*" = "repo view --json visibility --jq .visibility" ] || exit 97\n'
            'printf "%s\\n" "${MUSE_TEST_VISIBILITY:-PUBLIC}"'
        ),
    }.items():
        binary = bindir / name
        binary.write_text(f"#!/bin/bash\n{body}\n")
        binary.chmod(0o755)
    env = launcher_environment()
    env.update(
        PATH=f"{bindir}:{os.defpath}",
        AGENT_ORIGINAL_PATH=f"{bindir}:{os.defpath}",
        AGENT_REAL_GH=str(bindir / "gh"),
        MUSE_TEST_CALLS=str(tmp_path / "muse-calls"),
    )
    return env


def launch(env: dict[str, str], *args: str, dry: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(REPO / "start-muse-driver.sh"), *args],
        cwd=REPO,
        env={**env, "LAUNCHER_DRY_RUN": "1" if dry else "0"},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert not Path(env["MUSE_TEST_CALLS"]).exists(), "admission/dry-run started the Muse binary"
    return result


class LauncherGroup:
    """A launcher started as its own process-group leader, with its output drained.

    The Muse provider stub is a looping bash child of the launcher. Killing only
    the launcher (the old ``process.kill()`` / ``subprocess.run`` timeout path)
    orphans that loop, and it then runs forever, so teardown SIGKILLs the whole
    group (#10779).

    The leader is never reaped before the group signal: a zombie leader keeps its
    pid, and so the process-group id, reserved. Exit is observed with
    ``waitid(WNOWAIT)``, never ``poll``/``wait``/``communicate``, so ``killpg``
    can never reach an unrelated group that reused the id.
    """

    def __init__(self, argv: list[str], *, cwd: Path, env: dict[str, str]) -> None:
        self.argv = argv
        self.process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        self.pid = self.process.pid
        self._chunks: dict[str, list[str]] = {"stdout": [], "stderr": []}
        self._readers = [
            threading.Thread(target=self._drain, args=(stream, self._chunks[name]), daemon=True)
            for name, stream in (("stdout", self.process.stdout), ("stderr", self.process.stderr))
        ]
        for reader in self._readers:
            reader.start()
        self._result: subprocess.CompletedProcess[str] | None = None

    @staticmethod
    def _drain(stream: Any, sink: list[str]) -> None:
        with stream:
            sink.append(stream.read())

    def exited(self) -> bool:
        """True once the leader has exited; it stays an unreaped zombie."""
        assert self.process.returncode is None, "launcher leader was reaped before its group was signalled"
        return os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOWAIT | os.WNOHANG) is not None

    def signal_leader(self, sig: int) -> None:
        """Signal only the leader; it is unreaped, so its pid is still ours."""
        assert self.process.returncode is None, "launcher leader was reaped before it was signalled"
        os.kill(self.pid, sig)

    def wait_done(self, timeout: float) -> bool:
        """Wait for leader exit and output EOF (like ``communicate``) without reaping."""
        deadline = time.monotonic() + timeout
        while not self.exited():
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.02)
        for reader in self._readers:
            reader.join(max(0.0, deadline - time.monotonic()))
        return not any(reader.is_alive() for reader in self._readers)

    def reap(self, *, timeout: float = 10.0) -> subprocess.CompletedProcess[str]:
        """SIGKILL the group while the leader is unreaped, prove it empty, then reap the leader."""
        if self._result is not None:
            return self._result
        survivors: list[int] = []
        try:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(self.pid, signal.SIGKILL)
            deadline = time.monotonic() + timeout
            while (not self.exited() or live_group_members(self.pid)) and time.monotonic() < deadline:
                time.sleep(0.05)
            # Checked before the reap below, while the zombie leader still reserves the id.
            survivors = live_group_members(self.pid)
        finally:
            self.process.wait(timeout=timeout)
            for reader in self._readers:
                reader.join(timeout)
            self._result = subprocess.CompletedProcess(
                self.argv, self.process.returncode, "".join(self._chunks["stdout"]), "".join(self._chunks["stderr"])
            )
        assert not survivors, f"launcher stub processes survived teardown: {survivors}"
        return self._result

    def finish(self, timeout: float) -> subprocess.CompletedProcess[str]:
        """``communicate`` for a launcher group: wait, reap the group, raise on timeout."""
        done = self.wait_done(timeout)
        result = self.reap()
        if not done:
            raise subprocess.TimeoutExpired(self.argv, timeout, result.stdout, result.stderr)
        return result

    def wait_for_readiness(self, ready_paths: list[Path], *, timeout: float = 60) -> None:
        """``_wait_for_launcher_readiness`` without ``poll()``, which would reap the leader."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if all(path.is_file() for path in ready_paths):
                return
            if self.exited():
                break
            time.sleep(0.05)
        result = self.reap()
        missing = ", ".join(os.fspath(path) for path in ready_paths if not path.is_file())
        pytest.fail(
            f"timed out waiting for launcher readiness (missing {missing}, rc={result.returncode}):\n"
            f"{result.stdout}{result.stderr}"
        )


def start_launcher_group(argv: list[str], *, cwd: Path, env: dict[str, str]) -> LauncherGroup:
    """Start a launcher as its own process-group leader so teardown can reap its stubs."""
    return LauncherGroup(argv, cwd=cwd, env=env)


def live_group_members(pgid: int) -> list[int]:
    """Pids of non-zombie processes still in process group ``pgid`` (Linux /proc)."""
    members = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
        except (OSError, IndexError):
            continue
        # fields: state, ppid, pgrp, ...
        if fields[0] != "Z" and int(fields[2]) == pgid:
            members.append(int(entry.name))
    return members


def run_launcher(
    argv: list[str], *, cwd: Path, env: dict[str, str], timeout: float = 60
) -> subprocess.CompletedProcess[str]:
    """``subprocess.run`` for a launcher whose stub children must not outlive the test."""
    return start_launcher_group(argv, cwd=cwd, env=env).finish(timeout)


_LOOPING_STUB = "while :; do sleep 0.1; done"


def _pid_running(pid: int) -> bool:
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return False


def _wait_for_pid_file(path: Path) -> int:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if path.is_file() and path.read_text().strip():
            return int(path.read_text())
        time.sleep(0.02)
    pytest.fail(f"stub never published its pid at {path}")


def test_killing_only_the_launcher_orphans_the_stub_and_group_reap_removes_it(tmp_path: Path) -> None:
    # The old teardown (killing only the launcher) is the leak premise; LauncherGroup.reap is the fix.
    pid_file = tmp_path / "stub.pid"
    group = start_launcher_group(
        ["bash", "-c", f'bash -c \'echo $$ > "$1"; {_LOOPING_STUB}\' stub "$1" & wait', "launcher", str(pid_file)],
        cwd=tmp_path,
        env=launcher_environment(),
    )
    try:
        stub_pid = _wait_for_pid_file(pid_file)
        group.signal_leader(signal.SIGKILL)
        deadline = time.monotonic() + 10
        while not group.exited() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert group.exited()
        assert _pid_running(stub_pid), "premise: killing only the launcher must orphan the looping stub"
    finally:
        group.reap()
    assert not _pid_running(stub_pid)
    assert live_group_members(group.pid) == []


@pytest.fixture
def signal_reap_order(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int, bool]]:
    """Record group signals and leader reaps, with whether the id was still reserved when signalled."""
    events: list[tuple[str, int, bool]] = []
    real_killpg, real_waitpid = os.killpg, os.waitpid

    def spy_killpg(pgid: int, sig: int) -> None:
        events.append(("killpg", pgid, Path(f"/proc/{pgid}").exists()))
        real_killpg(pgid, sig)

    def spy_waitpid(pid: int, options: int) -> tuple[int, int]:
        result = real_waitpid(pid, options)
        if result[0] == pid and pid > 0:
            events.append(("reaped", pid, True))
        return result

    monkeypatch.setattr(os, "killpg", spy_killpg)
    monkeypatch.setattr(os, "waitpid", spy_waitpid)
    return events


def _assert_signalled_before_reaped(events: list[tuple[str, int, bool]], pid: int) -> None:
    mine = [event for event in events if event[1] == pid]
    kinds = [kind for kind, _pid, _reserved in mine]
    assert "killpg" in kinds and "reaped" in kinds, mine
    assert kinds.index("killpg") < kinds.index("reaped"), f"group signalled after the leader was reaped: {mine}"
    assert all(reserved for kind, _pid, reserved in mine if kind == "killpg"), mine


def test_run_launcher_signals_the_group_before_reaping_the_leader(
    tmp_path: Path, signal_reap_order: list[tuple[str, int, bool]]
) -> None:
    result = run_launcher(["bash", "-c", "exit 3"], cwd=tmp_path, env=launcher_environment())

    assert result.returncode == 3
    reaped = {pid for kind, pid, _reserved in signal_reap_order if kind == "reaped"}
    assert len(reaped) == 1, signal_reap_order
    _assert_signalled_before_reaped(signal_reap_order, reaped.pop())


def test_run_launcher_timeout_reaps_the_group_and_raises(tmp_path: Path) -> None:
    pid_file = tmp_path / "stub.pid"
    with pytest.raises(subprocess.TimeoutExpired):
        run_launcher(
            ["bash", "-c", f'echo $$ > "$1"; {_LOOPING_STUB}', "launcher", str(pid_file)],
            cwd=tmp_path,
            env=launcher_environment(),
            timeout=1,
        )
    assert not _pid_running(_wait_for_pid_file(pid_file))


def test_help_needs_no_provider_or_visibility_probe(muse_env: dict[str, str]) -> None:
    result = launch({**muse_env, "MUSE_TEST_GH_RC": "1"}, "--help", dry=False)
    assert result.returncode == 0, result.stderr
    for expected in ("Usage: ./start-muse-driver.sh", "muse-wonder-full-1.0", "--effort", "--dry-run", "EXIT CODES:"):
        assert expected in result.stdout
    assert "--force" not in result.stdout
    assert "Unproven guards: shell, credential, publish, destructive-command, filesystem." in result.stdout


RETIRED_MODEL = "model 'muse-wonder-full-1.0' is retired in the model catalog"
SELECTORS = ["devops", "infra.devops", "monitor", "infra.monitor", "ops-api", "ops.api", "operator-api"]


@pytest.mark.parametrize("selector", SELECTORS)
@pytest.mark.parametrize("dry", [True, False])
@pytest.mark.parametrize(
    "model_args",
    [[], ["--model", "muse-wonder-full-1.0"]],
    ids=["default-model", "explicit-model"],
)
def test_retired_model_refuses_before_lease_or_provider(
    muse_env: dict[str, str],
    tmp_path: Path,
    selector: str,
    dry: bool,
    model_args: list[str],
) -> None:
    """MUSE-RETIRE-1112: the retired Wonder pin stops the launch before any lease, canary or provider work."""
    argv_path = tmp_path / "argv"
    result = launch(
        {**muse_env, "LAUNCHER_DRY_RUN_ARGV_FILE": str(argv_path)},
        "--epic",
        selector,
        *model_args,
        "--",
        "A bounded task",
        dry=dry,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert RETIRED_MODEL in result.stderr
    assert not argv_path.exists()
    assert "would claim" not in result.stdout
    assert "would exec" not in result.stdout


@pytest.mark.parametrize("selector", SELECTORS)
def test_retired_model_never_calls_lease_or_provider_boundaries(
    muse_env: dict[str, str],
    tmp_path: Path,
    selector: str,
) -> None:
    events = tmp_path / "forbidden-events"
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; '
            "for boundary in claim_session_supervisor_env launcher_driver_renew_loop launcher_close_driver_lease launcher_exec_command; do "
            r'eval "$boundary() { printf forbidden >> \"\$MUSE_TEST_EVENTS\"; return 99; }"; '
            'done; launcher_main muse driver --epic "$2" --dry-run',
            "bash",
            str(CORE),
            selector,
        ],
        cwd=REPO,
        env={**muse_env, "MUSE_TEST_EVENTS": str(events), "META_API_KEY": "authentication-must-stay-hidden"},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert RETIRED_MODEL in result.stderr
    assert not events.exists()
    assert not Path(muse_env["MUSE_TEST_CALLS"]).exists()
    assert "authentication-must-stay-hidden" not in result.stdout + result.stderr


@pytest.mark.parametrize("lane", ["devops", "monitor"])
@pytest.mark.parametrize("dry", [True, False])
@pytest.mark.parametrize(
    ("args", "override", "code", "reason"),
    [
        (["--model", "unknown"], {}, 4, "MUSE_MODEL_UNCERTIFIED"),
        (["--model", "muse-spark-1.3"], {}, 4, "MUSE_MODEL_UNCERTIFIED"),
        ([], {"LAUNCHER_MODEL": "muse-spark-1.3"}, 4, "MUSE_MODEL_UNCERTIFIED"),
        (["--model", "claude-fable-5"], {}, 4, "MUSE_MODEL_UNCERTIFIED"),
        (["--model="], {}, 4, "MUSE_MODEL_UNCERTIFIED"),
        ([], {"LAUNCHER_MODEL": "unknown"}, 4, "MUSE_MODEL_UNCERTIFIED"),
        (["--effort", "bogus"], {}, 2, "MUSE_EFFORT_UNSUPPORTED"),
    ],
)
def test_typed_refusals_before_provider(
    muse_env: dict[str, str],
    args: list[str],
    override: dict[str, str],
    code: int,
    reason: str,
    dry: bool,
    lane: str,
) -> None:
    result = launch({**muse_env, **override}, "--epic", lane, *args, dry=dry)
    assert result.returncode == code, result.stdout + result.stderr
    assert reason in result.stderr
    assert "would exec" not in result.stdout
    assert "would claim" not in result.stdout


def test_direct_exec_seam_still_refuses(muse_env: dict[str, str]) -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; source "$2"; LC_DRY_RUN=0; launcher_adapter_exec',
            "bash",
            str(CORE),
            str(ADAPTER),
        ],
        cwd=REPO,
        env=muse_env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 4
    assert "MUSE_GUARD_PARITY_UNPROVEN" in result.stderr
    assert not Path(muse_env["MUSE_TEST_CALLS"]).exists()
