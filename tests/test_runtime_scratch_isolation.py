"""Delegate runtime leases stay off the host scratch root (#9927)."""

from __future__ import annotations

import os
import tempfile
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
