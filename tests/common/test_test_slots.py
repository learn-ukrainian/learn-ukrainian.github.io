"""Host-wide test-run slot pool (#10662): serialize, release on every exit, FIFO, private and typed."""

from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.common import test_slots
from tests.wait_helpers import wait_for_line

REPO_ROOT = Path(__file__).resolve().parents[2]

# A child that queues for slots, reports when it waits and when it holds, then holds until told to stop.
HOLDER = textwrap.dedent(
    """\
    import sys
    import time
    from pathlib import Path

    from scripts.common import test_slots

    requested, out, release, ending = int(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
    queued = Path(str(out) + ".queued")


    def progress(line):
        if not queued.exists():
            queued.write_text(line + "\\n")


    hold = test_slots.acquire(requested, kind="launcher", progress=progress)
    out.write_text(f"{hold.count} {time.monotonic()}\\n")
    while not release.exists():
        time.sleep(0.02)
    if ending == "release":
        hold.release()
    """
)
PRINTER = (
    "import json, os, sys; print(json.dumps({'argv': sys.argv[1:], "
    "'holder': os.environ.get('LU_TEST_SLOTS_HOLDER'), 'auto': os.environ.get('PYTEST_XDIST_AUTO_NUM_WORKERS')}))"
)


@dataclass
class Child:
    process: subprocess.Popen[str]
    out: Path
    queued: Path
    release: Path

    def finish(self) -> None:
        self.release.touch()
        self.process.wait(timeout=30)


@pytest.fixture(autouse=True)
def pool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A private two-slot pool per test; an outer governed run's holder marker must not leak in."""
    path = tmp_path / "pool"
    monkeypatch.setenv(test_slots.ENABLE_ENV, "on")
    monkeypatch.setenv(test_slots.DIR_ENV, str(path))
    monkeypatch.setenv(test_slots.COUNT_ENV, "2")
    monkeypatch.delenv(test_slots.WAIT_ENV, raising=False)
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    monkeypatch.delenv(test_slots.TASK_ENV, raising=False)
    return path


def _child_env(**extra: str) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key != test_slots.HOLDER_ENV}
    env["PYTHONPATH"] = str(REPO_ROOT)
    env.update(extra)
    return env


def _start(tmp_path: Path, name: str, requested: int, *, ending: str = "release", **env: str) -> Child:
    out, release = tmp_path / f"{name}.out", tmp_path / f"{name}.release"
    process = subprocess.Popen(
        [sys.executable, "-c", HOLDER, str(requested), str(out), str(release), ending],
        cwd=REPO_ROOT,
        env=_child_env(**env),
        text=True,
    )
    return Child(process, out, Path(f"{out}.queued"), release)


def _launch(*command: str, timeout: float = 60, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scripts.common.test_slots", *command],
        cwd=REPO_ROOT,
        env=_child_env(**env),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---- AC-01: the pool serializes and always gives slots back ---------------------------------------------------


def test_two_holders_requesting_more_than_the_pool_serialize(tmp_path: Path) -> None:
    first = _start(tmp_path, "first", 2)
    second = None
    try:
        assert wait_for_line(first.out).split()[0] == "2"
        second = _start(tmp_path, "second", 2)
        assert "queue position 1/1" in wait_for_line(second.queued)
        assert not second.out.exists()
        released_at = time.monotonic()
        first.finish()
        count, acquired_at = wait_for_line(second.out).split()
        assert count == "2" and float(acquired_at) >= released_at
    finally:
        for child in (first, second):
            if child is not None:
                child.finish()


@pytest.mark.parametrize("ending", ["release", "exit", "kill"])
def test_slots_return_on_release_normal_exit_and_sigkill(tmp_path: Path, ending: str) -> None:
    holder = _start(tmp_path, "holder", 2, ending=ending)
    try:
        wait_for_line(holder.out)
        with pytest.raises(test_slots.SlotError) as refused:
            test_slots.acquire(1, kind="pytest", wait_s=0.3)
        assert refused.value.reason == "wait_timeout"
        if ending == "kill":
            holder.process.send_signal(signal.SIGKILL)
            holder.process.wait(timeout=30)
            assert holder.process.returncode == -signal.SIGKILL
        else:
            holder.finish()
            assert holder.process.returncode == 0
        with test_slots.acquire(2, kind="pytest", wait_s=10) as hold:
            assert hold.count == 2 and hold.waited < 5
    finally:
        holder.finish()
    report = test_slots.status()
    assert report["holders"] == [] and report["queue"] == [] and report["slots_in_use"] == 0


def test_slots_return_when_the_holder_raises() -> None:
    with pytest.raises(RuntimeError, match="boom"), test_slots.acquire(2, kind="pytest") as hold:
        assert test_slots.status()["slots_in_use"] == 2 == hold.count
        raise RuntimeError("boom")
    with test_slots.acquire(2, kind="pytest", wait_s=0.5) as again:
        assert again.count == 2
    assert test_slots.status()["slots_in_use"] == 0


def test_queue_is_fifo_and_a_large_request_is_not_starved(tmp_path: Path) -> None:
    busy = test_slots.acquire(1, kind="pytest")
    big = _start(tmp_path, "big", 2)
    small = None
    try:
        wait_for_line(big.queued)
        small = _start(tmp_path, "small", 1)
        assert "queue position 2/2" in wait_for_line(small.queued)
        queue = test_slots.status()["queue"]
        assert [(entry["position"], entry["requested"]) for entry in queue] == [(1, 2), (2, 1)]
        # One slot is free, yet the small request queued behind the large one must not take it.
        busy.release()
        assert wait_for_line(big.out).split()[0] == "2"
        assert not small.out.exists()
        big_acquired = float(wait_for_line(big.out).split()[1])
        big.finish()
        assert float(wait_for_line(small.out).split()[1]) > big_acquired
    finally:
        busy.release()
        for child in (big, small):
            if child is not None:
                child.finish()


def test_a_request_larger_than_the_pool_is_capped_not_deadlocked() -> None:
    with test_slots.acquire(5, kind="pytest", wait_s=2) as hold:
        assert (hold.requested, hold.count, hold.pool_size) == (5, 2, 2)


def test_wait_timeout_is_a_typed_refusal_that_leaves_no_ticket() -> None:
    with test_slots.acquire(2, kind="pytest"):
        started = time.monotonic()
        with pytest.raises(test_slots.SlotError) as refused:
            test_slots.acquire(1, kind="gate", wait_s=0.3)
        assert time.monotonic() - started < 10
        assert refused.value.reason == "wait_timeout"
        assert str(refused.value).startswith("test_slots_wait_timeout:")
        assert test_slots.status()["queue"] == []


def test_stale_slot_files_and_tickets_do_not_block(pool: Path) -> None:
    pool.mkdir(mode=0o700)
    for index in range(2):
        (pool / f"slot-{index:03d}.lock").write_text('{"task_id": "gone", "pid": 1}\n')
    for directory in ("queue", "holders"):
        (pool / directory).mkdir(mode=0o700)
        (pool / directory / f"00000000000000000001-{directory}.ticket").write_text('{"requested": 2}\n')
    with test_slots.acquire(2, kind="pytest", wait_s=2) as hold:
        assert hold.count == 2 and hold.queue_position == 1
        assert test_slots.status()["queue"] == []
    assert not any((pool / "queue").glob("0*.ticket")) and not any((pool / "holders").glob("0*.ticket"))


# ---- configuration --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cpus", "expected"), [(16, 14), (8, 6), (4, 2), (3, 2), (1, 2), (None, 2)], ids=lambda value: str(value)
)
def test_default_pool_size_reserves_cpus_for_services_with_a_floor_of_two(
    cpus: int | None, expected: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(test_slots.COUNT_ENV)
    monkeypatch.setattr(test_slots.os, "cpu_count", lambda: cpus)
    assert test_slots.pool_size() == expected


@pytest.mark.parametrize(
    ("ci", "setting", "expected"),
    [(None, None, True), ("true", None, False), ("1", None, False), ("false", None, True), ("true", "on", True)],
)
def test_ci_runs_unchanged_unless_explicitly_enabled(ci: str | None, setting: str | None, expected: bool) -> None:
    environ = {key: value for key, value in (("CI", ci), (test_slots.ENABLE_ENV, setting)) if value is not None}
    assert test_slots.enabled(environ) is expected


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (test_slots.ENABLE_ENV, "maybe"),
        (test_slots.COUNT_ENV, "0"),
        (test_slots.COUNT_ENV, "-1"),
        (test_slots.COUNT_ENV, "two"),
        (test_slots.COUNT_ENV, "1.5"),
        (test_slots.WAIT_ENV, "-1"),
        (test_slots.WAIT_ENV, "nan"),
        (test_slots.WAIT_ENV, "soon"),
        (test_slots.DIR_ENV, "relative/pool"),
    ],
)
def test_invalid_configuration_is_refused(name: str, value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(test_slots.SlotError) as refused:
        test_slots.acquire(1, kind="pytest", wait_s=0.1)
    assert refused.value.reason == "invalid_configuration"
    assert test_slots.status()["error"]["reason"] == "invalid_configuration"


# ---- the pool directory ---------------------------------------------------------------------------------------


def test_pool_directory_is_private_to_this_user(pool: Path) -> None:
    pool.mkdir(mode=0o755)
    pool.chmod(0o755)
    with test_slots.acquire(1, kind="pytest"):
        info = pool.stat()
        assert stat.S_IMODE(info.st_mode) == 0o700 and info.st_uid == os.geteuid()
        for entry in pool.rglob("*"):
            assert entry.stat().st_uid == os.geteuid()
            assert stat.S_IMODE(entry.stat().st_mode) & 0o077 == 0, entry.name


def test_the_scratch_root_convention_matches_scratch_py() -> None:
    from scripts.common import scratch

    assert test_slots.SCRATCH_ROOT_ENV == scratch.SCRATCH_ROOT_ENV_VAR
    assert test_slots.DEFAULT_SCRATCH_ROOT == scratch.DEFAULT_SCRATCH_ROOT


@pytest.mark.exercises_default_scratch_root
def test_the_built_in_default_root_is_isolated_like_scratch_py(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.common import scratch

    monkeypatch.delenv(test_slots.DIR_ENV)
    assert test_slots.DEFAULT_SCRATCH_ROOT == scratch.DEFAULT_SCRATCH_ROOT != Path("/var/tmp/lu")
    expected = scratch.DEFAULT_SCRATCH_ROOT / "learn-ukrainian" / f"test-slots-{os.geteuid()}"
    assert test_slots.pool_dir() == expected


def test_default_pool_lives_under_the_fleet_scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(test_slots.DIR_ENV)
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    expected = tmp_path / "scratch" / "learn-ukrainian" / f"test-slots-{os.geteuid()}"
    assert test_slots.pool_dir() == expected
    with test_slots.acquire(1, kind="pytest"):
        assert expected.is_dir()
    assert test_slots.status()["location"] == "default"


@pytest.mark.parametrize("marker", ["checkout", "worktree", "git_directory", "bare_repository"])
def test_a_pool_inside_any_git_checkout_or_git_directory_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, marker: str
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    if marker == "checkout":
        (root / ".git").mkdir()
        target = root / "batch_state" / "pool"
    elif marker == "worktree":
        (root / ".git").write_text("gitdir: /elsewhere\n")
        target = root / "pool"
    elif marker == "git_directory":
        target = root / ".git" / "pool"
    else:
        for name in ("objects", "refs"):
            (root / name).mkdir()
        (root / "HEAD").write_text("ref: refs/heads/main\n")
        target = root / "pool"
    monkeypatch.setenv(test_slots.DIR_ENV, str(target))
    with pytest.raises(test_slots.SlotError) as refused:
        test_slots.acquire(1, kind="pytest")
    assert refused.value.reason == "pool_unavailable"
    assert "Git" in str(refused.value)
    assert not target.exists()


def test_a_symlinked_pool_directory_is_refused(tmp_path: Path, pool: Path) -> None:
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    pool.symlink_to(real)
    with pytest.raises(test_slots.SlotError) as refused:
        test_slots.acquire(1, kind="pytest")
    assert refused.value.reason == "pool_unavailable"
    assert list(real.iterdir()) == []


# ---- visibility -----------------------------------------------------------------------------------------------


def test_status_reports_holders_by_task_and_the_queue_without_paths(
    tmp_path: Path, pool: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(test_slots.TASK_ENV, "impl-42")
    hold = test_slots.acquire(1, kind="pytest")
    waiter = _start(tmp_path, "waiter", 2, **{test_slots.TASK_ENV: "not a valid id!"})
    try:
        wait_for_line(waiter.queued)
        report = test_slots.status()
    finally:
        hold.release()
        waiter.finish()
    assert report["schema"] == "test-slots.status.v1"
    assert (report["enabled"], report["pool_exists"], report["pool_size"]) == (True, True, 2)
    assert (report["slots_in_use"], report["slots_free"], report["queue_depth"]) == (1, 1, 1)
    assert report["location"] == "override" and report["error"] is None
    [holder] = report["holders"]
    assert set(holder) == {"task_id", "kind", "pid", "requested", "slots", "held_s", "waited_s"}
    assert (holder["task_id"], holder["kind"], holder["slots"], holder["pid"]) == ("impl-42", "pytest", 1, os.getpid())
    [entry] = report["queue"]
    assert set(entry) == {"position", "task_id", "kind", "pid", "requested", "waiting_s"}
    assert (entry["position"], entry["task_id"], entry["requested"]) == (1, "unknown", 2)
    assert report["longest_wait_s"] == entry["waiting_s"] >= 0
    text = json.dumps(report)
    assert str(pool) not in text and str(tmp_path) not in text and "/" not in text


def test_status_is_read_only_and_reports_a_missing_or_disabled_pool(
    pool: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = test_slots.status()
    assert report["pool_exists"] is False and report["holders"] == [] and report["queue_depth"] == 0
    monkeypatch.setenv(test_slots.ENABLE_ENV, "off")
    assert test_slots.status()["enabled"] is False
    assert not pool.exists()


def test_status_cli_prints_json_and_a_readable_summary(pool: Path) -> None:
    with test_slots.acquire(2, kind="pytest"):
        machine = _launch("status", "--json")
        human = _launch("status")
    assert machine.returncode == 0, machine.stderr
    assert json.loads(machine.stdout)["slots_in_use"] == 2
    assert human.returncode == 0 and "2 of 2 slots in use" in human.stdout and "pytest" in human.stdout


# ---- the launcher ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("arguments", "expected", "auto"),
    [
        (["-n", "8"], ["-n", "2"], "2"),
        (["-n8"], ["-n2"], "2"),
        (["--numprocesses=8"], ["--numprocesses=2"], "2"),
        (["-n", "auto"], ["-n", "2"], "2"),
        (["-n", "logical"], ["-n", "2"], "2"),
        (["--numprocesses", "1", "-q"], ["--numprocesses", "1", "-q"], "1"),
        (["-q"], ["-q"], "1"),
    ],
)
def test_launcher_limits_the_wrapped_run_to_the_slots_it_holds(
    arguments: list[str], expected: list[str], auto: str
) -> None:
    """Visible ``-n`` values are rewritten; a hidden ``-n auto`` is capped through xdist's own variable."""
    result = _launch("run", "--", sys.executable, "-c", PRINTER, *arguments)
    assert result.returncode == 0, result.stderr
    seen = json.loads(result.stdout)
    assert seen["argv"] == expected
    assert seen["holder"] is not None and seen["holder"].split(":", 1)[0] == auto
    assert seen["auto"] == auto
    assert test_slots.status()["slots_in_use"] == 0


def test_launcher_holds_slots_for_the_command_and_passes_its_exit_code() -> None:
    probe = (
        "import sys; from scripts.common import test_slots; report = test_slots.status(); "
        "print(report['slots_in_use'], report['holders'][0]['kind']); sys.exit(3)"
    )
    result = _launch("run", "--slots", "2", "--", sys.executable, "-c", probe)
    assert result.returncode == 3, result.stderr
    assert result.stdout.split() == ["2", "launcher"]
    assert test_slots.status()["slots_in_use"] == 0


@pytest.mark.parametrize(("size", "concurrent"), [(3, False), (4, True)], ids=["pool_too_small", "pool_fits_both"])
def test_two_concurrent_wrapped_runs_never_exceed_the_pool(tmp_path: Path, size: int, concurrent: bool) -> None:
    """Two wrapped ``-n 2`` runs started together overlap only when the pool holds both of them."""
    probe = textwrap.dedent(
        """\
        import json, sys, time
        from pathlib import Path
        from scripts.common import test_slots

        own, other = Path(sys.argv[1]), Path(sys.argv[2])
        Path(f"{own}.started").touch()
        overlapped, deadline = False, time.monotonic() + 5
        while time.monotonic() < deadline:
            if Path(f"{other}.started").exists():
                overlapped = not Path(f"{other}.done").exists()
                break
            time.sleep(0.02)
        in_use = test_slots.status()["slots_in_use"]
        own.write_text(json.dumps({"argv": sys.argv[3:], "overlapped": overlapped, "in_use": in_use}))
        Path(f"{own}.done").touch()
        """
    )
    first, second = tmp_path / "first", tmp_path / "second"
    wrapped = [sys.executable, "-m", "scripts.common.test_slots", "run", "--", sys.executable, "-c", probe]
    runs = [
        subprocess.Popen(
            [*wrapped, str(own), str(other), "-n", "2"],
            cwd=REPO_ROOT,
            env=_child_env(**{test_slots.COUNT_ENV: str(size)}),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        for own, other in ((first, second), (second, first))
    ]
    for run in runs:
        _, stderr = run.communicate(timeout=60)
        assert run.returncode == 0, stderr
    results = [json.loads(path.read_text()) for path in (first, second)]
    assert [result["argv"] for result in results] == [["-n", "2"], ["-n", "2"]]
    assert all(result["in_use"] <= size for result in results)
    assert any(result["overlapped"] for result in results) is concurrent
    assert test_slots.status()["slots_in_use"] == 0


def test_a_nested_launch_runs_inside_its_holders_slots() -> None:
    nested = [
        sys.executable,
        "-m",
        "scripts.common.test_slots",
        "run",
        "--",
        sys.executable,
        "-c",
        "print('nested ok')",
    ]
    result = _launch("run", "--", *nested, timeout=30, **{test_slots.COUNT_ENV: "1", test_slots.WAIT_ENV: "5"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "nested ok"


def test_a_dead_holder_marker_is_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(test_slots.HOLDER_ENV, f"2:{tmp_path / 'pool' / 'holders' / 'gone.ticket'}")
    assert test_slots.inherited_hold() is None
    with test_slots.acquire(1, kind="pytest") as hold:
        monkeypatch.setenv(test_slots.HOLDER_ENV, hold.marker())
        assert test_slots.inherited_hold() == 1
    assert test_slots.inherited_hold() is None


def test_launcher_wait_timeout_is_typed_and_shows_the_queue_position() -> None:
    with test_slots.acquire(2, kind="pytest"):
        result = _launch("run", "--", sys.executable, "-c", "print('ran')", **{test_slots.WAIT_ENV: "0.5"})
    assert result.returncode == test_slots.EXIT_REFUSED == 75
    assert "ran" not in result.stdout
    assert "queue position 1/1" in result.stderr
    verdict = json.loads(next(line for line in result.stderr.splitlines() if line.startswith('{"test_slots"')))
    assert verdict["test_slots"]["outcome"] == "refused" and verdict["test_slots"]["reason"] == "wait_timeout"


def test_disabled_pool_runs_the_command_unchanged(pool: Path) -> None:
    result = _launch("run", "--", sys.executable, "-c", PRINTER, "-n", "8", **{test_slots.ENABLE_ENV: "off"})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"argv": ["-n", "8"], "holder": None, "auto": None}
    assert not pool.exists()
