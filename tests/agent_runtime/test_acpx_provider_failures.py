"""Structural provider failure and installed Codex regressions for #9273."""

import json
import subprocess
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters import acpx
from scripts.agent_runtime.env_sanitize import build_agent_env
from scripts.ai_agent_bridge import _acp_compat, _cli

ERROR_BODY = json.dumps(
    {
        "type": "error",
        "status": 400,
        "error": {
            "type": "invalid_request_error",
            "message": "The 'gpt-6.1-sol' model is not supported when using Codex with a ChatGPT account.",
        },
    }
)


def stream(*updates, error=None, result_meta=None):
    events = [{"jsonrpc": "2.0", "id": 2, "method": "session/prompt", "params": {}}]
    events.extend(
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": "fixture",
                "update": update,
            },
        }
        for update in updates
    )
    events.append(
        {
            "jsonrpc": "2.0",
            "id": 2,
            **(
                {"error": error}
                if error
                else {
                    "result": {
                        "stopReason": "end_turn",
                        **({"_meta": result_meta} if result_meta is not None else {}),
                    }
                }
            ),
        }
    )
    return "\n".join(json.dumps(event) for event in events)


def parse(stdout):
    return acpx.AcpxAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None)


def text_chunk(text):
    return {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": text}}


@pytest.mark.parametrize(
    "meta",
    [
        # Captured live from codex-acp 1.13.1 / bundled Codex 0.156.1.
        {"codex": {"threadStatus": {"type": "systemError"}}},
        {"codex": {"error": {"message": ERROR_BODY, "willRetry": False}}},
        # The same adapter's negotiated typed sessionFailure extension.
        {
            "jetbrains": {
                "air": {
                    "version": 1,
                    "sessionFailure": {
                        "category": "provider_error",
                        "severity": "error",
                        "title": ERROR_BODY,
                    },
                }
            }
        },
    ],
)
def test_provider_error_wrappers_fail_even_with_success_terminal(meta):
    result = parse(stream({"sessionUpdate": "session_info_update", "_meta": meta}, text_chunk(ERROR_BODY)))
    assert not result.ok
    assert result.failure_code == "provider_error"
    assert result.response == ""
    receipt = SimpleNamespace(ok=False, transport_outcome="error", usage_record={"failure_code": result.failure_code})
    assert _acp_compat._failure_metadata(result=receipt) == {
        "phase": "provider",
        "code": "provider_error",
        "retryable": False,
    }
    assert (
        runner._privacy_safe_failure_code(
            outcome="error",
            rate_limited=False,
            stalled=False,
            returncode=0,
            explicit_code=result.failure_code,
        )
        == "provider_error"
    )


@pytest.mark.parametrize(
    "answer",
    [
        ERROR_BODY,
        f"Example error:\n{ERROR_BODY}",
        "The 'gpt-6.1-sol' model is not supported when using Codex with a ChatGPT account.",
    ],
)
def test_answer_quoting_identical_error_is_success(answer):
    result = parse(stream(text_chunk(answer)))
    assert result.ok
    assert result.response == answer


@pytest.mark.parametrize(
    "meta",
    [
        {},
        {"codex": {"threadStatus": {"type": "active"}}},
        {"codex": {"error": {"willRetry": True, "message": ERROR_BODY}}},
        {"jetbrains": {"air": {"sessionFailure": {"severity": "warning"}}}},
    ],
)
def test_nonterminal_metadata_does_not_fail_success(meta):
    assert parse(stream({"sessionUpdate": "session_info_update", "_meta": meta}, text_chunk("answer"))).ok


@pytest.mark.parametrize("severity,expected_ok", [("error", False), ("warning", True)])
def test_terminal_result_session_failure_metadata(severity, expected_ok):
    # codex-acp terminalFailurePromptResponse carries this in the result,
    # without necessarily emitting a session_info_update first.
    result = parse(
        stream(
            text_chunk("answer"),
            result_meta={
                "jetbrains": {
                    "air": {
                        "version": 1,
                        "sessionFailure": {"severity": severity, "category": "provider_error"},
                    }
                }
            },
        )
    )
    assert result.ok is expected_ok
    assert result.failure_code == (None if expected_ok else "provider_error")


@pytest.mark.parametrize(
    "data",
    [
        {"codexErrorInfo": {"httpConnectionFailed": {"httpStatusCode": 400}}},
        {"errorKind": "invalid_request"},  # claude-agent-acp
        {"errorName": "APIError"},  # opencode ACP
        {},  # Grok/text/native wrappers: ordinary JSON-RPC error
    ],
)
@pytest.mark.parametrize(
    "adapter_type",
    [
        acpx.AcpxAdapter,
        acpx.AcpxClaudeShadowAdapter,
        acpx.AcpxGrokShadowAdapter,
        acpx.AcpxAgyShadowAdapter,
        acpx.AcpxGlmShadowAdapter,
        acpx.AcpxGemmaShadowAdapter,
        acpx.AcpxDeepSeekShadowAdapter,
        acpx.AcpxCursorShadowAdapter,
        acpx.AcpxPoolShadowAdapter,
    ],
)
def test_shared_parser_closes_provider_rpc_errors_for_all_participant_paths(adapter_type, data):
    result = adapter_type().parse_response(
        stdout=stream(error={"code": -32603, "message": ERROR_BODY, "data": data}),
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert not result.ok
    assert result.failure_code


def test_codex_effort_high_refusal_names_supported_default():
    with pytest.raises(
        runner.InterAgentTransportError, match=r"supported effort values: default \(omit --effort\)"
    ) as exc:
        runner.resolve_inter_agent_route("codex", effort="high")
    assert _acp_compat._failure_metadata(error=exc.value) == {
        "phase": "admission",
        "code": "route_effort_conflict",
        "retryable": False,
    }


def test_installed_codex_resolution_and_version(monkeypatch):
    monkeypatch.setattr(acpx, "resolve_agent_binary", lambda name: "/installed/current-codex")
    calls = []

    def probe(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="codex-cli 0.159.2\n")

    monkeypatch.setattr(acpx.subprocess, "run", probe)
    assert acpx._require_codex_cli() == ("/installed/current-codex", "0.159.2")
    assert calls == [["/installed/current-codex", "--version"]]


@pytest.mark.parametrize("failure", ["missing", "invalid", "nonzero", "timeout", "oserror"])
def test_installed_codex_probe_fails_closed(monkeypatch, failure):
    monkeypatch.setattr(acpx, "resolve_agent_binary", lambda name: None if failure == "missing" else "/installed/codex")

    def probe(*args, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired("codex", 5)
        if failure == "oserror":
            raise OSError("unavailable")
        return SimpleNamespace(returncode=1 if failure == "nonzero" else 0, stdout="invalid")

    monkeypatch.setattr(acpx.subprocess, "run", probe)
    with pytest.raises(acpx.AcpxShadowRefusalError):
        acpx._require_codex_cli()


def test_codex_path_survives_sanitizer_only_for_codex_seat(monkeypatch):
    monkeypatch.setenv("CODEX_PATH", "/old/bundled-codex")
    env = build_agent_env(provider="acpx-codex-shadow", overrides={"CODEX_PATH": "/installed/current-codex"})
    assert env["CODEX_PATH"] == "/installed/current-codex"
    assert "CODEX_PATH" not in build_agent_env(provider="acpx-grok-shadow")


def test_structural_failure_makes_ask_exit_nonzero(monkeypatch):
    parsed = parse(
        stream(
            {
                "sessionUpdate": "session_info_update",
                "_meta": {
                    "codex": {"threadStatus": {"type": "systemError"}},
                },
            },
            text_chunk(ERROR_BODY),
        )
    )
    monkeypatch.setattr(_acp_compat, "run_compat_ask", lambda *args, **kwargs: parsed)
    args = _cli._build_parser().parse_args(["ask-codex", "question", "--task-id", "fixture", "--from", "codex"])
    with pytest.raises(SystemExit) as exc:
        _cli._handle_ask_codex(args)
    assert exc.value.code != 0


def test_provider_failure_terminalizes_and_replays_through_real_store(tmp_path, monkeypatch):
    from scripts.fleet_comms.authority import AuthorityService

    parsed = parse(
        stream(
            {
                "sessionUpdate": "session_info_update",
                "_meta": {
                    "codex": {"threadStatus": {"type": "systemError"}},
                },
            },
            text_chunk(ERROR_BODY),
        )
    )
    result = SimpleNamespace(
        ok=parsed.ok,
        agent="codex",
        model="gpt-6.1-sol",
        response=parsed.response,
        stderr_excerpt=parsed.stderr_excerpt,
        duration_s=0.5,
        returncode=0,
        effort="not-exposed",
        transport_outcome="error",
        rate_limited=False,
        transport_metadata=None,
        usage_record={"failure_code": parsed.failure_code},
    )
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "fleet-comms"))
    calls = []

    def invoke(*args, **kwargs):
        calls.append(kwargs)
        return result

    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)
    monkeypatch.setattr(acpx, "probe_participant_reachability", lambda participant: None)

    @contextmanager
    def execution_cwd(*args, **kwargs):
        yield tmp_path

    monkeypatch.setattr("scripts.ai_agent_bridge._acp_execution.acp_execution_cwd", execution_cwd)
    for _ in range(2):
        returned = _acp_compat._run_compat_ask_impl(
            "codex",
            "question",
            task_id="provider-error-9273",
            source="codex",
        )
        assert not returned.ok
        assert returned.transport_outcome == "error"
    assert len(calls) == 1  # replay must not make another provider call
    with AuthorityService() as service:
        rows = service.store.connection.execute("SELECT job_id FROM authority_jobs").fetchall()
        assert len(rows) == 1
        job = service.get_job(rows[0]["job_id"])
        assert job.state == "failed"
        assert job.lease_owner is None
        assert job.lease_expires_at is None
        receipt = json.loads(service.read_job_result(job.job_id))
        assert receipt["failure_code"] == "provider_error"
        assert receipt["returncode"] == 0
        assert receipt["substitution_decision"]["substitute"] is False
        finished = service.store.connection.execute(
            "SELECT metadata_json FROM authority_job_events WHERE job_id = ? AND event_type = 'finished'",
            (job.job_id,),
        ).fetchall()
        assert len(finished) == 1
        assert json.loads(finished[0]["metadata_json"])["failure"] == {
            "phase": "provider",
            "code": "provider_error",
            "retryable": False,
        }
