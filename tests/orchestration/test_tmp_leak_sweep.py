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
    assert tls.name_matches_leak_pattern("mq-runner-log-123")
    assert tls.name_matches_leak_pattern("contracts-job-scratch-456")
    assert tls.name_matches_leak_pattern("learn-ukrainian-bridge-asks")
    assert tls.name_matches_leak_pattern("learn-ukrainian-something")
    assert not tls.name_matches_leak_pattern("com.apple.imagent")
    assert not tls.name_matches_leak_pattern("claude-501")
    assert not tls.name_matches_leak_pattern("cc-socks")
    assert not tls.name_matches_leak_pattern("random-scratch")


def test_default_tmp_roots_includes_scratch_and_base_override(tmp_path: Path, monkeypatch) -> None:
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    base_root = tmp_path / "base"
    base_root.mkdir()

    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch_root))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(base_root))

    roots = tls.default_tmp_roots()
    resolved_roots = [r.resolve() for r in roots]
    assert scratch_root.resolve() in resolved_roots
    assert base_root.resolve() in resolved_roots


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


def test_dry_run_does_not_delete(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "pr6568"
    _touch_old(target, age_s=10_000)
    real_run = tls.subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if cmd[0] == "pgrep":
            return tls.subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(tls.subprocess, "run", fake_run)
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


def test_apply_reaps_old_candidate(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-2002"
    _touch_old(target, age_s=10_000)
    real_run = tls.subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if cmd[0] == "pgrep":
            return tls.subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(tls.subprocess, "run", fake_run)
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


def test_path_has_live_process_matching_and_nonmatching(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-process-check"

    # returncode == 0 means matching process found -> True
    monkeypatch.setattr(
        tls.subprocess,
        "run",
        lambda *args, **kwargs: tls.subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=b"1234\n", stderr=b""
        ),
    )
    assert tls.path_has_live_process(target) is True

    # returncode != 0 means no process found -> False
    monkeypatch.setattr(
        tls.subprocess,
        "run",
        lambda *args, **kwargs: tls.subprocess.CompletedProcess(args=args[0], returncode=1, stdout=b"", stderr=b""),
    )
    assert tls.path_has_live_process(target) is False


def test_path_has_live_process_fails_closed_on_exceptions(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-fail-closed"

    def raise_timeout(*args, **kwargs):
        raise tls.subprocess.TimeoutExpired(cmd="pgrep", timeout=5)

    monkeypatch.setattr(tls.subprocess, "run", raise_timeout)
    assert tls.path_has_live_process(target) is True

    def raise_fnf(*args, **kwargs):
        raise FileNotFoundError("pgrep not found")

    monkeypatch.setattr(tls.subprocess, "run", raise_fnf)
    assert tls.path_has_live_process(target) is True

    def raise_oserror(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(tls.subprocess, "run", raise_oserror)
    assert tls.path_has_live_process(target) is True


def test_live_process_is_skipped_via_pgrep(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-3003"
    _touch_old(target, age_s=10_000)
    # pgrep finds a process
    monkeypatch.setattr(
        tls.subprocess,
        "run",
        lambda *args, **kwargs: tls.subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=b"9999\n", stderr=b""
        ),
    )
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


def test_live_process_skipped_on_pgrep_timeout_fail_closed(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-3004"
    _touch_old(target, age_s=10_000)

    def raise_timeout(*args, **kwargs):
        raise tls.subprocess.TimeoutExpired(cmd="pgrep", timeout=5)

    monkeypatch.setattr(tls.subprocess, "run", raise_timeout)
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


def test_recheck_liveness_immediately_before_deletion(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-3005"
    _touch_old(target, age_s=10_000)

    pgrep_call_count = 0
    real_run = tls.subprocess.run

    def fake_run(cmd, *args, **kwargs):
        nonlocal pgrep_call_count
        if cmd[0] == "pgrep":
            pgrep_call_count += 1
            # First pgrep call during candidate loop: dead (rc=1)
            # Second pgrep call immediately before deletion: live (rc=0)
            if pgrep_call_count == 1:
                return tls.subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
            return tls.subprocess.CompletedProcess(args=cmd, returncode=0, stdout="8888\n", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(tls.subprocess, "run", fake_run)
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
    assert pgrep_call_count == 2


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
