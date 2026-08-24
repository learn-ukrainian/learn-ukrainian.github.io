"""Regression coverage for the uniform ask model/effort/provenance contract."""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from scripts.ai_agent_bridge import _acp_compat, _cli
from scripts.ai_agent_bridge._ask_contract import (
    EFFORT_CHOICES,
    failed_response_provenance,
    resolve_model_selection,
    response_provenance,
    unsupported_effort_note,
)

ASK_SEATS = (
    ("ask-claude", "_handle_ask_claude", "claude"),
    ("ask-codex", "_handle_ask_codex", "codex"),
    ("ask-agy", "_handle_ask_agy", "agy"),
    ("ask-grok", "_handle_ask_grok_build", "grok"),
    ("ask-glm", "_handle_ask_glm", "glm"),
    ("ask-gemma", "_handle_ask_gemma", "gemma"),
    ("ask-kimi", "_handle_ask_kimi", "kimi"),
    ("ask-cursor", "_handle_ask_cursor", "cursor"),
    ("ask-hermes", "_handle_ask_hermes", "hermes"),
    ("ask-deepseek", "_handle_ask_deepseek", "deepseek"),
    ("ask-pool", "_handle_ask_pool", "pool"),
)

RETIRED_ASK_SEATS = (
    ("ask-opencode", "_handle_ask_opencode", "opencode"),
)


@pytest.mark.parametrize(("command", "handler_name", "target"), ASK_SEATS)
def test_effort_and_to_model_reach_every_enabled_acp_route(
    command: str, handler_name: str, target: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every enabled compatibility parser forwards controls to the ACP shim."""
    captured: dict[str, object] = {}

    def fake_compat(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(_acp_compat, "run_compat_ask", fake_compat)
    args = _cli._build_parser().parse_args(
        [
            command,
            "question",
            "--task-id",
            "contract-seat",
            "--from",
            "claude",
            "--to-model",
            "requested-model",
            "--effort",
            "xhigh",
        ]
    )

    getattr(_cli, handler_name)(args)

    forwarded = tuple(captured.get("args", ())) + tuple(captured.values())
    assert captured["args"][0] == target
    assert "requested-model" in forwarded
    assert captured["effort"] == "xhigh"


def test_terminal_failure_replays_without_invoking_provider_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "fleet-comms"))
    invoke = Mock(side_effect=RuntimeError("protected primary refused"))
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)
    # Hermetic from host PATH state: the reachability probe is stubbed, and
    # the replay path must never call it — only the real invocation may.
    probe = Mock(return_value=None)
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.acpx.probe_participant_reachability", probe
    )

    with pytest.raises(RuntimeError, match="protected primary refused"):
        _acp_compat.run_compat_ask(
            "agy",
            "same prompt",
            task_id="failure-replay",
            source="codex",
            model="gemini-3.6-flash-high",
            effort="high",
        )

    replay = _acp_compat.run_compat_ask(
        "agy",
        "same prompt",
        task_id="failure-replay",
        source="codex",
        model="gemini-3.6-flash-high",
        effort="high",
    )

    assert replay.ok is False
    assert replay.transport_outcome == "error"
    assert replay.usage_record == {
        "from_model": "gemini-3.6-flash-high",
        "model_requested": "gemini-3.6-flash-high",
        "effort_requested": "high",
        "effort_applied": None,
        "harness": "acp",
        "replayed": True,
        "transport": "acp",
    }
    assert invoke.call_count == 1
    # The probe fires once — for the call that actually invoked the provider —
    # and never for the terminal replay.
    assert probe.call_count == 1


def test_terminalization_conflict_preserves_completed_provider_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A bookkeeping collision must not hide the completed provider response."""
    from scripts.fleet_comms.authority import AuthorityStaleLeaseError

    claim_state = {"claimed": False}

    class TerminalConflictAuthority:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_request(self, **_kwargs):
            return SimpleNamespace(job_id="job-6367", state="queued")

        def claim_job(self, *_args, **_kwargs):
            claim_state["claimed"] = True
            return SimpleNamespace(fence_token=1)

        def finish_job(self, *_args, **_kwargs):
            raise AuthorityStaleLeaseError("terminalization_conflict")

    def probe_after_claim(_participant: str) -> str | None:
        # Hermetic from host PATH state, and order-sensitive: the probe is
        # legitimate only once a job was claimed — i.e. only when a real
        # provider invocation is about to occur, never at admission.
        if not claim_state["claimed"]:
            return "probe fired before any provider invocation was due"
        return None

    @contextmanager
    def execution_cwd(*_args, **_kwargs):
        yield tmp_path

    provider_result = SimpleNamespace(
        ok=True,
        agent="agy",
        model="gemini-3.6-flash-high",
        response="completed provider response",
        stderr_excerpt=None,
        duration_s=1.0,
        returncode=0,
        effort="high",
        transport_metadata=None,
        transport_outcome="ok",
    )
    invoke = Mock(return_value=provider_result)
    output_path = tmp_path / "response.txt"
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", TerminalConflictAuthority)
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)
    monkeypatch.setattr("scripts.ai_agent_bridge._acp_execution.acp_execution_cwd", execution_cwd)
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.acpx.probe_participant_reachability",
        probe_after_claim,
    )

    with pytest.raises(RuntimeError, match="terminal bookkeeping failed after provider response"):
        _acp_compat._run_compat_ask_impl(
            "agy",
            "question",
            task_id="terminalization-conflict",
            model="gemini-3.6-flash-high",
            effort="high",
            output_path=str(output_path),
        )

    captured = capsys.readouterr()
    assert captured.out == "completed provider response\n"
    assert "terminalization_conflict" in captured.err
    assert output_path.read_text(encoding="utf-8") == "completed provider response"
    assert invoke.call_count == 1


def test_claim_race_to_terminal_replays_without_invoking_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A terminal race after enqueue must replay instead of spending a provider call."""
    from scripts.fleet_comms.authority import AuthorityServiceError

    replay_result = SimpleNamespace(
        ok=True,
        agent="agy",
        model="gemini-3.6-flash-high",
        response="durably completed response",
        stderr_excerpt=None,
        duration_s=1.0,
        returncode=0,
        effort="high",
        transport_metadata=None,
        transport_outcome="ok",
    )

    class ConcurrentTerminalAuthority:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_request(self, **_kwargs):
            return SimpleNamespace(job_id="job-race", state="queued")

        def claim_job(self, *_args, **_kwargs):
            raise AuthorityServiceError("job_not_claimable")

        def get_job(self, _job_id):
            return SimpleNamespace(job_id="job-race", state="complete")

        def read_job_result(self, _job_id):
            return _acp_compat._result_receipt(replay_result)

    invoke = Mock(side_effect=AssertionError("terminal job reinvoked provider"))
    # Hermetic from host PATH state, and order-sensitive: a claim-race replay
    # must never reach the reachability probe at all.
    probe = Mock(return_value="probe fired on a terminal-replay path")
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", ConcurrentTerminalAuthority)
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.acpx.probe_participant_reachability", probe
    )

    result = _acp_compat._run_compat_ask_impl(
        "agy",
        "question",
        task_id="terminal-claim-race",
        model="gemini-3.6-flash-high",
        effort="high",
    )

    assert result.response == "durably completed response"
    assert result.usage_record["replayed"] is True
    assert result.usage_record["transport"] == "acp"
    assert result.usage_record["from_model"] == "gemini-3.6-flash-high"
    assert result.usage_record["harness"] == "acp"
    assert invoke.call_count == 0
    assert probe.call_count == 0


def test_cli_returns_nonzero_for_replayed_or_live_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        _acp_compat,
        "run_compat_ask",
        lambda *args, **kwargs: SimpleNamespace(ok=False, stderr_excerpt="replayed failure"),
    )
    args = _cli._build_parser().parse_args(
        ["ask-agy", "question", "--task-id", "failed-seat", "--from", "codex"]
    )

    with pytest.raises(SystemExit, match="replayed failure"):
        _cli._handle_ask_agy(args)


# Raw DSML tool-call markup leaked by the toolless deepseek seat on the first
# live firing of the #6878 gate (#6886): the model attempted tool calls it
# does not have instead of delivering a verdict. Kept as a gate fixture.
DSML_TOOLCALL_GARBLE = (
    "<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>function<｜tool▁sep｜>read_file\n"
    '```json\n{"path": "scripts/fleet_comms/authority.py"}\n```'
    "<｜tool▁call▁end｜><｜tool▁calls▁end｜>"
)


@pytest.mark.parametrize(
    "response",
    [
        # Documented on #6805: literal garbage with transport outcome=ok.
        "DXVECTOR",
        # The #6886 live firing: raw DSML tool-call markup, no verdict.
        DSML_TOOLCALL_GARBLE,
        # Model preamble / harness confusion, no verdict ever delivered.
        "Deep breath — emit the tool call now… Wait, formatting requires blocks.",
        "I'll verify key claims against the diff before writing anything.",
        # A verdict with zero grounding is not a review outcome either.
        "VERDICT: APPROVED. Looks fine to me.",
        "",
    ],
)
def test_review_outcome_failure_rejects_non_evidentiary_replies(response: str) -> None:
    assert _acp_compat.review_outcome_failure(response) is not None


@pytest.mark.parametrize(
    "response",
    [
        "VERDICT: REQUEST_CHANGES\n- Finding: scripts/foo.py:42 swallows the error.",
        "verdict: approved\nEvidence: reviewed the diff at head 0123abc, 3 files.",
        "Verdict: PASS\nFindings: none. Checked scripts/ai_agent_bridge/_cli.py and #6805.",
    ],
)
def test_review_outcome_failure_accepts_grounded_verdicts(response: str) -> None:
    assert _acp_compat.review_outcome_failure(response) is None


def _make_ok_result(response: str) -> object:
    from agent_runtime.result import Result

    return Result(
        ok=True,
        agent="glm",
        model="glm-5.3",
        mode="read-only",
        response=response,
        stderr_excerpt=None,
        duration_s=1.0,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        effort="high",
        transport_outcome="ok",
    )


def _stub_live_invocation(
    monkeypatch: pytest.MonkeyPatch, authority: object, result: object
) -> Mock:
    """Wire the recording authority plus a one-shot provider result."""

    @contextmanager
    def execution_cwd(*_args, **_kwargs):
        yield Path.cwd()

    invoke = Mock(return_value=result)
    monkeypatch.setattr(
        "scripts.fleet_comms.authority.AuthorityService", lambda: authority
    )
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._acp_execution.acp_execution_cwd", execution_cwd
    )
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.acpx.probe_participant_reachability",
        Mock(return_value=None),
    )
    return invoke


def test_review_ask_with_garbled_reply_terminalizes_failed_non_evidentiary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """#6805: transport-ok garbage on a review ask must never terminalize as
    a silent success — the job fails with the non_evidentiary code."""
    authority = _RecordingAuthority()
    _stub_live_invocation(monkeypatch, authority, _make_ok_result("DXVECTOR"))

    result = _acp_compat._run_compat_ask_impl(
        "glm", "review this diff", task_id="garbled-review", review=True
    )

    assert result.ok is False
    assert result.transport_outcome == "non_evidentiary"
    assert result.response == "DXVECTOR"  # body preserved for forensics
    assert "no VERDICT token" in (result.stderr_excerpt or "")
    assert len(authority.finished) == 1
    assert authority.finished[0]["state"] == "failed"
    assert authority.finished[0]["failure"] == {
        "phase": "postprocess",
        "code": "non_evidentiary",
        "retryable": False,
    }
    assert "outcome=non_evidentiary" in capsys.readouterr().err


def test_review_ask_with_grounded_verdict_stays_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _RecordingAuthority()
    _stub_live_invocation(
        monkeypatch,
        authority,
        _make_ok_result("VERDICT: APPROVED\nEvidence: diff at head 0123abc, 2 files."),
    )

    result = _acp_compat._run_compat_ask_impl(
        "glm", "review this diff", task_id="grounded-review", review=True
    )

    assert result.ok is True
    assert authority.finished[0]["state"] == "complete"
    assert authority.finished[0]["failure"] is None


def test_non_review_ask_is_not_outcome_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plain queries keep transport semantics — a one-token answer is fine."""
    authority = _RecordingAuthority()
    _stub_live_invocation(monkeypatch, authority, _make_ok_result("OK glm-5.3"))

    result = _acp_compat._run_compat_ask_impl("glm", "ping", task_id="plain-query")

    assert result.ok is True
    assert authority.finished[0]["state"] == "complete"


def test_non_evidentiary_review_ask_terminalizes_through_real_authority_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#6886: end-to-end seam the #6878 tests missed — the gate and the
    failure metadata were each validated against a recording stub, so the real
    authority failure-code allowlist rejecting ``non_evidentiary`` crashed
    finish_job AFTER the provider replied and stranded the claimed lease.
    Run the gate through the real store: the job must terminalize
    failed:non_evidentiary with the lease released and no exception."""
    from scripts.fleet_comms.authority import AuthorityService

    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "fleet-comms"))
    invoke = Mock(return_value=_make_ok_result(DSML_TOOLCALL_GARBLE))
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.acpx.probe_participant_reachability",
        Mock(return_value=None),
    )

    @contextmanager
    def execution_cwd(*_args, **_kwargs):
        yield tmp_path

    monkeypatch.setattr(
        "scripts.ai_agent_bridge._acp_execution.acp_execution_cwd", execution_cwd
    )

    result = _acp_compat._run_compat_ask_impl(
        "deepseek", "review this diff", task_id="review-6886-seam", review=True
    )

    assert result.ok is False
    assert result.transport_outcome == "non_evidentiary"

    with AuthorityService() as service:
        rows = service.store.connection.execute(
            "SELECT job_id FROM authority_jobs"
        ).fetchall()
        assert len(rows) == 1
        job = service.get_job(str(rows[0]["job_id"]))
        events = service.store.connection.execute(
            """SELECT event_type, metadata_json FROM authority_job_events
               WHERE job_id = ? ORDER BY created_at""",
            (job.job_id,),
        ).fetchall()

    # Clean terminalization — the #6886 crash left the job mid-lease instead.
    assert job.state == "failed"
    assert job.lease_owner is None
    assert job.lease_expires_at is None
    finished = [event for event in events if event["event_type"] == "finished"]
    assert len(finished) == 1
    metadata = json.loads(str(finished[0]["metadata_json"]))
    assert metadata["failure"] == {
        "phase": "postprocess",
        "code": "non_evidentiary",
        "retryable": False,
    }


@pytest.mark.parametrize(
    ("command", "handler_name", "extra_argv"),
    [
        # Drivers pass --type review (#6805 evidence); ask-glm has no --review.
        ("ask-glm", "_handle_ask_glm", ["--type", "review"]),
        ("ask-claude", "_handle_ask_claude", ["--review"]),
    ],
)
def test_review_intent_never_reaches_the_toolless_acp_shim(
    command: str, handler_name: str, extra_argv: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """#7155: review intent must reach a reviewer WITH tools, never ACP.

    ACP's `--deny-all --no-fs --no-terminal` transport cannot run `gh`
    (Terra ABSTAIN on #7155). Both spellings of review intent — `--type
    review` and `--review` — must route to headless dispatch instead of
    `run_compat_ask`.
    """

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("run_compat_ask must not be called for review intent (#7155)")

    monkeypatch.setattr(_acp_compat, "run_compat_ask", fail_if_called)

    captured: dict[str, object] = {}
    from scripts.ai_agent_bridge import _dispatch_wrappers

    def fake_dispatch(agent, content, **kwargs):
        captured["agent"] = agent
        captured["content"] = content
        captured.update(kwargs)
        return {"ok": True, "status": "done", "response": "VERDICT: APPROVED\nEvidence: reviewed diff."}

    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", fake_dispatch)

    args = _cli._build_parser().parse_args(
        [command, "question", "--task-id", "review-intent", "--from", "kimi", *extra_argv]
    )

    getattr(_cli, handler_name)(args)

    assert captured["agent"] == command.removeprefix("ask-")


@pytest.mark.parametrize(("command", "handler_name", "target"), RETIRED_ASK_SEATS)
def test_ask_target_without_an_enabled_acp_route_fails_closed(
    command: str, handler_name: str, target: str
) -> None:
    args = _cli._build_parser().parse_args(
        [command, "question", "--task-id", "retired-seat"]
    )
    with pytest.raises(SystemExit, match=f"{target!r} has no enabled ACP route"):
        getattr(_cli, handler_name)(args)


class _RecordingAuthority:
    """Minimal in-memory authority: enqueue + claim succeed, finish_job records."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.finished: list[dict[str, object]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def enqueue_request(self, **_kwargs):
        return SimpleNamespace(job_id="job-dead-seat", state="queued")

    def claim_job(self, *_args, **_kwargs):
        return SimpleNamespace(fence_token=1)

    def finish_job(self, _job_id, **kwargs):
        self.finished.append(kwargs)


def test_compat_ask_fails_before_provider_invocation_when_provider_binary_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#6805: a dead seat fails before the provider is invoked, with the
    actionable remediation and documented route — not mid-review at spawn.
    The authority job is enqueued and claimed first: terminal-replay paths
    must stay reachable even when the provider CLI is absent."""
    from scripts.agent_runtime import binary_resolve as binary_resolve_module

    invoke = Mock(side_effect=AssertionError("dead seat invoked the provider"))
    monkeypatch.setattr(binary_resolve_module, "_which", lambda _name, *_a, **_k: None)
    monkeypatch.setattr(
        "scripts.fleet_comms.authority.AuthorityService", _RecordingAuthority
    )
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)

    with pytest.raises(ValueError) as exc_info:
        _acp_compat._run_compat_ask_impl("hermes", "question", task_id="dead-seat")

    message = str(exc_info.value)
    # The DeepSeek participant rides the opencode transport since the Hermes
    # removal (#6805): the admission refusal names the binary that is actually
    # required now, with the opencode remediation — never the dead hermes path.
    assert "opencode binary not found on PATH" in message
    assert "hermes binary not found on PATH" not in message
    assert "docs/runbooks/agent-seat-onboarding.md" in message
    assert invoke.call_count == 0


def test_ask_hermes_cli_surfaces_remediation_when_binary_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#6805: the CLI exits nonzero with the remediation the caller reroutes on."""
    from scripts.agent_runtime import binary_resolve as binary_resolve_module

    monkeypatch.setattr(binary_resolve_module, "_which", lambda _name, *_a, **_k: None)
    monkeypatch.setattr(
        "scripts.fleet_comms.authority.AuthorityService", _RecordingAuthority
    )
    args = _cli._build_parser().parse_args(
        ["ask-hermes", "question", "--task-id", "dead-seat", "--from", "codex"]
    )

    with pytest.raises(SystemExit) as exc_info:
        _cli._handle_ask_hermes(args)

    message = str(exc_info.value)
    assert "opencode binary not found on PATH" in message
    assert "docs/runbooks/agent-seat-onboarding.md" in message


@pytest.mark.parametrize("effort", EFFORT_CHOICES)
def test_every_contract_effort_value_is_accepted(effort: str) -> None:
    args = _cli._build_parser().parse_args(
        ["ask-codex", "question", "--task-id", "effort-values", "--effort", effort]
    )
    assert args.effort == effort


def test_to_model_wins_only_when_legacy_alias_agrees() -> None:
    assert (
        resolve_model_selection(
            lane="ask-cursor",
            to_model="requested",
            model="requested",
            default="default",
        )
        == "requested"
    )
    with pytest.raises(ValueError, match="conflicts with deprecated --model"):
        resolve_model_selection(
            lane="ask-cursor",
            to_model="requested",
            model="legacy",
            default="default",
        )


def test_unsupported_effort_emits_note_and_stamps_null(capsys: pytest.CaptureFixture[str]) -> None:
    applied, reason = unsupported_effort_note(
        lane="cursor", effort="xhigh", reason="Cursor Agent has no per-invocation effort flag"
    )
    assert applied is None
    assert reason == "Cursor Agent has no per-invocation effort flag"
    assert "NOTE: cursor cannot apply requested effort=xhigh" in capsys.readouterr().out


@pytest.mark.parametrize(
    "harness",
    [seat[0].removeprefix("ask-") for seat in (*ASK_SEATS, *RETIRED_ASK_SEATS)],
)
def test_every_response_provenance_shape_has_required_fields(harness: str) -> None:
    data, from_model = response_provenance(
        {"data": json.dumps({"to_model": "requested", "effort": "xhigh"})},
        actual_model="actual",
        harness=harness,
        effort_applied="xhigh",
    )
    assert from_model == "actual"
    assert json.loads(data) == {
        "effort_applied": "xhigh",
        "effort_requested": "xhigh",
        "from_model": "actual",
        "harness": harness,
        "model_requested": "requested",
    }


def test_failed_response_provenance_preserves_request_and_marks_unapplied_effort() -> None:
    data, from_model = failed_response_provenance(
        {"data": json.dumps({"to_model": "requested", "effort": "xhigh"})},
        bridge_model="agy-bridge-error",
        harness="agy",
    )

    assert from_model == "agy-bridge-error"
    assert json.loads(data) == {
        "effort_applied": None,
        "effort_reason": "bridge execution failed before the requested effort could be applied",
        "effort_requested": "xhigh",
        "from_model": "agy-bridge-error",
        "harness": "agy",
        "model_requested": "requested",
    }


def test_acp_result_receipt_and_replay_preserve_response_provenance() -> None:
    result = SimpleNamespace(
        ok=True,
        agent="agy",
        model="gemini-3.6-flash-high",
        response="answer",
        stderr_excerpt=None,
        duration_s=1.0,
        returncode=0,
        effort="high",
        transport_metadata=None,
        transport_outcome="ok",
    )

    receipt = _acp_compat._result_receipt(
        result, model_requested="gemini-3.6-flash-high", effort_requested="high"
    )
    payload = json.loads(receipt)
    assert {key: payload[key] for key in ("from_model", "model_requested", "effort_requested", "effort_applied", "harness")} == {
        "from_model": "gemini-3.6-flash-high",
        "model_requested": "gemini-3.6-flash-high",
        "effort_requested": "high",
        "effort_applied": "high",
        "harness": "acp",
    }
    replay = _acp_compat._replay_result(receipt)
    assert replay.usage_record == {
        "from_model": "gemini-3.6-flash-high",
        "model_requested": "gemini-3.6-flash-high",
        "effort_requested": "high",
        "effort_applied": "high",
        "harness": "acp",
        "replayed": True,
        "transport": "acp",
    }


def test_acp_replay_preserves_explicit_none_effort_applied() -> None:
    result = SimpleNamespace(
        ok=True,
        agent="agy",
        model="gemini-3.6-flash-high",
        response="answer",
        stderr_excerpt=None,
        duration_s=1.0,
        returncode=0,
        effort="high",
        transport_metadata=None,
        transport_outcome="ok",
    )
    payload = json.loads(_acp_compat._result_receipt(result))
    payload["effort_applied"] = None

    replay = _acp_compat._replay_result(json.dumps(payload).encode("utf-8"))

    assert replay.usage_record["effort_applied"] is None


def test_acp_failed_result_receipt_serializes_none_effort_as_unapplied() -> None:
    result = SimpleNamespace(
        ok=False,
        agent="agy",
        model="gemini-3.6-flash-high",
        response="",
        stderr_excerpt="provider failed",
        duration_s=1.0,
        returncode=1,
        effort=None,
        transport_metadata=None,
        transport_outcome="error",
    )

    payload = json.loads(_acp_compat._result_receipt(result))

    assert payload["effort"] == "unknown"
    assert payload["effort_applied"] is None


def test_native_ask_tool_contract_present_in_ask_mode_and_absent_otherwise() -> None:
    """Native grok ask prompt includes NATIVE_ASK_TOOL_CONTRACT when not review-provisioned; absent on review-provisioned, reverted builders, and full drivers (#5893)."""
    from scripts.ai_agent_bridge._ask_contract import NATIVE_ASK_TOOL_CONTRACT
    from scripts.ai_agent_bridge._grok_build import _build_grok_build_prompt
    from scripts.ai_agent_bridge._prompts import (
        _build_full_execution_prompt,
        build_agy_prompt,
        build_claude_prompt,
        build_codex_prompt,
    )

    dummy_msg = {"from": "user", "task_id": "test-1", "type": "query", "content": "Hello", "data": None}

    # Present ONLY on native grok ask path without a provisioned review worktree
    assert NATIVE_ASK_TOOL_CONTRACT in _build_grok_build_prompt(dummy_msg, review_worktree_provisioned=False)

    # ABSENT on grok review-provisioned path
    assert NATIVE_ASK_TOOL_CONTRACT not in _build_grok_build_prompt(
        dummy_msg, review=True, review_worktree_provisioned=True
    )

    # ABSENT in the three reverted builders
    assert NATIVE_ASK_TOOL_CONTRACT not in build_agy_prompt(dummy_msg)
    assert NATIVE_ASK_TOOL_CONTRACT not in build_claude_prompt(dummy_msg)
    assert NATIVE_ASK_TOOL_CONTRACT not in build_codex_prompt(dummy_msg)

    # ABSENT in full driver prompt
    full_driver_prompt = _build_full_execution_prompt(dummy_msg, delimiters=None)
    assert NATIVE_ASK_TOOL_CONTRACT not in full_driver_prompt


# --- #6877: per-seat ask timeout profiles -------------------------------


def test_ask_hard_timeout_profile_table_is_exact() -> None:
    """Mutation-check (#M-16): every compat seat resolves its exact profile.

    Kimi is the only max-effort-only seat on the compat routes (K3; long
    deliberation before first output is designed behavior), so it gets 1800s.
    Every other seat — claude/grok/agy/glm/deepseek are pinned at "high", not
    max-only — keeps the generic 300s default. Exact equality here means a
    silent profile-table edit fails this test.
    """
    assert _acp_compat.ASK_HARD_TIMEOUT_DEFAULT_S == 300
    assert _acp_compat.ASK_HARD_TIMEOUT_PROFILES == {"kimi": 1800}
    for target in _acp_compat._TARGETS:
        expected = 1800 if target == "kimi" else 300
        assert _acp_compat.ask_hard_timeout(target) == expected, target
    assert _acp_compat.ask_hard_timeout("no-such-seat") == 300


def test_compat_ask_resolves_seat_timeout_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """hard_timeout=None resolves the seat profile before the provider call."""
    authority = _RecordingAuthority()
    invoke = _stub_live_invocation(monkeypatch, authority, _make_ok_result("OK"))

    _acp_compat._run_compat_ask_impl("kimi", "review this diff", task_id="kimi-profile")
    assert invoke.call_args.kwargs["hard_timeout"] == 1800

    _acp_compat._run_compat_ask_impl("glm", "ping", task_id="glm-profile")
    assert invoke.call_args.kwargs["hard_timeout"] == 300


def test_compat_ask_explicit_timeout_beats_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicit hard_timeout (--no-timeout's 86400) bypasses the profile."""
    authority = _RecordingAuthority()
    invoke = _stub_live_invocation(monkeypatch, authority, _make_ok_result("OK"))

    _acp_compat._run_compat_ask_impl(
        "kimi", "review this diff", task_id="kimi-no-timeout", hard_timeout=86400
    )
    assert invoke.call_args.kwargs["hard_timeout"] == 86400


@pytest.mark.parametrize(
    ("command", "handler_name", "expected"),
    [
        ("ask-kimi", "_handle_ask_kimi", None),  # None → compat resolves 1800s
        ("ask-claude", "_handle_ask_claude", None),  # None → compat resolves 300s
    ],
)
def test_cli_defers_timeout_to_seat_profile(
    command: str, handler_name: str, expected: int | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        _acp_compat,
        "run_compat_ask",
        lambda *args, **kwargs: captured.update(kwargs) or SimpleNamespace(ok=True),
    )
    args = _cli._build_parser().parse_args(
        [command, "question", "--task-id", "profile-forward", "--from", "codex"]
    )

    getattr(_cli, handler_name)(args)

    assert captured["hard_timeout"] is expected


def test_cli_no_timeout_still_bypasses_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        _acp_compat,
        "run_compat_ask",
        lambda *args, **kwargs: captured.update(kwargs) or SimpleNamespace(ok=True),
    )
    args = _cli._build_parser().parse_args(
        ["ask-kimi", "question", "--task-id", "no-timeout", "--from", "codex", "--no-timeout"]
    )

    _cli._handle_ask_kimi(args)

    assert captured["hard_timeout"] == 86400


def test_timeout_error_names_seat_profile_and_no_timeout_escape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#6877: the timeout exit text names the seat's profile and the escape."""
    from agent_runtime.errors import AgentTimeoutError

    def raise_timeout(*args: object, **kwargs: object) -> object:
        raise AgentTimeoutError("acpx-kimi-shadow", 1800)

    monkeypatch.setattr(_acp_compat, "run_compat_ask", raise_timeout)
    args = _cli._build_parser().parse_args(
        ["ask-kimi", "question", "--task-id", "slow-review", "--from", "codex"]
    )

    with pytest.raises(SystemExit) as exc_info:
        _cli._handle_ask_kimi(args)

    message = str(exc_info.value)
    assert "ask-kimi" in message
    assert "hard_timeout=1800s" in message
    assert "defaults to 1800s" in message
    assert "generic default 300s" in message
    assert "--no-timeout" in message
