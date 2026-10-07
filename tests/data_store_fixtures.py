"""Fixture-time real-store inputs and visible not-run reporting (#9981).

Request ``data_store_factory(store, required_sqlite_tables=...)`` for a validated
read-only path, or declare ``data_tier(store, tables=(...))`` on a test. Injected
``StoreBinding`` values are for synthetic contract tests only. Ordinary readers
use the resolver's environment/primary binding, without a test-root fallback.
"""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import sys
from collections.abc import Callable, Collection
from pathlib import Path

import pytest

from scripts.lib.readonly_sqlite import open_readonly
from scripts.storage import topology

_NOT_RUN = "data_store.not_run"
_RECORDS = pytest.StashKey[dict[str, set[tuple[str, str]]]]()
StoreFactory = Callable[..., Path]


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--require-data",
        action="store_true",
        default=False,
        help="Fail real-store tests on unavailable sources/vesum inputs (default: report and skip).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.stash[_RECORDS] = {}
    config.pluginmanager.register(DataStoreReporter(config), "data-store-reporter")
    config.addinivalue_line("markers", "data_tier(*stores, tables=()): requires fixture-time read-only logical stores")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        stores = [name.removeprefix("requires_").removesuffix("_db") for name in item.fixturenames
                  if name in {"requires_sources_db", "requires_vesum_db"}]
        if stores or "data_store_factory" in item.fixturenames:
            item.add_marker(pytest.mark.data_tier(*stores, fixture_inputs=True))


@pytest.fixture
def data_store_factory(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> StoreFactory:
    """Resolve, validate and bind each input at fixture time; never create a DB."""
    def require(
        store: topology.StoreId,
        *,
        required_sqlite_tables: Collection[str] = (),
        binding: topology.StoreBinding | None = None,
    ) -> Path:
        request.node.add_marker(pytest.mark.data_tier(store))
        result = topology.resolve_store(store, binding=binding)
        if isinstance(result, topology.StoreBinding):
            try:
                with contextlib.closing(open_readonly(result.path)) as connection:
                    tables = {row[0] for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
                    )}
                missing = sorted(set(required_sqlite_tables) - tables)
                if missing:
                    result = topology.StoreRefusal(store, "sqlite_tables_missing:" + ",".join(missing))
            except sqlite3.Error:
                result = topology.StoreRefusal(store, "sqlite_unreadable")
        if isinstance(result, topology.StoreRefusal):
            record = json.dumps({"store": result.store, "reason": result.reason}, sort_keys=True)
            request.node.user_properties.append((_NOT_RUN, record))
            message = f"data store unavailable: store={result.store} reason={result.reason}"
            if request.config.getoption("require_data"):
                pytest.fail(message, pytrace=False)
            pytest.skip(message)
        # Readers and their subprocesses share the validated binding. Legacy
        # VESUM imports still capture their default before fixtures execute.
        if binding is None:
            monkeypatch.setenv(f"LU_{store.upper()}_DB", str(result.path))
            if store == "vesum":
                for name in ("scripts.rag.config", "rag.config", "scripts.verification.vesum",
                             "verification.vesum", "scripts.build.phases.vocab_coverage", "build.phases.vocab_coverage"):
                    module = sys.modules.get(name)
                    if module is not None and hasattr(module, "VESUM_DB_PATH"):
                        monkeypatch.setattr(module, "VESUM_DB_PATH", result.path)
        return result.path

    return require


@pytest.fixture(autouse=True)
def _declared_data_stores(request: pytest.FixtureRequest) -> None:
    """Marker inputs are requested after the needs_artifact setup gate."""
    for marker in tuple(request.node.iter_markers("data_tier")):
        if marker.kwargs.get("fixture_inputs"):
            continue
        for store in marker.args:
            request.getfixturevalue("data_store_factory")(
                store, required_sqlite_tables=marker.kwargs.get("tables", ())
            )


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> pytest.TestReport:
    report = yield
    if report.skipped and item.get_closest_marker("data_tier") and not any(
        name == _NOT_RUN for name, _ in report.user_properties
    ):
        # Earlier artifact/sparse skips also stay visible, while their original
        # skip message (especially needs_artifact:) remains untouched for CI.
        stores = {store for marker in item.iter_markers("data_tier") for store in marker.args} or {"unspecified"}
        reason = "needs_artifact" if "needs_artifact:" in str(report.longrepr) else "test_skipped"
        for store in sorted(stores):
            report.user_properties.append((_NOT_RUN, json.dumps({"store": store, "reason": reason})))
    return report


class DataStoreReporter:
    def __init__(self, config: pytest.Config) -> None:
        self.config = config

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if not (report.skipped or report.failed):
            return
        for name, value in report.user_properties:
            if name == _NOT_RUN:
                record = json.loads(value)
                self.config.stash[_RECORDS].setdefault(report.nodeid, set()).add((record["store"], record["reason"]))

    def pytest_terminal_summary(self, terminalreporter: pytest.TerminalReporter) -> None:
        records = self.config.stash[_RECORDS]
        if not records:
            return
        terminalreporter.write_sep("=", "data tests not run")
        lines = ["### data tests not run", ""]
        for nodeid, reasons in sorted(records.items()):
            detail = "; ".join(f"store={store} reason={reason}" for store, reason in sorted(reasons))
            terminalreporter.write_line(f"{nodeid}: {detail}")
            lines.append(f"- `{nodeid}`: {detail}")
        if summary_path := os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(summary_path, "a", encoding="utf-8") as output:
                output.write("\n".join([*lines, "", ""]))
