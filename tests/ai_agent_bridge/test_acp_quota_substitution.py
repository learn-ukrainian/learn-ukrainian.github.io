"""#8499: an over-quota ACP ask substitutes to the mapped ACP seat, once.

The fake ACP participant is a monkeypatched ``invoke_inter_agent``; no real
provider is ever called. The substitution map comes from a tmp-path YAML via
the shared loader, so these tests exercise the same ``dispatch_fallbacks``
table delegate.py reads.
"""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime.errors import RateLimitedError
from agent_runtime.result import Result

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


def _quota_result(participant: str) -> Result:
    """The post-#8655 shape: parsed provider quota wording, outcome=error."""
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


def _wire(
    monkeypatch: pytest.MonkeyPatch,
    authority: _FakeAuthority,
    behavior: dict[str, object],
    *,
    fallbacks_yaml: str | None = _FALLBACKS_YAML,
    tmp_path: Path | None = None,
) -> Mock:
    """Fake the ACP participant, the reachability probe, and the subs table."""

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
    if fallbacks_yaml is not None:
        assert tmp_path is not None
        config = tmp_path / "agent_fallback_substitutions.yaml"
        config.write_text(fallbacks_yaml, encoding="utf-8")
        monkeypatch.setattr(_acp_compat, "_FALLBACK_SUBS_PATH", config)
    return invoke


def test_quota_error_substitutes_once_to_mapped_seat_and_records_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _quota_result("codex"), "cursor": _ok_result("cursor", "cursor answer")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-sub", source="claude")

    assert result.ok is True
    assert result.response == "cursor answer"
    assert result.substitution == {"from": "codex", "to": "cursor", "reason": "provider_quota"}
    # One invocation per seat; the substitute gets no per-seat overrides.
    assert [call.args[0] for call in invoke.call_args_list] == ["codex", "cursor"]
    err = capsys.readouterr().err
    assert "ACP substitution: codex -> cursor (reason: provider_quota)" in err
    # Task record: the failed seat's job terminalizes as a capacity failure
    # before the substitute runs; the substitute's job carries the record.
    assert authority.enqueued[0]["recipient"] == "codex"
    assert "substitution" not in authority.enqueued[0]["metadata"]
    assert authority.enqueued[1]["recipient"] == "cursor"
    assert authority.enqueued[1]["metadata"]["substitution"] == {
        "from": "codex",
        "to": "cursor",
        "reason": "provider_quota",
    }
    assert authority.finished[0]["state"] == "failed"
    assert authority.finished[0]["failure"] == {
        "phase": "provider",
        "code": "rate_limited",
        "retryable": True,
    }
    assert authority.finished[1]["state"] == "complete"
    receipt = json.loads(authority.finished[1]["result"])
    assert receipt["substitution"] == {"from": "codex", "to": "cursor", "reason": "provider_quota"}
    assert receipt["ok"] is True


def test_quota_substitution_drops_explicit_model_and_effort_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _quota_result("codex"), "cursor": _ok_result("cursor")},
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


def test_substitute_also_over_quota_fails_loudly_without_second_hop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"codex": _quota_result("codex"), "cursor": _quota_result("cursor")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("codex", "question", task_id="quota-double")

    assert result.ok is False
    # Exactly one hop: codex, cursor, stop. No third seat, no bridge/provider.
    assert [call.args[0] for call in invoke.call_args_list] == ["codex", "cursor"]
    assert len(authority.enqueued) == 2
    err = capsys.readouterr().err
    assert "ACP substitution: codex -> cursor (reason: provider_quota)" in err
    assert "ACP substitution exhausted: substitute seat 'cursor' is also over quota" in err
    assert "refusing a second substitution and any bridge/provider fallback" in err
    assert result.substitution == {"from": "codex", "to": "cursor", "reason": "provider_quota"}


def test_substitute_rate_limited_exception_fails_loudly_without_second_hop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {
            "codex": _quota_result("codex"),
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
    err = capsys.readouterr().err
    assert "ACP substitution" not in err
    assert "outcome=error" in err


def test_seat_without_mapping_fails_unchanged_with_clear_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    authority = _FakeAuthority()
    invoke = _wire(
        monkeypatch,
        authority,
        {"kimi": _quota_result("kimi")},
        tmp_path=tmp_path,
    )

    result = _acp_compat._run_compat_ask_impl("kimi", "question", task_id="quota-no-map")

    assert result.ok is False
    assert invoke.call_count == 1
    assert result.substitution is None
    err = capsys.readouterr().err
    assert "ACP substitution:" not in err
    assert (
        "ACP seat 'kimi' is over quota/rate-limited (reason: provider_quota) and "
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
        {"codex": _quota_result("codex")},
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
    substitution = {"from": "codex", "to": "cursor", "reason": "provider_quota"}

    receipt = _acp_compat._result_receipt(result, substitution=substitution)
    replay = _acp_compat._replay_result(receipt)

    assert replay.ok is True
    assert replay.substitution == substitution
    assert replay.usage_record["substitution"] == substitution


def test_delegate_dispatch_fallbacks_use_the_same_shared_table() -> None:
    """delegate.py and the ACP ask path read one loader, not two copies."""
    import delegate

    from scripts.common.fallback_substitutions import load_dispatch_fallbacks

    assert delegate._load_dispatch_fallbacks() == load_dispatch_fallbacks(delegate._FALLBACK_SUBS_PATH)
    assert delegate._load_dispatch_fallbacks()["codex"] == "cursor"
