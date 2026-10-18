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
from tests.claude_route_accounts import HOST_ACCOUNT

SLUGS = ("claude-sonnet-5-5-high", "claude-opus-5-5-high")
LABELS = ("Claude Sonnet 5.5 (High)", "Claude Opus 5.5 (High)")
BACKEND_IDS = ("claude-sonnet-5-5-high", "claude-opus-5-5-high")


@pytest.fixture(autouse=True)
def no_provider_process(monkeypatch):
    popen = agy.subprocess.Popen

    def local_git_only(cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and cmd[0] == "git":
            return popen(cmd, *args, **kwargs)
        pytest.fail("provider subprocess must not run")

    monkeypatch.setattr(agy.subprocess, "Popen", local_git_only)


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
def test_worker_route_keeps_high_pin_and_existing_permissions(tmp_path, monkeypatch, mode, model):
    monkeypatch.setattr(agy, "require_hook_config", lambda *args, **kwargs: None)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *args: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *args: tmp_path / "agy.log")
    monkeypatch.setattr(agy, "_write_review_permissions", lambda *a, **k: pytest.fail("worker wrote review grants"))
    plan = build(tmp_path, model, mode)
    assert plan.cmd[plan.cmd.index("--model") + 1] == agy.AgyAdapter.resolve_model_slug(model)
    assert "--dangerously-skip-permissions" in plan.cmd
    assert "--sandbox" not in plan.cmd
    assert "--effort" not in plan.cmd


@pytest.mark.parametrize("model", SLUGS)
def test_real_delegate_probe_keeps_explicit_high_pin(tmp_path, monkeypatch, model):
    monkeypatch.setattr(agy, "require_hook_config", lambda *a, **k: None)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *args: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *args: tmp_path / "agy.log")
    assert delegate._adapter_model_rejection("agy", model) is None
    with pytest.raises(delegate.BudgetGuardRefuseError, match="pinned AGY Claude identity"):
        delegate._resolve_substitution_model("agy", model)


@pytest.mark.parametrize("owned", [["scripts/delegate.py"], ["scripts/agent_runtime/"], ["scripts/"]])
def test_sonnet_worker_security_floor_precedes_hooks_and_cli(tmp_path, monkeypatch, owned):
    monkeypatch.setattr(agy, "require_hook_config", lambda *a, **k: pytest.fail("hooks ran before security refusal"))
    with pytest.raises(ValueError, match="agy_sonnet_security_refused"):
        build(tmp_path, SLUGS[0], "danger", {"owned_paths": owned})


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
    result = evaluate_candidate(candidate, ResolverInputs(author_model=author, risk="low", claude_account=HOST_ACCOUNT))
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
    assert result.ok is (observed == "matching")
    assert result.response == ("READY" if observed == "matching" else "")
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
    assert parsed.ok is (not mismatch and form not in {"absent", "empty"})
    assert parsed.response == ("" if mismatch or form in {"absent", "empty"} else "READY")
    if form in {"absent", "empty"}:
        assert parsed.model_identity is None
    else:
        assert parsed.model_identity == {
            "actual_model": value if form in {"pin", "display", "backend", "different"} else None,
            "actual_model_known": form in {"pin", "display", "backend", "different"},
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
    assert parsed.model_identity is None
    assert parsed.substitution is None


def mock_agy_provider(monkeypatch, tmp_path, runner, *, stdout, exit_kind="complete", version="1.4.0"):
    """Mock only the process boundary, keeping adapter planning/parsing and runner custody."""
    from types import SimpleNamespace

    monkeypatch.setattr(agy, "require_hook_config", lambda *a, **k: None)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    plan, _ = _identity_stream_plan(tmp_path, SLUGS[1])
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(tmp_path / "agy-data"))
    monkeypatch.setattr(agy, "_agy_app_data", lambda overrides: tmp_path / "agy-data")
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: tmp_path / "agy.log")
    binary = tmp_path / "agy-cli-fixture"
    binary.write_bytes(b"synthetic CLI artifact, never executed\n")
    original_which = agy.shutil.which
    monkeypatch.setattr(agy.shutil, "which", lambda name: str(binary) if name == "agy" else original_which(name))
    monkeypatch.setattr(runner, "has_headroom", lambda *a: (True, "fixture"))
    monkeypatch.setattr(runner, "load_failover_chain", lambda *a, **k: None)
    monkeypatch.setattr(runner, "write_record", lambda *a: None)
    monkeypatch.setattr(runner, "resolve_invocation_telemetry", lambda **k: SimpleNamespace(
        model=k["requested_model"], effort="high", cli_version=version,
    ))
    monkeypatch.setattr(runner.FleetCapture, "start", lambda **k: None)
    monkeypatch.setattr(runner.PrimaryTreeWatch, "start", lambda **k: None)
    monkeypatch.setattr(runner._ChildCwdPin, "start", lambda **k: None)
    monkeypatch.setattr(runner, "_prepare_spawn_command", lambda cmd, env: (cmd, env))
    launches = []

    class Process:
        pid = 999_999_991
        returncode = None

        def poll(self):
            if self.returncode is not None:
                return self.returncode
            if exit_kind == "timeout":
                return None
            if exit_kind == "cancel":
                raise KeyboardInterrupt("synthetic cancellation")
            if exit_kind == "exception":
                raise RuntimeError("synthetic runtime failure")
            self.returncode = 0
            return self.returncode

        def wait(self, **kwargs):
            return self.returncode

    proc = Process()

    def spawn(cmd, **kwargs):
        launches.append((cmd, kwargs))
        return proc, None, None

    monkeypatch.setattr(runner, "_spawn_subprocess", spawn)
    monkeypatch.setattr(runner, "_kill_process_tree", lambda proc: setattr(proc, "returncode", -15))
    monkeypatch.setattr(runner, "_agy_process_group_exited", lambda pid: True)
    state = SimpleNamespace(stdout_lines=stdout.splitlines(keepends=True), stderr_lines=[])
    monkeypatch.setattr(runner, "start_watchdog", lambda *a, **k: (state, []))
    monkeypatch.setattr(runner, "stop_watchdog", lambda *a, **k: None)
    if exit_kind == "timeout":
        monkeypatch.setattr(runner, "should_kill", lambda *a, **k: "hard_timeout")
    return launches, plan, binary


@pytest.mark.parametrize("model", ["claude-sonnet-5-5-medium", "Claude Opus 5.5 (Low)"])
def test_unknown_variant_refuses_normal_builder_before_hooks(tmp_path, monkeypatch, model):
    monkeypatch.setattr(agy, "require_hook_config", lambda *a, **k: pytest.fail("unsupported pin reached hooks"))
    with pytest.raises(ValueError, match="Unsupported AGY model"):
        build(tmp_path, model, "danger")


@pytest.mark.parametrize("source", ["requested", "configuration", {"provider-init": True}])
def test_request_or_configuration_init_cannot_qualify(tmp_path, source):
    plan, terminal = _identity_stream_plan(tmp_path, SLUGS[1])
    stdout = "\n".join(map(json.dumps, [
        {"event": "init", "init": {"model": SLUGS[1], "source": source}}, terminal,
    ]))
    result = agy.AgyAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan)
    assert result.ok is False
    assert result.model_identity is None
    assert result.stderr_excerpt == "agy_model_identity_missing"


@pytest.mark.parametrize("position", ["duplicate", "after-tool", "after-result"])
def test_init_is_one_initial_observation(tmp_path, position):
    plan, terminal = _identity_stream_plan(tmp_path, SLUGS[1])
    init = {"event": "init", "model": SLUGS[1]}
    events = {
        "duplicate": [init, init, terminal],
        "after-tool": [{"event": "step_update", "model": SLUGS[1]}, init, terminal],
        "after-result": [terminal, init],
    }[position]
    result = agy.AgyAdapter().parse_response(
        stdout="\n".join(map(json.dumps, events)), stderr="", returncode=0, output_file=None, plan=plan,
    )
    assert result.ok is False
    assert result.stderr_excerpt == "agy_model_event_mismatch"


@pytest.mark.parametrize("identifiers", [
    {"conversation_id": "one", "session_id": "two"},
    {"conversation_id": 7},
    {"conversation_id": ""},
    {"conversation_id": "stale-session"},
])
def test_provider_session_must_bind_to_this_stream(tmp_path, identifiers):
    plan, terminal = _identity_stream_plan(tmp_path, SLUGS[1])
    init = {"event": "init", "model": SLUGS[1], **identifiers}
    result = agy.AgyAdapter().parse_response(
        stdout="\n".join(map(json.dumps, [init, terminal])), stderr="", returncode=0, output_file=None, plan=plan,
    )
    assert result.ok is False
    assert result.model_identity is None or result.model_identity["substituted"] is True


@pytest.mark.parametrize("model", ["claude-opus-5-5-high", "claude-sonnet-5-5-high"])
def test_identity_survives_provider_failure_without_claiming_success(tmp_path, model):
    plan, terminal = _identity_stream_plan(tmp_path, model)
    terminal["result"].update(status="ERROR", error="synthetic provider failure")
    result = agy.AgyAdapter().parse_response(
        stdout="\n".join(map(json.dumps, [{"event": "init", "model": model}, terminal])),
        stderr="", returncode=1, output_file=None, plan=plan,
    )
    assert result.ok is False
    assert result.model_identity["actual_model"] == model
    assert result.model_identity["actual_model_known"] is True


@pytest.mark.parametrize("model", SLUGS)
def test_claude_worker_keeps_the_real_shell_output_hook_gate(tmp_path, model):
    from scripts.agent_runtime.agy_hook_config import AgyHookConfigError

    hooks = tmp_path / ".agents" / "hooks.json"
    hooks.parent.mkdir()
    hooks.write_bytes(b"{}\n")
    with pytest.raises(AgyHookConfigError, match="missing_guard"):
        build(tmp_path, model, "workspace-write", {"agy_home_override": str(tmp_path / "home")})
    assert hooks.read_bytes() == b"{}\n"


def test_sonnet_explicit_critical_worker_is_refused_without_owned_paths(tmp_path):
    with pytest.raises(ValueError, match="agy_sonnet_security_refused"):
        build(tmp_path, SLUGS[0], "workspace-write", {"risk": "critical"})


@pytest.mark.parametrize("config", [{"risk": "critical"}, {"owned_paths": ["scripts/delegate.py"]}])
def test_opus_security_worker_keeps_its_existing_catalog_role(tmp_path, monkeypatch, config):
    monkeypatch.setattr(agy, "require_hook_config", lambda *a, **k: None)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: tmp_path / "agy.log")
    plan = build(tmp_path, SLUGS[1], "workspace-write", config)
    assert plan.cmd[plan.cmd.index("--model") + 1] == SLUGS[1]
    assert "--dangerously-skip-permissions" in plan.cmd


@pytest.mark.parametrize("slug", SLUGS)
@pytest.mark.parametrize("reverse", [False, True], ids=["matching-last", "matching-first"])
@pytest.mark.parametrize("member,first,last,nested", [
    ("model", '"gemini-3.8-flash-high"', '"MODEL"', False),
    ("model", '"gemini-3.8-flash-high"', '"MODEL"', True),
    ("source", '"configuration"', '"provider-init"', False),
    ("source", '"requested"', '"runtime"', True),
    ("model_source", '"configuration"', '"runtime"', False),
    ("model_source", '"requested"', '"provider-init"', True),
    ("init", '{"model":"gemini-3.8-flash-high"}', '{"model":"MODEL"}', False),
    ("event", '"step_update"', '"init"', False),
    ("conversation_id", '"stale-session"', '"7cd3ba85-817f-4a03-8223-1ff39ca42419"', False),
    ("session_id", '"stale-session"', '"7cd3ba85-817f-4a03-8223-1ff39ca42419"', True),
    ("model", '"MODEL"', '"MODEL"', True),
    ("metadata", '{"model":"other","model":"MODEL"}', '{}', True),
    ("metadata", '[{"source":"requested","source":"runtime"}]', '[]', False),
])
@pytest.mark.parametrize("entrypoint", ["parser", "runner", "cancel", "exception"])
def test_duplicate_init_members_never_qualify(
    tmp_path, monkeypatch, slug, reverse, member, first, last, nested, entrypoint,
):
    from scripts.agent_runtime import runner

    if reverse:
        first, last = last, first
    # Escape the second spelling: duplicate detection must compare decoded names.
    escaped_key = f'"\\u{ord(member[0]):04x}{member[1:]}"'
    pairs = f'{json.dumps(member)}:{first},{escaped_key}:{last}'.replace("MODEL", slug)
    defaults = [f'"model":{json.dumps(slug)}'] if member != "model" else []
    if not nested and member != "event":
        defaults.append('"event":"init"')
    body = "{" + ",".join([*defaults, pairs]) + "}"
    init = '{"event":"init","init":' + body + "}" if nested else body
    plan, terminal = _identity_stream_plan(tmp_path, slug)
    stdout = init + "\n" + json.dumps(terminal) + "\n"
    if entrypoint == "parser":
        result = agy.AgyAdapter().parse_response(
            stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan,
        )
    else:
        provider_dir = tmp_path / "provider"
        provider_dir.mkdir()
        launches, _, _ = mock_agy_provider(
            monkeypatch, provider_dir, runner, stdout=stdout,
            exit_kind=entrypoint if entrypoint != "runner" else "complete",
        )
        kwargs = dict(mode="workspace-write", cwd=tmp_path, model=slug, task_id="duplicate-init",
                      tool_config={"run_nonce": "duplicate-run", "owned_paths": ["artifact.txt"]})
        if entrypoint in {"cancel", "exception"}:
            with pytest.raises(KeyboardInterrupt if entrypoint == "cancel" else RuntimeError) as caught:
                runner.invoke("agy", "Implement.", **kwargs)
            assert len(launches) == 1
            assert caught.value.model_identity is None
            assert runner._AGY_OBSERVED_IDENTITY.get() is None
            return
        result = runner.invoke("agy", "Implement.", **kwargs)
        assert len(launches) == 1
        assert runner._AGY_OBSERVED_IDENTITY.get() is None
    assert result.ok is False
    assert result.response == ""
    assert result.model_identity is None
    assert result.failure_code == "provider_policy_refusal"
    assert result.stderr_excerpt == "agy_model_event_mismatch"


@pytest.mark.parametrize("slug", SLUGS)
@pytest.mark.parametrize("entrypoint", ["parser", "runner", "cancel", "exception"])
def test_duplicate_later_event_revokes_matching_identity(tmp_path, monkeypatch, slug, entrypoint):
    from scripts.agent_runtime import runner

    plan, terminal = _identity_stream_plan(tmp_path, slug)
    stdout = "\n".join([
        json.dumps({"event": "init", "model": slug}),
        '{"event":"init","event":"step_update","model":"other"}',
        json.dumps(terminal),
    ])
    if entrypoint == "parser":
        result = agy.AgyAdapter().parse_response(
            stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan,
        )
        identity = result.model_identity
    else:
        provider_dir = tmp_path / "provider"
        provider_dir.mkdir()
        launches, _, _ = mock_agy_provider(
            monkeypatch, provider_dir, runner, stdout=stdout,
            exit_kind=entrypoint if entrypoint != "runner" else "complete",
        )
        kwargs = dict(mode="workspace-write", cwd=tmp_path, model=slug, task_id="late-duplicate",
                      tool_config={"run_nonce": "duplicate-run", "owned_paths": ["artifact.txt"]})
        if entrypoint in {"cancel", "exception"}:
            with pytest.raises(KeyboardInterrupt if entrypoint == "cancel" else RuntimeError) as caught:
                runner.invoke("agy", "Implement.", **kwargs)
            identity = caught.value.model_identity
        else:
            result = runner.invoke("agy", "Implement.", **kwargs)
            identity = result.model_identity
        assert len(launches) == 1
        assert runner._AGY_OBSERVED_IDENTITY.get() is None
    if entrypoint in {"parser", "runner"}:
        assert result.ok is False
        assert result.response == ""
        assert result.stderr_excerpt == "agy_model_event_mismatch"
    assert identity is None
    if entrypoint in {"parser", "runner"}:
        assert result.substitution is None


@pytest.mark.parametrize("slug", SLUGS)
@pytest.mark.parametrize("container", ["object", "array"])
@pytest.mark.parametrize("entrypoint", ["parser", "runner"])
def test_duplicate_descendants_cannot_hide_in_unique_envelopes(tmp_path, monkeypatch, slug, container, entrypoint):
    from scripts.agent_runtime import runner

    plan, terminal = _identity_stream_plan(tmp_path, slug)
    descendant = '{"model":"other","model":' + json.dumps(slug) + "}"
    metadata = '{"nested":' + descendant + "}" if container == "object" else "[" + descendant + "]"
    init = '{"event":"init","model":' + json.dumps(slug) + ',"metadata":' + metadata + "}"
    stdout = init + "\n" + json.dumps(terminal)
    if entrypoint == "parser":
        result = agy.AgyAdapter().parse_response(
            stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan,
        )
    else:
        provider_dir = tmp_path / "provider"
        provider_dir.mkdir()
        launches, _, _ = mock_agy_provider(monkeypatch, provider_dir, runner, stdout=stdout)
        result = runner.invoke("agy", "Implement.", mode="workspace-write", cwd=tmp_path, model=slug,
                               task_id="nested-duplicates", tool_config={"run_nonce": "nested-run"})
        assert len(launches) == 1
    assert result.ok is False
    assert result.response == ""
    assert result.model_identity is None
    assert result.stderr_excerpt == "agy_model_event_mismatch"


def consistency_stream(slug, case):
    """Frozen author inputs; expectations live in the consuming tests."""
    other = "claude-opus-5-5-high" if "sonnet" in slug else "claude-sonnet-5-5-high"
    init = {"event": "init", "model": slug, "session_id": "7cd3ba85-817f-4a03-8223-1ff39ca42419"}
    terminal = {"event": "result", "result": {
        "status": "SUCCESS", "response": "READY", "conversation_id": "7cd3ba85-817f-4a03-8223-1ff39ca42419",
    }}
    events = [init]
    if case == "display":
        init["model"] = "Claude Sonnet 5.5 (High)" if "sonnet" in slug else "Claude Opus 5.5 (High)"
    elif case in {"other-pin", "mismatch-then-duplicate", "mismatch-then-session"}:
        init["model"] = other
    elif case == "other-family":
        init["model"] = "gemini-3.8-flash-high"
    elif case == "nested-model":
        init["init"] = {"model": other}
    elif case == "nested-session":
        init["init"] = {"session_id": "different-session"}
    elif case == "terminal-session":
        terminal["result"]["conversation_id"] = "different-session"
    elif case.startswith("repeated"):
        repeated = dict(init)
        if case == "repeated-model":
            repeated["model"] = other
        elif case == "repeated-session":
            repeated["session_id"] = "different-session"
        elif case == "repeated-source":
            repeated["source"] = "configuration"
        events.append(repeated)
    elif case in {"unknown", "retired", "non-string"}:
        init["model"] = {"unknown": "unrecognized", "retired": "Claude Opus 4.6 (Thinking)", "non-string": 7}[case]
    elif case == "configuration":
        init["source"] = "requested"
    elif case == "missing":
        events = []
    elif case == "late":
        events.insert(0, {"event": "step_update"})
    elif case == "provider-failure":
        terminal["result"].update(status="ERROR", error="synthetic provider failure")
    if case == "mismatch-then-session":
        events.append({**init, "session_id": "different-session"})
    lines = list(map(json.dumps, events))
    if case in {"duplicate-after", "mismatch-then-duplicate"}:
        lines.append('{"event":"step_update","metadata":[{"model":"one","\\u006dodel":"two"}]}')
    lines.append(json.dumps(terminal))
    return "\n".join(lines) + "\n"


@pytest.mark.parametrize("nested,top,observed", [
    ("other-nested", "other-top", "other-nested"),
    ("other-nested", "gemini-4-argon-high", "other-nested"),
    ("gemini-4-argon-high", "other-top", "other-top"),
])
def test_argon_preserves_nested_first_mismatch_observation(tmp_path, nested, top, observed):
    plan, terminal = _identity_stream_plan(tmp_path, "gemini-4-argon-high")
    identity = {}
    result, problem = agy._stream_result(
        "\n".join(map(json.dumps, [{"event": "init", "init": {"model": nested}, "model": top}, terminal])),
        plan=plan, model_identity=identity,
    )
    assert result is None
    assert problem == "agy_model_event_mismatch"
    assert identity == {"actual_model": observed, "actual_model_known": True,
                        "substituted": True, "source": "provider-init"}
