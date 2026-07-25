"""Tests for v7_build.py resume-default phase-skip helpers.

Resume policy:
  - A phase is skipped iff its on-disk artifact exists AND reports the canonical
    success shape for that phase.
  - Any missing/failed artifact forces the phase to re-run.
  - Once one phase re-runs (`force_rerun` flips True), every downstream phase
    re-runs unconditionally — corrections can invalidate later verdicts.

These tests pin the predicates in `_phase_artifact_passes` because they're the
single source of truth that downstream resume logic depends on.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import pytest

from scripts.build import v7_build


@pytest.fixture()
def module_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


# ----- knowledge_packet -------------------------------------------------------

def test_knowledge_packet_skipped_when_both_artifacts_present(module_dir: Path) -> None:
    (module_dir / "knowledge_packet.md").write_text("kp", encoding="utf-8")
    (module_dir / "wiki_manifest.json").write_text("{}", encoding="utf-8")
    assert v7_build._phase_artifact_passes(module_dir, "knowledge_packet") is True


def test_knowledge_packet_reruns_when_manifest_missing(module_dir: Path) -> None:
    (module_dir / "knowledge_packet.md").write_text("kp", encoding="utf-8")
    assert v7_build._phase_artifact_passes(module_dir, "knowledge_packet") is False


def test_knowledge_packet_reruns_when_kp_missing(module_dir: Path) -> None:
    (module_dir / "wiki_manifest.json").write_text("{}", encoding="utf-8")
    assert v7_build._phase_artifact_passes(module_dir, "knowledge_packet") is False


# ----- writer -----------------------------------------------------------------

def test_writer_skipped_when_all_artifacts_present(module_dir: Path) -> None:
    for name in (
        "module.md",
        "activities.yaml",
        "vocabulary.yaml",
        "resources.yaml",
        "writer_output.raw.md",
        "implementation_map.json",
    ):
        (module_dir / name).write_text("x", encoding="utf-8")
    assert v7_build._phase_artifact_passes(module_dir, "writer") is True


def test_writer_reruns_when_any_artifact_missing(module_dir: Path) -> None:
    for name in ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml"):
        (module_dir / name).write_text("x", encoding="utf-8")
    # writer_output.raw.md missing
    assert v7_build._phase_artifact_passes(module_dir, "writer") is False


# ----- python_qg --------------------------------------------------------------

def test_python_qg_skipped_when_gates_passed(module_dir: Path) -> None:
    _write_json(
        module_dir / "python_qg.json",
        {"gates": {"passed": True, "checks": {}}},
    )
    assert v7_build._phase_artifact_passes(module_dir, "python_qg") is True


def test_python_qg_reruns_when_gates_failed(module_dir: Path) -> None:
    _write_json(
        module_dir / "python_qg.json",
        {"gates": {"passed": False}},
    )
    assert v7_build._phase_artifact_passes(module_dir, "python_qg") is False


def test_python_qg_reruns_when_artifact_missing(module_dir: Path) -> None:
    assert v7_build._phase_artifact_passes(module_dir, "python_qg") is False


def test_python_qg_reruns_when_artifact_malformed(module_dir: Path) -> None:
    (module_dir / "python_qg.json").write_text("not json {{", encoding="utf-8")
    assert v7_build._phase_artifact_passes(module_dir, "python_qg") is False


# ----- wiki_completeness_gate -------------------------------------------------

def test_wiki_completeness_gate_skipped_when_passed(module_dir: Path) -> None:
    _write_json(
        module_dir / "wiki_completeness_gate.json",
        {"verdict": "PASS", "checks": {}},
    )
    assert v7_build._phase_artifact_passes(module_dir, "wiki_completeness_gate") is True


def test_wiki_completeness_gate_reruns_when_failed(module_dir: Path) -> None:
    _write_json(
        module_dir / "wiki_completeness_gate.json",
        {"verdict": "FAIL", "checks": {}},
    )
    assert v7_build._phase_artifact_passes(module_dir, "wiki_completeness_gate") is False


# ----- wiki_coverage_gate -----------------------------------------------------

def test_wiki_coverage_gate_skipped_when_passed(module_dir: Path) -> None:
    _write_json(
        module_dir / "wiki_coverage_gate.json",
        {"passed": True, "coverage_pct": 1.0},
    )
    assert v7_build._phase_artifact_passes(module_dir, "wiki_coverage_gate") is True


def test_wiki_coverage_gate_reruns_when_passed_false(module_dir: Path) -> None:
    _write_json(
        module_dir / "wiki_coverage_gate.json",
        {"passed": False, "coverage_pct": 0.5},
    )
    assert v7_build._phase_artifact_passes(module_dir, "wiki_coverage_gate") is False


# ----- wiki_coverage_review ---------------------------------------------------

def test_wiki_coverage_review_skipped_when_overall_pass(module_dir: Path) -> None:
    _write_json(
        module_dir / "wiki_coverage_review.json",
        {"overall_verdict": "PASS", "verdicts": []},
    )
    assert v7_build._phase_artifact_passes(module_dir, "wiki_coverage_review") is True


def test_wiki_coverage_review_skipped_when_overall_pass_lowercase(
    module_dir: Path,
) -> None:
    """Verdict casing should normalize on read; pipeline canonical form is uppercase."""
    _write_json(
        module_dir / "wiki_coverage_review.json",
        {"overall_verdict": "pass", "verdicts": []},
    )
    assert v7_build._phase_artifact_passes(module_dir, "wiki_coverage_review") is True


def test_wiki_coverage_review_reruns_when_overall_fail(module_dir: Path) -> None:
    _write_json(
        module_dir / "wiki_coverage_review.json",
        {"overall_verdict": "FAIL", "verdicts": []},
    )
    assert v7_build._phase_artifact_passes(module_dir, "wiki_coverage_review") is False


# ----- llm_qg ------------------------------------------------------------------
#
# QUARANTINED — these three encode a contract that DIRECTLY CONTRADICTS
# tests/test_v7_build_reviewer_assert.py::test_llm_qg_phase_artifact_requires_current_db_record.
# Both cannot hold at once:
#
#   * here: a fresh on-disk llm_qg.json MAY stand in for a DB record, so a resumed
#     build in a freshly dispatched worktree (which has no gitignored llm_qg.db) does
#     not re-run paid LLM quality-gate calls;
#   * there: a fresh llm_qg.json must NOT count as a pass without a current DB record,
#     so a stale or hand-written file cannot make a build skip its LLM quality gate.
#
# They coexisted undetected because CI selected tests by changed files and never ran
# both. #5766 made the suite run unconditionally and the contradiction surfaced
# immediately. PR #5784 restored the fallback and satisfied these three while silently
# breaking the gate-integrity test; that production change has been reverted here,
# because weakening a quality gate is not a call to make in passing.
#
# Which contract wins is a DESIGN decision (gate integrity vs. resume cost) and is
# handed to the advisor seat — see the issue referenced in the marker below.
# strict=True on purpose: if someone makes these pass, this file FAILS until the
# contradiction is resolved deliberately rather than drifting back.

_LLM_QG_CONTRACT_CONFLICT = pytest.mark.xfail(
    strict=True,
    reason=(
        "contradicts test_llm_qg_phase_artifact_requires_current_db_record: a fresh "
        "llm_qg.json may not substitute for a current DB record. Design decision pending "
        "(gate integrity vs. resume cost) — see #5788."
    ),
)


@_LLM_QG_CONTRACT_CONFLICT
def test_llm_qg_skipped_when_terminal_verdict_pass(module_dir: Path) -> None:
    _write_json(
        module_dir / "llm_qg.json",
        {
            "aggregate": {
                "verdict": "REJECT",
                "terminal_verdict": "PASS",
                "min_score": 4.0,
            }
        },
    )
    assert v7_build._phase_artifact_passes(module_dir, "llm_qg") is True


def test_llm_qg_reruns_when_terminal_verdict_revise(module_dir: Path) -> None:
    _write_json(
        module_dir / "llm_qg.json",
        {
            "aggregate": {
                "verdict": "REVISE",
                "terminal_verdict": "REVISE",
                "min_score": 8.5,
            }
        },
    )
    assert v7_build._phase_artifact_passes(module_dir, "llm_qg") is False


@_LLM_QG_CONTRACT_CONFLICT
def test_llm_qg_skipped_for_legacy_aggregate_pass(module_dir: Path) -> None:
    _write_json(
        module_dir / "llm_qg.json",
        {"aggregate": {"verdict": "PASS", "min_score": 9.0}},
    )
    assert v7_build._phase_artifact_passes(module_dir, "llm_qg") is True


def test_llm_qg_reruns_when_aggregate_missing(module_dir: Path) -> None:
    _write_json(module_dir / "llm_qg.json", {"placeholder": True})
    assert v7_build._phase_artifact_passes(module_dir, "llm_qg") is False


@_LLM_QG_CONTRACT_CONFLICT
def test_llm_qg_skipped_when_db_empty_but_json_file_is_fresh(module_dir: Path) -> None:
    """A freshly dispatched worktree has no local llm_qg.db (gitignored).

    Resume must fall back to a module-local llm_qg.json when it is not older
    than the module's learner-facing content, mirroring
    scripts.api.state_compute.read_llm_qg (docs/runbooks/module-quality-gates.md
    Persistence).
    """
    (module_dir / "module.md").write_text("# Fixture\n", encoding="utf-8")
    time.sleep(0.01)
    _write_json(
        module_dir / "llm_qg.json",
        {"aggregate": {"verdict": "PASS", "terminal_verdict": "PASS", "min_score": 9.0}},
    )
    assert v7_build._phase_artifact_passes(module_dir, "llm_qg") is True


def test_llm_qg_reruns_when_json_file_is_stale_relative_to_content(module_dir: Path) -> None:
    """A pass artifact older than the current module content must not be trusted."""
    _write_json(
        module_dir / "llm_qg.json",
        {"aggregate": {"verdict": "PASS", "terminal_verdict": "PASS", "min_score": 9.0}},
    )
    stale_mtime = time.time() - 3600
    os.utime(module_dir / "llm_qg.json", (stale_mtime, stale_mtime))
    (module_dir / "module.md").write_text("# Fixture, revised\n", encoding="utf-8")
    assert v7_build._phase_artifact_passes(module_dir, "llm_qg") is False


# ----- unknown phase ----------------------------------------------------------

def test_unknown_phase_returns_false(module_dir: Path) -> None:
    """Defensive default: never skip a phase we don't recognize."""
    assert v7_build._phase_artifact_passes(module_dir, "not_a_real_phase") is False


# ----- CLI flag wiring --------------------------------------------------------

def test_parse_args_rejects_removed_resume_flag() -> None:
    with pytest.raises(SystemExit):
        v7_build.parse_args(["a1", "my-morning", "--resume", "/tmp/some/module/dir"])


def test_parse_args_resume_defaults_to_enabled() -> None:
    args = v7_build.parse_args(["a1", "my-morning"])
    assert args.no_resume is False


def test_parse_args_no_resume_disables_resume_default() -> None:
    args = v7_build.parse_args(["a1", "my-morning", "--no-resume"])
    assert args.no_resume is True
