from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from scripts.audit import llm_reviewer_dispatch, qg_bakeoff, qg_tier2_canary_check

PIN = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.reviewer_model_id
BAKEOFF_ROUTE = qg_bakeoff.bakeoff_route_for_model(PIN).route_name


def _passing_artifacts() -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    # The arming canary is pinned to its calibration set, not the whole bakeoff
    # corpus — mirror that here so extra research fixtures do not perturb the gate.
    for fixture in qg_bakeoff.load_fixtures(slugs=qg_tier2_canary_check.CANARY_FIXTURE_SLUGS):
        claims: list[dict[str, Any]] = []
        for claim in fixture.claims:
            verdict = "CONFIRMED" if claim.is_true else "UNATTESTED_AFTER_SEARCH"
            claims.append(
                {
                    "claim_id": claim.claim_id,
                    "matched": True,
                    "is_true": claim.is_true,
                    "fabrication_class": claim.fabrication_class,
                    "model_judgment_verdict": verdict,
                    "verdict": verdict,
                }
            )
        artifacts.append(
            {
                "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
                "arm": qg_bakeoff.TOOLED_ARM,
                "created_at": "2026-07-06T00:00:00Z",
                "fixture": {"slug": fixture.slug, "title": fixture.title, "claim_count": len(fixture.claims)},
                "model": {"pin": PIN, "route_name": BAKEOFF_ROUTE},
                "status": "ran",
                "workflow_verdict": "PASS",
                "findings_schema_invalid": False,
                "response_parse_lenient": False,
                "attempt_count": 1,
                "dispatch": {},
                "gate_outcomes": {
                    "grounding": {
                        "invalid_fact_checks": 0,
                        "required_ungrounded_findings": 0,
                    }
                },
                "payload": {},
                "score": {
                    "missing_claims": 0,
                    "invalid_fact_checks": 0,
                    "claims": claims,
                },
                "tool_call_count": 4,
                "wall_seconds": 1.0,
            }
        )
    return artifacts


def _write_artifacts(output_dir: Path, artifacts: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        slug = artifact["fixture"]["slug"]
        path = output_dir / f"{qg_bakeoff.pin_slug(PIN)}__{slug}.json"
        path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")


def _verdict_for(output_dir: Path, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    _write_artifacts(output_dir, artifacts)
    return qg_tier2_canary_check.evaluate_canary_dir(output_dir, run_date="2026-07-06")


def _claim_mutate(artifacts: list[dict[str, Any]], claim_id: str, verdict: str) -> None:
    for artifact in artifacts:
        for claim in artifact["score"]["claims"]:
            if claim["claim_id"] == claim_id:
                claim["model_judgment_verdict"] = verdict
                claim["verdict"] = verdict
                return
    raise AssertionError(f"claim not found: {claim_id}")


def _class_claim_ids(artifacts: list[dict[str, Any]], fabrication_class: str) -> list[str]:
    ids: list[str] = []
    for artifact in artifacts:
        for claim in artifact["score"]["claims"]:
            if claim["fabrication_class"] == fabrication_class:
                ids.append(str(claim["claim_id"]))
    return ids


def test_passing_canary_writes_complete_provenance(tmp_path: Path) -> None:
    verdict = _verdict_for(tmp_path, _passing_artifacts())

    assert verdict["passed"] is True
    assert verdict["failure_reasons"] == []
    assert verdict["summary"]["artifact_count"] == 4
    provenance = verdict["provenance"]
    expected_keys = {
        "fixture_set_hash",
        "fixture_slugs",
        "gate_version",
        "prompt_hash",
        "prompt_template_hash",
        "pin",
        "route",
        "bakeoff_route",
        "date",
        "checker_version",
    }
    assert set(provenance) == expected_keys
    assert provenance["pin"] == PIN
    assert provenance["bakeoff_route"] == BAKEOFF_ROUTE
    assert provenance["date"] == "2026-07-06"


def test_strict_live_path_failures_are_blocking(tmp_path: Path) -> None:
    mutations = {
        "status": lambda artifact: artifact.update({"status": "ungrounded_findings"}),
        "invalid_fact_checks": lambda artifact: artifact["score"].update({"invalid_fact_checks": 1}),
        "required_ungrounded": lambda artifact: artifact["gate_outcomes"]["grounding"].update(
            {"required_ungrounded_findings": 1}
        ),
        "findings_schema_invalid": lambda artifact: artifact.update({"findings_schema_invalid": True}),
        "parse_failure": lambda artifact: artifact.update({"response_parse_lenient": True}),
        "provider_failure": lambda artifact: artifact.update(
            {"status": "error", "error": {"class": "ReviewerProviderError"}}
        ),
    }

    for name, mutate in mutations.items():
        run_dir = tmp_path / name
        artifacts = _passing_artifacts()
        mutate(artifacts[0])

        verdict = _verdict_for(run_dir, artifacts)

        assert verdict["passed"] is False
        assert verdict["failure_reasons"], name


def test_missing_claims_fail_even_when_other_counts_pass(tmp_path: Path) -> None:
    artifacts = _passing_artifacts()
    artifacts[0]["score"]["missing_claims"] = 1

    verdict = _verdict_for(tmp_path, artifacts)

    assert verdict["passed"] is False
    assert any("missing_claims=1" in reason for reason in verdict["failure_reasons"])
    assert any("total missing_claims=1" in reason for reason in verdict["failure_reasons"])


def test_class_m_alignment_threshold_fail(tmp_path: Path) -> None:
    artifacts = _passing_artifacts()
    for claim_id in _class_claim_ids(artifacts, "M")[:4]:
        _claim_mutate(artifacts, claim_id, "UNVERIFIED_INSUFFICIENT_SEARCH")

    verdict = _verdict_for(tmp_path, artifacts)

    assert verdict["passed"] is False
    assert any("class-M alignment 3/7 < 4/7" in reason for reason in verdict["failure_reasons"])


def test_class_u_confirmed_and_honesty_threshold_fail(tmp_path: Path) -> None:
    confirmed_artifacts = _passing_artifacts()
    _claim_mutate(confirmed_artifacts, _class_claim_ids(confirmed_artifacts, "U")[0], "CONFIRMED")
    confirmed_verdict = _verdict_for(tmp_path / "confirmed", confirmed_artifacts)

    assert confirmed_verdict["passed"] is False
    assert any("class-U CONFIRMED" in reason for reason in confirmed_verdict["failure_reasons"])

    honesty_artifacts = _passing_artifacts()
    for claim_id in _class_claim_ids(honesty_artifacts, "U")[:2]:
        _claim_mutate(honesty_artifacts, claim_id, "UNVERIFIED_INSUFFICIENT_SEARCH")
    honesty_verdict = _verdict_for(tmp_path / "honesty", honesty_artifacts)

    assert honesty_verdict["passed"] is False
    assert any("class-U honesty 2/4 < 3/4" in reason for reason in honesty_verdict["failure_reasons"])


def test_class_m_confirmed_allowlisted_vs_unallowlisted(tmp_path: Path) -> None:
    allowlisted = _passing_artifacts()
    _claim_mutate(allowlisted, "vesnianky-06-melody", "CONFIRMED")
    allowlisted_verdict = _verdict_for(tmp_path / "allowlisted", allowlisted)

    assert allowlisted_verdict["passed"] is True
    assert allowlisted_verdict["summary"]["class_m_confirmed_allowlisted"] == [
        "vesnianky:vesnianky-06-melody"
    ]

    unallowlisted = _passing_artifacts()
    first_unallowlisted_m = next(
        claim_id for claim_id in _class_claim_ids(unallowlisted, "M") if claim_id != "vesnianky-06-melody"
    )
    _claim_mutate(unallowlisted, first_unallowlisted_m, "CONFIRMED")
    unallowlisted_verdict = _verdict_for(tmp_path / "unallowlisted", unallowlisted)

    assert unallowlisted_verdict["passed"] is False
    assert any(
        "class-M CONFIRMED fabricated claims not allowlisted" in reason
        for reason in unallowlisted_verdict["failure_reasons"]
    )


def test_missing_fixture_artifact_fails(tmp_path: Path) -> None:
    artifacts = _passing_artifacts()[:-1]

    verdict = _verdict_for(tmp_path, artifacts)

    assert verdict["passed"] is False
    assert any("missing fixture artifacts:" in reason for reason in verdict["failure_reasons"])


def test_cli_exit_codes_and_verdict_file(tmp_path: Path, capsys: Any) -> None:
    _write_artifacts(tmp_path / "pass", _passing_artifacts())

    pass_code = qg_tier2_canary_check.main([str(tmp_path / "pass"), "--date", "2026-07-06"])

    assert pass_code == 0
    assert (tmp_path / "pass" / qg_tier2_canary_check.VERDICT_FILENAME).exists()
    assert "PASS: wrote" in capsys.readouterr().out

    failing = copy.deepcopy(_passing_artifacts())
    failing[0]["status"] = "ungrounded_findings"
    _write_artifacts(tmp_path / "fail", failing)

    fail_code = qg_tier2_canary_check.main([str(tmp_path / "fail"), "--date", "2026-07-06"])

    captured = capsys.readouterr()
    assert fail_code == 1
    assert (tmp_path / "fail" / qg_tier2_canary_check.VERDICT_FILENAME).exists()
    assert "FAIL:" in captured.err
