"""Unit tests for the fail-closed deploy size gate (#5274)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.deploy.check_site_size import (
    GITHUB_PAGES_FAIL_BYTES,
    GITHUB_PAGES_HARD_CAP_BYTES,
    GITHUB_PAGES_WARN_BYTES,
    SiteSizeReport,
    apply_profile,
    check_site_size,
    main,
    resolve_profile,
    scan_dist,
)


def _write_file(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def _empty_report(**overrides: object) -> SiteSizeReport:
    base = SiteSizeReport(
        total_bytes=0,
        file_count=0,
        largest_files=[],
        families={},
        lexicon_page_count=0,
        lexicon_page_bytes=0,
        projected_bytes_at_target=None,
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_resolve_profile_fail_closed_on_missing_or_unknown() -> None:
    with pytest.raises(ValueError, match="fail closed"):
        resolve_profile(None)
    with pytest.raises(ValueError, match="fail closed"):
        resolve_profile("")
    with pytest.raises(ValueError, match="fail closed"):
        resolve_profile("not-a-real-profile")


def test_github_pages_pass_under_70_percent() -> None:
    report = _empty_report(total_bytes=GITHUB_PAGES_WARN_BYTES - 1, file_count=1)
    apply_profile(report, resolve_profile("github-pages"))
    assert report.ok is True
    assert report.warnings == []
    assert report.failures == []


def test_github_pages_warn_between_70_and_80_percent() -> None:
    size = (GITHUB_PAGES_WARN_BYTES + GITHUB_PAGES_FAIL_BYTES) // 2
    report = _empty_report(total_bytes=size, file_count=1)
    apply_profile(report, resolve_profile("github-pages"))
    assert report.ok is True
    assert any("warn" in w for w in report.warnings)
    assert report.failures == []


def test_github_pages_fail_at_or_above_80_percent() -> None:
    report = _empty_report(total_bytes=GITHUB_PAGES_FAIL_BYTES, file_count=1)
    apply_profile(report, resolve_profile("github-pages"))
    assert report.ok is False
    assert any("fail" in f for f in report.failures)


def test_github_pages_hard_cap_fails() -> None:
    # Above fail% would already fail; pin just under fail% but at hard cap
    # is impossible (hard cap 900M > fail 80%≈859M). Assert hard-cap message
    # when total crosses the absolute ceiling.
    report = _empty_report(total_bytes=GITHUB_PAGES_HARD_CAP_BYTES, file_count=1)
    apply_profile(report, resolve_profile("github-pages"))
    assert report.ok is False
    assert any("hard cap" in f for f in report.failures)


def test_unknown_profile_main_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dist = tmp_path / "dist"
    _write_file(dist / "index.html", 32)
    monkeypatch.delenv("DEPLOY_PROFILE", raising=False)
    assert main([str(dist), "--profile", "nope"]) == 1
    assert main([str(dist)]) == 1  # missing profile also fails closed


def test_cloudflare_file_count_caps() -> None:
    free = _empty_report(total_bytes=100, file_count=3)
    apply_profile(free, resolve_profile("cloudflare-free"))
    assert free.ok is True

    free_hit = _empty_report(total_bytes=100, file_count=20_000)
    apply_profile(free_hit, resolve_profile("cloudflare-free"))
    assert free_hit.ok is False
    assert any("file count" in f for f in free_hit.failures)

    paid_ok = _empty_report(total_bytes=100, file_count=20_000)
    apply_profile(paid_ok, resolve_profile("cloudflare-paid"))
    assert paid_ok.ok is True

    paid_hit = _empty_report(total_bytes=100, file_count=100_000)
    apply_profile(paid_hit, resolve_profile("cloudflare-paid"))
    assert paid_hit.ok is False
    assert any("file count" in f for f in paid_hit.failures)


def test_route_families_and_fixed_base_projection(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_file(dist / "index.html", 1000)  # base
    _write_file(dist / "etymology" / "index.html", 2000)
    _write_file(dist / "lexicon" / "index.html", 500)  # not a word page
    _write_file(dist / "lexicon" / "кава" / "index.html", 4000)
    _write_file(dist / "lexicon" / "вода" / "index.html", 6000)

    report = scan_dist(dist)
    assert report.families["base"].bytes == 1000
    assert report.families["etymology"].bytes == 2000
    assert report.families["lexicon"].bytes == 500 + 4000 + 6000
    assert report.lexicon_page_count == 2
    assert report.lexicon_page_bytes == 10_000
    # base = total - lexicon word pages = 13500 - 10000 = 3500
    # slope = 5000; projected @20k = 3500 + 20000*5000
    assert report.total_bytes == 13_500
    assert report.projected_bytes_at_target == 3500 + 20_000 * 5_000


def test_check_site_size_end_to_end_pass(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _write_file(dist / "index.html", 128)
    report, profile = check_site_size(dist, "github-pages")
    assert profile.name == "github-pages"
    assert report.ok is True
    assert report.file_count == 1
