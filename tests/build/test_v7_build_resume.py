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
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import llm_qg_store
from scripts.audit.llm_qg_store import CONTENT_FILES, DB_ENV_VAR, db_path, record_llm_qg
from scripts.build import linear_pipeline, v7_build


@pytest.fixture()
def module_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _qg_pass_payload() -> dict[str, Any]:
    return {
        "aggregate": {
            "verdict": "PASS",
            "terminal_verdict": "PASS",
            "min_score": 9.0,
            "min_dim": "naturalness",
        },
        "dimensions": {},
    }


def _write_module_content(module_dir: Path) -> None:
    module_dir.mkdir(parents=True, exist_ok=True)
    contents = {
        "module.md": "# Тестовий модуль\n\nТекст для перевірки.\n",
        "activities.yaml": "[]\n",
        "vocabulary.yaml": "[]\n",
        "resources.yaml": "[]\n",
    }
    for name, content in contents.items():
        (module_dir / name).write_text(content, encoding="utf-8")


def _write_resumable_artifacts(module_dir: Path) -> None:
    (module_dir / "knowledge_packet.md").write_text("knowledge packet\n", encoding="utf-8")
    _write_json(module_dir / "wiki_manifest.json", {})
    for artifact in linear_pipeline.WRITER_ARTIFACTS:
        path = module_dir / artifact
        if not path.exists():
            path.write_text(f"{artifact}\n", encoding="utf-8")
    (module_dir / "writer_output.raw.md").write_text("writer output\n", encoding="utf-8")
    _write_json(module_dir / "implementation_map.json", {"entries": []})
    _write_json(module_dir / "stress_annotation.json", {"passed": True})
    _write_json(module_dir / "ulp_fidelity_gate.json", {"passed": True})
    _write_json(module_dir / "python_qg.json", {"gates": {"passed": True}})
    _write_json(module_dir / "wiki_completeness_gate.json", {"verdict": "PASS"})
    _write_json(module_dir / "wiki_coverage_gate.json", {"passed": True})
    _write_json(module_dir / "wiki_coverage_review.json", {"overall_verdict": "PASS", "verdicts": []})


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True, timeout=30,
    )


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

def test_llm_qg_payload_terminal_verdict_pass_wins_over_warning_aggregate() -> None:
    """Payload shape is compatible; a DB record remains required to resume."""
    assert v7_build._llm_qg_payload_passes(
        {
            "aggregate": {
                "verdict": "REJECT",
                "terminal_verdict": "PASS",
                "min_score": 4.0,
            }
        }
    )


def test_llm_qg_payload_rejects_terminal_revise() -> None:
    assert not v7_build._llm_qg_payload_passes(
        {
            "aggregate": {
                "verdict": "REVISE",
                "terminal_verdict": "REVISE",
                "min_score": 8.5,
            }
        }
    )


def test_llm_qg_payload_supports_legacy_aggregate_pass() -> None:
    """Legacy payload compatibility does not change the DB authority rule."""
    assert v7_build._llm_qg_payload_passes({"aggregate": {"verdict": "PASS", "min_score": 9.0}})


def test_llm_qg_payload_rejects_missing_aggregate() -> None:
    assert not v7_build._llm_qg_payload_passes({"placeholder": True})


@pytest.mark.parametrize("changed_name", CONTENT_FILES)
def test_llm_qg_authority_rejects_each_changed_content_file(
    tmp_path: Path,
    changed_name: str,
) -> None:
    module = tmp_path / "b1" / "target"
    _write_module_content(module)
    expected_prompt_hash = "expected-prompt-hash"
    record_llm_qg(
        level="b1",
        slug="target",
        module_dir=module,
        payload=_qg_pass_payload(),
        gate_version=v7_build.LLM_QG_GATE_VERSION,
        prompt_hash=expected_prompt_hash,
    )

    assert v7_build._phase_artifact_passes(
        module,
        "llm_qg",
        expected_llm_qg_prompt_hash=expected_prompt_hash,
    )
    (module / changed_name).write_text("changed\n", encoding="utf-8")
    assert not v7_build._phase_artifact_passes(
        module,
        "llm_qg",
        expected_llm_qg_prompt_hash=expected_prompt_hash,
    )


def test_llm_qg_authority_rejects_wrong_gate_or_prompt_hash(tmp_path: Path) -> None:
    module = tmp_path / "b1" / "target"
    _write_module_content(module)
    record_llm_qg(
        level="b1",
        slug="target",
        module_dir=module,
        payload=_qg_pass_payload(),
        gate_version="v7.llm_qg.old",
        prompt_hash="expected-prompt-hash",
    )
    assert not v7_build._phase_artifact_passes(
        module,
        "llm_qg",
        expected_llm_qg_prompt_hash="expected-prompt-hash",
    )

    record_llm_qg(
        level="b1",
        slug="target",
        module_dir=module,
        payload=_qg_pass_payload(),
        gate_version=v7_build.LLM_QG_GATE_VERSION,
        prompt_hash="wrong-prompt-hash",
    )
    assert not v7_build._phase_artifact_passes(
        module,
        "llm_qg",
        expected_llm_qg_prompt_hash="expected-prompt-hash",
    )


def test_llm_qg_authority_fails_closed_without_expected_prompt_hash(tmp_path: Path) -> None:
    module = tmp_path / "b1" / "target"
    _write_module_content(module)
    record_llm_qg(
        level="b1",
        slug="target",
        module_dir=module,
        payload=_qg_pass_payload(),
        gate_version=v7_build.LLM_QG_GATE_VERSION,
        prompt_hash="expected-prompt-hash",
    )

    assert not v7_build._phase_artifact_passes(module, "llm_qg")

def test_llm_qg_resumes_from_shared_store_in_linked_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init")
    _git(primary, "config", "user.email", "test@example.invalid")
    _git(primary, "config", "user.name", "LLM QG test")
    (primary / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(primary, "add", "README.md")
    _git(primary, "commit", "-m", "fixture")
    linked = tmp_path / "linked"
    _git(primary, "worktree", "add", "--detach", str(linked), "HEAD")

    monkeypatch.delenv(DB_ENV_VAR)
    monkeypatch.setattr(llm_qg_store, "LIVE_REPO_ROOT", primary)
    shared_db = db_path()
    monkeypatch.setattr(llm_qg_store, "LIVE_REPO_ROOT", linked)
    assert db_path() == shared_db
    assert shared_db == primary / "data" / "telemetry" / "llm_qg.db"

    plan = {"level": "b1", "slug": "target", "sequence": 1}
    plan_content = "level: b1\nslug: target\n"
    module_a = primary / "curriculum" / "l2-uk-en" / "b1" / "target"
    module_b = linked / "curriculum" / "l2-uk-en" / "b1" / "target"
    _write_module_content(module_a)
    _write_module_content(module_b)
    _write_resumable_artifacts(module_a)
    _write_resumable_artifacts(module_b)
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "render_review_prompt",
        lambda *_args, **_kwargs: f"prompt::{_args[3]}",
    )
    monkeypatch.setattr(v7_build, "read_implementation_map", lambda _path: {"entries": []})
    expected_prompt_hash = v7_build._expected_llm_qg_prompt_hash(
        plan=plan,
        plan_content=plan_content,
        module_dir=module_a,
        wiki_manifest={},
        implementation_map={"entries": []},
        use_generator=False,
        obligation_checklist=None,
    )
    assert expected_prompt_hash is not None
    record_llm_qg(
        level="b1",
        slug="target",
        module_dir=module_a,
        payload=_qg_pass_payload(),
        gate_version=v7_build.LLM_QG_GATE_VERSION,
        prompt_hash=expected_prompt_hash,
    )

    assert shared_db.exists()
    assert not (linked / "data" / "telemetry" / "llm_qg.db").exists()
    assert not (module_b / "llm_qg.json").exists()
    assert v7_build._phase_artifact_passes(
        module_b,
        "llm_qg",
        expected_llm_qg_prompt_hash=expected_prompt_hash,
    )

    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(plan_content, encoding="utf-8")
    monkeypatch.setattr(v7_build.linear_pipeline, "plan_path_for", lambda *_args: plan_path)
    monkeypatch.setattr(v7_build.linear_pipeline, "load_plan", lambda _path: plan)
    monkeypatch.setattr(v7_build.linear_pipeline, "validate_plan", lambda _plan: None)
    monkeypatch.setattr(v7_build.linear_pipeline, "curriculum_profile_for_level", lambda _level: "core")
    monkeypatch.setattr(v7_build.linear_pipeline, "assemble_mdx", lambda *_args: None)

    def paid_reviewer_must_not_run(**_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("paid LLM-QG reviewer ran despite a shared current record")

    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "run_llm_qg_with_corrections",
        paid_reviewer_must_not_run,
    )
    args = v7_build.parse_args(["b1", "target", "--out", str(module_b)])
    assert v7_build._run(args) == 0
    assert not (module_b / "llm_qg.json").exists()

    explicit_db = tmp_path / "explicit" / "llm_qg.db"
    monkeypatch.setenv(DB_ENV_VAR, str(explicit_db))
    assert db_path() == explicit_db
    assert not v7_build._phase_artifact_passes(
        module_b,
        "llm_qg",
        expected_llm_qg_prompt_hash=expected_prompt_hash,
    )
    record_llm_qg(
        level="b1",
        slug="target",
        module_dir=module_b,
        payload=_qg_pass_payload(),
        gate_version=v7_build.LLM_QG_GATE_VERSION,
        prompt_hash=expected_prompt_hash,
    )
    assert v7_build._phase_artifact_passes(
        module_b,
        "llm_qg",
        expected_llm_qg_prompt_hash=expected_prompt_hash,
    )


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
