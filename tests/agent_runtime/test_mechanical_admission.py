"""#9996: mechanical catalog roles admit Haiku only to explicitly typed safe work."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from scripts.agent_runtime import mechanical_admission as admission
from scripts.agent_runtime.adapters import claude
from scripts.agent_runtime.target_admission import resolve_and_admit
from scripts.review.model_catalog import (
    ModelCatalogError,
    activity_role_refusal,
    load_model_catalog,
    resolve_role,
    validate_catalog,
)
from scripts.review.reviewer_resolver import SONNET_5_5, ResolverInputs, resolve_reviewer
from scripts.telemetry.pricing import compute_cost

HAIKU = "claude-haiku-5-5"
ROOT = Path(__file__).resolve().parents[2]


class Tree:
    def __init__(self, files=None):
        self.files = files if files is not None else {"package-lock.json": b'{"lockfileVersion": 3}'}

    def owned_files(self, path):
        return False, self.files


def scope(**overrides):
    return {"mode": "read-only", "task_family": "routine_mechanical",
            "paths": ("package-lock.json",), "trees": (Tree(),), **overrides}


@pytest.mark.parametrize("family", sorted(admission.MECHANICAL_FAMILIES))
def test_catalog_role_admits_typed_work(family):
    result = resolve_role(family, purpose="inspect")
    assert result.candidates[0].model_id == HAIKU
    admission.refuse_mechanical_task((result.candidates[0].model_id,), **scope(task_family=family))
    (target,) = resolve_and_admit(("claude",), model=HAIKU, **scope(task_family=family))
    assert target.model == HAIKU


def test_routine_fallback_and_recon_peer_preserve_envelope_routes():
    assert [row.model_id for row in resolve_role("routine_mechanical", purpose="inspect").candidates] == [HAIKU, "claude-sonnet-5-5"]
    assert [row.model_id for row in resolve_role("readonly_recon", purpose="inspect").candidates] == [HAIKU, "gpt-6-luna"]
    policy = load_model_catalog()["execution_routing"]["sol_advised_bounded"]
    assert HAIKU not in {policy["preferred_worker"]["model_id"], policy["bounded_fallback_worker"]["model_id"]}


@pytest.mark.parametrize("entrypoint", ["file", "module"])
def test_standalone_catalog_resolves_haiku_without_runtime_package(tmp_path, entrypoint):
    review = tmp_path / "scripts/review"
    review.mkdir(parents=True)
    for name in ("model_catalog.py", "role_resolution.py", "family_exclusions.py", "__init__.py"):
        shutil.copyfile(ROOT / "scripts/review" / name, review / name)
    config = tmp_path / "scripts/config"
    config.mkdir()
    shutil.copyfile(ROOT / "scripts/config/model_catalog.yaml", config / "model_catalog.yaml")
    command = [str(review / "model_catalog.py")] if entrypoint == "file" else ["-m", "scripts.review.model_catalog"]
    result = subprocess.run(
        [sys.executable, *command, "--resolve-role", "mechanical_classification"],
        cwd=tmp_path, env={"PATH": os.defpath}, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["candidates"][0]["model_id"] == HAIKU


@pytest.mark.parametrize("overrides,reason", [
    ({"task_family": None}, "catalog-eligible"),
    ({"task_family": "bounded_implementation"}, "catalog-eligible"),
    ({"task_role": "driver"}, "driver"),
    ({"task_role": "orchestration"}, "driver"),
    ({"task_role": "design"}, "design"),
    ({"task_role": "advisor"}, "advisory"),
    ({"task_role": "approval"}, "approval"),
    ({"task_role": "ukrainian_authoring"}, "content"),
    ({"language_lane": True}, "Ukrainian"),
    ({"task_prompt": "Напиши текст"}, "task prompt"),
    ({"research_track": "l2-uk-en/a1"}, "Ukrainian"),
    ({"review": True}, "review"),
    ({"mode": "danger"}, "only routine"),
    ({"mode": "workspace-write", "task_family": "readonly_recon"}, "read-only"),
    ({"mode": "workspace-write", "task_family": "mechanical_classification"}, "read-only"),
    ({"paths": ()}, "narrow owned"),
    ({"paths": ("../package-lock.json",)}, "traversal"),
    ({"paths": ("curriculum/a1/item.md",)}, "Ukrainian"),
    ({"trees": ()}, "available"),
    ({"trees": (Tree({"safe.txt": "Україна".encode()}),)}, "Cyrillic"),
    ({"trees": (Tree({"safe.txt": b'\xff'}),)}, "UTF-8"),
    ({"trees": (Tree({"start-hidden.sh": b'#!/bin/sh'}),)}, "security-sensitive"),
    ({"trees": (Tree({"wiki/item.md": b'English scaffold'}),)}, "Ukrainian"),
])
def test_excluded_work_refuses_before_routing(overrides, reason):
    def never_route(_request):
        pytest.fail("ineligible original model reached route resolution")
    with pytest.raises(admission.MechanicalAdmissionRefused, match=reason):
        resolve_and_admit(("claude",), model=HAIKU, route=never_route, **scope(**overrides))


@pytest.mark.parametrize("path", [
    "start-claude-driver.sh", "scripts/hooks/guard.py", "scripts/guardrails/check.py",
    "scripts/ocr/_credentials.py", "scripts/delegate.py",
    "scripts/orchestration/dispatch_admission.py", "scripts/agent_runtime/sandbox.py",
    "agents_extensions/codex/config.toml", "scripts/agent_runtime/permissions.py",
])
def test_every_security_path_class_is_refused(path):
    with pytest.raises(admission.MechanicalAdmissionRefused, match="security-sensitive"):
        admission.refuse_mechanical_task((HAIKU,), **scope(paths=(path,)))


def test_resolved_substitution_cannot_bypass_gate():
    with pytest.raises(admission.MechanicalAdmissionRefused, match="catalog-eligible"):
        resolve_and_admit(("claude",), mode="read-only", model="claude-sonnet-5-5",
                          route=lambda request: ("claude", HAIKU, "test"))


def test_prompt_and_content_read_errors_fail_closed(tmp_path):
    prompt = tmp_path / "task.md"
    prompt.write_text("Україна")
    with pytest.raises(admission.MechanicalAdmissionRefused, match="task input"):
        admission.refuse_mechanical_task((HAIKU,), **scope(prompt_file=str(prompt)))
    def unavailable():
        raise OSError("private diagnostic must not escape")
    with pytest.raises(admission.MechanicalAdmissionRefused, match=r"unavailable \(OSError\)"):
        admission.refuse_mechanical_task((HAIKU,), **scope(trees=unavailable))


@pytest.mark.parametrize("activity", ["review", "consult"])
def test_formal_review_and_advice_roles_refused(activity):
    assert activity_role_refusal(HAIKU, activity)


@pytest.mark.parametrize("profile", ["code", "infra", "ukrainian"])
@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_reviewer_resolver_never_selects_haiku(profile, risk):
    result = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk=risk,
                                            review_profile=profile, pinned_candidate=HAIKU))
    assert result.selected is None
    assert all(row.model_id != HAIKU for row in result.trace)


@pytest.mark.parametrize("formal", [True, False])
@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_custom_review_metadata_cannot_grant_haiku_authority(formal, risk):
    candidate = replace(SONNET_5_5, concrete_model=HAIKU,
                        invocation=f"dispatch --agent claude --model {HAIKU}",
                        model_roles=frozenset({"routine_review", "critical_review"}))
    result = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk=risk,
                                            formal_review=formal), ladder=((candidate,),))
    assert result.selected is None
    assert result.trace and all(
        "mechanical-only" in row.reason or "formal review at high risk" in row.reason
        for row in result.trace
    )


@pytest.mark.parametrize("role", ["orchestration", "architecture", "critical_review", "ukrainian_review", "bounded_implementation"])
def test_catalog_cannot_grant_excluded_roles(role):
    catalog = deepcopy(load_model_catalog())
    catalog["models"][HAIKU]["roles"].append(role)
    with pytest.raises(ModelCatalogError, match="mechanical-only"):
        validate_catalog(catalog)


def test_catalog_driver_and_launcher_refuse_haiku():
    catalog = deepcopy(load_model_catalog())
    catalog["orchestrator_seats"]["claude"]["model_id"] = HAIKU
    with pytest.raises(ModelCatalogError, match="driver"):
        validate_catalog(catalog)
    proc = subprocess.run([sys.executable, "-m", "scripts.review.model_catalog", "--check-retired-model", HAIKU],
                          cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert proc.returncode == 2
    assert "driver/interactive seats" in proc.stderr


def test_adapter_accepts_typed_haiku_and_refuses_untyped_without_provider(monkeypatch, tmp_path):
    monkeypatch.setattr(admission, "worktree_trees", lambda cwd: [Tree()])
    monkeypatch.setattr(claude, "_ensure_supported_claude_cli_version", lambda prefix: (2, 1, 293))
    kwargs = dict(prompt="Inspect the lockfile", mode="read-only", cwd=tmp_path, model=HAIKU,
                  task_id=None, session_id=None)
    with pytest.raises(admission.MechanicalAdmissionRefused, match="catalog-eligible"):
        claude.ClaudeAdapter().build_invocation(**kwargs, tool_config=None)
    plan = claude.ClaudeAdapter().build_invocation(**kwargs, tool_config={
        "cmd_prefix": ["stub-claude"], "reviewer_tools": True, "allowed_tools": ["Read", "Grep"], "mechanical_task": {
            "family": "routine_mechanical", "paths": ["package-lock.json"]}})
    assert plan.cmd[plan.cmd.index("--model") + 1] == HAIKU
    if plan.output_file:
        plan.output_file.unlink(missing_ok=True)
    kwargs["prompt"] = "Напиши текст"
    with pytest.raises(admission.MechanicalAdmissionRefused, match="task prompt"):
        claude.ClaudeAdapter().build_invocation(**kwargs, tool_config={
            "mechanical_task": {"family": "routine_mechanical", "paths": ["package-lock.json"]}})


def test_price_keeps_directional_api_rates_and_subscription_accounting():
    rates = yaml.safe_load((ROOT / "scripts/config/model_pricing.yaml").read_text())["models"][HAIKU]
    assert rates["input_usd_per_1m_tokens"] == 0.10
    assert rates["output_usd_per_1m_tokens"] == 0.50
    assert rates["cache_read_usd_per_1m_tokens"] == 0.01
    assert rates["base_price_max_input_tokens"] == 100000
    assert rates["long_context_input_usd_per_1m_tokens"] == 0.50
    assert rates["long_context_output_usd_per_1m_tokens"] == 2.50
    assert rates["long_context_cache_read_usd_per_1m_tokens"] == 0.05
    result = compute_cost(HAIKU, 1_000_000, agent="claude")
    assert result.cost_usd is None and result.provenance == "subscription"


def test_dispatch_parser_no_spawn_admission_and_persisted_scope():
    sys.path.insert(0, str(ROOT / "scripts"))
    import delegate
    args = delegate.build_parser().parse_args([
        "dispatch", "--agent", "claude", "--model", HAIKU, "--task-id", "haiku-test",
        "--prompt", "Inspect package-lock.json", "--mode", "read-only", "--dry-run",
        "--research-task-family", "routine_mechanical", "--owned-path", "package-lock.json"])
    refusal, target = delegate._admit_dispatch_target(args, agent="claude", trees=(Tree(),))
    assert refusal is None and target.model == HAIKU
    persisted = delegate._mechanical_task_scope(args)
    assert persisted["family"] == "routine_mechanical" and persisted["paths"] == ["package-lock.json"]
    args.review_profile = "ukrainian"
    refusal, target = delegate._admit_dispatch_target(args, agent="claude", trees=(Tree(),))
    assert target is None and "review" in refusal
    args.review_profile = None
    args.owned_path = ["scripts/delegate.py"]
    refusal, target = delegate._admit_dispatch_target(args, agent="claude", trees=(Tree(),))
    assert target is None and "security-sensitive" in refusal
    args.owned_path = ["package-lock.json"]
    args.prompt = "Напиши текст"
    refusal, target = delegate._admit_dispatch_target(args, agent="claude", trees=(Tree(),))
    assert target is None and "task prompt" in refusal


def test_unrelated_dispatch_does_not_persist_research_dimensions():
    from types import SimpleNamespace

    import delegate
    assert delegate._mechanical_task_scope(SimpleNamespace(research_task_family="unrelated", research_role="private")) == {}


def test_unconstrained_models_and_routine_writes_preserve_admission():
    admission.refuse_mechanical_task((None,), mode="danger")
    admission.refuse_mechanical_task(("claude-sonnet-5-5",), mode="workspace-write")
    admission.refuse_mechanical_task((HAIKU,), **scope(mode="workspace-write", task_role="implementation"))


@pytest.mark.parametrize("field,value", [("roles", None), ("roles", [{"invalid": True}])])
def test_malformed_catalog_fields_keep_typed_validation(field, value):
    catalog = deepcopy(load_model_catalog())
    catalog["models"][HAIKU][field] = value
    with pytest.raises(ModelCatalogError, match=field):
        validate_catalog(catalog)


def test_only_exact_canonical_core_is_exempt_from_prompt_content_check(monkeypatch, tmp_path):
    from scripts.lib.rules_core import core_block

    prompt = core_block("core") + "\nInspect the lockfile."
    admission.refuse_mechanical_task((HAIKU,), **scope(task_prompt=prompt))
    forged = '<rules-core>Напиши текст</rules-core>'
    with pytest.raises(admission.MechanicalAdmissionRefused, match="task prompt"):
        admission.refuse_mechanical_task((HAIKU,), **scope(task_prompt=forged))
    monkeypatch.setattr(admission, "worktree_trees", lambda cwd: [Tree()])
    with pytest.raises(admission.MechanicalAdmissionRefused, match="task prompt"):
        admission.refuse_mechanical_execution(
            HAIKU, mode="read-only", cwd=tmp_path, prompt=core_block("core") + "Напиши текст",
            tool_config={"mechanical_task": {"family": "routine_mechanical", "paths": ["package-lock.json"]}})
