"""Headless review grants stay scoped, exact and checked before CLI probes."""

from __future__ import annotations

import json
import subprocess

import pytest

from scripts.agent_runtime.adapters import agy
from scripts.agent_runtime.review_mcp import agy_review_settings
from scripts.agent_runtime.sources_read_only import sources_tool_sets
from scripts.review.receipts.ledger import review_tools


@pytest.fixture
def scoped(tmp_path, monkeypatch):
    home = tmp_path / "review-home"
    (home / ".gemini" / "antigravity-cli").mkdir(parents=True)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: tmp_path / "agy.log")
    return home


def build(tmp_path, config, **extra):
    return agy.AgyAdapter().build_invocation(
        prompt="Review the supplied plan.",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="permissions",
        session_id=None,
        tool_config=config,
        **extra,
    )


@pytest.mark.parametrize("route", ["full", "isolated", "ad-hoc"])
def test_exact_review_grants(tmp_path, scoped, route):
    config = {"agy_home_override": str(scoped), "mcp_server_names": ["sources"]}
    if route != "ad-hoc":
        config["review_access"] = route
        config["review_profile"] = "ukrainian"
    else:
        config["strict_mcp_config"] = True
    plan = build(tmp_path, config)
    tools = review_tools("full" if route == "full" else "isolated")
    settings = scoped / ".gemini" / "antigravity-cli" / "settings.json"
    assert json.loads(settings.read_text()) == {
        "permissions": {
            "allow": [
                f"read_file({tmp_path.resolve()})",
                *[f"mcp(sources/{name})" for name in sorted(tools)],
            ],
            "deny": [
                "command(*)",
                "write_file(*)",
                *[f"mcp(sources/{name})" for name in sorted(set().union(*sources_tool_sets()) - tools)],
            ],
        }
    }
    assert settings.stat().st_mode & 0o777 == 0o600
    assert "--dangerously-skip-permissions" not in plan.cmd
    assert "--sandbox" in plan.cmd
    assert not (set(tools) & set(sources_tool_sets()[1]))
    # A repeated gate/launch builds the same settings, without a second grant.
    assert build(tmp_path, config).env_overrides == plan.env_overrides


@pytest.mark.parametrize("profile", ["ukrainian", "code"])
@pytest.mark.parametrize("route", ["full", "isolated", "permission-only"])
def test_profile_does_not_deny_workspace_evidence(tmp_path, scoped, route, profile):
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("workspace evidence")
    config = {"agy_home_override": str(scoped), "review_profile": profile}
    if route != "permission-only":
        config["review_access"] = route
    plan = build(tmp_path, config)
    assert plan.cwd == tmp_path
    rules = json.loads((scoped / ".gemini" / "antigravity-cli" / "settings.json").read_text())["permissions"]
    assert not any(rule.startswith("read_file(") for rule in rules["deny"])
    assert evidence.read_text() == "workspace evidence"


def test_permission_only_provisioned_home_passes_adapter_for_review_tools(tmp_path, monkeypatch):
    from scripts.agent_runtime.review_mcp import prepare_agy_permission_home

    token = tmp_path / "fixture-token"
    token.write_text("fixture")
    monkeypatch.setattr("scripts.agent_runtime.review_mcp._real_agy_token", lambda: token)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: tmp_path / "agy.log")
    home = prepare_agy_permission_home(tmp_path, checkout_root=tmp_path)
    settings = home / ".gemini" / "antigravity-cli" / "settings.json"
    before = settings.read_bytes()
    plan = build(
        tmp_path,
        {
            "review_profile": "ukrainian",
            "agy_home_override": str(home),
            "agy_required_permissions": [f"mcp(sources/{name})" for name in review_tools()],
        },
    )
    assert settings.read_bytes() == before
    assert "--dangerously-skip-permissions" not in plan.cmd


@pytest.mark.parametrize(
    "required",
    [
        *[f"mcp(sources/{name})" for name in sources_tool_sets()[1]],
        "mcp(other/verify_words)",
        "mcp(sources/nonexistent)",
        "command(cat)",
        "write_file(*)",
    ],
)
def test_permission_only_route_refuses_writers_and_non_sources(tmp_path, scoped, required):
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permission_outside_allow_set"):
        build(
            tmp_path,
            {
                "review_profile": "ukrainian",
                "agy_home_override": str(scoped),
                "agy_required_permissions": [required],
            },
        )
    assert not (scoped / ".gemini" / "antigravity-cli" / "settings.json").exists()


@pytest.mark.parametrize("required", sorted(set().union(*sources_tool_sets()) - review_tools()))
def test_permission_only_route_refuses_every_non_review_sources_tool(tmp_path, scoped, required):
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permission_outside_allow_set"):
        build(
            tmp_path,
            {
                "review_profile": "ukrainian",
                "agy_home_override": str(scoped),
                "agy_required_permissions": [f"mcp(sources/{required})"],
            },
        )


@pytest.mark.parametrize("route", [None, "isolated", "full"])
def test_unreadable_inventory_refuses_before_launch_even_after_cached_read(tmp_path, scoped, monkeypatch, route):
    from scripts.agent_runtime import review_mcp

    agy_review_settings(route)
    monkeypatch.setattr(review_mcp, "sources_server_launch", lambda: (tmp_path / "interpreter", tmp_path / "missing"))
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: pytest.fail("must refuse before probe"))
    config = {"review_profile": "ukrainian", "agy_home_override": str(scoped)}
    if route:
        config["review_access"] = route
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permissions_tool_inventory_unavailable"):
        build(tmp_path, config)
    assert not (scoped / ".gemini" / "antigravity-cli" / "settings.json").exists()


def test_deny_inventory_uses_launched_server_declarations(tmp_path, monkeypatch):
    from scripts.agent_runtime import review_mcp
    from scripts.agent_runtime.sources_read_only import SERVER_PATH

    server = tmp_path / "server.py"
    # Add a tool to the actual list_tools declaration, with its default read-only annotation.
    text = SERVER_PATH.read_text()
    start = text.index("async def list_tools")
    offset = text.index("return [", start) + len("return [")
    server.write_text(
        text[:offset] + '\n_tool(name="future_reader", description="fixture", inputSchema={}),\n' + text[offset:]
    )
    monkeypatch.setattr(review_mcp, "sources_server_launch", lambda: (tmp_path / "interpreter", server))
    rules = agy_review_settings()["permissions"]
    assert "mcp(sources/future_reader)" in rules["deny"]
    assert "mcp(sources/future_reader)" not in rules["allow"]


@pytest.mark.parametrize("marker", ["review_id", "attempt_id", "review_attempt_boundary"])
def test_receipt_marker_prevents_permission_only_widening(tmp_path, scoped, marker):
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permission_outside_allow_set"):
        build(
            tmp_path,
            {
                "review_profile": "ukrainian",
                "agy_home_override": str(scoped),
                marker: "receipt",
                "agy_required_permissions": ["mcp(sources/search_resources)"],
            },
        )


@pytest.mark.parametrize(
    "required", ["command(rm)", "command(*)", "mcp(sources/query_ulif)", "mcp(other/verify_words)", "read_url(*)"]
)
def test_outside_requirements_refused_before_probe(tmp_path, scoped, monkeypatch, required):
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: pytest.fail("CLI probe"))
    with pytest.raises(ValueError, match="agy_review_permission_outside_allow_set"):
        build(
            tmp_path,
            {"review_access": "isolated", "agy_home_override": str(scoped), "agy_required_permissions": [required]},
        )
    assert not (scoped / ".gemini" / "antigravity-cli" / "settings.json").exists()


@pytest.mark.parametrize("route", ["full", "isolated"])
def test_review_missing_scoped_home_refused_before_probe(tmp_path, monkeypatch, route):
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: pytest.fail("CLI probe"))
    with pytest.raises(ValueError, match="agy_review_permissions_require_scoped_home"):
        build(tmp_path, {"review_access": route})


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"permissions": {"allow": ["mcp(*)"]}},
        {"permissions": {"allow": [], "ask": ["mcp(*)"]}},
        {"toolPermission": "always-proceed"},
        {"permissions": {"allow": ["read_file(*)"]}},
        {"permissions": {"allow": ["read_file(/)"]}},
        {"permissions": {"allow": ["command(cat)"]}},
        {"permissions": {"allow": ["write_file(*)"]}},
    ],
)
def test_existing_config_is_not_silently_repaired(tmp_path, scoped, settings):
    path = scoped / ".gemini" / "antigravity-cli" / "settings.json"
    path.write_text(json.dumps(settings))
    with pytest.raises(ValueError, match="agy_review_permissions_config_mismatch"):
        build(tmp_path, {"review_access": "isolated", "agy_home_override": str(scoped)})
    assert json.loads(path.read_text()) == settings


def test_scoped_settings_symlink_does_not_touch_global_config(tmp_path, scoped):
    global_settings = tmp_path / "global-settings.json"
    global_settings.write_text("{}")
    path = scoped / ".gemini" / "antigravity-cli" / "settings.json"
    path.symlink_to(global_settings)
    with pytest.raises(ValueError, match="agy_review_permissions_unsafe_config"):
        build(tmp_path, {"review_access": "isolated", "agy_home_override": str(scoped)})
    assert global_settings.read_text() == "{}"


def test_review_skip_permissions_refused_before_probe(tmp_path, scoped, monkeypatch):
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: pytest.fail("CLI probe"))
    with pytest.raises(ValueError, match="agy_review_permission_outside_allow_set"):
        build(tmp_path, {"review_access": "isolated", "agy_home_override": str(scoped), "agy_skip_permissions": True})


@pytest.mark.parametrize("access", ["full", "isolated"])
@pytest.mark.parametrize("writer", sources_tool_sets()[1])
def test_every_sources_writer_is_refused(tmp_path, scoped, access, writer):
    with pytest.raises(agy.AgyReviewPermissionError) as refused:
        build(
            tmp_path,
            {
                "review_access": access,
                "agy_home_override": str(scoped),
                "agy_required_permissions": [f"mcp(sources/{writer})"],
            },
        )
    assert refused.value.reason.startswith("agy_review_permission_outside_allow_set")


@pytest.mark.parametrize(
    "extra",
    [
        {"allowed_tools": "Write"},
        {"allowed_tools": ["Read"]},
        {"mcp_server_names": ["sources", "other"]},
        {"agy_required_permissions": "command(cat)"},
        {"agy_required_permissions": [None]},
        {"agy_required_permissions": ["command(git status)"]},
    ],
)
def test_requirement_shapes_and_route_capabilities_fail_closed(tmp_path, scoped, extra):
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permission_outside_allow_set"):
        build(tmp_path, {"review_access": "isolated", "agy_home_override": str(scoped), **extra})


def test_declared_admitted_requirements_and_tools(tmp_path, scoped):
    plan = build(
        tmp_path,
        {
            "review_access": "isolated",
            "agy_home_override": str(scoped),
            "allowed_tools": "Read,Glob,Grep,mcp__sources__verify_words",
            "agy_required_permissions": ["mcp(sources/verify_words)"],
        },
    )
    assert "--dangerously-skip-permissions" not in plan.cmd


def test_invalid_access_and_resumed_session_are_refused(tmp_path, scoped):
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permissions_invalid_access"):
        build(tmp_path, {"review_access": "unknown", "agy_home_override": str(scoped)})
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permissions_require_fresh_session"):
        agy.AgyAdapter().build_invocation(
            prompt="",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id="test",
            session_id="previous",
            tool_config={"review_access": "isolated", "agy_home_override": str(scoped)},
        )


def test_review_home_cannot_be_global_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permissions_require_scoped_home"):
        build(tmp_path, {"review_access": "isolated", "agy_home_override": str(tmp_path)})


@pytest.mark.parametrize("content", ["{", '{"permissions": {}, "permissions": {}}', "x" * 65537])
def test_malformed_and_oversized_settings_are_refused(tmp_path, scoped, content):
    (scoped / ".gemini" / "antigravity-cli" / "settings.json").write_text(content)
    with pytest.raises(agy.AgyReviewPermissionError, match=r"agy_review_permissions_(unsafe_config|config_mismatch)"):
        build(tmp_path, {"review_access": "isolated", "agy_home_override": str(scoped)})


def test_settings_directory_symlink_is_refused(tmp_path, scoped):
    app = scoped / ".gemini" / "antigravity-cli"
    app.rmdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    app.symlink_to(outside, target_is_directory=True)
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permissions_unsafe_config"):
        build(tmp_path, {"review_access": "isolated", "agy_home_override": str(scoped)})
    assert not (outside / "settings.json").exists()


def test_ad_hoc_reviewer_marker_requires_scoped_home(tmp_path):
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permissions_require_scoped_home"):
        build(tmp_path, {"reviewer_tools": True})


# Audit every granted executable's documented flag surface. An added executable
# or newly documented option needs inspection, rather than silently inheriting
# an unbounded prefix grant (as rg --pre did).
READER_LONG_OPTIONS = {
    "cat": {"show-all", "number-nonblank", "show-ends", "number", "squeeze-blank", "show-tabs", "show-nonprinting"},
    "head": {"bytes", "lines", "quiet", "silent", "verbose", "zero-terminated"},
    "tail": {
        "bytes",
        "follow",
        "lines",
        "pid",
        "quiet",
        "silent",
        "sleep-interval",
        "max-unchanged-stats",
        "verbose",
        "zero-terminated",
        "use-polling",
        "retry",
        "debug",
    },
    "wc": {"bytes", "chars", "files0-from", "lines", "max-line-length", "total", "words"},
}


@pytest.mark.parametrize("access", ["full", "isolated"])
def test_review_command_grants_are_empty(access):
    from scripts.agent_runtime.review_mcp import agy_review_settings

    commands = [
        rule[8:-1] for rule in agy_review_settings(access)["permissions"]["allow"] if rule.startswith("command(")
    ]
    assert not commands
    assert agy_review_settings(access)["permissions"]["deny"][:2] == ["command(*)", "write_file(*)"]


@pytest.mark.parametrize("binary", READER_LONG_OPTIONS)
@pytest.mark.parametrize("flag", ["--pre", "--exec", "--to-command", "--output"])
def test_granted_readers_reject_program_and_output_flags(tmp_path, binary, flag):
    marker = tmp_path / "executed"
    program = tmp_path / "program"
    program.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
    program.chmod(0o700)
    result = subprocess.run(
        [binary, f"{flag}={program}"], input="evidence\n", capture_output=True, text=True, timeout=5
    )
    assert result.returncode != 0
    assert not marker.exists()
    assert program.read_text().startswith("#!/bin/sh")


@pytest.mark.parametrize("access", ["full", "isolated"])
@pytest.mark.parametrize(
    "command",
    [
        "rg",
        "rg --pre bash",
        "rg --pre-glob *",
        "git status",
        "git ls-files",
        "git log --output=settings.json",
        "git diff --output=settings.json",
        "git show --output=settings.json",
    ],
)
def test_executing_and_settings_writing_commands_have_no_grant(tmp_path, scoped, access, command):
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permission_outside_allow_set"):
        build(
            tmp_path,
            {
                "review_access": access,
                "agy_home_override": str(scoped),
                "agy_required_permissions": [f"command({command})"],
            },
        )


def auto_denial(kind, target="<target>"):
    # Verbatim CLI line retained in the three named tasks' stderr.log files;
    # the logs had command, command and mcp respectively, with no real target.
    return (
        f'jetski: no output produced — a tool required the "{kind}" permission that headless mode cannot prompt for, '
        f"so it was auto-denied. Add an allow-rule under permissions.allow in settings.json (e.g. {kind}({target})). "
        "Alternatively, re-run with --dangerously-skip-permissions to auto-approve all tools."
    )


@pytest.mark.parametrize(
    "task,kind",
    [
        ("plan-review-a1-p2-r3", "command"),
        ("plan-review-a1-p3-r3", "command"),
        ("plan-review-a1-p2-full-2", "mcp"),
        ("uk9623-v2-smoke-3-flash-adapted-v2-r1-review-00", "read_file"),
        ("uk9623-v2-smoke-3-flash-none-r1-review-00", "read_file"),
        ("uk9623-v2-smoke-3-flash-none-r1-review-03", "mcp"),
    ],
)
@pytest.mark.parametrize("returncode", [0, 1])
def test_recorded_headless_auto_denial_is_typed_before_completion(task, kind, returncode, monkeypatch):
    monkeypatch.setattr(agy, "_completion_gap", lambda *a: pytest.fail("denial must precede transcript gate"))
    parsed = agy.AgyAdapter().parse_response(
        stdout="",
        stderr="agy_background_task_unconfirmed\n" + auto_denial(kind),
        returncode=returncode,
        output_file=None,
    )
    assert not parsed.ok and not parsed.response and not parsed.rate_limited, task
    assert parsed.failure_code == "provider_policy_refusal"
    assert parsed.provider_error_text == ""
    reason, details = parsed.stderr_excerpt.split("\n", 1)
    assert reason == agy.AGY_HEADLESS_PERMISSION_DENIED
    assert reason in agy.AGY_INCOMPLETE_RUN_REASONS
    assert json.loads(details) == {"permission_kind": kind, "permission_target": "unknown"}
    assert parsed.agy_attempt.permission_target == "unknown"
    assert parsed.agy_attempt.permission_kind == kind
    assert "skip-permissions" not in parsed.stderr_excerpt


@pytest.mark.parametrize(
    "kind,target",
    [("command", "rg --pre bash"), ("mcp", "sources/query_ulif"), ("read_file", "workspace/evidence.txt")],
)
def test_auto_denial_does_not_persist_unbound_concrete_resource(kind, target):
    parsed = agy.AgyAdapter().parse_response(
        stdout="", stderr=auto_denial(f"{kind}({target})"), returncode=0, output_file=None
    )
    assert json.loads(parsed.stderr_excerpt.split("\n", 1)[1]) == {
        "permission_kind": kind,
        "permission_target": "unknown",
        "permission_target_source": "cli_notice",
        "transcript_read_reason": "transcript_unbound_or_unreadable",
    }
    assert target not in parsed.stderr_excerpt
    assert agy._headless_permission_denial(auto_denial(f"{kind}({target})")) == (kind, target)
    assert parsed.agy_attempt.permission_target == "unknown"
    assert parsed.agy_attempt.permission_target_unknown_reason == "target_kind_unsupported"


@pytest.mark.parametrize(
    "target,expected,reason",
    [
        ("https://example.org/private?q=x", "url:example.org", None),
        ("https://fixture.internal/private", "unknown", "url_host_private"),
    ],
)
def test_cli_url_fallback_needs_no_workspace_plan(target, expected, reason):
    from scripts.agent_runtime.result import AgyTelemetry

    parsed = agy.AgyAdapter().parse_response(
        stdout="", stderr=auto_denial(f"read_url({target})"), returncode=1, output_file=None
    )
    assert parsed.failure_code == "provider_policy_refusal"
    assert not parsed.ok and not parsed.agy_pre_model_failure
    attempt = AgyTelemetry(attempts=(parsed.agy_attempt,)).task_fields()["agy_attempts"][0]
    assert attempt["permission_target"] == expected
    assert attempt["permission_target_unknown_reason"] == reason
    assert attempt["denied_tool_name"] is None
    assert "private" not in parsed.stderr_excerpt


def test_permission_help_example_is_not_an_observed_target():
    assert agy._headless_permission_denial(auto_denial("command", "cat example.txt")) == ("command", None)
    assert agy._headless_permission_denial(auto_denial("read_file", "workspace/evidence.txt")) == ("read_file", None)


@pytest.mark.parametrize(
    "text",
    [
        "",
        'required the "command" permission',
        "agent: " + auto_denial("command"),
        auto_denial("command").replace("auto-denied", "approved"),
    ],
)
def test_non_cli_notices_are_not_permission_failures(text):
    assert agy._headless_permission_denial(text) is None


def test_model_response_cannot_supply_permission_denial(monkeypatch):
    monkeypatch.setattr(agy, "_completion_gap", lambda *a: (None, None))
    parsed = agy.AgyAdapter().parse_response(stdout=auto_denial("command"), stderr="", returncode=0, output_file=None)
    assert parsed.ok


@pytest.mark.parametrize("profile", ["ukrainian", "code"])
@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_review_profile_rejects_write_mode_before_probe(tmp_path, scoped, monkeypatch, profile, mode):
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: pytest.fail("CLI probe"))
    with pytest.raises(agy.AgyReviewPermissionError, match="agy_review_permissions_require_read_only"):
        agy.AgyAdapter().build_invocation(
            prompt="Review the supplied plan.",
            mode=mode,
            cwd=tmp_path,
            model=None,
            task_id="permissions",
            session_id=None,
            tool_config={"review_profile": profile, "agy_home_override": str(scoped)},
        )
    assert not (scoped / ".gemini" / "antigravity-cli" / "settings.json").exists()


@pytest.mark.parametrize("profile", ["ukrainian", "code"])
def test_trusted_review_profile_requires_scoped_home_before_probe(tmp_path, monkeypatch, profile):
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: pytest.fail("CLI probe"))
    with pytest.raises(agy.AgyReviewPermissionError, match="require_scoped_home"):
        build(tmp_path, {"review_profile": profile})


@pytest.mark.parametrize("config", [None, {"task_family": "recon"}])
def test_prompt_keywords_never_enable_the_profile_for_recon(tmp_path, monkeypatch, config):
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: tmp_path / "agy.log")
    plan = build(tmp_path, config)
    assert "--dangerously-skip-permissions" in plan.cmd
    assert plan.metadata["agy_permission_profile_id"] is None


@pytest.mark.parametrize(
    ("profile", "profile_id"),
    [
        ("ukrainian", "ukrainian-review-command-denial-v3"),
        ("code", "code-review-command-denial-v1"),
    ],
)
def test_profile_denies_commands_and_preserves_sources(tmp_path, scoped, profile, profile_id):
    plan = build(tmp_path, {"review_profile": profile, "agy_home_override": str(scoped)})
    assert "--sandbox" in plan.cmd
    assert "--dangerously-skip-permissions" not in plan.cmd
    assert plan.metadata["agy_permission_profile_id"] == profile_id
    rules = json.loads((scoped / ".gemini" / "antigravity-cli" / "settings.json").read_text())["permissions"]
    assert "command(*)" in rules["deny"]
    assert "read_file(*)" not in rules["deny"]
    assert rules == agy_review_settings(None, checkout_root=tmp_path)["permissions"]
    assert {rule for rule in rules["deny"] if rule.startswith("mcp(")} == {
        f"mcp(sources/{tool})" for tool in set().union(*sources_tool_sets()) - review_tools()
    }
    assert all(
        f"mcp(sources/{tool})" in rules["allow"]
        for tool in ("verify_words", "query_cefr_level", "check_russian_shadow")
    )


def test_scoped_attempt_log_is_unique_in_same_process(tmp_path, scoped):
    config = {
        "review_access": "isolated",
        "agy_home_override": str(scoped),
        "review_attempt_boundary": True,
        "review_write_root": str(tmp_path),
    }
    first = build(tmp_path, config)
    second = build(tmp_path, config)
    assert first.env_overrides[agy._AGY_LOG_ENV] != second.env_overrides[agy._AGY_LOG_ENV]


@pytest.mark.parametrize("access", ["isolated", "full"])
def test_facet_authorities_granted_and_every_server_writer_denied(access):
    added = {
        "verify_word",
        "verify_lemma",
        "search_slovnyk_me",
        "search_esum",
        "search_grinchenko_1907",
        "search_definitions",
    }
    permissions = agy_review_settings(access)["permissions"]
    assert {f"mcp(sources/{tool})" for tool in added} <= set(permissions["allow"])
    for writer in sources_tool_sets()[1]:
        assert f"mcp(sources/{writer})" in permissions["deny"]
        assert f"mcp(sources/{writer})" not in permissions["allow"]


@pytest.mark.parametrize("access", ["isolated", "full"])
def test_checkout_read_grant_is_recursive_and_has_no_other_native_allow(tmp_path, access):
    checkout = tmp_path / "checkout with spaces"
    checkout.mkdir()
    rules = agy_review_settings(access, checkout_root=checkout)["permissions"]
    native = [rule for rule in rules["allow"] if not rule.startswith("mcp(sources/")]
    assert native == [f"read_file({checkout.resolve()})"]
    assert "command(*)" in rules["deny"]
    assert "write_file(*)" in rules["deny"]
    assert all("*" not in rule for rule in rules["allow"])


@pytest.mark.parametrize("name", ["*", "bad)name", "bad(name", "bad\nname", "bad\u202ename"])
def test_unsafe_checkout_names_never_become_permission_rules(tmp_path, name):
    checkout = tmp_path / name
    checkout.mkdir()
    with pytest.raises(ValueError, match="agy_review_permissions_unsafe_checkout"):
        agy_review_settings(checkout_root=checkout)


def test_filesystem_root_and_root_alias_never_become_read_grants(tmp_path):
    alias = tmp_path / "root-alias"
    alias.symlink_to("/", target_is_directory=True)
    for root in ("/", alias):
        with pytest.raises(ValueError, match="agy_review_permissions_unsafe_checkout"):
            agy_review_settings(checkout_root=root)


def test_checkout_change_refuses_existing_grant_before_probe(tmp_path, scoped, monkeypatch):
    build(tmp_path, {"review_access": "full", "agy_home_override": str(scoped)})
    other = tmp_path / "other-checkout"
    other.mkdir()
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: pytest.fail("CLI probe"))
    with pytest.raises(agy.AgyReviewPermissionError, match="config_mismatch"):
        build(other, {"review_access": "full", "agy_home_override": str(scoped)})
