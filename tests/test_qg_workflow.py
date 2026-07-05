from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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

    def reviewer(target: qg_workflow.ReviewTarget, _prompt: str) -> str:
        calls.append(target.level)
        return '{"findings": []}'

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
        options=qg_workflow.WorkflowOptions(enable_llm=True, reviewer_model_id="test-reviewer"),
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


def test_tier2_threads_tool_telemetry_into_store(tmp_path: Path) -> None:
    seminar_dir = _write_module(
        tmp_path,
        level="folk",
        slug="tooled-seminar",
        module_md="# Семінар\n\nУчасники аналізують джерела спокійно й уважно.\n",
    )
    db_path = tmp_path / "qg.db"

    def reviewer(_target: qg_workflow.ReviewTarget, _prompt: str) -> llm_reviewer_dispatch.DispatchResult:
        return llm_reviewer_dispatch.DispatchResult(
            response_text='{"findings": []}',
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
            route_name="opencode_frontier",
            tool_call_count=6,
            tools_used=("sources_query_wikipedia", "sources_search_heritage"),
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
