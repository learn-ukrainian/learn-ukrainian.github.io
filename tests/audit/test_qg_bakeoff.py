from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import llm_reviewer_dispatch, qg_bakeoff, qg_factcheck_scoring


def _fixture() -> qg_bakeoff.BakeoffFixture:
    return qg_bakeoff.BakeoffFixture(
        slug="sample",
        title="Sample",
        passage_md="True claim. Fabricated claim.",
        claims=(
            qg_bakeoff.FixtureClaim("c-true", "True claim.", True),
            qg_bakeoff.FixtureClaim("c-false", "Fabricated claim.", False, "M", "real adjacent quote"),
        ),
    )


def _event(query: str = "True claim") -> dict[str, Any]:
    return {
        "tool": "sources_query_wikipedia",
        "input": {"query": query, "mode": "section"},
        "status": "completed",
        "tool_call_id": "call_1",
        "output": "True claim. Fabricated claim.",
    }


def _dispatch_result(payload: dict[str, Any], route: llm_reviewer_dispatch.ReviewerRoute) -> llm_reviewer_dispatch.DispatchResult:
    return llm_reviewer_dispatch.DispatchResult(
        response_text=json.dumps(payload),
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        tool_call_count=1,
        tools_used=("sources_query_wikipedia",),
        tool_events=(_event(),),
    )


def test_fixture_validation_rejects_duplicate_claim_id(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "slug": "bad",
                "title": "Bad",
                "passage_md": "x",
                "claims": [
                    {"claim_id": "dup", "claim": "a", "is_true": True},
                    {"claim_id": "dup", "claim": "b", "is_true": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="duplicate claim_id"):
        qg_bakeoff.load_fixture(path)


def test_fixture_validation_rejects_class_m_without_distractor(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "slug": "bad",
                "title": "Bad",
                "passage_md": "x",
                "claims": [
                    {
                        "claim_id": "m",
                        "claim": "m",
                        "is_true": False,
                        "fabrication_class": "M",
                        "distractor_evidence": "",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="class-M claims require distractor_evidence"):
        qg_bakeoff.load_fixture(path)


def test_vesnianky_anchor_fixture_shape() -> None:
    fixture = qg_bakeoff.load_fixture(qg_bakeoff.FIXTURE_DIR / "vesnianky.json")
    false_claims = {claim.claim_id: claim for claim in fixture.claims if not claim.is_true}

    assert fixture.slug == "vesnianky"
    assert len(fixture.claims) == 8
    assert false_claims["vesnianky-04-hai-trees"].fabrication_class == "U"
    assert false_claims["vesnianky-06-melody"].fabrication_class == "M"
    assert "Весну зустрічали радісно й пишно" in (
        false_claims["vesnianky-06-melody"].distractor_evidence or ""
    )


def test_guards_refuse_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "1")
    monkeypatch.setenv("QG_BAKEOFF", "1")

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="CI"):
        qg_bakeoff.require_offline_opt_in()


def test_guards_refuse_without_explicit_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("QG_BAKEOFF", raising=False)

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="QG_BAKEOFF=1"):
        qg_bakeoff.require_offline_opt_in()


def test_bakeoff_deepseek_route_stays_unregistered_while_live_policy_rejects_deepseek() -> None:
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/deepseek/deepseek-v4-pin")

    assert route not in llm_reviewer_dispatch.ROUTES
    assert all(existing.route_name != route.route_name for existing in llm_reviewer_dispatch.ROUTES)
    with pytest.raises(llm_reviewer_dispatch.ReviewerRouteError):
        llm_reviewer_dispatch.assert_route_allowed(route)
    hermes_route = qg_bakeoff.bakeoff_route_for_model("hermes/some-model-pin")
    with pytest.raises(llm_reviewer_dispatch.ReviewerRouteError):
        llm_reviewer_dispatch.assert_route_allowed(hermes_route)


def test_scoring_counts_missing_claim_and_preserves_model_judgment_on_downgrade() -> None:
    payload = {
        "fact_checks": [
            {
                "claim": "Fabricated claim.",
                "verdict": "UNVERIFIED_INSUFFICIENT_SEARCH",
                "original_verdict": "CONFIRMED",
                "admissibility_downgraded": True,
            }
        ]
    }

    score = qg_bakeoff.score_payload(payload, _fixture())

    assert qg_factcheck_scoring.score_verdict("UNVERIFIED_INSUFFICIENT_SEARCH", claim_is_true=False) == 0
    assert score["missing_claims"] == 1
    assert score["model_judgment_score"] == -110
    assert score["live_admissible_score"] == -10
    false_row = next(row for row in score["claims"] if row["claim_id"] == "c-false")
    assert false_row["model_judgment_points"] == -100
    assert false_row["live_admissible_points"] == 0


def test_claim_matching_accepts_standalone_extraction_from_anchor_fragment() -> None:
    fixture = qg_bakeoff.BakeoffFixture(
        slug="fragment",
        title="Fragment",
        passage_md="x",
        claims=(qg_bakeoff.FixtureClaim("u", "або вигаданий обряд.", False, "U"),),
    )
    payload = {"fact_checks": [{"claim": "вигаданий обряд.", "verdict": "UNATTESTED_AFTER_SEARCH"}]}

    score = qg_bakeoff.score_payload(payload, fixture)

    assert score["missing_claims"] == 0
    assert score["model_judgment_score"] == 10


def test_resume_skips_existing_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/google/gemma-4-31b-it")
    artifact_path = tmp_path / f"{qg_bakeoff.pin_slug(route.reviewer_model_id)}__{fixture.slug}.json"
    artifact_path.write_text(
        json.dumps(
            {
                "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
                "fixture": {"slug": fixture.slug},
                "model": {"pin": route.reviewer_model_id},
                "score": {},
            }
        ),
        encoding="utf-8",
    )

    def fail_runner(
        _route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        raise AssertionError("resume should not invoke provider")

    runs = qg_bakeoff.run_matrix([fixture], [route.reviewer_model_id], output_dir=tmp_path, runner=fail_runner)

    assert runs[0].skipped is True
    assert (tmp_path / qg_bakeoff.SCORECARD_NAME).exists()


def test_run_one_uses_scripted_runner_without_live_invocation(tmp_path: Path) -> None:
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/google/gemma-4-31b-it")
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

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _dispatch_result(payload, run_route)

    run = qg_bakeoff.run_one(route, fixture, output_dir=tmp_path, runner=runner)

    assert run.artifact["status"] == "ran"
    assert run.artifact["score"]["model_judgment_score"] == 30
    assert run.artifact["score"]["live_admissible_score"] == 30


def test_run_matrix_is_guarded_on_direct_programmatic_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cursor review of #4458 (blocker): run_matrix must enforce the opt-in itself."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("QG_BAKEOFF", raising=False)
    fixture = _fixture()

    def fail_runner(
        _route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        raise AssertionError("guard must fire before any provider invocation")

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="QG_BAKEOFF=1"):
        qg_bakeoff.run_matrix(
            [fixture],
            ["openrouter/google/gemma-4-31b-it"],
            output_dir=tmp_path,
            runner=fail_runner,
        )

    monkeypatch.setenv("QG_BAKEOFF", "1")
    monkeypatch.setenv("CI", "1")
    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="CI"):
        qg_bakeoff.run_matrix(
            [fixture],
            ["openrouter/google/gemma-4-31b-it"],
            output_dir=tmp_path,
            runner=fail_runner,
        )


def test_force_reruns_existing_artifact(tmp_path: Path) -> None:
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/google/gemma-4-31b-it")
    artifact_path = tmp_path / f"{qg_bakeoff.pin_slug(route.reviewer_model_id)}__{fixture.slug}.json"
    artifact_path.write_text(
        json.dumps(
            {
                "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
                "fixture": {"slug": fixture.slug},
                "model": {"pin": route.reviewer_model_id},
                "score": {},
            }
        ),
        encoding="utf-8",
    )
    calls: list[str] = []

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(run_route.reviewer_model_id)
        return _dispatch_result(
            {
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
            },
            run_route,
        )

    run = qg_bakeoff.run_one(route, fixture, output_dir=tmp_path, runner=runner, force=True)

    assert run.skipped is False
    assert calls, "force=True must re-invoke the runner despite the existing artifact"
    assert run.artifact["status"] == "ran"


def test_run_one_with_default_live_runner_is_guarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("QG_BAKEOFF", raising=False)
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/google/gemma-4-31b-it")

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="QG_BAKEOFF=1"):
        qg_bakeoff.run_one(route, _fixture(), output_dir=tmp_path)


def test_matrix_survives_schema_invalid_cell_and_retry_failures_reruns_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A schema-invalid model payload is a MEASURED error cell, never a matrix crash.

    First live run: gemma findings flunked validate_finding and killed all 24
    cells (ValueError propagated out of run_matrix). Error cells score as
    all-claims-missing; --retry-failures re-runs ONLY error cells.
    """
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
    calls: list[str] = []

    def flaky_runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(run_route.reviewer_model_id)
        if run_route.reviewer_model_id.endswith("bad-model"):
            raise ValueError("finding missing required fields: attribution")
        return _dispatch_result(
            {
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
            },
            run_route,
        )

    runs = qg_bakeoff.run_matrix(
        [fixture],
        ["openrouter/test/bad-model", "openrouter/test/good-model"],
        output_dir=tmp_path,
        runner=flaky_runner,
    )

    assert len(runs) == 2
    by_status = {run.artifact["model"]["pin"]: run.artifact["status"] for run in runs}
    assert by_status["openrouter/test/bad-model"] == "error"
    assert by_status["openrouter/test/good-model"] == "ran"
    error_artifact = next(r.artifact for r in runs if r.artifact["status"] == "error")
    assert error_artifact["error"]["class"] == "ValueError"
    assert error_artifact["score"]["missing_claims"] == len(fixture.claims)
    assert (tmp_path / qg_bakeoff.SCORECARD_NAME).exists()

    # resume: neither cell re-runs without flags
    calls.clear()
    qg_bakeoff.run_matrix(
        [fixture],
        ["openrouter/test/bad-model", "openrouter/test/good-model"],
        output_dir=tmp_path,
        runner=flaky_runner,
    )
    assert calls == []

    # --retry-failures: ONLY the error cell re-runs
    calls.clear()
    qg_bakeoff.run_matrix(
        [fixture],
        ["openrouter/test/bad-model", "openrouter/test/good-model"],
        output_dir=tmp_path,
        runner=flaky_runner,
        retry_failures=True,
    )
    assert calls == ["openrouter/test/bad-model"]


def test_retry_failures_still_runs_missing_cells_and_overwrites_error_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--retry-failures is a RESUME MODIFIER (codex review of #4463):

    missing cells run as in plain resume; error cells re-run and a successful
    retry OVERWRITES the error artifact.
    """
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
    good_payload = {
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
    fail_once = {"flaky": True}
    calls: list[str] = []

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(run_route.reviewer_model_id)
        if run_route.reviewer_model_id.endswith("flaky-model") and fail_once.pop("flaky", False):
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return _dispatch_result(good_payload, run_route)

    # Pass 1: flaky errors, fresh model absent entirely.
    runs = qg_bakeoff.run_matrix(
        [fixture], ["openrouter/test/flaky-model"], output_dir=tmp_path, runner=runner
    )
    assert runs[0].artifact["status"] == "error"

    # Pass 2 with retry_failures: error cell re-runs AND the missing fresh-model cell runs.
    calls.clear()
    runs = qg_bakeoff.run_matrix(
        [fixture],
        ["openrouter/test/flaky-model", "openrouter/test/fresh-model"],
        output_dir=tmp_path,
        runner=runner,
        retry_failures=True,
    )
    assert sorted(calls) == ["openrouter/test/flaky-model", "openrouter/test/fresh-model"]
    statuses = {run.artifact["model"]["pin"]: run.artifact["status"] for run in runs}
    assert statuses == {
        "openrouter/test/flaky-model": "ran",
        "openrouter/test/fresh-model": "ran",
    }


def test_error_artifact_preserves_response_head_for_parse_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()

    def prose_runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return llm_reviewer_dispatch.DispatchResult(
            response_text="Ой у лузі червона калина — no JSON here.",
            reviewer_model_id=run_route.reviewer_model_id,
            reviewer_family=run_route.reviewer_family,
            route_name=run_route.route_name,
            tool_call_count=1,
            tools_used=("sources_query_wikipedia",),
            tool_events=(
                {
                    "tool": "sources_query_wikipedia",
                    "input": {"query": "калина"},
                    "status": "completed",
                    "tool_call_id": "call_1",
                    "output": "калина",
                },
            ),
        )

    route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/prose-model")
    run = qg_bakeoff.run_one(route, fixture, output_dir=tmp_path, runner=prose_runner)

    assert run.artifact["status"] == "error"
    assert run.artifact["error"]["class"] == "BakeoffCellError"
    assert "червона калина" in run.artifact["error"]["response_head"]


def test_nonconforming_findings_counted_not_fatal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Findings-schema flunk is an ORTHOGONAL metric — fact_checks still score.

    Live gemma cells emitted valid fact_checks with findings missing the strict
    11 required fields; voiding those cells confounded the central fact-check
    measurement with contract-following noise.
    """
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
    payload = {
        "findings": [{"excerpt": "щось", "message": "bare finding, misses 11 fields"}],
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

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _dispatch_result(payload, run_route)

    route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/loose-findings-model")
    run = qg_bakeoff.run_one(route, fixture, output_dir=tmp_path, runner=runner)

    assert run.artifact["status"] != "error"
    assert run.artifact["findings_schema_invalid"] is True
    assert run.artifact["payload"]["findings"] == []
    assert run.artifact["score"]["model_judgment_score"] == 30

    # Invalid FACT_CHECKS remain a genuine error cell (regression guard).
    bad_facts = dict(payload, findings=[], fact_checks=[{"claim": "x", "verdict": "NOT_A_VERDICT"}])

    def bad_runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _dispatch_result(bad_facts, run_route)

    bad_route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/bad-facts-model")
    bad_run = qg_bakeoff.run_one(bad_route, fixture, output_dir=tmp_path, runner=bad_runner)
    assert bad_run.artifact["status"] == "error"


def test_trailing_garbage_after_valid_json_is_lenient_parsed_and_flagged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Live deepseek-v4-flash class: valid payload + trailing text ("Extra data")."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
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

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return llm_reviewer_dispatch.DispatchResult(
            response_text=json.dumps(payload) + "\n\nОсь мій аналіз повністю.",
            reviewer_model_id=run_route.reviewer_model_id,
            reviewer_family=run_route.reviewer_family,
            route_name=run_route.route_name,
            tool_call_count=1,
            tools_used=("sources_query_wikipedia",),
            tool_events=(_event(),),
        )

    route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/trailing-model")
    run = qg_bakeoff.run_one(route, fixture, output_dir=tmp_path, runner=runner)

    assert run.artifact["status"] != "error"
    assert run.artifact["response_parse_lenient"] is True
    assert run.artifact["score"]["model_judgment_score"] == 30

    # Pure prose still fails closed.
    def prose_runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return llm_reviewer_dispatch.DispatchResult(
            response_text="Жодного JSON тут немає.",
            reviewer_model_id=run_route.reviewer_model_id,
            reviewer_family=run_route.reviewer_family,
            route_name=run_route.route_name,
            tool_call_count=1,
            tools_used=("sources_query_wikipedia",),
            tool_events=(_event(),),
        )

    prose_route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/prose-only-model")
    prose_run = qg_bakeoff.run_one(prose_route, fixture, output_dir=tmp_path, runner=prose_runner)
    assert prose_run.artifact["status"] == "error"
