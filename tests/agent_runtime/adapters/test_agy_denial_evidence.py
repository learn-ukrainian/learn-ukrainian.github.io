"""Replay recorded planner/result shapes with public replacement targets (#8771).

The planner shape comes from generic_results_transcript.jsonl; native denial
result text comes from the AGY 1.2.17 permission probe. No private data retained.
"""

from __future__ import annotations

import json
from dataclasses import replace
from itertools import permutations
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
    plan, events = denial_plan(tmp_path, recorded_transcript, "evidence.txt")
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


def test_native_permission_result_with_no_matching_call_is_unknown(tmp_path, recorded_transcript):
    plan, events = denial_plan(tmp_path, recorded_transcript, "never-denied.txt")
    events.append(_result("ERROR", _headless_read_denial("actually-denied.txt")))
    agy._transcript_path_from_plan(plan).write_text("\n".join(json.dumps(event) for event in events))
    attempt = record(parse(plan))
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"


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
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"
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
                ("ipv4-dotted-hex", "0xc0.0xa8.1.5"),
                ("ipv4-all-hex", "0x7f.0x0.0x0.0x1"),
                ("ipv4-mixed-radix", "0xc0.0250.1.0x5"),
                ("ipv4-octal", "0177.0.0.1"),
                ("ipv4-hex-short", "0x7f.1"),
                ("ipv4-hex-root-dot", "0x7f.0x1."),
                ("ipv4-hex-uppercase-root-dot", "0X7F.0XAB."),
                ("invalid-numeric-last-label", "foo.1"),
                ("invalid-hex-last-label", "foo.0x1"),
                ("invalid-empty-hex-last-label", "foo.0x"),
                ("invalid-empty-uppercase-hex-last-label", "foo.0X."),
                ("invalid-octal-last-label", "foo.09"),
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
                        "alt",
                        "home",
                        "corp",
                        "mail",
                        "localdomain",
                    )
                ],
                *[
                    ("suffix-uppercase-root-dot-" + suffix, "FIXTURE." + suffix.upper() + ".")
                    for suffix in ("alt", "home", "corp", "mail", "localdomain")
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
    assert attempt["permission_target_unknown_reason"] == (
        "trigger_ambiguous" if problem in {"ambiguous", "missing-arg"} else None
    )
    assert attempt["denied_tool_name"] is None
    assert attempt["via_symlink"] is False
    details = json.loads(result.stderr_excerpt.split("\n", 1)[1])
    assert details["permission_target_source"] == "cli_notice"
    transcript_reasons = {
        "unbound": "transcript_unbound_or_unreadable",
        "corrupt": "transcript_corrupt",
        "read-refused": "transcript_read_refused",
    }
    if problem in transcript_reasons:
        assert details["transcript_read_reason"] == transcript_reasons[problem]
        assert attempt["evidence_complete"] is False
    else:
        assert "transcript_read_reason" not in details
    assert "private?q=x" not in json.dumps(attempt) + result.stderr_excerpt


@pytest.mark.parametrize("target", ["transcript.txt", "https://fixture.internal/private"])
def test_matching_cli_notice_preserves_transcript_target_sanitization(tmp_path, recorded_transcript, target):
    kind = "read_url" if "://" in target else "read_file"
    tool, arg = ("view_file", "AbsolutePath") if kind == "read_file" else ("read_url_content", "Url")
    plan, _ = denial_plan(tmp_path, recorded_transcript, target, tool=tool, arg=arg)
    result = agy.AgyAdapter().parse_response(
        stdout="",
        stderr=auto_denial(f"{kind}({target})"),
        returncode=1,
        output_file=None,
        plan=plan,
    )
    attempt = record(result)
    assert attempt["permission_target"] == ("workspace:transcript.txt" if kind == "read_file" else "unknown")
    assert attempt["permission_target_unknown_reason"] == (None if kind == "read_file" else "url_host_private")
    assert attempt["denied_tool_name"] == tool


@pytest.mark.parametrize(
    "host",
    [
        "EXAMPLE.ORG.",
        "fixture.locality.org",
        "local.example.org",
        "example.org",
        "0x7f.example.org",
        "example.0xg",
        "example.0x1g",
        "example.1a",
        "alt.example.org",
        "fixture.homepage.org",
    ],
)
def test_public_domain_is_not_confused_with_private_suffix(tmp_path, recorded_transcript, host):
    plan, _ = denial_plan(tmp_path, recorded_transcript, f"https://{host}/private", tool="read_url_content", arg="Url")
    attempt = record(parse(plan, "read_url"))
    assert attempt["permission_target"] == "url:" + host.lower().removesuffix(".")
    assert attempt["permission_target_unknown_reason"] is None


# AGY 1.4.3 result slots, from live read-only code-review probes (#10334);
# paths replaced with fixture paths. Rule matches return the refusal to the
# model and the turn continues; only the unmatched (prompting) read ends it.
_REVIEW_PROFILE = "code-review-command-denial-v1"


def _stamped(text):
    return f"Created At: 2026-10-20T07:56:32Z\nCompleted At: 2026-10-20T07:56:33Z\n{text}"


def _rule_denial(kind, target, rule="user-configured deny"):
    return _stamped(
        f'Encountered error in step execution: permission check failed for {kind} "{target}": '
        f"Permission denied for {kind}({target}). Matches {rule} rule."
    )


def _headless_read_denial(target):
    return _stamped(
        f'Encountered error in step execution: permission check failed for read_file "{target}": '
        f"user denied permission for read_file({target})\n"
        "Do not attempt to circumvent this denial by rephrasing the command, using alternative tools/scripts "
        "(e.g. python, sh, curl), or accessing the same target resource. Proceed without performing this action."
    )


def _planner(*calls, content=None):
    event = {"source": "MODEL", "type": "PLANNER_RESPONSE", "status": "DONE"}
    if calls:
        event["tool_calls"] = [{"name": name, "args": {key: json.dumps(value)}} for name, key, value in calls]
    if content is not None:
        event["content"] = content
    return event


def _result(status, content):
    return {"source": "MODEL", "type": "GENERIC", "status": status, "content": content}


def review_plan(tmp_path, events, *, profile=_REVIEW_PROFILE):
    lines = [json.dumps({"type": "USER_INPUT", "status": "DONE", "content": "Public fixture review."})]
    plan = _background_plan(tmp_path, _FINISHED_CONVERSATION_ID, lines + [json.dumps(event) for event in events])
    workspace = tmp_path / "repo" / ".worktrees" / "dispatch" / "agy" / "fixture"
    workspace.mkdir(parents=True, exist_ok=True)
    return replace(plan, cwd=workspace, metadata={**plan.metadata, "agy_permission_profile_id": profile})


@pytest.mark.parametrize("result_type", ["GENERIC", "TOOL_RESPONSE"])
@pytest.mark.parametrize("status", ["DONE", "ERROR", "INVALID"])
def test_leftover_after_unidentified_result_is_ambiguous(tmp_path, result_type, status):
    events = [
        _planner(("read_file", "Path", "really-denied.txt"), ("list_dir", "DirectoryPath", "done-dir")),
        {**_result(status, "Directory listing result."), "type": result_type},
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"


@pytest.mark.parametrize("completed_result", [False, True])
@pytest.mark.parametrize("native_result", [False, True])
def test_cli_notice_mismatch_never_attributes_leftover_call(tmp_path, completed_result, native_result):
    calls = [("list_dir", "DirectoryPath", "done-dir")]
    if completed_result:
        calls.insert(0, ("read_file", "Path", "earlier.txt"))
    events = [
        _planner(*calls),
        *([_result("DONE", "Earlier read completed.")] if completed_result else []),
        *([_result("ERROR", _headless_read_denial("done-dir"))] if native_result else []),
    ]
    result = agy.AgyAdapter().parse_response(
        stdout="",
        stderr=auto_denial("read_file(really-denied.txt)"),
        returncode=1,
        output_file=None,
        plan=review_plan(tmp_path, events),
    )
    attempt = record(result)
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "workspace:really-denied.txt"
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"


def test_leftover_without_current_turn_results_is_attributed(tmp_path):
    events = [
        _planner(("list_dir", "DirectoryPath", "done-dir")),
        _result("DONE", "Directory listing completed."),
        _planner(("read_file", "Path", "really-denied.txt")),
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_tool_name"] == "read_file"
    assert attempt["permission_target"] == "workspace:really-denied.txt"
    assert attempt["permission_target_unknown_reason"] is None


@pytest.mark.parametrize("completed_result", [False, True])
def test_leftover_matching_concrete_cli_notice_is_attributed(tmp_path, completed_result):
    events = [
        _planner(
            *([("list_dir", "DirectoryPath", "done-dir")] if completed_result else []),
            ("read_file", "Path", "./really-denied.txt"),
        ),
        *([_result("DONE", "Directory listing completed.")] if completed_result else []),
    ]
    plan = review_plan(tmp_path, events)
    result = agy.AgyAdapter().parse_response(
        stdout="",
        stderr=auto_denial(f"read_file({plan.cwd / 'really-denied.txt'})"),
        returncode=1,
        output_file=None,
        plan=plan,
    )
    attempt = record(result)
    assert attempt["denied_tool_name"] == "read_file"
    assert attempt["permission_target"] == "workspace:really-denied.txt"
    assert attempt["permission_target_unknown_reason"] is None


@pytest.mark.parametrize("completed_tool", ["view_file", "view_file_outline"])
@pytest.mark.parametrize("reverse_calls", [False, True])
def test_cli_notice_with_same_target_calls_never_uses_result_order(tmp_path, completed_tool, reverse_calls):
    calls = [("view_file", "AbsolutePath", "x.txt"), ("view_file_outline", "AbsolutePath", "x.txt")]
    events = [
        _planner(*(reversed(calls) if reverse_calls else calls)),
        _result("DONE", f"{completed_tool} completed."),
    ]
    result = agy.AgyAdapter().parse_response(
        stdout="",
        stderr=auto_denial("read_file(x.txt)"),
        returncode=1,
        output_file=None,
        plan=review_plan(tmp_path, events),
    )
    attempt = record(result)
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "workspace:x.txt"
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"


def test_non_string_cli_notice_never_matches_missing_call_target(tmp_path):
    event = _planner(("list_dir", "DirectoryPath", "unused"))
    event["tool_calls"][0]["args"] = {}
    plan = review_plan(tmp_path, [event])
    evidence = agy._headless_denial_evidence(
        agy._invocation_transcript(plan), plan, "read_file", notice_target="null"
    )
    assert evidence.denied_tool_name is None
    assert evidence.permission_target_unknown_reason == "trigger_ambiguous"
    result = agy.AgyAdapter().parse_response(
        stdout="",
        stderr=auto_denial("read_file(null)"),
        returncode=1,
        output_file=None,
        plan=plan,
    )
    attempt = record(result)
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "target_missing"


@pytest.mark.parametrize("notice_target", ["x.txt", "unmatched.txt"])
def test_cli_notice_attributes_only_one_matching_call(tmp_path, notice_target):
    result = agy.AgyAdapter().parse_response(
        stdout="",
        stderr=auto_denial(f"read_file({notice_target})"),
        returncode=1,
        output_file=None,
        plan=review_plan(tmp_path, [_planner(("view_file", "AbsolutePath", "x.txt"))]),
    )
    attempt = record(result)
    assert attempt["permission_target"] == f"workspace:{notice_target}"
    assert attempt["denied_tool_name"] == ("view_file" if notice_target == "x.txt" else None)
    assert attempt["permission_target_unknown_reason"] == (None if notice_target == "x.txt" else "trigger_ambiguous")


def test_cli_notice_without_matching_call_keeps_target_and_ambiguity(tmp_path):
    events = [
        _planner(("list_dir", "DirectoryPath", "done-dir")),
        _result("DONE", "Directory listing completed."),
    ]
    result = agy.AgyAdapter().parse_response(
        stdout="",
        stderr=auto_denial("read_file(really-denied.txt)"),
        returncode=1,
        output_file=None,
        plan=review_plan(tmp_path, events),
    )
    attempt = record(result)
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "workspace:really-denied.txt"
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"


def _git_metadata_chain(tmp_path):
    """git refused by command(*), then the worktree pointer, then primary Git metadata."""
    workspace = tmp_path / "repo" / ".worktrees" / "dispatch" / "agy" / "fixture"
    git_dir = tmp_path / "repo" / ".git" / "worktrees" / "fixture"
    return [
        _planner(("run_command", "CommandLine", "git log -n 2 --oneline")),
        _result("ERROR", _rule_denial("unsandboxed", "git log -n 2 --oneline")),
        _planner(("read_file", "Path", str(workspace / ".git"))),
        _result("DONE", _stamped(f"Showing lines 1-1 of 1\n1: gitdir: {git_dir}")),
        _planner(("read_file", "Path", str(git_dir / "HEAD"))),
    ]


def test_review_ended_by_outside_git_metadata_read_names_the_read(tmp_path):
    plan = review_plan(tmp_path, _git_metadata_chain(tmp_path))
    result = parse(plan)
    attempt = record(result)
    assert attempt["permission_kind"] == "read_file"
    assert attempt["denied_tool_name"] == "read_file"
    assert attempt["permission_target"] == "outside:repo-root"
    assert attempt["permission_target_unknown_reason"] is None
    assert attempt["permission_profile_id"] == _REVIEW_PROFILE
    # The refused command is counted and was never executed; it did not end the run.
    assert attempt["denied_command_count"] == 1
    assert attempt["executed_command_count"] == 0
    reason, details = result.stderr_excerpt.split("\n", 1)
    assert reason == agy.AGY_HEADLESS_PERMISSION_DENIED
    assert json.loads(details) == {
        "permission_kind": "read_file",
        "permission_target": "outside:repo-root",
        "driver_hint": agy.AGY_DRIVER_HINT_INLINE_REVIEW_INPUTS,
    }
    assert str(tmp_path) not in json.dumps(attempt) + result.stderr_excerpt


def test_review_headless_read_result_slot_is_the_trigger_and_is_counted(tmp_path, monkeypatch):
    home = tmp_path / "private-user-home"
    monkeypatch.setattr(agy.Path, "home", lambda: home)
    workspace = tmp_path / "repo" / ".worktrees" / "dispatch" / "agy" / "fixture"
    target = home / "private-name" / "conventions.md"
    events = [
        _planner(("read_file", "Path", str(workspace / "calc.py")), ("read_file", "Path", str(target))),
        _result("DONE", _stamped("Showing lines 1-1 of 1\n1: def average(values): ...")),
        _result("ERROR", _headless_read_denial(target)),
    ]
    result = parse(review_plan(tmp_path, events))
    attempt = record(result)
    assert attempt["denied_tool_name"] == "read_file"
    assert attempt["permission_target"] == "outside:home"
    assert attempt["denied_file_read_count"] == 1
    assert json.loads(result.stderr_excerpt.split("\n", 1)[1])["driver_hint"] == "inline_review_inputs"
    assert "private-" not in json.dumps(attempt) + result.stderr_excerpt


@pytest.mark.parametrize("result_type", ["GENERIC", "TOOL_RESPONSE"])
@pytest.mark.parametrize("status", ["ERROR", "INVALID"])
@pytest.mark.parametrize("pending_count", [1, 2])
@pytest.mark.parametrize("denied_first", [False, True], ids=["pending-before", "pending-after"])
def test_explicit_denial_takes_precedence_over_pending_sibling_reads(
    tmp_path, result_type, status, pending_count, denied_first
):
    denied = ("read_file", "Path", "actually-denied.txt")
    siblings = [("list_dir", "DirectoryPath", f"never-denied-{index}") for index in range(pending_count)]
    events = [
        _planner(*([denied, *siblings] if denied_first else [*siblings, denied])),
        {**_result(status, _headless_read_denial("actually-denied.txt")), "type": result_type},
    ]
    result = parse(review_plan(tmp_path, events))
    attempt = record(result)
    assert attempt["denied_tool_name"] == "read_file"
    assert attempt["permission_target"] == "workspace:actually-denied.txt"
    assert attempt["permission_target_unknown_reason"] is None
    assert attempt["denied_file_read_count"] == 1
    assert json.loads(result.stderr_excerpt.split("\n", 1)[1])["permission_target"] == "workspace:actually-denied.txt"


@pytest.mark.parametrize("same_tool", [False, True])
@pytest.mark.parametrize("completed_first", [False, True])
def test_denial_with_two_matching_calls_is_ambiguous(tmp_path, same_tool, completed_first):
    second = ("read_file", "Path") if same_tool else ("view_file", "AbsolutePath")
    events = [
        _planner(("read_file", "Path", "actually-denied.txt"), (*second, "actually-denied.txt")),
        *([_result("DONE", "Earlier read completed.")] if completed_first else []),
        _result("ERROR", _headless_read_denial("actually-denied.txt")),
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"


@pytest.mark.parametrize("call_order", list(permutations(range(3))))
@pytest.mark.parametrize("denial_first", [False, True])
def test_completed_then_denied_then_pending_call_names_only_denied_call(tmp_path, call_order, denial_first):
    calls = [
        ("list_dir", "DirectoryPath", "completed-dir"),
        ("read_file", "Path", "actually-denied.txt"),
        ("view_file", "AbsolutePath", "pending.txt"),
    ]
    results = [
        _result("DONE", "Directory listing completed."),
        _result("ERROR", _headless_read_denial("actually-denied.txt")),
    ]
    events = [
        _planner(*(calls[index] for index in call_order)),
        *(reversed(results) if denial_first else results),
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_tool_name"] == "read_file"
    assert attempt["permission_target"] == "workspace:actually-denied.txt"
    assert attempt["permission_target_unknown_reason"] is None


@pytest.mark.parametrize("reverse_results", [False, True])
def test_two_headless_denials_are_ambiguous(tmp_path, reverse_results):
    targets = ["first.txt", "second.txt"]
    events = [
        _planner(("read_file", "Path", targets[0]), ("view_file", "AbsolutePath", targets[1])),
        *[_result("ERROR", _headless_read_denial(target)) for target in targets[:: -1 if reverse_results else 1]],
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"


def test_new_model_turn_clears_earlier_denial(tmp_path):
    events = [
        _planner(("read_file", "Path", "earlier.txt")),
        _result("ERROR", _headless_read_denial("earlier.txt")),
        _planner(content="Proceed without the read."),
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "trigger_missing"


@pytest.mark.parametrize("absolute", [False, True])
def test_denial_matches_decoded_path_before_privacy_sanitization(tmp_path, absolute):
    target = str(tmp_path / "repo" / "denied.txt") if absolute else "./actually-denied.txt"
    events = [
        _planner(("list_dir", "DirectoryPath", "never-denied-dir"), ("read_file", "Path", target)),
        _result("ERROR", _headless_read_denial(target)),
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_tool_name"] == "read_file"
    assert attempt["permission_target"] == ("outside:repo-root" if absolute else "workspace:actually-denied.txt")
    assert attempt["permission_target_unknown_reason"] is None


def test_different_outside_targets_cannot_match_by_sanitized_class(tmp_path):
    events = [
        _planner(("read_file", "Path", str(tmp_path / "repo" / "never-denied.txt"))),
        _result("ERROR", _headless_read_denial(tmp_path / "repo" / "actually-denied.txt")),
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "trigger_ambiguous"


def test_relative_call_matches_absolute_denied_path(tmp_path):
    workspace = tmp_path / "repo" / ".worktrees" / "dispatch" / "agy" / "fixture"
    events = [
        _planner(("list_dir", "DirectoryPath", "never-denied"), ("read_file", "Path", "./actually-denied.txt")),
        _result("ERROR", _headless_read_denial(workspace / "actually-denied.txt")),
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_tool_name"] == "read_file"
    assert attempt["permission_target"] == "workspace:actually-denied.txt"
    assert attempt["permission_target_unknown_reason"] is None


def test_url_match_uses_full_target_before_host_sanitization(tmp_path):
    target = "https://example.org/actually-denied"
    events = [
        _planner(
            ("read_url_content", "Url", "https://example.org/never-denied"),
            ("read_url_content", "Url", target),
        ),
        _result(
            "ERROR",
            f'Encountered error in step execution: permission check failed for read_url "{target}": '
            f"user denied permission for read_url({target})",
        ),
    ]
    attempt = record(parse(review_plan(tmp_path, events), "read_url"))
    assert attempt["denied_tool_name"] == "read_url_content"
    assert attempt["permission_target"] == "url:example.org"
    assert attempt["permission_target_unknown_reason"] is None


@pytest.mark.parametrize("status", [None, 17, [], {}, "", " ", True, 1.5])
@pytest.mark.parametrize("event_index", [0, 1, 2], ids=["user-input", "planner", "result"])
def test_malformed_transcript_status_stays_typed_unknown(tmp_path, status, event_index):
    events = [
        _planner(("read_file", "Path", "actually-denied.txt"), ("read_file", "Path", "never-denied.txt")),
        _result("ERROR", _headless_read_denial("actually-denied.txt")),
    ]
    plan = review_plan(tmp_path, events)
    transcript = agy._transcript_path_from_plan(plan)
    recorded = [json.loads(line) for line in transcript.read_text().splitlines()]
    recorded[event_index]["status"] = status
    transcript.write_text("\n".join(json.dumps(event) for event in recorded))
    result = parse(plan)
    attempt = record(result)
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "transcript_corrupt"
    assert attempt["denied_tool_name"] is None
    assert attempt["evidence_complete"] is False
    bound = agy._invocation_transcript(plan)
    assert bound.unreadable_lines == 0
    assert bound.malformed_status_lines == 1
    details = json.loads(result.stderr_excerpt.split("\n", 1)[1])
    assert details["transcript_unreadable_lines"] == 0
    assert details["transcript_malformed_status_lines"] == 1


def test_malformed_status_and_unreadable_lines_are_counted_separately(tmp_path):
    plan = review_plan(tmp_path, [_planner(("read_file", "Path", "evidence.txt")), _result(None, "Bad status.")])
    transcript = agy._transcript_path_from_plan(plan)
    with transcript.open("ab") as handle:
        handle.write(b"\n{truncated\n17\n\xff\n")
    bound = agy._invocation_transcript(plan)
    assert bound.unreadable_lines == 3
    assert bound.malformed_status_lines == 1
    result = parse(plan)
    attempt = record(result)
    assert attempt["permission_target_unknown_reason"] == "transcript_corrupt"
    assert attempt["denied_tool_name"] is None
    assert attempt["evidence_complete"] is False
    details = json.loads(result.stderr_excerpt.split("\n", 1)[1])
    assert details["transcript_unreadable_lines"] == 3
    assert details["transcript_malformed_status_lines"] == 1


@pytest.mark.parametrize(
    "rule", ["user-configured deny", "hardcoded system protection boundary"], ids=["deny-rule", "hardcoded"]
)
def test_rule_matched_read_refusal_is_counted_but_never_the_trigger(tmp_path, rule):
    events = [
        _planner(("read_file", "Path", "settings.json")),
        _result("ERROR", _rule_denial("read_file", "settings.json", rule)),
    ]
    attempt = record(parse(review_plan(tmp_path, events)))
    assert attempt["denied_file_read_count"] == 1
    assert attempt["denied_tool_name"] is None
    assert attempt["permission_target"] == "unknown"
    assert attempt["permission_target_unknown_reason"] == "trigger_missing"


@pytest.mark.parametrize("kind", ["read_file", "mcp", "command"])
@pytest.mark.parametrize("profile", [None, _REVIEW_PROFILE])
def test_inline_inputs_hint_only_for_review_read_refusals(tmp_path, kind, profile):
    plan = review_plan(tmp_path, _git_metadata_chain(tmp_path), profile=profile)
    result = parse(plan, kind)
    details = json.loads(result.stderr_excerpt.split("\n", 1)[1])
    assert details["permission_kind"] == kind
    if kind == "read_file" and profile:
        assert details["driver_hint"] == agy.AGY_DRIVER_HINT_INLINE_REVIEW_INPUTS
    else:
        assert "driver_hint" not in details


def test_review_with_refused_commands_completes_and_never_runs_them(tmp_path):
    reply = "calc.py adds 1 to every mean.\nVERDICT: REQUEST_CHANGES"
    workspace = tmp_path / "repo" / ".worktrees" / "dispatch" / "agy" / "fixture"
    events = [
        _planner(("run_command", "CommandLine", "git log -1")),
        _result("ERROR", _rule_denial("unsandboxed", "git log -1")),
        _planner(("run_command", "CommandLine", "pytest -q")),
        _result("ERROR", _rule_denial("unsandboxed", "pytest -q")),
        _planner(("read_file", "Path", str(workspace / "calc.py"))),
        _result("DONE", _stamped("Showing lines 1-2 of 2\n1: def average(values):")),
        _planner(content=reply),
    ]
    result = agy.AgyAdapter().parse_response(
        stdout=reply, stderr="", returncode=0, output_file=None, plan=review_plan(tmp_path, events)
    )
    assert result.ok and result.response == reply and result.failure_code is None
    assert result.agy_attempt.denied_command_count == 2
    assert result.agy_attempt.executed_command_count == 0
    assert result.agy_attempt.permission_kind is None
