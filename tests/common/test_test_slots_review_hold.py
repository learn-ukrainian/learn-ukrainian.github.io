"""Review holds: a sandboxed reviewer runs inside slots its trusted launcher holds (#11230, #10744).

Codex's read-only sandbox maps only this user, so the pool's root-owned ancestors show the overflow owner, and
it mounts the pool read-only. The governor must keep refusing to prepare a pool there, while a marker its
launcher issued lets the reviewer run inside the launcher's real, host-wide slots. These tests reproduce that
view with an injected ownership map and a pool this user cannot write, and check that the marker is never
trusted beyond the hold it names.
"""

from __future__ import annotations

import contextlib
import errno
import fcntl
import json
import os
import re
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


def test_a_real_read_only_user_namespace_sandbox_runs_only_inside_the_launchers_hold(
    pool: Path, review: test_slots.Hold
) -> None:
    """The reproduction under a real sandbox: unmapped root owners and the launcher's pool read-only at its place."""
    sandbox = _bwrap_at_default(pool)
    if sandbox is None:
        pytest.skip("no unprivileged user-namespace sandbox (bwrap) on this host")
    probe = [sys.executable, "-c", "print('ran inside the review hold')"]

    marked = _sandboxed(sandbox, *probe, **{test_slots.HOLDER_ENV: _inside_marker(review)})
    unmarked = _sandboxed(sandbox, *probe)

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
        "round-1-format",
        "wrong-nonce",
    ],
)
def test_a_forged_or_stale_marker_runs_nothing_inside_slots_it_does_not_hold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    hold = test_slots.acquire(2, kind="review", task_id=TASK)
    _count, nonce, record = hold.marker().split(":", 2)
    env = {key: value for key, value in os.environ.items() if key != test_slots.HOLDER_ENV}
    descriptor = None
    try:
        if case == "malformed":
            env[test_slots.HOLDER_ENV] = f"two:{nonce}:{record}"
        elif case == "missing-ticket":
            env[test_slots.HOLDER_ENV] = f"2:{nonce}:{Path(record).parent / 'missing.ticket'}"
        elif case == "inflated-count":
            env[test_slots.HOLDER_ENV] = f"8:{nonce}:{record}"
        elif case == "deflated-count":
            env[test_slots.HOLDER_ENV] = f"1:{nonce}:{record}"
        elif case == "another-task":
            env.update({test_slots.HOLDER_ENV: hold.marker(), test_slots.TASK_ENV: "impl-other-task"})
        elif case == "counterfeit-outside-the-pool":
            forged = {"kind": "review", "held": 2, "task_id": TASK, "pid": os.getpid(), "nonce": nonce, "slots": [0, 1]}
            path, descriptor = _counterfeit(tmp_path / "elsewhere" / "holders", forged)
            env[test_slots.HOLDER_ENV] = f"2:{nonce}:{path}"
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
            env[test_slots.HOLDER_ENV] = f"2:{nonce}:{link}"
        elif case == "dead-holder":
            env[test_slots.HOLDER_ENV] = hold.marker()
            hold.release()
        elif case == "round-1-format":  # ``<count>:<ticket>`` carries no issued nonce
            env[test_slots.HOLDER_ENV] = f"2:{record}"
        elif case == "wrong-nonce":
            env[test_slots.HOLDER_ENV] = f"2:{nonce[::-1]}:{record}"

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
    nested = None
    try:
        with pytest.raises(test_slots.SlotError) as waited:
            test_slots.join_inherited(env, wait_s=0.3, progress=lambda _line: None)
        assert waited.value.reason == "wait_timeout" and "another test run of this review" in waited.value.detail
        nested = test_slots.join_inherited({**env, **first.environment()}, wait_s=0.3)
        assert nested is not None and nested.count == 2  # the turn's own descendants never wait for it
        first.release()
        # The turn's own run ended, but a run of that turn still runs: the next turn waits for it as well.
        with pytest.raises(test_slots.SlotError) as straggler:
            test_slots.join_inherited(env, wait_s=0.3, progress=lambda _line: None)
        assert straggler.value.reason == "wait_timeout" and "previous test run" in straggler.value.detail
    finally:
        first.release()
        if nested is not None:
            nested.release()
    second = test_slots.join_inherited(env, wait_s=0.3)
    assert second is not None and second.environment()[test_slots.SESSION_ENV].startswith(f"{os.getpid()}:")
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


# ---- round 2 (#11230): forged turns, counterfeit holders, early release, issued nonces -------------------------

# A governed run's command: it records the session value it was given, then, once it has run, when it ran.
RECORDER = textwrap.dedent(
    """\
    import os, sys, time
    start = time.monotonic()
    with open(sys.argv[1], "w") as out:
        out.write(os.environ.get("LU_TEST_SLOTS_SESSION", "-") + "\\n")
    time.sleep(float(sys.argv[2]))
    with open(sys.argv[1], "a") as out:
        out.write(f"{start} {time.monotonic()}\\n")
    """
)


def _record_path(hold: test_slots.Hold) -> Path:
    """The holder ticket a marker names: its last field, whatever fields come before it."""
    return Path(hold.marker().rsplit(":", 1)[1])


def _governed(out: Path, seconds: float, *slots: str, **env: str) -> subprocess.Popen[str]:
    """A real governed test run (``test_slots run``) whose command records when it ran."""
    command = [sys.executable, "-m", "scripts.common.test_slots", "run", *slots, "--"]
    return subprocess.Popen(
        [*command, sys.executable, "-c", RECORDER, str(out), str(seconds)],
        cwd=REPO_ROOT,
        env=_child_env(**env),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _interval(out: Path) -> tuple[float, float] | None:
    """When a recorded run ran, or ``None`` when its command never finished."""
    lines = out.read_text(encoding="utf-8").splitlines() if out.exists() else []
    if len(lines) < 2:
        return None
    start, end = map(float, lines[1].split())
    return start, end


def _most_at_once(intervals: list[tuple[float, float]]) -> int:
    """The largest number of the runs that ran at the same moment."""
    events = sorted([(start, 1) for start, _ in intervals] + [(end, -1) for _, end in intervals])
    running = most = 0
    for _, step in events:  # an end sorts before a start at the same instant: touching runs never overlap
        running += step
        most = max(most, running)
    return most


@pytest.mark.parametrize("value", ["session-path", "copied-token"])
def test_siblings_presenting_a_predictable_session_value_never_share_the_turn(
    tmp_path: Path, read_only_pool: Path, review: test_slots.Hold, value: str
) -> None:
    """Two real sibling runs that present one guessable session value are refused while a run holds the turn."""
    turn_out = tmp_path / "turn"
    turn = _governed(turn_out, 3.0, **review.environment())
    siblings: list[subprocess.Popen[str]] = []
    try:
        token = wait_for_line(turn_out, stop_if=lambda: turn.poll() is not None)
        predictable = (
            str(_record_path(review).with_suffix(test_slots.SESSION_SUFFIX)) if value == "session-path" else token
        )
        siblings = [
            _governed(tmp_path / f"sibling-{index}", 0.3, **review.environment(), LU_TEST_SLOTS_SESSION=predictable)
            for index in range(2)
        ]
        results = [sibling.communicate(timeout=60) for sibling in siblings]
        turn_result = turn.communicate(timeout=60)
    finally:
        for process in (turn, *siblings):
            if process.poll() is None:
                process.kill()
                process.wait(timeout=30)
    ran = [_interval(path) for path in (turn_out, tmp_path / "sibling-0", tmp_path / "sibling-1")]
    assert turn.returncode == 0, turn_result
    assert _most_at_once([interval for interval in ran if interval is not None]) == 1
    for sibling, (_, stderr) in zip(siblings, results, strict=True):
        assert sibling.returncode == test_slots.EXIT_REFUSED, stderr
        assert "test_slots_session_unverified" in stderr


SURVIVING_HOLDER = textwrap.dedent(
    """\
    import os, subprocess, sys, time
    from scripts.common import test_slots

    out, task, ending, recorder = sys.argv[1:5]
    hold = test_slots.acquire(2, kind="review", task_id=task)
    # The CLI stand-in: a shell whose child is the reviewer's governed test run, so that run is a grandchild.
    script = '"$1" -m scripts.common.test_slots run -- "$1" -c "$2" "$3" 4; true'
    subprocess.Popen(["sh", "-c", script, "sh", sys.executable, recorder, out], env={**os.environ, **hold.environment()})
    while not (os.path.exists(out) and open(out).read().endswith("\\n")):
        time.sleep(0.02)
    if ending == "released":
        hold.release()
        open(out + ".released", "w").write("released\\n")
    time.sleep(120)
    """
)


@pytest.mark.parametrize("ending", ["killed", "released"])
def test_slots_stay_taken_while_a_review_test_run_outlives_its_holder(tmp_path: Path, pool: Path, ending: str) -> None:
    """The pool cap holds: a replacement run never starts while the review's surviving grandchild still runs."""
    survivor_out = tmp_path / "survivor"
    holder = subprocess.Popen(
        [sys.executable, "-c", SURVIVING_HOLDER, str(survivor_out), TASK, ending, RECORDER],
        cwd=REPO_ROOT,
        env=_child_env(),
        start_new_session=True,  # its own process group, so cleanup reaches the shell and the survivor
    )
    try:
        wait_for_line(survivor_out, stop_if=lambda: holder.poll() is not None)
        if ending == "killed":
            holder.send_signal(signal.SIGKILL)
            holder.wait(timeout=30)
        else:
            wait_for_line(Path(f"{survivor_out}.released"), stop_if=lambda: holder.poll() is not None)
        report = test_slots.status()  # the holder's record is gone, but its surviving run still takes both slots
        assert (report["slots_in_use"], report["slots_draining"], report["slots_free"]) == (0, 2, 0)
        replacement_out = tmp_path / "replacement"
        replacement = _governed(replacement_out, 0.2, "--slots", "2", **{test_slots.WAIT_ENV: "60"})
        _, stderr = replacement.communicate(timeout=90)
        assert replacement.returncode == 0, stderr
        deadline = time.monotonic() + 30
        while _interval(survivor_out) is None and time.monotonic() < deadline:
            time.sleep(0.05)
        survivor, replaced = _interval(survivor_out), _interval(replacement_out)
        assert survivor is not None and replaced is not None
        # Each run holds both of the pool's two slots, so two at once would be four slots in use.
        assert 2 * _most_at_once([survivor, replaced]) <= 2
        assert replaced[0] >= survivor[1]
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(holder.pid, signal.SIGKILL)
        if holder.poll() is None:
            holder.wait(timeout=30)


def _forged_ticket(directory: Path, record: dict[str, object]) -> tuple[Path, int]:
    """A locked, hand-written holder ticket in ``directory``; the caller closes the descriptor."""
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    path = directory / "00000000000000000009-forged.ticket"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
    os.write(fd, json.dumps(record).encode())
    fcntl.flock(fd, fcntl.LOCK_EX)
    return path, fd


@pytest.mark.parametrize(
    "claim", ["free-slots", "free-slots-with-forged-slot-files", "another-runs-slots", "the-holds-own-slots"]
)
def test_a_hand_forged_ticket_in_the_launchers_pool_is_refused(
    monkeypatch: pytest.MonkeyPatch, pool: Path, claim: str
) -> None:
    """A locked copy of a real record claiming slots it does not hold never verifies; the real hold still does."""
    monkeypatch.setenv(test_slots.COUNT_ENV, "4")
    genuine = test_slots.acquire(2, kind="review", task_id=TASK)
    other = test_slots.acquire(2, kind="pytest", task_id="impl-other-task") if claim == "another-runs-slots" else None
    descriptor = None
    try:
        record = json.loads(_record_path(genuine).read_text(encoding="utf-8"))
        claimed = {"another-runs-slots": [2, 3], "the-holds-own-slots": record["slots"]}.get(claim, [2, 3])
        forged, descriptor = _forged_ticket(pool / "holders", {**record, "slots": claimed})
        if claim == "free-slots-with-forged-slot-files":  # the forger also writes the pool's slot records
            for index in claimed:
                claim_record = {"ticket": forged.name, "nonce": record["nonce"]}
                (pool / f"slot-{index:03d}.lock").write_text(json.dumps(claim_record), encoding="utf-8")
        env = {**os.environ, test_slots.HOLDER_ENV: genuine.marker().replace(str(_record_path(genuine)), str(forged))}

        assert test_slots.inherited_hold(env) is None
        assert test_slots.join_inherited(env) is None
        assert test_slots.inherited_hold({**os.environ, test_slots.HOLDER_ENV: genuine.marker()}) == 2
    finally:
        if descriptor is not None:
            os.close(descriptor)
        genuine.release()
        if other is not None:
            other.release()


def test_a_session_token_naming_a_descriptor_without_the_turns_lock_is_refused(review: test_slots.Hold) -> None:
    """The named process must hold the turn's lock through the named descriptor, not merely have the file open."""
    env = _marked(review)
    turn = test_slots.join_inherited(env)
    assert turn is not None
    session = _record_path(review).with_suffix(test_slots.SESSION_SUFFIX)
    unlocked = os.open(session, os.O_RDONLY)  # this process is its own ancestor and has the session file open
    try:
        token = f"{os.getpid()}:{test_slots._start_ticks(os.getpid())}:{unlocked}"
        with pytest.raises(test_slots.SlotError) as refused:
            test_slots.join_inherited({**env, test_slots.SESSION_ENV: token}, wait_s=0.3)
        assert refused.value.reason == "session_unverified" and "does not hold" in refused.value.detail
        nested = test_slots.join_inherited({**env, **turn.environment()}, wait_s=0.3)  # the locking descriptor
        assert nested is not None
        nested.release()
    finally:
        os.close(unlocked)
        turn.release()


def test_a_hand_written_ticket_in_a_pool_the_caller_created_is_refused(tmp_path: Path, review: test_slots.Hold) -> None:
    caller_pool = tmp_path / "caller-pool"
    record = json.loads(_record_path(review).read_text(encoding="utf-8"))
    forged, descriptor = _forged_ticket(caller_pool / "holders", record)
    try:
        env = {
            **os.environ,
            test_slots.DIR_ENV: str(caller_pool),
            test_slots.HOLDER_ENV: review.marker().replace(str(_record_path(review)), str(forged)),
        }
        assert test_slots.inherited_hold(env) is None
        assert test_slots.join_inherited(env) is None
    finally:
        os.close(descriptor)


def test_each_hold_issues_its_own_nonce_and_a_marker_must_carry_it(monkeypatch: pytest.MonkeyPatch, pool: Path) -> None:
    """The nonce is minted at issue, never the ambient run nonce, and a marker with any other value is refused."""
    ambient = "ambient0run0nonce"
    monkeypatch.setenv(test_slots.COUNT_ENV, "4")
    monkeypatch.setenv("LU_RUNTIME_RUN_NONCE", ambient)
    first = test_slots.acquire(2, kind="review", task_id=TASK)
    second = test_slots.acquire(2, kind="review", task_id=TASK)
    try:
        nonces = [json.loads(_record_path(hold).read_text(encoding="utf-8"))["nonce"] for hold in (first, second)]
        assert all(re.fullmatch(r"[0-9a-f]{32}", nonce) for nonce in nonces) and nonces[0] != nonces[1]
        count, nonce, record = first.marker().split(":", 2)
        assert nonce == nonces[0] and ambient not in first.marker()
        for wrong in (nonces[1], ambient, "0" * 32, ""):
            assert test_slots.inherited_hold({**os.environ, test_slots.HOLDER_ENV: f"{count}:{wrong}:{record}"}) is None
        assert test_slots.inherited_hold({**os.environ, test_slots.HOLDER_ENV: first.marker()}) == 2
    finally:
        first.release()
        second.release()


# ---- the real sandbox: the launcher's pool at its fixed location ---------------------------------------------


def _kept_visible() -> list[str]:
    """Bind the checkout and the interpreter back over the sandbox's empty scratch parent, wherever they live."""
    return [option for path in (REPO_ROOT, Path(sys.prefix)) for option in ("--ro-bind", str(path), str(path))]


def _bwrap_at_default(pool: Path) -> list[str] | None:
    """Codex's view with ``pool`` mounted read-only where a sandboxed run must find it: the default location."""
    sandbox = _bwrap()
    if sandbox is None:
        return None
    inside = test_slots.DEFAULT_SCRATCH_ROOT / f"test-slots-{os.geteuid()}"
    mounts = ["--tmpfs", str(inside.parent.parent), *_kept_visible(), "--dir", str(inside.parent)]
    mounts += ["--ro-bind", os.path.realpath(pool), str(inside)]
    return [*sandbox[:-1], *mounts, sandbox[-1]]


def _inside_marker(hold: test_slots.Hold) -> str:
    """``hold``'s marker as the sandbox sees it: its ticket in the pool mounted at the default location."""
    ticket = _record_path(hold)
    inside = test_slots.DEFAULT_SCRATCH_ROOT / f"test-slots-{os.geteuid()}" / "holders" / ticket.name
    return f"{hold.marker()[: -len(str(ticket))]}{inside}"


# Variables that select a pool or name a hold; a sandboxed run gets only those a test sets on purpose.
_POOL_SELECTORS = (test_slots.DIR_ENV, test_slots.SCRATCH_ROOT_ENV, test_slots.HOLDER_ENV)


def _sandboxed(prefix: list[str], *command: str, **env: str) -> subprocess.CompletedProcess[str]:
    """Run ``test_slots run -- <command>`` in ``prefix`` with no pool override unless ``env`` sets one."""
    base = {key: value for key, value in _child_env().items() if key not in _POOL_SELECTORS}
    return subprocess.run(
        [*prefix, sys.executable, "-m", "scripts.common.test_slots", "run", "--slots", "1", "--", *command],
        cwd=REPO_ROOT,
        env={**base, test_slots.WAIT_ENV: "1", **env},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize("override", [test_slots.DIR_ENV, test_slots.SCRATCH_ROOT_ENV])
def test_a_sandboxed_run_refuses_a_pool_override_even_for_a_complete_pool_it_points_at(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, override: str
) -> None:
    """A sandboxed process cannot select the pool: a real pool at a caller-chosen place is refused, typed."""
    sandbox = _bwrap()
    if sandbox is None:
        pytest.skip("no unprivileged user-namespace sandbox (bwrap) on this host")
    scratch = tmp_path / "caller-scratch"
    caller_pool = scratch / f"test-slots-{os.geteuid()}" if override == test_slots.SCRATCH_ROOT_ENV else scratch
    monkeypatch.setenv(test_slots.DIR_ENV, str(caller_pool))
    with test_slots.acquire(2, kind="review", task_id=TASK) as caller_hold:
        result = _sandboxed(
            sandbox,
            sys.executable,
            "-c",
            "print('ran inside a pool the caller chose')",
            **{override: str(scratch), test_slots.HOLDER_ENV: caller_hold.marker()},
        )
    assert result.returncode == test_slots.EXIT_REFUSED, result.stdout
    assert "ran inside" not in result.stdout
    assert "test_slots_pool_override_refused" in result.stderr


def test_a_sandboxed_run_may_join_only_a_review_hold(pool: Path) -> None:
    sandbox = _bwrap_at_default(pool)
    if sandbox is None:
        pytest.skip("no unprivileged user-namespace sandbox (bwrap) on this host")
    with test_slots.acquire(2, kind="launcher", task_id=TASK) as launcher_hold:
        result = _sandboxed(
            sandbox, sys.executable, "-c", "print('ran')", **{test_slots.HOLDER_ENV: _inside_marker(launcher_hold)}
        )
    assert result.returncode == test_slots.EXIT_REFUSED and "ran" not in result.stdout


def test_a_sandboxed_turn_serves_its_own_descendants_but_not_a_sibling_holding_its_token(
    tmp_path: Path, pool: Path, review: test_slots.Hold
) -> None:
    """Inside Codex's pid namespace a nested run of the turn joins it; a sibling with the copied token cannot."""
    sandbox = _bwrap_at_default(pool)
    if sandbox is None:
        pytest.skip("no unprivileged user-namespace sandbox (bwrap) on this host")
    marker = {test_slots.HOLDER_ENV: _inside_marker(review)}
    # A real child of the turn (subprocess closes the turn's descriptors), not the turn's own exec'd command.
    nested = "import subprocess, sys; sys.exit(subprocess.call([sys.executable, '-m', 'scripts.common.test_slots', 'run', '--', sys.executable, '-c', 'print(\"nested\")']))"
    joined = _sandboxed(sandbox, sys.executable, "-c", nested, **marker)
    assert joined.returncode == 0, joined.stderr
    assert joined.stdout.strip() == "nested"

    token_out = tmp_path / "token"
    turn = subprocess.Popen(
        [
            *sandbox,
            "--bind",
            str(tmp_path),
            str(tmp_path),
            sys.executable,
            "-m",
            "scripts.common.test_slots",
            "run",
            "--",
            sys.executable,
            "-c",
            RECORDER,
            str(token_out),
            "3",
        ],
        cwd=REPO_ROOT,
        env={**{key: value for key, value in _child_env().items() if key not in _POOL_SELECTORS}, **marker},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        token = wait_for_line(token_out, stop_if=lambda: turn.poll() is not None)
        sibling = _sandboxed(sandbox, sys.executable, "-c", "print('ran')", **marker, LU_TEST_SLOTS_SESSION=token)
        assert sibling.returncode == test_slots.EXIT_REFUSED and "ran" not in sibling.stdout
        assert "test_slots_session_unverified" in sibling.stderr
        assert turn.wait(timeout=60) == 0
    finally:
        if turn.poll() is None:
            turn.kill()
            turn.wait(timeout=30)


# A governed run whose command starts a governed child run, the shape of a test that starts pytest.
NESTED_RUN = (
    "import subprocess, sys; sys.exit(subprocess.call([sys.executable, '-m', 'scripts.common.test_slots', 'run', "
    "'--', sys.executable, '-c', 'print(\"nested ran\")']))"
)


def test_a_child_of_the_turn_joins_it_without_waiting(read_only_pool: Path, review: test_slots.Hold) -> None:
    """A real child (its descriptors closed by ``subprocess``) proves its ancestry and runs inside the turn."""
    started = time.monotonic()
    result = _launch("run", "--", sys.executable, "-c", NESTED_RUN, **review.environment(), LU_TEST_SLOTS_WAIT_S="2")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "nested ran"
    assert "waiting" not in result.stderr and time.monotonic() - started < 30


def test_a_turn_whose_slots_changed_hands_while_it_joined_gets_nothing_and_keeps_nothing(
    monkeypatch: pytest.MonkeyPatch, review: test_slots.Hold
) -> None:
    env = _marked(review)
    real_share = test_slots._share

    def slots_taken(path: Path) -> int | None:
        return None if path.name.startswith("slot-") else real_share(path)

    monkeypatch.setattr(test_slots, "_share", slots_taken)
    assert test_slots.join_inherited(env, wait_s=0.3) is None
    monkeypatch.setattr(test_slots, "_share", real_share)
    joined = test_slots.join_inherited(env, wait_s=0.3)  # nothing of the refused join is still held
    assert joined is not None
    joined.release()


def _slot_free(pool: Path, index: int) -> bool:
    """Whether no process holds slot ``index``'s file in any mode."""
    fd = os.open(test_slots._slot_path(pool, index), os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    finally:
        os.close(fd)
    return True


@pytest.mark.parametrize("kind", ["launcher", "pytest", "review"])
def test_an_xdist_worker_keeps_the_slots_after_the_run_that_issued_them_ends(pool: Path, kind: str) -> None:
    """A worker's join holds every slot shared, so they stay taken until the worker lets go; a stale one gets none."""
    hold = test_slots.acquire(2, kind=kind, task_id=TASK)
    turn = None
    try:
        env = _marked(hold)
        if kind == "review":
            assert test_slots.join_as_worker(env) is None  # no turn token: a worker never waits for or takes a turn
            turn = test_slots.join_inherited(env)
            assert turn is not None
            env = {**env, **turn.environment()}
        worker = test_slots.join_as_worker(env)
        assert worker is not None and worker.count == 2
    finally:
        if turn is not None:
            turn.release()
        hold.release()
    assert [index for index in range(2) if _slot_free(pool, index)] == []
    assert test_slots.join_as_worker(env) is None  # the issuing hold has ended: nothing new to join
    worker.release()
    assert [index for index in range(2) if not _slot_free(pool, index)] == []


def test_a_worker_whose_hold_changed_hands_while_it_joined_is_refused_and_keeps_nothing(
    monkeypatch: pytest.MonkeyPatch, pool: Path
) -> None:
    """A successor holds its slots shared too, so only the re-check after sharing tells the worker its hold ended.

    The worker was named by a live hold, so it is refused, typed, rather than left to run tests on no slot.
    """
    hold = test_slots.acquire(2, kind="launcher", task_id=TASK)
    env = _marked(hold)
    real_share_slots = test_slots._share_slots
    successors: list[test_slots.Hold] = []

    def changing_hands(found: object, descriptors: list[int]) -> bool:
        hold.release()  # the controller's hold ends after the worker checked it, and another run takes the slots
        successors.append(test_slots.acquire(2, kind="pytest", task_id=TASK))
        return real_share_slots(found, descriptors)

    monkeypatch.setattr(test_slots, "_share_slots", changing_hands)
    try:
        with pytest.raises(test_slots.SlotError) as refused:
            test_slots.join_as_worker(env)
        assert refused.value.reason == "hold_ended"
    finally:
        hold.release()
        for successor in successors:
            successor.release()
    assert len(successors) == 1
    assert [index for index in range(2) if not _slot_free(pool, index)] == []


@pytest.mark.parametrize("kind", ["launcher", "review"])
def test_a_worker_its_hold_names_but_cannot_share_a_slot_is_refused(
    monkeypatch: pytest.MonkeyPatch, pool: Path, kind: str
) -> None:
    """A slot another run holds alone means the hold ended; a worker the hold named is refused, not left unreserved."""
    hold = test_slots.acquire(2, kind=kind, task_id=TASK)
    turn = None
    try:
        env = _marked(hold)
        if kind == "review":
            turn = test_slots.join_inherited(env)
            assert turn is not None
            env = {**env, **turn.environment()}
        monkeypatch.setattr(test_slots, "_share_slots", lambda found, descriptors: False)
        with pytest.raises(test_slots.SlotError) as refused:
            test_slots.join_as_worker(env)
        assert refused.value.reason == "hold_ended"
    finally:
        if turn is not None:
            turn.release()
        hold.release()
    assert [index for index in range(2) if not _slot_free(pool, index)] == []


@pytest.mark.parametrize("failing", [1, 2])
@pytest.mark.parametrize("joining", ["turn", "nested", "xdist-worker"])
def test_a_slot_that_cannot_be_opened_while_joining_keeps_no_slot_held(
    monkeypatch: pytest.MonkeyPatch, pool: Path, failing: int, joining: str
) -> None:
    """An open failure on a later slot refuses the join, typed, and the slots it opened before stay unheld."""
    monkeypatch.setenv(test_slots.COUNT_ENV, "3")
    hold = test_slots.acquire(3, kind="review", task_id=TASK)
    turn = None
    try:
        env = _marked(hold)
        if joining != "turn":  # a run of the turn, or a worker it started, presents the turn's token
            turn = test_slots.join_inherited(env)
            assert turn is not None
            env = {**env, **turn.environment()}
        unopenable = test_slots._slot_path(pool, failing).name
        real_open = os.open

        def opening(path: object, flags: int, *args: object, **kwargs: object) -> int:
            # Only the join's own open of the slot fails; the marker's ownership check reads it first and must pass.
            if Path(os.fspath(path)).name == unopenable and sys._getframe(1).f_code.co_name == "_share":
                raise OSError(errno.EIO, "injected open failure")
            return real_open(path, flags, *args, **kwargs)

        with monkeypatch.context() as patched:
            patched.setattr(test_slots.os, "open", opening)
            with pytest.raises(test_slots.SlotError) as refused:
                if joining == "xdist-worker":
                    test_slots.join_as_worker(env)
                else:
                    test_slots.join_inherited(env, wait_s=0.3)
        assert refused.value.reason == "pool_unavailable"
    finally:
        if turn is not None:
            turn.release()
        hold.release()
    shared_lock_retained_after_refusal = [index for index in range(3) if not _slot_free(pool, index)]
    assert shared_lock_retained_after_refusal == []
