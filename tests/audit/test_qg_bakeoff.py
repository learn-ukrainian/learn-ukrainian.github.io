from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.audit import llm_reviewer_dispatch, qg_bakeoff, qg_factcheck_scoring, qg_schema


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


def _bare_dispatch_result(
    payload: dict[str, Any], route: llm_reviewer_dispatch.ReviewerRoute
) -> llm_reviewer_dispatch.DispatchResult:
    """A bare (tool-free) dispatch: no tool calls, no tool events, no grounding."""
    return llm_reviewer_dispatch.DispatchResult(
        response_text=json.dumps(payload, ensure_ascii=False),
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        tool_call_count=0,
        tools_used=(),
        tool_events=(),
    )


# The tooled reviewer output that passes theatre + grounding gates (CONFIRMED grounded,
# UNATTESTED grounded) → model judgment 30 for _fixture().
_TOOLED_GRODED_PAYLOAD: dict[str, Any] = {
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


def test_fixture_validation_rejects_duplicate_claim_id(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "slug": "bad",
                "title": "Bad",
                "passage_md": "a b",
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


def test_claim_matching_prefers_tightest_containing_row_over_first() -> None:
    """Containment must pick the most specific row, not the first in row order
    (codex review, PR #4485): a broad row with a different verdict must not
    shadow a tighter, more specific match."""
    fixture = qg_bakeoff.BakeoffFixture(
        slug="specific",
        title="Specific",
        passage_md="x",
        claims=(qg_bakeoff.FixtureClaim("m", "вінок пускали на воду.", False, "M", "real quote"),),
    )
    payload = {
        "fact_checks": [
            # Broad row FIRST (row-order trap): whole-paragraph quote, honest verdict.
            {
                "claim": "Дівчата плели вінки, вінок пускали на воду, а хлопці стрибали через вогонь.",
                "verdict": "UNATTESTED_AFTER_SEARCH",
            },
            # Tighter row SECOND: sentence-level quote, endorses the fabrication.
            {"claim": "Вінок пускали на воду, співаючи.", "verdict": "CONFIRMED"},
        ]
    }

    score = qg_bakeoff.score_payload(payload, fixture)

    assert score["missing_claims"] == 0
    (per_claim,) = score["claims"]
    assert per_claim["model_claim"] == "Вінок пускали на воду, співаючи."
    # CONFIRMED on a fabricated claim = the fatal endorsement constant.
    assert per_claim["model_judgment_points"] == qg_factcheck_scoring.score_verdict(
        "CONFIRMED", claim_is_true=False
    )


def test_negative_verdict_on_shared_sentence_does_not_refute_true_subclaim() -> None:
    """A REFUTED row for a compound sentence (one true + one fabricated
    sub-claim) targets the fabricated part; the true sub-claim must count
    missing (−10), never refuted-true (−50) (codex review, PR #4485)."""
    fixture = qg_bakeoff.BakeoffFixture(
        slug="compound",
        title="Compound",
        passage_md="x",
        claims=(
            qg_bakeoff.FixtureClaim("t", "Веснянки співали навесні.", True),
            qg_bakeoff.FixtureClaim("f", "лише чоловіки у шкіряних масках.", False, "M", "real quote"),
        ),
    )
    compound = "Веснянки співали навесні лише чоловіки у шкіряних масках."
    payload = {"fact_checks": [{"claim": compound, "verdict": "REFUTED_BY_CONTRADICTION"}]}

    score = qg_bakeoff.score_payload(payload, fixture)

    by_id = {row["claim_id"]: row for row in score["claims"]}
    # Fabricated sub-claim: refutation transfers (the model caught it).
    assert by_id["f"]["matched"] is True
    assert by_id["f"]["model_judgment_points"] == qg_factcheck_scoring.score_verdict(
        "REFUTED_BY_CONTRADICTION", claim_is_true=False
    )
    # True sub-claim: the negative verdict must NOT transfer — missing, not refuted.
    assert by_id["t"]["matched"] is False
    assert by_id["t"]["reason"] == "missing_claim"
    assert by_id["t"]["model_judgment_points"] == qg_bakeoff.MISSING_CLAIM_PENALTY
    # A CONFIRMED compound row still transfers to the true sub-claim.
    confirmed = {"fact_checks": [{"claim": compound, "verdict": "CONFIRMED"}]}
    score2 = qg_bakeoff.score_payload(confirmed, fixture)
    by_id2 = {row["claim_id"]: row for row in score2["claims"]}
    assert by_id2["t"]["matched"] is True
    assert by_id2["f"]["model_judgment_points"] == qg_factcheck_scoring.score_verdict(
        "CONFIRMED", claim_is_true=False
    )


def test_model_pins_reject_whitespace_mega_pin() -> None:
    """A space-separated --models string must fail fast, not run garbage cells
    (live burn 2026-07-05: one mega-pin ran 4 junk artifacts)."""
    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="whitespace"):
        qg_bakeoff.model_pins_from_args(["pin/a pin/b pin/c"])
    assert qg_bakeoff.model_pins_from_args(["pin/a,pin/b"]) == ["pin/a", "pin/b"]


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
    assert run.artifact["arm"] == "tooled"
    assert run.artifact_path.name.endswith("__sample.json")
    assert not run.artifact_path.name.endswith("__bare.json")
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


def test_containment_matching_maps_sentence_quotes_to_subspan_claims(tmp_path: Path) -> None:
    """Models quote passage SENTENCES; fixture claims are sub-spans (live finding)."""
    fixture = qg_bakeoff.BakeoffFixture(
        slug="contain",
        title="Containment",
        passage_md="x",
        claims=(
            qg_bakeoff.FixtureClaim(claim_id="c-true", claim="Колядки — величальна поезія українського народу.", is_true=True),
            qg_bakeoff.FixtureClaim(
                claim_id="c-m",
                claim="Обходи очолювали заміжні жінки.",
                is_true=False,
                fabrication_class="M",
                distractor_evidence="жінкам колядувати заборонено",
            ),
        ),
    )
    payload = {
        "fact_checks": [
            {
                # ONE sentence-quote covering BOTH sub-claims → verdict applies to each.
                "claim": "Колядки — величальна поезія українського народу, а обходи очолювали заміжні жінки.",
                "verdict": "CONFIRMED",
            },
        ]
    }
    score = qg_bakeoff.score_payload(payload, fixture)
    assert score["missing_claims"] == 0
    by_id = {c["claim_id"]: c for c in score["claims"]}
    assert by_id["c-true"]["model_judgment_points"] == 20
    assert by_id["c-m"]["model_judgment_points"] == -100  # confirming the sentence = confirming the fabrication


def test_rescore_recomputes_from_stored_payloads_without_model_calls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
    # a stored artifact whose payload quotes the WHOLE sentence (old matcher → missing)
    artifact = {
        "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
        "fixture": {"slug": fixture.slug, "title": fixture.title, "claim_count": len(fixture.claims)},
        "model": {"pin": "openrouter/test/m", "pin_slug": "openrouter-test-m", "family": "test", "route_name": "bakeoff_test", "bridge_command": []},
        "status": "ran",
        "workflow_verdict": "PASS",
        "attempt_count": 1,
        "dispatch": {},
        "gate_outcomes": {"grounding": {"invalid_fact_checks": 0, "inadmissible_positive_verdicts": 0}},
        "payload": {
            "fact_checks": [
                {"claim": "True claim. Додаткові слова навколо.", "verdict": "CONFIRMED"},
                {"claim": "Fabricated claim. Ще слова.", "verdict": "UNATTESTED_AFTER_SEARCH"},
            ]
        },
        "score": {"model_judgment_score": -999},
        "tool_call_count": 1,
        "wall_seconds": 1.0,
    }
    fixtures_dir = tmp_path / "fx"
    fixtures_dir.mkdir()
    (fixtures_dir / f"{fixture.slug}.json").write_text(
        json.dumps(
            {
                "slug": fixture.slug,
                "title": fixture.title,
                "passage_md": fixture.passage_md,
                "claims": [
                    {
                        "claim_id": c.claim_id,
                        "claim": c.claim,
                        "is_true": c.is_true,
                        "fabrication_class": c.fabrication_class,
                        "distractor_evidence": c.distractor_evidence,
                    }
                    for c in fixture.claims
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()
    (out / "openrouter-test-m__anchor.json").write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")

    n = qg_bakeoff.rescore_artifacts(out, fixtures_dir)

    assert n == 1
    updated = json.loads((out / "openrouter-test-m__anchor.json").read_text(encoding="utf-8"))
    assert updated["score"]["model_judgment_score"] == 30  # 20 + 10, containment matched
    assert updated["score"]["missing_claims"] == 0
    assert "rescored_at" in updated
    assert (out / qg_bakeoff.SCORECARD_NAME).exists()


# --- Bare control arm (#2156 step 3: harness-lift measurement) --------------


def test_bare_prompt_reuses_taxonomy_verbatim_without_tool_mandate() -> None:
    """Bare prompt: same verdict taxonomy (so scoring is identical) but NO tool mandate."""
    prompt = qg_bakeoff.build_bare_factcheck_prompt("Веснянки", "Spring songs. Гаї shown.")

    # The verdict set is reused VERBATIM from the live reviewer template — no fork.
    assert qg_bakeoff._reviewer_verdict_taxonomy() in prompt
    for verdict in qg_schema.FACT_CHECK_VERDICTS:
        assert verdict in prompt

    # Same JSON contract (fact_checks with claim + verdict, literal spans).
    assert "fact_checks" in prompt
    assert "verbatim span" in prompt

    # No tool/search/grounding MANDATE (those tooled sections must be absent).
    assert "Required Search Protocol" not in prompt
    assert "Tool Budget" not in prompt
    assert "at most 3 tool calls" not in prompt
    # Bare explicitly permits the can't-verify verdict and judges from own knowledge.
    assert "UNVERIFIED_INSUFFICIENT_SEARCH" in prompt
    assert "own knowledge" in prompt
    assert "ignored by bare scoring" in prompt


def test_bare_run_skips_gates_confirmed_without_grounding_passes(tmp_path: Path) -> None:
    """A payload that WOULD fail the tooled theatre/grounding gates passes bare.

    CONFIRMED with NO grounding and ZERO tool calls trips tooled theatre; bare has
    no gates by design, so it is scored on model judgment alone.
    """
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/google/gemma-4-31b-it")
    payload = {
        "fact_checks": [
            {"claim": "True claim.", "verdict": "CONFIRMED"},
            {"claim": "Fabricated claim.", "verdict": "UNATTESTED_AFTER_SEARCH"},
        ]
    }

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _bare_dispatch_result(payload, run_route)

    run = qg_bakeoff.run_one_bare(route, fixture, output_dir=tmp_path, runner=runner)

    assert run.artifact["status"] == "ran"
    assert run.artifact["arm"] == "bare"
    assert run.artifact["workflow_verdict"] == "BARE"
    assert run.artifact["gate_outcomes"] == {}
    assert run.artifact["tool_call_count"] == 0
    assert run.artifact_path.name.endswith("__bare__opencode.json")
    # CONFIRMED-on-true (+20) + UNATTESTED-on-fabricated (+10) = 30, same scorer as tooled.
    assert run.artifact["score"]["model_judgment_score"] == 30
    assert run.artifact["score"]["invalid_fact_checks"] == 0
    assert run.artifact["score"]["inadmissible_positive_verdicts"] == 0


def test_bare_strips_nonconforming_findings_and_still_scores(tmp_path: Path) -> None:
    """Findings are orthogonal to the bare fact-check measurement: stripped + flagged."""
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/bare-findings")
    payload = {
        "findings": [{"excerpt": "щось", "message": "bare finding, misses required fields"}],
        "fact_checks": [
            {"claim": "True claim.", "verdict": "CONFIRMED"},
            {"claim": "Fabricated claim.", "verdict": "UNATTESTED_AFTER_SEARCH"},
        ],
    }

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _bare_dispatch_result(payload, run_route)

    run = qg_bakeoff.run_one_bare(route, fixture, output_dir=tmp_path, runner=runner)

    assert run.artifact["status"] == "ran"
    assert run.artifact["findings_schema_invalid"] is True
    assert run.artifact["payload"]["findings"] == []
    assert run.artifact["score"]["model_judgment_score"] == 30


def test_bare_invalid_fact_checks_is_error_cell(tmp_path: Path) -> None:
    """An out-of-taxonomy verdict is a real error cell (score = every claim missing)."""
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/bad-bare")

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _bare_dispatch_result({"fact_checks": [{"claim": "x", "verdict": "NOPE"}]}, run_route)

    run = qg_bakeoff.run_one_bare(route, fixture, output_dir=tmp_path, runner=runner)

    assert run.artifact["status"] == "error"
    assert run.artifact["arm"] == "bare"
    assert run.artifact["score"]["missing_claims"] == len(fixture.claims)


def test_run_one_bare_with_default_runner_is_guarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("QG_BAKEOFF", raising=False)
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/google/gemma-4-31b-it")

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="QG_BAKEOFF=1"):
        qg_bakeoff.run_one_bare(route, _fixture(), output_dir=tmp_path)


def test_subscription_runtime_bare_invokes_agent_runtime_with_bare_claude_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route = qg_bakeoff.route_for_matrix_pin(
        qg_bakeoff.CLAUDE_SUBSCRIPTION_BARE_MODEL_ID,
        arm=qg_bakeoff.BARE_ARM,
    )
    calls: list[dict[str, Any]] = []

    def fake_invoke(agent_name: str, prompt: str, **kwargs: Any) -> SimpleNamespace:
        calls.append({"agent_name": agent_name, "prompt": prompt, **kwargs})
        return SimpleNamespace(
            ok=True,
            response=json.dumps({"fact_checks": []}),
            rate_limited=False,
            returncode=0,
            stderr_excerpt=None,
            usage_record={"model": "claude-opus-resolved"},
            cli_version="claude-code 2.2.0",
            agent=agent_name,
            model="claude-opus-resolved",
            tool_calls=[],
            tool_calls_total=0,
        )

    monkeypatch.setattr("scripts.agent_runtime.runner.invoke", fake_invoke)

    result = qg_bakeoff.invoke_subscription_bare_route(route, "bare prompt", "task-1")

    assert result.response_text == json.dumps({"fact_checks": []})
    assert calls == [
        {
            "agent_name": "claude",
            "prompt": "bare prompt",
            "mode": "read-only",
            "cwd": qg_bakeoff._neutral_runtime_cwd(),
            "model": qg_bakeoff.CLAUDE_SUBSCRIPTION_BARE_MODEL_ID,
            "task_id": "task-1",
            "session_id": None,
            # use_bare=False is load-bearing: `claude --bare` bypasses the
            # OAuth session and demands ANTHROPIC_API_KEY — on the
            # subscription machine it fails "Not logged in" (2026-07-06 probe).
            "tool_config": {"use_bare": False, "output_format": "stream-json"},
            "entrypoint": qg_bakeoff.BARE_RUNTIME_ENTRYPOINT,
            "hard_timeout": 1800,
            "stall_timeout": 600,
        }
    ]
    assert result.usage and result.usage["cli_version"] == "claude-code 2.2.0"
    assert result.usage["resolved_model"] == "claude-opus-resolved"
    assert result.usage["cwd_policy"] == "neutral-tmp"


def test_subscription_runtime_bare_cwd_is_outside_the_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Standing-rules firewall: bare cells must NEVER run from inside the repo.

    Agent CLIs walk up from cwd to load CLAUDE.md / AGENTS.md / GEMINI.md —
    a cwd under PROJECT_ROOT injects project standing rules into a
    measurement that promises a bare prompt (caught live 2026-07-06: the
    gpt/gemini cells ran with repo rules in context).
    """
    seen_cwds: list[Path] = []

    def fake_invoke(agent_name: str, prompt: str, **kwargs: Any) -> SimpleNamespace:
        seen_cwds.append(Path(kwargs["cwd"]))
        return SimpleNamespace(
            ok=True,
            response=json.dumps({"fact_checks": []}),
            rate_limited=False,
            returncode=0,
            stderr_excerpt=None,
            usage_record={},
            cli_version="x",
            agent=agent_name,
            model="m",
            tool_calls=[],
            tool_calls_total=0,
        )

    monkeypatch.setattr("scripts.agent_runtime.runner.invoke", fake_invoke)
    for pin in (
        qg_bakeoff.CLAUDE_SUBSCRIPTION_BARE_MODEL_ID,
        qg_bakeoff.GPT_SUBSCRIPTION_BARE_MODEL_ID,
        qg_bakeoff.GEMINI_SUBSCRIPTION_BARE_MODEL_ID,
    ):
        route = qg_bakeoff.route_for_matrix_pin(pin, arm=qg_bakeoff.BARE_ARM)
        qg_bakeoff.invoke_subscription_bare_route(route, "bare prompt", f"task-{pin}")

    assert len(seen_cwds) == 3
    repo_root = qg_bakeoff.PROJECT_ROOT.resolve()
    for cwd in seen_cwds:
        resolved = cwd.resolve()
        assert resolved != repo_root
        assert not resolved.is_relative_to(repo_root)


def test_subscription_runtime_bare_artifact_identity_and_filename(tmp_path: Path) -> None:
    fixture = _fixture()
    route = qg_bakeoff.route_for_matrix_pin(
        qg_bakeoff.GPT_SUBSCRIPTION_BARE_MODEL_ID,
        arm=qg_bakeoff.BARE_ARM,
    )
    payload = {
        "fact_checks": [
            {"claim": "True claim.", "verdict": "CONFIRMED"},
            {"claim": "Fabricated claim.", "verdict": "UNATTESTED_AFTER_SEARCH"},
        ]
    }

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return llm_reviewer_dispatch.DispatchResult(
            response_text=json.dumps(payload),
            reviewer_model_id=run_route.reviewer_model_id,
            reviewer_family=run_route.reviewer_family,
            route_name=run_route.route_name,
            usage={"model": "gpt-5.5-resolved", "cli_version": "codex 1.0.0"},
        )

    run = qg_bakeoff.run_one_bare(route, fixture, output_dir=tmp_path, runner=runner)

    assert run.artifact_path.name == "gpt-5-5__sample__bare__runtime-codex.json"
    assert route.input_usd_per_mtok == 0.0
    assert route.output_usd_per_mtok == 0.0
    model = run.artifact["model"]
    assert model["route_name"] == "bare_runtime_gpt"
    assert model["transport"] == "runtime-codex"
    assert model["entrypoint"] == qg_bakeoff.BARE_RUNTIME_ENTRYPOINT
    assert model["session_policy"] == "fresh"
    assert model["measurement_tier"] == qg_bakeoff.SUBSCRIPTION_RUNTIME_BARE_TIER
    assert model["cli_version"] == "codex 1.0.0"
    assert model["resolved_model"] == "gpt-5.5-resolved"
    assert model["pricing_basis"].startswith("subscription runtime bare seat")
    assert model["bridge_command"][0] == "agent_runtime.invoke"
    assert all(not str(part).startswith("ask-") for part in model["bridge_command"])


def test_subscription_native_pins_are_refused_for_tooled_or_both() -> None:
    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="bare-only"):
        qg_bakeoff.route_for_matrix_pin(
            qg_bakeoff.GPT_SUBSCRIPTION_BARE_MODEL_ID,
            arm=qg_bakeoff.TOOLED_ARM,
        )
    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="bare-only"):
        qg_bakeoff.route_for_matrix_pin(
            qg_bakeoff.GEMINI_SUBSCRIPTION_BARE_MODEL_ID,
            arm=qg_bakeoff.BOTH_ARM,
        )


def test_bare_transport_retry_once_and_records_attempts(tmp_path: Path) -> None:
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/flaky-transport")
    calls = 0
    payload = {
        "fact_checks": [
            {"claim": "True claim.", "verdict": "CONFIRMED"},
            {"claim": "Fabricated claim.", "verdict": "UNATTESTED_AFTER_SEARCH"},
        ]
    }

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise llm_reviewer_dispatch.ReviewerProviderError("connection reset")
        return _bare_dispatch_result(payload, run_route)

    run = qg_bakeoff.run_one_bare(route, fixture, output_dir=tmp_path, runner=runner)

    assert calls == 2
    assert run.artifact["status"] == "ran"
    assert run.artifact["attempt_count"] == 2
    assert run.artifact["transport_retry"] == {"attempted": True, "reason": "connection reset"}
    assert run.artifact["timed_out"] is False


def test_bare_parse_failure_does_not_retry_and_is_model_failure(tmp_path: Path) -> None:
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/prose")
    calls = 0

    def runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return llm_reviewer_dispatch.DispatchResult(
            response_text="No JSON here.",
            reviewer_model_id=run_route.reviewer_model_id,
            reviewer_family=run_route.reviewer_family,
            route_name=run_route.route_name,
        )

    run = qg_bakeoff.run_one_bare(route, fixture, output_dir=tmp_path, runner=runner)

    assert calls == 1
    assert run.artifact["status"] == "error"
    assert run.artifact["failure_class"] == qg_bakeoff.FAILURE_CLASS_MODEL_FAILURE
    assert run.artifact["attempt_count"] == 1
    assert run.artifact["transport_retry"] == {"attempted": False, "reason": None}


def test_bare_resume_transport_mismatch_hard_fails(tmp_path: Path) -> None:
    fixture = _fixture()
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/google/gemma-4-31b-it")
    artifact_path = qg_bakeoff._bare_artifact_path(tmp_path, route, fixture)
    artifact_path.write_text(
        json.dumps(
            {
                "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
                "arm": qg_bakeoff.BARE_ARM,
                "fixture": {"slug": fixture.slug},
                "model": {"pin": route.reviewer_model_id, "transport": "runtime-codex"},
                "status": "ran",
                "score": {},
            }
        ),
        encoding="utf-8",
    )

    def runner(*_args: Any, **_kwargs: Any) -> llm_reviewer_dispatch.DispatchResult:  # pragma: no cover
        raise AssertionError("transport mismatch must fail before invocation")

    with pytest.raises(qg_bakeoff.BakeoffConfigError, match="transport"):
        qg_bakeoff.run_one_bare(route, fixture, output_dir=tmp_path, runner=runner)


def test_arm_both_runs_tooled_and_bare_cells_and_scorecard_shows_lift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--arm both runs 2 cells per pair; the scorecard carries the harness-lift column.

    Bare CONFIRMS the fabrication (rationalizes without sources: −80) while the tooled
    reviewer catches it (+30) → harness_lift = 30 − (−80) = 110, the pitch headline.
    """
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
    bare_payload = {
        "fact_checks": [
            {"claim": "True claim.", "verdict": "CONFIRMED"},
            {"claim": "Fabricated claim.", "verdict": "CONFIRMED"},
        ]
    }

    def tooled_runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _dispatch_result(_TOOLED_GRODED_PAYLOAD, run_route)

    def bare_runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _bare_dispatch_result(bare_payload, run_route)

    runs = qg_bakeoff.run_matrix(
        [fixture],
        ["openrouter/google/gemma-4-31b-it"],
        output_dir=tmp_path,
        runner=tooled_runner,
        bare_runner=bare_runner,
        arm="both",
    )

    assert sorted(run.artifact["arm"] for run in runs) == ["bare", "tooled"]
    names = sorted(p.name for p in tmp_path.glob("*.json"))
    assert any(n.endswith("__bare__opencode.json") for n in names)
    assert any(n.endswith("__sample.json") for n in names)

    scorecard = (tmp_path / qg_bakeoff.SCORECARD_NAME).read_text(encoding="utf-8")
    assert "| model | transport | entrypoint | passage | arm |" in scorecard
    assert "Harness Lift With Anchor" in scorecard
    assert "harness_lift" in scorecard
    assert "| 110 |" in scorecard  # tooled 30 − bare (−80)


def test_harness_lift_computed_over_paired_cells_only() -> None:
    """Unpaired fixtures must not leak into the lift (codex review, PR #4500
    finding 1): tooled has fixtures a+b, bare only a → lift uses a alone."""

    def _artifact(slug: str, arm: str, mj: int) -> dict:
        return {
            "model": {"pin": "pin/x"},
            "fixture": {"slug": slug},
            "arm": arm,
            "score": {
                "model_judgment_score": mj,
                "fractions": {"class_m_alignment": {"numerator": 1, "denominator": 2}},
            },
        }

    lines = qg_bakeoff._harness_lift_section(
        "Test",
        [
            _artifact("a", "tooled", 30),
            _artifact("b", "tooled", 150),  # unpaired — must NOT count
            _artifact("a", "bare", -80),
        ],
    )
    row = next(line for line in lines if line.startswith("| pin/x"))
    # paired=1, tooled=30 (not 180), bare=-80, lift=110
    assert row.split("|")[2].strip() == "1"
    assert "| 30 |" in row
    assert "| 110 |" in row
    assert "180" not in row

    # Zero paired fixtures → n/a, never a fabricated number.
    lines = qg_bakeoff._harness_lift_section("Test", [_artifact("a", "tooled", 30)])
    row = next(line for line in lines if line.startswith("| pin/x"))
    assert "n/a" in row and "30" not in row.replace("| 0 |", "")


def test_harness_lift_key_includes_transport_and_entrypoint() -> None:
    """Same pin + fixture but different transport must never fabricate a pair."""

    def _artifact(transport: str, entrypoint: str, arm: str, mj: int) -> dict:
        return {
            "model": {
                "pin": "same/pin",
                "transport": transport,
                "entrypoint": entrypoint,
            },
            "fixture": {"slug": "same-fixture"},
            "arm": arm,
            "score": {
                "model_judgment_score": mj,
                "fractions": {"class_m_alignment": {"numerator": 1, "denominator": 1}},
            },
        }

    lines = qg_bakeoff._harness_lift_section(
        "Test",
        [
            _artifact("opencode", "qg_bakeoff_opencode", "tooled", 30),
            _artifact("runtime-codex", "qg_bakeoff_runtime", "bare", -80),
        ],
    )

    rows = [line for line in lines if line.startswith("| same/pin")]
    assert len(rows) == 2
    assert all("| 0 | n/a | n/a | n/a |" in row for row in rows)
    assert not any("| 110 |" in row for row in rows)


def test_ops_quota_error_cells_are_excluded_from_judgment_aggregates() -> None:
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/quota")
    artifact = qg_bakeoff._error_artifact(
        route,
        _fixture(),
        qg_bakeoff.BakeoffOpsQuotaError("no headroom"),
        0.1,
        arm=qg_bakeoff.BARE_ARM,
    )

    assert artifact["failure_class"] == qg_bakeoff.FAILURE_CLASS_OPS_QUOTA
    assert qg_bakeoff._aggregate_by_model_arm([artifact]) == {}
    lines = qg_bakeoff._harness_lift_section("Test", [artifact])
    assert not any(line.startswith("| openrouter/test/quota") for line in lines)


def test_run_matrix_preflights_pins_against_routing_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A subscription-family pin must fail the matrix at config time — before
    any cell runs (codex review, PR #4500 finding 2)."""
    from scripts.ai_agent_bridge.routing_guard import RoutingGuardError

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("LU_ROUTING_GUARD_OVERRIDE", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    calls = 0

    def runner(*args, **kwargs):  # pragma: no cover - must never run
        nonlocal calls
        calls += 1
        raise AssertionError("runner must not fire for a guarded pin")

    with pytest.raises(RoutingGuardError):
        qg_bakeoff.run_matrix(
            [_fixture()],
            ["openrouter/anthropic/claude-sonnet-5"],
            output_dir=tmp_path,
            runner=runner,
            bare_runner=runner,
            arm="both",
        )
    assert calls == 0
    assert not list(tmp_path.glob("*.json"))


def test_reviewer_opencode_transport_is_guarded(monkeypatch: pytest.MonkeyPatch) -> None:
    """The reviewer dispatch runs its OWN opencode invocation (not the bridge's
    guarded _run_opencode) — the guard must sit at this transport too."""
    from scripts.ai_agent_bridge.routing_guard import RoutingGuardError

    monkeypatch.delenv("LU_ROUTING_GUARD_OVERRIDE", raising=False)
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/openai/gpt-5.5")
    with pytest.raises(RoutingGuardError):
        llm_reviewer_dispatch._invoke_opencode_reviewer(
            "prompt", route, default_timeout_s=1, require_mcp=False
        )


def test_bare_strips_gate_only_fields_before_scoring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A bare model self-emitting admissibility_downgraded/original_verdict must
    not split the judgment/live columns (codex review, PR #4500 finding 3): no
    bare gate produced those fields, so they are stripped before scoring."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()
    gamed_payload = {
        "fact_checks": [
            {"claim": "True claim.", "verdict": "CONFIRMED"},
            {
                # Gaming attempt: CONFIRMED live verdict, honest-looking
                # "downgraded" judgment verdict.
                "claim": "Fabricated claim.",
                "verdict": "CONFIRMED",
                "admissibility_downgraded": True,
                "original_verdict": "UNATTESTED_AFTER_SEARCH",
            },
        ]
    }

    def bare_runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _bare_dispatch_result(gamed_payload, run_route)

    run = qg_bakeoff.run_one_bare(
        qg_bakeoff.bakeoff_route_for_model("openrouter/google/gemma-4-31b-it"),
        fixture,
        output_dir=tmp_path,
        runner=bare_runner,
    )

    score = run.artifact["score"]
    # Both columns score the emitted verdict: CONFIRMED on the fabrication.
    assert score["model_judgment_score"] == score["live_admissible_score"]
    by_id = {row["claim_id"]: row for row in score["claims"]}
    assert by_id["c-false"]["model_judgment_verdict"] == "CONFIRMED"
    # The persisted payload rows carry ONLY claim + verdict.
    for row in run.artifact["payload"]["fact_checks"]:
        assert sorted(row) == ["claim", "verdict"]


def test_arm_bare_after_tooled_scorecard_keeps_both_arms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Running one arm rebuilds the scorecard from ALL artifacts on disk (both arms)."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    fixture = _fixture()

    def tooled_runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _dispatch_result(_TOOLED_GRODED_PAYLOAD, run_route)

    def bare_runner(
        run_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return _bare_dispatch_result(
            {"fact_checks": [{"claim": "True claim.", "verdict": "CONFIRMED"}]}, run_route
        )

    pins = ["openrouter/google/gemma-4-31b-it"]
    qg_bakeoff.run_matrix([fixture], pins, output_dir=tmp_path, runner=tooled_runner, arm="tooled")
    qg_bakeoff.run_matrix([fixture], pins, output_dir=tmp_path, bare_runner=bare_runner, arm="bare")

    scorecard = (tmp_path / qg_bakeoff.SCORECARD_NAME).read_text(encoding="utf-8")
    # both arms appear in the totals even though only bare ran last.
    assert "| tooled |" in scorecard
    assert "| bare |" in scorecard


def test_rescore_covers_both_arms_and_backfills_arm(tmp_path: Path) -> None:
    """Rescore recomputes BOTH arms and backfills ``arm`` on legacy tooled artifacts."""
    fixture = _fixture()
    fixtures_dir = tmp_path / "fx"
    fixtures_dir.mkdir()
    (fixtures_dir / f"{fixture.slug}.json").write_text(
        json.dumps(
            {
                "slug": fixture.slug,
                "title": fixture.title,
                "passage_md": fixture.passage_md,
                "claims": [
                    {
                        "claim_id": c.claim_id,
                        "claim": c.claim,
                        "is_true": c.is_true,
                        "fabrication_class": c.fabrication_class,
                        "distractor_evidence": c.distractor_evidence,
                    }
                    for c in fixture.claims
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()
    # legacy tooled artifact: NO arm field, stale score.
    (out / "m__sample.json").write_text(
        json.dumps(
            {
                "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
                "fixture": {"slug": fixture.slug, "title": fixture.title, "claim_count": 2},
                "model": {"pin": "openrouter/test/m"},
                "gate_outcomes": {"grounding": {"invalid_fact_checks": 0, "inadmissible_positive_verdicts": 0}},
                "payload": {
                    "fact_checks": [
                        {"claim": "True claim.", "verdict": "CONFIRMED"},
                        {"claim": "Fabricated claim.", "verdict": "UNATTESTED_AFTER_SEARCH"},
                    ]
                },
                "score": {"model_judgment_score": -999},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    # bare artifact: arm=bare, no gate_outcomes at all.
    (out / "m__sample__bare.json").write_text(
        json.dumps(
            {
                "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
                "arm": "bare",
                "fixture": {"slug": fixture.slug, "title": fixture.title, "claim_count": 2},
                "model": {"pin": "openrouter/test/m"},
                "payload": {
                    "fact_checks": [
                        {"claim": "True claim.", "verdict": "CONFIRMED"},
                        {"claim": "Fabricated claim.", "verdict": "CONFIRMED"},
                    ]
                },
                "score": {"model_judgment_score": -999},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Foreign JSON in the out-dir (the live trap: a tier2-canary-verdict.json
    # written by the canary checker) — rescore must SKIP it entirely, not
    # fabricate an 'unknown' scorecard row with a phantom passage count.
    (out / "tier2-canary-verdict.json").write_text(
        json.dumps(
            {
                "schema_version": "qg_tier2_canary_verdict.v1",
                "passed": True,
                "failure_reasons": [],
                "summary": {"artifact_count": 4},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    n = qg_bakeoff.rescore_artifacts(out, fixtures_dir)

    assert n == 2
    tooled = json.loads((out / "m__sample.json").read_text(encoding="utf-8"))
    bare = json.loads((out / "m__sample__bare.json").read_text(encoding="utf-8"))
    assert tooled["arm"] == "tooled"  # backfilled
    assert bare["arm"] == "bare"  # preserved
    assert tooled["score"]["model_judgment_score"] == 30  # 20 + 10
    assert bare["score"]["model_judgment_score"] == -80  # 20 + (−100) CONFIRMED-on-fabricated
    assert bare["score"]["invalid_fact_checks"] == 0
    scorecard = (out / qg_bakeoff.SCORECARD_NAME).read_text(encoding="utf-8")
    assert "Harness Lift With Anchor" in scorecard
    assert "| unknown [" not in scorecard  # foreign JSON never becomes a model row
    verdict_after = json.loads((out / "tier2-canary-verdict.json").read_text(encoding="utf-8"))
    assert "rescored_at" not in verdict_after  # untouched, not rewritten
