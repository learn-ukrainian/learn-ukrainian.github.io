"""The watchdog's SIGABRT dump: armed at start-up, private and bounded (#10674)."""

from __future__ import annotations

import fcntl
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.rag import hang_diagnostics as hd

ROOT = Path(__file__).resolve().parents[2]

ABORT_CHILD = """\
import ctypes, os, resource, sys, threading
sys.path.insert(0, sys.argv[1])
from scripts.rag.hang_diagnostics import arm_abort_dump

name = arm_abort_dump(keep=int(sys.argv[2]), max_bytes=int(sys.argv[3]))
gate = threading.Event()

def parked_worker_alpha():
    gate.wait()

def parked_worker_beta():
    gate.wait()

for target in (parked_worker_alpha, parked_worker_beta):
    threading.Thread(target=target, daemon=True).start()
dumpable = ctypes.CDLL(None).prctl(3, 0, 0, 0, 0)  # PR_GET_DUMPABLE
print(name, resource.getrlimit(resource.RLIMIT_CORE)[1], dumpable, flush=True)
gate.wait()
"""


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "state"
    directory.mkdir(mode=0o700)
    return directory


def _abort_child(state: Path, keep: int = hd.DEFAULT_KEEP_DUMPS, max_bytes: int = hd.DEFAULT_MAX_DUMP_BYTES) -> str:
    """Start a child that arms the dump, SIGABRT it, return its dump file's name."""
    child = subprocess.Popen(
        [sys.executable, "-c", ABORT_CHILD, str(ROOT), str(keep), str(max_bytes)],
        env={**os.environ, hd.STATE_DIRECTORY_ENV: str(state)},
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        name, core_limit, dumpable = child.stdout.readline().split()  # type: ignore[union-attr]
        assert (core_limit, dumpable) == ("0", "0"), "core dumps must be off"
        child.send_signal(signal.SIGABRT)
        assert child.wait(20) == -signal.SIGABRT
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(10)
        child.stdout.close()  # type: ignore[union-attr]
    return name


def _dumps(state: Path) -> list[Path]:
    return sorted(path for path in state.iterdir() if path.name.startswith(hd.DUMP_PREFIX))


def test_sigabrt_writes_every_threads_stack_and_kills_the_process(state_dir: Path) -> None:
    name = _abort_child(state_dir)
    dump = state_dir / name
    text = dump.read_text(encoding="utf-8")
    assert text.startswith("Fatal Python error: Aborted")
    assert "in parked_worker_alpha" in text and "in parked_worker_beta" in text
    assert text.count("hread 0x") >= 3
    assert oct(dump.stat().st_mode & 0o777) == "0o600"
    assert oct(state_dir.stat().st_mode & 0o777) == "0o700"


def test_repeated_dumps_stay_within_the_file_and_byte_bounds(state_dir: Path) -> None:
    keep, budget = 3, 6000
    max_bytes = hd.MAX_DUMP_BYTES + budget
    names = [_abort_child(state_dir, keep=keep, max_bytes=max_bytes) for _ in range(7)]
    dumps = _dumps(state_dir)
    assert len(dumps) <= keep
    # Earlier dumps fit the budget left after room for one more dump.
    sizes = {path.name: path.stat().st_size for path in dumps}
    assert sum(sizes.values()) - sizes[names[-1]] <= budget
    assert names[-1] in sizes and sizes[names[-1]] > 0, "the latest dump is kept"
    assert all(size > 0 for size in sizes.values())


def test_a_live_writers_file_is_never_pruned(state_dir: Path) -> None:
    """A file whose lock is held belongs to a live process: kept and still written."""
    live_name = f"{hd.DUMP_PREFIX}20261015T000000Z-pid1-00000000{hd.DUMP_SUFFIX}"
    live = os.open(state_dir / live_name, os.O_WRONLY | os.O_CREAT, 0o600)
    fcntl.flock(live, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for second in range(20):
        (state_dir / f"{hd.DUMP_PREFIX}20261015T0001{second:02d}Z-pid2-00000000{hd.DUMP_SUFFIX}").write_text("x" * 100)
    dir_fd = hd.open_state_dir(str(state_dir))
    try:
        removed = hd.prune_dumps(dir_fd, keep=2, max_bytes=10_000)
    finally:
        os.close(dir_fd)
    try:
        assert live_name not in removed
        assert os.fstat(live).st_nlink == 1
        os.write(live, b"still writing")
    finally:
        os.close(live)
    assert (state_dir / live_name).read_bytes() == b"still writing"
    assert len(removed) == 18
    assert len(_dumps(state_dir)) == 3


def test_empty_files_go_first_and_other_files_and_symlinks_are_left_alone(state_dir: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("keep me")
    (state_dir / f"{hd.DUMP_PREFIX}20261015T000001Z-pid3-0{hd.DUMP_SUFFIX}").write_text("")
    (state_dir / f"{hd.DUMP_PREFIX}20261015T000002Z-pid3-0{hd.DUMP_SUFFIX}").write_text("dump")
    (state_dir / f"{hd.DUMP_PREFIX}20261015T000000Z-pid3-link{hd.DUMP_SUFFIX}").symlink_to(outside)
    (state_dir / "notes.txt").write_text("unrelated")
    (state_dir / hd.READY_MARKER).write_text("0" * 32 + "\n")
    dir_fd = hd.open_state_dir(str(state_dir))
    try:
        assert hd.prune_dumps(dir_fd, keep=0, max_bytes=0) == [
            f"{hd.DUMP_PREFIX}20261015T000002Z-pid3-0{hd.DUMP_SUFFIX}",
            f"{hd.DUMP_PREFIX}20261015T000001Z-pid3-0{hd.DUMP_SUFFIX}",
        ]
    finally:
        os.close(dir_fd)
    assert sorted(path.name for path in state_dir.iterdir()) == [
        f"{hd.DUMP_PREFIX}20261015T000000Z-pid3-link{hd.DUMP_SUFFIX}",
        "notes.txt",
        hd.READY_MARKER,
    ]
    assert outside.read_text() == "keep me"


def test_nothing_happens_outside_the_unit(tmp_path: Path) -> None:
    assert hd.arm_abort_dump({}) is None
    assert not any(tmp_path.iterdir())


@pytest.mark.parametrize("problem", ["missing", "symlink", "group_readable", "not_a_directory"])
def test_the_state_directory_must_be_a_private_directory(tmp_path: Path, problem: str) -> None:
    """Opened once without following a symlink; never created or chmod-ed by path."""
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    target = tmp_path / "state"
    if problem == "symlink":
        target.symlink_to(real)
    elif problem == "group_readable":
        target.mkdir()
        target.chmod(0o750)
    elif problem == "not_a_directory":
        target.write_text("")
    with pytest.raises(hd.StateDirectoryError):
        hd.arm_abort_dump({hd.STATE_DIRECTORY_ENV: str(target)})
    if problem == "missing":
        assert not target.exists()
    if problem == "group_readable":
        assert oct(target.stat().st_mode & 0o777) == "0o750"
    assert not any(real.iterdir())


def test_a_directory_owned_by_someone_else_is_refused(state_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getuid", lambda: state_dir.stat().st_uid + 1)
    with pytest.raises(hd.StateDirectoryError):
        hd.open_state_dir(str(state_dir))


def test_the_ready_marker_round_trips_through_the_state_directory(state_dir: Path, monkeypatch) -> None:
    invocation = "0123456789abcdef0123456789abcdef"
    assert hd.write_ready_marker({"INVOCATION_ID": invocation}) is False  # not armed yet
    dir_fd = hd.open_state_dir(str(state_dir))
    monkeypatch.setattr(hd, "_STATE_DIR_FD", dir_fd)
    try:
        assert hd.write_ready_marker({"INVOCATION_ID": "not-an-invocation"}) is False
        assert hd.write_ready_marker({"INVOCATION_ID": invocation}) is True
        assert hd.read_ready_marker(dir_fd) == invocation
        assert oct((state_dir / hd.READY_MARKER).stat().st_mode & 0o777) == "0o600"
        (state_dir / hd.READY_MARKER).write_text("../../etc/passwd\n")
        assert hd.read_ready_marker(dir_fd) is None
    finally:
        os.close(dir_fd)
    assert [path.name for path in state_dir.iterdir()] == [hd.READY_MARKER]
