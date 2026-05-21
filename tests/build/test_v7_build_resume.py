"""Tests for the v7_build.py --resume flag and phase-skip helpers.

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

def test_llm_qg_skipped_when_aggregate_pass(module_dir: Path) -> None:
    _write_json(
        module_dir / "llm_qg.json",
        {"aggregate": {"verdict": "PASS", "min_score": 9.0}},
    )
    assert v7_build._phase_artifact_passes(module_dir, "llm_qg") is True


def test_llm_qg_reruns_when_aggregate_revise(module_dir: Path) -> None:
    _write_json(
        module_dir / "llm_qg.json",
        {"aggregate": {"verdict": "REVISE", "min_score": 6.0}},
    )
    assert v7_build._phase_artifact_passes(module_dir, "llm_qg") is False


def test_llm_qg_reruns_when_aggregate_missing(module_dir: Path) -> None:
    _write_json(module_dir / "llm_qg.json", {"placeholder": True})
    assert v7_build._phase_artifact_passes(module_dir, "llm_qg") is False


# ----- unknown phase ----------------------------------------------------------

def test_unknown_phase_returns_false(module_dir: Path) -> None:
    """Defensive default: never skip a phase we don't recognize."""
    assert v7_build._phase_artifact_passes(module_dir, "not_a_real_phase") is False


# ----- CLI flag wiring --------------------------------------------------------

def test_parse_args_accepts_resume() -> None:
    args = v7_build.parse_args(
        ["a1", "my-morning", "--resume", "/tmp/some/module/dir"]
    )
    assert args.resume == "/tmp/some/module/dir"


def test_parse_args_resume_defaults_to_none() -> None:
    args = v7_build.parse_args(["a1", "my-morning"])
    assert args.resume is None


def test_main_rejects_resume_with_worktree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--resume and --worktree are mutually exclusive — resume already targets
    an existing build dir, so creating a new worktree alongside it is a
    user error caught upfront with exit 2."""
    fake_module = tmp_path / "module"
    fake_module.mkdir()
    code = v7_build.main(
        ["a1", "my-morning", "--resume", str(fake_module), "--worktree"]
    )
    assert code == 2
    captured = capsys.readouterr()
    assert "mutually exclusive" in captured.err
