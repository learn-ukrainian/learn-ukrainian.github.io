"""uv cache size/growth line for lu-driver-status (#10779), driven by injected sizes."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.hygiene import uv_cache_status as uv

GIB = 1024**3
HOUR = 3600
NOW = 1_800_000_000.0


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LU_UV_CACHE_WARN_GB", "LU_UV_CACHE_GROWTH_WARN_GB", "UV_CACHE_DIR", "LU_DRIVER_STATUS_STATE_DIR"):
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


def test_tree_size_counts_hardlinks_once_and_never_follows_symlinks(tmp_path: Path) -> None:
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

    assert uv.tree_size(root / "a") == uv.tree_size(lone)  # the hardlinked pair counts once
    # only the symlink entry itself is counted, not the 1 MB tree behind it
    assert 0 <= uv.tree_size(root) - uv.tree_size(root / "a") < 16384


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
