"""Replay recorded planner/result shapes with public replacement targets (#8771).

The planner shape comes from generic_results_transcript.jsonl; native denial
result text comes from the AGY 1.2.17 permission probe. No private data retained.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

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
    assert attempt["via_symlink"] is False
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


def test_parent_traversal_is_classified_outside(tmp_path, recorded_transcript):
    plan, _ = denial_plan(tmp_path, recorded_transcript, "../outside.txt")
    attempt = record(parse(plan))
    assert attempt["permission_target"] == "outside:repo-root"
    assert attempt["via_symlink"] is False


@pytest.mark.parametrize("direction", ["outward", "inward", "within", "parent"])
def test_symlink_preserves_requested_classification(tmp_path, recorded_transcript, direction):
    plan, events = denial_plan(tmp_path, recorded_transcript, "evidence.txt")
    if direction == "inward":
        requested = tmp_path / "repo" / "evidence.txt"
        resolved = plan.cwd / "resolved-private-name.txt"
        expected = "outside:repo-root"
    elif direction == "parent":
        (plan.cwd / "inputs").symlink_to(tmp_path / "repo", target_is_directory=True)
        requested = plan.cwd / "inputs" / "evidence.txt"
        resolved = tmp_path / "repo" / "evidence.txt"
        expected = "workspace:inputs/evidence.txt"
    else:
        requested = plan.cwd / "evidence.txt"
        resolved = (plan.cwd if direction == "within" else tmp_path / "repo") / "resolved-private-name.txt"
        expected = "workspace:evidence.txt"
    if direction != "parent":
        requested.symlink_to(resolved)
    events[-1]["tool_calls"][0]["args"]["AbsolutePath"] = json.dumps(str(requested))
    agy._transcript_path_from_plan(plan).write_text("\n".join(json.dumps(event) for event in events))
    result = parse(plan)
    attempt = record(result)
    assert attempt["permission_target"] == expected
    assert attempt["via_symlink"] is True
    assert str(resolved) not in json.dumps(attempt) + result.stderr_excerpt
    assert "resolved-private-name" not in json.dumps(attempt) + result.stderr_excerpt


@pytest.mark.parametrize(
    "kind,target,reason",
    [
        ("read_file", "bad\nname", "target_unsafe"),
        ("read_file", "file:///private/file", "file_target_invalid"),
        ("read_url", "https://[::1]/private?q=x", "url_host_private"),
        ("read_url", "https://127.0.0.1/private", "url_host_private"),
        ("read_url", "not-a-url", "url_invalid"),
        pytest.param("read_url", "https://fixture.internal../private", "url_invalid", id="invalid-empty-label"),
        pytest.param("read_url", "https://%66ixture.internal/private", "url_invalid", id="encoded-host"),
        pytest.param("read_url", "https://éxample.org/private", "url_invalid", id="unicode-host"),
        *[
            pytest.param("read_url", f"https://{host}/private?q=x", "url_host_private", id=label)
            for label, host in [
                ("single-label", "fixture"),
                ("single-hex-label", "0x7f000001"),
                ("single-decimal-label", "2130706433"),
                ("localhost", "localhost"),
                ("ipv4-private-10", ".".join(map(str, (10, 0, 0, 1)))),
                ("ipv4-private-172", ".".join(map(str, (172, 16, 0, 1)))),
                ("ipv4-private-192", ".".join(map(str, (192, 168, 0, 1)))),
                ("ipv4-public", ".".join(map(str, (200, 1, 2, 3)))),
                ("ipv4-unspecified", "0.0.0.0"),
                ("ipv4-short", "127.1"),
                ("ipv6-private", "[fd00::1]"),
                ("ipv6-link-local", "[fe80::1]"),
                ("ipv6-public", "[2000::1]"),
                ("ipv6-mapped", "[::ffff:127.0.0.1]"),
                ("ipv6-unspecified", "[::]"),
                *[
                    ("suffix-" + suffix, "fixture." + suffix)
                    for suffix in (
                        "local",
                        "localhost",
                        "internal",
                        "lan",
                        "home.arpa",
                        "test",
                        "invalid",
                        "example",
                        "onion",
                    )
                ],
                ("suffix-uppercase-root-dot", "FIXTURE.INTERNAL."),
                ("localhost-root-dot", "LOCALHOST."),
                ("home-arpa-apex", "home.arpa"),
            ]
        ],
    ],
)
@pytest.mark.parametrize("source", ["transcript", "cli"])
def test_unsafe_or_invalid_target_is_not_persisted(tmp_path, recorded_transcript, kind, target, reason, source):
    tool, arg = ("view_file", "AbsolutePath") if kind == "read_file" else ("read_url_content", "Url")
    plan, events = denial_plan(tmp_path, recorded_transcript, target, tool=tool, arg=arg)
    if source == "cli":
        events[-1]["tool_calls"] = []
        agy._transcript_path_from_plan(plan).write_text("\n".join(json.dumps(event) for event in events))
        result = agy.AgyAdapter().parse_response(
            stdout="", stderr=auto_denial(f"{kind}({target})"), returncode=1, output_file=None, plan=plan
        )
    else:
        result = parse(plan, kind)
    attempt = record(result)
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == reason
    assert attempt["via_symlink"] is False
    assert target not in json.dumps(attempt) + result.stderr_excerpt


@pytest.mark.parametrize(
    "problem", ["unbound", "corrupt", "read-refused", "missing-trigger", "ambiguous", "missing-arg"]
)
@pytest.mark.parametrize("kind", ["read_file", "read_url"])
def test_cli_notice_target_fills_missing_transcript_target(tmp_path, recorded_transcript, monkeypatch, problem, kind):
    tool, arg = ("view_file", "AbsolutePath") if kind == "read_file" else ("read_url_content", "Url")
    plan, events = denial_plan(tmp_path, recorded_transcript, "unused", tool=tool, arg=arg)
    transcript = agy._transcript_path_from_plan(plan)
    if problem == "unbound":
        Path(plan.env_overrides[agy._AGY_LOG_ENV]).write_text("no conversation bound")
    elif problem == "corrupt":
        transcript.write_text("{truncated\n")
    elif problem == "read-refused":

        def refuse(*args, **kwargs):
            raise agy.AttemptReadError("attempt_read_symlink")

        monkeypatch.setattr(agy, "safe_read_attempt_file", refuse)
    else:
        if problem == "missing-trigger":
            events[-1]["tool_calls"] = []
        elif problem == "ambiguous":
            events[-1]["tool_calls"] *= 2
            events[-1]["tool_calls"][1] = {"name": tool, "args": {arg: '"other"'}}
        else:
            events[-1]["tool_calls"][0]["args"] = {}
        transcript.write_text("\n".join(json.dumps(event) for event in events))
    target = "evidence.txt" if kind == "read_file" else "https://example.org/private?q=x"
    result = agy.AgyAdapter().parse_response(
        stdout="", stderr=auto_denial(f"{kind}({target})"), returncode=1, output_file=None, plan=plan
    )
    attempt = record(result)
    assert attempt["permission_target"] == ("workspace:evidence.txt" if kind == "read_file" else "url:example.org")
    assert attempt["permission_target_unknown_reason"] is None
    assert attempt["via_symlink"] is False
    assert "private?q=x" not in json.dumps(attempt) + result.stderr_excerpt


@pytest.mark.parametrize("target", ["transcript.txt", "https://fixture.internal/private"])
def test_cli_fallback_does_not_override_transcript_target(tmp_path, recorded_transcript, target):
    kind = "read_url" if "://" in target else "read_file"
    tool, arg = ("view_file", "AbsolutePath") if kind == "read_file" else ("read_url_content", "Url")
    plan, _ = denial_plan(tmp_path, recorded_transcript, target, tool=tool, arg=arg)
    result = agy.AgyAdapter().parse_response(
        stdout="",
        stderr=auto_denial(f"{kind}(https://example.org/fallback)"),
        returncode=1,
        output_file=None,
        plan=plan,
    )
    attempt = record(result)
    assert attempt["permission_target"] == ("workspace:transcript.txt" if kind == "read_file" else "unknown")
    assert attempt["permission_target_unknown_reason"] == (None if kind == "read_file" else "url_host_private")


@pytest.mark.parametrize("host", ["EXAMPLE.ORG.", "fixture.locality.org", "local.example.org", "example.org"])
def test_public_domain_is_not_confused_with_private_suffix(tmp_path, recorded_transcript, host):
    plan, _ = denial_plan(tmp_path, recorded_transcript, f"https://{host}/private", tool="read_url_content", arg="Url")
    attempt = record(parse(plan, "read_url"))
    assert attempt["permission_target"] == "url:" + host.lower().removesuffix(".")
    assert attempt["permission_target_unknown_reason"] is None
