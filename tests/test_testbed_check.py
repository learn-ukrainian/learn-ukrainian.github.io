"""Testbed regression check — runs audit on baseline modules and detects regressions.

This test is marked 'slow' because it runs audit_module on 10+ modules.
CI can include it with: pytest -k testbed
"""
from __future__ import annotations

import json
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

    from run_testbed import audit_module, grade_module, load_baseline, load_config, GRADE_ORDER

    baseline = load_baseline()
    modules = load_config()
    regressions = []

    for mod in modules:
        r = audit_module(mod)
        r["grade"] = grade_module(r)
        key = f"{r['track']}-{r['slug']}"
        if key not in baseline:
            continue
        old_grade = baseline[key].get("grade", "?")
        new_grade = r.get("grade", "?")
        old_ord = GRADE_ORDER.get(old_grade, 9)
        new_ord = GRADE_ORDER.get(new_grade, 9)
        if new_ord > old_ord:
            regressions.append(f"{r['track']} M{r['num']} {r['slug']}: {old_grade} → {new_grade}")

    assert not regressions, f"Regressions detected:\n" + "\n".join(regressions)
