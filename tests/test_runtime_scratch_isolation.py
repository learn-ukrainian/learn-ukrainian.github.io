"""Delegate runtime leases stay off the host scratch root (#9927)."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
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
    monkeypatch.setenv(scratch.SCRATCH_SCAN_ROOT_ENV_VAR, str(tmp_path / "missing-boundary"))
    with pytest.raises(OSError, match="LU_SCRATCH_SCAN_ROOT"):
        scratch.scratch_scan_roots()
