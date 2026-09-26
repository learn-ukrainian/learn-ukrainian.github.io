"""#8499: an over-quota ACP ask substitutes to the mapped ACP seat, once.

The fake ACP participant is a monkeypatched ``invoke_inter_agent``; no real
provider is ever called. The substitution map comes from a tmp-path YAML via
the shared loader, so these tests exercise the same ``dispatch_fallbacks``
table delegate.py reads.

The substitution decision is a pure function of typed signals (the runner's
RateLimitedError, the result's rate_limited flag, a rate_limited transport
outcome, or a typed capacity failure code) — never of message text. It is
computed once at the live failure and persisted in the job result receipt;
replay and retry read the stored field and never recompute.
"""

from __future__ import annotations

import json
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime.errors import RateLimitedError
from agent_runtime.result import Result
from agent_runtime.runner import _SAFE_ACP_FAILURE_CODES

from scripts.ai_agent_bridge import _acp_compat, _cli

_FALLBACKS_YAML = """\
dispatch_fallbacks:
  claude: codex
  codex: cursor
"""


def _ok_result(participant: str, response: str = "answer") -> Result:
    return Result(
        ok=True,
        agent=participant,
        model=f"{participant}-model",
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


def _capacity_result(participant: str) -> Result:
    """A typed provider-capacity failure: every typed rate-limit signal set."""
    return Result(
        ok=False,
        agent=participant,
        model=f"{participant}-model",
        mode="read-only",
        response="",
        stderr_excerpt="acpx RUNTIME: provider quota exhausted",
        duration_s=0.5,
        session_id=None,
        rate_limited=True,
        stalled=False,
        returncode=1,
        effort="high",
        usage_record={"failure_code": "rate_limited"},
        transport_outcome="rate_limited",
    )


def _text_only_quota_result(participant: str) -> Result:
    """The post-#8655 shape: quota wording only in text, generic typed code.

    With the text fallback deleted (#8499) this is an adapter parsing gap,
    not a capacity signal: it must fail without substitution.
    """
    return Result(
        ok=False,
        agent=participant,
        model=f"{participant}-model",
        mode="read-only",
        response="",
        stderr_excerpt="acpx RUNTIME: provider quota exhausted",
        duration_s=0.5,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=1,
        effort="high",
        usage_record={"failure_code": "transport_error"},
        transport_outcome="error",
    )


def _non_quota_result(participant: str) -> Result:
    return Result(
        ok=False,
        agent=participant,
        model=f"{participant}-model",
        mode="read-only",
        response="",
        stderr_excerpt="acpx RUNTIME: agent crashed mid-turn",
        duration_s=0.5,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=1,
        effort="high",
        usage_record={"failure_code": "transport_error"},
        transport_outcome="error",
    )


def _typed_failure_result(participant: str, *, failure_code: str, excerpt: str) -> Result:
    """A parser-typed failure whose bounded excerpt happens to mention quota."""
    return Result(
        ok=False,
        agent=participant,
        model=f"{participant}-model",
        mode="read-only",
        response="",
        stderr_excerpt=excerpt,
        duration_s=0.5,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=1,
        effort="high",
        usage_record={"failure_code": failure_code},
        transport_outcome="error",
    )


def _coded_failure_result(participant: str, failure_code: str | None) -> Result:
    """A parser-typed failure whose excerpt is saturated with capacity wording.

    The decision must come from the typed code alone (#8499): only the
    capacity code substitutes, however loudly the text mentions quota.
    """
    return Result(
        ok=False,
        agent=participant,
        model=f"{participant}-model",
        mode="read-only",
        response="",
        stderr_excerpt="acpx RUNTIME: provider quota exhausted\n[acpx stderr]\nrate limit 429",
        duration_s=0.5,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=1,
        effort="high",
        usage_record={} if failure_code is None else {"failure_code": failure_code},
        transport_outcome="error",
    )


class _FakeAuthority:
    """In-memory authority: every ask gets its own job; metadata is captured."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        self.enqueued: list[dict[str, object]] = []
        self.finished: list[dict[str, object]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def enqueue_request(self, **kwargs):
        self.enqueued.append(kwargs)
        return SimpleNamespace(job_id=f"job-{len(self.enqueued)}", state="queued")

    def claim_job(self, *_args, **_kwargs):
        return SimpleNamespace(fence_token=1)

    def finish_job(self, job_id, **kwargs):
        self.finished.append({"job_id": job_id, **kwargs})


def _forbidden_acp_bypass(channel: str):
    """Fail the test if an ordinary ask leaves the ACP seat path."""

    def _refuse(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(f"ACP-only ask must not call {channel}")

    return _refuse


def _wire(
    monkeypatch: pytest.MonkeyPatch,
    authority: _FakeAuthority,
    behavior: dict[str, object],
    *,
    fallbacks_yaml: str | None = _FALLBACKS_YAML,
    tmp_path: Path | None = None,
) -> Mock:
    """Fake the ACP participant, the reachability probe, and the subs table.

    Ordinary asks stay on ACP. ``runner.invoke``, a provider subprocess, the
    headless review dispatcher, and ``delegate.py`` dispatch all fail the
    test if the ask reaches them. The local-plane probe is pinned off so the
    subprocess guard is not tripped by the git check that decides forwarding.
    """

    def fake_invoke(participant: str, *_args, **_kwargs) -> Result:
        outcome = behavior[participant]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    invoke = Mock(side_effect=fake_invoke)

    @contextmanager
    def execution_cwd(*_args, **_kwargs):
        yield Path.cwd()

    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", lambda: authority)
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)
    monkeypatch.setattr("scripts.ai_agent_bridge._acp_execution.acp_execution_cwd", execution_cwd)
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.acpx.probe_participant_reachability",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._job_host_forward.local_plane_is_retired",
        lambda *_args, **_kwargs: False,
    )
    # Import delegate before the subprocess guard: module import may probe git.
    monkeypatch.setattr("delegate.cmd_dispatch", _forbidden_acp_bypass("delegate.cmd_dispatch"))
    monkeypatch.setattr(
        _cli,
        "_dispatch_headless_review",
        _forbidden_acp_bypass("_cli._dispatch_headless_review"),
    )
    monkeypatch.setattr("agent_runtime.runner.invoke", _forbidden_acp_bypass("runner.invoke"))
    monkeypatch.setattr(subprocess, "run", _forbidden_acp_bypass("subprocess.run"))
    monkeypatch.setattr(subprocess, "Popen", _forbidden_acp_bypass("subprocess.Popen"))
    if fallbacks_yaml is not None:
        assert tmp_path is not None
        config = tmp_path / "agent_fallback_substitutions.yaml"
        config.write_text(fallbacks_yaml, encoding="utf-8")
        monkeypatch.setattr(_acp_compat, "_FALLBACK_SUBS_PATH", config)
    return invoke


def test_typed_capacity_failure_substitutes_once_to_mapped_seat_and_records_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _capacity_result("codex"), "cursor": _ok_result("cursor", "cursor answer")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-sub", source="claude")

    assert result.ok is True
    assert result.response == "cursor answer"
    assert result.seat_substitution == {"from": "codex", "to": "cursor", "reason": "rate_limited"}
    assert result.substitution is None
    # One invocation per seat; the substitute gets no per-seat overrides.
    assert [call.args[0] for call in invoke.call_args_list] == ["codex", "cursor"]
    err = capsys.readouterr().err
    assert "ACP substitution: codex -> cursor (reason: rate_limited)" in err
    # Task record: the failed seat's job terminalizes as a capacity failure
    # before the substitute runs; the substitute's job carries the record.
    assert authority.enqueued[0]["recipient"] == "codex"
    assert "seat_substitution" not in authority.enqueued[0]["metadata"]
    assert "substitution" not in authority.enqueued[0]["metadata"]
    assert authority.enqueued[1]["recipient"] == "cursor"
    assert authority.enqueued[1]["metadata"]["seat_substitution"] == {
        "from": "codex",
        "to": "cursor",
        "reason": "rate_limited",
    }
    assert "substitution" not in authority.enqueued[1]["metadata"]
    assert authority.finished[0]["state"] == "failed"
    assert authority.finished[0]["failure"] == {
        "phase": "provider",
        "code": "rate_limited",
        "retryable": True,
    }
    assert authority.finished[1]["state"] == "complete"
    receipt = json.loads(authority.finished[1]["result"])
    assert receipt["seat_substitution"] == {"from": "codex", "to": "cursor", "reason": "rate_limited"}
    assert "substitution" not in receipt
    assert receipt["ok"] is True
    # The failed seat's receipt stores the typed code and the decision itself.
    failed_receipt = json.loads(authority.finished[0]["result"])
    assert failed_receipt["failure_code"] == "rate_limited"
    assert failed_receipt["substitution_decision"] == {"substitute": True, "reason": "rate_limited"}


def test_quota_substitution_drops_explicit_model_and_effort_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _capacity_result("codex"), "cursor": _ok_result("cursor")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl(
        "codex", "question", task_id="quota-sub-overrides", model="gpt-6-astra", effort="high"
    )

    assert result.ok is True
    assert invoke.call_args_list[0].kwargs["model"] == "gpt-6-astra"
    assert invoke.call_args_list[0].kwargs["effort"] == "high"
    # Pins are per-seat: the substitute runs on its registered pin.
    assert invoke.call_args_list[1].kwargs["model"] is None
    assert invoke.call_args_list[1].kwargs["effort"] is None
    assert "overrides dropped" in capsys.readouterr().err


def test_rate_limited_exception_substitutes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {
            "codex": RateLimitedError("codex", "gpt-6-astra", "usage limit reached"),
            "cursor": _ok_result("cursor"),
        },
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-exc")

    assert result.ok is True
    assert [call.args[0] for call in invoke.call_args_list] == ["codex", "cursor"]
    assert authority.finished[0]["failure"] == {
        "phase": "provider",
        "code": "rate_limited",
        "retryable": True,
    }
    assert "ACP substitution: codex -> cursor (reason: rate_limited)" in capsys.readouterr().err
    # The exception-path receipt also stores the typed code and the decision.
    receipt = json.loads(authority.finished[0]["result"])
    assert receipt["failure_code"] == "rate_limited"
    assert receipt["substitution_decision"] == {"substitute": True, "reason": "rate_limited"}
    assert receipt["transport_outcome"] == "rate_limited"


def test_substitute_also_over_quota_fails_loudly_without_second_hop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _capacity_result("codex"), "cursor": _capacity_result("cursor")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-double")

    assert result.ok is False
    # Exactly one hop: codex, cursor, stop. No third seat, no bridge/provider.
    assert [call.args[0] for call in invoke.call_args_list] == ["codex", "cursor"]
    assert len(authority.enqueued) == 2
    err = capsys.readouterr().err
    assert "ACP substitution: codex -> cursor (reason: rate_limited)" in err
    assert "ACP substitution exhausted: substitute seat 'cursor' is also over quota" in err
    assert "refusing a second substitution and any bridge/provider fallback" in err
    assert result.seat_substitution == {"from": "codex", "to": "cursor", "reason": "rate_limited"}
    assert result.substitution is None


def test_substitute_rate_limited_exception_fails_loudly_without_second_hop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {
            "codex": _capacity_result("codex"),
            "cursor": RateLimitedError("cursor", "auto", "429"),
        },
        tmp_path=tmp_path,
    )

    with pytest.raises(RateLimitedError):
        _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-double-exc")

    assert [call.args[0] for call in invoke.call_args_list] == ["codex", "cursor"]
    assert len(authority.enqueued) == 2
    assert "ACP substitution exhausted" in capsys.readouterr().err


def test_non_quota_error_is_unchanged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _non_quota_result("codex")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="non-quota")

    assert result.ok is False
    assert invoke.call_count == 1
    assert result.substitution is None
    assert getattr(result, "seat_substitution", None) is None
    err = capsys.readouterr().err
    assert "ACP substitution" not in err
    assert "outcome=error" in err


def test_text_only_quota_wording_is_an_adapter_gap_not_a_capacity_signal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The post-#8655 shape — provider quota wording only in the excerpt,
    typed code transport_error — is an adapter parsing gap, not a capacity
    signal: with the text fallback deleted it fails without substitution and
    its durable failure metadata keeps the generic transport class (#8499)."""
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _text_only_quota_result("codex"), "cursor": _ok_result("cursor")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-text-only")

    assert result.ok is False
    assert [call.args[0] for call in invoke.call_args_list] == ["codex"]
    assert result.substitution is None
    assert getattr(result, "seat_substitution", None) is None
    assert "ACP substitution" not in capsys.readouterr().err
    assert authority.finished[0]["failure"] == {
        "phase": "transport",
        "code": "transport_error",
        "retryable": False,
    }
    receipt = json.loads(authority.finished[0]["result"])
    assert receipt["failure_code"] == "transport_error"
    assert receipt["substitution_decision"] == {"substitute": False, "reason": None}


def test_seat_without_mapping_fails_unchanged_with_clear_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"kimi": _capacity_result("kimi")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("kimi", "question", task_id="quota-no-map")

    assert result.ok is False
    assert invoke.call_count == 1
    assert result.substitution is None
    assert getattr(result, "seat_substitution", None) is None
    err = capsys.readouterr().err
    assert "ACP substitution:" not in err
    assert (
        "ACP seat 'kimi' is over quota/rate-limited (reason: rate_limited) and "
        "agent_fallback_substitutions.yaml dispatch_fallbacks has no substitute for it"
    ) in err
    assert "failing without bridge/provider fallback" in err


def test_mapping_to_a_non_acp_seat_fails_unchanged_with_clear_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _capacity_result("codex")},
        fallbacks_yaml="dispatch_fallbacks:\n  codex: not-an-acp-seat\n",
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-bad-map")

    assert result.ok is False
    assert invoke.call_count == 1
    err = capsys.readouterr().err
    assert "maps it to 'not-an-acp-seat', which is not an enabled ACP ask seat" in err
    assert "ACP substitution:" not in err


def test_cli_turns_unmapped_rate_limit_into_a_clean_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_rate_limited(*_args: object, **_kwargs: object) -> object:
        raise RateLimitedError("kimi", "k3", "usage limit reached")

    monkeypatch.setattr(_acp_compat, "run_compat_ask", raise_rate_limited)
    args = _cli._build_parser().parse_args(["ask-kimi", "question", "--task-id", "rate-limited-cli", "--from", "codex"])

    with pytest.raises(SystemExit, match="kimi/k3 rate limited"):
        _cli._handle_ask_kimi(args)


def test_substitution_record_survives_receipt_replay() -> None:
    result = _ok_result("cursor")
    substitution = {"from": "codex", "to": "cursor", "reason": "rate_limited"}
    decision = {"substitute": False, "reason": None}

    receipt = _acp_compat._result_receipt(result, seat_substitution=substitution, substitution_decision=decision)
    replay = _acp_compat._replay_result(receipt)

    assert replay.ok is True
    assert replay.seat_substitution == substitution
    assert replay.substitution is None
    assert replay.usage_record["seat_substitution"] == substitution
    assert "substitution" not in replay.usage_record
    assert replay.substitution_decision == decision


@pytest.mark.parametrize(
    ("failure_code", "excerpt"),
    [
        (
            "acp_auth_required",
            "acpx AUTH_REQUIRED: login required\n[acpx stderr]\nquota usage report follows",
        ),
        (
            "result_invalid",
            "unrecognized terminal stopReason schema: 'quota'\n[acpx stderr]\nquota",
        ),
        (
            "acp_agent_disconnected",
            "acpx AGENT_DISCONNECTED: connection dropped; quota state unknown",
        ),
        (
            # The parser's untyped catch-all with appended stderr that mentions
            # quota without a provider capacity phrasing is still not capacity.
            "transport_error",
            "acpx exec exited rc=1 despite stopReason='end_turn'\n[acpx stderr]\nsee quota docs",
        ),
        (
            # The post-#8655 quota shape: the parser's untyped catch-all whose
            # excerpt keeps the provider's exact capacity wording. With the
            # text fallback deleted this is an adapter parsing gap, not a
            # capacity signal.
            "transport_error",
            "acpx RUNTIME: provider quota exhausted",
        ),
    ],
    ids=["auth", "schema", "network", "generic-with-bare-quota-word", "generic-with-exact-quota-phrasing"],
)
def test_typed_non_capacity_failure_mentioning_quota_is_not_substituted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    failure_code: str,
    excerpt: str,
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _typed_failure_result("codex", failure_code=failure_code, excerpt=excerpt)},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id=f"typed-{failure_code}")

    assert result.ok is False
    assert invoke.call_count == 1
    assert result.substitution is None
    assert getattr(result, "seat_substitution", None) is None
    assert "ACP substitution" not in capsys.readouterr().err


def test_typed_capacity_failure_code_substitutes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {
            "codex": _typed_failure_result("codex", failure_code="rate_limited", excerpt="acpx RUNTIME: throttled"),
            "cursor": _ok_result("cursor"),
        },
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="typed-capacity-code")

    assert result.ok is True
    assert [call.args[0] for call in invoke.call_args_list] == ["codex", "cursor"]
    assert result.seat_substitution == {"from": "codex", "to": "cursor", "reason": "rate_limited"}
    assert result.substitution is None
    assert authority.finished[0]["failure"] == {
        "phase": "provider",
        "code": "rate_limited",
        "retryable": True,
    }
    assert "reason: rate_limited" in capsys.readouterr().err
    receipt = json.loads(authority.finished[0]["result"])
    assert receipt["failure_code"] == "rate_limited"
    assert receipt["substitution_decision"] == {"substitute": True, "reason": "rate_limited"}


@pytest.mark.parametrize(
    ("overrides",),
    [
        ({"rate_limited": True, "transport_outcome": "rate_limited"},),
        ({"transport_outcome": "rate_limited"},),
    ],
    ids=["rate-limited-flag", "rate-limited-outcome"],
)
def test_runner_typed_rate_limit_signals_substitute(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    overrides: dict[str, object],
) -> None:
    failure = _non_quota_result("codex")
    failure = replace(failure, **overrides)
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": failure, "cursor": _ok_result("cursor")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="typed-rl-signal")

    assert result.ok is True
    assert [call.args[0] for call in invoke.call_args_list] == ["codex", "cursor"]
    assert result.seat_substitution == {"from": "codex", "to": "cursor", "reason": "rate_limited"}
    assert result.substitution is None
    assert "reason: rate_limited" in capsys.readouterr().err


@pytest.mark.parametrize("failure_code", [*sorted(_SAFE_ACP_FAILURE_CODES), None])
def test_live_and_replay_decisions_match_for_every_parser_code(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure_code: str | None
) -> None:
    """Live and replayed asks route identically for every typed code (#8499).

    The excerpt is saturated with provider capacity wording on every row: the
    decision is a pure function of the typed code (only the capacity code
    substitutes), is persisted on the receipt together with the code, and
    replay reads the stored field verbatim instead of recomputing.
    """
    expected = {
        "substitute": failure_code == "rate_limited",
        "reason": "rate_limited" if failure_code == "rate_limited" else None,
    }
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _coded_failure_result("codex", failure_code), "cursor": _ok_result("cursor")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id=f"typed-code-{failure_code}")

    seats = [call.args[0] for call in invoke.call_args_list]
    if expected["substitute"]:
        assert seats == ["codex", "cursor"]
        assert result.seat_substitution == {"from": "codex", "to": "cursor", "reason": "rate_limited"}
        assert result.substitution is None
    else:
        assert seats == ["codex"]
        assert result.substitution is None
        assert getattr(result, "seat_substitution", None) is None
    receipt = json.loads(authority.finished[0]["result"])
    assert receipt["failure_code"] == failure_code
    assert receipt["substitution_decision"] == expected
    replayed = _acp_compat._replay_result(authority.finished[0]["result"])
    assert _acp_compat._substitution_decision(result=replayed) == expected


def test_old_receipt_without_stored_decision_replays_as_no_substitution() -> None:
    """Receipts written before the decision field existed replay as no
    substitution (#8499): even with quota wording in the excerpt and a
    rate_limited transport outcome, the durable failure stands — replay never
    recomputes a decision from text or outcome."""
    old_receipt = json.dumps(
        {
            "ok": False,
            "agent": "codex",
            "model": "codex-model",
            "response": "",
            "stderr_excerpt": "acpx RUNTIME: provider quota exhausted",
            "duration_s": 0.5,
            "returncode": 1,
            "effort": "high",
            "from_model": "codex-model",
            "model_requested": "codex-model",
            "effort_requested": None,
            "effort_applied": None,
            "harness": "acp",
            "transport_metadata": None,
            "transport_outcome": "rate_limited",
        }
    ).encode("utf-8")

    replayed = _acp_compat._replay_result(old_receipt)

    assert replayed.ok is False
    assert replayed.substitution is None
    assert getattr(replayed, "seat_substitution", None) is None
    assert replayed.substitution_decision == {"substitute": False, "reason": None}
    assert _acp_compat._substitution_decision(result=replayed) == {
        "substitute": False,
        "reason": None,
    }


def test_old_receipt_substitution_key_is_not_a_seat_hop() -> None:
    """The provider-route field name is not a seat hop. Receipts that stored
    the hop under ``substitution``, or omit ``seat_substitution``, replay as
    no seat substitution (#8499)."""
    old_receipt = json.dumps(
        {
            "ok": True,
            "agent": "cursor",
            "model": "cursor-model",
            "response": "cursor answer",
            "stderr_excerpt": None,
            "duration_s": 1.0,
            "returncode": 0,
            "effort": "high",
            "from_model": "cursor-model",
            "model_requested": "cursor-model",
            "effort_requested": None,
            "effort_applied": "high",
            "harness": "acp",
            "substitution": {"from": "codex", "to": "cursor", "reason": "rate_limited"},
            "substitution_decision": {"substitute": False, "reason": None},
            "transport_metadata": None,
            "transport_outcome": "ok",
        }
    ).encode("utf-8")

    replayed = _acp_compat._replay_result(old_receipt)

    assert getattr(replayed, "seat_substitution", None) is None
    assert replayed.substitution is None
    assert "substitution" not in replayed.usage_record
    assert "seat_substitution" not in replayed.usage_record


def test_seat_hop_preserves_provider_route_substitution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    provider_route = {
        "substituted": True,
        "requested_provider": "openai",
        "actual_provider": "openai",
        "requested_model": "gpt-6-astra",
        "actual_model": "composer-2.5",
    }
    authority = _FakeAuthority()
    _wire(
        monkeypatch,
        authority,
        {
            "codex": _capacity_result("codex"),
            "cursor": replace(_ok_result("cursor", "cursor answer"), substitution=provider_route),
        },
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-provider-route")

    assert result.seat_substitution == {"from": "codex", "to": "cursor", "reason": "rate_limited"}
    assert result.substitution == provider_route


def test_unrelated_error_named_rate_limited_does_not_substitute(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class RateLimitedError(Exception):
        pass

    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": RateLimitedError("usage limit reached"), "cursor": _ok_result("cursor")},
        tmp_path=tmp_path,
    )

    with pytest.raises(RateLimitedError):
        _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-impostor")

    assert [call.args[0] for call in invoke.call_args_list] == ["codex"]
    assert authority.finished[0]["failure"]["code"] != "rate_limited"


def test_acp_only_wiring_refuses_bridge_and_provider_execution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import delegate
    from agent_runtime import runner

    _wire(monkeypatch, _FakeAuthority(), {"codex": _ok_result("codex")}, tmp_path=tmp_path)

    with pytest.raises(AssertionError, match=r"runner\.invoke"):
        runner.invoke("codex", "prompt")
    with pytest.raises(AssertionError, match=r"subprocess\.run"):
        subprocess.run(["false"], timeout=5)
    with pytest.raises(AssertionError, match=r"subprocess\.Popen"):
        subprocess.Popen(["false"])
    with pytest.raises(AssertionError, match=r"_cli\._dispatch_headless_review"):
        _cli._dispatch_headless_review(
            "codex",
            "prompt",
            data=None,
            task_id="t",
            model=None,
            effort=None,
            output_path=None,
            stdout_only=False,
            hard_timeout=None,
        )
    with pytest.raises(AssertionError, match=r"delegate\.cmd_dispatch"):
        delegate.cmd_dispatch(SimpleNamespace())


class _DurableAuthority:
    """Persists jobs across runs and enforces the real idempotency rule:

    a re-enqueue under an existing key must carry an identical payload, else
    AuthorityServiceError, mirroring authority.py's _assert_job_payload.
    """

    def __init__(self, store: dict[str, object]) -> None:
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def enqueue_request(self, *, recipient, body, sender, metadata, idempotency_key):
        payload = {"recipient": recipient, "metadata": metadata, "body": body}
        jobs = self.store["jobs"]
        existing = self.store["by_key"].get(idempotency_key)
        if existing is not None:
            job = jobs[existing]
            if job["payload"] != payload:
                from scripts.fleet_comms.authority import AuthorityServiceError

                raise AuthorityServiceError("idempotency_key_reused_with_different_payload")
            return SimpleNamespace(job_id=job["job_id"], state=job["state"])
        job_id = f"job-{len(jobs) + 1}"
        jobs[job_id] = {"job_id": job_id, "payload": payload, "state": "queued", "result": None}
        self.store["by_key"][idempotency_key] = job_id
        return SimpleNamespace(job_id=job_id, state="queued")

    def claim_job(self, job_id, *_args, **_kwargs):
        if job_id in self.store.get("crash_job_ids", ()):
            raise KeyboardInterrupt("simulated crash after the substitute was enqueued")
        return SimpleNamespace(fence_token=1)

    def get_job(self, job_id):
        job = self.store["jobs"][job_id]
        return SimpleNamespace(job_id=job_id, state=job["state"])

    def read_job_result(self, job_id):
        return self.store["jobs"][job_id]["result"]

    def finish_job(self, job_id, *, state, result, failure, **_kwargs):
        job = self.store["jobs"][job_id]
        job["state"] = state
        job["result"] = result
        job["failure"] = failure


def test_retry_after_crash_replays_the_stored_reason_and_completes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Live run classifies RateLimitedError as rate_limited, enqueues the
    substitute, then crashes. The retry replays the stored receipt and reads
    the persisted decision verbatim, so the substitute's re-enqueue under the
    same idempotency key carries identical substitution metadata.
    """
    store: dict[str, object] = {"jobs": {}, "by_key": {}, "crash_job_ids": {"job-2"}}
    invoke = _wire(
        monkeypatch,
        _DurableAuthority(store),
        {
            "codex": RateLimitedError("codex", "gpt-6-astra", "usage limit reached"),
            "cursor": _ok_result("cursor", "cursor answer"),
        },
        tmp_path=tmp_path,
    )

    with pytest.raises(KeyboardInterrupt):
        _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-crash")

    # The substitute was enqueued under the live decision before the crash,
    # and the failed seat's receipt persisted the decision for replay.
    jobs = store["jobs"]
    assert jobs["job-2"]["payload"]["metadata"]["seat_substitution"] == {
        "from": "codex",
        "to": "cursor",
        "reason": "rate_limited",
    }
    assert "substitution" not in jobs["job-2"]["payload"]["metadata"]
    receipt = json.loads(jobs["job-1"]["result"])
    assert receipt["transport_outcome"] == "rate_limited"
    assert receipt["failure_code"] == "rate_limited"
    assert receipt["substitution_decision"] == {"substitute": True, "reason": "rate_limited"}
    # codex's invocation raised; the crash hit before cursor was invoked.
    assert [call.args[0] for call in invoke.call_args_list] == ["codex"]
    assert "reason: rate_limited" in capsys.readouterr().err

    store["crash_job_ids"] = set()
    invoke.reset_mock()

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-crash")

    # No idempotency rejection: the replayed stored decision matched the live
    # decision, so the substitute's payload was identical and the queued job
    # resumed.
    assert result.ok is True
    assert result.response == "cursor answer"
    assert result.seat_substitution == {"from": "codex", "to": "cursor", "reason": "rate_limited"}
    assert result.substitution is None
    assert [call.args[0] for call in invoke.call_args_list] == ["cursor"]
    assert jobs["job-2"]["state"] == "complete"


def test_delegate_dispatch_fallbacks_use_the_same_shared_table() -> None:
    """delegate.py and the ACP ask path read one loader, not two copies."""
    import delegate

    from scripts.common.fallback_substitutions import load_dispatch_fallbacks

    assert delegate._load_dispatch_fallbacks() == load_dispatch_fallbacks(delegate._FALLBACK_SUBS_PATH)
    assert delegate._load_dispatch_fallbacks()["codex"] == "cursor"
