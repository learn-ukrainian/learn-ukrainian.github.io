from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

from scripts.audit import llm_qg_store, llm_reviewer, llm_reviewer_dispatch, qg_schema, qg_workflow
from scripts.audit.curriculum_qg_harness import CHECKER_VERSION

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_FILE = PROJECT_ROOT / "tests" / "fixtures" / "curriculum_qg" / "fixtures.yaml"
B1_27_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "b1" / "aspect-in-imperatives"


def _fixture_by_id(fixture_id: str) -> dict[str, Any]:
    payload = yaml.safe_load(FIXTURE_FILE.read_text(encoding="utf-8"))
    for fixture in payload["fixtures"]:
        if fixture["id"] == fixture_id:
            return fixture
    raise AssertionError(f"missing fixture {fixture_id}")


def _write_fixture_module(tmp_path: Path, fixture_id: str) -> Path:
    fixture = _fixture_by_id(fixture_id)
    module_dir = tmp_path / fixture["slug"]
    module_dir.mkdir()
    for name, body in fixture["module"].items():
        (module_dir / name).write_text(str(body).rstrip() + "\n", encoding="utf-8")
    return module_dir


def _write_module(
    tmp_path: Path,
    *,
    level: str = "b1",
    slug: str = "clean-module",
    module_md: str | None = None,
    activities_yaml: str = "[]\n",
) -> Path:
    module_dir = tmp_path / level / slug
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text(
        module_md
        or "# Чистий модуль\n\nУчні читають український текст і виконують коротке завдання.\n",
        encoding="utf-8",
    )
    (module_dir / "activities.yaml").write_text(activities_yaml, encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def _reviewer_response(issue_id: str = "LLM_STYLE_REVIEW") -> str:
    return json.dumps(
        {
            "findings": [
                {
                    "issue_id": issue_id,
                    "issue_class": "fluency",
                    "dimension": "naturalness",
                    "severity": "warning",
                    "excerpt": "український текст",
                    "message": "Injected reviewer warning.",
                }
            ]
        },
        ensure_ascii=False,
    )


def _seminar_response() -> str:
    return json.dumps(
        {
            "findings": [],
            "fact_checks": [
                {
                    "claim": "Веснянки — це весняні обрядові пісні.",
                    "verdict": "CONFIRMED",
                    "grounding": {
                        "tool": "sources_query_wikipedia",
                        "query": "Веснянки",
                        "evidence_excerpt": "весняні обрядові пісні",
                        "tool_call_id": "call_1",
                    },
                }
            ],
            "evidence_gaps": [],
        },
        ensure_ascii=False,
    )


def _wiki_event(
    *,
    query: str = "Веснянки",
    mode: str = "summary",
    output: str = "Веснянки — це весняні обрядові пісні.",
    call_id: str = "call_1",
) -> dict[str, Any]:
    return {
        "tool": "sources_query_wikipedia",
        "input": {"query": query, "mode": mode},
        "status": "completed",
        "tool_call_id": call_id,
        "output": output,
    }


def _seminar_dispatch(
    *,
    response_text: str | None = None,
    events: tuple[dict[str, Any], ...] = (),
    tool_call_count: int | None = None,
) -> llm_reviewer_dispatch.DispatchResult:
    return llm_reviewer_dispatch.DispatchResult(
        response_text=response_text or _seminar_response(),
        reviewer_model_id="test-reviewer",
        reviewer_family="test-family",
        route_name="opencode_frontier",
        tool_call_count=len(events) if tool_call_count is None else tool_call_count,
        tools_used=tuple(dict.fromkeys(str(event["tool"]) for event in events)),
        tool_events=events,
    )


def _target(module_dir: Path, *, level: str = "b1", slug: str | None = None) -> qg_workflow.ReviewTarget:
    return qg_workflow.ReviewTarget(
        level=level,
        slug=slug or module_dir.name,
        module_dir=module_dir,
    )


def _tier(record: dict[str, Any], number: int) -> dict[str, Any]:
    return next(tier for tier in record["qg_workflow"]["tiers"] if tier["tier"] == number)


def test_tier_order_and_tier0_hard_fail_short_circuits_llm(tmp_path: Path) -> None:
    module_dir = _write_fixture_module(tmp_path, "b1-27-restored-bad")
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> str:
        nonlocal calls
        calls += 1
        return '{"findings": []}'

    record = qg_workflow.review_module(
        _target(module_dir, slug="aspect-in-imperatives"),
        options=qg_workflow.WorkflowOptions(enable_llm=True),
        reviewer=reviewer,
    )

    assert [tier["tier"] for tier in record["qg_workflow"]["tiers"]] == [0, 1, 2]
    assert _tier(record, 0)["verdict"] == "FAIL"
    assert _tier(record, 2)["status"] == "skipped_tier0_hard_fail"
    assert record["llm_review"]["cost_override_applied"] is True
    assert calls == 0


def test_tier2_policy_gate_reaches_seminar_and_skips_a1_a2(tmp_path: Path) -> None:
    calls: list[str] = []

    def reviewer(target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(target.level)
        return llm_reviewer_dispatch.DispatchResult(
            response_text=_seminar_response(),
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
            route_name="opencode_frontier",
            tool_call_count=1,
            tools_used=("sources_query_wikipedia",),
            tool_events=(_wiki_event(mode="section"),),
        )

    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="calm-seminar",
        module_md="# Семінар\n\nУчасники аналізують джерела спокійно й уважно.\n",
    )
    a1_dir = _write_module(tmp_path, level="a1", slug="a1-clean")
    a2_dir = _write_module(tmp_path, level="a2", slug="a2-clean")

    seminar = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="calm-seminar"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=tmp_path / "seminar-qg.db",
    )
    a1 = qg_workflow.review_module(
        _target(a1_dir, level="a1", slug="a1-clean"),
        options=qg_workflow.WorkflowOptions(enable_llm=True, reviewer_model_id="test-reviewer"),
        reviewer=reviewer,
    )
    a2 = qg_workflow.review_module(
        _target(a2_dir, level="a2", slug="a2-clean"),
        options=qg_workflow.WorkflowOptions(enable_llm=True, reviewer_model_id="test-reviewer"),
        reviewer=reviewer,
    )

    assert _tier(seminar, 2)["status"] == "ran"
    assert _tier(seminar, 2)["llm_required_by_policy"] is True
    assert _tier(a1, 2)["status"] == "skipped_policy"
    assert _tier(a2, 2)["status"] == "skipped_policy"
    assert calls == ["folk"]


def test_composite_cache_invalidates_on_gate_version_bump(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path)
    db_path = tmp_path / "qg.db"
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> str:
        nonlocal calls
        calls += 1
        return _reviewer_response()

    options_v1 = qg_workflow.WorkflowOptions(
        enable_llm=True,
        gate_version="gate.v1",
        reviewer_model_id="test-reviewer",
    )
    first = qg_workflow.review_module(
        _target(module_dir),
        options=options_v1,
        reviewer=reviewer,
        store_path=db_path,
    )
    second = qg_workflow.review_module(
        _target(module_dir),
        options=options_v1,
        reviewer=None,
        store_path=db_path,
    )
    third = qg_workflow.review_module(
        _target(module_dir),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            gate_version="gate.v2",
            reviewer_model_id="test-reviewer",
        ),
        reviewer=reviewer,
        store_path=db_path,
    )

    assert _tier(first, 2)["status"] == "ran"
    assert _tier(second, 2)["status"] == "cache_hit"
    assert _tier(third, 2)["status"] == "ran"
    assert calls == 2


def test_default_gate_version_v3_invalidates_v2_cache_rows(tmp_path: Path) -> None:
    assert qg_workflow.DEFAULT_GATE_VERSION == "qg_workflow.v3"
    module_dir = _write_module(tmp_path)
    db_path = tmp_path / "qg.db"
    prompt = llm_reviewer.build_reviewer_prompt(
        level="b1",
        slug="clean-module",
        module_md=(module_dir / "module.md").read_text(encoding="utf-8"),
        activities_yaml=(module_dir / "activities.yaml").read_text(encoding="utf-8"),
        vocabulary_yaml=(module_dir / "vocabulary.yaml").read_text(encoding="utf-8"),
        resources_yaml=(module_dir / "resources.yaml").read_text(encoding="utf-8"),
    )
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="clean-module",
        module_dir=module_dir,
        payload=qg_workflow._payload_from_findings([]),
        gate_version="qg_workflow.v2",
        prompt_hash=llm_qg_store.prompt_hash_for_text(prompt),
        checker_version=CHECKER_VERSION,
        level_policy_family="b1_plus",
        reviewer_model="test-reviewer",
        path=db_path,
    )
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> str:
        nonlocal calls
        calls += 1
        return _reviewer_response()

    record = qg_workflow.review_module(
        _target(module_dir),
        options=qg_workflow.WorkflowOptions(enable_llm=True, reviewer_model_id="test-reviewer"),
        reviewer=reviewer,
        store_path=db_path,
    )

    assert _tier(record, 2)["status"] == "ran"
    assert calls == 1


def test_cache_hit_revalidates_theatre_gate_on_stored_payload(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="cache-theatre",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    db_path = tmp_path / "qg.db"
    prompt = llm_reviewer.build_reviewer_prompt(
        level="folk",
        slug="cache-theatre",
        module_md=(seminar_dir / "module.md").read_text(encoding="utf-8"),
        activities_yaml=(seminar_dir / "activities.yaml").read_text(encoding="utf-8"),
        vocabulary_yaml=(seminar_dir / "vocabulary.yaml").read_text(encoding="utf-8"),
        resources_yaml=(seminar_dir / "resources.yaml").read_text(encoding="utf-8"),
    )
    payload = qg_workflow._payload_from_findings(
        [],
        fact_checks=[
            {
                "claim": "Веснянки — це весняні обрядові пісні.",
                "verdict": "CONFIRMED",
                "grounding": {
                    "tool": "sources_query_wikipedia",
                    "query": "Веснянки",
                    "evidence_excerpt": "весняні обрядові пісні",
                    "tool_call_id": "call_1",
                },
            }
        ],
    )
    llm_qg_store.record_llm_qg(
        level="folk",
        slug="cache-theatre",
        module_dir=seminar_dir,
        payload=payload,
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
        prompt_hash=llm_qg_store.prompt_hash_for_text(prompt),
        checker_version=CHECKER_VERSION,
        level_policy_family="seminar",
        reviewer_model="test-reviewer",
        reviewer_family="test-family",
        tool_call_count=0,
        tools_used=(),
        source="test",
        path=db_path,
    )
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return llm_reviewer_dispatch.DispatchResult(
            response_text=_seminar_response(),
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
            route_name="opencode_frontier",
            tool_call_count=1,
            tools_used=("sources_query_wikipedia",),
            tool_events=(_wiki_event(mode="section"),),
        )

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="cache-theatre"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=db_path,
    )

    assert _tier(record, 2)["status"] == "ran"
    assert calls == 1


def test_cache_hit_replays_grounding_gate_from_stored_tool_events(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="cache-grounding",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    db_path = tmp_path / "qg.db"
    prompt = llm_reviewer.build_reviewer_prompt(
        level="folk",
        slug="cache-grounding",
        module_md=(seminar_dir / "module.md").read_text(encoding="utf-8"),
        activities_yaml=(seminar_dir / "activities.yaml").read_text(encoding="utf-8"),
        vocabulary_yaml=(seminar_dir / "vocabulary.yaml").read_text(encoding="utf-8"),
        resources_yaml=(seminar_dir / "resources.yaml").read_text(encoding="utf-8"),
    )
    fabricated_finding = qg_schema.build_finding(
        issue_id="SEMINAR_FACTUAL_DETAIL",
        issue_class="other",
        dimension="seminar_sensitivity",
        severity="warning",
        file="module.md",
        line=3,
        span={"start": 0, "end": 8},
        excerpt="Веснянки",
        message="Fabricated grounding should fail cache replay.",
        confidence="llm_judgment",
        detector={"adapter": "llm_reviewer", "rule_id": "SEMINAR_FACTUAL_DETAIL"},
        attribution={"corpus": "reviewer"},
        grounding={
            "tool": "sources_query_wikipedia",
            "query": "Веснянки",
            "evidence_excerpt": "вигаданий фрагмент",
            "tool_call_id": "call_1",
        },
    )
    payload = qg_workflow._payload_from_findings(
        [fabricated_finding],
        fact_checks=json.loads(_seminar_response())["fact_checks"],
    )
    llm_qg_store.record_llm_qg(
        level="folk",
        slug="cache-grounding",
        module_dir=seminar_dir,
        payload=payload,
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
        prompt_hash=llm_qg_store.prompt_hash_for_text(prompt),
        checker_version=CHECKER_VERSION,
        level_policy_family="seminar",
        reviewer_model="test-reviewer",
        reviewer_family="test-family",
        route_name=None,
        tool_call_count=1,
        tools_used=("sources_query_wikipedia",),
        tool_events=(_wiki_event(mode="section"),),
        source="test",
        path=db_path,
    )
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> str:
        nonlocal calls
        calls += 1
        return _seminar_response()

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="cache-grounding"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=db_path,
    )

    issue_ids = [
        finding["issue_id"]
        for dimension in record["dimensions"].values()
        for finding in dimension["findings"]
    ]
    tier2 = _tier(record, 2)
    assert tier2["status"] == llm_reviewer_dispatch.UNGROUNDED_FINDINGS
    assert tier2["cache_regate"] == "replayed"
    assert "SEMINAR_FACTUAL_DETAIL" not in issue_ids
    assert "LLM_REVIEWER_GROUNDING_GATE" in issue_ids
    assert calls == 0


def test_cache_hit_deep_read_retry_requirement_falls_through_to_live_run(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="cache-deep-read",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    db_path = tmp_path / "qg.db"
    prompt = llm_reviewer.build_reviewer_prompt(
        level="folk",
        slug="cache-deep-read",
        module_md=(seminar_dir / "module.md").read_text(encoding="utf-8"),
        activities_yaml=(seminar_dir / "activities.yaml").read_text(encoding="utf-8"),
        vocabulary_yaml=(seminar_dir / "vocabulary.yaml").read_text(encoding="utf-8"),
        resources_yaml=(seminar_dir / "resources.yaml").read_text(encoding="utf-8"),
    )
    old = llm_qg_store.record_llm_qg(
        level="folk",
        slug="cache-deep-read",
        module_dir=seminar_dir,
        payload=qg_workflow._payload_from_reviewer_payload(json.loads(_seminar_response())),
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
        prompt_hash=llm_qg_store.prompt_hash_for_text(prompt),
        checker_version=CHECKER_VERSION,
        level_policy_family="seminar",
        reviewer_model="test-reviewer",
        reviewer_family="test-family",
        route_name=None,
        tool_call_count=1,
        tools_used=("sources_query_wikipedia",),
        tool_events=(_wiki_event(mode="summary"),),
        source="test",
        path=db_path,
    )
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return _seminar_dispatch(events=(_wiki_event(mode="section"),))

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="cache-deep-read"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=db_path,
    )

    latest = llm_qg_store.latest_llm_qg("folk", "cache-deep-read", path=db_path)
    assert _tier(record, 2)["status"] == "ran"
    assert "cache_regate" not in _tier(record, 2)
    assert calls == 1
    assert latest is not None
    assert latest.run_id != old.run_id


def test_pre_change_cache_row_without_tool_events_is_marked_unavailable(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="legacy-cache",
        module_md="# Семінар\n\nУчасники аналізують джерела спокійно й уважно.\n",
    )
    db_path = tmp_path / "qg.db"
    prompt = llm_reviewer.build_reviewer_prompt(
        level="folk",
        slug="legacy-cache",
        module_md=(seminar_dir / "module.md").read_text(encoding="utf-8"),
        activities_yaml=(seminar_dir / "activities.yaml").read_text(encoding="utf-8"),
        vocabulary_yaml=(seminar_dir / "vocabulary.yaml").read_text(encoding="utf-8"),
        resources_yaml=(seminar_dir / "resources.yaml").read_text(encoding="utf-8"),
    )
    stored = llm_qg_store.record_llm_qg(
        level="folk",
        slug="legacy-cache",
        module_dir=seminar_dir,
        payload=qg_workflow._payload_from_findings([]),
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
        prompt_hash=llm_qg_store.prompt_hash_for_text(prompt),
        checker_version=CHECKER_VERSION,
        level_policy_family="seminar",
        reviewer_model="test-reviewer",
        reviewer_family="test-family",
        route_name=None,
        tool_call_count=1,
        tools_used=("sources_query_wikipedia",),
        tool_events=(_wiki_event(mode="section"),),
        source="test",
        path=db_path,
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE llm_qg_runs SET tool_events_json = NULL WHERE run_id = ?", (stored.run_id,))

    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> str:
        nonlocal calls
        calls += 1
        return _seminar_response()

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="legacy-cache"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=db_path,
    )

    tier2 = _tier(record, 2)
    assert tier2["status"] == "cache_hit"
    assert tier2["cache_regate"] == "unavailable"
    assert calls == 0


def test_legacy_cache_row_without_raw_capture_never_emits_certification_wrapper(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="legacy-raw-capture",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    db_path = tmp_path / "qg.db"
    prompt = llm_reviewer.build_reviewer_prompt(
        level="folk",
        slug="legacy-raw-capture",
        module_md=(seminar_dir / "module.md").read_text(encoding="utf-8"),
        activities_yaml=(seminar_dir / "activities.yaml").read_text(encoding="utf-8"),
        vocabulary_yaml=(seminar_dir / "vocabulary.yaml").read_text(encoding="utf-8"),
        resources_yaml=(seminar_dir / "resources.yaml").read_text(encoding="utf-8"),
    )
    llm_qg_store.record_llm_qg(
        level="folk",
        slug="legacy-raw-capture",
        module_dir=seminar_dir,
        payload=qg_workflow._payload_from_reviewer_payload(json.loads(_seminar_response())),
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
        prompt_hash=llm_qg_store.prompt_hash_for_text(prompt),
        checker_version=CHECKER_VERSION,
        level_policy_family="seminar",
        reviewer_model="test-reviewer",
        reviewer_family="test-family",
        route_name=None,
        tool_call_count=1,
        tools_used=("sources_query_wikipedia",),
        tool_events=(_wiki_event(mode="section"),),
        source="qg_workflow",
        path=db_path,
    )

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="legacy-raw-capture"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            capture_tier2=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        store_path=db_path,
    )

    tier2 = _tier(record, 2)
    assert tier2["status"] == "cache_hit"
    assert tier2["cache_regate"] == "replayed"
    assert "raw_response" not in tier2
    assert "dispatch" not in tier2
    assert "retry_history" not in tier2


def test_live_and_cache_paths_use_shared_reviewer_gate_helper(tmp_path: Path, monkeypatch: Any) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="shared-helper",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    db_path = tmp_path / "qg.db"
    calls: list[bool] = []

    def fake_gate(
        payload: dict[str, Any],
        dispatch_meta: dict[str, Any],
        *,
        policy_family: str,
        theatre_retry_available: bool,
        deep_read_retry_available: bool,
        factual_sweep_retry_available: bool,
        retry_unavailable_fails: bool = False,
    ) -> qg_workflow._ReviewerGateOutcome:
        calls.append(retry_unavailable_fails)
        clean_payload = dict(payload)
        return qg_workflow._ReviewerGateOutcome(
            payload=clean_payload,
            findings=[],
            grounding_gate=llm_reviewer_dispatch.GroundingGateResult(payload=clean_payload),
        )

    monkeypatch.setattr(qg_workflow, "_run_reviewer_gate_sequence", fake_gate)

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        return _seminar_dispatch(events=(_wiki_event(mode="section"),))

    first = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="shared-helper"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=db_path,
    )
    second = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="shared-helper"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=None,
        store_path=db_path,
    )

    assert _tier(first, 2)["status"] == "ran"
    assert _tier(second, 2)["status"] == "cache_hit"
    assert calls == [False, True]


def test_missing_fact_sweep_retries_once_and_recovers(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="fact-sweep-recovery",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    section_event = _wiki_event(mode="section")
    calls: list[str] = []

    def reviewer(_target: qg_workflow.ReviewTarget, prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(prompt)
        response = json.dumps({"findings": []}) if len(calls) == 1 else _seminar_response()
        return _seminar_dispatch(response_text=response, events=(section_event,))

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="fact-sweep-recovery"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            capture_tier2=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    tier = _tier(record, 2)
    assert tier["status"] == "ran"
    assert record["terminal_verdict"] == "PASS"
    assert len(calls) == 2
    assert "Factual Sweep Required" in calls[1]
    assert len(tier["retry_history"]) == 2
    assert tier["gate_outcomes"]["factual_sweep_retried"] is True


def test_missing_fact_sweep_retry_exhausts_fail_closed(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="fact-sweep-exhausted",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    section_event = _wiki_event(mode="section")
    calls: list[str] = []

    def reviewer(_target: qg_workflow.ReviewTarget, prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(prompt)
        return _seminar_dispatch(
            response_text=json.dumps({"findings": []}),
            events=(section_event,),
        )

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="fact-sweep-exhausted"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    assert _tier(record, 2)["status"] == "factual_sweep_incomplete"
    assert record["terminal_verdict"] == "FAIL"
    assert len(calls) == 2
    assert "Factual Sweep Required" in calls[1]


def test_exhausted_fact_sweep_replays_fail_closed_from_cache(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="fact-sweep-cache-exhausted",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    db_path = tmp_path / "qg.db"
    calls: list[str] = []

    def reviewer(_target: qg_workflow.ReviewTarget, prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(prompt)
        return _seminar_dispatch(
            response_text=json.dumps({"findings": []}),
            events=(_wiki_event(mode="section"),),
        )

    options = qg_workflow.WorkflowOptions(
        enable_llm=True,
        reviewer_model_id="test-reviewer",
        reviewer_family="test-family",
    )
    target = _target(seminar_dir, level="folk", slug="fact-sweep-cache-exhausted")
    first = qg_workflow.review_module(
        target,
        options=options,
        reviewer=reviewer,
        store_path=db_path,
    )
    stored = llm_qg_store.latest_llm_qg(
        "folk", "fact-sweep-cache-exhausted", path=db_path
    )
    assert stored is not None
    assert stored.gate_outcomes is not None
    assert stored.gate_outcomes["factual_sweep_retried"] is True
    second = qg_workflow.review_module(
        target,
        options=options,
        reviewer=None,
        store_path=db_path,
    )

    assert _tier(first, 2)["status"] == "factual_sweep_incomplete"
    assert first["terminal_verdict"] == "FAIL"
    assert _tier(second, 2)["status"] == "factual_sweep_incomplete"
    assert _tier(second, 2)["cache_regate"] == "replayed"
    assert second["terminal_verdict"] == "FAIL"
    assert len(calls) == 2


def test_missing_fact_sweep_retry_honors_lower_call_limit(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="fact-sweep-call-limit",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    calls: list[str] = []

    def reviewer(_target: qg_workflow.ReviewTarget, prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(prompt)
        return _seminar_dispatch(
            response_text=json.dumps({"findings": []}),
            events=(_wiki_event(mode="section"),),
        )

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="fact-sweep-call-limit"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            max_llm_calls=1,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    assert _tier(record, 2)["status"] == "factual_sweep_incomplete"
    assert record["terminal_verdict"] == "FAIL"
    assert len(calls) == 1


def test_theatre_then_missing_fact_sweep_recovers_within_three_calls(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="theatre-fact-sweep",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    section_event = _wiki_event(mode="section")
    calls: list[str] = []

    def reviewer(_target: qg_workflow.ReviewTarget, prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(prompt)
        if len(calls) == 1:
            return _seminar_dispatch(response_text=json.dumps({"findings": []}), tool_call_count=0)
        response = json.dumps({"findings": []}) if len(calls) == 2 else _seminar_response()
        return _seminar_dispatch(response_text=response, events=(section_event,))

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="theatre-fact-sweep"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    assert _tier(record, 2)["status"] == "ran"
    assert record["terminal_verdict"] == "PASS"
    assert len(calls) == qg_workflow.MAX_TIER2_REVIEWER_CALLS
    assert "Tools Required" in calls[1]
    assert "Tools Required" in calls[2]
    assert "Factual Sweep Required" in calls[2]


def test_tier2_threads_tool_telemetry_into_store(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="tooled-seminar",
        module_md="# Семінар\n\nУчасники аналізують джерела спокійно й уважно.\n",
    )
    db_path = tmp_path / "qg.db"
    events = (
        _wiki_event(mode="section"),
        {
            "tool": "sources_search_heritage",
            "input": {"query": "Веснянки"},
            "status": "completed",
            "tool_call_id": "call_2",
            "output": "Heritage result",
        },
    )

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        return llm_reviewer_dispatch.DispatchResult(
            response_text=_seminar_response(),
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
            route_name="opencode_frontier",
            tool_call_count=6,
            tools_used=("sources_query_wikipedia", "sources_search_heritage"),
            tool_events=events,
        )

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="tooled-seminar"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=db_path,
    )

    assert _tier(record, 2)["status"] == "ran"
    stored = llm_qg_store.latest_llm_qg("folk", "tooled-seminar", path=db_path)
    assert stored is not None
    assert stored.tool_call_count == 6
    assert stored.tools_used == ("sources_query_wikipedia", "sources_search_heritage")
    assert stored.tool_events == events


def test_summary_only_positive_verdict_after_retry_fails_inadmissible_citations(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="summary-only-positive",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    summary_event = _wiki_event(mode="summary")
    calls: list[str] = []

    def reviewer(_target: qg_workflow.ReviewTarget, prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(prompt)
        return _seminar_dispatch(events=(summary_event,))

    db_path = tmp_path / "qg.db"
    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="summary-only-positive"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=db_path,
    )

    tier = _tier(record, 2)
    assert tier["status"] == "inadmissible_citations"
    assert tier["inadmissible_positive_verdicts"] == 1
    assert tier["invalid_fact_checks"] == 0
    assert record["workflow_verdict"] == "FAIL"
    assert record["terminal_verdict"] == "FAIL"
    assert len(calls) == 2
    assert "Deep Read Required" in calls[1]

    gate_findings = [
        finding
        for dimension in record["dimensions"].values()
        for finding in dimension["findings"]
        if finding["issue_id"] == "LLM_REVIEWER_GROUNDING_GATE"
    ]
    assert gate_findings[0]["message"] == (
        "reviewer confirmed/refuted claims on summary-only wiki evidence after the forced "
        "deep-read retry — factual sweep uncertified"
    )
    stored = llm_qg_store.latest_llm_qg("folk", "summary-only-positive", path=db_path)
    assert stored is not None
    assert stored.payload["inadmissible_positive_verdicts"] == 1
    fact_check = stored.payload["fact_checks"][0]
    assert fact_check["verdict"] == "UNVERIFIED_INSUFFICIENT_SEARCH"
    assert fact_check["original_verdict"] == "CONFIRMED"
    assert fact_check["admissibility_downgraded"] is True


def test_required_ungrounded_finding_status_precedes_inadmissible_citations(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="ungrounded-plus-summary",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    summary_event = _wiki_event(mode="summary")
    required_finding = {
        "issue_id": "SEMINAR_FACTUAL_DETAIL",
        "issue_class": "other",
        "dimension": "seminar_sensitivity",
        "severity": "warning",
        "excerpt": "Веснянки",
        "message": "Fabricated grounding should keep the ungrounded status.",
        "grounding": {
            "tool": "sources_query_wikipedia",
            "query": "Веснянки",
            "evidence_excerpt": "вигаданий фрагмент",
            "tool_call_id": "call_1",
        },
    }
    response = json.dumps(
        {
            "findings": [required_finding],
            "fact_checks": json.loads(_seminar_response())["fact_checks"],
            "evidence_gaps": [],
        },
        ensure_ascii=False,
    )
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return _seminar_dispatch(response_text=response, events=(summary_event,))

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="ungrounded-plus-summary"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    tier = _tier(record, 2)
    assert tier["status"] == llm_reviewer_dispatch.UNGROUNDED_FINDINGS
    assert tier["inadmissible_positive_verdicts"] == 1
    assert calls == 2


def test_tier2_theatre_then_deep_read_retry_stays_within_three_calls(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="retry-budget",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    summary_event = _wiki_event(mode="summary")
    calls: list[str] = []

    def reviewer(_target: qg_workflow.ReviewTarget, prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        calls.append(prompt)
        if len(calls) == 1:
            return _seminar_dispatch(tool_call_count=0)
        return _seminar_dispatch(events=(summary_event,))

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="retry-budget"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
        ),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    assert _tier(record, 2)["status"] == "inadmissible_citations"
    assert len(calls) == 3
    assert "Tools Required" in calls[1]
    assert "Deep Read Required" in calls[2]


def test_budget_exhaustion_emits_skipped_budget_and_incomplete(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path)
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> str:
        nonlocal calls
        calls += 1
        return '{"findings": []}'

    record = qg_workflow.review_module(
        _target(module_dir),
        options=qg_workflow.WorkflowOptions(enable_llm=True, max_llm_calls=0),
        reviewer=reviewer,
    )

    assert _tier(record, 2)["status"] == "skipped_budget"
    assert _tier(record, 2)["reason"] == "max_llm_calls"
    assert record["workflow_verdict"] == "SKIPPED_BUDGET"
    assert record["completion_status"] == "INCOMPLETE"
    assert record["terminal_verdict"] == "FAIL"
    assert calls == 0


def test_dry_run_estimates_tier2_without_reviewer_or_canary(tmp_path: Path) -> None:
    first = _write_module(tmp_path, slug="clean-one")
    second = _write_module(tmp_path, slug="clean-two")
    output = tmp_path / "dry-run.json"

    code = qg_workflow.main(
        [
            "--target",
            f"b1:clean-one:{first}",
            "--target",
            f"b1:clean-two:{second}",
            "--dry-run",
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert code == 0
    assert payload["dry_run"] is True
    assert payload["writes"] == 0
    assert payload["counts"]["modules"] == 2
    assert payload["counts"]["tier2_estimated_calls"] == 2
    assert payload["level_profiles"]["b1_plus"]["tier2_estimated_calls"] == 2
    assert payload["level_profiles"]["b1_plus"]["estimated_prompt_tokens"] > 0
    assert payload["level_profiles"]["b1_plus"]["estimated_cost_usd"] > 0


def test_workflow_dedupes_cached_tier2_findings_by_finding_id(tmp_path: Path) -> None:
    activities = (
        "- id: wb-essay-missing\n"
        "  type: essay-response\n"
        "  title: Напишіть есе\n"
        "  instruction: Напишіть 120 слів.\n"
    )
    module_dir = _write_module(
        tmp_path,
        level="b2",
        slug="model-answer-module",
        activities_yaml=activities,
    )
    target = _target(module_dir, level="b2", slug="model-answer-module")
    duplicate_findings = llm_reviewer.run_structural_checks("b2", activities)
    assert len(duplicate_findings) == 1
    prompt = llm_reviewer.build_reviewer_prompt(
        level="b2",
        slug="model-answer-module",
        module_md=(module_dir / "module.md").read_text(encoding="utf-8"),
        activities_yaml=activities,
        vocabulary_yaml="[]\n",
        resources_yaml="[]\n",
    )
    db_path = tmp_path / "qg.db"
    llm_qg_store.record_llm_qg(
        level="b2",
        slug="model-answer-module",
        module_dir=module_dir,
        payload=qg_workflow._payload_from_findings(duplicate_findings),
        gate_version="gate.v1",
        prompt_hash=llm_qg_store.prompt_hash_for_text(prompt),
        checker_version=CHECKER_VERSION,
        level_policy_family="b1_plus",
        reviewer_model="test-reviewer",
        path=db_path,
    )

    record = qg_workflow.review_module(
        target,
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            llm_on_fail=True,
            gate_version="gate.v1",
            reviewer_model_id="test-reviewer",
        ),
        store_path=db_path,
    )

    findings = [
        finding
        for dimension in record["dimensions"].values()
        for finding in dimension["findings"]
        if finding["issue_id"] == "MISSING_MODEL_ANSWER"
    ]
    assert _tier(record, 2)["status"] == "cache_hit"
    assert len(findings) == 1
    qg_schema.validate_record(record)


def test_current_b1_27_production_stays_green_without_llm_bulk_run() -> None:
    record = qg_workflow.review_module(
        qg_workflow.ReviewTarget(
            level="b1",
            slug="aspect-in-imperatives",
            module_dir=B1_27_DIR,
        )
    )

    assert record["module_id"] == "b1/aspect-in-imperatives"
    assert record["verdict"] == "PASS"
    assert record["terminal_verdict"] == "PASS"
    assert record["llm_review"]["used"] is False
    assert _tier(record, 2)["status"] == "skipped_flag_off"
    qg_schema.validate_record(record)


def test_tier2_rejects_route_name_mismatch(tmp_path: Path) -> None:
    """codex review of #4401 (Medium): route_name keys the composite cache — an
    injected reviewer answering from the WRONG route (same model/family) must
    fail identity, not poison route-keyed cache rows."""
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="route-mismatch",
        module_md="# Семінар\n\nУчасники аналізують джерела спокійно й уважно.\n",
    )
    db_path = tmp_path / "qg.db"

    expected_route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        return llm_reviewer_dispatch.DispatchResult(
            response_text='{"findings": []}',
            reviewer_model_id=expected_route.reviewer_model_id,
            reviewer_family=expected_route.reviewer_family,
            route_name="agy_frontier",  # WRONG route: expected opencode_frontier
        )

    # live_reviewer resolves the expected route; the canary/lineage block is
    # out of scope here (tested elsewhere) — patch it away to isolate the
    # route-identity check.
    from unittest.mock import patch

    with patch.object(qg_workflow, "_live_reviewer_block", return_value=None):
        record = qg_workflow.review_module(
            _target(seminar_dir, level="folk", slug="route-mismatch"),
            options=qg_workflow.WorkflowOptions(
                enable_llm=True,
                live_reviewer=True,
                max_cost_usd=5.0,
                reviewer_model_id=expected_route.reviewer_model_id,
                reviewer_family=expected_route.reviewer_family,
                daily_spend_path=tmp_path / "spend.jsonl",
                circuit_state_path=tmp_path / "circuit.json",
            ),
            reviewer=reviewer,
            store_path=db_path,
        )

    tier2 = _tier(record, 2)
    assert tier2["status"] == "provider_error"
    assert tier2["reason"] == "reviewer_identity_mismatch"
    assert tier2["actual_route_name"] == "agy_frontier"
    # nothing persisted for the poisoned run
    assert llm_qg_store.latest_llm_qg("folk", "route-mismatch", path=db_path) is None


def _record_circuit_window(path: Path, statuses: list[str]) -> dict[str, Any]:
    status: dict[str, Any] = {}
    for index, tier2_status in enumerate(statuses):
        status = llm_qg_store.record_live_tier2_outcome(
            level="folk",
            slug=f"circuit-{index}",
            gate_version=qg_workflow.DEFAULT_GATE_VERSION,
            reviewer_model=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.reviewer_model_id,
            reviewer_family=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.reviewer_family,
            route_name=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.route_name,
            status=tier2_status,
            path=path,
        )
    return status


def test_live_tier2_circuit_trips_at_first_integer_over_threshold(tmp_path: Path) -> None:
    circuit_path = tmp_path / "circuit.json"
    closed = _record_circuit_window(
        circuit_path,
        ["ran"] * 25 + ["provider_error"] * 4 + ["ran"],
    )

    assert closed["attempted"] == 30
    assert closed["terminal_failures"] == 4
    assert closed["open"] is False

    opened = llm_qg_store.record_live_tier2_outcome(
        level="folk",
        slug="circuit-open",
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
        reviewer_model=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.reviewer_model_id,
        reviewer_family=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.reviewer_family,
        route_name=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.route_name,
        status="provider_error",
        path=circuit_path,
    )

    assert opened["attempted"] == 30
    assert opened["terminal_failures"] == 5
    assert opened["open"] is True
    assert "circuit_open" in opened["operator_message"]


def test_live_tier2_gate_downgrades_do_not_count_as_circuit_failures(tmp_path: Path) -> None:
    circuit_path = tmp_path / "circuit.json"
    status = _record_circuit_window(
        circuit_path,
        ["ran"] * 25 + [llm_reviewer_dispatch.UNGROUNDED_FINDINGS] * 5,
    )

    assert status["attempted"] == 30
    assert status["terminal_failures"] == 0
    assert status["open"] is False


def test_circuit_open_refuses_live_dispatch(tmp_path: Path) -> None:
    circuit_path = tmp_path / "circuit.json"
    _record_circuit_window(circuit_path, ["ran"] * 25 + ["provider_error"] * 5)
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="blocked-live",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> str:
        nonlocal calls
        calls += 1
        return _seminar_response()

    record = qg_workflow.review_module(
        _target(seminar_dir, level="folk", slug="blocked-live"),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            live_reviewer=True,
            max_cost_usd=5.0,
            circuit_state_path=circuit_path,
        ),
        reviewer=reviewer,
        store_path=tmp_path / "qg.db",
    )

    tier2 = _tier(record, 2)
    assert tier2["status"] == "circuit_open"
    assert tier2["reason"] == "circuit_open"
    assert "circuit_open" in tier2["message"]
    assert calls == 0


def test_reset_circuit_allows_live_dispatch_after_operator_clear(tmp_path: Path) -> None:
    circuit_path = tmp_path / "circuit.json"
    _record_circuit_window(circuit_path, ["ran"] * 25 + ["provider_error"] * 5)
    output = tmp_path / "reset.json"

    code = qg_workflow.main(
        [
            "--reset-circuit",
            "--qg-circuit-state",
            str(circuit_path),
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )

    reset_payload = json.loads(output.read_text(encoding="utf-8"))
    assert code == 0
    assert reset_payload["open"] is False
    assert llm_qg_store.live_tier2_circuit_status(circuit_path)["open"] is False

    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="reset-live",
        module_md="# Семінар\n\nВеснянки — це весняні обрядові пісні.\n",
    )
    expected_route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    calls = 0

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return llm_reviewer_dispatch.DispatchResult(
            response_text=_seminar_response(),
            reviewer_model_id=expected_route.reviewer_model_id,
            reviewer_family=expected_route.reviewer_family,
            route_name=expected_route.route_name,
            tool_call_count=1,
            tools_used=("sources_query_wikipedia",),
            tool_events=(_wiki_event(mode="section"),),
        )

    with patch.object(qg_workflow, "_live_reviewer_block", return_value=None):
        record = qg_workflow.review_module(
            _target(seminar_dir, level="folk", slug="reset-live"),
            options=qg_workflow.WorkflowOptions(
                enable_llm=True,
                live_reviewer=True,
                max_cost_usd=5.0,
                circuit_state_path=circuit_path,
                daily_spend_path=tmp_path / "spend.jsonl",
            ),
            reviewer=reviewer,
            store_path=tmp_path / "qg.db",
        )

    assert _tier(record, 2)["status"] == "ran"
    assert calls == 1
    assert llm_qg_store.live_tier2_circuit_status(circuit_path)["open"] is False


def test_live_batch_preflight_failure_short_circuits_before_dispatch(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    first = _write_module(
        tmp_path,
        level="folk",
        slug="batch-one",
        module_md="# Семінар\n\nУчасники аналізують джерела.\n",
    )
    second = _write_module(
        tmp_path,
        level="folk",
        slug="batch-two",
        module_md="# Семінар\n\nУчасники аналізують джерела.\n",
    )

    def fail_preflight(_routes: Any) -> None:
        raise llm_reviewer_dispatch.ReviewerPreflightError(
            "opencode_unavailable",
            "opencode missing in test",
        )

    monkeypatch.setattr(llm_reviewer_dispatch, "live_batch_preflight", fail_preflight)

    with pytest.raises(ValueError, match="opencode_unavailable"):
        qg_workflow.review_modules(
            [
                _target(first, level="folk", slug="batch-one"),
                _target(second, level="folk", slug="batch-two"),
            ],
            options=qg_workflow.WorkflowOptions(
                enable_llm=True,
                live_reviewer=True,
                max_cost_usd=5.0,
                circuit_state_path=tmp_path / "circuit.json",
            ),
            store_path=tmp_path / "qg.db",
        )
