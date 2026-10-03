"""Headless review grants stay scoped, exact and checked before CLI probes."""

from __future__ import annotations

import json

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
    commands = ["cat", "head", "tail", "wc", "rg"]
    if route == "full":
        commands += ["git status", "git diff", "git log", "git show", "git ls-files"]
    settings = scoped / ".gemini" / "antigravity-cli" / "settings.json"
    assert json.loads(settings.read_text()) == {
        "permissions": {
            "allow": [
                *[f"mcp(sources/{name})" for name in sorted(tools)],
                *[f"command({command})" for command in commands],
            ]
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
            "agy_required_permissions": ["command(cat)", "mcp(sources/verify_words)"],
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
