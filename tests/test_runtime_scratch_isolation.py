"""Delegate runtime leases stay off the host scratch root (#9927)."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from scripts.common import scratch

# The host constant, bound before any per-test patch of the module attribute.
_HOST_DEFAULT_SCRATCH_ROOT = scratch.DEFAULT_SCRATCH_ROOT


def _resolved(path: Path) -> Path:
    return path.resolve()


def _assert_scan_stays_inside(boundary: Path, found: list[Path]) -> list[Path]:
    """Fail before a sweep can act when a scan root leaves ``boundary``."""
    resolved = [_resolved(path) for path in found]
    outside = [path for path in resolved if not path.is_relative_to(boundary)]
    assert not outside, f"scratch scan left the per-test root: {outside}"
    return resolved


def _assert_deletion_target_inside(boundary: Path, root: Path, *, deletions: int) -> None:
    """Refuse, before any removal, when the resolved target leaves ``boundary``."""
    resolved = _resolved(root)
    assert resolved.is_relative_to(boundary), (
        f"review-root deletion target left the per-test root before removal (deletions={deletions})"
    )


def test_scan_root_override_drops_roots_outside_the_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A confine root with no in-bound candidate is itself the whole scan."""
    outside = tmp_path.parent / f"scan-outside-{tmp_path.name}"
    outside.mkdir()
    try:
        monkeypatch.setenv(scratch.SCRATCH_ROOT_ENV_VAR, str(tmp_path / "missing-scratch"))
        monkeypatch.delenv("LU_RUNTIME_TMP_BASE_ROOT", raising=False)
        monkeypatch.setattr(scratch, "DEFAULT_SCRATCH_ROOT", outside)
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(outside))

        roots = scratch.scratch_scan_roots()
        assert [_resolved(path) for path in roots] == [_resolved(tmp_path)]
    finally:
        shutil.rmtree(outside)


def test_scan_root_override_rejects_a_missing_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A confine path that does not exist scans nothing and does not fall open."""
    missing = tmp_path / "missing-boundary"
    monkeypatch.setenv(scratch.SCRATCH_SCAN_ROOT_ENV_VAR, str(missing))
    with pytest.raises(scratch.ScratchScanRootError) as caught:
        scratch.scratch_scan_roots()
    assert caught.value.reason == scratch.SCAN_ROOT_REASON_NOT_A_DIRECTORY
    assert str(caught.value) == "LU_SCRATCH_SCAN_ROOT is misconfigured: not_a_directory"
    assert "/" not in str(caught.value)
    assert caught.value.__cause__ is None


def test_review_root_deletion_stays_inside_the_per_test_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deletion guard calls the real remove only after the target resolves inside tmp_path.

    Confinement is on. The real review sweep reaps one aged review root that
    lives under this test's directory. ``counting_remove`` resolves that
    target and asserts it is inside ``tmp_path`` before the real remove.
    The scan guard checks the scan result before that deletion.
    """
    from scripts.review import isolation

    boundary = _resolved(tmp_path)
    host_temp = _resolved(Path(tempfile.gettempdir()))
    assert not host_temp.is_relative_to(boundary)
    assert not _resolved(_HOST_DEFAULT_SCRATCH_ROOT).is_relative_to(boundary)

    review_root = tmp_path / "lu-review-snap-confinement"
    review_root.mkdir()
    (review_root / "payload").write_text("review-root", encoding="utf-8")
    now = time.time()
    old = now - isolation.REVIEW_TEMP_ORPHAN_MAX_AGE_S - 5
    os.utime(review_root, (old, old))

    removals = {"n": 0}
    original_scan = scratch.scratch_scan_roots
    original_remove = isolation._remove_review_temp_orphan
    seen: list[Path] = []

    def counting_remove(root: Path) -> None:
        _assert_deletion_target_inside(boundary, root, deletions=removals["n"])
        removals["n"] += 1
        original_remove(root)

    def guarded_scan() -> list[Path]:
        found = original_scan()
        resolved = [_resolved(path) for path in found]
        outside = [path for path in resolved if not path.is_relative_to(boundary)]
        assert not outside, (
            "scratch scan left the per-test root before any review-root deletion "
            f"(outside={len(outside)}, deletions={removals['n']})"
        )
        seen.extend(resolved)
        return found

    monkeypatch.setattr(scratch, "scratch_scan_roots", guarded_scan)
    monkeypatch.setattr(isolation, "scratch_scan_roots", guarded_scan)
    monkeypatch.setattr(isolation, "_remove_review_temp_orphan", counting_remove)

    result = isolation.sweep_review_temp_orphans(now=now)
    assert result["roots_reaped"] == 1
    assert result["errors"] == 0
    assert not review_root.exists()
    assert removals["n"] == 1
    assert seen, "review sweep did not scan"
    assert host_temp not in seen
    assert _resolved(_HOST_DEFAULT_SCRATCH_ROOT) not in seen
    assert all(path.is_relative_to(boundary) for path in seen)


def test_review_sweep_refuses_an_outside_review_root_before_deletion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An outside review root offered to the sweep is refused before it is deleted.

    Confinement stays on, so every scan root stays inside ``tmp_path``. The
    sweep is then offered one aged review root that lives outside that
    directory. The deletion guard raises on the resolved target, and the
    sentinel directory is still there afterwards.
    """
    from scripts.review import isolation

    boundary = _resolved(tmp_path)
    sentinel = tmp_path.parent / f"lu-review-snap-outside-{tmp_path.name}"
    sentinel.mkdir()
    try:
        (sentinel / "payload").write_text("keep", encoding="utf-8")
        assert not _resolved(sentinel).is_relative_to(boundary)
        now = time.time()
        old = now - isolation.REVIEW_TEMP_ORPHAN_MAX_AGE_S - 5
        os.utime(sentinel, (old, old))

        removals = {"n": 0}
        original_scan = scratch.scratch_scan_roots
        original_remove = isolation._remove_review_temp_orphan
        original_candidates = isolation._review_temp_orphan_candidates
        seen: list[Path] = []

        def counting_remove(root: Path) -> None:
            _assert_deletion_target_inside(boundary, root, deletions=removals["n"])
            removals["n"] += 1
            original_remove(root)

        def guarded_scan() -> list[Path]:
            found = original_scan()
            resolved = _assert_scan_stays_inside(boundary, found)
            seen.extend(resolved)
            return found

        def offer_sentinel(base: Path) -> tuple[Path, ...]:
            found = original_candidates(base)
            if any(_resolved(path) == _resolved(sentinel) for path in found):
                return found
            return (*found, sentinel)

        monkeypatch.setattr(scratch, "scratch_scan_roots", guarded_scan)
        monkeypatch.setattr(isolation, "scratch_scan_roots", guarded_scan)
        monkeypatch.setattr(isolation, "_remove_review_temp_orphan", counting_remove)
        monkeypatch.setattr(isolation, "_review_temp_orphan_candidates", offer_sentinel)

        with pytest.raises(AssertionError, match="left the per-test root before removal") as caught:
            isolation.sweep_review_temp_orphans(now=now)
        assert "deletions=0" in str(caught.value)
        assert sentinel.is_dir()
        assert (sentinel / "payload").read_text(encoding="utf-8") == "keep"
        assert removals["n"] == 0
        assert seen, "review sweep did not scan"
        assert _resolved(sentinel) not in seen
        assert all(path.is_relative_to(boundary) for path in seen)
    finally:
        shutil.rmtree(sentinel, ignore_errors=True)


def test_scan_root_symlink_inside_its_parent_remains_the_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A symlink that stays inside its parent is still a confine directory."""
    parent = tmp_path / "confine-parent"
    real = parent / "real"
    real.mkdir(parents=True)
    link = parent / "link"
    link.symlink_to(real, target_is_directory=True)
    monkeypatch.setenv(scratch.SCRATCH_SCAN_ROOT_ENV_VAR, str(link))
    assert scratch.resolve_confined_scan_root() == real.resolve()
