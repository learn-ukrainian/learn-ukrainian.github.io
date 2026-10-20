"""Give ordinary pytest runs invocation ownership for the scheduled sweep (#10831)."""

from __future__ import annotations

import os

import pytest

from scripts.common.scratch import ensure_scratch_root
from scripts.common.task_scratch import _verify_private_dir, allocate

NAMESPACE = "pytest-runs"


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Hold one invocation lock until teardown; explicit base temps retain their owner."""
    if hasattr(config, "workerinput") or config.option.basetemp is not None:
        return
    root = ensure_scratch_root() / NAMESPACE
    root.mkdir(mode=0o700, exist_ok=True)
    _verify_private_dir(root, what="pytest scratch root")
    # The pre-push gate also verifies ancestors of its test fixtures. Do not
    # let a collaborative umask create a group-writable pytest parent.
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fchmod(fd, 0o700)
    finally:
        os.close(fd)
    scratch = allocate("pytest", root=root)
    # Pytest recreates --basetemp. Keep ownership metadata outside that payload.
    config.option.basetemp = str(scratch.payload_dir / "base")
    config.add_cleanup(scratch.preserve)
