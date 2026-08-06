"""Mechanical tests for the machine-pinned Phase 3 near-duplicate firewall."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_near_duplicate as near

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data/projects/open_model_data/evidence/correction_protection_near_duplicate_policy_v1.json"


def _record(*, document: str = "doc:a", unit: str = "unit:1", span: str = "span:1", surface: str = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon") -> dict[str, str]:
    return {
        "source_document_identity": document,
        "unit_identity": unit,
        "span_fingerprint": span,
        "normalized_surface": surface,
    }


def test_policy_is_self_pinned_and_covers_every_required_use() -> None:
    policy = near.load_policy(POLICY)
    assert policy["policy_fingerprint_sha256"] == near.policy_fingerprint(policy)
    assert set(policy["governs"]) == near.REQUIRED_GOVERNS
    assert set(policy["scopes"]) == near.REQUIRED_SCOPES
    assert {item["expected"] for item in policy["golden_fixtures"]} == {"exact", "near", "nonmatch"}
    assert near.policy_for_governed_use("ua_eval_exclusion", path=POLICY) == policy
    with pytest.raises(near.NearDuplicatePolicyError, match="not governed"):
        near.policy_for_governed_use("unapproved_use", path=POLICY)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("ALPHA— beta", "alpha beta", "exact"),
        (
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon",
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau phi",
            "near",
        ),
        ("alpha beta gamma", "orange violet black", "nonmatch"),
    ],
)
def test_golden_mechanics_classify_exact_near_and_nonmatch(left: str, right: str, expected: str) -> None:
    assert near.classify_texts(left, right, policy=near.load_policy(POLICY)).classification == expected


def test_fixture_manifest_is_executable() -> None:
    policy = near.load_policy(POLICY)
    for fixture in policy["golden_fixtures"]:
        result = near.classify_texts(fixture["left"], fixture["right"], scope=fixture["scope"], policy=policy)
        assert result.classification == fixture["expected"]


def test_document_unit_and_span_scopes_are_distinct() -> None:
    policy = near.load_policy(POLICY)
    left = _record()
    assert near.classify_records(left, _record(document="doc:b"), scope="document", policy=policy).classification == "nonmatch"
    assert near.classify_records(left, _record(unit="unit:2"), scope="unit", policy=policy).classification == "nonmatch"
    assert near.classify_records(
        left,
        _record(
            span="span:2",
            surface="alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau phi",
        ),
        scope="span",
        policy=policy,
    ).classification == "near"


def test_policy_drift_and_malformed_comparison_fail_closed(tmp_path: Path) -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    policy["numeric_thresholds"]["near_duplicate_minimum"] = 0.91
    drifted = tmp_path / "drifted.json"
    drifted.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(near.NearDuplicatePolicyError, match="thresholds drift"):
        near.load_policy(drifted)
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    policy["golden_fixtures"][0]["left"] = "changed mechanical fixture"
    policy["policy_fingerprint_sha256"] = near.policy_fingerprint(policy)
    drifted.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(near.NearDuplicatePolicyError, match="implementation policy pin drift"):
        near.load_policy(drifted)
    assert near.duplicate_or_fail_closed(_record(), {"normalized_surface": "x"}, policy=near.load_policy(POLICY)) is True


def test_expected_fingerprint_mismatch_fails_closed() -> None:
    with pytest.raises(near.NearDuplicatePolicyError, match="expected fingerprint drift"):
        near.pinned_policy_fingerprint(path=POLICY, expected_fingerprint="0" * 64)


def test_canonical_rule_collapse_and_nonduplicate_activation_counts_are_policy_bound() -> None:
    policy = near.load_policy(POLICY)
    first = {"surface": "Alpha beta", "replacement": "Gamma"}
    second = {"surface": "alpha—beta", "replacement": "gamma"}
    third = {"surface": "other", "replacement": "gamma"}
    near_first = {
        "surface": "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon",
        "replacement": "result",
    }
    near_second = {
        "surface": "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau phi",
        "replacement": "result",
    }
    groups = near.collapse_canonical_rules([third, near_second, second, near_first, first], policy=policy)
    assert sorted(len(group) for group in groups.values()) == [1, 2, 2]
    assert any(near_first in group and near_second in group for group in groups.values())
    assert near.canonical_json(groups) == near.canonical_json(
        near.collapse_canonical_rules([first, near_first, second, near_second, third], policy=policy)
    )
    assert near.nonduplicate_activation_count(
        [
            {"duplicate": False, "rule": first},
            {"duplicate": False, "rule": second},
            {"duplicate": False, "rule": third},
            {"duplicate": False, "rule": near_first},
            {"duplicate": False, "rule": near_second},
        ],
        policy=policy,
    ) == 3
    with pytest.raises(near.NearDuplicatePolicyError, match="explicitly false"):
        near.nonduplicate_activation_count([{"duplicate": True, "rule": first}], policy=policy)


def test_cli_reports_verified_pin_and_machine_classification(capsys: pytest.CaptureFixture[str]) -> None:
    assert near.main(["--policy", str(POLICY), "verify"]) == 0
    assert json.loads(capsys.readouterr().out)["verified"] is True
    assert near.main(["--policy", str(POLICY), "classify", "alpha beta", "ALPHA—BETA"]) == 0
    assert json.loads(capsys.readouterr().out)["classification"] == "exact"
