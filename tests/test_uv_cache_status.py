"""uv cache size/growth line for lu-driver-status (#10779), driven by injected sizes."""

from __future__ import annotations

import json
import os
import threading
import time
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


def _status(cache: Path, history: Path, size: int, now: float = NOW, **kwargs: object) -> dict[str, object]:
    return uv.build_status(cache=cache, history_path=history, now=now, size_fn=lambda _root: size, **kwargs)


def test_growth_uses_oldest_sample_inside_24h_and_reports_real_span(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "h.jsonl"
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
    history = tmp_path / "h.jsonl"
    _write_history(history, (NOW - 24 * HOUR, 4 * GIB))

    assert uv.format_line(_status(cache, history, 5 * GIB)) == "UV CACHE: 5.00 GiB, +1.00 GiB over 24h"


def test_shrinking_cache_reports_negative_growth_without_warning(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "h.jsonl"
    _write_history(history, (NOW - 24 * HOUR, 9 * GIB))

    status = _status(cache, history, 4 * GIB)

    assert status["warnings"] == []
    assert uv.format_line(status) == "UV CACHE: 4.00 GiB, -5.00 GiB over 24h"


def test_no_usable_baseline_reports_history_building(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "h.jsonl"
    _write_history(history, (NOW - 600, 3 * GIB))  # too young to say anything about growth

    status = _status(cache, history, 3 * GIB)

    assert status["growth_bytes"] is None
    assert uv.format_line(status) == "UV CACHE: 3.00 GiB, growth n/a (history building)"


def test_first_run_creates_history_and_second_run_dedupes_inside_interval(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "state" / "h.jsonl"

    _status(cache, history, GIB)
    _status(cache, history, 2 * GIB, now=NOW + 60)

    rows = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines()]
    assert rows == [{"ts": NOW, "bytes": GIB}]
    _status(cache, history, 2 * GIB, now=NOW + uv.MIN_SAMPLE_INTERVAL_SECONDS)
    assert len(history.read_text(encoding="utf-8").splitlines()) == 2


def test_samples_older_than_retention_are_dropped(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "h.jsonl"
    _write_history(history, (NOW - uv.RETENTION_SECONDS - 1, GIB), (NOW - 3 * HOUR, 2 * GIB))

    _status(cache, history, 3 * GIB)

    assert [row["bytes"] for row in uv.read_history(history)] == [2 * GIB, 3 * GIB]


def test_corrupt_history_lines_are_skipped(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "h.jsonl"
    history.write_text('not json\n{"ts": "x"}\n{"ts": 1, "bytes": 2}\n[1]\n', encoding="utf-8")

    assert uv.read_history(history) == [{"ts": 1.0, "bytes": 2.0}]


def test_absolute_size_warning_uses_default_and_env_threshold(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    history = tmp_path / "h.jsonl"

    status = _status(cache, history, 11 * GIB, record=False)
    assert status["warnings"] == ["size above 10 GiB"]
    assert uv.format_line(status).endswith("[WARN: size above 10 GiB]")

    monkeypatch.setenv("LU_UV_CACHE_WARN_GB", "20")
    assert _status(cache, history, 11 * GIB, record=False)["warnings"] == []


def test_growth_warning_uses_default_and_env_threshold(
    cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    history = tmp_path / "h.jsonl"
    _write_history(history, (NOW - 24 * HOUR, 5 * GIB))

    status = _status(cache, history, 8 * GIB, record=False)
    assert status["warnings"] == ["growth above 2 GiB per 24 h"]

    monkeypatch.setenv("LU_UV_CACHE_GROWTH_WARN_GB", "3")
    assert _status(cache, history, 8 * GIB, record=False)["warnings"] == []
    monkeypatch.setenv("LU_UV_CACHE_GROWTH_WARN_GB", "garbage")
    assert _status(cache, history, 8 * GIB, record=False)["warnings"] == ["growth above 2 GiB per 24 h"]


def test_no_record_leaves_no_history_file(cache: Path, tmp_path: Path) -> None:
    history = tmp_path / "state" / "h.jsonl"

    _status(cache, history, GIB, record=False)

    assert not history.exists() and not history.parent.exists()


def test_missing_cache_is_reported_without_touching_history(tmp_path: Path) -> None:
    history = tmp_path / "h.jsonl"

    status = uv.build_status(cache=tmp_path / "absent", history_path=history, now=NOW)

    assert uv.format_line(status) == "UV CACHE: not present"
    assert not history.exists()


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
    history = tmp_path / "h.jsonl"

    def unreadable(_root: Path) -> int:
        raise PermissionError(13, "Permission denied")

    status = uv.build_status(cache=cache, history_path=history, now=NOW, size_fn=unreadable)

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
    history = tmp_path / "state" / "h.jsonl"
    history.parent.mkdir()
    _write_history(history, (1000.0, GIB))
    original_read = uv.read_history
    older_has_read = threading.Event()
    newer_done = threading.Event()

    def racing_read(path: Path) -> list[dict[str, float]]:
        rows = original_read(path)
        if threading.current_thread().name == "older":
            older_has_read.set()
            # Unserialized writers let the newer one read, write and finish in this window.
            newer_done.wait(timeout=2)
        return rows

    def newer_writer() -> None:
        uv.record_sample(history, 3000.0, 3 * GIB)
        newer_done.set()

    monkeypatch.setattr(uv, "read_history", racing_read)
    older = threading.Thread(target=uv.record_sample, args=(history, 2000.0, 2 * GIB), name="older")
    newer = threading.Thread(target=newer_writer, name="newer")
    older.start()
    assert older_has_read.wait(timeout=30)
    newer.start()
    older.join(timeout=30)
    newer.join(timeout=30)

    assert [row["ts"] for row in original_read(history)] == [1000.0, 2000.0, 3000.0]
    assert (history.parent / (history.name + uv.LOCK_SUFFIX)).is_file()


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
    assert len(uv.read_history(state / uv.HISTORY_FILENAME)) == 1
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
