"""Give ordinary pytest runs invocation ownership for the scheduled sweep (#10831)."""

from __future__ import annotations

import os
import tempfile

import pytest

from scripts.common.scratch import ensure_scratch_root
from scripts.common.task_scratch import _verify_private_dir, allocate

NAMESPACE = "pytest-runs"
RUNS_DIRNAME = "runs"


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
    scratch = allocate("pytest", root=root, namespace_dirname=RUNS_DIRNAME)
    # Pytest recreates --basetemp. Keep ownership metadata outside that payload.
    config.option.basetemp = str(scratch.payload_dir / "base")
    config.add_cleanup(scratch.preserve)
    # Fixtures and ordinary tempfile users must share a containment root.
    # Workers inherit TMPDIR; this process may already have cached tempdir.
    previous_env = os.environ.get("TMPDIR")
    previous_tempdir = tempfile.tempdir
    os.environ["TMPDIR"] = str(scratch.payload_dir)
    tempfile.tempdir = str(scratch.payload_dir)

    def restore_tempdir() -> None:
        tempfile.tempdir = previous_tempdir
        if previous_env is None:
            os.environ.pop("TMPDIR", None)
        else:
            os.environ["TMPDIR"] = previous_env

    config.add_cleanup(restore_tempdir)
