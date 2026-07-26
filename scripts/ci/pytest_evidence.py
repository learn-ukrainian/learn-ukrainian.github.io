"""Pytest plugin that executes an exact CI plan and records executed node IDs."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def _is_wiki_node(nodeid: str) -> bool:
    """Return whether a test can invoke the sources-MCP dense reranker."""
    test_file = nodeid.split("::", 1)[0]
    filename = Path(test_file).name
    return test_file.startswith("tests/wiki/") or filename.startswith("test_wiki")


class EvidencePlugin:
    """Keep every shard honest about the test nodes it ran."""

    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.plan_path = Path(os.environ["CI_PYTEST_PLAN_FILE"])
        self.executed_path = Path(os.environ["CI_PYTEST_EXECUTED_FILE"])
        self.current_path = Path(os.environ["CI_PYTEST_CURRENT_FILE"])
        self.expected = {
            nodeid for nodeid in self.plan_path.read_text(encoding="utf-8").splitlines() if nodeid
        }
        if not self.expected:
            raise pytest.UsageError(f"CI pytest plan is empty: {self.plan_path}")
        self.executed: set[str] = set()
        self.wiki_no_mlx = os.environ.get("CI_PYTEST_WIKI_NO_MLX") == "1"
        self.original_no_mlx = os.environ.get("SOURCES_MCP_NO_MLX")

    def pytest_collection_modifyitems(self, config: pytest.Config, items: list[pytest.Item]) -> None:
        available = {item.nodeid for item in items}
        missing = sorted(self.expected - available)
        if missing:
            raise pytest.UsageError(f"CI pytest plan references uncollected node IDs: {missing[:10]}")
        selected = [item for item in items if item.nodeid in self.expected]
        deselected = [item for item in items if item.nodeid not in self.expected]
        items[:] = selected
        config.hook.pytest_deselected(items=deselected)

    def pytest_runtest_setup(self, item: pytest.Item) -> None:
        """Avoid the MLX worker only where a wiki test can use it.

        `tests/test_mlx_bridge_gate.py` is itself a contract for the explicit
        force-MLX override, so setting the kill switch at workflow scope makes
        that ordinary unit test fail for the wrong reason.  Scope the safe
        fallback to wiki nodes instead, and restore the caller's environment
        after the session.
        """
        if not self.wiki_no_mlx:
            return
        if _is_wiki_node(item.nodeid):
            os.environ["SOURCES_MCP_NO_MLX"] = "1"
        elif self.original_no_mlx is None:
            os.environ.pop("SOURCES_MCP_NO_MLX", None)
        else:
            os.environ["SOURCES_MCP_NO_MLX"] = self.original_no_mlx

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        # Setup reports exist for passed, failed, and explicitly skipped tests.
        # A node missing here means pytest never reached its execution protocol.
        if report.when == "setup":
            self.executed.add(report.nodeid)

    def pytest_runtest_logstart(self, nodeid: str, location: tuple[str, int, str]) -> None:
        """Persist the last node the controller dispatched before a worker can die.

        xdist can lose its only worker after it has received a node but before
        the worker emits a setup report.  The outer shard wrapper must still
        name that node in its timeout evidence rather than report an anonymous
        worker crash.
        """
        del location
        self.current_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.current_path.with_name(f".{self.current_path.name}.tmp")
        temporary.write_text(f"{nodeid}\n", encoding="utf-8")
        temporary.replace(self.current_path)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        # xdist workers inherit this plugin.  The controller receives their reports
        # and is the one authoritative writer, avoiding cross-process file races.
        if hasattr(self.config, "workerinput"):
            return
        self.executed_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.executed_path.with_name(f".{self.executed_path.name}.tmp")
        temporary.write_text("".join(f"{nodeid}\n" for nodeid in sorted(self.executed)), encoding="utf-8")
        temporary.replace(self.executed_path)
        if self.original_no_mlx is None:
            os.environ.pop("SOURCES_MCP_NO_MLX", None)
        else:
            os.environ["SOURCES_MCP_NO_MLX"] = self.original_no_mlx


def pytest_configure(config: pytest.Config) -> None:
    if os.environ.get("CI_PYTEST_PLAN_FILE"):
        config.pluginmanager.register(EvidencePlugin(config), "ci-pytest-evidence")
