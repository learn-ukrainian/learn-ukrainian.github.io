"""Headless review grants stay scoped, exact and checked before CLI probes."""

from __future__ import annotations

import json
import subprocess

import pytest

from scripts.agent_runtime.adapters import agy
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
    else:
        config["strict_mcp_config"] = True
    plan = build(tmp_path, config)
    tools = review_tools("full" if route == "full" else "isolated")
    settings = scoped / ".gemini" / "antigravity-cli" / "settings.json"
    assert json.loads(settings.read_text()) == {
        "permissions": {
            "allow": [
                *[f"mcp(sources/{name})" for name in sorted(tools)],
            ],
            "deny": ["command(*)", "write_file(*)"],
        }
    }
    assert settings.stat().st_mode & 0o777 == 0o600
    assert "--dangerously-skip-permissions" not in plan.cmd
    assert "--sandbox" in plan.cmd
    assert not (set(tools) & set(sources_tool_sets()[1]))
    # A repeated gate/launch builds the same settings, without a second grant.
    assert build(tmp_path, config).env_overrides == plan.env_overrides


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
    assert agy_review_settings(access)["permissions"]["deny"] == ["command(*)", "write_file(*)"]


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
    [("plan-review-a1-p2-r3", "command"), ("plan-review-a1-p3-r3", "command"), ("plan-review-a1-p2-full-2", "mcp")],
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
    assert json.loads(details) == {"permission_kind": kind, "permission_target": None}
    assert "skip-permissions" not in parsed.stderr_excerpt


@pytest.mark.parametrize("kind,target", [("command", "rg --pre bash"), ("mcp", "sources/query_ulif")])
def test_auto_denial_preserves_concrete_resource(kind, target):
    parsed = agy.AgyAdapter().parse_response(
        stdout="", stderr=auto_denial(f"{kind}({target})"), returncode=0, output_file=None
    )
    assert json.loads(parsed.stderr_excerpt.split("\n", 1)[1]) == {"permission_kind": kind, "permission_target": target}
    assert agy._headless_permission_denial(auto_denial(f"{kind}({target})")) == (kind, target)


def test_permission_help_example_is_not_an_observed_target():
    assert agy._headless_permission_denial(auto_denial("command", "cat example.txt")) == ("command", None)


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


def test_trusted_ukrainian_profile_requires_scoped_home_before_probe(tmp_path, monkeypatch):
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: pytest.fail("CLI probe"))
    with pytest.raises(agy.AgyReviewPermissionError, match="require_scoped_home"):
        build(tmp_path, {"review_profile": "ukrainian"})


@pytest.mark.parametrize("config", [None, {"review_profile": "code"}, {"task_family": "recon"}])
def test_prompt_keywords_never_enable_the_profile_for_recon(tmp_path, monkeypatch, config):
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: tmp_path / "agy.log")
    plan = build(tmp_path, config)
    assert "--dangerously-skip-permissions" in plan.cmd
    assert plan.metadata["agy_permission_profile_id"] is None


def test_profile_denies_commands_and_preserves_sources(tmp_path, scoped):
    plan = build(tmp_path, {"review_profile": "ukrainian", "agy_home_override": str(scoped)})
    assert plan.metadata["agy_permission_profile_id"] == "ukrainian-review-command-denial-v1"
    rules = json.loads((scoped / ".gemini" / "antigravity-cli" / "settings.json").read_text())["permissions"]
    assert "command(*)" in rules["deny"]
    assert not any(rule.startswith("mcp(") for rule in rules["deny"])
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
