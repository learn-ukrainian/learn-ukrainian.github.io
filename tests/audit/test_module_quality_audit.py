from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.audit.llm_qg_canaries import (
    evaluate_canaries,
    extract_issue_ids,
    list_canaries,
)
from scripts.audit.llm_qg_store import record_llm_qg
from scripts.audit.module_quality_audit import audit_modules, main, planned_modules


def _write_module(root: Path, level: str, slug: str, body: str) -> Path:
    module_dir = root / level / slug
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text(body, encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def _write_manifest(root: Path) -> None:
    (root / "plans").mkdir(parents=True)
    manifest = {
        "levels": {
            "a1": {"modules": ["01-intro"]},
            "b1": {"modules": ["27-bad-style", "28-not-built"]},
            "hist": {"modules": ["01-seminar"]},
        }
    }
    (root / "curriculum.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )


def _payload() -> dict:
    return {
        "aggregate": {
            "verdict": "PASS",
            "terminal_verdict": "PASS",
            "min_score": 8.5,
            "min_dim": "naturalness",
        },
        "findings": [],
    }


def test_planned_modules_use_manifest_order_and_profiles(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    modules = planned_modules(curriculum_root=tmp_path, level_ids=["a1", "b1", "hist"])

    assert [(item.num, item.level, item.slug, item.profile) for item in modules] == [
        (1, "a1", "intro", "a1"),
        (1, "b1", "bad-style", "b1_plus"),
        (2, "b1", "not-built", "b1_plus"),
        (1, "hist", "seminar", "seminar"),
    ]


def test_audit_modules_reports_surface_and_llm_qg_coverage(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    a1_dir = _write_module(
        tmp_path,
        "a1",
        "intro",
        "Read the short dialogue.\n\n**Я тут.** - I am here.\n",
    )
    b1_dir = _write_module(
        tmp_path,
        "b1",
        "bad-style",
        "This paragraph explains the whole grammar point in English before Ukrainian appears.\n",
    )
    qg_artifact = b1_dir / "llm_qg.json"
    qg_artifact.write_text(json.dumps(_payload()), encoding="utf-8")
    (b1_dir / "module.md").write_text(
        "This paragraph explains the whole grammar point in English before Ukrainian appears.\n\n"
        "**Я тут.**\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "llm_qg.db"
    record_llm_qg(
        level="a1",
        slug="intro",
        module_dir=a1_dir,
        payload=_payload(),
        gate_version="test.v1",
        prompt_hash="prompt-sha",
        reviewer_model="review-model",
        reviewer_family="reviewer-family",
        source="test",
        path=db_path,
    )

    report = audit_modules(
        curriculum_root=tmp_path,
        level_ids=["a1", "b1"],
        db_path=db_path,
        include_findings=False,
    )

    assert report["summary"]["planned_modules"] == 3
    assert report["summary"]["built_modules"] == 2
    assert report["summary"]["unbuilt_modules"] == 1
    assert report["summary"]["surface_fail_modules"] == 1
    assert report["summary"]["current_db_llm_qg_modules"] == 1
    assert report["summary"]["stale_llm_qg_modules"] == 1
    assert report["summary"]["modules_without_current_db_llm_qg"] == 1
    assert report["summary"]["modules_needing_llm_review"] == 1
    assert report["summary"]["modules_recommended_for_second_review"] == 1

    rows = {(row["level"], row["slug"]): row for row in report["modules"]}
    assert rows[("a1", "intro")]["llm_qg_status"] == "current_db"
    assert rows[("a1", "intro")]["llm_qg_gate_version"] == "test.v1"
    assert rows[("a1", "intro")]["llm_qg_prompt_hash"] == "prompt-sha"
    assert rows[("a1", "intro")]["llm_qg_reviewer_family"] == "reviewer-family"
    assert rows[("a1", "intro")]["llm_qg_reviewer_model"] == "review-model"
    assert rows[("b1", "bad-style")]["llm_qg_status"] == "stale_file"
    assert rows[("b1", "bad-style")]["surface_verdict"] == "FAIL"
    assert rows[("b1", "bad-style")]["second_review_reason"] == "surface_fail"
    assert rows[("b1", "not-built")]["llm_qg_status"] == "not_built"


def test_cli_json_output(tmp_path: Path, capsys) -> None:
    _write_manifest(tmp_path)
    _write_module(tmp_path, "a1", "intro", "**Я тут.**\n")

    code = main(
        [
            "--curriculum-root",
            str(tmp_path),
            "--level",
            "a1",
            "--llm-qg-db",
            str(tmp_path / "missing.db"),
            "--format",
            "json",
        ]
    )

    assert code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["summary"]["planned_modules"] == 1
    assert output["summary"]["missing_llm_qg_modules"] == 1


def test_cli_includes_canary_results_and_can_fail_on_canary_failure(
    tmp_path: Path,
    capsys,
) -> None:
    _write_manifest(tmp_path)
    _write_module(tmp_path, "b1", "bad-style", "**Я тут.**\n")
    canary_path = tmp_path / "canary.json"
    canary_path.write_text(
        json.dumps({"findings": [{"issue_id": "AI_LEAKAGE"}]}),
        encoding="utf-8",
    )

    code = main(
        [
            "--curriculum-root",
            str(tmp_path),
            "--level",
            "b1",
            "--format",
            "json",
            "--canary-result",
            f"b1={canary_path}",
            "--fail-on-canary-failure",
        ]
    )

    assert code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["canaries"]["b1"]["passed"] is False
    assert "AWKWARD_PASSIVE_RESULT_STATE" in output["canaries"]["b1"]["missing_issue_ids"]


def test_b1_canary_snippets_include_required_examples() -> None:
    b1_snippets = [item.snippet for item in list_canaries("b1")]

    assert any("застосунок має бути відкритий" in snippet for snippet in b1_snippets)
    assert any(
        "Застереження каже: будь обережний, щоб небажаний результат не стався."
        in snippet
        for snippet in b1_snippets
    )


def test_extract_issue_ids_reads_top_level_and_dimensional_findings() -> None:
    result = {
        "issue_ids": ["internal_leakage"],
        "flags": ["awkward passive result state"],
        "aggregate": {
            "findings": [{"type": "ai_leakage"}, {"issue_type": "path_leakage"}],
        },
        "dimensions": {
            "register": {
                "findings": [
                    {"kind": "seminar_register_pathos"},
                    {"type": "ENGLISH_LEAKAGE"},
                ],
                "flags_raised": ["unnatural anthropomorphism"],
            },
        },
        "other": "must be ignored",
    }

    assert set(extract_issue_ids(result)) == {
        "AI_LEAKAGE",
        "PATH_LEAKAGE",
        "SEMINAR_REGISTER_PATHOS",
        "ENGLISH_LEAKAGE",
        "INTERNAL_LEAKAGE",
        "AWKWARD_PASSIVE_RESULT_STATE",
        "UNNATURAL_ANTHROPOMORPHISM",
    }


def test_evaluator_fails_when_required_issue_ids_are_missing_for_level() -> None:
    result = {
        "findings": [
            {"issue_type": "AI_LEAKAGE"},
            {"issue_type": "PATH_LEAKAGE"},
            {"issue_type": "INTERNAL_LEAKAGE"},
            {"issue_type": "AWKWARD_PASSIVE_RESULT_STATE"},
        ],
    }

    report = evaluate_canaries(result, "b1")
    assert not report["passed"]
    assert report["level"] == "b1"
    assert "UNNATURAL_ANTHROPOMORPHISM" in report["missing_issue_ids"]
    assert "ENGLISH_LEAKAGE" in report["missing_issue_ids"]


def test_evaluator_can_score_one_named_canary() -> None:
    result = {
        "canary_id": "b1-passive-result-state",
        "findings": [{"issue_id": "AWKWARD_PASSIVE_RESULT_STATE"}],
    }

    report = evaluate_canaries(result, "b1")

    assert report["passed"]
    assert report["canary_ids"] == ("b1-passive-result-state",)
    assert report["missing_issue_ids"] == ()


def test_evaluator_marks_pass_when_all_required_issue_ids_present() -> None:
    level = "seminar"
    required = set()
    for canary in list_canaries(level):
        required.update(canary.required_issue_ids)

    result = {"findings": [{"type": issue_id} for issue_id in sorted(required)]}
    report = evaluate_canaries(result, level)

    assert report["passed"]
    assert report["missing_issue_ids"] == ()
    assert set(report["matched_canaries"]) == {
        canary.canary_id for canary in list_canaries(level)
    }


def test_evaluator_fails_when_allow_list_canary_is_false_positive() -> None:
    result = {
        "findings": [{"issue_id": "AI_LEAKAGE"}],
        "dimensions": {"tone": {"flags": ["ENGLISH_LEAKAGE"]}},
    }

    report = evaluate_canaries(result, "a1")

    assert not report["passed"]
    assert "ENGLISH_LEAKAGE" in report["forbidden_issue_ids"]
    assert "ENGLISH_LEAKAGE" in report["forbidden_issue_ids_found"]
    assert "a1-english-scaffold-allowed" in report["missed_canaries"]


@pytest.mark.parametrize("level", ["a1", "a2", "b1", "seminar", "any"])
def test_list_canaries_includes_global_and_level_specific_rules(level: str) -> None:
    ids = {canary.canary_id for canary in list_canaries(level)}

    assert "surface-ai-leakage" in ids
    assert "surface-path-leakage" in ids
    assert "surface-internal-leakage" in ids

    if level == "a1":
        assert "a1-english-scaffold-allowed" in ids
        return

    if level == "a2":
        assert "a2-english-gloss-allowed" in ids
        return

    if level == "b1":
        assert "b1-passive-result-state" in ids
        assert "b1-anthropomorphic-pathos" in ids
        assert "policy-b1-english-led" in ids
        return

    if level == "seminar":
        assert "policy-seminar-english-led" in ids
        assert "seminar-register-pathos" in ids
        return

    assert level == "any"
    required = set(
        issue
        for canary in list_canaries(level)
        for issue in canary.required_issue_ids
    )
    assert "AI_LEAKAGE" in required


def test_seminar_track_ids_use_seminar_canaries() -> None:
    ids = {canary.canary_id for canary in list_canaries("hist")}

    assert "policy-seminar-english-led" in ids
    assert "seminar-register-pathos" in ids
