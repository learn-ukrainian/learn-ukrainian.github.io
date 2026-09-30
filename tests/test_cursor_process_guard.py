"""Execution tripwires and detached-process session failure regressions (#9241)."""
from __future__ import annotations

import contextlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

from tests import cursor_exec_tripwire as tripwire
from tests import cursor_process_guard as guard


@pytest.fixture(autouse=True)
def fake_process_owner(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TEST_CURSOR_TEST_OWNER", str(tmp_path))


@pytest.mark.parametrize("name", ["cursor-agent", "agent"])
@pytest.mark.parametrize("nested", [False, True])
def test_path_and_alias_execute_only_recording_fake(name, nested, fake_cursor_bin, tmp_path, monkeypatch):
    log = tmp_path / "record.jsonl"
    monkeypatch.setenv("LU_TEST_CURSOR_LOG", str(log))
    cmd = [name, "-p"]
    if nested:
        cmd = [sys.executable, "-c", f"import subprocess; subprocess.run({cmd!r}, input='probe', text=True, check=True)"]
    result = subprocess.run(cmd, input="probe", text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(log.read_text()) == {"argv": ["-p"], "stdin": "probe"}


@pytest.fixture
def installed_double(tmp_path, monkeypatch):
    target = tmp_path / "installation" / "cursor-agent"
    target.parent.mkdir()
    marker = tmp_path / "real-executed"
    target.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\n")
    target.chmod(0o755)
    monkeypatch.setattr(tripwire, "real_targets", frozenset({str(target)}))
    return target, marker


@pytest.mark.parametrize("route", ["absolute", "alias", "symlink", "shell", "python", "executable", "system", "posix_spawn"])
def test_installed_targets_refused_before_execution(installed_double, tmp_path, route, monkeypatch):
    target, marker = installed_double
    alias = tmp_path / "agent"
    alias.symlink_to(target)
    with pytest.raises(RuntimeError, match="cursor execution tripwire"):
        if route == "absolute":
            subprocess.run([str(target)], timeout=5)
        elif route == "alias":
            subprocess.run(["agent"], env={"PATH": str(tmp_path)}, timeout=5)
        elif route == "symlink":
            subprocess.run([str(alias)], timeout=5)
        elif route == "shell":
            subprocess.run(shlex.quote(str(target)), shell=True, timeout=5)
        elif route == "python":
            subprocess.run([sys.executable, "-c", f"import subprocess; subprocess.run([{str(target)!r}])"], timeout=5)
        elif route == "executable":
            subprocess.run(["harmless"], executable=str(target), timeout=5)
        elif route == "system":
            os.system(shlex.quote(str(target)))
        else:
            os.posix_spawn(str(target), [str(target)], {})
    assert not marker.exists()


@pytest.mark.parametrize("depth", [1, 2])
def test_nested_python_with_replaced_environment_refuses_installed_binary(installed_double, tmp_path, depth):
    target, marker = installed_double
    # The parent command does not contain the target; the nested Python must
    # inherit and execute the tripwire, including with env={} and changed cwd.
    script = tmp_path / "child.py"
    script.write_text(f"import subprocess\nsubprocess.run([{str(target)!r}])\n")
    cmd = [sys.executable, str(script)]
    if depth == 2:
        outer = tmp_path / "outer.py"
        outer.write_text(f"import subprocess, sys\nsubprocess.run([sys.executable, {str(script)!r}], env={{}}, check=True)\n")
        cmd = [sys.executable, str(outer)]
    result = subprocess.run(cmd, env={}, cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert "cursor execution tripwire" in result.stderr
    assert not marker.exists()


@pytest.mark.parametrize("method", ["system", "exec"])
def test_nested_system_and_exec_refuse_installed_binary(installed_double, tmp_path, method):
    target, marker = installed_double
    script = tmp_path / "child.py"
    script.write_text(f"import os\nos.execve({str(target)!r}, [{str(target)!r}], {{}})\n")
    if method == "system":
        assert os.system(f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}") != 0
    else:
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=5)
        assert result.returncode != 0
        assert "cursor execution tripwire" in result.stderr
    assert not marker.exists()


def test_node_install_entrypoint_refused(tmp_path, monkeypatch):
    root = tmp_path / "cursor-install"
    monkeypatch.setattr(tripwire, "real_roots", (str(root),))
    with pytest.raises(RuntimeError, match="cursor execution tripwire"):
        subprocess.run(["node", str(root / "versions" / "v1" / "index.js")], timeout=5)


def test_tripwire_lookup_is_not_replaced_by_adapter_mock(installed_double, tmp_path, monkeypatch):
    import shutil

    target, marker = installed_double
    (tmp_path / "agent").symlink_to(target)
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="cursor execution tripwire"):
        subprocess.run("agent; exit 0", shell=True, env={"PATH": str(tmp_path)}, timeout=5)
    assert not marker.exists()


def test_malformed_shell_token_does_not_break_unrelated_execution():
    tripwire.refuse_real_cursor(sys.executable, [sys.executable, "an unmatched '"], {})


def test_tripwire_can_be_inactive(monkeypatch, installed_double):
    target, _ = installed_double
    monkeypatch.setattr(tripwire, "active", False)
    tripwire.refuse_real_cursor(str(target), [str(target)])


def test_audit_hook_propagates_guard_through_explicit_environment(tmp_path):
    env = {"PYTHONPATH": "existing-import-root"}
    tripwire.audit_exec("subprocess.Popen", ("not-a-real-binary", ["not-a-real-binary"], None, env))
    assert json.loads(env["LU_TEST_CURSOR_TARGETS"]) == sorted(tripwire.real_targets)
    assert json.loads(env["LU_TEST_CURSOR_ROOTS"]) == list(tripwire.real_roots)
    assert env["PYTHONPATH"].split(os.pathsep) == [str(tripwire.child_directory), "existing-import-root"]
    first_path = env["PYTHONPATH"]
    tripwire.audit_exec("os.posix_spawn", ("not-a-real-binary", ["not-a-real-binary"], env))
    assert env["PYTHONPATH"] == first_path


def test_audit_system_refuses_installed_target(installed_double):
    target, marker = installed_double
    with pytest.raises(RuntimeError, match="cursor execution tripwire"):
        tripwire.audit_exec("os.system", (shlex.quote(str(target)),))
    assert not marker.exists()


def test_child_initialization_restores_guard_from_environment(monkeypatch):
    monkeypatch.setattr(tripwire, "child_directory", tripwire.child_directory)
    monkeypatch.setenv("LU_TEST_CURSOR_TARGETS", json.dumps(sorted(tripwire.real_targets)))
    monkeypatch.setenv("LU_TEST_CURSOR_ROOTS", json.dumps(tripwire.real_roots))
    tripwire.install_from_environment()
    assert tripwire.child_directory == Path(tripwire.__file__).parent


def _detached_script(pidfile: Path) -> str:
    return f"""import os, time
if os.fork():
    os._exit(0)
os.setsid()
if os.fork():
    os._exit(0)
os.chdir('/')
fd = os.open(os.devnull, os.O_RDWR)
for dest in (0, 1, 2):
    os.dup2(fd, dest)
with open({str(pidfile)!r}, 'w') as handle:
    handle.write(str(os.getpid()))
time.sleep(30)
"""


def _wait_pidfile(pidfile: Path) -> int:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if pidfile.exists() and pidfile.read_text():
            return int(pidfile.read_text())
        time.sleep(0.01)
    raise AssertionError("fake detached process did not become ready")


def _clean_fake_processes(root):
    for proc in psutil.process_iter():
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
            if proc.status() != psutil.STATUS_ZOMBIE and proc.environ().get("LU_TEST_CURSOR_TEST_OWNER") == str(root):
                proc.kill()
                with contextlib.suppress(psutil.TimeoutExpired):
                    proc.wait(timeout=0.1)


@pytest.mark.parametrize("name", sorted(guard.PROCESS_NAMES))
def test_snapshot_finds_double_fork_after_reparent_and_cwd_change(tmp_path, name):
    baseline = guard.process_snapshot()
    script = tmp_path / name
    pidfile = tmp_path / "pid"
    script.write_text(_detached_script(pidfile))
    try:
        subprocess.run([sys.executable, str(script)], check=True, timeout=5)
        pid = _wait_pidfile(pidfile)
        proc = psutil.Process(pid)
        identity = (pid, proc.create_time())
        assert proc.cwd() == "/"
        assert proc.ppid() != os.getpid()
        assert (pid, proc.create_time()) in guard.process_snapshot().keys() - baseline.keys()
    finally:
        _clean_fake_processes(tmp_path)
    assert identity not in guard.process_snapshot()


def test_baseline_ignores_preexisting_process_and_pid_reuse_is_detected(monkeypatch, capsys):
    monkeypatch.setattr(tripwire, "active", tripwire.active)
    before = {(101, 1.0): "tsserver.js"}
    monkeypatch.setattr(guard, "process_snapshot", lambda: before.copy())
    session = SimpleNamespace(config=SimpleNamespace(), exitstatus=pytest.ExitCode.OK)
    guard.pytest_sessionstart(session)
    guard.pytest_sessionfinish(session, 0)
    assert session.exitstatus == pytest.ExitCode.OK
    monkeypatch.setattr(guard, "process_snapshot", lambda: {(101, 2.0): "typingsInstaller.js"})
    guard.pytest_sessionfinish(session, 0)
    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    assert "typingsInstaller.js pid=101" in capsys.readouterr().out
    tripwire.active = True


def test_real_pytest_session_fails_and_names_detached_survivor(tmp_path):
    baseline = guard.process_snapshot()
    pidfile = tmp_path / "leaked.pid"
    child = tmp_path / "typescript-language-server"
    child.write_text(_detached_script(pidfile))
    (tmp_path / "conftest.py").write_text("pytest_plugins = ['tests.cursor_process_guard']\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "test_leak.py").write_text(
        "import subprocess, sys, time\nfrom pathlib import Path\n"
        "def test_leak():\n"
        f"    subprocess.run([sys.executable, {str(child)!r}], check=True, timeout=5)\n"
        f"    ready = Path({str(pidfile)!r})\n"
        "    for _ in range(500):\n"
        "        if ready.exists() and ready.read_text(): return\n"
        "        time.sleep(0.01)\n"
        "    assert False, 'child not ready'\n",
    )
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(root), str(root / "scripts")]), PYTEST_ADDOPTS="")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-c", str(tmp_path / "pytest.ini"),
             "--confcutdir", str(tmp_path), str(tmp_path / "test_leak.py")],
            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=20,
        )
        assert result.returncode == pytest.ExitCode.TESTS_FAILED, result.stdout + result.stderr
        assert "survived session: typescript-language-server" in result.stdout
        assert str(_wait_pidfile(pidfile)) in result.stdout
    finally:
        _clean_fake_processes(tmp_path)


def test_real_smoke_explicit_option_is_refused_in_workers(monkeypatch):
    monkeypatch.setattr(guard, "_DISPATCH_OR_CI", True)
    request = SimpleNamespace(config=SimpleNamespace(getoption=lambda _: True))
    fixture = guard.real_cursor_binary.__wrapped__(request)
    with pytest.raises(pytest.fail.Exception, match="forbidden in CI and dispatch workers"):
        next(fixture)
    assert not tripwire.allow_real


def test_real_smoke_unavailable_binary_fails_instead_of_skipping(monkeypatch):
    monkeypatch.setattr(guard, "_DISPATCH_OR_CI", False)
    monkeypatch.setattr(guard, "REAL_TARGETS", frozenset())
    request = SimpleNamespace(config=SimpleNamespace(getoption=lambda _: True))
    with pytest.raises(pytest.fail.Exception, match="no binary was found"):
        next(guard.real_cursor_binary.__wrapped__(request))


def test_real_smoke_permission_is_scoped_and_restored(monkeypatch, fake_cursor_bin):
    monkeypatch.setattr(guard, "_DISPATCH_OR_CI", False)
    monkeypatch.setattr(guard, "REAL_TARGETS", frozenset({str(fake_cursor_bin / "cursor-agent")}))
    monkeypatch.setattr(guard, "_REAL_CURSOR_BINARY", str(fake_cursor_bin / "cursor-agent"))
    request = SimpleNamespace(config=SimpleNamespace(getoption=lambda _: True))
    fixture = guard.real_cursor_binary.__wrapped__(request)
    assert next(fixture) == str(fake_cursor_bin / "cursor-agent")
    assert tripwire.allow_real
    fixture.close()
    assert not tripwire.allow_real


@pytest.mark.parametrize("ending", ["success", "failure", "timeout", "exception"])
@pytest.mark.parametrize("exec_sleep", [False, True])
def test_smoke_reaps_group_and_detached_child_for_all_outcomes(tmp_path, ending, exec_sleep, monkeypatch):
    baseline = guard.process_snapshot()
    script = tmp_path / "cursor-agent"
    pidfile = tmp_path / "pid"
    child_code = _detached_script(pidfile)
    if exec_sleep:
        child_code = child_code.replace("time.sleep(30)", "os.execl('/bin/sleep', 'sleep', '30')")
    script.write_text(f"#!{sys.executable}\n" + child_code.replace(
        "if os.fork():\n    os._exit(0)",
        f"if os.fork():\n    while not os.path.exists({str(pidfile)!r}): time.sleep(0.01)\n"
        f"    {'time.sleep(30)' if ending == 'timeout' else 'time.sleep(0.05)'}\n"
        f"    {'print(\"PONG\", flush=True)' if ending == 'success' else 'pass'}\n"
        f"    os._exit({1 if ending == 'failure' else 0})", 1,
    ))
    script.chmod(0o755)
    if ending == "exception":
        def broken_communicate(proc, *args, **kwargs):
            _wait_pidfile(pidfile)
            raise ValueError("fake communication failure")

        monkeypatch.setattr(subprocess.Popen, "communicate", broken_communicate)
    try:
        if ending == "timeout":
            with pytest.raises(subprocess.TimeoutExpired):
                guard.bounded_cursor_smoke(str(script), timeout=0.3)
        elif ending == "exception":
            with pytest.raises(ValueError, match="communication failure"):
                guard.bounded_cursor_smoke(str(script), timeout=2)
        else:
            result = guard.bounded_cursor_smoke(str(script), timeout=2)
            assert result.returncode == (1 if ending == "failure" else 0)
            if ending == "success":
                assert "PONG" in result.stdout
        with contextlib.suppress(psutil.NoSuchProcess):
            assert psutil.Process(_wait_pidfile(pidfile)).status() == psutil.STATUS_ZOMBIE
        # The suite-wide snapshot may include concurrent sessions. Assert the
        # owned fake is gone here; the plugin enforces the full session diff.
        pid = _wait_pidfile(pidfile)
        assert pid not in {identity[0] for identity in guard.process_snapshot()}
    finally:
        _clean_fake_processes(tmp_path)


def test_smoke_teardown_preserves_unrelated_preexisting_process(tmp_path, fake_cursor_bin):
    baseline = guard.process_snapshot()
    other = tmp_path / "typescript-language-server"
    pidfile = tmp_path / "other.pid"
    other.write_text(_detached_script(pidfile))
    try:
        subprocess.run([sys.executable, str(other)], check=True, timeout=5)
        pid = _wait_pidfile(pidfile)
        result = guard.bounded_cursor_smoke(str(fake_cursor_bin / "cursor-agent"), timeout=5)
        assert result.returncode == 0
        assert psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
    finally:
        _clean_fake_processes(tmp_path)


def test_install_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setattr(tripwire, "_installed", True)
    monkeypatch.setattr(sys, "addaudithook", lambda _: pytest.fail("hook installed twice"))
    tripwire.install(tripwire.real_targets, tripwire.real_roots, tripwire.child_directory)
