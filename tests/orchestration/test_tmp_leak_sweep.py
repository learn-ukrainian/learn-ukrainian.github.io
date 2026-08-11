"""Tests for ad-hoc /tmp leak sweep (# disk pressure)."""

from __future__ import annotations

import os
import time
from pathlib import Path

from scripts.orchestration import tmp_leak_sweep as tls


def _touch_old(path: Path, *, age_s: float, as_file: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if as_file or path.suffix:
        path.write_text("x", encoding="utf-8")
    else:
        path.mkdir(parents=True, exist_ok=True)
        (path / "marker").write_text("x", encoding="utf-8")
    past = time.time() - age_s
    os.utime(path, (past, past))


def test_name_patterns_match_known_leaks() -> None:
    assert tls.name_matches_leak_pattern("review-6621")
    assert tls.name_matches_leak_pattern("pr6591-exact-ujs9Ng")
    assert tls.name_matches_leak_pattern("lu-agent-runtime-git")
    assert tls.name_matches_leak_pattern("data_test_pipe3")
    assert tls.name_matches_leak_pattern("atlas6507-build.DnfqH3")
    assert not tls.name_matches_leak_pattern("com.apple.imagent")
    assert not tls.name_matches_leak_pattern("claude-501")
    assert not tls.name_matches_leak_pattern("cc-socks")
    assert not tls.name_matches_leak_pattern("random-scratch")


def test_discover_skips_young_and_unrelated(tmp_path: Path) -> None:
    old = tmp_path / "review-1001"
    young = tmp_path / "review-1002"
    safe = tmp_path / "com.apple.foo"
    _touch_old(old, age_s=10_000)
    _touch_old(young, age_s=30)
    _touch_old(safe, age_s=10_000)

    found = tls.discover_candidates([tmp_path], now=time.time(), min_age_s=3600)
    names = {c.path.name for c in found}
    assert "review-1001" in names
    assert "review-1002" not in names
    assert "com.apple.foo" not in names


def test_dry_run_does_not_delete(tmp_path: Path) -> None:
    target = tmp_path / "pr6568"
    _touch_old(target, age_s=10_000)
    report = tls.sweep_tmp_leaks(
        apply=False,
        tmp_roots=[tmp_path],
        now=time.time(),
        min_age_s=3600,
        min_free_gb=0.0,  # force non-pressure ages via min_age_s
    )
    assert report["candidates"] >= 1
    assert report["roots_reaped"] == 0
    assert target.exists()
    assert any(item["action"] == "would_reap" for item in report["reaped"])


def test_apply_reaps_old_candidate(tmp_path: Path) -> None:
    target = tmp_path / "review-2002"
    _touch_old(target, age_s=10_000)
    report = tls.sweep_tmp_leaks(
        apply=True,
        tmp_roots=[tmp_path],
        now=time.time(),
        min_age_s=3600,
        min_free_gb=0.0,
    )
    assert report["roots_reaped"] == 1
    assert not target.exists()
    assert report["bytes_freed"] > 0


def test_live_process_is_skipped(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-3003"
    _touch_old(target, age_s=10_000)
    monkeypatch.setattr(tls, "path_has_live_process", lambda _path: True)
    report = tls.sweep_tmp_leaks(
        apply=True,
        tmp_roots=[tmp_path],
        now=time.time(),
        min_age_s=3600,
        min_free_gb=0.0,
    )
    assert report["roots_reaped"] == 0
    assert report["skipped_live"] == 1
    assert target.exists()


def test_pressure_shortens_age(tmp_path: Path, monkeypatch) -> None:
    """Under free-space pressure, 45-minute-old leak is eligible."""
    target = tmp_path / "pr7001-exact-abc"
    _touch_old(target, age_s=45 * 60)
    monkeypatch.setattr(tls, "free_space_gb", lambda _path: 5.0)
    found = tls.discover_candidates(
        [tmp_path],
        now=time.time(),
        min_age_s=tls.DEFAULT_PRESSURE_MIN_AGE_S,
    )
    assert any(c.path.name == "pr7001-exact-abc" for c in found)
