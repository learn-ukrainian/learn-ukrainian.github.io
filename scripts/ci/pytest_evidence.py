"""Pytest plugin that executes an exact CI plan and records executed node IDs."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


class EvidencePlugin:
    """Keep every shard honest about the test nodes it ran."""

    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.plan_path = Path(os.environ["CI_PYTEST_PLAN_FILE"])
        self.executed_path = Path(os.environ["CI_PYTEST_EXECUTED_FILE"])
        self.expected = {
            nodeid for nodeid in self.plan_path.read_text(encoding="utf-8").splitlines() if nodeid
        }
        if not self.expected:
            raise pytest.UsageError(f"CI pytest plan is empty: {self.plan_path}")
        self.executed: set[str] = set()

    def pytest_collection_modifyitems(self, config: pytest.Config, items: list[pytest.Item]) -> None:
        available = {item.nodeid for item in items}
        missing = sorted(self.expected - available)
        if missing:
            raise pytest.UsageError(f"CI pytest plan references uncollected node IDs: {missing[:10]}")
        selected = [item for item in items if item.nodeid in self.expected]
        deselected = [item for item in items if item.nodeid not in self.expected]
        items[:] = selected
        config.hook.pytest_deselected(items=deselected)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        # Setup reports exist for passed, failed, and explicitly skipped tests.
        # A node missing here means pytest never reached its execution protocol.
        if report.when == "setup":
            self.executed.add(report.nodeid)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        # xdist workers inherit this plugin.  The controller receives their reports
        # and is the one authoritative writer, avoiding cross-process file races.
        if hasattr(self.config, "workerinput"):
            return
        self.executed_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.executed_path.with_name(f".{self.executed_path.name}.tmp")
        temporary.write_text("".join(f"{nodeid}\n" for nodeid in sorted(self.executed)), encoding="utf-8")
        temporary.replace(self.executed_path)


def pytest_configure(config: pytest.Config) -> None:
    if os.environ.get("CI_PYTEST_PLAN_FILE"):
        config.pluginmanager.register(EvidencePlugin(config), "ci-pytest-evidence")
