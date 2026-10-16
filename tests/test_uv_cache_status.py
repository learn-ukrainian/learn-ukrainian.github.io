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


def test_growth_uses_oldest_sample_inside_24h_and_reports_real_span(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    _write_history(
        history,
        (NOW - 30 * HOUR, 1 * GIB),  # outside the window: ignored
        (NOW - 20 * HOUR, 5 * GIB),
        (NOW - 2 * HOUR, 6 * GIB),
    )

    status = _status(cache, history, 6 * GIB + GIB // 2)

    assert status["growth_bytes"] == GIB + GIB // 2
    assert status["growth_span_seconds"] == 20 * HOUR
    assert uv.format_line(status) == "UV CACHE: 6.50 GiB, +1.50 GiB over 20.0h"


def test_full_24h_window_is_labelled_24h(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    _write_history(history, (NOW - 24 * HOUR, 4 * GIB))

    assert uv.format_line(_status(cache, history, 5 * GIB)) == "UV CACHE: 5.00 GiB, +1.00 GiB over 24h"


def test_shrinking_cache_reports_negative_growth_without_warning(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    _write_history(history, (NOW - 24 * HOUR, 9 * GIB))

    status = _status(cache, history, 4 * GIB)

    assert status["warnings"] == []
    assert uv.format_line(status) == "UV CACHE: 4.00 GiB, -5.00 GiB over 24h"


def test_no_usable_baseline_reports_history_building(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    _write_history(history, (NOW - 600, 3 * GIB))  # too young to say anything about growth

    status = _status(cache, history, 3 * GIB)

    assert status["growth_bytes"] is None
    assert uv.format_line(status) == "UV CACHE: 3.00 GiB, growth n/a (history building)"


def test_first_run_creates_history_and_second_run_dedupes_inside_interval(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "state" / uv.HISTORY_FILENAME

    _status(cache, history, GIB)
    _status(cache, history, 2 * GIB, now=NOW + 60)

    rows = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines()]
    assert rows == [{"ts": NOW, "bytes": GIB}]
    _status(cache, history, 2 * GIB, now=NOW + uv.MIN_SAMPLE_INTERVAL_SECONDS)
    assert len(history.read_text(encoding="utf-8").splitlines()) == 2


def test_samples_older_than_retention_are_dropped(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    _write_history(history, (NOW - uv.RETENTION_SECONDS - 1, GIB), (NOW - 3 * HOUR, 2 * GIB))

    _status(cache, history, 3 * GIB)

    assert [row["bytes"] for row in _read(history)] == [2 * GIB, 3 * GIB]


def test_corrupt_history_lines_are_skipped(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    history.write_text('not json\n{"ts": "x"}\n{"ts": 1, "bytes": 2}\n[1]\n', encoding="utf-8")

    assert _read(history) == [{"ts": 1.0, "bytes": 2.0}]


def test_absolute_size_warning_uses_default_and_env_threshold(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    history = tmp_path / uv.HISTORY_FILENAME

    status = _status(cache, history, 11 * GIB, record=False)
    assert status["warnings"] == ["size above 10 GiB"]
    assert uv.format_line(status).endswith("[WARN: size above 10 GiB]")

    monkeypatch.setenv("LU_UV_CACHE_WARN_GB", "20")
    assert _status(cache, history, 11 * GIB, record=False)["warnings"] == []


def test_growth_warning_uses_default_and_env_threshold(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    history = tmp_path / uv.HISTORY_FILENAME
    _write_history(history, (NOW - 24 * HOUR, 5 * GIB))

    status = _status(cache, history, 8 * GIB, record=False)
    assert status["warnings"] == ["growth above 2 GiB per 24 h"]

    monkeypatch.setenv("LU_UV_CACHE_GROWTH_WARN_GB", "3")
    assert _status(cache, history, 8 * GIB, record=False)["warnings"] == []
    monkeypatch.setenv("LU_UV_CACHE_GROWTH_WARN_GB", "garbage")
    assert _status(cache, history, 8 * GIB, record=False)["warnings"] == ["growth above 2 GiB per 24 h"]


def test_no_record_leaves_no_history_file(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))

    assert uv.main(["--no-record"]) == 0

    assert capsys.readouterr().out.startswith("UV CACHE: 0.00 GiB")
    assert not state.exists()


def test_missing_cache_is_reported_without_touching_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("UV_CACHE_DIR", str(tmp_path / "absent"))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))

    assert uv.main([]) == 0

    assert capsys.readouterr().out == "UV CACHE: not present\n"
    assert not state.exists()
    assert uv.format_line(uv.build_status(cache=tmp_path / "absent", history_dir_fd=None, now=NOW)) == (
        "UV CACHE: not present"
    )


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


def _slow_du(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a ``du`` on PATH that publishes its pid and then hangs like a stalled scan."""
    bindir = tmp_path / "slow-bin"
    bindir.mkdir()
    pid_file = tmp_path / "du.pid"
    du = bindir / "du"
    du.write_text(f'#!/bin/sh\necho $$ > "{pid_file}"\nexec sleep 300\n', encoding="utf-8")
    du.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    return pid_file


def _pid_running(pid: int) -> bool:
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return False


def test_slow_scan_is_bounded_reports_unavailable_and_records_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    state = tmp_path / "state"
    pid_file = _slow_du(tmp_path, monkeypatch)
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))
    monkeypatch.setenv("LU_UV_CACHE_SCAN_TIMEOUT_S", "0.5")

    started = time.monotonic()
    assert uv.main([]) == 0
    elapsed = time.monotonic() - started

    assert capsys.readouterr().out == "UV CACHE: size unavailable (scan exceeded 0.5s)\n"
    assert elapsed < 0.5 + uv.KILL_GRACE_SECONDS + 3
    assert not (state / uv.HISTORY_FILENAME).exists()
    assert not _pid_running(int(pid_file.read_text()))


def test_scan_timeout_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    assert uv.scan_timeout_seconds() == 8
    monkeypatch.setenv("LU_UV_CACHE_SCAN_TIMEOUT_S", "2.5")
    assert uv.scan_timeout_seconds() == 2.5
    for bad in ("0", "-1", "soon", "inf"):
        monkeypatch.setenv("LU_UV_CACHE_SCAN_TIMEOUT_S", bad)
        assert uv.scan_timeout_seconds() == 8


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


def _retargeting_du(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, link: Path, target: Path) -> None:
    """Put a ``du`` on PATH that retargets ``link`` to ``target`` mid-measurement, then reports 4 KiB."""
    bindir = tmp_path / "retarget-bin"
    bindir.mkdir()
    du = bindir / "du"
    du.write_text(f'#!/bin/sh\nln -sfn "{target}" "{link}"\nprintf "4\\t%s\\n" "$3"\n', encoding="utf-8")
    du.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")


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
    _retargeting_du(tmp_path, monkeypatch, link, cache)
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(link))

    assert uv.main([]) == 2

    assert "history directory is a symlink" in capsys.readouterr().err
    assert list(cache.iterdir()) == [] and list(outside.iterdir()) == []


def test_history_writes_stay_bound_when_a_parent_symlink_is_retargeted_into_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "parent-link"
    link.symlink_to(outside, target_is_directory=True)
    _retargeting_du(tmp_path, monkeypatch, link, cache)
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(link / "state"))

    assert uv.main([]) == 0

    assert capsys.readouterr().out.startswith("UV CACHE: 0.00 GiB")
    assert link.resolve() == cache.resolve()  # the retarget did happen mid-measurement
    assert list(cache.iterdir()) == []
    assert len(_read(outside / "state" / uv.HISTORY_FILENAME)) == 1


def test_cache_swapped_onto_the_history_path_after_resolving_is_refused_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(outside / "state"))
    real_check = uv.history_inside_cache

    def check_then_swap(cache_path: Path, history_dir: Path) -> bool:
        inside = real_check(cache_path, history_dir)
        # Between the path check and the open, the cache takes the history parent's place.
        outside.rename(tmp_path / "outside-moved")
        cache.rename(outside)
        return inside

    monkeypatch.setattr(uv, "history_inside_cache", check_then_swap)

    assert uv.main([]) == 2

    assert "inside it" in capsys.readouterr().err
    assert list(outside.iterdir()) == []  # the cache, now at the old path, gained nothing


def test_bound_dir_inside_cache_checks_both_inode_chain_and_kernel_path(tmp_path: Path) -> None:
    cache_real = tmp_path / "cache"
    cache_id = (1, 2)
    elsewhere = tmp_path / "state"

    assert uv.bound_dir_inside_cache([(1, 1), (1, 2), (1, 3)], elsewhere, cache_id, cache_real)
    assert uv.bound_dir_inside_cache([(1, 1)], cache_real, cache_id, cache_real)
    assert uv.bound_dir_inside_cache([(1, 1)], cache_real / "a" / "b", cache_id, cache_real)
    assert uv.bound_dir_inside_cache([(1, 1)], cache_real / "a", None, cache_real)
    assert not uv.bound_dir_inside_cache([(1, 1), (1, 3)], elsewhere, cache_id, cache_real)
    assert not uv.bound_dir_inside_cache([(1, 1)], tmp_path / "cache-state", None, cache_real)


def _tree(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


def test_history_directory_moved_into_the_cache_during_measurement_is_refused_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Sol final-round reproducer: the opened history directory is moved into the
    # cache while du runs, and its configured pathname is recreated.
    cache = tmp_path / "cache"
    cache.mkdir()
    state = tmp_path / "state"
    bindir = tmp_path / "moving-bin"
    bindir.mkdir()
    du = bindir / "du"
    du.write_text(
        f'#!/bin/sh\nmv "{state}" "{cache}/moved-state" && mkdir "{state}"\nprintf "4\\t%s\\n" "$3"\n',
        encoding="utf-8",
    )
    du.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))

    assert uv.main([]) == 2

    captured = capsys.readouterr()
    assert captured.out == "" and "inside it" in captured.err
    assert _tree(cache) == ["moved-state"]  # the move happened; nothing was written into it
    assert list(state.iterdir()) == []


def _move_into_cache_on_check(
    bound: uv.BoundHistoryDir, cache: Path, cache_real: Path, at_call: int
) -> uv.LocationCheck:
    calls = 0

    def check() -> None:
        nonlocal calls
        calls += 1
        if calls == at_call:
            bound.path.rename(cache / "moved-state")
            bound.path.mkdir()
        uv.verify_history_location(bound, cache, cache_real)

    return check


@pytest.mark.parametrize(
    "at_call", [1, 2, 3, 4], ids=["before-lock", "before-temp-file", "before-write", "before-rename"]
)
def test_every_history_write_rechecks_the_location(cache: Path, tmp_path: Path, at_call: int) -> None:
    bound = uv.open_history_dir(cache, tmp_path / "state", create=True)
    assert bound is not None
    try:
        check = _move_into_cache_on_check(bound, cache, cache.resolve(), at_call)
        with pytest.raises(uv.HistoryLocationError, match="inside it"):
            uv.record_sample(bound.fd, NOW, GIB, lock_timeout_s=1, location_check=check)
    finally:
        os.close(bound.fd)

    # The lock file this call created and the temporary file are gone again; no history was written.
    assert _tree(cache) == ["moved-state"]
    assert list((tmp_path / "state").iterdir()) == []


def test_refusal_keeps_a_lock_file_this_call_did_not_create(cache: Path, tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    (state / (uv.HISTORY_FILENAME + uv.LOCK_SUFFIX)).touch()
    bound = uv.open_history_dir(cache, state, create=True)
    assert bound is not None
    try:
        check = _move_into_cache_on_check(bound, cache, cache.resolve(), 2)
        with pytest.raises(uv.HistoryLocationError):
            uv.record_sample(bound.fd, NOW, GIB, lock_timeout_s=1, location_check=check)
    finally:
        os.close(bound.fd)

    assert _tree(cache) == ["moved-state", "moved-state/" + uv.HISTORY_FILENAME + uv.LOCK_SUFFIX]


@pytest.mark.parametrize("change", ["moved-elsewhere", "replaced-in-place", "deleted"])
def test_history_directory_moved_outside_the_cache_is_refused_too(cache: Path, tmp_path: Path, change: str) -> None:
    state = tmp_path / "state"
    bound = uv.open_history_dir(cache, state, create=True)
    assert bound is not None
    try:
        uv.verify_history_location(bound, cache, cache.resolve())  # untouched: accepted
        if change == "moved-elsewhere":
            state.rename(tmp_path / "elsewhere")
        elif change == "replaced-in-place":
            state.rename(tmp_path / "elsewhere")
            state.mkdir()
        else:
            state.rmdir()
        with pytest.raises(uv.HistoryLocationError, match="moved after it was opened"):
            uv.verify_history_location(bound, cache, cache.resolve())
    finally:
        os.close(bound.fd)


def test_cache_path_repointed_over_the_history_after_opening_is_refused(tmp_path: Path) -> None:
    # The cache's real path is taken again at each check, not only at open time.
    cache = tmp_path / "cache"
    cache.mkdir()
    bound = uv.open_history_dir(cache, tmp_path / "state", create=True)
    assert bound is not None
    try:
        cache_real_at_open = cache.resolve()
        cache.rename(tmp_path / "cache-old")
        cache.symlink_to(tmp_path, target_is_directory=True)
        with pytest.raises(uv.HistoryLocationError, match="inside it"):
            uv.verify_history_location(bound, cache, cache_real_at_open)
    finally:
        os.close(bound.fd)


def test_history_directory_moved_while_being_opened_is_refused(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state"
    real_check = uv.bound_dir_inside_cache

    def check_then_move(*args: object) -> bool:
        inside = real_check(*args)  # type: ignore[arg-type]
        state.rename(tmp_path / "elsewhere")
        return inside

    monkeypatch.setattr(uv, "bound_dir_inside_cache", check_then_move)

    with pytest.raises(uv.HistoryLocationError, match="moved after it was opened"):
        uv.open_history_dir(cache, state, create=True)


def test_refusal_never_removes_a_lock_file_that_replaced_the_one_it_created(cache: Path, tmp_path: Path) -> None:
    state = tmp_path / "state"
    bound = uv.open_history_dir(cache, state, create=True)
    assert bound is not None
    lock = uv.HISTORY_FILENAME + uv.LOCK_SUFFIX
    try:
        inner = _move_into_cache_on_check(bound, cache, cache.resolve(), 2)
        calls = 0

        def replace_lock_then_check() -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                (state / lock).unlink()
                (state / lock).write_text("another writer's lock", encoding="utf-8")
            inner()

        with pytest.raises(uv.HistoryLocationError):
            uv.record_sample(bound.fd, NOW, GIB, lock_timeout_s=1, location_check=replace_lock_then_check)
    finally:
        os.close(bound.fd)

    assert (cache / "moved-state" / lock).read_text(encoding="utf-8") == "another writer's lock"


def _move_state_into_cache(state: Path, cache: Path) -> None:
    state.rename(cache / "moved-state")
    state.mkdir()


def test_lock_creation_retry_after_the_directory_moved_into_the_cache_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Sol round-4 reproducer: exclusive creation meets an existing lock; the held
    # directory then moves into the cache, its pathname is recreated, and the old
    # lock is removed, so the plain open fails and the creation is retried.
    cache = tmp_path / "cache"
    cache.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    lock = uv.HISTORY_FILENAME + uv.LOCK_SUFFIX
    _write_history(state / uv.HISTORY_FILENAME, (time.time(), 4096))  # recent: the run would only dedupe
    (state / lock).touch()
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))
    real_open = os.open
    moved = False

    def open_then_move(path: object, flags: int, *args: object, **kwargs: object) -> int:
        nonlocal moved
        try:
            return real_open(path, flags, *args, **kwargs)  # type: ignore[arg-type]
        except FileExistsError:
            if path == lock and not moved:
                moved = True
                _move_state_into_cache(state, cache)
                (cache / "moved-state" / lock).unlink()
            raise

    monkeypatch.setattr(os, "open", open_then_move)

    assert uv.main([]) == 2

    captured = capsys.readouterr()
    assert moved and captured.out == "" and "inside it" in captured.err
    assert _tree(cache) == ["moved-state", "moved-state/" + uv.HISTORY_FILENAME]  # no lock created in the cache
    assert list(state.iterdir()) == []


def test_history_directory_moved_during_serialization_gets_no_bytes_inside_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Sol round-4 reproducer: the directory moves while the samples are serialized.
    cache = tmp_path / "cache"
    cache.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))
    real_dumps, real_open, real_unlink = json.dumps, os.open, os.unlink
    created: list[Path] = []
    discarded: list[tuple[Path, int]] = []

    def _where(path: object, dir_fd: int | None) -> Path:
        base = Path(os.readlink(f"/proc/self/fd/{dir_fd}")) if dir_fd is not None else Path.cwd()
        return base / os.fsdecode(path)  # type: ignore[arg-type]

    def dumps_then_move(*args: object, **kwargs: object) -> str:
        # Only the history sample; harness hooks serialize other objects meanwhile.
        is_sample = bool(args) and isinstance(args[0], dict) and "ts" in args[0]
        if is_sample and not (cache / "moved-state").exists():
            _move_state_into_cache(state, cache)
        return real_dumps(*args, **kwargs)  # type: ignore[arg-type]

    def recording_open(path: object, flags: int, *args: object, dir_fd: int | None = None, **kwargs: object) -> int:
        if flags & os.O_CREAT:
            created.append(_where(path, dir_fd))
        return real_open(path, flags, *args, dir_fd=dir_fd, **kwargs)  # type: ignore[arg-type]

    def recording_unlink(path: object, *, dir_fd: int | None = None) -> None:
        with contextlib.suppress(OSError):
            discarded.append((_where(path, dir_fd), os.stat(path, dir_fd=dir_fd).st_size))  # type: ignore[arg-type]
        real_unlink(path, dir_fd=dir_fd)  # type: ignore[arg-type]

    monkeypatch.setattr(json, "dumps", dumps_then_move)
    monkeypatch.setattr(os, "open", recording_open)
    monkeypatch.setattr(os, "unlink", recording_unlink)

    assert uv.main([]) == 2

    assert "inside it" in capsys.readouterr().err
    cache_real = cache.resolve()
    assert [path for path in created if cache_real in path.parents] == []
    assert [entry for entry in discarded if cache_real in entry[0].parents and entry[1] > 0] == []
    assert _tree(cache) == ["moved-state"]


def test_symlinked_cache_root_is_measured_where_it_points(tmp_path: Path) -> None:
    real = tmp_path / "real-cache"
    real.mkdir()
    (real / "wheel.bin").write_bytes(b"w" * 1_000_000)
    link = tmp_path / "cache-link"
    link.symlink_to(real, target_is_directory=True)

    assert uv.measure_bytes(link) == uv.measure_bytes(real) >= 1_000_000


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


def test_tool_runs_as_a_plain_file_outside_the_repository(cache: Path, tmp_path: Path) -> None:
    state = tmp_path / "state"

    result = _run_as_file(tmp_path, cache, state)

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("UV CACHE: 0.00 GiB, growth n/a (history building)")
    assert len(_read(state / uv.HISTORY_FILENAME)) == 1


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


def test_lock_name_that_is_not_a_regular_file_is_refused(cache: Path, tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    os.mkfifo(state / (uv.HISTORY_FILENAME + uv.LOCK_SUFFIX))

    with _dir_fd(state) as fd, pytest.raises(uv.HistoryLocationError, match="not a regular file"):
        uv.record_sample(fd, NOW, GIB, lock_timeout_s=0.2)

    assert sorted(path.name for path in state.iterdir()) == [uv.HISTORY_FILENAME + uv.LOCK_SUFFIX]


def test_directory_shaped_lock_is_refused_cleanly(tmp_path: Path) -> None:
    # Sol r3 follow-up: a directory at the lock name used to end in exit 1 with a traceback.
    cache = tmp_path / "cache"
    cache.mkdir()
    state = tmp_path / "state"
    lock = state / (uv.HISTORY_FILENAME + uv.LOCK_SUFFIX)
    lock.mkdir(parents=True)

    result = _run_as_file(tmp_path, cache, state)

    assert result.returncode == 2, result.stderr
    assert result.stdout == ""
    assert "refusing to run: the history lock file is not a regular file" in result.stderr
    assert "Traceback" not in result.stderr and str(tmp_path) not in result.stderr
    assert str(Path.home()) not in result.stderr
    assert lock.is_dir() and list(lock.iterdir()) == []
    assert sorted(path.name for path in state.iterdir()) == [lock.name]


def test_partial_write_rechecks_the_location_before_the_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Sol r3 blocker 1: the kernel accepted 1 byte of the first write (RLIMIT_FSIZE), the
    # directory then moved into the cache, and the unchecked next write put the rest there.
    cache = tmp_path / "cache"
    cache.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))
    real_write = os.write
    cache_real = cache.resolve()
    writes: list[tuple[Path, int]] = []

    def short_first_write(fd: int, data: object) -> int:
        target = Path(os.readlink(f"/proc/self/fd/{fd}"))
        if target.name.endswith(".tmp"):
            if not writes:
                written = real_write(fd, bytes(data)[:1])  # type: ignore[call-overload]
                writes.append((target, written))
                _move_state_into_cache(state, cache)
                return written
            writes.append((target, len(data)))  # type: ignore[arg-type]
        return real_write(fd, data)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "write", short_first_write)

    assert uv.main([]) == 2

    assert "inside it" in capsys.readouterr().err
    assert len(writes) == 1 and writes[0][1] == 1  # the short write happened before the move
    assert [entry for entry in writes if cache_real in entry[0].parents] == []
    assert _tree(cache) == ["moved-state"]
    assert list(state.iterdir()) == []


# Runs the tool with a real 1-byte short write (RLIMIT_FSIZE) of the temporary history file,
# after which the limit is restored and the file is hard-linked into the cache.
_SHORT_WRITE_THEN_HARDLINK = """
import json, os, resource, signal, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.hygiene import uv_cache_status as uv
alias, report = Path(sys.argv[2]), Path(sys.argv[3])
signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
real_write = os.write
writes = []
def write(fd, data):
    target = os.readlink(f"/proc/self/fd/{fd}")
    if not target.endswith(".tmp"):
        return real_write(fd, data)
    if writes:
        written = real_write(fd, data)
    else:
        limits = resource.getrlimit(resource.RLIMIT_FSIZE)
        resource.setrlimit(resource.RLIMIT_FSIZE, (1, limits[1]))
        try:
            written = real_write(fd, data)
        finally:
            resource.setrlimit(resource.RLIMIT_FSIZE, limits)
        os.link(target, alias)
    writes.append(written)
    return written
os.write = write
code = uv.main([])
report.write_text(json.dumps({"code": code, "writes": writes}), encoding="utf-8")
"""


def test_temporary_file_hard_linked_into_the_cache_after_a_short_write_gets_no_more_bytes(tmp_path: Path) -> None:
    # Sol r4 blocker (a): the directory never moves, so only the link count shows the alias.
    cache = tmp_path / "cache"
    cache.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    alias = cache / "alias"
    report = tmp_path / "report.json"
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env.update(UV_CACHE_DIR=str(cache), LU_DRIVER_STATUS_STATE_DIR=str(state))

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            _SHORT_WRITE_THEN_HARDLINK,
            str(Path(uv.__file__).resolve().parents[2]),
            str(alias),
            str(report),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    outcome = json.loads(report.read_text(encoding="utf-8"))
    assert outcome == {"code": 2, "writes": [1]}, result.stderr
    assert "refusing to run: the temporary history file has more than one link" in result.stderr
    assert "Traceback" not in result.stderr and str(tmp_path) not in result.stderr
    assert alias.stat().st_size == 1 and alias.stat().st_nlink == 1  # the temporary file was removed
    assert sorted(path.name for path in state.iterdir()) == []


def test_lock_file_hard_linked_to_a_cache_file_is_refused_without_locking_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Sol r4 blocker (b): a pre-existing hard link made the command lock a cache inode.
    cache = tmp_path / "cache"
    cache.mkdir()
    victim = cache / "victim"
    victim.write_bytes(b"v" * 100)
    state = tmp_path / "state"
    state.mkdir()
    lock = state / (uv.HISTORY_FILENAME + uv.LOCK_SUFFIX)
    os.link(victim, lock)
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))
    locked: list[int] = []
    real_flock = fcntl.flock

    def recording_flock(fd: int, operation: int) -> None:
        locked.append(fd)
        real_flock(fd, operation)

    monkeypatch.setattr(fcntl, "flock", recording_flock)

    assert uv.main([]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "refusing to run: the history lock file has more than one link" in captured.err
    assert str(tmp_path) not in captured.err
    assert locked == []
    assert victim.read_bytes() == b"v" * 100 and victim.stat().st_nlink == 2
    assert sorted(path.name for path in state.iterdir()) == [lock.name]


def test_lock_file_hard_linked_while_waiting_for_the_lock_is_refused(cache: Path, tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    lock = state / (uv.HISTORY_FILENAME + uv.LOCK_SUFFIX)
    alias = cache / "alias"
    real_lock_history = uv._lock_history

    def link_then_lock(lock_fd: int, deadline: float, timeout_s: float) -> None:
        os.link(lock, alias)
        real_lock_history(lock_fd, deadline, timeout_s)

    with (
        _dir_fd(state) as fd,
        pytest.MonkeyPatch.context() as patch,
        pytest.raises(uv.HistoryLocationError, match="history lock file has more than one link"),
    ):
        patch.setattr(uv, "_lock_history", link_then_lock)
        uv.record_sample(fd, NOW, GIB, lock_timeout_s=0.2)

    # This call created the lock, so it removes its own name; the alias is left alone.
    assert sorted(path.name for path in state.iterdir()) == []
    assert alias.stat().st_nlink == 1


class _LockChurn:
    """Real filesystem churn on the lock name: every exclusive create meets an existing
    lock and the lock is gone again before the plain open. Stops after ``limit`` attempts
    (or ``seconds``) so code without a deadline ends instead of spinning forever."""

    def __init__(self, limit: int = 1_000_000, seconds: float = 5.0) -> None:
        self.name = uv.HISTORY_FILENAME + uv.LOCK_SUFFIX
        self.limit, self.stop_at = limit, time.monotonic() + seconds
        self.attempts = 0
        self.real_open = os.open

    def churning(self) -> bool:
        return self.attempts < self.limit and time.monotonic() < self.stop_at

    def __call__(self, path: object, flags: int, *args: object, dir_fd: int | None = None, **kwargs: object) -> int:
        if path == self.name and self.churning():
            if flags & os.O_EXCL:
                self.attempts += 1
                os.close(self.real_open(path, os.O_WRONLY | os.O_CREAT, 0o600, dir_fd=dir_fd))  # type: ignore[arg-type]
            else:
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(path, dir_fd=dir_fd)  # type: ignore[arg-type]
        return self.real_open(path, flags, *args, dir_fd=dir_fd, **kwargs)  # type: ignore[arg-type]


def test_lock_creation_churn_is_bounded_by_the_lock_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Sol r3 blocker 2: 1,001 create/open retries took 0.328 s despite a 0.01 s deadline.
    cache = tmp_path / "cache"
    cache.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))
    monkeypatch.setenv("LU_UV_CACHE_LOCK_TIMEOUT_S", "0.05")
    churn = _LockChurn()
    monkeypatch.setattr(os, "open", churn)

    started = time.monotonic()
    assert uv.main([]) == 0
    elapsed = time.monotonic() - started

    assert churn.churning(), "the retries outlived the churn instead of the deadline"
    assert churn.attempts >= 2 and elapsed < 3
    assert capsys.readouterr().out.startswith("UV CACHE: history busy (lock held by another writer for 0.05s)")
    assert not (state / uv.HISTORY_FILENAME).exists()


def test_one_deadline_covers_lock_creation_retries_and_the_lock_wait(tmp_path: Path) -> None:
    # Churn uses most of the deadline, then another writer holds the lock: the wait gets
    # only what is left, not a fresh deadline of its own.
    state = tmp_path / "state"
    state.mkdir()
    timeout = 1.0
    churn = _LockChurn(seconds=0.7 * timeout)
    holder: list[int] = []

    def churn_then_hold(path: object, flags: int, *args: object, dir_fd: int | None = None, **kwargs: object) -> int:
        if path == churn.name and not churn.churning() and not holder:
            held = churn.real_open(path, os.O_RDWR | os.O_CREAT, 0o600, dir_fd=dir_fd)  # type: ignore[arg-type]
            fcntl.flock(held, fcntl.LOCK_EX)
            holder.append(held)
        return churn(path, flags, *args, dir_fd=dir_fd, **kwargs)

    try:
        with _dir_fd(state) as fd, pytest.MonkeyPatch.context() as patch:
            patch.setattr(os, "open", churn_then_hold)
            started = time.monotonic()
            with pytest.raises(uv.HistoryBusy):
                uv.record_sample(fd, NOW, GIB, lock_timeout_s=timeout)
            elapsed = time.monotonic() - started
    finally:
        for held in holder:
            os.close(held)

    assert holder and churn.attempts >= 2
    # A fresh deadline for the wait would end near 1.7 s.
    assert timeout <= elapsed < 1.4 * timeout
    assert not (state / uv.HISTORY_FILENAME).exists()


def test_location_problem_checks_cache_path_expected_path_and_identity(tmp_path: Path) -> None:
    cache_real = tmp_path / "cache"
    expected = tmp_path / "state"
    ident = (1, 7)

    def problem(bound_path: Path, expected_identity: tuple[int, int] | None = ident, **kwargs: object) -> str | None:
        return uv.location_problem(
            bound_path=str(bound_path),
            bound_identity=ident,
            expected_path=kwargs.get("expected_path", expected),  # type: ignore[arg-type]
            expected_identity=expected_identity,
            cache_reals=kwargs.get("cache_reals", [cache_real]),  # type: ignore[arg-type]
        )

    assert problem(expected) is None
    # Inside the cache, even when that is where the history was expected.
    assert problem(cache_real, expected_path=cache_real) == uv._INSIDE_CACHE
    assert problem(cache_real / "moved-state", expected_path=cache_real / "moved-state") == uv._INSIDE_CACHE
    # The cache's real path now counts as well as its real path at open time.
    now_cache = tmp_path / "cache-now"
    assert problem(expected, cache_reals=[cache_real, tmp_path]) == uv._INSIDE_CACHE
    assert problem(now_cache / "s", expected_path=now_cache / "s", cache_reals=[cache_real, now_cache]) == (
        uv._INSIDE_CACHE
    )
    assert problem(tmp_path / "elsewhere") == "the history directory was moved after it was opened"
    assert problem(expected, expected_identity=(1, 8)) == "the history directory path now names a different directory"
    assert problem(expected, expected_identity=None) == "the history directory path now names a different directory"
    assert problem(tmp_path / "cache-state", expected_path=tmp_path / "cache-state") is None


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads directories regardless of mode")
def test_unreadable_cache_reports_measurement_failed_and_records_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cache = tmp_path / "cache"
    (cache / "locked").mkdir(parents=True)
    (cache / "locked").chmod(0)
    state = tmp_path / "state"
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(state))
    try:
        assert uv.main([]) == 0
    finally:
        (cache / "locked").chmod(0o700)

    out = capsys.readouterr().out
    assert out.startswith("UV CACHE: measurement failed (")
    assert "Permission denied" in out and str(cache) not in out
    assert not (state / uv.HISTORY_FILENAME).exists()


def test_measuring_error_is_not_a_zero_sample(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / uv.HISTORY_FILENAME

    def unreadable(_root: Path) -> int:
        raise PermissionError(13, "Permission denied")

    with _dir_fd(tmp_path) as fd:
        status = uv.build_status(cache=cache, history_dir_fd=fd, now=NOW, size_fn=unreadable)

    assert uv.format_line(status) == "UV CACHE: measurement failed ([Errno 13] Permission denied)"
    assert "bytes" not in status and not history.exists()


def test_missing_du_reports_measurement_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    monkeypatch.setenv("PATH", str(empty_bin))
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setenv("LU_DRIVER_STATUS_STATE_DIR", str(tmp_path / "state"))

    assert uv.main(["--no-record"]) == 0
    assert capsys.readouterr().out.startswith("UV CACHE: measurement failed (du: ")


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
        status = uv.build_status(cache=cache, history_dir_fd=fd, now=NOW, size_fn=lambda _root: GIB)

    assert 0.2 <= elapsed < 2
    assert status["bytes"] == GIB
    assert uv.format_line(status) == (
        "UV CACHE: history busy (lock held by another writer for 2s); 1.00 GiB measured, no sample recorded"
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
            [sys.executable, "-m", "scripts.hygiene.uv_cache_status"],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        elapsed = time.monotonic() - started

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("UV CACHE: history busy (lock held by another writer for 0.3s); 0.00 GiB measured")
    assert elapsed < 0.3 + 5 + 20  # both deadlines plus interpreter start-up
    assert not (state / uv.HISTORY_FILENAME).exists()


def test_lock_timeout_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    assert uv.lock_timeout_seconds() == 2
    monkeypatch.setenv("LU_UV_CACHE_LOCK_TIMEOUT_S", "0.25")
    assert uv.lock_timeout_seconds() == 0.25
    for bad in ("0", "-1", "soon", "inf", "nan"):
        monkeypatch.setenv("LU_UV_CACHE_LOCK_TIMEOUT_S", bad)
        assert uv.lock_timeout_seconds() == 2


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

    assert uv.main([]) == 0

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
