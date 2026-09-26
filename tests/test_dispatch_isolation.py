"""Dispatch worker cgroup isolation (#8645 part C).

Unit tests put fake ``systemctl``, ``loginctl``, ``stat``, and ``systemd-run``
on ``PATH``. The one real test starts a throwaway scope and skips when no user
manager is reachable. It does not load or modify ``lu-dispatch.slice``.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
import time
import uuid
from contextlib import suppress
from pathlib import Path

import pytest

from scripts.orchestration import dispatch_isolation as iso

_PY = sys.executable
_MEMORY_MAX = str(iso.MEMORY_MAX_BYTES)
_MEMORY_SWAP = str(iso.MEMORY_SWAP_MAX_BYTES)


def _write_exe(path: Path, body: str) -> None:
    path.write_text(f"#!{_PY}\n" + textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(0o755)


def _install_fakes(tmp_path: Path) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_exe(
        bindir / "systemctl",
        """
        import os, sys, time
        mode = os.environ.get("FAKE_SYSTEMCTL", "ok")
        if mode == "timeout":
            time.sleep(30)
        if mode == "down":
            sys.stderr.write("Failed to connect to bus: No such file or directory\\n")
            sys.exit(1)
        if mode == "not-loaded":
            sys.stdout.write("LoadState=not-found\\nMemoryMax=infinity\\nMemorySwapMax=infinity\\n")
            raise SystemExit(0)
        if mode == "bad-memory":
            sys.stdout.write("LoadState=loaded\\nMemoryMax=infinity\\nMemorySwapMax=infinity\\n")
            raise SystemExit(0)
        if mode == "bad-swap":
            sys.stdout.write(f"LoadState=loaded\\nMemoryMax={os.environ['FAKE_MEMORY_MAX']}\\nMemorySwapMax=infinity\\n")
            raise SystemExit(0)
        sys.stdout.write(
            "LoadState=loaded\\n"
            f"MemoryMax={os.environ['FAKE_MEMORY_MAX']}\\n"
            f"MemorySwapMax={os.environ['FAKE_MEMORY_SWAP']}\\n"
        )
        """,
    )
    _write_exe(
        bindir / "loginctl",
        """
        import os, sys, time
        mode = os.environ.get("FAKE_LOGINCTL", "yes")
        if mode == "timeout":
            time.sleep(30)
        if mode == "down":
            sys.stderr.write("Failed to get user: not found\\n")
            sys.exit(1)
        value = "yes" if mode == "yes" else mode
        sys.stdout.write(f"Linger={value}\\n")
        """,
    )
    _write_exe(
        bindir / "stat",
        """
        import os, sys, time
        mode = os.environ.get("FAKE_STAT", "cgroup2fs")
        if mode == "timeout":
            time.sleep(30)
        if mode == "down":
            sys.stderr.write("stat: cannot read filesystem\\n")
            sys.exit(1)
        sys.stdout.write(mode + "\\n")
        """,
    )
    _write_exe(
        bindir / "systemd-run",
        """
        import os, sys, time
        log = os.environ.get("FAKE_ARGV_LOG")
        if log:
            open(log, "w", encoding="utf-8").write("\\n".join(sys.argv))
        mode = os.environ.get("FAKE_SYSTEMD_RUN", "exec")
        if mode == "fail":
            sys.stderr.write("Failed to start transient scope unit: Unit name already exists\\n")
            sys.exit(1)
        if mode == "timeout":
            time.sleep(30)
        if "--" not in sys.argv:
            sys.stderr.write("missing --\\n")
            sys.exit(2)
        command = sys.argv[sys.argv.index("--") + 1 :]
        os.execv(command[0], command)
        """,
    )
    return bindir


def _env(bindir: Path, **overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
    env["FAKE_MEMORY_MAX"] = _MEMORY_MAX
    env["FAKE_MEMORY_SWAP"] = _MEMORY_SWAP
    env.update(overrides)
    return env


def _subtree(tmp_path: Path, text: str = "cpu memory pids\n") -> Path:
    path = tmp_path / "cgroup.subtree_control"
    path.write_text(text, encoding="ascii")
    return path


def _probe(env: dict[str, str], subtree: Path, *, timeout_s: float = iso.PROBE_TIMEOUT_S) -> iso.ProbeResult:
    return iso.probe_isolation(env, timeout_s=timeout_s, subtree_path=subtree)


def _hex_token(unit: str, prefix: str) -> str:
    token = unit.removeprefix(prefix)
    assert len(token) == 8
    assert all(char in "0123456789abcdef" for char in token)
    return token


def test_scope_argv_names_the_slice_unit_and_collect():
    unit = iso.scope_unit_name("codex/task id", "abc123nonce")
    argv = iso.build_scope_argv([_PY, "delegate.py", "_worker"], unit=unit)

    assert argv[:8] == [
        "systemd-run",
        "--user",
        "--scope",
        f"--slice={iso.SLICE_UNIT}",
        f"--unit={unit}",
        "--collect",
        "--quiet",
        "--",
    ]
    assert argv[8:] == [_PY, "delegate.py", "_worker"]
    prefix = "lu-worker-codex-task-id-abc123nonce-"
    assert unit.startswith(prefix)
    _hex_token(unit, prefix)
    assert "/" not in unit and " " not in unit
    assert len(unit) + len(".scope") <= 255
    assert iso.MEMORY_MAX_BYTES == 11 * 1024**3
    assert iso.MEMORY_SWAP_MAX_BYTES == 1 * 1024**3
    assert iso.MEMORY_HIGH_BYTES == 10 * 1024**3
    unit_file = Path("packaging/systemd/lu-dispatch.slice").read_text(encoding="utf-8")
    assert "MemoryMax=11G" in unit_file
    assert "MemoryHigh=10G" in unit_file
    assert "MemorySwapMax=1G" in unit_file


def test_probe_is_ready_when_every_check_holds(tmp_path: Path):
    bindir = _install_fakes(tmp_path)
    result = _probe(_env(bindir), _subtree(tmp_path))

    assert result.ready
    assert result.reason is None


@pytest.mark.parametrize(
    ("overrides", "subtree_text", "check"),
    [
        ({"FAKE_SYSTEMCTL": "down"}, "cpu memory pids\n", "user-manager"),
        ({"FAKE_SYSTEMCTL": "not-loaded"}, "cpu memory pids\n", "load-state"),
        ({"FAKE_STAT": "tmpfs"}, "cpu memory pids\n", "cgroup2"),
        ({}, "cpu pids\n", "subtree-control"),
        ({"FAKE_SYSTEMCTL": "bad-memory"}, "cpu memory pids\n", "memory-max"),
        ({"FAKE_SYSTEMCTL": "bad-swap"}, "cpu memory pids\n", "memory-swap-max"),
        ({"FAKE_LOGINCTL": "no"}, "cpu memory pids\n", "linger"),
    ],
)
def test_probe_names_the_first_failed_check(tmp_path: Path, overrides: dict[str, str], subtree_text: str, check: str):
    bindir = _install_fakes(tmp_path)
    result = _probe(_env(bindir, **overrides), _subtree(tmp_path, subtree_text))

    assert not result.ready
    assert result.check == check
    assert result.reason is not None
    assert result.reason.startswith(f"{check}:")


def test_probe_timeout_on_systemctl_is_the_user_manager_check(tmp_path: Path):
    bindir = _install_fakes(tmp_path)
    result = _probe(_env(bindir, FAKE_SYSTEMCTL="timeout"), _subtree(tmp_path), timeout_s=0.2)

    assert result.check == "user-manager"
    assert result.reason is not None
    assert "timed out" in result.reason


def test_probe_timeout_on_loginctl_is_the_linger_check(tmp_path: Path):
    bindir = _install_fakes(tmp_path)
    result = _probe(_env(bindir, FAKE_LOGINCTL="timeout"), _subtree(tmp_path), timeout_s=0.2)

    assert result.check == "linger"
    assert result.reason is not None
    assert "timed out" in result.reason


def test_forced_fallback_skips_the_probe(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    calls: list[list[str]] = []

    def popen(argv, **_kwargs):
        calls.append(list(argv))

        class _Proc:
            pid = 7
            stdin = None

        return _Proc()

    _proc, launch = iso.spawn_detached_worker(
        [_PY, "-c", "print(1)"],
        task_id="forced",
        run_nonce="nonce",
        popen=popen,
        probe_env={"LU_DISPATCH_ISOLATION": "fallback"},
    )

    assert launch.mode == iso.LAUNCH_FALLBACK
    assert launch.unit is None
    assert launch.fallback_reason == "forced: LU_DISPATCH_ISOLATION=fallback"
    assert calls == [[_PY, "-c", "print(1)"]]
    assert "launching the worker with plain Popen" in capsys.readouterr().err


def test_systemd_run_failure_relaunches_once_with_popen(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    bindir = _install_fakes(tmp_path)
    env = _env(bindir, FAKE_SYSTEMD_RUN="fail")
    log = tmp_path / "stderr.log"
    stderr_fd = os.open(log, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o644)
    fallback: list[list[str]] = []
    real_popen = subprocess.Popen

    def popen(argv, **kwargs):
        if argv[0] == "systemd-run":
            return real_popen(argv, **kwargs)
        fallback.append(list(argv))

        class _Proc:
            pid = 9
            stdin = None

        return _Proc()

    try:
        _proc, launch = iso.spawn_detached_worker(
            [_PY, "-c", "print('should-not-run')"],
            task_id="again",
            run_nonce="nonce9",
            popen=popen,
            env=env,
            probe_env=env,
            stderr=stderr_fd,
            stderr_log=log,
            subtree_path=_subtree(tmp_path),
            timeout_s=2,
        )
    finally:
        os.close(stderr_fd)

    assert launch.mode == iso.LAUNCH_FALLBACK
    assert launch.unit is None
    assert launch.fallback_reason is not None
    assert "exited 1 before the worker started" in launch.fallback_reason
    assert "Unit name already exists" in launch.fallback_reason
    assert fallback == [[_PY, "-c", "print('should-not-run')"]]
    assert "launching the worker with plain Popen" in capsys.readouterr().err


def test_systemd_run_timeout_does_not_relaunch(tmp_path: Path):
    """A scope still alive at the timeout is not proof the worker never started."""
    bindir = _install_fakes(tmp_path)
    env = _env(bindir, FAKE_SYSTEMD_RUN="timeout")
    fallback: list[list[str]] = []
    held: list[subprocess.Popen[bytes]] = []
    real_popen = subprocess.Popen

    def popen(argv, **kwargs):
        if argv[0] == "systemd-run":
            proc = real_popen(argv, **kwargs)
            held.append(proc)
            return proc
        fallback.append(list(argv))

        class _Proc:
            pid = 11
            stdin = None

        return _Proc()

    try:
        with pytest.raises(iso.DispatchIsolationError, match="startup is ambiguous") as raised:
            iso.spawn_detached_worker(
                [_PY, "-c", "print('fallback')"],
                task_id="slow-start",
                run_nonce="nonce-slow",
                popen=popen,
                env=env,
                probe_env=env,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                subtree_path=_subtree(tmp_path),
                timeout_s=0.3,
            )
    finally:
        for proc in held:
            if proc.poll() is None:
                with suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)

    assert "will not be relaunched" in str(raised.value)
    assert fallback == []
    assert held
    assert held[0].poll() is not None


def test_late_start_marker_runs_exactly_one_worker(tmp_path: Path):
    """A marker written between the timeout and the kill must not start a second worker."""
    stamp = tmp_path / "worker-ran"
    cmd = [
        _PY,
        "-c",
        f"from pathlib import Path; Path({str(stamp)!r}).write_text('once', encoding='ascii')",
    ]
    fallback: list[list[str]] = []
    started: list[subprocess.Popen[bytes]] = []
    pid_max = int(Path("/proc/sys/kernel/pid_max").read_text(encoding="ascii"))

    class _Scope:
        def __init__(self, write_fd: int):
            self.write_fd = write_fd
            self.pid = pid_max + 1000
            self.returncode: int | None = None

        def poll(self) -> int | None:
            return self.returncode

        def kill(self) -> None:
            # The byte lands as the scope is stopped: after select timed out
            # and before the stop finishes.
            os.write(self.write_fd, b"1")
            started.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: float | None = None) -> int:
            self.returncode = -signal.SIGKILL
            return self.returncode

    def popen(argv, **kwargs):
        if argv[0] == "systemd-run":
            return _Scope(kwargs["pass_fds"][0])
        fallback.append(list(argv))

        class _Unused:
            pid = 3
            stdin = None

        return _Unused()

    try:
        with pytest.raises(iso.DispatchIsolationError, match="worker start marker arrived") as raised:
            iso.spawn_detached_worker(
                cmd,
                task_id="late-marker",
                run_nonce="nonce-late",
                popen=popen,
                check_probe=False,
                timeout_s=0,
            )
        assert "will not be relaunched" in str(raised.value)
        assert len(started) == 1
        assert started[0].wait(timeout=5) == 0
        assert stamp.read_text(encoding="ascii") == "once"
        assert fallback == []
    finally:
        for proc in started:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)


def test_scope_passes_the_environment_and_records_the_unit(tmp_path: Path):
    bindir = _install_fakes(tmp_path)
    argv_log = tmp_path / "argv.txt"
    env = _env(
        bindir,
        FAKE_SYSTEMD_RUN="exec",
        FAKE_ARGV_LOG=str(argv_log),
        LU_SCOPE_MARKER_8645="from-parent",
    )
    proc, launch = iso.spawn_detached_worker(
        [_PY, "-c", "import os; print(os.environ['LU_SCOPE_MARKER_8645'], flush=True)"],
        task_id="codex/env task",
        run_nonce="abc123",
        env=env,
        probe_env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        subtree_path=_subtree(tmp_path),
    )

    assert launch.mode == iso.LAUNCH_SCOPE
    assert launch.unit is not None
    _hex_token(launch.unit, "lu-worker-codex-env-task-abc123-")
    assert proc.stdout is not None
    assert proc.stdout.readline().decode() == "from-parent\n"
    proc.wait(timeout=5)
    recorded = argv_log.read_text(encoding="utf-8").splitlines()
    assert "--scope" in recorded
    assert "--collect" in recorded
    assert "--quiet" in recorded
    assert f"--slice={iso.SLICE_UNIT}" in recorded
    assert f"--unit={launch.unit}" in recorded
    separator = recorded.index("--")
    assert recorded[separator + 1 :][-3:] == [
        _PY,
        "-c",
        "import os; print(os.environ['LU_SCOPE_MARKER_8645'], flush=True)",
    ]


def test_worker_that_starts_and_exits_is_not_relaunched(tmp_path: Path):
    bindir = _install_fakes(tmp_path)
    env = _env(bindir, FAKE_SYSTEMD_RUN="exec")
    calls: list[str] = []
    real_popen = subprocess.Popen

    def popen(argv, **kwargs):
        calls.append(argv[0])
        return real_popen(argv, **kwargs)

    proc, launch = iso.spawn_detached_worker(
        [_PY, "-c", "import sys; sys.exit(3)"],
        task_id="dies",
        run_nonce="nonce-dies",
        popen=popen,
        env=env,
        probe_env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        subtree_path=_subtree(tmp_path),
    )

    assert calls == ["systemd-run"]
    assert launch.mode == iso.LAUNCH_SCOPE
    assert proc.wait(timeout=5) == 3


def test_scope_unit_names_differ_for_the_same_task_and_nonce():
    first = iso.scope_unit_name("same-task", "reused-nonce")
    second = iso.scope_unit_name("same-task", "reused-nonce")
    prefix = "lu-worker-same-task-reused-nonce-"

    assert first != second
    _hex_token(first, prefix)
    _hex_token(second, prefix)
    long_name = iso.scope_unit_name("t" * 500, "n" * 80 + "/bad")
    assert len(long_name) + len(".scope") <= 255
    assert "t" * 40 in long_name
    assert "/" not in long_name


def test_scope_start_failure_reads_a_bounded_stderr_excerpt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    bindir = _install_fakes(tmp_path)
    env = _env(bindir, FAKE_SYSTEMD_RUN="fail")
    log = tmp_path / "stderr.log"
    token = b"PREEXISTING-LOG-MUST-NOT-BE-READ\n"
    prefix_len = 8 * 1024 * 1024
    log.write_bytes(token + b"x" * (prefix_len - len(token)))
    stderr_fd = os.open(str(log), os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o644)
    reads: list[int] = []
    real_open = Path.open

    def tracking_open(self: Path, mode: str = "r", *args: object, **kwargs: object):
        handle = real_open(self, mode, *args, **kwargs)
        if self == log and "b" in str(mode):
            original = handle.read

            def bounded(n: int = -1) -> bytes:
                blob = original(n)
                if isinstance(blob, bytes):
                    reads.append(len(blob))
                    if n < 0 or len(blob) > iso._STDERR_EXCERPT_BYTES:
                        raise AssertionError(f"unbounded stderr read ({len(blob)} bytes, n={n})")
                return blob

            handle.read = bounded  # type: ignore[method-assign]
        return handle

    monkeypatch.setattr(Path, "open", tracking_open)
    fallback: list[list[str]] = []
    real_popen = subprocess.Popen

    def popen(argv, **kwargs):
        if argv[0] == "systemd-run":
            return real_popen(argv, **kwargs)
        fallback.append(list(argv))

        class _Proc:
            pid = 13
            stdin = None

        return _Proc()

    try:
        _proc, launch = iso.spawn_detached_worker(
            [_PY, "-c", "print('should-not-run')"],
            task_id="big-log",
            run_nonce="nonce-big",
            popen=popen,
            env=env,
            probe_env=env,
            stderr=stderr_fd,
            stderr_log=log,
            subtree_path=_subtree(tmp_path),
            timeout_s=2,
        )
    finally:
        os.close(stderr_fd)

    assert launch.mode == iso.LAUNCH_FALLBACK
    assert launch.fallback_reason is not None
    assert "Unit name already exists" in launch.fallback_reason
    assert "PREEXISTING-LOG-MUST-NOT-BE-READ" not in launch.fallback_reason
    assert reads
    assert sum(reads) <= iso._STDERR_EXCERPT_BYTES
    assert fallback == [[_PY, "-c", "print('should-not-run')"]]


def test_launch_fields_remain_beside_peak_rss(monkeypatch: pytest.MonkeyPatch):
    import resource

    import scripts.delegate as delegate

    class _Usage:
        ru_maxrss = 3 * 1024 * 1024 if sys.platform == "darwin" else 3 * 1024

    monkeypatch.setattr(resource, "getrusage", lambda _who: _Usage())
    state = {"launch_mode": iso.LAUNCH_SCOPE, "launch_unit": "lu-worker-t-n-1"}
    merged = {
        **state,
        **delegate._core_terminal_fields(
            status="done",
            duration_s=1.0,
            response="ok",
            result_file=None,
            stderr_excerpt=None,
            returncode=0,
            returncode_reason=None,
            dirty_on_exit=False,
            commits_ahead=0,
            needs_finalize=False,
            finalize_error=None,
            last_error=None,
        ),
    }

    assert merged["launch_mode"] == "scope"
    assert merged["launch_unit"] == "lu-worker-t-n-1"
    assert merged["peak_rss_mib"] == 3.0


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ActiveState=inactive\nMemoryCurrent=10\nMemoryMax=20\n", None),
        ("LoadState=not-found\nActiveState=inactive\n", None),
        ("ActiveState=active\nMemoryCurrent=[not set]\nMemoryMax=11811160064\n", None),
        (
            "ActiveState=active\nMemoryCurrent=4294967296\nMemoryMax=11811160064\n",
            "lu-dispatch.slice 4.0/11.0 GiB",
        ),
        (
            "ActiveState=active\nMemoryCurrent=1073741824\nMemoryMax=infinity\n",
            "lu-dispatch.slice 1.0 GiB (MemoryMax infinity)",
        ),
    ],
)
def test_format_slice_show(text: str, expected: str | None):
    assert iso.format_slice_show(text) == expected


def _require_user_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    bus = Path(runtime) / "bus"
    if not bus.exists():
        pytest.skip(f"no user manager is reachable: bus socket {bus} is absent")
    monkeypatch.setenv("XDG_RUNTIME_DIR", runtime)
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", f"unix:path={bus}")
    try:
        proc = subprocess.run(
            ["systemctl", "--user", "is-system-running"],
            capture_output=True,
            text=True,
            timeout=iso.PROBE_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        pytest.skip(f"no user manager is reachable: {exc}")
    state = (proc.stdout or "").strip()
    if state not in {"running", "degraded"}:
        detail = (proc.stderr or proc.stdout).strip()
        pytest.skip(f"no user manager is reachable: {detail or 'systemctl --user is-system-running failed'}")


def _scope_is_gone(unit: str) -> None:
    last = ""
    for _attempt in range(5):
        gone = subprocess.run(
            ["systemctl", "--user", "status", f"{unit}.scope"],
            capture_output=True,
            text=True,
            timeout=iso.PROBE_TIMEOUT_S,
            check=False,
        )
        last = f"{gone.stdout}{gone.stderr}"
        if gone.returncode != 0 and "could not be found" in last:
            return
        time.sleep(0.1)
    raise AssertionError(last)


def _show_dispatch_slice() -> str:
    proc = subprocess.run(
        ["systemctl", "--user", "show", "-p", "FragmentPath,MemoryMax,MemorySwapMax", iso.SLICE_UNIT],
        capture_output=True,
        text=True,
        timeout=iso.PROBE_TIMEOUT_S,
        check=False,
    )
    return proc.stdout


def test_real_scope_puts_the_popen_pid_in_a_throwaway_slice(monkeypatch: pytest.MonkeyPatch):
    """The helper's pid is inside a throwaway slice, and that slice is removed afterwards.

    Skipped when this process cannot reach a user manager. Does not install or
    modify lu-dispatch.slice.
    """
    _require_user_manager(monkeypatch)
    before = _show_dispatch_slice()
    nonce = uuid.uuid4().hex[:12]
    slice_unit = f"probe8645c{nonce}.slice"
    code = (
        "import os, sys\n"
        "from pathlib import Path\n"
        "sys.stdout.write(os.environ.get('LU_SCOPE_MARKER_8645', '') + '\\n')\n"
        "sys.stdout.write(Path('/proc/self/cgroup').read_text().strip() + '\\n')\n"
        "sys.stdout.flush()\n"
        "if os.environ.get('LU_HOLD') == '1':\n"
        "    import time\n"
        "    time.sleep(30)\n"
    )
    env = os.environ.copy()
    env["LU_SCOPE_MARKER_8645"] = "yes"
    env["LU_HOLD"] = "1"
    held: list[subprocess.Popen[bytes]] = []
    try:
        proc, launch = iso.spawn_detached_worker(
            [_PY, "-c", code],
            task_id=f"probe8645c{nonce}",
            run_nonce=nonce,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            slice_unit=slice_unit,
            check_probe=False,
            allow_fallback=False,
        )
        held.append(proc)
        assert launch.mode == iso.LAUNCH_SCOPE
        assert launch.unit is not None
        assert proc.stdout is not None
        assert proc.stdout.readline().decode() == "yes\n"
        child_cgroup = proc.stdout.readline().decode()
        parent_cgroup = Path(f"/proc/{proc.pid}/cgroup").read_text(encoding="utf-8")
        cmdline = Path(f"/proc/{proc.pid}/cmdline").read_bytes().replace(b"\0", b" ")
        assert slice_unit.removesuffix(".slice") in child_cgroup
        assert slice_unit.removesuffix(".slice") in parent_cgroup
        assert b"systemd-run" not in cmdline
        os.kill(proc.pid, signal.SIGTERM)
        assert proc.wait(timeout=5) == -signal.SIGTERM
        _scope_is_gone(launch.unit)

        env["LU_HOLD"] = "0"
        finished, finished_launch = iso.spawn_detached_worker(
            [_PY, "-c", code],
            task_id=f"probe8645c{nonce}x",
            run_nonce=f"{nonce}x",
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            slice_unit=slice_unit,
            check_probe=False,
            allow_fallback=False,
        )
        held.append(finished)
        assert finished.wait(timeout=5) == 0
        assert finished_launch.unit is not None
        _scope_is_gone(finished_launch.unit)
    finally:
        for proc in held:
            if proc.poll() is None:
                with suppress(ProcessLookupError):
                    os.kill(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
        subprocess.run(
            ["systemctl", "--user", "stop", slice_unit],
            capture_output=True,
            text=True,
            timeout=iso.PROBE_TIMEOUT_S,
            check=False,
        )
        subprocess.run(
            ["systemctl", "--user", "reset-failed", slice_unit],
            capture_output=True,
            text=True,
            timeout=iso.PROBE_TIMEOUT_S,
            check=False,
        )
    active = subprocess.run(
        ["systemctl", "--user", "is-active", slice_unit],
        capture_output=True,
        text=True,
        timeout=iso.PROBE_TIMEOUT_S,
        check=False,
    )
    assert active.stdout.strip() != "active"
    assert _show_dispatch_slice() == before
