"""Review holds: a sandboxed reviewer runs inside slots its trusted launcher holds (#11230, #10744).

Codex's read-only sandbox maps only this user, so the pool's root-owned ancestors show the overflow owner, and
it mounts the pool read-only. The governor must keep refusing to prepare a pool there, while a marker its
launcher issued lets the reviewer run inside the launcher's real, host-wide slots. These tests reproduce that
view with an injected ownership map and a pool this user cannot write, and check that the marker is never
trusted beyond the hold it names.
"""

from __future__ import annotations

import errno
import fcntl
import json
import os
import signal
import stat
import subprocess
import sys
import textwrap
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.common import test_slots
from tests.common.test_test_slots import UNSAFE_POOL_PATHS, _unsafe_pool_path
from tests.wait_helpers import wait_for_line

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK = "review-11230-fixture"
OVERFLOW_UID = 65534  # the kernel's overflow uid: how a user namespace shows an unmapped owner

# Root reads and writes regardless of mode and owns the inodes the sandbox view remaps.
pytestmark = pytest.mark.skipif(
    os.geteuid() == 0, reason="the sandbox view and an unwritable pool need a non-root user"
)


@pytest.fixture(autouse=True)
def pool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A private two-slot pool per test, run as dispatch task ``TASK``; no outer marker leaks in."""
    path = tmp_path / "pool"
    monkeypatch.setenv(test_slots.ENABLE_ENV, "on")
    monkeypatch.setenv(test_slots.DIR_ENV, str(path))
    monkeypatch.setenv(test_slots.COUNT_ENV, "2")
    monkeypatch.delenv(test_slots.WAIT_ENV, raising=False)
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    monkeypatch.delenv(test_slots.SESSION_ENV, raising=False)
    monkeypatch.setenv(test_slots.TASK_ENV, TASK)
    return path


@pytest.fixture
def review(pool: Path) -> Iterator[test_slots.Hold]:
    """The launcher's review hold, taken on the trusted side with the full ownership walk."""
    with test_slots.acquire(2, kind="review", task_id=TASK) as hold:
        yield hold


def _sandbox_view(monkeypatch: pytest.MonkeyPatch) -> None:
    """Show every root-owned inode as the overflow owner, as a user namespace mapping only this user does."""

    def reporting(original):
        def report(*args: object, **kwargs: object) -> os.stat_result:
            info = original(*args, **kwargs)
            if info.st_uid != 0:
                return info
            fields = list(info[:10])
            fields[4] = OVERFLOW_UID
            return os.stat_result(fields)

        return report

    for name in ("lstat", "stat", "fstat"):
        monkeypatch.setattr(test_slots.os, name, reporting(getattr(os, name)))


@pytest.fixture
def read_only_pool(pool: Path, review: test_slots.Hold) -> Iterator[Path]:
    """The pool as the sandbox mounts it: this user can read it and lock its files, but not write it."""
    directories = [pool, pool / "queue", pool / "holders"]
    for directory in directories:
        directory.chmod(0o500)
    try:
        yield pool
    finally:
        for directory in directories:
            directory.chmod(0o700)


def _marked(hold: test_slots.Hold, **extra: str) -> dict[str, str]:
    return {**os.environ, **hold.environment(), **extra}


def _child_env(**extra: str) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key != test_slots.XDIST_AUTO_ENV}
    env["PYTHONPATH"] = str(REPO_ROOT)
    env.update(extra)
    return env


def _launch(*command: str, timeout: float = 60, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scripts.common.test_slots", *command],
        cwd=REPO_ROOT,
        env=_child_env(**env),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---- the sandbox view -----------------------------------------------------------------------------------------


def test_the_sandbox_view_refuses_its_own_pool_but_runs_inside_the_launchers_hold(
    monkeypatch: pytest.MonkeyPatch, review: test_slots.Hold
) -> None:
    """The reproduction: an unmapped owner on ``/`` refuses acquisition; the launcher's marker still serves."""
    _sandbox_view(monkeypatch)
    assert os.lstat("/").st_uid == OVERFLOW_UID  # the view is in force: root shows as the overflow owner

    with pytest.raises(test_slots.SlotError) as refused:
        test_slots.acquire(1, kind="pytest", wait_s=0.1)
    joined = test_slots.join_inherited(_marked(review))

    assert refused.value.reason == "pool_unavailable"
    assert "a directory owned by another user" in refused.value.detail
    assert joined is not None and joined.count == 2
    joined.release()


def test_a_marked_run_never_writes_the_pool(read_only_pool: Path, review: test_slots.Hold) -> None:
    """A run inside the hold only reads: the pool stays unwritable, and a write attempt would have repaired it."""
    command = ("run", "--slots", "1", "--", sys.executable, "-c", "print('ran inside the review hold')")

    marked = _launch(*command, **review.environment(), **{test_slots.WAIT_ENV: "1"})

    assert marked.returncode == 0, marked.stderr
    assert marked.stdout.strip() == "ran inside the review hold"
    for directory in (read_only_pool, read_only_pool / "queue", read_only_pool / "holders"):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o500
    assert test_slots.status()["slots_in_use"] == 2  # only the launcher's hold: the marked run took nothing


def _bwrap() -> list[str] | None:
    """A read-only, user-namespaced sandbox like Codex's (only this user mapped), or ``None`` where unavailable."""
    prefix = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--unshare-user", "--unshare-pid"]
    probe = [*prefix, "--die-with-parent", sys.executable, "-I", "-c", "import os; print(os.lstat('/').st_uid)"]
    try:
        result = subprocess.run(probe, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return [*prefix, "--die-with-parent"] if result.stdout.strip() == str(OVERFLOW_UID) else None


def test_a_real_read_only_user_namespace_sandbox_runs_only_inside_the_launchers_hold(review: test_slots.Hold) -> None:
    """The reproduction under a real sandbox: unmapped root owners and a read-only pool, as Codex shows them."""
    sandbox = _bwrap()
    if sandbox is None:
        pytest.skip("no unprivileged user-namespace sandbox (bwrap) on this host")
    command = [*sandbox, sys.executable, "-m", "scripts.common.test_slots", "run", "--slots", "1", "--"]
    probe = [sys.executable, "-c", "print('ran inside the review hold')"]

    def run(**extra: str) -> subprocess.CompletedProcess[str]:
        env = _child_env(**{test_slots.WAIT_ENV: "1", **extra})
        return subprocess.run(
            [*command, *probe], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60, check=False
        )

    marked, unmarked = run(**review.environment()), run()

    assert marked.returncode == 0, marked.stderr
    assert marked.stdout.strip() == "ran inside the review hold"
    assert unmarked.returncode == test_slots.EXIT_REFUSED and "ran" not in unmarked.stdout
    assert "a directory owned by another user" in unmarked.stderr
    assert test_slots.status()["slots_in_use"] == 2


@pytest.mark.parametrize("case", sorted(UNSAFE_POOL_PATHS))
def test_the_launcher_still_refuses_every_pool_another_user_could_redirect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    """The trusted side keeps every refusal: a review hold is never taken on an unsafe pool path."""
    path, absent = _unsafe_pool_path(tmp_path, monkeypatch, case)
    monkeypatch.setenv(test_slots.DIR_ENV, str(path))

    with pytest.raises(test_slots.SlotError) as refused:
        test_slots.acquire(2, kind="review", task_id=TASK, wait_s=0.1)

    assert refused.value.reason == "pool_unavailable" and UNSAFE_POOL_PATHS[case] in refused.value.detail
    assert not any(os.path.lexists(entry) for entry in absent)


def test_a_marker_never_lets_acquisition_skip_the_ownership_walk(
    monkeypatch: pytest.MonkeyPatch, review: test_slots.Hold
) -> None:
    """Acquiring new slots ignores any marker: under the sandbox view it is refused even beside a live hold."""
    monkeypatch.setenv(test_slots.HOLDER_ENV, review.marker())
    _sandbox_view(monkeypatch)
    with pytest.raises(test_slots.SlotError) as refused:
        test_slots.acquire(1, kind="review", task_id=TASK, wait_s=0.1)
    assert refused.value.reason == "pool_unavailable"


# ---- the marker is checked, not trusted -----------------------------------------------------------------------


def _counterfeit(directory: Path, record: dict[str, object]) -> tuple[Path, int]:
    """A locked ticket with a plausible record, published outside the launcher's pool."""
    directory.mkdir(parents=True, mode=0o700)
    path = directory / "00000000000000000001-counterfeit.ticket"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
    os.write(fd, json.dumps(record).encode())
    fcntl.flock(fd, fcntl.LOCK_EX)
    return path, fd


@pytest.mark.parametrize(
    "case",
    [
        "absent",
        "malformed",
        "missing-ticket",
        "inflated-count",
        "deflated-count",
        "another-task",
        "counterfeit-outside-the-pool",
        "another-users-ticket",
        "linked-ticket",
        "dead-holder",
    ],
)
def test_a_forged_or_stale_marker_runs_nothing_inside_slots_it_does_not_hold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    hold = test_slots.acquire(2, kind="review", task_id=TASK)
    record = hold.marker().partition(":")[2]
    env = {key: value for key, value in os.environ.items() if key != test_slots.HOLDER_ENV}
    descriptor = None
    try:
        if case == "malformed":
            env[test_slots.HOLDER_ENV] = f"two:{record}"
        elif case == "missing-ticket":
            env[test_slots.HOLDER_ENV] = f"2:{Path(record).parent / 'missing.ticket'}"
        elif case == "inflated-count":
            env[test_slots.HOLDER_ENV] = f"8:{record}"
        elif case == "deflated-count":
            env[test_slots.HOLDER_ENV] = f"1:{record}"
        elif case == "another-task":
            env.update({test_slots.HOLDER_ENV: hold.marker(), test_slots.TASK_ENV: "impl-other-task"})
        elif case == "counterfeit-outside-the-pool":
            forged = {"kind": "review", "held": 2, "task_id": TASK, "pid": os.getpid()}
            path, descriptor = _counterfeit(tmp_path / "elsewhere" / "holders", forged)
            env[test_slots.HOLDER_ENV] = f"2:{path}"
        elif case == "another-users-ticket":
            env[test_slots.HOLDER_ENV] = hold.marker()
            real_fstat = os.fstat
            ticket = os.stat(record)

            def foreign(fd: int) -> os.stat_result:
                info = real_fstat(fd)
                if (info.st_dev, info.st_ino) != (ticket.st_dev, ticket.st_ino):
                    return info
                fields = list(info[:10])
                fields[4] = os.geteuid() + 1
                return os.stat_result(fields)

            monkeypatch.setattr(test_slots.os, "fstat", foreign)
        elif case == "linked-ticket":
            link = Path(record).with_name("00000000000000000002-link.ticket")
            link.symlink_to(record)
            env[test_slots.HOLDER_ENV] = f"2:{link}"
        elif case == "dead-holder":
            env[test_slots.HOLDER_ENV] = hold.marker()
            hold.release()

        assert test_slots.inherited_hold(env) is None
        assert test_slots.join_inherited(env) is None
    finally:
        hold.release()
        if descriptor is not None:
            os.close(descriptor)


@pytest.mark.parametrize("task", [TASK, None])
def test_the_holders_own_task_and_a_run_without_a_task_stay_inside_the_hold(
    review: test_slots.Hold, task: str | None
) -> None:
    """The suite runs its tests without the agent's identity, so a nested run naming no task keeps inheriting."""
    env = _marked(review)
    if task is None:
        env.pop(test_slots.TASK_ENV)
    assert test_slots.inherited_hold(env) == 2


def test_a_marker_for_another_pool_is_refused(tmp_path: Path, review: test_slots.Hold) -> None:
    env = _marked(review, **{test_slots.DIR_ENV: str(tmp_path / "another-pool")})
    assert test_slots.inherited_hold(env) is None


# ---- one review, one test run at a time -----------------------------------------------------------------------


def test_runs_of_one_review_take_turns_on_its_hold(review: test_slots.Hold) -> None:
    env = _marked(review)
    first = test_slots.join_inherited(env)
    assert first is not None
    try:
        with pytest.raises(test_slots.SlotError) as waited:
            test_slots.join_inherited(env, wait_s=0.3, progress=lambda _line: None)
        assert waited.value.reason == "wait_timeout" and "another test run of this review" in waited.value.detail
        nested = test_slots.join_inherited({**env, **first.environment()}, wait_s=0.3)
        assert nested is not None and nested.count == 2  # the turn's own descendants never wait for it
    finally:
        first.release()
    second = test_slots.join_inherited(env, wait_s=0.3)
    assert (
        second is not None
        and second.environment()[test_slots.SESSION_ENV] == first.environment()[test_slots.SESSION_ENV]
    )
    second.release()


def test_other_holds_keep_per_run_inheritance(pool: Path) -> None:
    with test_slots.acquire(2, kind="launcher") as hold:
        env = _marked(hold)
        first, second = test_slots.join_inherited(env), test_slots.join_inherited(env, wait_s=0.1)
        assert first is not None and second is not None and first.environment() == second.environment() == {}
        assert not list((pool / "holders").glob(f"*{test_slots.SESSION_SUFFIX}"))


def test_a_run_waiting_for_its_turn_gets_nothing_once_the_holder_ends(review: test_slots.Hold) -> None:
    env = _marked(review)
    first = test_slots.join_inherited(env)
    assert first is not None
    review.release()
    first.release()
    assert test_slots.join_inherited(env, wait_s=0.3) is None


# Each run records when it starts and ends; the two must never overlap inside one review hold.
INTERVAL = "import sys, time; start = time.monotonic(); time.sleep(0.6); print(start, time.monotonic())"


def test_concurrent_governed_runs_of_one_review_never_overlap(read_only_pool: Path, review: test_slots.Hold) -> None:
    command = [sys.executable, "-m", "scripts.common.test_slots", "run", "--", sys.executable, "-c", INTERVAL]
    runs = [
        subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            env=_child_env(**review.environment()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(2)
    ]
    outputs = [run.communicate(timeout=60) for run in runs]
    assert all(run.returncode == 0 for run in runs), outputs
    (first_start, first_end), (second_start, _second_end) = sorted(
        tuple(map(float, stdout.split())) for stdout, _ in outputs
    )
    assert second_start >= first_end > first_start
    assert any("another test run of this review" in stderr for _, stderr in outputs)


# ---- lifetime and cleanup -------------------------------------------------------------------------------------


def test_releasing_a_review_hold_removes_its_record_and_session_lock(pool: Path) -> None:
    hold = test_slots.acquire(2, kind="review", task_id=TASK)
    holders = pool / "holders"
    assert len(list(holders.glob("*.ticket"))) == len(list(holders.glob(f"*{test_slots.SESSION_SUFFIX}"))) == 1
    session = next(holders.glob(f"*{test_slots.SESSION_SUFFIX}"))
    assert stat.S_IMODE(session.stat().st_mode) == 0o600 and session.stat().st_uid == os.geteuid()
    hold.release()
    assert list(holders.iterdir()) == []
    assert test_slots.status()["slots_in_use"] == 0


KILLED_HOLDER = textwrap.dedent(
    """\
    import sys, time
    from scripts.common import test_slots

    hold = test_slots.acquire(2, kind="review", task_id=sys.argv[2])
    open(sys.argv[1], "w").write(hold.marker() + "\\n")
    time.sleep(120)
    """
)


def test_a_killed_review_holder_frees_its_slots_and_its_session_lock_is_reaped(tmp_path: Path, pool: Path) -> None:
    out = tmp_path / "marker"
    child = subprocess.Popen([sys.executable, "-c", KILLED_HOLDER, str(out), TASK], cwd=REPO_ROOT, env=_child_env())
    try:
        marker = wait_for_line(out, stop_if=lambda: child.poll() is not None).strip()
        assert test_slots.inherited_hold({**os.environ, test_slots.HOLDER_ENV: marker}) == 2
        child.send_signal(signal.SIGKILL)
        child.wait(timeout=30)
        assert test_slots.inherited_hold({**os.environ, test_slots.HOLDER_ENV: marker}) is None
        with test_slots.acquire(2, kind="pytest", wait_s=5) as hold:  # both slots came back at once
            assert hold.count == 2
        assert list((pool / "holders").glob(f"*{test_slots.SESSION_SUFFIX}")) == []
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=30)


def test_a_session_lock_that_cannot_be_created_refuses_the_hold_and_leaves_nothing(
    pool: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_open = os.open

    def failing(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if str(path).endswith(test_slots.SESSION_SUFFIX):
            raise OSError(errno.ENOSPC, "no space left on device")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(test_slots.os, "open", failing)
    with pytest.raises(test_slots.SlotError) as refused:
        test_slots.acquire(2, kind="review", task_id=TASK, wait_s=0.5)
    monkeypatch.setattr(test_slots.os, "open", real_open)

    assert refused.value.reason == "pool_unavailable"
    assert list((pool / "holders").iterdir()) == [] and list((pool / "queue").iterdir()) == []
    with test_slots.acquire(2, kind="pytest", wait_s=0.5) as hold:
        assert hold.count == 2


def test_status_shows_a_review_hold_by_task_without_paths(review: test_slots.Hold, pool: Path) -> None:
    report = test_slots.status()
    assert [(entry["task_id"], entry["kind"], entry["slots"]) for entry in report["holders"]] == [(TASK, "review", 2)]
    assert str(pool) not in json.dumps(report)


def test_a_session_wait_reports_progress_and_never_waits_past_its_limit(review: test_slots.Hold) -> None:
    env = _marked(review)
    first = test_slots.join_inherited(env)
    lines: list[str] = []
    started = time.monotonic()
    try:
        with pytest.raises(test_slots.SlotError):
            test_slots.join_inherited(env, wait_s=0.4, progress=lines.append)
    finally:
        assert first is not None
        first.release()
    assert 0.4 <= time.monotonic() - started < 5
    assert lines and lines[0].startswith("TEST SLOTS: waiting for another test run of this review")
