"""Cross-track shadow qualification and live-authorization safety tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import curriculum_lifecycle_pilot as pilot

REPO_ROOT = Path(__file__).resolve().parents[2]


def _report() -> dict[str, Any]:
    return pilot.build_shadow_report(repo_root=REPO_ROOT)


def test_matrix_is_complete_strict_and_shadow_only() -> None:
    matrix = pilot.load_matrix(repo_root=REPO_ROOT)

    assert matrix["mode"] == "shadow"
    assert len(matrix["rows"]) == 22
    assert {row["scenario"] for row in matrix["rows"]} == pilot.REQUIRED_SCENARIOS
    assert [(row["wave"]["position"], row["selector"]) for row in matrix["rows"] if row.get("wave")] == [
        (1, "folk/narodna-kultura-yak-systema"),
        (2, "folk/kalendarna-obriadovist-zvychai"),
        (3, "folk/koliadky-shchedrivky"),
    ]
    assert not any(pilot._is_generated_artifact_path(Path(path)) for path in matrix["identity_paths"])

    invalid = dict(matrix)
    invalid["live"] = True
    with pytest.raises(pilot.PilotError, match="Additional properties"):
        pilot._validate(invalid, REPO_ROOT / pilot.MATRIX_SCHEMA_PATH, "fixture")


def test_shadow_report_passes_all_rows_without_learner_mutation_or_model_cost() -> None:
    report = _report()

    assert report["verdict"] == "PASS"
    assert report["learner_tree"]["unchanged"] is True
    assert report["learner_tree"]["before_sha256"] == report["learner_tree"]["after_sha256"]
    assert report["metrics"] == {
        **report["metrics"],
        "row_count": 22,
        "model_calls": 0,
        "provider_cost_usd": 0,
        "external_cache_used": False,
        "false_positive_failures": 0,
        "evidence_freshness": "current",
    }
    assert report["metrics"]["resolver_requests"] == 2 * report["metrics"]["resolver_exact_replays"]
    assert all(row["passed"] and not row["mutation_detected"] for row in report["rows"])
    assert report["live_authorization"] == {
        "eligible": False,
        "reason": "separate-exact-report-review-and-human-authorization-required",
        "production_qg_armed": False,
    }


def test_shadow_report_is_exactly_reproducible_at_one_source_tree() -> None:
    assert _report() == _report()


def test_built_level_profiles_do_not_leak_cross_level_policy() -> None:
    rows = {row["id"]: row for row in _report()["rows"]}

    assert rows["a1-built-shadow"]["prompt"]["policy_checks_passed"] is True
    assert rows["a2-built-shadow"]["prompt"]["policy_checks_passed"] is True
    assert rows["b1-built-shadow"]["prompt"]["policy_checks_passed"] is True
    assert rows["b2-built-shadow"]["prompt"]["policy_checks_passed"] is True
    assert (
        len(
            {
                rows[row_id]["prompt"]["prompt_sha256"]
                for row_id in (
                    "a1-built-shadow",
                    "a2-built-shadow",
                    "b1-built-shadow",
                    "b2-built-shadow",
                )
            }
        )
        == 4
    )


def test_bio_pilot_binds_current_canonical_pass_and_bio_specific_prompt() -> None:
    row = next(row for row in _report()["rows"] if row["id"] == "bio-built-shadow")

    assert row["passed"] is True
    assert row["entry"]["state"] == "built-preparation-drift"
    assert row["disposition"] == "preparation-repair-required"
    assert row["prompt"]["profile"] == "seminar-bio"


def test_fixture_rows_prove_owned_pause_resume_and_qg_modes() -> None:
    rows = {row["scenario"]: row for row in _report()["rows"] if row["kind"] == "fixture"}

    assert rows["partial-ambiguous"]["disposition"] == "paused-built-artifact-owner"
    assert rows["reviewer-instability"]["disposition"] == "paused-audit-tooling-owner"
    assert rows["crash-resume"]["disposition"] == "resumed-idempotently"
    assert rows["quota-pause"]["disposition"] == "paused-without-mutation"
    assert rows["production-qg-pending"]["entry"]["state"] == "pbr-pass-qg-pending"
    assert rows["production-qg-disarmed"]["entry"]["state"] == "certified-final"


def test_shadow_detects_any_learner_tree_change(monkeypatch: pytest.MonkeyPatch) -> None:
    real_hashes = pilot._learner_hashes
    calls = 0

    def changed(matrix: dict[str, Any], repo_root: Path) -> dict[str, str]:
        nonlocal calls
        calls += 1
        value = real_hashes(matrix, repo_root)
        if calls == 2:
            value = {**value, "curriculum/l2-uk-en/a1/fake": "f" * 64}
        return value

    monkeypatch.setattr(pilot, "_learner_hashes", changed)

    report = pilot.build_shadow_report(repo_root=REPO_ROOT)

    assert report["verdict"] == "HOLD"
    assert report["learner_tree"]["unchanged"] is False
    assert all(row["mutation_detected"] and not row["passed"] for row in report["rows"])


def test_report_tampering_and_false_pass_fail_closed() -> None:
    matrix = pilot.load_matrix(repo_root=REPO_ROOT)
    report = _report()
    report["rows"][0]["passed"] = False

    with pytest.raises(pilot.PilotError, match="identity does not match"):
        pilot.validate_report_value(report, matrix=matrix, repo_root=REPO_ROOT)

    report["identity_sha256"] = pilot._report_identity(report)
    with pytest.raises(pilot.PilotError, match="row evidence does not match"):
        pilot.validate_report_value(report, matrix=matrix, repo_root=REPO_ROOT)

    report = _report()
    report["metrics"]["prompt_bytes"] += 1
    report["identity_sha256"] = pilot._report_identity(report)
    with pytest.raises(pilot.PilotError, match="metrics do not match"):
        pilot.validate_report_value(report, matrix=matrix, repo_root=REPO_ROOT)


def test_report_validation_rejects_contract_and_learner_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    matrix = pilot.load_matrix(repo_root=REPO_ROOT)
    report = _report()
    real_sources = pilot._source_records
    monkeypatch.setattr(
        pilot,
        "_source_records",
        lambda value, root: [
            *real_sources(value, root),
            {"path": "drift", "sha256": "f" * 64},
        ],
    )
    with pytest.raises(pilot.PilotError, match="contract source evidence is stale"):
        pilot.validate_report_value(report, matrix=matrix, repo_root=REPO_ROOT)

    monkeypatch.setattr(pilot, "_source_records", real_sources)
    monkeypatch.setattr(
        pilot,
        "_learner_hashes",
        lambda _matrix, _root: {"curriculum/changed": "e" * 64},
    )
    with pytest.raises(pilot.PilotError, match="learner-artifact evidence is stale"):
        pilot.validate_report_value(report, matrix=matrix, repo_root=REPO_ROOT)


def test_live_scope_rejects_fixture_historical_and_nonpassing_rows() -> None:
    rows = {row["id"]: row for row in _report()["rows"]}

    with pytest.raises(pilot.PilotError, match="repository rows only"):
        pilot._authorized_selectors(rows, ["partial-ambiguous-fixture"])
    with pytest.raises(pilot.PilotError, match="repository rows only"):
        pilot._authorized_selectors(rows, ["folk-material-repair-history"])
    rows["a1-built-shadow"]["passed"] = False
    passed = {row_id: row for row_id, row in rows.items() if row["passed"]}
    with pytest.raises(pilot.PilotError, match="absent or non-PASS"):
        pilot._authorized_selectors(passed, ["a1-built-shadow"])


def test_matrix_override_must_remain_repository_backed(tmp_path: Path) -> None:
    matrix_path = tmp_path / "matrix.yaml"
    matrix_path.write_text("schema_version: external\n", encoding="utf-8")

    with pytest.raises(pilot.PilotError, match="repository-backed"):
        pilot.load_matrix(repo_root=REPO_ROOT, matrix_path=matrix_path)


def test_same_family_live_authorization_is_rejected_before_scope_or_git_lookup(
    tmp_path: Path,
) -> None:
    report = _report()
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
    report_sha256 = pilot._sha256_bytes(report_path.read_bytes())
    first = next(row for row in report["rows"] if row["kind"] == "repository")
    authorization = {
        "schema_version": "curriculum-lifecycle-pilot-authorization.v1",
        "decision": "LIVE_PILOT_AUTHORIZED",
        "actor_type": "human",
        "actor_id": "operator",
        "approval_id": "approval-1",
        "matrix_sha256": report["matrix_sha256"],
        "report_sha256": report_sha256,
        "report_identity_sha256": report["identity_sha256"],
        "reviewed_commit": report["source_commit"],
        "review": {
            "verdict": "PASS",
            "author_family": "openai",
            "reviewer_family": "codex",
            "receipt": "review-receipt",
            "reviewed_report_sha256": report_sha256,
        },
        "scope": {
            "row_ids": [first["id"]],
            "selectors": [first["selector"]],
            "maximum_mutating_modules": 1,
        },
        "production_qg_armed": False,
    }
    authorization_path = tmp_path / "authorization.json"
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")

    with pytest.raises(pilot.PilotError, match="cross-family"):
        pilot.verify_authorization(
            authorization_path,
            report_path,
            repo_root=REPO_ROOT,
        )


def test_cli_has_no_live_execution_bypass() -> None:
    with pytest.raises(SystemExit):
        pilot.build_parser().parse_args(["shadow", "--live"])
