"""Shared dispatcher fixtures."""

import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.dispatcher.worker_reap import Reaper

DOCTOR_NOT_FETCHED = "Managed settings (remote): not fetched — requires an Enterprise or Team subscription"


@pytest.fixture(scope="session", autouse=True)
def dispatcher_worker_reaper() -> Iterator[Reaper]:
    """Fail the session if a dispatcher test left a detached worker alive.

    Defect class: a test leaks a detached worker process. The failure names that
    test and the pid. Per-test teardown kills the worker's group; this check is
    what remains at session end.
    """
    reaper = Reaper.start()
    try:
        yield reaper
    finally:
        reaper.finish()


@pytest.fixture(autouse=True)
def end_detached_dispatcher_workers(request: pytest.FixtureRequest, tmp_path: Path, dispatcher_worker_reaper: Reaper):
    """End workers this test detached, including when pytest-timeout uses ``os._exit``.

    The reaper is armed before the test body. Fixture teardown kills the groups.
    ``os._exit`` skips that teardown; the reaper's parent-death pipe does not.
    """
    dispatcher_worker_reaper.activate(tmp_path, request.node.nodeid)
    try:
        yield
    finally:
        dispatcher_worker_reaper.reap(tmp_path)


@pytest.fixture(autouse=True)
def claude_doctor(tmp_path_factory, monkeypatch):
    """A read-only Claude dispatch asks ``claude doctor`` for server-managed settings; answer as a consumer login.

    CI has no Claude Code, and a developer host's own login must not decide a test. Tests that start a
    provider ``claude`` put their own stub first on ``PATH``.
    """
    return install_claude_doctor_stub(tmp_path_factory.mktemp("claude-doctor"), monkeypatch)


def install_claude_doctor_stub(bin_dir, monkeypatch):
    """Put a ``claude`` that answers only ``claude doctor``, as a consumer login, first on ``PATH``."""
    stub = bin_dir / "claude"
    stub.write_text(
        f"#!{sys.executable}\nimport sys\n"
        f"if sys.argv[1:] != ['doctor']:\n    sys.exit('claude doctor stub: ' + ' '.join(sys.argv[1:]))\n"
        f"print({DOCTOR_NOT_FETCHED!r})\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', os.defpath)}")
    return stub
