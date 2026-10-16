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


@pytest.mark.parametrize("at_call", [1, 2, 3], ids=["before-lock", "before-temp-file", "before-rename"])
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
