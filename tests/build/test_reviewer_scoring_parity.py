"""Replay recorded findings against #7810's frozen baseline and changed code.

Run with ``pytest tests/build/test_reviewer_scoring_parity.py -q -s`` for raw
before/after evidence. Requires the baseline Git object (CI fetches full history).
These are deterministic regression replays, not independent held-out evaluation.
"""

from __future__ import annotations

import ast
import contextlib
import copy
import json
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.audit import llm_reviewer, qg_workflow
from scripts.build import build_module_direct as direct
from scripts.build import linear_pipeline as linear
from tests.build.test_reviewer_schema_transport import direct_context, mechanical_payload

BASELINE = "e22ead90994d6d0a967a01f8468f8cfed0f2fa1a"
ROOT = Path(__file__).resolve().parents[2]


def baseline_module(path: str, monkeypatch: pytest.MonkeyPatch):
    source = subprocess.run(
        ["git", "show", f"{BASELINE}:{path}"], cwd=ROOT, check=True,
        capture_output=True, text=True, timeout=30,
    ).stdout
    name = "_qg7810_baseline_" + Path(path).stem
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / path)
    monkeypatch.setitem(sys.modules, name, module)
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def constant_assignments(path: str) -> dict:
    values = {}
    for node in ast.parse((ROOT / path).read_text()).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            with contextlib.suppress(ValueError):
                values[node.targets[0].id] = ast.literal_eval(node.value)
    return values


def test_recorded_dimension_scoring_before_after(monkeypatch):
    before = baseline_module("scripts/build/linear_pipeline.py", monkeypatch)
    tree = ast.parse((ROOT / "tests/build/test_llm_qg_evidence_quotes.py").read_text())
    test = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "test_evidence_quotes_array_satisfies_contract")
    assignment = next(node for node in test.body if isinstance(node, ast.Assign))
    recorded = ast.literal_eval(assignment.value)
    # The legacy record predates explicit empty transport fields. Extend both
    # sides identically; never change its recorded score, quotes or verdict.
    payload = {"findings": [], "flags": [], "issue_ids": [], "rubric_mapping": None, **recorded}
    old_entry = before.parse_review_response(json.dumps(payload), "pedagogical")
    new_entry = linear.parse_review_response(copy.deepcopy(payload), "pedagogical")
    assert old_entry == new_entry
    old_report = before._placeholder_review_report()
    old_report["pedagogical"] = old_entry
    new_report = linear._placeholder_review_report()
    new_report["pedagogical"] = new_entry
    old_result = before.aggregate_llm_review(old_report, "A1")
    new_result = linear.aggregate_llm_review(new_report, "A1")
    assert old_result == new_result
    for label, result in (("before", old_result), ("after", new_result)):
        print(json.dumps({
            "case": "recorded_build_11_dimension", "side": label, "baseline": BASELINE,
            "scores": {dim: entry["score"] for dim, entry in result["dimensions"].items()},
            "aggregate": result["aggregate"],
        }, sort_keys=True))
    print("ASSERT recorded dimension findings, evidence and scoring identical: PASS")


def test_recorded_audit_findings_scoring_before_after(monkeypatch):
    before = baseline_module("scripts/audit/llm_reviewer.py", monkeypatch)
    before_workflow = baseline_module("scripts/audit/qg_workflow.py", monkeypatch)
    fixtures = constant_assignments("tests/audit/test_llm_reviewer.py")
    raw = fixtures["B1_27_BAD_LLM_RESPONSE"]
    content = fixtures["B1_27_BAD_TEXT"]
    old_findings = before.parse_and_evaluate_llm_response(raw, content)
    new_findings = llm_reviewer.parse_and_evaluate_llm_response(raw, content)
    assert old_findings == new_findings
    old_verdict = before_workflow._verdict_for_findings(old_findings)
    new_verdict = qg_workflow._verdict_for_findings(new_findings)
    assert old_verdict == new_verdict
    for label, findings, verdict in (("before", old_findings, old_verdict), ("after", new_findings, new_verdict)):
        print(json.dumps({
            "case": "recorded_B1_27_findings", "side": label, "baseline": BASELINE,
            "findings": len(findings), "severity_counts": dict(Counter(f["severity"] for f in findings)),
            "verdict": verdict,
        }, sort_keys=True))
    print("ASSERT recorded audit findings and scoring identical: PASS")


def test_direct_mechanical_record_verdict_before_after(tmp_path, monkeypatch, capsys):
    """Direct has no numeric score; compare phase decisions on identical data."""
    from scripts.agent_runtime import runner

    before = baseline_module("scripts/build/build_module_direct.py", monkeypatch)
    payload = mechanical_payload("direct")
    raw = json.dumps(payload)
    baseline_dir, head_dir = tmp_path / "baseline", tmp_path / "head"
    baseline_dir.mkdir()
    head_dir.mkdir()
    old_ctx, new_ctx = direct_context(baseline_dir), direct_context(head_dir)
    monkeypatch.setattr(before, "PROJECT_ROOT", baseline_dir)
    monkeypatch.setattr(direct, "PROJECT_ROOT", head_dir)
    with monkeypatch.context() as context:
        context.setattr(before.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout=raw))
        old_passed = before.phase_review(old_ctx)
    monkeypatch.setattr(runner, "invoke", lambda *a, **kw: SimpleNamespace(ok=True, response=raw))
    new_passed = direct.phase_review(new_ctx)
    old_phase = old_ctx.status_data["phases"]["review"]
    new_phase = new_ctx.status_data["phases"]["review"]
    assert old_passed == new_passed
    assert old_phase["verdict"] == new_phase["verdict"]
    assert old_phase["issues"] == new_phase["issues"]
    capsys.readouterr()  # Print only counts/decisions, never raw content logs.
    for label, phase in (("before", old_phase), ("after", new_phase)):
        print(json.dumps({
            "case": "direct_synthetic_transport_record", "side": label, "baseline": BASELINE,
            "verdict": phase["verdict"], "issues": len(phase["issues"]),
        }, sort_keys=True))
    print("ASSERT identical direct record retains verdict and issues: PASS")
