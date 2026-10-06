"""Replay recorded planner/result shapes with public replacement targets (#8771).

The planner shape comes from generic_results_transcript.jsonl; native denial
result text comes from the AGY 1.2.17 permission probe. No private data retained.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlunsplit

import pytest

from scripts.agent_runtime.adapters import agy
from scripts.agent_runtime.result import AgyTelemetry
from tests.agent_runtime.adapters.test_agy_adapter import _FINISHED_CONVERSATION_ID, _background_plan
from tests.agent_runtime.adapters.test_agy_cancel_recovery import _explicit_denial
from tests.agent_runtime.adapters.test_agy_review_permissions import auto_denial


@pytest.fixture
def recorded_transcript():
    return [
        json.loads(line)
        for line in (Path(__file__).parent / "fixtures" / "headless_denial.jsonl").read_text().splitlines()
    ]


def denial_plan(tmp_path, recorded_transcript, target, *, kind="read_file", tool="view_file", arg="AbsolutePath"):
    events = json.loads(json.dumps(recorded_transcript))
    events[-1]["tool_calls"] = [{"name": tool, "args": {arg: json.dumps(str(target))}}]
    plan = _background_plan(tmp_path, _FINISHED_CONVERSATION_ID, [json.dumps(event) for event in events])
    workspace = tmp_path / "repo" / ".worktrees" / "dispatch" / "codex" / "fixture"
    workspace.mkdir(parents=True, exist_ok=True)
    plan = replace(plan, cwd=workspace)
    return plan, events


def parse(plan, kind="read_file"):
    return agy.AgyAdapter().parse_response(
        stdout="", stderr=auto_denial(kind), returncode=1, output_file=None, plan=plan
    )


def record(result):
    assert not result.ok and not result.response and not result.rate_limited
    assert result.failure_code == "provider_policy_refusal"
    assert not result.agy_pre_model_failure
    return AgyTelemetry(attempts=(result.agy_attempt,)).task_fields()["agy_attempts"][0]


@pytest.mark.parametrize("absolute", [False, True])
def test_workspace_target_survives_json_record(tmp_path, recorded_transcript, absolute):
    workspace = tmp_path / "repo" / ".worktrees" / "dispatch" / "codex" / "fixture"
    target = str(workspace / "inputs" / "evidence.txt") if absolute else "inputs/evidence.txt"
    plan, _ = denial_plan(tmp_path, recorded_transcript, target)
    result = parse(plan)
    attempt = record(result)
    assert attempt["permission_target"] == "workspace:inputs/evidence.txt"
    assert attempt["denied_tool_name"] == "view_file"
    assert attempt["permission_kind"] == "read_file"
    assert attempt["permission_target_unknown_reason"] is None
    assert str(tmp_path) not in json.dumps(attempt) + result.stderr_excerpt


@pytest.mark.parametrize("label", ["home", "repo-root", "system", "tmp", "other"])
def test_outside_target_classes(tmp_path, recorded_transcript, monkeypatch, label):
    home = tmp_path / "private-user-home"
    monkeypatch.setattr(agy.Path, "home", lambda: home)
    targets = {
        "home": home / "private-name" / "secret.txt",
        "repo-root": tmp_path / "repo" / "private-name.txt",
        "system": Path("/etc/private-name.conf"),
        "tmp": tmp_path / "scratch" / "private-name.txt",
        "other": Path("/unclassified-fixture/private-name.txt"),
    }
    plan, _ = denial_plan(tmp_path, recorded_transcript, targets[label])
    plan = replace(plan, env_overrides={**plan.env_overrides, "TMPDIR": str(tmp_path / "scratch")})
    result = parse(plan)
    attempt = record(result)
    assert attempt["permission_target"] == "outside:" + label
    assert "private-name" not in json.dumps(attempt) + result.stderr_excerpt
    assert "private-user-home" not in json.dumps(attempt) + result.stderr_excerpt


def test_url_keeps_only_host(tmp_path, recorded_transcript):
    # Parts stay separate in source so secret scan never sees a userinfo URI literal.
    target = urlunsplit(
        (
            "https",
            "private-user" + ":" + "private-password" + "@" + "EXAMPLE.org:8443",
            "/private-path",
            "q=private-query",
            "private-fragment",
        )
    )
    plan, _ = denial_plan(tmp_path, recorded_transcript, target, tool="read_url_content", arg="Url")
    result = parse(plan, "read_url")
    attempt = record(result)
    assert attempt["permission_target"] == "url:example.org"
    assert attempt["permission_kind"] == "read_url"
    assert attempt["denied_tool_name"] == "read_url_content"
    assert "private-" not in json.dumps(attempt) + result.stderr_excerpt


@pytest.mark.parametrize("problem", ["missing", "corrupt", "read-error", "symlink", "unbound"])
def test_unreadable_transcript_stays_typed_unknown(tmp_path, recorded_transcript, monkeypatch, problem):
    plan, _ = denial_plan(tmp_path, recorded_transcript, "private-name.txt")
    transcript = agy._transcript_path_from_plan(plan)
    if problem == "missing":
        transcript.unlink()
    elif problem == "corrupt":
        transcript.write_bytes(b"{truncated\n")
    elif problem == "read-error":
        monkeypatch.setattr(agy, "_read_transcript_events", lambda *a, **kw: None)
    elif problem == "symlink":
        transcript.unlink()
        transcript.symlink_to(tmp_path / "absent")
    else:
        Path(plan.env_overrides[agy._AGY_LOG_ENV]).write_text("no conversation bound")
    attempt = record(parse(plan))
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"]
    assert attempt["denied_tool_name"] is None


def test_safe_read_refusal_is_unknown_and_cannot_override_typed_failure(tmp_path, recorded_transcript, monkeypatch):
    plan, _ = denial_plan(tmp_path, recorded_transcript, "evidence.txt")

    def refuse(*args, **kwargs):
        raise agy.AttemptReadError("attempt_read_symlink")

    monkeypatch.setattr(agy, "safe_read_attempt_file", refuse)
    attempt = record(parse(plan))
    assert attempt["permission_target_unknown_reason"] == "transcript_read_refused"


def test_nonfatal_deny_rule_cannot_supply_headless_trigger(tmp_path, recorded_transcript):
    plan, events = denial_plan(tmp_path, recorded_transcript, "evidence.txt")
    events[-1]["tool_calls"].append({"name": "call_mcp_tool", "args": {"Arguments": "private-content"}})
    events.append({"type": "GENERIC", "status": "ERROR", "content": _explicit_denial("read_file", "evidence.txt")})
    agy._transcript_path_from_plan(plan).write_text("\n".join(json.dumps(event) for event in events))
    attempt = record(parse(plan))
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "tool_kind_unverified"


def test_terminal_native_permission_result_identifies_trigger(tmp_path, recorded_transcript):
    plan, events = denial_plan(tmp_path, recorded_transcript, "directory")
    events.append(
        {
            "type": "GENERIC",
            "status": "ERROR",
            "content": _explicit_denial("read_file", "evidence.txt").replace(
                "Matches user-configured deny rule.", "Headless auto-denial."
            ),
        }
    )
    agy._transcript_path_from_plan(plan).write_text("\n".join(json.dumps(event) for event in events))
    attempt = record(parse(plan))
    assert attempt["denied_tool_name"] == "view_file"
    assert attempt["permission_target"] == "workspace:evidence.txt"


@pytest.mark.parametrize(
    "tool,arg",
    [
        ("view_file", "AbsolutePath"),
        ("view_file_outline", "AbsolutePath"),
        ("view_code_item", "File"),
        ("list_dir", "DirectoryPath"),
        ("grep_search", "SearchPath"),
        ("find_by_name", "SearchDirectory"),
    ],
)
def test_file_tool_argument_inventory(tmp_path, recorded_transcript, tool, arg):
    plan, _ = denial_plan(tmp_path, recorded_transcript, "inputs", tool=tool, arg=arg)
    attempt = record(parse(plan))
    assert attempt["denied_tool_name"] == tool
    assert attempt["permission_target"] == "workspace:inputs"


@pytest.mark.parametrize(
    "args,name,reason",
    [
        ({}, "view_file", "target_missing"),
        ({"AbsolutePath": []}, "view_file", "target_missing"),
        ({"AbsolutePath": "x"}, "bad-name", "tool_unknown"),
        ({"Arguments": "x"}, "call_mcp_tool", "tool_kind_unverified"),
    ],
)
def test_unknown_tool_or_target_has_body_free_reason(tmp_path, recorded_transcript, args, name, reason):
    plan, events = denial_plan(tmp_path, recorded_transcript, "unused")
    events[-1]["tool_calls"] = [{"name": name, "args": args}]
    agy._transcript_path_from_plan(plan).write_text("\n".join(json.dumps(event) for event in events))
    attempt = record(parse(plan))
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == reason


def test_model_and_mcp_output_cannot_supply_native_trigger(tmp_path, recorded_transcript):
    plan, events = denial_plan(tmp_path, recorded_transcript, "evidence.txt", tool="call_mcp_tool", arg="Arguments")
    events.append({"type": "GENERIC", "status": "DONE", "content": _explicit_denial("read_file", "private-fake.txt")})
    events.append(
        {
            "type": "PLANNER_RESPONSE",
            "source": "MODEL",
            "status": "DONE",
            "content": _explicit_denial("read_file", "private-fake.txt"),
        }
    )
    agy._transcript_path_from_plan(plan).write_text("\n".join(json.dumps(event) for event in events))
    attempt = record(parse(plan))
    assert attempt["permission_target_unknown_reason"] == "trigger_missing"
    assert attempt["denied_tool_name"] is None


def test_error_mcp_output_cannot_supply_file_permission_evidence(tmp_path, recorded_transcript):
    plan, events = denial_plan(tmp_path, recorded_transcript, "evidence.txt", tool="call_mcp_tool", arg="Arguments")
    events.append(
        {
            "type": "GENERIC",
            "status": "ERROR",
            "content": _explicit_denial("read_file", "private-fake.txt").replace(
                "Matches user-configured deny rule.", "Headless auto-denial."
            ),
        }
    )
    agy._transcript_path_from_plan(plan).write_text("\n".join(json.dumps(event) for event in events))
    attempt = record(parse(plan))
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "tool_kind_unverified"
    assert attempt["denied_tool_name"] is None


def test_multiple_pending_calls_remain_unknown(tmp_path, recorded_transcript):
    plan, events = denial_plan(tmp_path, recorded_transcript, "evidence.txt")
    events[-1]["tool_calls"].append({"name": "view_file", "args": {"AbsolutePath": '"other.txt"'}})
    agy._transcript_path_from_plan(plan).write_text("\n".join(json.dumps(event) for event in events))
    attempt = record(parse(plan))
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"


def test_resumed_transcript_cannot_supply_previous_trigger(tmp_path, recorded_transcript):
    plan, _ = denial_plan(tmp_path, recorded_transcript, "private-old-target.txt")
    transcript = agy._transcript_path_from_plan(plan)
    baseline = {"conversation_id": _FINISHED_CONVERSATION_ID, "offset": transcript.stat().st_size}
    plan = replace(plan, metadata={agy._TRANSCRIPT_BASELINE_KEY: baseline})
    attempt = record(parse(plan))
    assert attempt["permission_target"] == "unknown"
    assert attempt["denied_tool_name"] is None


@pytest.mark.parametrize("target", ["../outside.txt", "evidence.txt"])
def test_symlink_and_parent_traversal_are_classified_outside(tmp_path, recorded_transcript, target):
    plan, _ = denial_plan(tmp_path, recorded_transcript, target)
    (plan.cwd / "evidence.txt").symlink_to(tmp_path / "repo" / "outside.txt")
    assert record(parse(plan))["permission_target"] == "outside:repo-root"


@pytest.mark.parametrize(
    "kind,target,reason",
    [
        ("read_file", "bad\nname", "target_unsafe"),
        ("read_file", "file:///private/file", "file_target_invalid"),
        ("read_url", "https://[::1]/private?q=x", "url_invalid"),
        ("read_url", "https://127.0.0.1/private", "url_host_private"),
        ("read_url", "not-a-url", "url_invalid"),
    ],
)
def test_unsafe_or_invalid_target_is_not_persisted(tmp_path, recorded_transcript, kind, target, reason):
    tool, arg = ("view_file", "AbsolutePath") if kind == "read_file" else ("read_url_content", "Url")
    plan, _ = denial_plan(tmp_path, recorded_transcript, target, tool=tool, arg=arg)
    attempt = record(parse(plan, kind))
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == reason
