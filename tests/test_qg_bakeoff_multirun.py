from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import llm_reviewer_dispatch, qg_bakeoff

PIN = "openrouter/google/gemma-4-31b-it"


def _fixture(slug: str = "vesnianky") -> qg_bakeoff.BakeoffFixture:
    return qg_bakeoff.BakeoffFixture(
        slug=slug,
        title="Sample",
        passage_md="True claim. Fabricated claim.",
        claims=(
            qg_bakeoff.FixtureClaim("c-true", "True claim.", True),
            qg_bakeoff.FixtureClaim("c-false", "Fabricated claim.", False, "M", "real adjacent quote"),
        ),
    )


def _event() -> dict[str, Any]:
    return {
        "tool": "sources_query_wikipedia",
        "input": {"query": "True claim", "mode": "section"},
        "status": "completed",
        "tool_call_id": "call_1",
        "output": "True claim. Fabricated claim.",
    }


def _tooled_result(route: llm_reviewer_dispatch.ReviewerRoute) -> llm_reviewer_dispatch.DispatchResult:
    payload = {
        "findings": [],
        "fact_checks": [
            {
                "claim": "True claim.",
                "verdict": "CONFIRMED",
                "grounding": {
                    "tool": "sources_query_wikipedia",
                    "query": "True claim",
                    "evidence_excerpt": "True claim",
                    "tool_call_id": "call_1",
                },
            },
            {
                "claim": "Fabricated claim.",
                "verdict": "UNATTESTED_AFTER_SEARCH",
                "grounding": {
                    "tool": "sources_query_wikipedia",
                    "query": "True claim",
                    "evidence_excerpt": "Fabricated claim",
                    "tool_call_id": "call_1",
                },
            },
        ],
        "evidence_gaps": [],
    }
    return llm_reviewer_dispatch.DispatchResult(
        response_text=json.dumps(payload),
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        tool_call_count=1,
        tools_used=("sources_query_wikipedia",),
        tool_events=(_event(),),
    )


def _artifact(
    *,
    slug: str = "vesnianky",
    arm: str = qg_bakeoff.TOOLED_ARM,
    run_index: int = 1,
    model: str = "openrouter/test/m",
    mj: int = 30,
    live: int | None = None,
    status: str = "ran",
    parse_lenient: bool = False,
    transport: str = qg_bakeoff.OPENCODE_TRANSPORT,
    entrypoint: str = qg_bakeoff.OPENCODE_ENTRYPOINT,
    claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    live_score = mj if live is None else live
    score_claims = claims if claims is not None else [
        {
            "claim_id": "c-true",
            "matched": True,
            "is_true": True,
            "fabrication_class": None,
            "model_judgment_verdict": "CONFIRMED",
            "verdict": "CONFIRMED",
        },
        {
            "claim_id": "c-false",
            "matched": True,
            "is_true": False,
            "fabrication_class": "M",
            "model_judgment_verdict": "UNATTESTED_AFTER_SEARCH",
            "verdict": "UNATTESTED_AFTER_SEARCH",
        },
    ]
    return {
        "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
        "arm": arm,
        "run_index": run_index,
        "created_at": "2026-07-06T00:00:00Z",
        "fixture": {"slug": slug, "title": "Sample", "claim_count": 2},
        "model": {
            "pin": model,
            "pin_slug": qg_bakeoff.pin_slug(model),
            "transport": transport,
            "entrypoint": entrypoint,
            "measurement_tier": qg_bakeoff.OPENCODE_MEASUREMENT_TIER,
        },
        "status": status,
        "workflow_verdict": "PASS" if status == "ran" else "ERROR",
        "findings_schema_invalid": False,
        "response_parse_lenient": parse_lenient,
        "attempt_count": 1,
        "dispatch": {},
        "gate_outcomes": {"grounding": {"invalid_fact_checks": 0, "inadmissible_positive_verdicts": 0}},
        "payload": {},
        "score": {
            "model_judgment_score": mj,
            "live_admissible_score": live_score,
            "missing_claims": 0,
            "invalid_fact_checks": 0,
            "inadmissible_positive_verdicts": 0,
            "claims": score_claims,
            "fractions": {
                "class_u_honesty": {"numerator": 0, "denominator": 0, "text": "0/0", "low_n": True},
                "class_m_alignment": {"numerator": 1, "denominator": 1, "text": "1/1", "low_n": True},
                "false_unsupported_on_true": {"numerator": 0, "denominator": 1, "text": "0/1", "low_n": True},
            },
        },
        "tool_call_count": 1,
        "wall_seconds": 1.0,
    }


def _write_artifact(path: Path, artifact: dict[str, Any]) -> None:
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_multirun_matrix_resume_retry_and_narrower_runs_leave_r3(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
    calls: list[str] = []

    def runner(
        route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(task_id)
        return _tooled_result(route)

    runs = qg_bakeoff.run_matrix([fixture], [PIN], output_dir=tmp_path, runner=runner, runs=3)

    assert len(runs) == 3
    assert [run.artifact["run_index"] for run in runs] == [1, 2, 3]
    names = sorted(path.name for path in tmp_path.glob("*.json"))
    assert names == [
        "openrouter-google-gemma-4-31b-it__vesnianky.json",
        "openrouter-google-gemma-4-31b-it__vesnianky__r2.json",
        "openrouter-google-gemma-4-31b-it__vesnianky__r3.json",
    ]
    assert calls == [
        "qg-bakeoff-openrouter-google-gemma-4-31b-it-vesnianky",
        "qg-bakeoff-openrouter-google-gemma-4-31b-it-vesnianky-r2",
        "qg-bakeoff-openrouter-google-gemma-4-31b-it-vesnianky-r3",
    ]

    calls.clear()
    resumed = qg_bakeoff.run_matrix([fixture], [PIN], output_dir=tmp_path, runner=runner, runs=3)
    assert all(run.skipped for run in resumed)
    assert calls == []

    r2_path = tmp_path / "openrouter-google-gemma-4-31b-it__vesnianky__r2.json"
    r2 = json.loads(r2_path.read_text(encoding="utf-8"))
    r2["status"] = "error"
    _write_artifact(r2_path, r2)
    calls.clear()
    qg_bakeoff.run_matrix(
        [fixture],
        [PIN],
        output_dir=tmp_path,
        runner=runner,
        retry_failures=True,
        runs=3,
    )
    assert calls == ["qg-bakeoff-openrouter-google-gemma-4-31b-it-vesnianky-r2"]

    r3_path = tmp_path / "openrouter-google-gemma-4-31b-it__vesnianky__r3.json"
    r3_before = r3_path.read_text(encoding="utf-8")
    calls.clear()
    qg_bakeoff.run_matrix([fixture], [PIN], output_dir=tmp_path, runner=runner, force=True, runs=2)
    assert calls == [
        "qg-bakeoff-openrouter-google-gemma-4-31b-it-vesnianky",
        "qg-bakeoff-openrouter-google-gemma-4-31b-it-vesnianky-r2",
    ]
    assert r3_path.read_text(encoding="utf-8") == r3_before


def test_cell_artifact_path_round_trips_all_arms_and_mismatch_fails(tmp_path: Path) -> None:
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model(PIN)
    direct = qg_bakeoff.bakeoff_route_for_model(qg_bakeoff.DEEPSEEK_DIRECT_FLASH_PIN)
    subscription = qg_bakeoff.route_for_matrix_pin(qg_bakeoff.GPT_SUBSCRIPTION_BARE_MODEL_ID, arm=qg_bakeoff.BARE_ARM)

    assert qg_bakeoff.default_output_dir(date(2026, 7, 6), multi_run=True).name == "2026-07-06-qg-bakeoff-multirun"
    assert qg_bakeoff._cell_artifact_path(tmp_path, route, fixture, qg_bakeoff.TOOLED_ARM).name == (
        "openrouter-google-gemma-4-31b-it__vesnianky.json"
    )
    assert qg_bakeoff._cell_artifact_path(tmp_path, route, fixture, qg_bakeoff.TOOLED_ARM, 2).name == (
        "openrouter-google-gemma-4-31b-it__vesnianky__r2.json"
    )
    assert qg_bakeoff._cell_artifact_path(tmp_path, route, fixture, qg_bakeoff.BARE_ARM, 3).name == (
        "openrouter-google-gemma-4-31b-it__vesnianky__bare__opencode__r3.json"
    )
    assert qg_bakeoff._cell_artifact_path(tmp_path, direct, fixture, qg_bakeoff.TOOLED_ARM).name == (
        "deepseek-direct-deepseek-v4-flash__vesnianky.json"
    )
    assert qg_bakeoff._cell_artifact_path(tmp_path, direct, fixture, qg_bakeoff.BARE_ARM, 3).name == (
        "deepseek-direct-deepseek-v4-flash__vesnianky__bare__opencode__r3.json"
    )
    assert qg_bakeoff._cell_artifact_path(tmp_path, subscription, fixture, qg_bakeoff.BARE_ARM, 2).name == (
        "gpt-5-5__vesnianky__bare__runtime-codex__r2.json"
    )

    mismatched = tmp_path / "openrouter-test-m__vesnianky.json"
    _write_artifact(mismatched, _artifact(run_index=2))
    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="run_index=2"):
        qg_bakeoff._load_all_artifacts(tmp_path)


def test_subscription_preflight_runs_at_each_sweep_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model(PIN)
    for run_index in (1, 2, 3):
        path = qg_bakeoff._cell_artifact_path(tmp_path, route, fixture, qg_bakeoff.BARE_ARM, run_index)
        _write_artifact(path, _artifact(arm=qg_bakeoff.BARE_ARM, run_index=run_index, model=PIN))

    calls: list[list[str]] = []

    def preflight(routes: list[llm_reviewer_dispatch.ReviewerRoute]) -> dict[str, Any]:
        calls.append([route.reviewer_model_id for route in routes])
        return {"status": "passed", "routes": []}

    monkeypatch.setattr(qg_bakeoff, "preflight_subscription_bare_routes", preflight)

    runs = qg_bakeoff.run_matrix([fixture], [PIN], output_dir=tmp_path, arm=qg_bakeoff.BARE_ARM, runs=3)

    assert all(run.skipped for run in runs)
    assert calls == [[PIN], [PIN], [PIN]]


def test_legacy_scorecard_renders_byte_identical_to_golden(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(qg_bakeoff, "_now_z", lambda: "2026-07-06T00:00:00Z")
    out = tmp_path / "SCORECARD.md"
    artifacts = [
        {key: value for key, value in _artifact(mj=30).items() if key != "run_index"},
        {key: value for key, value in _artifact(arm=qg_bakeoff.BARE_ARM, mj=-80).items() if key != "run_index"},
    ]

    qg_bakeoff.write_scorecard(out, artifacts)

    golden = Path("tests/fixtures/qg_bakeoff_scorecards/legacy_scorecard.md").read_text(encoding="utf-8")
    assert out.read_text(encoding="utf-8") == golden


def test_variance_math_stability_flags_and_single_run_gate(tmp_path: Path) -> None:
    assert qg_bakeoff._claim_stability_class(
        {"matched": True, "is_true": True, "model_judgment_verdict": "CONFIRMED"}
    ) == "true-confirmed"
    assert qg_bakeoff._claim_stability_class(
        {"matched": True, "is_true": False, "model_judgment_verdict": "REFUTED_BY_CONTRADICTION"}
    ) == "fabrication-caught"
    assert qg_bakeoff._claim_stability_class({"matched": False, "is_true": True}) == "missed"
    assert qg_bakeoff._claim_stability_class(
        {"matched": True, "is_true": True, "model_judgment_verdict": "UNATTESTED_AFTER_SEARCH"}
    ) == "other"

    single = tmp_path / "single.md"
    qg_bakeoff.write_scorecard(single, [_artifact(run_index=1)])
    assert "## Run Variance" not in single.read_text(encoding="utf-8")

    flipped_claims = [
        {
            "claim_id": "c-true",
            "matched": True,
            "is_true": True,
            "fabrication_class": None,
            "model_judgment_verdict": "UNATTESTED_AFTER_SEARCH",
            "verdict": "UNATTESTED_AFTER_SEARCH",
        },
        {
            "claim_id": "c-false",
            "matched": False,
            "is_true": False,
            "fabrication_class": "M",
            "model_judgment_verdict": "",
            "verdict": "",
        },
    ]
    artifacts = [
        _artifact(slug="vesnianky", run_index=1, mj=30),
        _artifact(slug="vesnianky", run_index=2, mj=30, parse_lenient=True),
        _artifact(slug="vesnianky", run_index=3, mj=-20, claims=flipped_claims),
        _artifact(slug="kupalski", run_index=1, mj=10),
        _artifact(slug="kupalski", run_index=2, mj=10),
        _artifact(slug="koliadky", run_index=1, status="error", mj=-20),
        _artifact(slug="koliadky", run_index=2, mj=30),
        _artifact(slug="koliadky", run_index=3, mj=30),
    ]
    multirun = tmp_path / "multi.md"
    qg_bakeoff.write_scorecard(multirun, artifacts)
    text = multirun.read_text(encoding="utf-8")
    assert "## Run Variance" in text
    assert "partial" in text
    assert "error" in text
    assert "parse-lenient-variance" in text
    assert "| openrouter/test/m [opencode/qg_bakeoff_opencode] | tooled | 1 | 1 | 1 | 1 |" in text


def test_domain_mapping_complete_and_unknown_slug_fails(tmp_path: Path) -> None:
    fixture_slugs = {path.stem for path in qg_bakeoff.FIXTURE_DIR.glob("*.json")}
    assert set(qg_bakeoff.DOMAIN_BY_SLUG) == fixture_slugs

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="DOMAIN_BY_SLUG"):
        qg_bakeoff.write_scorecard(tmp_path / "score.md", [_artifact(slug="unknown", run_index=2)])


def test_multirun_aggregate_and_harness_lift_do_not_triple_count() -> None:
    artifacts = [
        _artifact(run_index=1, mj=10),
        _artifact(run_index=2, mj=20),
        _artifact(run_index=3, mj=30),
    ]
    row = next(iter(qg_bakeoff._aggregate_by_model_arm(artifacts).values()))
    assert row["passages_per_run"] == [1, 1, 1]
    assert row["model_judgment_score"]["mean"] == 20

    lift_artifacts = [
        _artifact(slug="vesnianky", arm=qg_bakeoff.TOOLED_ARM, run_index=1, mj=30),
        _artifact(slug="vesnianky", arm=qg_bakeoff.TOOLED_ARM, run_index=2, mj=50),
        _artifact(slug="vesnianky", arm=qg_bakeoff.BARE_ARM, run_index=1, mj=-10),
        _artifact(slug="vesnianky", arm=qg_bakeoff.BARE_ARM, run_index=2, mj=10),
        _artifact(slug="kupalski", arm=qg_bakeoff.TOOLED_ARM, run_index=2, mj=999),
    ]
    lines = qg_bakeoff._harness_lift_section("Test", lift_artifacts)
    row = next(line for line in lines if line.startswith("| openrouter/test/m"))
    assert "| 1 |" in row
    assert "40 ± 0 [40..40]" in row
    assert "999" not in row


def test_rescore_preserves_multirun_run_index(tmp_path: Path) -> None:
    fixture = _fixture()
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / "vesnianky.json").write_text(
        json.dumps(
            {
                "slug": fixture.slug,
                "title": fixture.title,
                "passage_md": fixture.passage_md,
                "claims": [
                    {
                        "claim_id": claim.claim_id,
                        "claim": claim.claim,
                        "is_true": claim.is_true,
                        "fabrication_class": claim.fabrication_class,
                        "distractor_evidence": claim.distractor_evidence,
                    }
                    for claim in fixture.claims
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    artifact = _artifact(run_index=2, mj=-999)
    artifact["payload"] = {
        "fact_checks": [
            {"claim": "True claim.", "verdict": "CONFIRMED"},
            {"claim": "Fabricated claim.", "verdict": "UNATTESTED_AFTER_SEARCH"},
        ]
    }
    path = tmp_path / "openrouter-test-m__vesnianky__r2.json"
    _write_artifact(path, artifact)

    assert qg_bakeoff.rescore_artifacts(tmp_path, fixtures_dir) == 1
    updated = json.loads(path.read_text(encoding="utf-8"))
    assert updated["run_index"] == 2
    assert updated["score"]["model_judgment_score"] == 30


def test_run_one_tooled_resume_transport_mismatch_hard_fails(tmp_path: Path) -> None:
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model(PIN)
    path = qg_bakeoff._cell_artifact_path(tmp_path, route, fixture, qg_bakeoff.TOOLED_ARM)
    artifact = _artifact(model=PIN, transport="runtime-codex")
    _write_artifact(path, artifact)

    def runner(*_args: Any, **_kwargs: Any) -> llm_reviewer_dispatch.DispatchResult:  # pragma: no cover
        raise AssertionError("transport mismatch must fail before invocation")

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="transport"):
        qg_bakeoff.run_one(route, fixture, output_dir=tmp_path, runner=runner)
