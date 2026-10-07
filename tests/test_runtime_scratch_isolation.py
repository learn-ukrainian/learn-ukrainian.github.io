"""Delegate runtime leases stay off the host scratch root (#9927)."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
import traceback
from collections.abc import Iterator
from pathlib import Path

import pytest

import scripts.delegate as delegate
from scripts.common import scratch

# The host constant, bound before any per-test patch of the module attribute.
_HOST_DEFAULT_SCRATCH_ROOT = scratch.DEFAULT_SCRATCH_ROOT


def _resolved(path: Path) -> Path:
    return path.resolve()


def test_delegate_lease_is_not_created_under_the_real_default_scratch_root(tmp_path: Path) -> None:
    """A delegate lease uses the per-test override, never the host default namespace.

    The first assertion is the tripwire: with the isolation fixture disabled,
    ``LU_SCRATCH_ROOT`` is unset and this fails before a lease is created.
    """
    override = os.environ.get(scratch.SCRATCH_ROOT_ENV_VAR, "").strip()
    assert override, "LU_SCRATCH_ROOT was not set; a delegate lease would use the host scratch root"
    root = Path(override)
    assert _resolved(root).is_relative_to(_resolved(tmp_path))
    assert _resolved(root) != _resolved(_HOST_DEFAULT_SCRATCH_ROOT)

    lease, namespace = delegate._create_runtime_tmp_lease("scratch-isolation-guard")
    real_namespace = _HOST_DEFAULT_SCRATCH_ROOT / "learn-ukrainian"
    fallback_namespace = Path(tempfile.gettempdir()) / scratch.FALLBACK_SCRATCH_DIRNAME / "learn-ukrainian"
    assert _resolved(namespace) == _resolved(root / "learn-ukrainian")
    assert _resolved(lease.parent) == _resolved(namespace)
    assert _resolved(namespace) != _resolved(real_namespace)
    assert _resolved(namespace) != _resolved(fallback_namespace)
    assert lease.is_dir()
    assert delegate._read_runtime_tmp_task_id_marker(lease) == "scratch-isolation-guard"


@pytest.mark.exercises_default_scratch_root
def test_default_scratch_resolution_uses_a_private_fake_root(
    tmp_path: Path,
    _isolate_runtime_scratch_root: Path,
) -> None:
    """Default-root tests keep the override unset and must not touch /var/tmp/lu."""
    assert os.environ.get(scratch.SCRATCH_ROOT_ENV_VAR, "").strip() == ""
    assert scratch.resolve_scratch_root() == _isolate_runtime_scratch_root
    assert scratch.ensure_scratch_root() == _isolate_runtime_scratch_root
    assert _resolved(_isolate_runtime_scratch_root).is_relative_to(_resolved(tmp_path))
    assert _resolved(_isolate_runtime_scratch_root) != _resolved(_HOST_DEFAULT_SCRATCH_ROOT)

    lease, namespace = delegate._create_runtime_tmp_lease("default-resolution-guard")
    assert _resolved(namespace) == _resolved(_isolate_runtime_scratch_root / "learn-ukrainian")
    assert _resolved(lease.parent) == _resolved(namespace)
    assert _resolved(namespace) != _resolved(_HOST_DEFAULT_SCRATCH_ROOT / "learn-ukrainian")
    assert delegate._read_runtime_tmp_task_id_marker(lease) == "default-resolution-guard"

    scanned = [_resolved(path) for path in scratch.scratch_scan_roots()]
    assert _resolved(_isolate_runtime_scratch_root) in scanned
    assert all(path.is_relative_to(_resolved(tmp_path)) for path in scanned)
    assert _resolved(_HOST_DEFAULT_SCRATCH_ROOT) not in scanned
    assert _resolved(Path(tempfile.gettempdir())) not in scanned


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


def test_orphan_sweep_scans_and_deletes_only_inside_the_per_test_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real orphan sweeps never see a path outside this test's tmp dir.

    The per-test scratch root is created first, so a confined scan has a
    root to return and the sweep has a lease to reap. With confinement
    removed, the system temp directory is always a candidate and is not
    under ``tmp_path``. The assertion runs on the scan result before that
    result is handed back to the sweep, so the failure deletes nothing.
    """
    override = os.environ.get(scratch.SCRATCH_ROOT_ENV_VAR, "").strip()
    assert override, "LU_SCRATCH_ROOT was not set; a sweep would scan the host scratch roots"
    root = Path(override)
    root.mkdir(parents=True)
    boundary = _resolved(tmp_path)
    assert _resolved(root).is_relative_to(boundary)
    host_temp = _resolved(Path(tempfile.gettempdir()))
    assert not host_temp.is_relative_to(boundary)

    namespace = root / "learn-ukrainian"
    lease = namespace / "confinement-orphan"
    lease.mkdir(parents=True)
    (lease / "payload").write_text("orphan", encoding="utf-8")
    now = time.time()
    old = now - delegate._RUNTIME_TMP_ORPHAN_MAX_AGE_S - 5
    os.utime(lease, (old, old))

    from scripts.review import isolation

    original = scratch.scratch_scan_roots
    seen: list[Path] = []

    def guarded_scan() -> list[Path]:
        found = original()
        resolved = _assert_scan_stays_inside(boundary, found)
        seen.extend(resolved)
        return found

    monkeypatch.setattr(scratch, "scratch_scan_roots", guarded_scan)
    monkeypatch.setattr(delegate, "scratch_scan_roots", guarded_scan)
    monkeypatch.setattr(isolation, "scratch_scan_roots", guarded_scan)

    review = isolation.sweep_review_temp_orphans(now=now)
    assert review["roots_reaped"] == 0
    assert review["errors"] == 0
    assert lease.is_dir()

    swept = delegate._sweep_runtime_tmp_orphans(now=now)
    assert swept["leases_reaped"] == 1
    assert swept["errors"] == 0
    assert not lease.exists()
    assert seen, "sweep did not scan"
    assert _resolved(root) in seen
    assert host_temp not in seen
    assert _resolved(_HOST_DEFAULT_SCRATCH_ROOT) not in seen
    assert all(path.is_relative_to(boundary) for path in seen)


def test_unset_scan_root_keeps_default_fallback_and_legacy_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without the scan override, resolution still unions the historical roots."""
    fake_default = tmp_path / "fake-default"
    fake_temp = tmp_path / "fake-temp"
    fake_default.mkdir()
    fake_temp.mkdir()
    fallback = fake_temp / scratch.FALLBACK_SCRATCH_DIRNAME
    fallback.mkdir()
    monkeypatch.delenv(scratch.SCRATCH_SCAN_ROOT_ENV_VAR, raising=False)
    monkeypatch.delenv(scratch.SCRATCH_ROOT_ENV_VAR, raising=False)
    monkeypatch.delenv("LU_RUNTIME_TMP_BASE_ROOT", raising=False)
    monkeypatch.setattr(scratch, "DEFAULT_SCRATCH_ROOT", fake_default)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(fake_temp))

    roots = {path.resolve() for path in scratch.scratch_scan_roots()}
    assert fake_default.resolve() in roots
    assert fallback.resolve() in roots
    assert fake_temp.resolve() in roots


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


_CALLER_MISCONFIGURATIONS = (
    scratch.SCAN_ROOT_REASON_RELATIVE,
    scratch.SCAN_ROOT_REASON_OUTSIDE,
    scratch.SCAN_ROOT_REASON_SYMLINK,
    scratch.SCAN_ROOT_REASON_NOT_A_DIRECTORY,
)


@pytest.fixture
def misconfigured_scan_root(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    _isolate_runtime_scratch_root: Path,
) -> Iterator[str]:
    """Point ``LU_SCRATCH_SCAN_ROOT`` at one misconfiguration and clean up after it.

    Depends on the autouse scratch fixture so this override runs after it.
    """
    reason = request.param
    leftovers: list[Path] = []
    variable = scratch.SCRATCH_SCAN_ROOT_ENV_VAR
    if reason == scratch.SCAN_ROOT_REASON_RELATIVE:
        monkeypatch.setenv(variable, "relative-scan-root")
    elif reason == scratch.SCAN_ROOT_REASON_NOT_A_DIRECTORY:
        monkeypatch.setenv(variable, str(tmp_path / "missing-scan-root"))
    elif reason == scratch.SCAN_ROOT_REASON_OUTSIDE:
        monkeypatch.setenv(variable, str(tmp_path / ".." / f"outside-{tmp_path.name}"))
    elif reason == scratch.SCAN_ROOT_REASON_SYMLINK:
        target = tmp_path.parent / f"symlink-target-{tmp_path.name}"
        target.mkdir()
        leftovers.append(target)
        link = tmp_path / "escaping-scan-link"
        link.symlink_to(target, target_is_directory=True)
        monkeypatch.setenv(variable, str(link))
    else:
        raise AssertionError(reason)
    try:
        yield reason
    finally:
        for path in leftovers:
            shutil.rmtree(path)


def _keep_misconfigured_scans_inside_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """If a bad setting falls open, the historical candidates are still this test's tmp dir."""
    private = tmp_path / "fake-default"
    private.mkdir()
    monkeypatch.setattr(scratch, "DEFAULT_SCRATCH_ROOT", private)
    monkeypatch.setattr(delegate, "DEFAULT_SCRATCH_ROOT", private)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))


def _assert_typed_scan_root_error(caught: pytest.ExceptionInfo[scratch.ScratchScanRootError], reason: str) -> None:
    """The caller boundary raised the documented error and no host path."""
    assert caught.value.reason == reason
    assert str(caught.value) == f"LU_SCRATCH_SCAN_ROOT is misconfigured: {reason}"
    assert "/" not in str(caught.value)
    assert caught.value.__cause__ is None
    assert not isinstance(caught.value, OSError)
    frames = traceback.extract_tb(caught.tb)
    assert frames[-1].name == "_scratch_scan_roots"


@pytest.mark.parametrize("misconfigured_scan_root", _CALLER_MISCONFIGURATIONS, indirect=True)
def test_runtime_tmp_sweep_refuses_a_misconfigured_scan_root(
    misconfigured_scan_root: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Dispatch orphan sweep fails closed before it can delete a lease."""
    _keep_misconfigured_scans_inside_tmp(monkeypatch, tmp_path)

    def refuse_delete(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("misconfigured scan root reached lease deletion")

    monkeypatch.setattr(delegate, "_remove_runtime_tmp_lease", refuse_delete)
    with pytest.raises(scratch.ScratchScanRootError) as caught:
        delegate._sweep_runtime_tmp_orphans()
    _assert_typed_scan_root_error(caught, misconfigured_scan_root)
    assert traceback.extract_tb(caught.tb)[-1].filename.endswith("delegate.py")


@pytest.mark.parametrize("misconfigured_scan_root", _CALLER_MISCONFIGURATIONS, indirect=True)
def test_runtime_tmp_reap_refuses_a_misconfigured_scan_root(
    misconfigured_scan_root: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Dispatch lease reap fails closed instead of recording a raw filesystem error."""
    _keep_misconfigured_scans_inside_tmp(monkeypatch, tmp_path)
    namespace = tmp_path / "learn-ukrainian"
    lease = namespace / "misconfigured-lease"
    lease.mkdir(parents=True)
    (lease / "payload").write_text("keep", encoding="utf-8")

    def refuse_delete(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("misconfigured scan root reached lease deletion")

    monkeypatch.setattr(delegate, "_remove_runtime_tmp_lease", refuse_delete)
    with pytest.raises(scratch.ScratchScanRootError) as caught:
        delegate._reap_runtime_tmp_lease(lease, namespace)
    _assert_typed_scan_root_error(caught, misconfigured_scan_root)
    assert traceback.extract_tb(caught.tb)[-1].filename.endswith("delegate.py")
    assert lease.is_dir()
    assert (lease / "payload").read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("misconfigured_scan_root", _CALLER_MISCONFIGURATIONS, indirect=True)
def test_review_sweep_refuses_a_misconfigured_scan_root(
    misconfigured_scan_root: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Review orphan sweep fails closed before it can delete a review root."""
    from scripts.review import isolation

    _keep_misconfigured_scans_inside_tmp(monkeypatch, tmp_path)
    review_root = tmp_path / "lu-review-snap-misconfigured"
    review_root.mkdir()
    (review_root / "payload").write_text("keep", encoding="utf-8")

    def refuse_delete(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("misconfigured scan root reached review-root deletion")

    monkeypatch.setattr(isolation, "_remove_review_temp_orphan", refuse_delete)
    with pytest.raises(scratch.ScratchScanRootError) as caught:
        isolation.sweep_review_temp_orphans()
    _assert_typed_scan_root_error(caught, misconfigured_scan_root)
    assert traceback.extract_tb(caught.tb)[-1].filename.endswith("isolation.py")
    assert review_root.is_dir()


def test_unset_or_blank_scan_root_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty ``LU_SCRATCH_SCAN_ROOT`` keeps the historical scan; it is not an error."""
    monkeypatch.delenv(scratch.SCRATCH_SCAN_ROOT_ENV_VAR, raising=False)
    assert scratch.resolve_confined_scan_root() is None

    monkeypatch.setenv(scratch.SCRATCH_SCAN_ROOT_ENV_VAR, "   ")
    assert scratch.resolve_confined_scan_root() is None


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
