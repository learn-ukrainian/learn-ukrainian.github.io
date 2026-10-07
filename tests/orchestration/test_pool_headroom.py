"""Shared lu.slice pool headroom from fake cgroup v2 files (#9975)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.orchestration import pool_headroom

_GIB = 1024**3


def fake_cgroup(
    directory: Path,
    *,
    current: int | str,
    active_file: int = 0,
    inactive_file: int = 0,
    high: int | str = "max",
    maximum: int | str = "max",
    stat: str | None = None,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "memory.current").write_text(f"{current}\n", encoding="ascii")
    (directory / "memory.high").write_text(f"{high}\n", encoding="ascii")
    (directory / "memory.max").write_text(f"{maximum}\n", encoding="ascii")
    if stat is None:
        stat = f"anon 1\nfile {active_file + inactive_file}\nactive_file {active_file}\ninactive_file {inactive_file}\n"
    (directory / "memory.stat").write_text(stat, encoding="ascii")
    return directory


def test_use_excludes_reclaimable_file_cache(tmp_path):
    pool = fake_cgroup(
        tmp_path / "lu.slice", current=10 * _GIB, active_file=3 * _GIB, inactive_file=2 * _GIB, high=24 * _GIB
    )

    check = pool_headroom.check_pool(2 * _GIB, pool)

    assert check.skipped is None
    assert check.memory is not None
    assert check.memory.nonreclaimable == 5 * _GIB
    assert check.headroom_bytes == 19 * _GIB
    assert check.fits
    assert check.clause() == "lu.slice 5.0/24.0 GiB non-cache (+5.0 GiB file cache; worker reserve 2 GiB)"


def test_cache_heavy_pool_fits_where_raw_current_would_not(tmp_path):
    pool = fake_cgroup(tmp_path / "lu.slice", current=23 * _GIB, inactive_file=6 * _GIB, high=24 * _GIB)

    assert pool_headroom.check_pool(2 * _GIB, pool).fits


def test_reserve_past_memory_high_does_not_fit(tmp_path):
    pool = fake_cgroup(tmp_path / "lu.slice", current=25 * _GIB, active_file=2 * _GIB, high=24 * _GIB)

    check = pool_headroom.check_pool(2 * _GIB, pool)

    assert not check.fits
    assert check.failure() == (
        "lu.slice non-cache use 23.0 GiB plus a 2 GiB worker reserve exceeds MemoryHigh 24.0 GiB"
    )


def test_reserve_exactly_at_memory_high_fits(tmp_path):
    pool = fake_cgroup(tmp_path / "lu.slice", current=22 * _GIB, high=24 * _GIB)

    assert pool_headroom.check_pool(2 * _GIB, pool).fits
    assert not pool_headroom.check_pool(2 * _GIB + 1, pool).fits


def test_memory_max_is_the_limit_when_high_is_unset(tmp_path):
    pool = fake_cgroup(tmp_path / "lu.slice", current=25 * _GIB, high="max", maximum=26 * _GIB)

    check = pool_headroom.check_pool(2 * _GIB, pool)

    assert not check.fits
    assert "exceeds MemoryMax 26.0 GiB" in check.failure()


def test_uncapped_pool_always_fits(tmp_path):
    pool = fake_cgroup(tmp_path / "lu.slice", current=40 * _GIB)

    check = pool_headroom.check_pool(2 * _GIB, pool)

    assert check.fits
    assert check.headroom_bytes is None
    assert "no limit" in check.clause()


@pytest.mark.parametrize(
    ("setup", "reason"),
    [
        (lambda d: None, "memory.current unavailable"),
        (lambda d: fake_cgroup(d, current="garbage"), "memory.current is not a number"),
        (lambda d: fake_cgroup(d, current=_GIB, stat="anon 1\n"), "no active_file/inactive_file"),
        (lambda d: fake_cgroup(d, current=_GIB, stat="active_file x\ninactive_file 1\n"), "no active_file"),
    ],
)
def test_missing_or_invalid_files_skip_without_raising(tmp_path, setup, reason):
    directory = tmp_path / "lu.slice"
    setup(directory)

    check = pool_headroom.check_pool(2 * _GIB, directory)

    assert check.memory is None
    assert reason in (check.skipped or "")
    assert check.fits
    assert check.clause().startswith("lu.slice pool check skipped (")
    assert str(tmp_path) not in check.clause()


def test_default_pool_cgroup_honours_override_and_user_path(monkeypatch):
    assert pool_headroom.default_pool_cgroup({"LU_SLICE_CGROUP": "/fake/lu.slice"}) == Path("/fake/lu.slice")
    default = pool_headroom.default_pool_cgroup({})
    assert default.name == "lu.slice"
    assert default.parent.name.startswith("user@")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("/user.slice/lu.slice/lu-dispatch.slice", "user.slice/lu.slice/lu-dispatch.slice"),
        ("", None),
        (None, None),
        ("relative/lu.slice", None),
        ("/user.slice/../etc", None),
    ],
)
def test_cgroup_dir_accepts_only_absolute_safe_paths(value, expected):
    result = pool_headroom.cgroup_dir(value)
    assert result == (None if expected is None else pool_headroom.CGROUP_ROOT / expected)


@pytest.mark.parametrize(
    ("high", "maximum", "reason"),
    [
        ("24G", 26 * _GIB, "lu.slice memory.high is neither a number nor 'max'"),
        ("", 26 * _GIB, "lu.slice memory.high is neither a number nor 'max'"),
        ("-1", 26 * _GIB, "lu.slice memory.high is negative"),
        (24 * _GIB, "garbage", "lu.slice memory.max is neither a number nor 'max'"),
        ("max", "garbage", "lu.slice memory.max is neither a number nor 'max'"),
    ],
)
def test_malformed_limit_skips_instead_of_falling_back(tmp_path, high, maximum, reason):
    pool = fake_cgroup(tmp_path / "lu.slice", current=25 * _GIB, high=high, maximum=maximum)

    check = pool_headroom.check_pool(2 * _GIB, pool)

    assert check.memory is None
    assert check.skipped == reason
    assert check.clause() == f"lu.slice pool check skipped ({reason})"


def test_missing_memory_high_skips_instead_of_falling_back(tmp_path):
    pool = fake_cgroup(tmp_path / "lu.slice", current=25 * _GIB, maximum=26 * _GIB)
    (pool / "memory.high").unlink()

    check = pool_headroom.check_pool(2 * _GIB, pool)

    assert check.memory is None
    assert (check.skipped or "").startswith("lu.slice memory.high unavailable: ")
    assert str(tmp_path) not in check.clause()
