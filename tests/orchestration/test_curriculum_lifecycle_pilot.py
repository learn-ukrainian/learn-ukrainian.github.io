"""Cross-track shadow qualification and live-authorization safety tests."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import curriculum_lifecycle_pilot as pilot

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def pilot_matrix() -> dict[str, Any]:
    return pilot.load_matrix(repo_root=REPO_ROOT)


@pytest.fixture(scope="module")
def shadow_report() -> dict[str, Any]:
    """One shadow report per xdist worker.

    Several tests need a PASS report. Rebuilding it per test re-runs preparation
    and prompt resolution for every matrix row and is what pushed
    ``test_report_tampering_and_false_pass_fail_closed`` past the CI thread
    timeout under shard load (#6519 → worker ``os._exit``).
    """
    return pilot.build_shadow_report(repo_root=REPO_ROOT)


def test_matrix_is_complete_strict_and_shadow_only(pilot_matrix: dict[str, Any]) -> None:
    matrix = pilot_matrix

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


def test_shadow_report_passes_all_rows_without_learner_mutation_or_model_cost(
    shadow_report: dict[str, Any],
) -> None:
    report = shadow_report

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


def test_shadow_report_is_exactly_reproducible_at_one_source_tree(
    shadow_report: dict[str, Any],
) -> None:
    assert shadow_report == pilot.build_shadow_report(repo_root=REPO_ROOT)


def test_built_level_profiles_do_not_leak_cross_level_policy(
    shadow_report: dict[str, Any],
) -> None:
    rows = {row["id"]: row for row in shadow_report["rows"]}

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


def test_bio_pilot_binds_current_canonical_pass_and_bio_specific_prompt(
    shadow_report: dict[str, Any],
) -> None:
    row = next(row for row in shadow_report["rows"] if row["id"] == "bio-built-shadow")

    assert row["passed"] is True
    assert row["entry"]["state"] == "built-preparation-drift"
    assert row["disposition"] == "preparation-repair-required"
    assert row["prompt"]["profile"] == "seminar-bio"


def test_fixture_rows_prove_owned_pause_resume_and_qg_modes(
    shadow_report: dict[str, Any],
) -> None:
    rows = {row["scenario"]: row for row in shadow_report["rows"] if row["kind"] == "fixture"}

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


def test_report_tampering_and_false_pass_fail_closed(
    pilot_matrix: dict[str, Any],
    shadow_report: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-closed on identity / row / metrics tampering.

    ``validate_report_value(..., verify_current_rows=True)`` re-runs preparation
    and prompt resolution for every matrix row. This test historically paid that
    cost twice on top of ``build_shadow_report``, which is fine alone (~13–22s)
    but under CI xdist shard load exceeded the 110s faulthandler / 120s thread
    timeout and killed the worker via ``os._exit`` (#6519).

    Freeze one captured current-replay (the just-built PASS report's rows plus
    one learner-hash snapshot) so both fail-closed branches still execute the
    real validator against current evidence without a second full I/O replay.
    """
    matrix = pilot_matrix
    valid_report = shadow_report
    current_rows = {row["id"]: row for row in valid_report["rows"]}
    frozen_learner_hashes = pilot._learner_hashes(matrix, REPO_ROOT)

    monkeypatch.setattr(
        pilot,
        "_row_result",
        lambda row, _repo_root: deepcopy(current_rows[str(row["id"])]),
    )
    monkeypatch.setattr(
        pilot,
        "_learner_hashes",
        lambda _matrix, _repo_root: dict(frozen_learner_hashes),
    )

    report = deepcopy(valid_report)
    report["rows"][0]["passed"] = False

    with pytest.raises(pilot.PilotError, match="identity does not match"):
        pilot.validate_report_value(report, matrix=matrix, repo_root=REPO_ROOT)

    report["identity_sha256"] = pilot._report_identity(report)
    with pytest.raises(pilot.PilotError, match="row evidence does not match"):
        pilot.validate_report_value(report, matrix=matrix, repo_root=REPO_ROOT)

    report = deepcopy(valid_report)
    report["metrics"]["prompt_bytes"] += 1
    report["identity_sha256"] = pilot._report_identity(report)
    with pytest.raises(pilot.PilotError, match="metrics do not match"):
        pilot.validate_report_value(report, matrix=matrix, repo_root=REPO_ROOT)


def test_report_validation_rejects_contract_and_learner_drift(
    pilot_matrix: dict[str, Any],
    shadow_report: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    matrix = pilot_matrix
    report = shadow_report
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


def test_live_scope_rejects_fixture_historical_and_nonpassing_rows(
    shadow_report: dict[str, Any],
) -> None:
    # deepcopy: this test mutates a nested row; the module fixture is shared.
    rows = {row["id"]: row for row in deepcopy(shadow_report)["rows"]}

    with pytest.raises(pilot.PilotError, match="repository rows only"):
        pilot._authorized_selectors(
            rows,
            ["partial-ambiguous-fixture"],
            maximum_mutating_modules=1,
        )
    with pytest.raises(pilot.PilotError, match="repository rows only"):
        pilot._authorized_selectors(
            rows,
            ["folk-material-repair-history"],
            maximum_mutating_modules=1,
        )
    rows["a1-built-shadow"]["passed"] = False
    passed = {row_id: row for row_id, row in rows.items() if row["passed"]}
    with pytest.raises(pilot.PilotError, match="absent or non-PASS"):
        pilot._authorized_selectors(
            passed,
            ["a1-built-shadow"],
            maximum_mutating_modules=1,
        )


def test_live_scope_enforces_maximum_mutating_modules(
    shadow_report: dict[str, Any],
) -> None:
    rows = {
        row["id"]: row
        for row in deepcopy(shadow_report)["rows"]
        if row["passed"] and row["kind"] == "repository"
    }
    row_ids = list(rows)[:2]

    with pytest.raises(pilot.PilotError, match="maximum mutating modules"):
        pilot._authorized_selectors(
            rows,
            row_ids,
            maximum_mutating_modules=1,
        )


def test_matrix_override_must_remain_repository_backed(tmp_path: Path) -> None:
    matrix_path = tmp_path / "matrix.yaml"
    matrix_path.write_text("schema_version: external\n", encoding="utf-8")

    with pytest.raises(pilot.PilotError, match="repository-backed"):
        pilot.load_matrix(repo_root=REPO_ROOT, matrix_path=matrix_path)


def test_same_family_live_authorization_is_rejected_before_scope_or_git_lookup(
    shadow_report: dict[str, Any],
    tmp_path: Path,
) -> None:
    report = shadow_report
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
