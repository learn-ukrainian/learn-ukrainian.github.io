from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import llm_reviewer_dispatch, qg_bakeoff

PIN = "openrouter/test/emitter-model"
CREATED_AT = "2026-07-06T12:34:56Z"


def _fixture() -> qg_bakeoff.BakeoffFixture:
    return qg_bakeoff.BakeoffFixture(
        slug="emitter",
        title="Emitter",
        passage_md="True claim. U fabricated claim. M fabricated claim.",
        claims=(
            qg_bakeoff.FixtureClaim("true", "True claim.", True),
            qg_bakeoff.FixtureClaim("u", "U fabricated claim.", False, "U"),
            qg_bakeoff.FixtureClaim("m", "M fabricated claim.", False, "M", "real adjacent quote"),
        ),
    )


def _write_fixture(fixtures_dir: Path, fixture: qg_bakeoff.BakeoffFixture) -> None:
    fixtures_dir.mkdir()
    (fixtures_dir / f"{fixture.slug}.json").write_text(
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
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _event() -> dict[str, Any]:
    return {
        "tool": "sources_query_wikipedia",
        "input": {"query": "fixture", "mode": "section"},
        "status": "completed",
        "tool_call_id": "call_1",
        "output": "True claim. U fabricated claim. M fabricated claim.",
    }


def _dispatch_result(
    payload: dict[str, Any],
    route: llm_reviewer_dispatch.ReviewerRoute,
    *,
    tool_call_count: int,
) -> llm_reviewer_dispatch.DispatchResult:
    return llm_reviewer_dispatch.DispatchResult(
        response_text=json.dumps(payload, ensure_ascii=False),
        reviewer_model_id=route.reviewer_model_id,
        reviewer_family=route.reviewer_family,
        route_name=route.route_name,
        tool_call_count=tool_call_count,
        tools_used=("sources_query_wikipedia",) if tool_call_count else (),
        tool_events=(_event(),) if tool_call_count else (),
    )


def _tooled_runner(
    route: llm_reviewer_dispatch.ReviewerRoute,
    _prompt: str,
    _task_id: str,
) -> llm_reviewer_dispatch.DispatchResult:
    payload = {
        "findings": [],
        "fact_checks": [
            {
                "claim": "True claim.",
                "verdict": "CONFIRMED",
                "grounding": {
                    "tool": "sources_query_wikipedia",
                    "query": "fixture",
                    "evidence_excerpt": "True claim.",
                    "tool_call_id": "call_1",
                },
            },
            {
                "claim": "U fabricated claim.",
                "verdict": "UNATTESTED_AFTER_SEARCH",
                "grounding": {
                    "tool": "sources_query_wikipedia",
                    "query": "fixture",
                    "evidence_excerpt": "U fabricated claim.",
                    "tool_call_id": "call_1",
                },
            },
            {
                "claim": "M fabricated claim.",
                "verdict": "UNATTESTED_AFTER_SEARCH",
                "grounding": {
                    "tool": "sources_query_wikipedia",
                    "query": "fixture",
                    "evidence_excerpt": "M fabricated claim.",
                    "tool_call_id": "call_1",
                },
            },
        ],
        "evidence_gaps": [],
    }
    return _dispatch_result(payload, route, tool_call_count=1)


def _bare_runner(
    route: llm_reviewer_dispatch.ReviewerRoute,
    _prompt: str,
    _task_id: str,
) -> llm_reviewer_dispatch.DispatchResult:
    payload = {
        "findings": [],
        "fact_checks": [
            {"claim": "True claim.", "verdict": "CONFIRMED"},
            {"claim": "U fabricated claim.", "verdict": "CONFIRMED"},
            {"claim": "M fabricated claim.", "verdict": "CONFIRMED"},
        ],
        "evidence_gaps": [],
    }
    return _dispatch_result(payload, route, tool_call_count=0)


def _load_lang_uk_leaderboard_records(path: Path) -> list[dict[str, Any]]:
    """Minimal lang-uk loader contract: model_name plus float metrics per task."""
    data = json.loads(path.read_text(encoding="utf-8"))
    config_general = data["config_general"]
    assert isinstance(config_general["model_name"], str)
    results = data["results"]
    assert isinstance(results, dict)

    records: list[dict[str, Any]] = []
    for task_name, metrics in results.items():
        assert isinstance(task_name, str)
        assert isinstance(metrics, dict)
        for metric_name, value in metrics.items():
            if metric_name == "qg_meta":
                assert isinstance(value, dict)
                continue
            assert isinstance(value, int | float)
            assert not isinstance(value, bool)
            records.append(
                {
                    "model_name": config_general["model_name"],
                    "task": task_name,
                    "metric": metric_name,
                    "value": float(value),
                }
            )
    return records


def _artifact(
    *,
    slug: str,
    arm: str,
    run_index: int,
    model_judgment_score: int,
    class_u: tuple[int, int],
    class_m: tuple[int, int],
) -> dict[str, Any]:
    return {
        "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
        "arm": arm,
        "run_index": run_index,
        "created_at": CREATED_AT,
        "fixture": {"slug": slug, "title": slug, "claim_count": 3},
        "model": {
            "pin": PIN,
            "pin_slug": qg_bakeoff.pin_slug(PIN),
            "transport": qg_bakeoff.OPENCODE_TRANSPORT,
            "entrypoint": qg_bakeoff.OPENCODE_ENTRYPOINT,
            "measurement_tier": qg_bakeoff.OPENCODE_MEASUREMENT_TIER,
        },
        "status": "ran",
        "score": {
            "model_judgment_score": model_judgment_score,
            "live_admissible_score": model_judgment_score,
            "missing_claims": 0,
            "invalid_fact_checks": 0,
            "inadmissible_positive_verdicts": 0,
            "fractions": {
                "class_u_honesty": {
                    "numerator": class_u[0],
                    "denominator": class_u[1],
                    "text": f"{class_u[0]}/{class_u[1]}",
                    "low_n": True,
                },
                "class_m_alignment": {
                    "numerator": class_m[0],
                    "denominator": class_m[1],
                    "text": f"{class_m[0]}/{class_m[1]}",
                    "low_n": True,
                },
                "false_unsupported_on_true": {
                    "numerator": 0,
                    "denominator": 1,
                    "text": "0/1",
                    "low_n": True,
                },
            },
        },
        "tool_call_count": 0,
        "wall_seconds": 1.0,
    }


def test_emitter_round_trips_through_vendored_lang_uk_aggregation_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QG_BAKEOFF", "1")
    monkeypatch.setattr(qg_bakeoff, "_now_z", lambda: CREATED_AT)
    fixture = _fixture()
    fixtures_dir = tmp_path / "fixtures"
    output_dir = tmp_path / "artifacts"
    emit_dir = tmp_path / "eval-results"
    _write_fixture(fixtures_dir, fixture)

    qg_bakeoff.run_matrix(
        [fixture],
        [PIN],
        output_dir=output_dir,
        runner=_tooled_runner,
        bare_runner=_bare_runner,
        arm=qg_bakeoff.BOTH_ARM,
    )

    assert qg_bakeoff.main(
        [
            "--rescore",
            "--out-dir",
            str(output_dir),
            "--fixtures-dir",
            str(fixtures_dir),
            "--emit-lm-eval",
            str(emit_dir),
        ]
    ) == 0

    result_path = emit_dir / qg_bakeoff.pin_slug(PIN) / f"results_{CREATED_AT}.json"
    rows = _load_lang_uk_leaderboard_records(result_path)
    by_task = {row["task"]: row["value"] for row in rows}
    assert set(by_task) == {
        qg_bakeoff.LM_EVAL_TASK_MODEL_JUDGMENT,
        qg_bakeoff.LM_EVAL_TASK_U_HONESTY,
        qg_bakeoff.LM_EVAL_TASK_M_ALIGNMENT,
        qg_bakeoff.LM_EVAL_TASK_HARNESS_LIFT,
    }

    artifacts = qg_bakeoff._load_all_artifacts(output_dir)
    model_key = (PIN, qg_bakeoff.OPENCODE_TRANSPORT, qg_bakeoff.OPENCODE_ENTRYPOINT)
    totals = qg_bakeoff._aggregate_by_model_arm(artifacts)
    tooled = totals[(model_key, qg_bakeoff.TOOLED_ARM)]
    bare = totals[(model_key, qg_bakeoff.BARE_ARM)]
    assert by_task[qg_bakeoff.LM_EVAL_TASK_MODEL_JUDGMENT] == float(tooled["model_judgment_score"])
    assert by_task[qg_bakeoff.LM_EVAL_TASK_U_HONESTY] == 1.0
    assert by_task[qg_bakeoff.LM_EVAL_TASK_M_ALIGNMENT] == 1.0
    assert by_task[qg_bakeoff.LM_EVAL_TASK_HARNESS_LIFT] == float(
        tooled["model_judgment_score"] - bare["model_judgment_score"]
    )

    data = json.loads(result_path.read_text(encoding="utf-8"))
    meta = data["results"][qg_bakeoff.LM_EVAL_TASK_M_ALIGNMENT]["qg_meta"]
    assert meta["arm"] == qg_bakeoff.TOOLED_ARM
    assert meta["runs"] == 1
    assert meta["low_n"] is True
    assert meta["partial"] is False
    assert meta["transport"] == qg_bakeoff.OPENCODE_TRANSPORT
    assert meta["entrypoint"] == qg_bakeoff.OPENCODE_ENTRYPOINT


def test_emitter_multirun_metrics_match_run_aware_scorecard_means(tmp_path: Path) -> None:
    artifacts = [
        _artifact(
            slug="passage-a",
            arm=qg_bakeoff.TOOLED_ARM,
            run_index=1,
            model_judgment_score=10,
            class_u=(0, 1),
            class_m=(1, 1),
        ),
        _artifact(
            slug="passage-a",
            arm=qg_bakeoff.TOOLED_ARM,
            run_index=2,
            model_judgment_score=30,
            class_u=(1, 1),
            class_m=(1, 1),
        ),
        _artifact(
            slug="passage-b",
            arm=qg_bakeoff.TOOLED_ARM,
            run_index=1,
            model_judgment_score=50,
            class_u=(1, 1),
            class_m=(0, 1),
        ),
        _artifact(
            slug="passage-b",
            arm=qg_bakeoff.TOOLED_ARM,
            run_index=2,
            model_judgment_score=70,
            class_u=(1, 1),
            class_m=(1, 1),
        ),
        _artifact(
            slug="passage-a",
            arm=qg_bakeoff.BARE_ARM,
            run_index=1,
            model_judgment_score=-10,
            class_u=(0, 1),
            class_m=(0, 1),
        ),
        _artifact(
            slug="passage-a",
            arm=qg_bakeoff.BARE_ARM,
            run_index=2,
            model_judgment_score=10,
            class_u=(0, 1),
            class_m=(0, 1),
        ),
        _artifact(
            slug="passage-b",
            arm=qg_bakeoff.BARE_ARM,
            run_index=1,
            model_judgment_score=20,
            class_u=(0, 1),
            class_m=(0, 1),
        ),
        _artifact(
            slug="passage-b",
            arm=qg_bakeoff.BARE_ARM,
            run_index=2,
            model_judgment_score=20,
            class_u=(0, 1),
            class_m=(0, 1),
        ),
    ]
    [result_path] = qg_bakeoff.emit_lm_eval_results(artifacts, tmp_path / "eval-results")

    rows = _load_lang_uk_leaderboard_records(result_path)
    by_task = {row["task"]: row["value"] for row in rows}
    model_key = (PIN, qg_bakeoff.OPENCODE_TRANSPORT, qg_bakeoff.OPENCODE_ENTRYPOINT)
    totals = qg_bakeoff._aggregate_by_model_arm(artifacts)
    tooled = totals[(model_key, qg_bakeoff.TOOLED_ARM)]
    lift = qg_bakeoff._lm_eval_harness_lift_for_model(model_key, artifacts)

    assert tooled["model_judgment_score"]["mean"] == 80
    assert sum(a["score"]["model_judgment_score"] for a in artifacts if a["arm"] == qg_bakeoff.TOOLED_ARM) == 160
    assert by_task[qg_bakeoff.LM_EVAL_TASK_MODEL_JUDGMENT] == tooled["model_judgment_score"]["mean"]
    assert by_task[qg_bakeoff.LM_EVAL_TASK_U_HONESTY] == tooled["class_u_honesty"]["mean"]
    assert by_task[qg_bakeoff.LM_EVAL_TASK_M_ALIGNMENT] == tooled["class_m_alignment"]["mean"]
    assert lift is not None
    assert by_task[qg_bakeoff.LM_EVAL_TASK_HARNESS_LIFT] == lift["score"] == 30


def test_emitter_marks_legacy_partial_without_wall_clock(tmp_path: Path) -> None:
    output_dir = tmp_path / "artifacts"
    emit_dir = tmp_path / "eval-results"
    output_dir.mkdir()
    artifact = {
        "schema_version": qg_bakeoff.RUN_SCHEMA_VERSION,
        "fixture": {"slug": "legacy"},
        "model": {"pin": "openrouter/test/legacy"},
        "status": "ran",
    }
    (output_dir / "openrouter-test-legacy__legacy.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    [result_path] = qg_bakeoff.emit_lm_eval_results_from_dir(output_dir, emit_dir)

    assert result_path.name == "results_unknown.json"
    rows = _load_lang_uk_leaderboard_records(result_path)
    by_task = {row["task"]: row["value"] for row in rows}
    assert qg_bakeoff.LM_EVAL_TASK_HARNESS_LIFT not in by_task
    assert by_task[qg_bakeoff.LM_EVAL_TASK_MODEL_JUDGMENT] == 0.0

    data = json.loads(result_path.read_text(encoding="utf-8"))
    meta = data["results"][qg_bakeoff.LM_EVAL_TASK_MODEL_JUDGMENT]["qg_meta"]
    assert meta["partial"] is True
    assert "missing_created_at" in meta["partial_reasons"]
    assert "missing_score" in meta["partial_reasons"]
