"""Offline admission and provider identity checks for #10420."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts import delegate
from scripts.agent_runtime.adapters import agy
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.review.model_catalog import load_model_catalog
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, evaluate_candidate
from tests.agent_runtime.agy_hook_helpers import register_agy_hooks

SLUGS = ("claude-sonnet-5-5-high", "claude-opus-5-5-high")
LABELS = ("Claude Sonnet 5.5 (High)", "Claude Opus 5.5 (High)")
BACKEND_IDS = ("claude-sonnet-5-5-high", "claude-opus-5-5-high")


@pytest.fixture(autouse=True)
def no_provider_process(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("provider subprocess must not run")

    monkeypatch.setattr(agy.subprocess, "run", forbidden)
    monkeypatch.setattr(agy.subprocess, "Popen", forbidden)


def build(tmp_path, model, mode="read-only", config=None):
    return agy.AgyAdapter().build_invocation(
        prompt="Review supplied evidence.",
        mode=mode,
        cwd=tmp_path,
        model=model,
        task_id="claude-route",
        session_id=None,
        tool_config=config,
        effort="high",
    )


@pytest.mark.parametrize("slug,label", zip(SLUGS, LABELS, strict=True))
def test_exact_slug_and_display_label_resolve(slug, label):
    adapter = agy.AgyAdapter()
    assert adapter._resolve_model_flag(slug) == slug
    assert adapter._resolve_model_flag(label) == slug


@pytest.mark.parametrize("slug,label,backend", zip(SLUGS, LABELS, BACKEND_IDS, strict=True))
def test_reported_forms_use_agy_slug_map(slug, label, backend):
    assert [agy.AgyAdapter.resolve_model_slug(value) for value in (slug, label, backend)] == [slug] * 3


@pytest.mark.parametrize(
    "model",
    [
        "claude-sonnet-5-5",
        "claude-opus-5-5",
        "claude-sonnet-5-5-low",
        "claude-opus-5-5-low",
        "claude-sonnet-5-5-medium",
        "claude-opus-5-5-medium",
        "Claude Sonnet 5.5 (Medium)",
        "Claude Opus 5.5 (Low)",
        "claude-unknown-5-5-high",
    ],
)
def test_other_claude_names_stay_unsupported(model):
    with pytest.raises(ValueError, match="Unsupported AGY model"):
        agy.AgyAdapter()._resolve_model_flag(model)


@pytest.mark.parametrize("model", ["Claude Sonnet 4.6 (Thinking)", "Claude Opus 4.6 (Thinking)"])
def test_retired_thinking_labels_keep_retirement_error(model):
    with pytest.raises(ValueError, match="retired"):
        agy.AgyAdapter()._resolve_model_flag(model)


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
@pytest.mark.parametrize("model", [*SLUGS, *LABELS])
@pytest.mark.parametrize("config", [None, {}, {"bridge_repo_read": True}])
def test_non_review_rejects_before_permission_writes_and_probes(tmp_path, monkeypatch, mode, model, config):
    def forbidden(*args, **kwargs):
        pytest.fail("refusal must precede permission writes and version probes")

    monkeypatch.setattr(agy, "_write_review_permissions", forbidden)
    monkeypatch.setattr(agy, "_require_background_wait_support", forbidden)
    with pytest.raises(ValueError) as error:
        build(tmp_path, model, mode, config)
    assert str(error.value).startswith("agy_claude_requires_review_route")
    assert model in str(error.value)
    assert "rejected" in str(error.value)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("model", SLUGS)
def test_real_delegate_probe_refuses_without_default_substitution(model):
    refusal = delegate._adapter_model_rejection("agy", model)
    assert refusal.startswith("agy_claude_requires_review_route")
    assert model in refusal
    with pytest.raises(delegate.BudgetGuardRefuseError) as error:
        delegate._resolve_substitution_model("agy", model)
    assert model in str(error.value)
    assert "agy_claude_requires_review_route" in str(error.value)
    assert "gemini-3.8-flash-high" not in str(error.value)


@pytest.mark.parametrize("model", [*SLUGS, *LABELS])
def test_review_route_denies_commands_and_writes_without_effort(tmp_path, monkeypatch, model):
    home = tmp_path / "home"
    (home / ".gemini" / "antigravity-cli").mkdir(parents=True)
    register_agy_hooks(tmp_path, home=home)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *args: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *args: tmp_path / "agy.log")
    plan = build(tmp_path, model, config={"review_profile": "code", "agy_home_override": str(home)})
    assert "--sandbox" in plan.cmd
    assert "--dangerously-skip-permissions" not in plan.cmd
    assert "--effort" not in plan.cmd
    assert plan.cmd[plan.cmd.index("--model") + 1] == agy.AgyAdapter.resolve_model_slug(model)
    permissions = json.loads((home / ".gemini" / "antigravity-cli" / "settings.json").read_text())["permissions"]
    assert "command(*)" in permissions["deny"]
    assert "write_file(*)" in permissions["deny"]


def test_catalog_adds_only_agy_identity_transport():
    catalog = load_model_catalog()
    for slug in SLUGS:
        model_id = slug.removesuffix("-high")
        spec = catalog["models"][model_id]
        assert spec["family"] == "anthropic"
        assert spec["transports"] == (
            ["native_claude", "agy"] if model_id == "claude-opus-5-5" else ["native_claude", "cursor", "agy"]
        )
        expected = {"native_claude": model_id, "agy": slug}
        if model_id == "claude-opus-5-5":
            assert spec["roles"] == [
                "orchestration",
                "architecture",
                "agentic_coding",
                "critical_review",
                "security_review",
                "ukrainian_review",
            ]
        else:
            assert spec["roles"] == [
                "implementation",
                "agentic_coding",
                "strong_review",
                "document_authoring",
                "routine_mechanical",
            ]
        assert spec["routing_wire_ids"] == expected
        assert "quota_bucket" not in spec
        for field in ("review_ladders", "formal_cf_defaults"):
            assert slug not in json.dumps(catalog[field])
        assert slug not in json.dumps(catalog["budget_substitution_models"].get("agy", {}))
        assert slug not in catalog["review_candidates"]
        assert all(
            not (row["model_id"] == model_id and row["route"] == "agy") for row in catalog["review_candidates"].values()
        )
        for seat in catalog["seats"].values():
            if seat["model_id"] == model_id:
                assert all(row["transport"] != "agy" for row in seat["routes"].values())
    from scripts.common.fallback_substitutions import load_dispatch_fallbacks

    assert all(slug not in json.dumps(load_dispatch_fallbacks(delegate._FALLBACK_SUBS_PATH)) for slug in SLUGS)


@pytest.mark.parametrize("author", ["claude-opus-5-5", "claude-sonnet-5-5"])
def test_anthropic_agy_fixture_candidate_cannot_review_anthropic_author(author):
    candidate = replace(
        REVIEW_CANDIDATES["claude-opus-5-5"],
        name="fixture-anthropic-agy",
        concrete_model="claude-opus-5-5-high",
        route="agy",
        transport="agy",
        family="anthropic",
    )
    result = evaluate_candidate(candidate, ResolverInputs(author_model=author, risk="low"))
    assert result.status == "excluded"
    assert "same family as author" in result.reason


@pytest.mark.parametrize("shape", ["nested", "top-level"])
@pytest.mark.parametrize("slug", SLUGS)
@pytest.mark.parametrize("observed", ["matching", "mismatching", "absent", "no-init", "tool-only"])
def test_provider_init_identity_on_existing_parse_result(tmp_path, monkeypatch, slug, observed, shape):
    plan = InvocationPlan(
        cmd=["agy", "--output-format", "stream-json", "--model", slug],
        cwd=tmp_path,
        stdin_payload="",
        output_file=None,
        env_overrides={},
        env_unsets=(),
        liveness_paths=(),
        metadata={"entire_fleet": {"requested_model": slug, "actual_model": slug}},
    )
    monkeypatch.setattr(agy, "_bound_conversation", lambda *args: ("fixture", tmp_path))
    monkeypatch.setattr(agy, "_invocation_transcript", lambda *args: None)
    monkeypatch.setattr(agy, "_completion_gap", lambda *args: (None, None))
    events = []
    if observed not in {"no-init", "tool-only"}:
        init = {"event": "init"}
        if observed != "absent":
            value = slug if observed == "matching" else "gemini-3.8-flash-high"
            init.update({"init": {"model": value}} if shape == "nested" else {"model": value})
        events.append(init)
    events.extend(
        [
            {
                "event": "step_update",
                "model": "wrong-tool-model",
                "step_update": {"type": "PLANNER_RESPONSE", "model": "wrong-tool-model"},
            },
            {
                "event": "result",
                "result": {
                    "status": "SUCCESS",
                    "conversation_id": "fixture",
                    "response": "READY",
                    "model": "wrong-terminal-model",
                },
            },
        ]
    )
    result = agy.AgyAdapter().parse_response(
        stdout="\n".join(json.dumps(event) for event in events),
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )
    assert result.ok is (observed != "mismatching")
    assert result.response == ("" if observed == "mismatching" else "READY")
    identity = result.model_identity
    if observed != "mismatching":
        assert result.substitution is None
    if observed not in {"matching", "mismatching"}:
        assert identity is None
        return
    assert identity is not None
    assert identity["actual_model"] == (
        slug if observed == "matching" else "gemini-3.8-flash-high" if observed == "mismatching" else None
    )
    assert identity["actual_model_known"] is (observed in {"matching", "mismatching"})
    assert identity["substituted"] is (observed == "mismatching")
    if observed == "mismatching":
        assert result.stderr_excerpt == "agy_model_event_mismatch"
        assert result.failure_code == "provider_policy_refusal"


@pytest.mark.parametrize(
    "reported_model",
    [
        None,
        "",
        "gemini-3.8-flash-high",
        "Gemini 3.8 Flash (High)",
        "gemini-3-flash-preview",
        "gemini-3.1-pro-high",
        "gemini-3.7-flash-high",
    ],
)
@pytest.mark.parametrize(
    "requested_model", ["gemini-3.8-flash-high", "Gemini 3.8 Flash (High)", "gemini-3-flash-preview"]
)
def test_gemini_init_is_ignored(tmp_path: Path, reported_model: str | None, requested_model: str) -> None:
    conversation_id = "7cd3ba85-817f-4a03-8223-1ff39ca42419"
    app_data = tmp_path / "agy-data"
    transcript = app_data / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
    transcript.parent.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "agy" / "verify_words_transcript.jsonl"
    transcript.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    log_file = tmp_path / "agy.log"
    log_file.write_text(f"Print mode: conversation={conversation_id}, sending message\n", encoding="utf-8")
    plan = InvocationPlan(
        cmd=["agy", "--output-format", "stream-json", "--model", requested_model],
        cwd=tmp_path,
        stdin_payload="",
        output_file=None,
        env_overrides={"AGY_RUNTIME_LOG_FILE": str(log_file), "AGY_APP_DATA_DIR": str(app_data)},
        env_unsets=(),
        liveness_paths=(log_file,),
        metadata={"entire_fleet": {"requested_model": requested_model}},
    )
    init = {"event": "init"}
    if reported_model is not None:
        init["model"] = reported_model
    stdout = "\n".join(
        [
            json.dumps(init),
            json.dumps(
                {
                    "event": "result",
                    "result": {
                        "status": "SUCCESS",
                        "conversation_id": conversation_id,
                        "response": "READY",
                    },
                }
            ),
        ]
    )

    result = agy.AgyAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan)

    no_init = stdout.split("\n", 1)[1]
    baseline = agy.AgyAdapter().parse_response(stdout=no_init, stderr="", returncode=0, output_file=None, plan=plan)
    assert result == baseline
    assert result.ok is True
    assert result.response == "READY"
    assert result.substitution is None
    assert result.model_identity is None


def _identity_stream_plan(tmp_path, slug):
    conversation_id = "7cd3ba85-817f-4a03-8223-1ff39ca42419"
    app_data = tmp_path / "agy-data"
    transcript = app_data / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
    transcript.parent.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "agy" / "verify_words_transcript.jsonl"
    transcript.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    log_file = tmp_path / "agy.log"
    log_file.write_text(f"Print mode: conversation={conversation_id}, sending message\n", encoding="utf-8")
    plan = InvocationPlan(
        cmd=["agy", "--output-format", "stream-json", "--model", slug],
        cwd=tmp_path,
        env_overrides={"AGY_RUNTIME_LOG_FILE": str(log_file), "AGY_APP_DATA_DIR": str(app_data)},
        metadata={"entire_fleet": {"requested_model": slug}},
    )
    terminal = {
        "event": "result",
        "result": {
            "status": "SUCCESS",
            "conversation_id": conversation_id,
            "response": "READY",
        },
    }
    return plan, terminal


@pytest.mark.parametrize("shape", ["nested", "top-level"])
@pytest.mark.parametrize("slug,label,backend", zip(SLUGS, LABELS, BACKEND_IDS, strict=True))
@pytest.mark.parametrize(
    "form",
    ["absent", "empty", "pin", "display", "backend", "different", "whitespace", "non-string", "retired", "unknown"],
)
def test_claude_reported_identity_fails_closed(tmp_path, slug, label, backend, form, shape):
    plan, terminal = _identity_stream_plan(tmp_path, slug)
    value = {
        "absent": None,
        "empty": "",
        "pin": slug,
        "display": label,
        "backend": backend,
        "different": "gemini-3.8-flash-high",
        "whitespace": "   ",
        "non-string": 7,
        "retired": "Claude Opus 4.6 (Thinking)",
        "unknown": "unrecognized",
    }[form]
    init = {"event": "init"}
    if form != "absent":
        init.update({"init": {"model": value}} if shape == "nested" else {"model": value})
    parsed = agy.AgyAdapter().parse_response(
        stdout="\n".join(map(json.dumps, [init, terminal])),
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )
    mismatch = form in {"different", "whitespace", "non-string", "retired", "unknown"}
    assert parsed.ok is not mismatch
    assert parsed.response == ("" if mismatch else "READY")
    if form in {"absent", "empty"}:
        assert parsed.model_identity is None
    else:
        assert parsed.model_identity == {
            "actual_model": value if isinstance(value, str) else None,
            "actual_model_known": isinstance(value, str),
            "source": "provider-init",
            "substituted": mismatch,
        }
    if mismatch:
        assert parsed.failure_code == "provider_policy_refusal"
        assert parsed.stderr_excerpt == "agy_model_event_mismatch"
    else:
        assert parsed.substitution is None


@pytest.mark.parametrize("slug", SLUGS)
@pytest.mark.parametrize("nested_matches", [True, False])
def test_conflicting_init_model_values_fail_closed(tmp_path, slug, nested_matches):
    plan, terminal = _identity_stream_plan(tmp_path, slug)
    different = "gemini-3.8-flash-high"
    init = {
        "event": "init",
        "init": {"model": slug if nested_matches else different},
        "model": different if nested_matches else slug,
    }
    parsed = agy.AgyAdapter().parse_response(
        stdout="\n".join(map(json.dumps, [init, terminal])),
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )
    assert parsed.ok is False
    assert parsed.failure_code == "provider_policy_refusal"
    assert parsed.stderr_excerpt == "agy_model_event_mismatch"
    assert parsed.model_identity["actual_model"] == different
    assert parsed.model_identity["substituted"] is True
