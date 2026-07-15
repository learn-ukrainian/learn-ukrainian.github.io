"""Direct adversarial tests for certification evidence authority."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.audit import llm_reviewer_dispatch, qg_workflow

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "agents_extensions"
    / "shared"
    / "skills"
    / "track-completion"
    / "scripts"
    / "certification_evidence.py"
)
SPEC = importlib.util.spec_from_file_location("certification_evidence_for_tests", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
ce = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ce
SPEC.loader.exec_module(ce)

TRACK_SCRIPT = ROOT / "agents_extensions/shared/skills/track-completion/scripts/track_completion.py"
TRACK_SPEC = importlib.util.spec_from_file_location("track_completion_for_certification_tests", TRACK_SCRIPT)
assert TRACK_SPEC is not None and TRACK_SPEC.loader is not None
tc = importlib.util.module_from_spec(TRACK_SPEC)
sys.modules[TRACK_SPEC.name] = tc
TRACK_SPEC.loader.exec_module(tc)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _identity() -> dict[str, str]:
    return {name: _sha(name) for name in ce.QG_IDENTITY_KEYS}


def _event(
    *,
    tool: str = "mcp__sources__query_wikipedia",
    query: str = "Веснянки",
    mode: str = "section",
    call_id: str = "call-1",
    output: str = "Веснянки — це особливий жанр обрядових пісень, що відзначають пробудження природи та прихід весни.",
) -> dict[str, Any]:
    return {
        "tool": tool,
        "input": {"query": query, "mode": mode},
        "status": "completed",
        "tool_call_id": call_id,
        "output": output,
    }


def _response(
    *,
    excerpt: str = "Веснянки — це особливий жанр обрядових пісень, що відзначають пробудження природи та прихід весни.",
    query: str = "Веснянки",
    call_id: str = "call-1",
) -> str:
    return json.dumps(
        {
            "findings": [],
            "fact_checks": [
                {
                    "claim": "Веснянки — це особливий жанр обрядових пісень, що відзначають пробудження природи та прихід весни.",
                    "verdict": "CONFIRMED",
                    "grounding": {
                        "tool": "mcp__sources__query_wikipedia",
                        "query": query,
                        "evidence_excerpt": excerpt,
                        "tool_call_id": call_id,
                    },
                    "deep_read_attempted": True,
                }
            ],
            "evidence_gaps": [],
        },
        ensure_ascii=False,
    )


def _write_live_canary(tmp_path: Path) -> Path:
    route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    path = tmp_path / "seminar-canary.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": llm_reviewer_dispatch.CANARY_SCHEMA_VERSION,
                "level": "seminar",
                "gate_version": qg_workflow.DEFAULT_GATE_VERSION,
                "prompt_template_hash": llm_reviewer_dispatch.prompt_template_hash(),
                "reviewer_model_id": route.reviewer_model_id,
                "reviewer_family": route.reviewer_family,
                "route_name": route.route_name,
                "passed": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _capture_module(tmp_path: Path) -> tuple[Path, llm_reviewer_dispatch.DispatchResult]:
    repo = tmp_path / "repo"
    module_dir = repo / "curriculum/l2-uk-en/folk/demo"
    module_dir.mkdir(parents=True)
    for name, text in {
        "module.md": "# Модуль\n\nВеснянки — це особливий жанр обрядових пісень.\n",
        "activities.yaml": "[]\n",
        "vocabulary.yaml": "[]\n",
        "resources.yaml": "[]\n",
    }.items():
        (module_dir / name).write_text(text, encoding="utf-8")
    event = _event()
    dispatch = llm_reviewer_dispatch.DispatchResult(
        response_text=_response(),
        reviewer_model_id=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.reviewer_model_id,
        reviewer_family=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.reviewer_family,
        route_name=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.route_name,
        tool_call_count=1,
        tools_used=(event["tool"],),
        tool_events=(event,),
    )
    return module_dir, dispatch


@pytest.fixture
def qg_capture(tmp_path: Path) -> dict[str, Any]:
    """Capture through the real live dispatcher with a no-network provider stub."""
    module_dir, dispatch = _capture_module(tmp_path)
    calls = 0

    def runner(
        _route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return dispatch

    reviewer = llm_reviewer_dispatch.LiveReviewerDispatcher(
        policy_family="seminar",
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
        author_family="codex",
        runner=runner,
    )
    record = qg_workflow.review_module(
        qg_workflow.ReviewTarget(level="folk", slug="demo", module_dir=module_dir),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            force_llm=True,
            live_reviewer=True,
            capture_tier2=True,
            persist_llm_qg=False,
            author_family="codex",
            canary_artifacts={"seminar": _write_live_canary(tmp_path)},
            max_cost_usd=1.0,
            circuit_state_path=tmp_path / "live-circuit.json",
            daily_spend_path=tmp_path / "live-spend.jsonl",
        ),
        reviewer=reviewer,
    )
    tier2 = next(tier for tier in record["qg_workflow"]["tiers"] if tier["tier"] == 2)
    assert record["terminal_verdict"] == "PASS"
    assert tier2["status"] == "ran"
    assert calls == 1
    return {"repo": module_dir.parents[3], "module_dir": module_dir, "record": record, "tier2": tier2}


@pytest.fixture
def injected_qg_capture(tmp_path: Path) -> dict[str, Any]:
    """The old callback-only fixture remains a valid workflow, not production, capture."""
    module_dir, dispatch = _capture_module(tmp_path)
    fabricated = replace(
        dispatch,
        execution_provenance={"kind": "live_reviewer_dispatcher", "dispatcher": "LiveReviewerDispatcher"},
        author_lineage={"family": "codex", "source": "explicit", "evidence": "codex"},
        cross_family_validated=True,
    )
    record = qg_workflow.review_module(
        qg_workflow.ReviewTarget(level="folk", slug="demo", module_dir=module_dir),
        options=qg_workflow.WorkflowOptions(
            enable_llm=True,
            force_llm=True,
            capture_tier2=True,
            persist_llm_qg=False,
            reviewer_model_id=dispatch.reviewer_model_id,
            reviewer_family=dispatch.reviewer_family,
        ),
        reviewer=lambda *_args: fabricated,
    )
    tier2 = next(tier for tier in record["qg_workflow"]["tiers"] if tier["tier"] == 2)
    assert tier2["status"] == "ran"
    return {"module_dir": module_dir, "record": record, "tier2": tier2}


@pytest.fixture
def qg_replay_capture(tmp_path: Path) -> dict[str, Any]:
    """A cold live capture followed by the real SQLite cache replay path."""
    module_dir, dispatch = _capture_module(tmp_path)
    calls = 0

    def runner(
        _route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        nonlocal calls
        calls += 1
        return dispatch

    reviewer = llm_reviewer_dispatch.LiveReviewerDispatcher(
        policy_family="seminar",
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
        author_family="codex",
        runner=runner,
    )
    options = qg_workflow.WorkflowOptions(
        enable_llm=True,
        force_llm=True,
        live_reviewer=True,
        capture_tier2=True,
        author_family="codex",
        canary_artifacts={"seminar": _write_live_canary(tmp_path)},
        max_cost_usd=1.0,
        circuit_state_path=tmp_path / "replay-circuit.json",
        daily_spend_path=tmp_path / "replay-spend.jsonl",
    )
    target = qg_workflow.ReviewTarget(level="folk", slug="demo", module_dir=module_dir)
    store_path = tmp_path / "qg.db"
    first = qg_workflow.review_module(target, options=options, reviewer=reviewer, store_path=store_path)
    second = qg_workflow.review_module(target, options=options, reviewer=reviewer, store_path=store_path)
    tier2 = next(tier for tier in second["qg_workflow"]["tiers"] if tier["tier"] == 2)
    return {
        "module_dir": module_dir,
        "first": first,
        "record": second,
        "tier2": tier2,
        "calls": calls,
    }


def _route(identity: dict[str, str], tier2: dict[str, Any]) -> dict[str, Any]:
    dispatch = tier2["dispatch"]
    return {
        "family": dispatch["reviewer_family"],
        "model": dispatch["reviewer_model_id"],
        "route": dispatch["route_name"],
        "lineage": dispatch["route_lineage_id"],
        "canary": {
            "status": "PASS",
            "artifact_sha256": _sha("canary-artifact"),
            "route": dispatch["route_name"],
            "model": dispatch["reviewer_model_id"],
            "prompt_identity": identity["prompt"],
            "gate_identity": identity["gate"],
        },
        "budget": {
            "status": "QUALIFIED",
            "policy_sha256": identity["cost"],
            "max_module_cost_usd": 1.0,
            "max_daily_cost_usd": 2.0,
        },
        "circuit": {"status": "CLOSED", "policy_sha256": identity["circuit"]},
        "resume": {"status": "QUALIFIED", "contract_sha256": identity["resume"]},
    }


def _authorization(tmp_path: Path, identity: dict[str, str], tier2: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    profile = {"id": "seminar-pending", "version": "1.0.0"}
    route = _route(identity, tier2)
    qualification = {
        "schema_version": "production-qg-qualification.v1",
        "verdict": "PASS",
        "profile": profile,
        "identity": identity,
        "route": route,
    }
    qualification_path = tmp_path / "qualification.json"
    qualification_path.write_text(json.dumps(qualification, sort_keys=True), encoding="utf-8")
    arming = {
        "schema_version": "production-qg-human-arming.v1",
        "decision": "ARMED",
        "actor_type": "human",
        "actor_id": "operator-1",
        "approval_id": "approval-1",
        "qualification_sha256": hashlib.sha256(qualification_path.read_bytes()).hexdigest(),
        "profile": profile,
        "route": route,
        "budget": route["budget"],
    }
    arming_path = tmp_path / "arming.json"
    arming_path.write_text(json.dumps(arming, sort_keys=True), encoding="utf-8")
    qg_profile = {
        "mode": "armed-canary",
        "qualification_artifact": qualification_path.name,
        "human_arming_artifact": arming_path.name,
    }
    authorization = ce.load_authorization(
        qg_profile, repo_root=tmp_path, expected_profile=profile, expected_identity=identity
    )
    return authorization, qg_profile


def _artifact(capture: dict[str, Any], authorization: dict[str, Any], identity: dict[str, str]) -> ce.EvidenceArtifact:
    tier = capture["tier2"]
    fields = (
        "source",
        "workflow_run_id",
        "tier2_run_id",
        "attempt_id",
        "status",
        "completion_status",
        "dispatch",
        "payload",
        "raw_response",
        "raw_response_sha256",
        "retry_history",
        "gate_outcomes",
    )
    copied_tier = {key: copy.deepcopy(tier[key]) for key in fields} | {"canonical_tier_index": 2}
    if "cache_regate" in tier:
        copied_tier["cache_regate"] = copy.deepcopy(tier["cache_regate"])
    value = {
        "schema_version": "certification-evidence.v1",
        "kind": "production-qg",
        "target": "folk/demo",
        "profile": {"id": "seminar-pending", "version": "1.0.0"},
        "preparation_identity": _sha("preparation"),
        "learner_hashes": {"content": _sha("learner")},
        "arm": "production-qualified",
        "authorization": {"identity": identity, **{key: authorization[key] for key in authorization if key.endswith("sha256")}},
        "canonical_record": copy.deepcopy(capture["record"]),
        "tier2": copied_tier,
    }
    ce.validate_evidence_value(value)
    return ce.EvidenceArtifact(Path("/tmp/captured-qg.json"), _sha(json.dumps(value, sort_keys=True)), value)


def _mirror_tier(artifact: ce.EvidenceArtifact) -> None:
    canonical = artifact.value["canonical_record"]["qg_workflow"]["tiers"][2]
    for key, value in artifact.value["tier2"].items():
        if key != "canonical_tier_index":
            canonical[key] = copy.deepcopy(value)


def _completion_case(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, Any], dict[str, Any]]:
    """Build a real B1 completion input set with no authority monkeypatches."""
    repo = tmp_path / "completion-repo"
    shutil.copytree(ROOT / "agents_extensions", repo / "agents_extensions")
    config = tc.load_config()
    paths = [*config["identity_paths"], *config["certification_identity_paths"]["pbr"]]
    for declared in config["certification_identity_paths"]["production_qg"].values():
        paths.extend(declared)
    for relative in dict.fromkeys(paths):
        source = ROOT / relative
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    slug = "adjectives-comparative"
    (repo / "curriculum/l2-uk-en/plans/b1").mkdir(parents=True)
    shutil.copy2(ROOT / f"curriculum/l2-uk-en/plans/b1/{slug}.yaml", repo / f"curriculum/l2-uk-en/plans/b1/{slug}.yaml")
    shutil.copytree(ROOT / f"curriculum/l2-uk-en/b1/{slug}", repo / f"curriculum/l2-uk-en/b1/{slug}")
    manifest = {"levels": {"b1": {"type": "core", "modules": [slug]}}}
    (repo / "curriculum/l2-uk-en/curriculum.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    config_path = repo / "agents_extensions/shared/skills/track-completion/config/track-completion.v1.yaml"
    ledger_root = tmp_path / "ledgers"
    _, ledger = tc.start_run(
        f"b1/{slug}", owner="codex/test", repo_root=repo, config_path=config_path, ledger_root=ledger_root
    )
    ledger["author_families"] = ["codex"]
    inputs = tc.certification_inputs(f"b1/{slug}", repo_root=repo, config_path=config_path, ledger=ledger)
    pbr = {
        "result_path": "/outside/pbr.json",
        "result_sha256": _sha("result"),
        "reproducibility_key": _sha("repro"),
        "stability_key": _sha("pbr-key"),
        "material_fingerprint": _sha("pbr-fingerprint"),
        "status": "PASS",
        "reviewer_family": "gemini",
        "reviewer_model": "fixture",
        "target_identity_sha256": ledger["current_identity"]["sha256"],
        "certification": {
            "profile": inputs["profile"],
            "preparation_identity": inputs["preparation_identity"],
            "learner_hashes": inputs["learner_hashes"],
            "plan_hash": inputs["plan_hash"],
            "raw_response_sha256": _sha("pbr-raw"),
            "dependency_hashes": inputs["workflow_hashes"],
            "dependency_identity": inputs["pbr_dependency_identity"],
        },
    }
    ledger["reviews"] = [pbr]
    return repo, config_path, ledger_root, ledger, inputs


def _independent_value(inputs: dict[str, Any], *, unresolved: bool = False, stale: bool = False) -> dict[str, Any]:
    return {
        "schema_version": "certification-evidence.v1",
        "kind": "independent-review",
        "target": inputs["target"],
        "profile": inputs["profile"],
        "preparation_identity": _sha("stale-preparation") if stale else inputs["preparation_identity"],
        "learner_hashes": inputs["learner_hashes"],
        "mutation_identity": inputs["mutation_identity"],
        "diff_sha256": _sha("diff"),
        "review": {
            "author_families": ["codex"],
            "reviewer_family": "gemini",
            "verdict": "CHANGES_REQUESTED" if unresolved else "PASS",
            "material_findings": ([{"id": "finding", "severity": "high", "resolved": False}] if unresolved else []),
            "resolution_state": "UNRESOLVED" if unresolved else "RESOLVED",
            "raw_response_sha256": _sha("independent-raw"),
        },
    }


def _integration_value(inputs: dict[str, Any], independent_sha: str) -> dict[str, Any]:
    return {
        "schema_version": "certification-evidence.v1",
        "kind": "integration",
        "target": inputs["target"],
        "profile": inputs["profile"],
        "preparation_identity": inputs["preparation_identity"],
        "learner_hashes": inputs["learner_hashes"],
        "mutation_identity": inputs["mutation_identity"],
        "diff_sha256": _sha("diff"),
        "independent_evidence_sha256": independent_sha,
        "integration": {
            "issue": 5156,
            "branch": "codex/5156-certification-chain",
            "worktree": ".worktrees/dispatch/codex/5156-certification-chain",
            "commit": "a" * 40,
            "pr": 5156,
            "ci_gate": "PASS",
            "review_gate": "PASS",
            "merge_sha": "b" * 40,
            "telemetry": {"applicable": False, "receipt": None},
            "cleanup": {"state": "COMPLETE"},
        },
    }


def _passes(artifact: ce.EvidenceArtifact, capture: dict[str, Any], authorization: dict[str, Any], identity: dict[str, str]) -> bool:
    return ce.production_qg_passes(
        artifact,
        expected_identity=identity,
        expected_facts=ce.current_qg_facts(target="folk/demo", module_dir=capture["module_dir"]),
        seminar=True,
        authorization=authorization,
    )


def test_canonical_route_mapping_succeeds_and_each_mismatch_fails(qg_capture: dict[str, Any], tmp_path: Path) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    assert _passes(artifact, qg_capture, authorization, identity)

    for dispatch_key in ("reviewer_family", "reviewer_model_id", "route_name", "route_lineage_id"):
        altered = copy.deepcopy(artifact)
        altered.value["tier2"]["dispatch"][dispatch_key] = "wrong"
        _mirror_tier(altered)
        assert not _passes(altered, qg_capture, authorization, identity)


def test_injected_callback_capture_cannot_certify_production(
    injected_qg_capture: dict[str, Any], tmp_path: Path
) -> None:
    """A callback may test QG behavior but cannot claim live-dispatch provenance."""
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, injected_qg_capture["tier2"])
    artifact = _artifact(injected_qg_capture, authorization, identity)
    assert not _passes(artifact, injected_qg_capture, authorization, identity)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda dispatch: dispatch["author_lineage"].update({"family": "google"}),
        lambda dispatch: dispatch["author_lineage"].update({"family": ""}),
        lambda dispatch: dispatch["author_lineage"].update({"source": ""}),
        lambda dispatch: dispatch["author_lineage"].update({"evidence": ""}),
    ],
    ids=("same-family", "missing-family", "missing-source", "missing-evidence"),
)
def test_live_capture_requires_real_cross_family_author_lineage(
    qg_capture: dict[str, Any], tmp_path: Path, mutation: Any
) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    mutation(artifact.value["tier2"]["dispatch"])
    _mirror_tier(artifact)
    assert not _passes(artifact, qg_capture, authorization, identity)


@pytest.mark.parametrize("key", ["module_id", "content_sha"])
def test_wrong_target_or_content_hash_fails(
    qg_capture: dict[str, Any], tmp_path: Path, key: str
) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    artifact.value["canonical_record"][key] = "wrong/target" if key == "module_id" else _sha("wrong-content")
    assert not _passes(artifact, qg_capture, authorization, identity)


@pytest.mark.parametrize(
    ("container", "key"),
    [
        ("qg_workflow", "prompt_hash"),
        ("qg_workflow", "gate_version"),
        ("qg_workflow", "checker_version"),
        ("qg_workflow", "checker_config_hash"),
        ("level_policy", "family"),
    ],
)
def test_current_qg_contract_fact_mismatches_fail(
    qg_capture: dict[str, Any], tmp_path: Path, container: str, key: str
) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    artifact.value["canonical_record"][container][key] = "wrong"
    assert not _passes(artifact, qg_capture, authorization, identity)


@pytest.mark.parametrize("field", ["raw_response_sha256", "workflow_run_id", "tier2_run_id", "attempt_id"])
def test_raw_response_and_run_linkage_mismatches_fail(
    qg_capture: dict[str, Any], tmp_path: Path, field: str
) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    artifact.value["tier2"][field] = _sha("wrong") if field == "raw_response_sha256" else "wrong"
    assert not _passes(artifact, qg_capture, authorization, identity)


@pytest.mark.parametrize("flag", ["shadow", "advisory", "attested_judge"])
def test_shadow_advisory_and_attested_judge_arms_fail(
    qg_capture: dict[str, Any], tmp_path: Path, flag: str
) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    artifact.value["tier2"]["dispatch"][flag] = True
    _mirror_tier(artifact)
    assert not _passes(artifact, qg_capture, authorization, identity)


def test_cache_replay_is_the_only_cache_admissibility_path(qg_capture: dict[str, Any], tmp_path: Path) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    artifact.value["tier2"]["status"] = "cache_hit"
    _mirror_tier(artifact)
    assert not _passes(artifact, qg_capture, authorization, identity)
    artifact.value["tier2"]["cache_regate"] = "replayed"
    _mirror_tier(artifact)
    # A field-flipped result is not a replay: it has no cache-run linkage nor
    # persisted replay-grade capture.  The actual two-run test below is the
    # only admissible replay construction.
    assert not _passes(artifact, qg_capture, authorization, identity)
    artifact.value["tier2"]["status"] = "ran"
    _mirror_tier(artifact)
    assert not _passes(artifact, qg_capture, authorization, identity)


def test_real_cache_replay_is_complete_and_certification_admissible(
    qg_replay_capture: dict[str, Any], tmp_path: Path
) -> None:
    tier2 = qg_replay_capture["tier2"]
    assert qg_replay_capture["calls"] == 1
    assert tier2["status"] == "cache_hit"
    assert tier2["cache_regate"] == "replayed"
    assert {
        "source",
        "workflow_run_id",
        "tier2_run_id",
        "attempt_id",
        "dispatch",
        "payload",
        "raw_response",
        "raw_response_sha256",
        "retry_history",
        "gate_outcomes",
    } <= set(tier2)
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, tier2)
    artifact = _artifact(qg_replay_capture, authorization, identity)
    assert _passes(artifact, qg_replay_capture, authorization, identity)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda tier: tier.update({"raw_response": ""}),
        lambda tier: tier["dispatch"].pop("tool_events"),
        lambda tier: tier.update({"retry_history": []}),
        lambda tier: tier["dispatch"].update({"tools_used": []}),
        lambda tier: tier["dispatch"].pop("author_lineage"),
    ],
    ids=("missing-raw", "missing-tool-events", "missing-retry", "missing-tools", "missing-live-lineage"),
)
def test_cache_replay_with_incomplete_capture_cannot_certify(
    qg_replay_capture: dict[str, Any], tmp_path: Path, mutation: Any
) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_replay_capture["tier2"])
    artifact = _artifact(qg_replay_capture, authorization, identity)
    mutation(artifact.value["tier2"])
    _mirror_tier(artifact)
    assert not _passes(artifact, qg_replay_capture, authorization, identity)


@pytest.mark.parametrize("state", ["unavailable", "provider_error", "cost_overrun", "canary_required", "circuit_open"])
def test_forbidden_workflow_states_fail_closed(qg_capture: dict[str, Any], tmp_path: Path, state: str) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    artifact.value["tier2"]["gate_outcomes"]["reason"] = state
    _mirror_tier(artifact)
    assert not _passes(artifact, qg_capture, authorization, identity)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda tier: tier["dispatch"].update({"tool_events": [], "tool_call_count": 0, "tools_used": []}),
        lambda tier: tier["dispatch"]["tool_events"][0].update({"tool": "mcp__fake__search"}),
        lambda tier: tier["payload"]["fact_checks"][0]["grounding"].update({"tool_call_id": "fake-call"}),
        lambda tier: tier["payload"]["fact_checks"][0]["grounding"].update({"query": "unrelated query"}),
        lambda tier: tier["payload"]["fact_checks"][0]["grounding"].update({"evidence_excerpt": "fabricated excerpt"}),
        lambda tier: tier["payload"]["fact_checks"][0]["grounding"].update({"evidence_excerpt": "Веснянки nonexistent пісні"}),
        lambda tier: tier["dispatch"]["tool_events"][0]["input"].update({"mode": "summary"}),
    ],
)
def test_grounding_and_tool_theatre_bypasses_fail(
    qg_capture: dict[str, Any], tmp_path: Path, mutation: Any
) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    mutation(artifact.value["tier2"])
    _mirror_tier(artifact)
    assert not _passes(artifact, qg_capture, authorization, identity)


def test_genuine_captured_section_event_passes_grounding(qg_capture: dict[str, Any], tmp_path: Path) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    assert _passes(_artifact(qg_capture, authorization, identity), qg_capture, authorization, identity)


def test_normalized_source_tool_event_is_admissible(qg_capture: dict[str, Any], tmp_path: Path) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    artifact = _artifact(qg_capture, authorization, identity)
    artifact.value["tier2"]["dispatch"]["tool_events"][0]["tool"] = "sources_query_wikipedia"
    artifact.value["tier2"]["dispatch"]["tools_used"] = ["sources_query_wikipedia"]
    artifact.value["tier2"]["retry_history"][-1]["dispatch"]["tool_events"][0]["tool"] = "sources_query_wikipedia"
    artifact.value["tier2"]["retry_history"][-1]["dispatch"]["tools_used"] = ["sources_query_wikipedia"]
    _mirror_tier(artifact)
    assert _passes(artifact, qg_capture, authorization, identity)


def test_authorization_is_strict_and_human_bound(qg_capture: dict[str, Any], tmp_path: Path) -> None:
    identity = _identity()
    authorization, qg_profile = _authorization(tmp_path, identity, qg_capture["tier2"])
    assert authorization["route"] == _route(identity, qg_capture["tier2"])

    arming_path = tmp_path / qg_profile["human_arming_artifact"]
    arming = json.loads(arming_path.read_text(encoding="utf-8"))
    arming["actor_type"] = "llm"
    arming_path.write_text(json.dumps(arming), encoding="utf-8")
    with pytest.raises(ce.CertificationEvidenceError):
        ce.load_authorization(qg_profile, repo_root=tmp_path, expected_profile={"id": "seminar-pending", "version": "1.0.0"}, expected_identity=identity)


def test_qualification_stale_identity_wrong_route_and_empty_artifact_fail(qg_capture: dict[str, Any], tmp_path: Path) -> None:
    identity = _identity()
    _, qg_profile = _authorization(tmp_path, identity, qg_capture["tier2"])
    qualification_path = tmp_path / qg_profile["qualification_artifact"]
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    qualification["identity"]["prompt"] = _sha("stale")
    qualification_path.write_text(json.dumps(qualification), encoding="utf-8")
    with pytest.raises(ce.CertificationEvidenceError):
        ce.load_authorization(qg_profile, repo_root=tmp_path, expected_profile={"id": "seminar-pending", "version": "1.0.0"}, expected_identity=identity)
    qualification_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ce.CertificationEvidenceError):
        ce.load_authorization(qg_profile, repo_root=tmp_path, expected_profile={"id": "seminar-pending", "version": "1.0.0"}, expected_identity=identity)


def test_qualification_wrong_profile_route_and_arbitrary_identity_key_fail(qg_capture: dict[str, Any], tmp_path: Path) -> None:
    identity = _identity()
    _, qg_profile = _authorization(tmp_path, identity, qg_capture["tier2"])
    qualification_path = tmp_path / qg_profile["qualification_artifact"]
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    original = copy.deepcopy(qualification)
    qualification["profile"]["id"] = "wrong-profile"
    qualification_path.write_text(json.dumps(qualification), encoding="utf-8")
    with pytest.raises(ce.CertificationEvidenceError):
        ce.load_authorization(qg_profile, repo_root=tmp_path, expected_profile={"id": "seminar-pending", "version": "1.0.0"}, expected_identity=identity)
    qualification = original
    qualification["identity"]["unexpected"] = _sha("unexpected")
    qualification_path.write_text(json.dumps(qualification), encoding="utf-8")
    with pytest.raises(ce.CertificationEvidenceError):
        ce.load_authorization(qg_profile, repo_root=tmp_path, expected_profile={"id": "seminar-pending", "version": "1.0.0"}, expected_identity=identity)


def test_qg_stability_uses_immutable_inputs_and_material_disposition(qg_capture: dict[str, Any], tmp_path: Path) -> None:
    identity = _identity()
    authorization, _ = _authorization(tmp_path, identity, qg_capture["tier2"])
    first = _artifact(qg_capture, authorization, identity)
    second = copy.deepcopy(first)
    assert ce.production_qg_stability_key(first) == ce.production_qg_stability_key(second)
    second.value["canonical_record"]["terminal_verdict"] = "FAIL"
    second.value["canonical_record"]["workflow_verdict"] = "FAIL"
    assert ce.production_qg_material_fingerprint(first) != ce.production_qg_material_fingerprint(second)
    second.value["tier2"]["dispatch"]["route_name"] = "different-route"
    assert ce.production_qg_stability_key(first) != ce.production_qg_stability_key(second)


def test_unchanged_qg_inputs_with_divergent_material_results_project_instability(
    qg_capture: dict[str, Any], tmp_path: Path
) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    profiles_path = repo / "agents_extensions/shared/curriculum-lifecycle/config/certification-profiles.v1.yaml"
    profiles = yaml.safe_load(profiles_path.read_text(encoding="utf-8"))
    profiles["profiles"]["core-pending"]["production_qg"] = {
        "adapter": "production-qg.v1",
        "mode": "armed-canary",
        "qualification_artifact": "qualification.json",
        "human_arming_artifact": "arming.json",
    }
    profiles_path.write_text(yaml.safe_dump(profiles, sort_keys=False), encoding="utf-8")
    qualification_path = repo / "qualification.json"
    arming_path = repo / "arming.json"
    qualification_path.write_text("{}\n", encoding="utf-8")
    arming_path.write_text("{}\n", encoding="utf-8")
    inputs = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)
    route = _route(inputs["qg_identity"], qg_capture["tier2"])
    qualification = {
        "schema_version": "production-qg-qualification.v1",
        "verdict": "PASS",
        "profile": inputs["profile"],
        "identity": inputs["qg_identity"],
        "route": route,
    }
    qualification_path.write_text(json.dumps(qualification, sort_keys=True), encoding="utf-8")
    arming = {
        "schema_version": "production-qg-human-arming.v1",
        "decision": "ARMED",
        "actor_type": "human",
        "actor_id": "operator-1",
        "approval_id": "approval-1",
        "qualification_sha256": hashlib.sha256(qualification_path.read_bytes()).hexdigest(),
        "profile": inputs["profile"],
        "route": route,
        "budget": route["budget"],
    }
    arming_path.write_text(json.dumps(arming, sort_keys=True), encoding="utf-8")
    authorization = ce.load_authorization(
        inputs["profile_config"]["production_qg"],
        repo_root=repo,
        expected_profile=inputs["profile"],
        expected_identity=inputs["qg_identity"],
    )

    first = _artifact(qg_capture, authorization, inputs["qg_identity"])
    first.value.update(
        {
            "target": inputs["target"],
            "profile": inputs["profile"],
            "preparation_identity": inputs["preparation_identity"],
            "learner_hashes": inputs["learner_hashes"],
        }
    )
    second = copy.deepcopy(first)
    second.value["canonical_record"]["terminal_verdict"] = "FAIL"
    second.value["canonical_record"]["workflow_verdict"] = "FAIL"
    ce.validate_evidence_value(first.value)
    ce.validate_evidence_value(second.value)

    independent_sha = _sha("independent-current")
    ledger["certification_evidence"] = [
        {"path": "/outside/independent.json", "sha256": independent_sha, "value": _independent_value(inputs)},
        {
            "path": "/outside/integration.json",
            "sha256": _sha("integration-current"),
            "value": _integration_value(inputs, independent_sha),
        },
        {"path": "/outside/qg-first.json", "sha256": _sha("qg-first"), "value": first.value},
        {"path": "/outside/qg-second.json", "sha256": _sha("qg-second"), "value": second.value},
    ]
    path = _completion_ledger_path(repo, config_path, ledger_root, inputs)
    tc._atomic_write_json(path, ledger)

    projection = tc.certification_projection(
        inputs["target"], repo_root=repo, config_path=config_path, ledger_root=ledger_root
    )
    assert projection["state"] == "REVIEWER_INSTABILITY"
    assert projection["production_qg"] == "instability"
    assert projection["final"] == "not-certified"


def test_stale_independent_evidence_cannot_satisfy_an_integration_link(tmp_path: Path) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    current_value = _independent_value(inputs)
    stale_value = _independent_value(inputs, stale=True)
    ce.validate_evidence_value(current_value)
    ce.validate_evidence_value(stale_value)
    current_sha, stale_sha = _sha("current-independent"), _sha("stale-independent")
    integration = _integration_value(inputs, stale_sha)
    ce.validate_evidence_value(integration)
    ledger["certification_evidence"] = [
        {"path": "/outside/current.json", "sha256": current_sha, "value": current_value},
        {"path": "/outside/stale.json", "sha256": stale_sha, "value": stale_value},
        {"path": "/outside/integration.json", "sha256": _sha("integration"), "value": integration},
    ]
    path = tc.ledger_path_for(tc.resolve_target(inputs["target"], repo_root=repo, config=tc.load_config(config_path)), repo_root=repo, config=tc.load_config(config_path), ledger_root=ledger_root)
    tc._atomic_write_json(path, ledger)

    projection = tc.certification_projection(inputs["target"], repo_root=repo, config_path=config_path, ledger_root=ledger_root)
    assert projection["state"] == "INTEGRATION_REQUIRED"
    assert projection["integration"] == "malformed"


def test_current_unresolved_independent_material_finding_blocks_a_pass(tmp_path: Path) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    passing = _independent_value(inputs)
    unresolved = _independent_value(inputs, unresolved=True)
    ce.validate_evidence_value(passing)
    ce.validate_evidence_value(unresolved)
    ledger["certification_evidence"] = [
        {"path": "/outside/pass.json", "sha256": _sha("pass"), "value": passing},
        {"path": "/outside/open.json", "sha256": _sha("open"), "value": unresolved},
    ]
    path = tc.ledger_path_for(tc.resolve_target(inputs["target"], repo_root=repo, config=tc.load_config(config_path)), repo_root=repo, config=tc.load_config(config_path), ledger_root=ledger_root)
    tc._atomic_write_json(path, ledger)

    projection = tc.certification_projection(inputs["target"], repo_root=repo, config_path=config_path, ledger_root=ledger_root)
    assert projection["state"] == "INDEPENDENT_REVIEW_REQUIRED"
    assert projection["independent_review"] == "unresolved"


def test_qg_only_drift_preserves_preparation_pbr_and_integration_bindings(tmp_path: Path) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    current = _independent_value(inputs)
    current_sha = _sha("current-independent")
    integration = _integration_value(inputs, current_sha)
    ledger["certification_evidence"] = [
        {"path": "/outside/current.json", "sha256": current_sha, "value": current},
        {"path": "/outside/integration.json", "sha256": _sha("integration"), "value": integration},
    ]
    path = tc.ledger_path_for(tc.resolve_target(inputs["target"], repo_root=repo, config=tc.load_config(config_path)), repo_root=repo, config=tc.load_config(config_path), ledger_root=ledger_root)
    tc._atomic_write_json(path, ledger)
    before = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)
    prompt_dependency = repo / "scripts/audit/prompts/reviewer_prompt.md"
    prompt_dependency.write_text(prompt_dependency.read_text(encoding="utf-8") + "\n<!-- qg-only drift -->\n", encoding="utf-8")
    after = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)

    assert after["preparation_identity"] == before["preparation_identity"]
    assert after["pbr_dependency_identity"] == before["pbr_dependency_identity"]
    assert after["qg_identity"] != before["qg_identity"]
    projection = tc.certification_projection(inputs["target"], repo_root=repo, config_path=config_path, ledger_root=ledger_root)
    assert projection["post_build"] == "current"
    assert projection["integration"] == "current"
    assert projection["production_qg"] == "pending"


def test_actual_qg_policy_source_drift_changes_only_qg_identity(tmp_path: Path) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    current = _independent_value(inputs)
    current_sha = _sha("current-independent")
    integration = _integration_value(inputs, current_sha)
    ledger["certification_evidence"] = [
        {"path": "/outside/current.json", "sha256": current_sha, "value": current},
        {"path": "/outside/integration.json", "sha256": _sha("integration"), "value": integration},
    ]
    path = tc.ledger_path_for(
        tc.resolve_target(inputs["target"], repo_root=repo, config=tc.load_config(config_path)),
        repo_root=repo,
        config=tc.load_config(config_path),
        ledger_root=ledger_root,
    )
    tc._atomic_write_json(path, ledger)
    before = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)
    policy_source = repo / "scripts/audit/content_surface_gates.py"
    policy_source.write_text(policy_source.read_text(encoding="utf-8") + "\n# qg policy identity drift\n", encoding="utf-8")
    after = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)

    assert after["qg_identity"] != before["qg_identity"]
    assert after["preparation_identity"] == before["preparation_identity"]
    assert after["pbr_dependency_identity"] == before["pbr_dependency_identity"]
    projection = tc.certification_projection(inputs["target"], repo_root=repo, config_path=config_path, ledger_root=ledger_root)
    assert projection["post_build"] == "current"
    assert projection["integration"] == "current"
    assert projection["production_qg"] == "pending"


@pytest.mark.parametrize(
    "relative_path",
    [
        "scripts/audit/curriculum_qg_harness.py",
        "scripts/audit/qg_adapters.py",
        "scripts/audit/llm_qg_canaries.py",
        "scripts/audit/anchor_primitives.py",
    ],
    ids=("checker-config", "deterministic-adapter", "canary-definitions", "grounding-normalizer"),
)
def test_live_qg_dependency_drift_changes_qg_identity_only(tmp_path: Path, relative_path: str) -> None:
    repo, config_path, _ledger_root, ledger, inputs = _completion_case(tmp_path)
    before = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)
    dependency = repo / relative_path
    dependency.write_text(dependency.read_text(encoding="utf-8") + "\n# qg dependency identity drift\n", encoding="utf-8")
    after = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)

    assert after["qg_identity"] != before["qg_identity"]
    assert after["preparation_identity"] == before["preparation_identity"]
    assert after["pbr_dependency_identity"] == before["pbr_dependency_identity"]


def test_learner_mutation_stales_both_pbr_and_qg_inputs(tmp_path: Path) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    before = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)
    content = repo / "curriculum/l2-uk-en/b1/adjectives-comparative/module.md"
    content.write_text(content.read_text(encoding="utf-8") + "\nЗміна учнівського тексту.\n", encoding="utf-8")
    after = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)

    assert after["learner_hashes"] != before["learner_hashes"]
    assert after["preparation_identity"] == before["preparation_identity"]
    assert tc._current_pbr_reviews(ledger, after)[0] is False
    assert after["target"] == before["target"]
    assert after["qg_identity"] == before["qg_identity"]
    projection = tc.certification_projection(inputs["target"], repo_root=repo, config_path=config_path, ledger_root=ledger_root)
    assert projection["state"] == "POST_BUILD_REVIEW_REQUIRED"


def test_in_repository_runtime_evidence_is_rejected_before_ledger_lookup(tmp_path: Path) -> None:
    value = {
        "schema_version": "certification-evidence.v1",
        "kind": "independent-review",
        "target": "b1/demo",
        "profile": {"id": "core-pending", "version": "1.0.0"},
        "preparation_identity": _sha("preparation"),
        "learner_hashes": {"content": _sha("content")},
        "mutation_identity": _sha("mutation"),
        "diff_sha256": _sha("diff"),
        "review": {
            "author_families": ["codex"],
            "reviewer_family": "gemini",
            "verdict": "PASS",
            "material_findings": [],
            "resolution_state": "RESOLVED",
            "raw_response_sha256": _sha("raw"),
        },
    }
    evidence = tmp_path / "runtime-evidence.json"
    evidence.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(tc.CompletionError, match="outside the common repository"):
        tc.record_certification_evidence("b1/demo", run_id="ignored", evidence=evidence, repo_root=tmp_path)


def _write_external_evidence(tmp_path: Path, name: str, value: dict[str, Any]) -> Path:
    path = tmp_path / "outside-evidence" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _completion_ledger_path(
    repo: Path, config_path: Path, ledger_root: Path, inputs: dict[str, Any]
) -> Path:
    config = tc.load_config(config_path)
    snapshot = tc.resolve_target(inputs["target"], repo_root=repo, config=config)
    return tc.ledger_path_for(snapshot, repo_root=repo, config=config, ledger_root=ledger_root)


def test_cursor_advances_current_independent_evidence_with_true_history_origin(tmp_path: Path) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    ledger["state"] = "INDEPENDENT_REVIEW_REQUIRED"
    path = _completion_ledger_path(repo, config_path, ledger_root, inputs)
    tc._atomic_write_json(path, ledger)
    evidence = _write_external_evidence(tmp_path, "independent.json", _independent_value(inputs))

    _, updated = tc.record_certification_evidence(
        inputs["target"],
        run_id=ledger["run"]["run_id"],
        evidence=evidence,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )

    event = next(item for item in updated["history"] if item["event"] == "CERTIFICATION_CURSOR_ADVANCED")
    assert updated["state"] == "INTEGRATION_REQUIRED"
    assert event["from_state"] == "INDEPENDENT_REVIEW_REQUIRED"
    assert event["to_state"] == "INTEGRATION_REQUIRED"


@pytest.mark.parametrize(
    ("mode", "expected"),
    [("pending", "PBR_PASS_QG_PENDING"), ("armed-canary", "PRODUCTION_QG_REQUIRED")],
)
def test_cursor_advances_current_integration_to_the_profile_qg_state(
    tmp_path: Path, mode: str, expected: str
) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    if mode == "armed-canary":
        profiles_path = repo / "agents_extensions/shared/curriculum-lifecycle/config/certification-profiles.v1.yaml"
        profiles = yaml.safe_load(profiles_path.read_text(encoding="utf-8"))
        profiles["profiles"]["core-pending"]["production_qg"] = {
            "adapter": "production-qg.v1",
            "mode": "armed-canary",
            "qualification_artifact": "qualification.json",
            "human_arming_artifact": "arming.json",
        }
        profiles_path.write_text(yaml.safe_dump(profiles, sort_keys=False), encoding="utf-8")
        (repo / "qualification.json").write_text("{}\n", encoding="utf-8")
        (repo / "arming.json").write_text("{}\n", encoding="utf-8")
        inputs = tc.certification_inputs(inputs["target"], repo_root=repo, config_path=config_path, ledger=ledger)
    ledger["state"] = "INDEPENDENT_REVIEW_REQUIRED"
    path = _completion_ledger_path(repo, config_path, ledger_root, inputs)
    tc._atomic_write_json(path, ledger)
    independent = _write_external_evidence(tmp_path, "independent.json", _independent_value(inputs))
    _, after_independent = tc.record_certification_evidence(
        inputs["target"],
        run_id=ledger["run"]["run_id"],
        evidence=independent,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    independent_sha = hashlib.sha256(independent.read_bytes()).hexdigest()
    integration = _write_external_evidence(tmp_path, "integration.json", _integration_value(inputs, independent_sha))

    _, updated = tc.record_certification_evidence(
        inputs["target"],
        run_id=after_independent["run"]["run_id"],
        evidence=integration,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )

    event = [item for item in updated["history"] if item["event"] == "CERTIFICATION_CURSOR_ADVANCED"][-1]
    assert updated["state"] == expected
    assert event["from_state"] == "INTEGRATION_REQUIRED"
    assert event["to_state"] == expected


def test_stale_certification_evidence_never_advances_cursor(tmp_path: Path) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    ledger["state"] = "INDEPENDENT_REVIEW_REQUIRED"
    path = _completion_ledger_path(repo, config_path, ledger_root, inputs)
    tc._atomic_write_json(path, ledger)
    evidence = _write_external_evidence(tmp_path, "stale-independent.json", _independent_value(inputs, stale=True))

    _, updated = tc.record_certification_evidence(
        inputs["target"],
        run_id=ledger["run"]["run_id"],
        evidence=evidence,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )

    assert updated["state"] == "INDEPENDENT_REVIEW_REQUIRED"
    assert not any(item["event"] == "CERTIFICATION_CURSOR_ADVANCED" for item in updated["history"])


def test_malformed_certification_evidence_never_advances_cursor(tmp_path: Path) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    ledger["state"] = "INDEPENDENT_REVIEW_REQUIRED"
    path = _completion_ledger_path(repo, config_path, ledger_root, inputs)
    tc._atomic_write_json(path, ledger)
    evidence = tmp_path / "outside-evidence" / "malformed.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("{}\n", encoding="utf-8")

    with pytest.raises(tc.certification.CertificationEvidenceError):
        tc.record_certification_evidence(
            inputs["target"],
            run_id=ledger["run"]["run_id"],
            evidence=evidence,
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )

    unchanged = tc._read_ledger(path)
    assert unchanged is not None
    assert unchanged["state"] == "INDEPENDENT_REVIEW_REQUIRED"
    assert not any(item["event"] == "CERTIFICATION_CURSOR_ADVANCED" for item in unchanged["history"])


def test_completed_provisional_run_resumes_for_fresh_qg_without_legacy_authority(tmp_path: Path) -> None:
    repo, config_path, ledger_root, ledger, inputs = _completion_case(tmp_path)
    independent = _independent_value(inputs)
    independent_sha = _sha("independent")
    integration = _integration_value(inputs, independent_sha)
    ledger["certification_evidence"] = [
        {"path": "/outside/independent.json", "sha256": independent_sha, "value": independent},
        {"path": "/outside/integration.json", "sha256": _sha("integration"), "value": integration},
    ]
    ledger["state"] = "COMPLETE"
    ledger["run"]["status"] = "completed"
    ledger["publication"] = {"pr": 1, "merge_sha": "a" * 40, "recorded_at": "2026-01-01T00:00:00Z"}
    path = _completion_ledger_path(repo, config_path, ledger_root, inputs)
    tc._atomic_write_json(path, ledger)

    _, resumed = tc.resume_run(
        inputs["target"],
        run_id=ledger["run"]["run_id"],
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )

    event = [item for item in resumed["history"] if item["event"] == "CERTIFICATION_RESUMED"][-1]
    assert resumed["run"]["status"] == "active"
    assert resumed["state"] == "PBR_PASS_QG_PENDING"
    assert event["from_state"] == "COMPLETE"
    assert tc.certification_projection(inputs["target"], repo_root=repo, config_path=config_path, ledger_root=ledger_root)[
        "final"
    ] == "provisional"


def test_common_repository_tree_rejects_primary_current_and_sibling_worktree_evidence(tmp_path: Path) -> None:
    repo, config_path, _ledger_root, _ledger, inputs = _completion_case(tmp_path)
    git_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True, env=git_env)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True, text=True, env=git_env)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-m", "fixture"],
        check=True,
        capture_output=True,
        text=True,
        env=git_env,
    )
    current = repo / ".worktrees/dispatch/codex/current"
    sibling = repo / ".worktrees/dispatch/codex/sibling"
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "-b", "fixture-current", str(current)],
        check=True,
        capture_output=True,
        text=True,
        env=git_env,
    )
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "-b", "fixture-sibling", str(sibling)],
        check=True,
        capture_output=True,
        text=True,
        env=git_env,
    )
    current_config = current / config_path.relative_to(repo)
    current_ledger_root = tmp_path / "ledgers-current"
    _, current_ledger = tc.start_run(
        inputs["target"],
        owner="codex/test",
        repo_root=current,
        config_path=current_config,
        ledger_root=current_ledger_root,
    )
    value = _independent_value(inputs)
    for _name, evidence in {
        "current": current / "batch_state/current.json",
        "primary": repo / "batch_state/primary.json",
        "sibling": sibling / "batch_state/sibling.json",
    }.items():
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(json.dumps(value), encoding="utf-8")
        with pytest.raises(tc.CompletionError, match="outside the common repository"):
            tc.record_certification_evidence(
                inputs["target"],
                run_id=current_ledger["run"]["run_id"],
                evidence=evidence,
                repo_root=current,
                config_path=current_config,
                ledger_root=current_ledger_root,
            )
        with pytest.raises(tc.CompletionError, match="outside the common repository"):
            tc.record_review(
                inputs["target"],
                run_id=current_ledger["run"]["run_id"],
                result_path=evidence,
                repo_root=current,
                config_path=current_config,
                ledger_root=current_ledger_root,
            )

    outside = _write_external_evidence(tmp_path, "outside-common.json", value)
    _, updated = tc.record_certification_evidence(
        inputs["target"],
        run_id=current_ledger["run"]["run_id"],
        evidence=outside,
        repo_root=current,
        config_path=current_config,
        ledger_root=current_ledger_root,
    )
    assert updated["certification_evidence"][-1]["path"] == str(outside.resolve())


def test_legacy_qg_artifacts_are_not_certification_evidence(tmp_path: Path) -> None:
    legacy = tmp_path / "llm_qg.json"
    legacy.write_text('{"verdict": "PASS", "state": "COMPLETE"}', encoding="utf-8")
    with pytest.raises(ce.CertificationEvidenceError):
        ce.read_evidence(legacy)


def test_certification_profile_selection_is_level_sensitive_and_unarmed() -> None:
    config_path = ROOT / "agents_extensions/shared/curriculum-lifecycle/config/certification-profiles.v1.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert {config["selectors"]["tracks"][level] for level in ("a1", "a2")} == {"core-disabled"}
    assert {config["selectors"]["tracks"][level] for level in ("b1", "b2", "c1", "c2")} == {"core-pending"}
    assert config["selectors"]["tracks"]["bio"] == "bio-pending"
    assert config["selectors"]["manifest_types"]["core"] == "core-pending"
    assert config["selectors"]["manifest_types"]["track"] == "seminar-pending"
    assert all(profile["production_qg"]["mode"] != "armed-canary" for profile in config["profiles"].values())
