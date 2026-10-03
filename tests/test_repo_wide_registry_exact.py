"""Exact ``repo_wide`` registry completeness, in the nightly ``slow`` lane (#9434).

The registry and its fast checks live in ``tests/test_repo_wide_marker_invariant.py``,
which is marked ``repo_wide`` at module scope so a worker runs it before pushing
(``pytest -m repo_wide``). This check collects the whole suite, so it lives here,
without that mark, and the worker's pre-push selection never runs it;
``test_exact_check_is_outside_the_repo_wide_selection`` there proves it.
"""

from __future__ import annotations

import pytest

from tests.test_repo_wide_marker_invariant import (
    _EXACT_COLLECT_TIMEOUT_S,
    _REPO_ROOT,
    KNOWN_REPO_WIDE_FUNCTIONS,
    KNOWN_REPO_WIDE_MODULES,
    _ci_test_files,
    _collect_repo_wide_marks,
    _drift_report,
    _registry_drift,
)


@pytest.mark.slow
@pytest.mark.timeout(_EXACT_COLLECT_TIMEOUT_S + 60)
def test_registry_matches_every_collected_repo_wide_mark() -> None:
    """Collect every CI test file, no prefilter, and compare the registry with the marks both ways.

    The PR-tier checks collect a prefiltered subset; this one does not depend on
    how a mark is spelled or where the code applying it lives.
    """
    marked = _collect_repo_wide_marks(_REPO_ROOT, _ci_test_files(), timeout=_EXACT_COLLECT_TIMEOUT_S)
    unregistered, stale = _registry_drift(marked, KNOWN_REPO_WIDE_MODULES, KNOWN_REPO_WIDE_FUNCTIONS)
    assert not unregistered and not stale, _drift_report(unregistered, stale)
