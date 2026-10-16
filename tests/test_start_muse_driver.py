"""Muse admission and shared lease lifecycle, with no provider/model calls."""

from __future__ import annotations

import contextlib
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from tests.test_launcher_contract import (
    _LAUNCHER_READY_TIMEOUT_S,
    _blocking_signal_provider,
    _core_driver_exit_fixture,
)

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
            "printf 'HTTP/2 200 OK\\r\\nContent-Type: application/json\\r\\n\\r\\n"
            '{"visibility":"%s"}\\n\' "${MUSE_TEST_VISIBILITY:-PUBLIC}"'
        ),
    }.items():
        binary = bindir / name
        binary.write_text(f"#!/bin/bash\n{body}\n")
        binary.chmod(0o755)
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("LAUNCHER_", "GIT_", "SESSION_", "LC_")) and key != "LU_RULES_SEAT"
    }
    env.update(
        PATH=f"{bindir}:{os.environ['PATH']}",
        AGENT_ORIGINAL_PATH=f"{bindir}:{os.environ['PATH']}",
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
        env=dict(os.environ),
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


def test_run_launcher_reaps_a_stub_that_outlives_the_launcher(tmp_path: Path) -> None:
    pid_file = tmp_path / "stub.pid"
    result = run_launcher(
        [
            "bash",
            "-c",
            # Exit only once the stub has published its pid, so it provably outlives the launcher.
            f'(echo $BASHPID > "$1"; {_LOOPING_STUB}) >/dev/null 2>&1 & while [ ! -s "$1" ]; do sleep 0.02; done; exit 3',
            "launcher",
            str(pid_file),
        ],
        cwd=tmp_path,
        env=dict(os.environ),
    )
    assert result.returncode == 3
    stub_pid = _wait_for_pid_file(pid_file)
    assert not _pid_running(stub_pid), "run_launcher teardown left the stub running"


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
    result = run_launcher(["bash", "-c", "exit 3"], cwd=tmp_path, env=dict(os.environ))

    assert result.returncode == 3
    reaped = {pid for kind, pid, _reserved in signal_reap_order if kind == "reaped"}
    assert len(reaped) == 1, signal_reap_order
    _assert_signalled_before_reaped(signal_reap_order, reaped.pop())


def test_teardown_of_a_running_launcher_signals_before_reaping(
    tmp_path: Path, signal_reap_order: list[tuple[str, int, bool]]
) -> None:
    group = start_launcher_group(["bash", "-c", _LOOPING_STUB], cwd=tmp_path, env=dict(os.environ))

    result = group.reap()

    assert result.returncode == -signal.SIGKILL
    _assert_signalled_before_reaped(signal_reap_order, group.pid)


def test_run_launcher_timeout_reaps_the_group_and_raises(tmp_path: Path) -> None:
    pid_file = tmp_path / "stub.pid"
    with pytest.raises(subprocess.TimeoutExpired):
        run_launcher(
            ["bash", "-c", f'echo $$ > "$1"; {_LOOPING_STUB}', "launcher", str(pid_file)],
            cwd=tmp_path,
            env=dict(os.environ),
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


@pytest.mark.parametrize(
    ("selector", "lane", "stream"),
    [
        ("devops", "devops", "epic:5703"),
        ("infra.devops", "devops", "epic:5703"),
        ("monitor", "monitor", "epic:7919"),
        ("infra.monitor", "monitor", "epic:7919"),
        ("ops-api", "monitor", "epic:7919"),
        ("ops.api", "monitor", "epic:7919"),
        ("operator-api", "monitor", "epic:7919"),
    ],
)
@pytest.mark.parametrize("effort", ["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"])
def test_dry_run_argv_and_capsule_binding(
    muse_env: dict[str, str],
    tmp_path: Path,
    selector: str,
    lane: str,
    stream: str,
    effort: str,
) -> None:
    # allow-hardcoded-epic: literal seven-selector contract independent of resolver
    argv_path = tmp_path / "argv"
    result = launch(
        {**muse_env, "LAUNCHER_DRY_RUN_ARGV_FILE": str(argv_path)},
        "--epic",
        selector,
        "--effort",
        effort,
        "--dry-run",
        "--",
        "A bounded task",
    )
    assert result.returncode == 0, result.stderr
    argv = argv_path.read_bytes().decode().rstrip("\0").split("\0")
    assert argv[:-1] == [
        "muse",
        "--provider",
        "meta",
        "--model",
        "muse-wonder-full-1.0",
        "--reasoning-effort",
        effort,
        "--workspace",
        str(REPO),
        "--worktree",
        "off",
        "--disable-shell",
        "--disable-write",
    ]
    assert argv[-1].startswith('<rules-core seat="core"')
    assert "A bounded task" in argv[-1]
    assert f"launcher already claimed the {lane} lease" in argv[-1]
    assert f"would claim lease stream={stream} agent=muse harness=muse-cli" in result.stdout
    assert f"slot=muse-{lane}" in result.stdout
    assert "provider canary: not run; rollover uses scripts.session_canary.muse_lane mint and score" in result.stdout
    assert "MUSE_GUARD_PARITY_UNPROVEN" in result.stdout


@pytest.mark.parametrize(
    "selector", ["devops", "infra.devops", "monitor", "infra.monitor", "ops-api", "ops.api", "operator-api"]
)
def test_dry_run_never_calls_lease_or_provider_boundaries(
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
    assert result.returncode == 0, result.stdout + result.stderr
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
        (["--epic", "folk"], {}, 4, "MUSE_UKRAINIAN_CONTENT_FORBIDDEN"),
        (["--epic", "bio"], {}, 4, "MUSE_UKRAINIAN_CONTENT_FORBIDDEN"),
        (["--epic", "hramatka"], {}, 4, "MUSE_UKRAINIAN_CONTENT_FORBIDDEN"),
        (["--epic", "open-model-data"], {}, 4, "MUSE_UKRAINIAN_CONTENT_FORBIDDEN"),
        (["--epic", "curriculum-upgrade"], {}, 4, "MUSE_CURRICULUM_CONTENT_FORBIDDEN"),
        (["--epic", "curriculum-upgrade"], {"LU_RULES_SEAT": "core"}, 4, "MUSE_CURRICULUM_CONTENT_FORBIDDEN"),
        ([], {"LU_RULES_SEAT": "content"}, 4, "MUSE_CURRICULUM_CONTENT_FORBIDDEN"),
        (["--epic", "infra"], {}, 4, "MUSE_STREAM_NOT_ADMITTED"),
        (["--epic", "harness"], {}, 4, "MUSE_STREAM_NOT_ADMITTED"),
        (["--epic", "infra.fleet-comms"], {}, 4, "MUSE_STREAM_NOT_ADMITTED"),
        (["--epic", "infra-harness"], {}, 4, "MUSE_STREAM_NOT_ADMITTED"),
        (["--epic", "atlas"], {}, 4, "MUSE_STREAM_NOT_ADMITTED"),
        (["--epic", "unknown"], {}, 4, "MUSE_STREAM_NOT_ADMITTED"),
        ([], {"MUSE_TEST_VISIBILITY": "PRIVATE"}, 4, "MUSE_PRIVATE_REPOSITORY_FORBIDDEN"),
        ([], {"MUSE_TEST_VISIBILITY": "INTERNAL"}, 4, "MUSE_PRIVATE_REPOSITORY_FORBIDDEN"),
        ([], {"MUSE_TEST_VISIBILITY": "UNKNOWN"}, 4, "MUSE_REPOSITORY_VISIBILITY_UNKNOWN"),
        ([], {"MUSE_TEST_GH_RC": "1"}, 4, "MUSE_REPOSITORY_VISIBILITY_UNKNOWN"),
        (["--effort", "bogus"], {}, 2, "MUSE_EFFORT_UNSUPPORTED"),
        (["--harness", "codex"], {}, 2, "MUSE_HARNESS_UNSUPPORTED"),
        (["--force"], {}, 4, "MUSE_FORCE_FORBIDDEN"),
        ([], {"LC_DRIVER_LEASE_ENABLED": "0"}, 4, "MUSE_LEASE_REQUIRED"),
        (["--", "--model", "muse-wonder-full-1.0"], {}, 2, "MUSE_PROVIDER_FLAGS_FORBIDDEN"),
        (["--", "--config=hooks=[]"], {}, 2, "MUSE_PROVIDER_FLAGS_FORBIDDEN"),
        (["--", "--yolo"], {}, 2, "MUSE_PROVIDER_FLAGS_FORBIDDEN"),
        (["--", "resume", "--last"], {}, 2, "MUSE_PROVIDER_FLAGS_FORBIDDEN"),
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


@pytest.mark.parametrize(
    "selector", ["devops", "infra.devops", "monitor", "infra.monitor", "ops-api", "ops.api", "operator-api"]
)
def test_real_guard_gate_cannot_be_overridden(muse_env: dict[str, str], selector: str) -> None:
    result = launch({**muse_env, "MUSE_GUARD_PARITY_PROVEN": "1"}, "--epic", selector, dry=False)
    assert result.returncode == 4
    assert "MUSE_GUARD_PARITY_UNPROVEN: shell,credential,publish,destructive-command,filesystem" in result.stderr
    assert result.stdout == ""


def test_repository_override_cannot_hide_private_checkout(muse_env: dict[str, str]) -> None:
    result = launch(
        {
            **muse_env,
            "GH_REPO": "example/public",
            "GITHUB_REPOSITORY": "example/public",
            "MUSE_TEST_VISIBILITY": "PRIVATE",
        },
        "--epic",
        "devops",
        dry=False,
    )
    assert result.returncode == 4
    assert "MUSE_PRIVATE_REPOSITORY_FORBIDDEN" in result.stderr


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


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini", "grok", "cursor", "kimi", "glm"])
@pytest.mark.parametrize("mode", ["interactive", "driver"])
@pytest.mark.parametrize("variant", ["help", "default"])
def test_other_launcher_help_and_defaults_are_unchanged(provider: str, mode: str, variant: str) -> None:
    from tests.review.test_model_catalog import APPROVED_BASELINE, APPROVED_INPUTS

    index = APPROVED_INPUTS["launchers"].index({"provider": provider, "mode": mode, "variant": variant})
    command = """source "$1"
LC_PROVIDER="$2" LC_MODE="$3" LC_CURSOR_SEAT_PIN=grok-4.7-high
LC_ROOT="$5" LC_DURABLE_HELPER_ROOT="$6"
launcher_defaults
if [ "$4" = help ]; then launcher_parse --help; fi
launcher_normalize_model
launcher_normalize_effort
launcher_validate_driver_certification
printf '%s\\n' "$LC_MODEL" "$LC_EFFORT" "$LC_HARNESS" "$LC_ENDPOINT" "$LC_ISOLATE_CONFIG"
"""
    env = {k: v for k, v in os.environ.items() if not k.startswith("LAUNCHER_")}
    result = subprocess.run(
        ["bash", "-c", command, "capture", str(CORE), provider, mode, variant, str(REPO), str(Path(sys.prefix).parent)],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert {"exit_status": result.returncode, "stdout": result.stdout, "stderr": result.stderr} == (
        APPROVED_BASELINE["launchers"][index]
    )


def lifecycle_fixture(tmp_path: Path, body: str, ready: Path | None = None) -> tuple[Path, Path, Path]:
    """Isolate only Muse admission; exercise the unmodified shared lease machinery."""
    old_launcher, attempts, closed, _ = _core_driver_exit_fixture(
        tmp_path,
        provider_body=body,
        forward_ready=ready,
    )
    root = old_launcher.parent
    launcher = root / "start-muse-driver.sh"
    shutil.copy2(REPO / launcher.name, launcher)
    # Reuse the fixture's scope exports for this new entrypoint as well.
    original_body = old_launcher.read_text()
    scope_exports = original_body.split("set -euo pipefail", 1)[0].split("\n", 1)[1]
    body_text = launcher.read_text()
    launcher.write_text(body_text.replace("set -euo pipefail", scope_exports + "set -euo pipefail", 1))
    adapter = root / "scripts/launchers/muse.sh"
    adapter.write_text(
        "launcher_adapter_validate() { :; }\n"
        "launcher_adapter_preflight() { :; }\n"
        'launcher_adapter_canary() { printf "canary\\n" >> "$MUSE_TEST_EVENTS"; }\n'
        "launcher_adapter_exec() { launcher_exec_command muse; }\n"
    )
    python_stub = root / ".venv/bin/python"
    text = python_stub.read_text()
    text = text.replace("  cat <<'JSON'", '  printf "claim\\n" >> "$MUSE_TEST_EVENTS"\n  cat <<\'JSON\'', 1)
    text = text.replace("  touch ", '  printf "close\\n" >> "$MUSE_TEST_EVENTS"\n  touch ', 1)
    python_stub.write_text(text)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    muse = bindir / "muse"
    muse.write_text('#!/bin/bash\nprintf "exec\\n" >> "$MUSE_TEST_EVENTS"\n' + body + "\n")
    muse.chmod(0o755)
    return launcher, attempts, closed


@pytest.mark.parametrize("exit_code", [0, 7])
def test_shared_lease_claim_exec_close_order(muse_env: dict[str, str], tmp_path: Path, exit_code: int) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    launcher, attempts, closed = lifecycle_fixture(fixture_dir, f"exit {exit_code}")
    events = tmp_path / "events"
    result = run_launcher(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={**muse_env, "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}", "MUSE_TEST_EVENTS": str(events)},
        timeout=60,
    )
    assert result.returncode == exit_code, result.stdout + result.stderr
    assert events.read_text().splitlines() == ["claim", "canary", "exec", "close"]
    assert attempts.read_text().strip() == "1"
    assert closed.is_file()


@pytest.mark.parametrize(("sig", "exit_code"), [(signal.SIGINT, 130), (signal.SIGTERM, 143), (signal.SIGHUP, 129)])
def test_shared_signal_closes_muse_lease(
    muse_env: dict[str, str],
    tmp_path: Path,
    sig: signal.Signals,
    exit_code: int,
) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    ready, child_ready, received = (tmp_path / name for name in ("parent-ready", "child-ready", "received"))
    launcher, attempts, closed = lifecycle_fixture(
        fixture_dir,
        _blocking_signal_provider(received, child_ready),
        ready,
    )
    events = tmp_path / "events"
    group = start_launcher_group(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={**muse_env, "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}", "MUSE_TEST_EVENTS": str(events)},
    )
    try:
        group.wait_for_readiness([ready, child_ready], timeout=_LAUNCHER_READY_TIMEOUT_S)
        group.signal_leader(sig)
        result = group.finish(60)
        assert result.returncode == exit_code, result.stdout + result.stderr
        assert received.is_file() and closed.is_file()
        assert attempts.read_text().strip() == "1"
        assert events.read_text().splitlines() == ["claim", "canary", "exec", "close"]
    finally:
        group.reap()


def test_occupied_lease_refuses_before_canary_and_exec(muse_env: dict[str, str], tmp_path: Path) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    launcher, attempts, closed = lifecycle_fixture(fixture_dir, "exit 99")
    python_stub = launcher.parent / ".venv/bin/python"
    body = python_stub.read_text().replace(
        '  printf "claim\\n" >> "$MUSE_TEST_EVENTS"',
        '  printf "occupied\\n" >> "$MUSE_TEST_EVENTS"\n  echo "already has live session" >&2\n  exit 1',
        1,
    )
    python_stub.write_text(body)
    events = tmp_path / "events"
    result = run_launcher(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={**muse_env, "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}", "MUSE_TEST_EVENTS": str(events)},
        timeout=60,
    )
    assert result.returncode == 1
    assert "already has live session" in result.stderr
    assert events.read_text().splitlines() == ["occupied"]
    assert not attempts.exists() and not closed.exists()


def test_canary_failure_closes_claim_without_provider(muse_env: dict[str, str], tmp_path: Path) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    launcher, attempts, closed = lifecycle_fixture(fixture_dir, "exit 99")
    adapter = launcher.parent / "scripts/launchers/muse.sh"
    adapter.write_text(
        adapter.read_text().replace(
            'printf "canary\\n" >> "$MUSE_TEST_EVENTS"; }',
            'printf "canary\\n" >> "$MUSE_TEST_EVENTS"; return 2; }',
        )
    )
    events = tmp_path / "events"
    result = run_launcher(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={**muse_env, "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}", "MUSE_TEST_EVENTS": str(events)},
        timeout=60,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert events.read_text().splitlines() == ["claim", "canary", "close"]
    assert closed.is_file() and attempts.read_text().strip() == "1"


@pytest.mark.parametrize("lost", [False, True])
def test_shared_renewal_precedes_close_and_stops_on_lease_loss(
    muse_env: dict[str, str],
    tmp_path: Path,
    lost: bool,
) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    launcher, attempts, closed = lifecycle_fixture(
        fixture_dir,
        'trap "exit 0" TERM\nwhile ! grep -q "^renew$" "$MUSE_TEST_EVENTS"; do sleep 0.05; done\n'
        + ("sleep 0.5\n" if lost else "")
        + "exit 0",
    )
    python_stub = launcher.parent / ".venv/bin/python"
    body = python_stub.read_text()
    first, rest = body.split("\n", 1)
    heartbeat = (
        'if [[ "${1:-}" == "-m" && "${2:-}" == "scripts.session_supervisor" && "${3:-}" == heartbeat ]]; then\n'
        '  printf "renew\\n" >> "$MUSE_TEST_EVENTS"\n'
        + ('  echo "LEASE LOST" >&2; exit 4\n' if lost else "  exit 0\n")
        + "fi\n"
    )
    python_stub.write_text(first + "\n" + heartbeat + rest)
    events = tmp_path / "events"
    result = run_launcher(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={
            **muse_env,
            "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}",
            "MUSE_TEST_EVENTS": str(events),
            "SESSION_STREAM_RENEW_INTERVAL_SECONDS": "1",
            "SESSION_STREAM_RENEW_JITTER_SECONDS": "0",
        },
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert events.read_text().splitlines() == ["claim", "canary", "exec", "renew", "close"]
    assert closed.is_file() and attempts.read_text().strip() == "1"
    if lost:
        assert "LEASE LOST" in result.stderr
    capsules = list((launcher.parent / ".agent/session-capsules/epic-5703").glob("*.json"))
    assert len(capsules) == 1
    import json

    capsule = json.loads(capsules[0].read_text())
    assert capsule["agent"] == "muse" and capsule["harness"] == "muse-cli"
