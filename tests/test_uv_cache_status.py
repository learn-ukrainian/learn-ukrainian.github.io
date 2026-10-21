"""uv cache size/growth line for lu-driver-status (#10779), driven by injected sizes."""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.hygiene import uv_cache_status as uv

GIB = 1024**3
HOUR = 3600
NOW = 1_800_000_000.0


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "LU_UV_CACHE_WARN_GB",
        "LU_UV_CACHE_GROWTH_WARN_GB",
        "LU_UV_CACHE_SCAN_TIMEOUT_S",
        "LU_UV_CACHE_LOCK_TIMEOUT_S",
        "UV_CACHE_DIR",
        "LU_DRIVER_STATUS_STATE_DIR",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    path = tmp_path / "uv"
    path.mkdir()
    return path


def _write_history(path: Path, *samples: tuple[float, int]) -> None:
    path.write_text("".join(json.dumps({"ts": ts, "bytes": size}) + "\n" for ts, size in samples), encoding="utf-8")


@contextlib.contextmanager
def _dir_fd(directory: Path) -> Iterator[int]:
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        yield fd
    finally:
        os.close(fd)


def _status(cache: Path, history: Path, size: int, now: float = NOW, **kwargs: object) -> dict[str, object]:
    """``build_status`` with the history file's directory bound as the history directory."""
    history.parent.mkdir(parents=True, exist_ok=True)
    with _dir_fd(history.parent) as fd:
        return uv.build_status(cache=cache, history_dir_fd=fd, now=now, size_fn=lambda _root: size, **kwargs)


def _read(history: Path) -> list[dict[str, float]]:
    with _dir_fd(history.parent) as fd:
        return uv.read_history(fd)


def test_first_run_creates_history_and_second_run_dedupes_inside_interval(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "state" / uv.HISTORY_FILENAME

    _status(cache, history, GIB, record=True)
    _status(cache, history, 2 * GIB, now=NOW + 60, record=True)

    rows = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines()]
    assert rows == [{"ts": NOW, "bytes": GIB}]
    _status(cache, history, 2 * GIB, now=NOW + uv.MIN_SAMPLE_INTERVAL_SECONDS, record=True)
    assert len(history.read_text(encoding="utf-8").splitlines()) == 2


def test_samples_older_than_retention_are_dropped(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    _write_history(history, (NOW - uv.RETENTION_SECONDS - 1, GIB), (NOW - 3 * HOUR, 2 * GIB))

    _status(cache, history, 3 * GIB, record=True)

    assert [row["bytes"] for row in _read(history)] == [2 * GIB, 3 * GIB]


def test_corrupt_history_lines_are_skipped(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    history.write_text('not json\n{"ts": "x"}\n{"ts": 1, "bytes": 2}\n[1]\n', encoding="utf-8")

    assert _read(history) == [{"ts": 1.0, "bytes": 2.0}]


def test_measure_bytes_counts_hardlinks_once_and_never_follows_symlinks(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    (root / "a").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "big.bin").write_bytes(b"x" * 1_000_000)
    (root / "a" / "one.bin").write_bytes(b"y" * 100_000)
    os.link(root / "a" / "one.bin", root / "a" / "two.bin")
    (root / "link").symlink_to(outside, target_is_directory=True)

    lone = tmp_path / "lone"
    lone.mkdir()
    (lone / "one.bin").write_bytes(b"y" * 100_000)

    assert uv.measure_bytes(root / "a") == uv.measure_bytes(lone)  # the hardlinked pair counts once
    # only the symlink entry itself is counted, not the 1 MB tree behind it
    assert 0 <= uv.measure_bytes(root) - uv.measure_bytes(root / "a") < 16384


@pytest.mark.parametrize("layout", ["same", "inside", "symlink-alias"])
def test_history_inside_the_cache_is_refused_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], layout: str
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    state = {"same": cache, "inside": cache / "state", "symlink-alias": tmp_path / "alias"}[layout]
    if layout == "symlink-alias":
        state.symlink_to(cache, target_is_directory=True)
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))

    assert uv.main([]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "refusing to run" in captured.err and str(cache) not in captured.err
    assert sorted(path.name for path in cache.iterdir()) == []


def test_sibling_history_with_a_cache_name_prefix_is_allowed(tmp_path: Path) -> None:
    cache = tmp_path / "uv"
    cache.mkdir()
    assert not uv.history_inside_cache(cache, tmp_path / "uv-state")
    assert uv.history_inside_cache(cache, cache / "a" / "b")


def test_symlinked_history_directory_is_refused_before_measuring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Sol r2 blocker 4: a history symlink retargeted into the cache during measurement.
    cache = tmp_path / "cache"
    cache.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "history-link"
    link.symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(uv, "measure_bytes", lambda _: pytest.fail("refusal must precede measurement"))
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(link))

    assert uv.main([]) == 2

    assert "history directory is a symlink" in capsys.readouterr().err
    assert list(cache.iterdir()) == [] and list(outside.iterdir()) == []


def _run_as_file(tmp_path: Path, cache: Path, state: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Launch the tool as a plain file from outside the repository, without PYTHONPATH."""
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env.update(UV_CACHE_DIR=str(cache), LU_DRIVER_STATUS_STATE_DIR=str(state))
    script = Path(uv.__file__).resolve()
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_symlinked_lock_file_is_refused_and_its_target_left_intact(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    (cache / "wheels").mkdir(parents=True)
    payload = cache / "wheels" / "pkg.whl"
    payload.write_bytes(b"w" * 5000)
    state = tmp_path / "state"
    state.mkdir()
    lock = state / (uv.HISTORY_FILENAME + uv.LOCK_SUFFIX)
    lock.symlink_to(payload)

    result = _run_as_file(tmp_path, cache, state)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "refusing to run: the history lock file is a symlink" in result.stderr
    assert "Traceback" not in result.stderr and str(tmp_path) not in result.stderr
    assert str(Path.home()) not in result.stderr
    assert payload.read_bytes() == b"w" * 5000 and lock.is_symlink()
    assert sorted(path.name for path in state.iterdir()) == [lock.name]


def test_measuring_error_is_not_a_zero_sample(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME

    def unreadable(_root: Path) -> int:
        raise PermissionError(13, "Permission denied")

    with _dir_fd(tmp_path) as fd:
        status = uv.build_status(cache=cache, history_dir_fd=fd, now=NOW, size_fn=unreadable)

    assert uv.format_line(status) == "UV CACHE: measurement failed ([Errno 13] Permission denied)"
    assert "bytes" not in status and not history.exists()


def test_concurrent_writers_never_drop_a_newer_sample(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    history = tmp_path / "state" / uv.HISTORY_FILENAME
    history.parent.mkdir()
    _write_history(history, (1000.0, GIB))
    original_read = uv.read_history
    older_has_read = threading.Event()
    newer_done = threading.Event()

    def racing_read(dir_fd: int | None) -> list[dict[str, float]]:
        rows = original_read(dir_fd)
        if threading.current_thread().name == "older":
            older_has_read.set()
            # Unserialized writers let the newer one read, write and finish in this window.
            newer_done.wait(timeout=2)
        return rows

    def writer(ts: float, size: int) -> None:
        with _dir_fd(history.parent) as fd:
            uv.record_sample(fd, ts, size, lock_timeout_s=30)
        if ts == 3000.0:
            newer_done.set()

    monkeypatch.setattr(uv, "read_history", racing_read)
    older = threading.Thread(target=writer, args=(2000.0, 2 * GIB), name="older")
    newer = threading.Thread(target=writer, args=(3000.0, 3 * GIB), name="newer")
    older.start()
    assert older_has_read.wait(timeout=30)
    newer.start()
    older.join(timeout=30)
    newer.join(timeout=30)

    assert [row["ts"] for row in _read(history)] == [1000.0, 2000.0, 3000.0]
    assert (history.parent / (history.name + uv.LOCK_SUFFIX)).is_file()


@contextlib.contextmanager
def _held_history_lock(state: Path) -> Iterator[None]:
    """Hold the history lock the way another writer would (its own open file description)."""
    state.mkdir(parents=True, exist_ok=True)
    fd = os.open(state / (uv.HISTORY_FILENAME + uv.LOCK_SUFFIX), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def test_busy_history_lock_is_bounded_and_reports_the_measurement(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "state" / uv.HISTORY_FILENAME

    with _held_history_lock(history.parent), _dir_fd(history.parent) as fd:
        started = time.monotonic()
        with pytest.raises(uv.HistoryBusy):
            uv.record_sample(fd, NOW, GIB, lock_timeout_s=0.2)
        elapsed = time.monotonic() - started
        status = uv.build_status(cache=cache, history_dir_fd=fd, now=NOW, size_fn=lambda _root: GIB, record=True)

    assert 0.2 <= elapsed < 2
    assert status["bytes"] == GIB
    assert uv.format_line(status) == (
        "UV CACHE: 1.00 GiB, history busy (lock held by another writer for 2s); no sample recorded"
    )
    assert not history.exists()


def test_cli_with_a_held_history_lock_finishes_within_both_deadlines(tmp_path: Path) -> None:
    # Sol r2 blocker 3: a held lock used to stall the status command until it was released.
    cache = tmp_path / "cache"
    cache.mkdir()
    state = tmp_path / "state"
    env = {
        **os.environ,
        "UV_CACHE_DIR": str(cache),
        "LU_DRIVER_STATUS_STATE_DIR": str(state),
        "LU_UV_CACHE_SCAN_TIMEOUT_S": "5",
        "LU_UV_CACHE_LOCK_TIMEOUT_S": "0.3",
    }
    repo = Path(uv.__file__).resolve().parents[2]

    with _held_history_lock(state):
        started = time.monotonic()
        result = subprocess.run(
            [sys.executable, "-m", "scripts.hygiene.uv_cache_status", "--record-history"],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        elapsed = time.monotonic() - started

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("UV CACHE: 0.00 GiB, history busy (lock held by another writer for 0.3s)")
    assert elapsed < 0.3 + 5 + 20  # both deadlines plus interpreter start-up
    assert not (state / uv.HISTORY_FILENAME).exists()


def test_cli_prints_line_records_history_and_deletes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cache = tmp_path / "cache"
    (cache / "wheels").mkdir(parents=True)
    keep = cache / "wheels" / "pkg.whl"
    keep.write_bytes(b"w" * 5000)
    state = tmp_path / "state"
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))

    assert uv.main(["--record-history"]) == 0

    out = capsys.readouterr().out
    assert out.startswith("UV CACHE: 0.00 GiB, growth n/a (history building)")
    assert str(cache) not in out
    assert len(_read(state / uv.HISTORY_FILENAME)) == 1
    assert keep.read_bytes() == b"w" * 5000


def test_cli_json_omits_the_cache_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(tmp_path / "state"))

    assert uv.main(["--json", "--no-record"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["present"] is True and "cache" not in payload


@pytest.mark.parametrize("record", [False, True])
@pytest.mark.parametrize("layout", ["inside-missing-cache", "parent-alias", "cache-alias", "lexical-inside"])
def test_directory_misconfiguration_refuses_before_any_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], record: bool, layout: str
) -> None:
    cache = tmp_path / "cache"
    state = cache / "nested" / "state"
    if layout != "inside-missing-cache":
        cache.mkdir()
    if layout == "parent-alias":
        alias = tmp_path / "alias"
        alias.symlink_to(cache, target_is_directory=True)
        state = alias / "nested" / "state"
    elif layout == "cache-alias":
        alias = tmp_path / "cache-link"
        alias.symlink_to(cache, target_is_directory=True)
        cache, state = alias, cache / "nested" / "state"
    elif layout == "lexical-inside":
        outside = tmp_path / "outside"
        outside.mkdir()
        (cache / "escape").symlink_to(outside, target_is_directory=True)
        state = cache / "escape" / "state"
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    assert uv.main(["--state-dir", str(state)] + (["--record-history"] if record else [])) == 2
    assert "refusing to run" in capsys.readouterr().err
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")) == before


@pytest.mark.parametrize("name", [uv.HISTORY_FILENAME, uv.HISTORY_FILENAME + uv.LOCK_SUFFIX])
@pytest.mark.parametrize("kind", ["symlink", "hardlink", "directory", "fifo"])
@pytest.mark.parametrize("record", [False, True])
def test_configured_file_aliases_refuse_before_writes(
    cache: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    name: str,
    kind: str,
    record: bool,
) -> None:
    victim = cache / "wheel"
    victim.write_bytes(b"cache stays intact")
    state = tmp_path / "state"
    state.mkdir()
    target = state / name
    if kind == "symlink":
        target.symlink_to(victim)
    elif kind == "hardlink":
        os.link(victim, target)
    elif kind == "directory":
        target.mkdir()
    else:
        os.mkfifo(target)
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    assert uv.main(["--state-dir", str(state)] + (["--record-history"] if record else [])) == 2
    captured = capsys.readouterr()
    assert "refusing to run" in captured.err and str(tmp_path) not in captured.err
    assert victim.read_bytes() == b"cache stays intact"
    assert [p.name for p in state.iterdir()] == [name]


def test_recording_requires_explicit_state_directory(
    cache: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    assert uv.main(["--record-history"]) == 2
    assert "requires --state-dir or LU_DRIVER_STATUS_STATE_DIR" in capsys.readouterr().err
    assert uv.state_dir() is None
    assert list(cache.iterdir()) == []
    assert uv.main([]) == 0
    assert capsys.readouterr().out == "UV CACHE: 0.00 GiB, growth n/a (history unavailable)\n"


@pytest.mark.parametrize("mode", [[], ["--no-record"], ["--json"]])
def test_status_readers_never_open_for_writing_or_create_directories(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: list[str]
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    _write_history(state / uv.HISTORY_FILENAME, (time.time() - 23.75 * HOUR, GIB))
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))
    monkeypatch.setattr(uv, "measure_bytes", lambda _: 2 * GIB)
    original_open = os.open

    def readonly_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        assert flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC) == 0
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", readonly_open)
    for _ in range(3):
        assert uv.main(mode) == 0
    output = capsys.readouterr().out
    assert "2.00 GiB, +1.00 GiB over 24h" in output or '"growth_bytes": 1073741824' in output
    assert [p.name for p in state.iterdir()] == [uv.HISTORY_FILENAME]
    assert len(_read(state / uv.HISTORY_FILENAME)) == 1
    # Missing state is also read-only, even its parent must not be created.
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(tmp_path / "missing" / "state"))
    assert uv.main(mode) == 0
    assert not (tmp_path / "missing").exists()


@pytest.mark.parametrize("contents", [None, "", "broken\n", '{"ts": NaN, "bytes": 4}\n', '{"ts": 5, "bytes": -1}\n'])
def test_unusable_history_is_unavailable_not_building(cache: Path, tmp_path: Path, contents: str | None) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    if contents is not None:
        history.write_text(contents)
    status = _status(cache, history, 11 * GIB)
    assert uv.format_line(status) == "UV CACHE: 11.00 GiB, growth n/a (history unavailable) [WARN: size above 10 GiB]"


def test_atomic_update_leaves_old_history_visible_until_replace(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    history = state / uv.HISTORY_FILENAME
    _write_history(history, (NOW - 24 * HOUR, GIB))
    old = history.read_bytes()
    real_replace, real_write = os.replace, os.write
    replacements = []

    def replace(src: str, dst: str, **kwargs: object) -> None:
        assert history.read_bytes() == old
        payload = (state / src).read_bytes()
        assert [json.loads(line)["bytes"] for line in payload.splitlines()] == [GIB, 2 * GIB]
        replacements.append((src, dst))
        real_replace(src, dst, **kwargs)

    def short_write(fd: int, data: object) -> int:
        assert history.read_bytes() == old
        return real_write(fd, bytes(data)[:1])

    monkeypatch.setattr(os, "replace", replace)
    monkeypatch.setattr(os, "write", short_write)
    with _dir_fd(state) as fd:
        uv.record_sample(fd, NOW, 2 * GIB)
    assert len(replacements) == 1
    assert _read(history) == [{"ts": NOW - 24 * HOUR, "bytes": float(GIB)}, {"ts": NOW, "bytes": float(2 * GIB)}]
    assert sorted(p.name for p in state.iterdir()) == [uv.HISTORY_FILENAME, uv.HISTORY_FILENAME + uv.LOCK_SUFFIX]


def test_failed_atomic_update_keeps_prior_history_and_cleans_temporary_file(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    _write_history(history, (NOW - 24 * HOUR, GIB))
    before = history.read_bytes()

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("injected rename failure")

    monkeypatch.setattr(os, "replace", fail)
    status = _status(cache, history, 2 * GIB, record=True)
    assert "history unavailable" in uv.format_line(status)
    assert history.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("race", ["symlink-retarget", "directory-move", "hardlink", "hardlink-unlink"])
def test_recorded_race_classes_cannot_turn_status_readers_into_writers(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], race: str
) -> None:
    # These mutations are outside the writer contract. A reader still writes nothing.
    state = tmp_path / "state"
    state.mkdir()
    history = state / uv.HISTORY_FILENAME
    _write_history(history, (time.time() - 23.75 * HOUR, GIB))
    parent = tmp_path / "parent"
    parent.symlink_to(state, target_is_directory=True)
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(parent / "."))
    # Use a real child so only the ancestor is a symlink.
    child = state / "child"
    child.mkdir()
    history.rename(child / uv.HISTORY_FILENAME)
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(parent / "child"))
    snapshot: list[tuple[str, bytes]] = []

    def measure(_: Path) -> int:
        source = child / uv.HISTORY_FILENAME
        if race == "symlink-retarget":
            parent.unlink()
            parent.symlink_to(cache, target_is_directory=True)
        elif race == "directory-move":
            state.rename(cache / "moved-state")
        else:
            os.link(source, cache / "alias")
            if race == "hardlink-unlink":
                source.unlink()
        snapshot.extend((str(p.relative_to(cache)), p.read_bytes()) for p in cache.rglob("*") if p.is_file())
        return 2 * GIB

    monkeypatch.setattr(uv, "measure_bytes", measure)
    assert uv.main([]) == 0
    assert "UV CACHE: 2.00 GiB" in capsys.readouterr().out
    assert [(str(p.relative_to(cache)), p.read_bytes()) for p in cache.rglob("*") if p.is_file()] == snapshot
    assert not list(tmp_path.rglob("*.lock")) and not list(tmp_path.rglob("*.tmp"))


def test_help_documents_owner_modes_and_side_effects(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as result:
        uv.main(["--help"])
    assert result.value.code == 0
    out = capsys.readouterr().out
    for text in (
        "--record-history",
        "--state-dir",
        "LU_DRIVER_STATUS_STATE_DIR",
        "Outputs:",
        "Exit codes:",
        "Related:",
    ):
        assert text in out


def test_state_option_overrides_environment_and_tempdir_is_ignored(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(cache / "forbidden"))
    monkeypatch.setenv("TMPDIR", str(cache))
    monkeypatch.setattr(uv, "measure_bytes", lambda _: GIB)
    state = tmp_path / "state"
    assert uv.main(["--record-history", "--state-dir", str(state)]) == 0
    assert "history building" in capsys.readouterr().out
    assert list(cache.iterdir()) == []
    assert (state / uv.HISTORY_FILENAME).stat().st_mode & 0o777 == 0o600
    assert state.stat().st_mode & 0o777 == 0o700


def test_history_unreadable_is_explicit_without_writing(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    _write_history(history, (NOW - 24 * HOUR, GIB))
    original_open = os.open

    def open_file(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if path == uv.HISTORY_FILENAME:
            raise PermissionError("injected read denial")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", open_file)
    assert uv.format_line(_status(cache, history, 2 * GIB)) == "UV CACHE: 2.00 GiB, growth n/a (history unavailable)"
    assert [p.name for p in tmp_path.iterdir() if p.is_file()] == [uv.HISTORY_FILENAME]
