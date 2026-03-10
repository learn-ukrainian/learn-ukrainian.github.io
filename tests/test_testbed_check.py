"""Testbed regression check — runs audit on baseline modules and detects regressions.

This test is marked 'slow' because it runs audit_module on 10+ modules.
CI can include it with: pytest -k testbed
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTBED_DIR = Path(__file__).resolve().parent / "testbed"
ROOT_DIR = TESTBED_DIR.parent.parent
BASELINE_JSON = TESTBED_DIR / "core" / "baseline.json"

sys.path.insert(0, str(TESTBED_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))


@pytest.mark.slow
def test_no_regressions_vs_baseline():
    """Audit testbed modules and assert no grade regressions vs baseline."""
    if not BASELINE_JSON.exists():
        pytest.skip("No baseline.json — run 'run_testbed.py baseline' first")

    from run_testbed import audit_module, grade_module, load_baseline, load_config, find_regressions

    baseline = load_baseline()
    modules = load_config()
    results = []

    for mod in modules:
        r = audit_module(mod)
        r["grade"] = grade_module(r)
        results.append(r)

    regressions = find_regressions(results, baseline)
    assert not regressions, f"Regressions detected:\n" + "\n".join(regressions)
