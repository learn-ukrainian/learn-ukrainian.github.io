"""The suite strips every live agent session identity variable (#8778).

``tests/conftest.py`` deletes ``SESSION_IDENTITY_ENV_VARS`` before each test's
fixtures set up. This module parses the sites that export identity into an
agent session and fails when one of them exports a name the tuple does not
cover.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ("pytester",)

# The export sites are repository trees (launchers, hooks, agent runtime) that
# this module globs rather than imports, so import selection cannot pick it (#8707).
pytestmark = pytest.mark.repo_wide

REPO_ROOT = Path(__file__).resolve().parents[1]


_NESTED_TEST = """
import os
import pytest

NAME = "LEARN_UKRAINIAN_SESSION_ID"
SEEN = {}


@pytest.fixture(scope="session", autouse=True)
def session_fixture():
    SEEN["session"] = os.environ.get(NAME)


@pytest.fixture(autouse=True)
def function_fixture(monkeypatch):
    SEEN["function"] = os.environ.get(NAME)
    yield
    SEEN["teardown"] = os.environ.get(NAME)


def test_identity_is_absent_from_every_fixture():
    SEEN["call"] = os.environ.get(NAME)
    os.environ[NAME] = "set-by-test"


def test_report():
    assert SEEN == {"session": None, "function": None, "call": None, "teardown": "set-by-test"}
"""


def test_isolation_runs_before_every_fixture_and_restores_after(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leaked identity is invisible to session and function fixtures (#8778)."""
    pytester.makeconftest(
        f"""
import importlib.util
spec = importlib.util.spec_from_file_location("project_tests_conftest", {str(REPO_ROOT / "tests" / "conftest.py")!r})
project_tests_conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project_tests_conftest)
pytest_runtest_protocol = project_tests_conftest.pytest_runtest_protocol


def pytest_sessionfinish(session):
    import os
    print("AFTER", os.environ.get("LEARN_UKRAINIAN_SESSION_ID"))
"""
    )
    pytester.makepyfile(_NESTED_TEST)
    monkeypatch.setenv("LEARN_UKRAINIAN_SESSION_ID", "live-operator-session")
    # A dispatch worker exports the repo's ci.* xdist cap plugin, which a
    # pytest rooted outside the repo cannot import.
    monkeypatch.delenv("PYTEST_PLUGINS", raising=False)

    result = pytester.runpytest_subprocess("-q", "-s")

    result.assert_outcomes(passed=2)
    # The test's own write is undone; the launching session's value returns.
    result.stdout.fnmatch_lines(["*AFTER live-operator-session"])
