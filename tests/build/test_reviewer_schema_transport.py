"""#7810 mechanism canaries, not reviewer-owned semantic held-out cases.

The 18-cell matrix stays fixed even where the production path cannot select a
route. Cross-path protocol tests exercise the shared invocation contract and
each path's real consumer. Separate tests assert the actual production pins.
No ordinary test invokes a provider. Live direct review requires explicit opt-in.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.agent_runtime.adapters._output_schema import load_output_schema
from scripts.audit import llm_reviewer, qg_schema
from scripts.build import build_module_direct as direct
from scripts.build import linear_pipeline as linear

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ("claude", "codex", "gemini", "grok", "cursor", "deepseek", "glm", "agy", "acpx_agy")
SUPPORTED = ("claude", "codex", "grok", "agy")
ADAPTERS = {
    "claude": ("claude", "ClaudeAdapter"),
    "codex": ("codex", "CodexAdapter"),
    "grok": ("grok_build", "GrokBuildAdapter"),
    "agy": ("agy", "AgyAdapter"),
    "cursor": ("cursor", "CursorAdapter"),
    "deepseek": ("deepseek", "DeepSeekAdapter"),
    "glm": ("glm", "GlmAdapter"),
}


def mechanical_payload(profile: str) -> dict[str, Any]:
    """Public synthetic transport data; never a linguistic/held-out oracle."""
    if profile == "dimension":
        return {
            "score": 7.0, "evidence": '"mechanical fixture quote"',
            "evidence_quotes": ["mechanical fixture quote"],
            "rubric_mapping": "Quote maps to a synthetic defect.",
            "issue_ids": ["MECHANICAL_FIXTURE"],
            "findings": [{
                "issue_id": "MECHANICAL_FIXTURE", "quote": "mechanical fixture quote",
                "severity": "high", "explanation": "Synthetic transport defect.",
                "replacement": None, "dimension": None,
            }],
            "flags": ["mechanical_flag"], "verdict": "REVISE",
        }
    if profile == "direct":
        return {
            "verdict": "FAIL", "summary": "Synthetic transport defect.",
            "dimensions": {
                dim: {"status": "FAIL" if dim == "activities" else "PASS", "notes": "Mechanical note."}
                for dim in ("language", "pedagogy", "activities", "l1_agnosticism", "decodability")
            },
            "issues": ["activities[0]: mechanical fixture defect"],
        }
    return {
        "findings": [{
            "issue_id": "MECHANICAL_FIXTURE", "issue_class": "other", "dimension": "mechanics",
            "severity": "warning", "excerpt": "fixture ```json text", "message": "Synthetic defect.",
            "suggested_replacement": None, "grounding": None,
        }],
        "fact_checks": [], "evidence_gaps": [],
    }


def adapter_for(route: str, monkeypatch: pytest.MonkeyPatch):
    module_name, class_name = ADAPTERS[route]
    module = importlib.import_module(f"scripts.agent_runtime.adapters.{module_name}")
    monkeypatch.setattr(module.shutil, "which", lambda command: f"/usr/bin/{command}")
    if route == "claude":
        monkeypatch.setattr(module, "_ensure_supported_claude_cli_version", lambda _: (2, 1, 200))
    if route == "glm":
        # These tests only build plans; no provider executes. Exercise the
        # unsupported-schema contract in CI independently of the egress guard,
        # whose refusal behavior is covered by test_agent_runtime_glm_adapter.
        monkeypatch.setattr(module, "assert_glm_egress_allowed", lambda _: None)
    return getattr(module, class_name)()


def build_plan(adapter, cwd: Path, config: dict[str, Any], *, model=None):
    return adapter.build_invocation(
        prompt="Public mechanical schema fixture.", mode="read-only", cwd=cwd,
        model=model, task_id="qg-schema-mechanics", session_id=None, tool_config=config,
    )


def terminal_output(route: str, payload: Any) -> str:
    if route == "claude":
        return json.dumps({
            "type": "result", "subtype": "success", "is_error": False,
            "structured_output": payload,
            # Decoy proves that findings come from structured_output alone.
            "result": '{"findings": [], "verdict": "PASS"}',
        })
    if route == "agy":
        return json.dumps({"status": "SUCCESS", "structured_output": payload, "response": "decoy prose"})
    if route == "grok":
        return json.dumps({"stopReason": "end_turn", "structuredOutput": payload, "text": "decoy prose"})
    return json.dumps(payload)


def parse_terminal(adapter, plan, route: str, wire: str, *, returncode=0):
    if route == "codex" and plan.output_file is not None:
        plan.output_file.write_text(wire, encoding="utf-8")
    return adapter.parse_response(
        stdout=wire if route != "codex" else "",
        stderr="", returncode=returncode, output_file=plan.output_file, plan=plan,
    )


def consume(profile: str, response):
    if profile == "dimension":
        return linear.parse_review_response(response, "pedagogical")
    return direct.parse_direct_review_response(response)


@pytest.mark.parametrize("profile", ("dimension", "direct"))
@pytest.mark.parametrize("route", ROUTES)
def test_matrix_schema_passed_and_consumed(profile, route, tmp_path, monkeypatch, caplog):
    payload = mechanical_payload(profile)
    seen = []

    def runtime(agent, prompt, **kwargs):
        assert agent == route
        config = kwargs["tool_config"] or {}
        seen.append(config)
        adapter = adapter_for(route, monkeypatch)
        # Protocol coverage uses the adapter's admitted default model. The
        # unchanged production Grok pin is separately tested as a refusal.
        plan = build_plan(adapter, tmp_path, config)
        if route in SUPPORTED:
            schema = load_output_schema(config)
            assert schema == qg_schema.reviewer_output_schema(profile)
            path = Path(config["output_schema_path"])
            assert hashlib.sha256(path.read_bytes()).hexdigest() == config["output_schema_sha256"]
            flag = "--output-schema" if route == "codex" else "--json-schema"
            value = plan.cmd[plan.cmd.index(flag) + 1]
            assert (json.loads(Path(value).read_text()) if route == "codex" else json.loads(value)) == schema
            return parse_terminal(adapter, plan, route, terminal_output(route, payload))
        assert "--json-schema" not in plan.cmd and "--output-schema" not in plan.cmd
        assert not any(key.startswith("output_schema") for key in config)
        return SimpleNamespace(ok=True, response=f"```json\n{json.dumps(payload)}\n```")

    if route in {"gemini", "acpx_agy"}:
        with pytest.raises(ValueError, match="unknown or route not selectable"):
            llm_reviewer.invoke_reviewer_with_schema(route, "fixture", profile=profile, cwd=tmp_path, invoker=runtime)
        assert not seen
        return
    response, _ = llm_reviewer.invoke_reviewer_with_schema(
        route, "fixture", profile=profile, cwd=tmp_path, invoker=runtime,
    )
    result = consume(profile, response)
    if profile == "dimension":
        assert result["score"] == 7.0 and result["verdict"] == "REVISE"
        assert result["findings"][0]["issue_id"] == "MECHANICAL_FIXTURE"
        assert result["flags"] == payload["flags"]
        assert result["evidence_quotes"] == payload["evidence_quotes"]
    else:
        assert result == payload
    assert isinstance(response, dict) == (route in SUPPORTED)
    assert ("compatibility fallback" in caplog.text) == (route not in SUPPORTED)
    if route in SUPPORTED:
        assert not Path(seen[0]["output_schema_path"]).exists()


@pytest.mark.parametrize("profile", ("dimension", "direct", "audit"))
@pytest.mark.parametrize("route", SUPPORTED)
@pytest.mark.parametrize("damage", ("invalid", "truncated", "missing", "wrapped", "execution", "missing_list"))
def test_supported_results_fail_without_downgrade(profile, route, damage, tmp_path, monkeypatch, caplog):
    calls = []
    payload = mechanical_payload(profile)

    def runtime(agent, prompt, **kwargs):
        calls.append(agent)
        adapter = adapter_for(route, monkeypatch)
        plan = build_plan(adapter, tmp_path, kwargs["tool_config"])
        damaged = copy.deepcopy(payload)
        if damage == "invalid":
            damaged = {"verdict": "PASS", "findings": []}
        elif damage == "missing_list":
            del damaged["issues" if profile == "direct" else "findings"]
        wire = terminal_output(route, damaged)
        if damage == "truncated":
            wire = wire[:-4]
        elif damage == "missing":
            wire = ""
        elif damage == "wrapped":
            wire = f"```json\n{wire}\n```"
        return parse_terminal(adapter, plan, route, wire, returncode=1 if damage == "execution" else 0)

    with pytest.raises(ValueError, match="reviewer execution failed"):
        llm_reviewer.invoke_reviewer_with_schema(route, "fixture", profile=profile, cwd=tmp_path, invoker=runtime)
    assert calls == [route]
    assert "compatibility fallback" not in caplog.text


@pytest.mark.parametrize("profile", ("dimension", "direct"))
@pytest.mark.parametrize("route", SUPPORTED)
def test_schema_rejection_does_not_retry(profile, route, tmp_path, caplog):
    calls = []

    def reject(*args, **kwargs):
        calls.append(kwargs["tool_config"])
        raise RuntimeError("provider rejected schema")

    with pytest.raises(RuntimeError, match="provider rejected schema"):
        llm_reviewer.invoke_reviewer_with_schema(route, "fixture", profile=profile, cwd=tmp_path, invoker=reject)
    assert len(calls) == 1 and "output_schema_path" in calls[0]
    assert "compatibility fallback" not in caplog.text


@pytest.mark.parametrize("profile", ("dimension", "direct"))
@pytest.mark.parametrize("route", SUPPORTED)
@pytest.mark.parametrize("response", ("{}", '{"findings":', "", '```json\n{"findings": []}\n```'))
def test_consumers_revalidate_even_if_runtime_claims_success(profile, route, response, tmp_path, caplog):
    with pytest.raises(ValueError, match=r"structured output|no result"):
        llm_reviewer.invoke_reviewer_with_schema(
            route, "fixture", profile=profile, cwd=tmp_path,
            invoker=lambda *a, **kw: SimpleNamespace(ok=True, response=response),
        )
    assert "compatibility fallback" not in caplog.text


@pytest.mark.parametrize("route", ("cursor", "deepseek", "glm"))
def test_unsupported_route_cannot_discard_a_requested_schema(route, tmp_path):
    with pytest.raises(ValueError, match="cannot enforce a requested output schema"):
        llm_reviewer.invoke_reviewer_with_schema(
            route, "fixture", profile="dimension", cwd=tmp_path,
            tool_config=qg_schema.write_reviewer_output_schema(tmp_path, "dimension"),
            invoker=lambda *a, **kw: pytest.fail("unsupported requested schema reached runtime"),
        )


@pytest.mark.parametrize("route", SUPPORTED)
def test_schema_hash_drift_refused_before_spawn(route, tmp_path, monkeypatch):
    config = qg_schema.write_reviewer_output_schema(tmp_path, "dimension")
    Path(config["output_schema_path"]).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 changed"):
        build_plan(adapter_for(route, monkeypatch), tmp_path, config)


@pytest.mark.parametrize("route", ("agy", "grok"))
@pytest.mark.parametrize("profile", ("dimension", "direct"))
@pytest.mark.parametrize("damage", ("no_structured", "error", "unfinished", "raw_payload"))
def test_native_envelope_requires_structured_terminal(route, profile, damage, tmp_path, monkeypatch):
    adapter = adapter_for(route, monkeypatch)
    plan = build_plan(adapter, tmp_path, qg_schema.write_reviewer_output_schema(tmp_path, profile))
    payload = mechanical_payload(profile)
    envelope = json.loads(terminal_output(route, payload))
    # A valid-looking free-text answer must not rescue a broken envelope.
    envelope["response" if route == "agy" else "text"] = json.dumps(payload)
    if damage == "no_structured":
        del envelope["structured_output" if route == "agy" else "structuredOutput"]
    elif damage == "error":
        envelope["error" if route == "agy" else "structuredOutputError"] = "schema rejected"
    elif damage == "unfinished":
        envelope["status" if route == "agy" else "stopReason"] = "WAITING" if route == "agy" else "max_tokens"
    else:
        envelope = payload
    result = parse_terminal(adapter, plan, route, json.dumps(envelope))
    assert result.ok is False and result.response == ""


def test_codex_dimension_and_direct_missing_file_never_recovers_prose(tmp_path, monkeypatch):
    adapter = adapter_for("codex", monkeypatch)

    def forbidden(*args, **kwargs):
        pytest.fail("schema invocation attempted unconstrained rollout recovery")

    monkeypatch.setattr(adapter, "_read_latest_rollout_task_complete", forbidden)
    for profile in ("dimension", "direct"):
        plan = build_plan(adapter, tmp_path, qg_schema.write_reviewer_output_schema(tmp_path, profile))
        assert adapter.check_early_reap(plan) is False
        result = adapter.parse_response(
            stdout=json.dumps(mechanical_payload(profile)), stderr="", returncode=0,
            output_file=None, plan=plan,
        )
        assert result.ok is False and result.response == ""


@pytest.mark.parametrize("wire", ('{"x":NaN}', '{"x":Infinity}', '{"x":1,"x":2}'))
def test_non_json_or_ambiguous_objects_rejected(wire):
    from scripts.agent_runtime.adapters._output_schema import INVALID_JSON, json_value

    assert json_value(wire) is INVALID_JSON


@pytest.mark.parametrize("route", SUPPORTED)
def test_nullable_schema_distinguishes_null_from_missing(route, tmp_path, monkeypatch):
    schema_path = tmp_path / "nullable.json"
    schema_path.write_text(json.dumps({"type": ["object", "null"]}))
    config = {"output_schema_path": str(schema_path),
              "output_schema_sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest()}
    adapter = adapter_for(route, monkeypatch)
    plan = build_plan(adapter, tmp_path, config)
    valid = parse_terminal(adapter, plan, route, terminal_output(route, None))
    assert valid.ok and valid.response == "null"
    if route == "codex":
        missing = ""
    else:
        envelope = json.loads(terminal_output(route, None))
        del envelope["structuredOutput" if route == "grok" else "structured_output"]
        missing = json.dumps(envelope)
    invalid = parse_terminal(adapter, plan, route, missing)
    assert not invalid.ok and invalid.response == ""


@pytest.mark.parametrize("damage", ("no_structured", "error", "not_terminal", "trailing_partial", "duplicate_terminal"))
def test_claude_dimension_and_direct_terminal_required(damage, tmp_path, monkeypatch):
    adapter = adapter_for("claude", monkeypatch)
    for profile in ("dimension", "direct"):
        plan = build_plan(adapter, tmp_path, qg_schema.write_reviewer_output_schema(tmp_path, profile))
        event = json.loads(terminal_output("claude", mechanical_payload(profile)))
        if damage == "no_structured":
            del event["structured_output"]
        elif damage == "error":
            event["is_error"] = True
        elif damage == "not_terminal":
            event["type"] = "assistant"
        wire = json.dumps(event)
        if damage == "trailing_partial":
            wire += '\n{"type":'
        elif damage == "duplicate_terminal":
            wire += "\n" + wire
        result = parse_terminal(adapter, plan, "claude", wire)
        assert result.ok is False and result.response == ""


@pytest.mark.parametrize("profile", ("dimension", "direct", "audit"))
def test_prompt_and_schema_single_source_agree(profile):
    contract = qg_schema.render_reviewer_output_contract(profile)
    encoded = contract.split("```json\n", 1)[1].split("\n```", 1)[0]
    assert json.loads(encoded) == qg_schema.reviewer_output_schema(profile)
    Draft202012Validator.check_schema(json.loads(encoded))
    if profile == "audit":
        assert contract in llm_reviewer.build_reviewer_prompt("a1", "fixture", "public fixture")
    elif profile == "dimension":
        for name in ("linear-review-dim.md", "linear-review-dim.generated.md"):
            template = ROOT / "scripts/build/phases" / name
            text = template.read_text()
            assert text.count("{REVIEWER_OUTPUT_SCHEMA}") == 1
            context = {token: "fixture" for token in linear.DOWNSTREAM_TOKENS if f"{{{token}}}" in text}
            context["REVIEWER_OUTPUT_SCHEMA"] = contract
            rendered = linear.render_phase_prompt(template, context)
            assert contract in rendered and "{REVIEWER_OUTPUT_SCHEMA}" not in rendered
    else:
        text = (direct.PHASES_DIR / "claude/direct-review.md").read_text()
        assert text.count("{{REVIEWER_OUTPUT_SCHEMA}}") == 1


@pytest.mark.parametrize("route", ("claude", "codex", "agy"))
def test_dimension_production_wrapper_passes_schema_and_consumes_object(route, tmp_path, monkeypatch):
    monkeypatch.setattr(linear, "_runtime_tool_config", lambda *a, **kw: {})
    calls = []

    def runtime(agent, prompt, **kwargs):
        calls.append(agent)
        assert agent == route
        assert kwargs["model"] == linear.REVIEWER_DEFAULTS[f"{route}-tools"]["model"]
        adapter = adapter_for(route, monkeypatch)
        plan = build_plan(adapter, tmp_path, kwargs["tool_config"], model=kwargs["model"])
        return parse_terminal(adapter, plan, route, terminal_output(route, mechanical_payload("dimension")))

    result = linear.invoke_reviewer_dim_ensemble(
        "fixture", f"{route}-tools", dim="pedagogical", writer_under_review="fixture",
        reviewer_samples=1, cwd=tmp_path, invoker=runtime,
    )
    assert calls == [route]
    assert result["findings"][0]["quote"] == "mechanical fixture quote"
    assert result["score"] == 7.0


def test_dimension_grok_frozen_model_remains_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(linear, "_runtime_tool_config", lambda *a, **kw: {})

    def runtime(agent, prompt, **kwargs):
        assert kwargs["model"] == "grok-4.5"
        return build_plan(adapter_for(agent, monkeypatch), tmp_path, kwargs["tool_config"], model=kwargs["model"])

    with pytest.raises(linear.LinearPipelineError, match="unsupported Grok model"):
        linear.invoke_reviewer_dim("fixture", "grok-tools", dim="pedagogical", writer_under_review="fixture",
                                   cwd=tmp_path, invoker=runtime)


def direct_context(tmp_path: Path) -> direct.DirectModuleContext:
    path = tmp_path / "module.yaml"
    path.write_text("type: vocabulary\ntitle: Public mechanical fixture\n", encoding="utf-8")
    return direct.DirectModuleContext(
        slug="fixture", level="a1", yaml_path=path, status_path=tmp_path / "status.json",
        orch_dir=tmp_path / "artifacts", module_data={"type": "vocabulary"}, do_review=True,
    )


@pytest.mark.parametrize("damage", ("none", "defect", "missing", "invalid", "truncated", "failed", "contradiction"))
def test_direct_claude_production_phase_consumes_result(damage, tmp_path, monkeypatch):
    from scripts.agent_runtime import runner

    monkeypatch.setattr(direct, "PROJECT_ROOT", tmp_path)
    ctx = direct_context(tmp_path)
    payload = mechanical_payload("direct")
    if damage == "none":
        payload["verdict"] = "PASS"
        payload["dimensions"]["activities"]["status"] = "PASS"
        payload["issues"] = []
    elif damage == "contradiction":
        payload["verdict"] = "PASS"

    def runtime(agent, prompt, **kwargs):
        assert agent == "claude" and kwargs["model"] == "claude-opus-4-8"
        assert qg_schema.render_reviewer_output_contract("direct") in prompt
        adapter = adapter_for(agent, monkeypatch)
        plan = build_plan(adapter, tmp_path, kwargs["tool_config"])
        wire = terminal_output(agent, payload if damage != "invalid" else {"verdict": "PASS"})
        if damage == "missing":
            wire = ""
        elif damage == "truncated":
            wire = wire[:-4]
        return parse_terminal(adapter, plan, agent, wire, returncode=1 if damage == "failed" else 0)

    monkeypatch.setattr(runner, "invoke", runtime)
    assert direct.phase_review(ctx) is (damage == "none")
    phase = ctx.status_data["phases"]["review"]
    assert (phase["status"] == "complete") is (damage == "none")
    if damage == "none":
        assert phase["dimensions"] == payload["dimensions"] and phase["issues"] == []
    if damage == "defect":
        assert phase["dimensions"] == payload["dimensions"] and phase["issues"] == payload["issues"]


def test_audit_claude_schema_and_embedded_fence_survive_consumption(tmp_path, monkeypatch):
    from scripts.agent_runtime import runner
    from scripts.audit import llm_reviewer_dispatch as dispatch

    payload = mechanical_payload("audit")
    monkeypatch.setattr(dispatch, "PROJECT_ROOT", tmp_path)

    def runtime(agent, prompt, **kwargs):
        assert load_output_schema(kwargs["tool_config"]) == qg_schema.reviewer_output_schema("audit")
        adapter = adapter_for(agent, monkeypatch)
        plan = build_plan(adapter, tmp_path, kwargs["tool_config"])
        parsed = parse_terminal(adapter, plan, agent, terminal_output(agent, payload))
        return SimpleNamespace(ok=parsed.ok, response=parsed.response, usage_record={}, stderr_excerpt=None)

    monkeypatch.setattr(runner, "invoke", runtime)
    route = dispatch.route_for_review(policy_family="core", escalation=True)
    result = dispatch._invoke_agent_runtime("claude", route, "fixture", "qg-schema-audit")
    findings = llm_reviewer.parse_and_evaluate_llm_response(result.response_text, "fixture ```json text")
    assert len(findings) == 1 and findings[0]["issue_id"] == "MECHANICAL_FIXTURE"
    assert findings[0]["excerpt"] == payload["findings"][0]["excerpt"]


@pytest.mark.skipif(os.environ.get("QG_SCHEMA_DIRECT_LIVE") != "1", reason="explicit provider-run opt-in required")
def test_direct_live(tmp_path, monkeypatch):
    """Public frozen D input, redirected to temp; semantic held-out still separate."""
    source = ROOT / "curriculum/l2-uk-direct/a1/dozvillia.yaml"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == "5560effd4abd5476347b936bf15057b92f52f31adc85a544d176f92e69a80d27"
    ctx = direct_context(tmp_path)
    ctx.yaml_path.write_bytes(source.read_bytes())
    ctx.module_data = direct.load_module_yaml(ctx.yaml_path)
    monkeypatch.setattr(direct, "PROJECT_ROOT", tmp_path)
    passed = direct.phase_review(ctx)
    raw = ctx.orch_dir / "review-output-raw.json"
    assert raw.exists(), "required live result missing; residual owner claude/prompt-audit-2026-09-07"
    report = direct.parse_direct_review_response(json.loads(raw.read_text()))
    assert passed == (report["verdict"] == "PASS")
    assert ctx.status_data["phases"]["review"]["dimensions"] == report["dimensions"]
    print(f"direct live: dimensions={len(report['dimensions'])} issues={len(report['issues'])} verdict={report['verdict']}; PASS")
