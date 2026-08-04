"""Tests for pointer-only review-pr entrypoint."""

from __future__ import annotations

import hashlib
import json
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from agent_runtime.adapters.acpx import (
    AcpxAdapter,
    AcpxGlmShadowAdapter,
    _confinement_prefix_argv,
)
from ai_agent_bridge import _review_pr as review_pr
from ai_agent_bridge._review_safety import ReviewSafetyError


def _invalid_response_args() -> Namespace:
    return Namespace(
        pr="6342",
        reviewer="auto",
        claude_available=None,
        model=None,
        effort=None,
        extra=None,
        task_id=None,
        dry_run=False,
        background=False,
        no_timeout=False,
        initiator="codex/orchestrator",
        author_model="gpt-5.6-sol",
        author_family="openai",
        allow_explicit_fallback=False,
        override_reason=None,
        review_profile=None,
        risk=None,
        role=None,
        required_capability=None,
        data_egress_policy=None,
        isolation_required=True,
    )


def _run_invalid_response_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    stale_lease: bool,
) -> tuple[int, list[str], object]:
    """Run one invalid response through the bridge with a real formal-job store."""
    from agent_runtime import runner
    from ai_agent_bridge import _review_worktree

    from scripts.fleet_comms import authority as authority_module
    from scripts.fleet_comms import routing_reservations
    from scripts.fleet_comms.artifacts import ArtifactStore
    from scripts.fleet_comms.formal_review_jobs import FormalReviewJobService

    checkout = SimpleNamespace(
        sha="a" * 40,
        base_sha="b" * 40,
        patch_digest="c" * 64,
        changed_paths=("src/app.py",),
        changed_line_numbers={"src/app.py": frozenset({1})},
        path=tmp_path,
        review_prompt_evidence=lambda _engine: "sealed-metadata",
        sealed_acp_tool_config=lambda **_kwargs: tmp_path / "sealed.json",
        sealed_evidence_input_bytes=lambda: 123,
    )

    @contextmanager
    def provision(*_args, **_kwargs):
        yield checkout

    reservation = SimpleNamespace(
        reservation_id="routing-reservation_fixture",
        resolved_candidate="claude-sonnet-5",
        resolved_route="claude",
        resolved_model="claude-sonnet-5",
        resolved_family="anthropic",
        quota_bucket="claude",
    )
    events: list[str] = []

    class FakeLedger:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def reserve_selection(self, *_args, **_kwargs):
            return reservation

        def mark_started(self, _reservation_id):
            events.append("started")

        def settle(self, _reservation_id, **_kwargs):
            events.append("settled")
            job = formal_jobs.list_jobs(include_attempts=True)[0]
            assert job.state == "failed"
            assert len(job.attempts) == 1
            capture_id = job.attempts[0].raw_capture_artifact_id
            assert capture_id is not None
            assert store.read_bytes(capture_id) == b"not valid JSON"
            return reservation

    store = ArtifactStore(root=tmp_path / "fleet-comms-v1")
    formal_jobs = FormalReviewJobService(store=store)

    class FakeAuthority:
        def __init__(self) -> None:
            self.store = store
            self.formal = None
            self.job = SimpleNamespace(state="queued", job_id="authority-job_fixture", subject_id="")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_formal_review(self, **_kwargs):
            self.formal = formal_jobs.create_job(
                "learn-ukrainian/learn-ukrainian.github.io",
                6342,
                checkout.sha,
                "cross-family-review",
            )
            self.job.subject_id = self.formal.review_id
            return self.job

        def require_publishable_formal_review(self, review_id, **_kwargs):
            return formal_jobs.get_job(review_id, include_attempts=False)

        def claim_job(self, *_args, **_kwargs):
            return SimpleNamespace(fence_token=1)

        def finish_job(self, *_args, **_kwargs):
            events.append("finish")
            assert self.formal is not None
            recorded = formal_jobs.get_job(self.formal.review_id)
            assert recorded.state == "failed"
            assert recorded.sealed_verdict_artifact_id is None
            assert len(recorded.attempts) == 1
            capture_id = recorded.attempts[0].raw_capture_artifact_id
            assert capture_id is not None
            assert store.read_bytes(capture_id) == b"not valid JSON"
            if stale_lease:
                raise authority_module.AuthorityStaleLeaseError("terminalization_conflict")

    authority = FakeAuthority()
    monkeypatch.setattr(_review_worktree, "provision_review_worktree", provision)
    monkeypatch.setattr(
        _review_worktree,
        "validate_code_review_response",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            _review_worktree.ReviewWorktreeError("review_response_invalid_json")
        ),
    )
    monkeypatch.setattr(review_pr, "_compute_review_routing_budget", lambda: {"agents": {}})
    monkeypatch.setattr(routing_reservations, "RoutingReservationLedger", FakeLedger)
    monkeypatch.setattr(authority_module, "AuthorityService", lambda: authority)
    monkeypatch.setattr(
        runner,
        "invoke_inter_agent",
        lambda *_args, **_kwargs: SimpleNamespace(ok=True, response="not valid JSON"),
    )
    try:
        return review_pr.handle_review_pr(_invalid_response_args()), events, formal_jobs
    finally:
        # The caller inspects the service before this helper returns; its store
        # is then closed by the test after assertions.
        pass


def test_invalid_json_is_captured_before_live_lease_failure_settlement(monkeypatch, tmp_path, capsys) -> None:
    code, events, formal_jobs = _run_invalid_response_lifecycle(
        monkeypatch,
        tmp_path,
        stale_lease=False,
    )
    try:
        assert code == 1
        assert events == ["started", "settled", "finish"]
        job = formal_jobs.list_jobs(include_attempts=True)[0]
        assert job.state == "failed"
        assert job.sealed_verdict_artifact_id is None
        assert job.attempts[0].completion_state == "failed"
        assert "reviewer result invalid" in capsys.readouterr().err
    finally:
        formal_jobs.close()


def test_invalid_json_is_captured_before_stale_lease_failure_settlement(monkeypatch, tmp_path, capsys) -> None:
    code, events, formal_jobs = _run_invalid_response_lifecycle(
        monkeypatch,
        tmp_path,
        stale_lease=True,
    )
    try:
        assert code == 1
        assert events == ["started", "settled", "finish"]
        job = formal_jobs.list_jobs(include_attempts=True)[0]
        assert job.state == "failed"
        assert job.sealed_verdict_artifact_id is None
        assert job.attempts[0].raw_capture_artifact_id is not None
        assert "lease was lost while validating" in capsys.readouterr().err
    finally:
        formal_jobs.close()


def test_parse_pr_number() -> None:
    assert review_pr.parse_pr_number("5443") == 5443
    assert review_pr.parse_pr_number("#99") == 99
    with pytest.raises(ReviewSafetyError):
        review_pr.parse_pr_number("not-a-pr")


def test_resolve_reviewer_auto() -> None:
    assert review_pr.resolve_reviewer("auto", claude_available=None) == "auto"
    assert review_pr.resolve_reviewer("auto", claude_available=False) == "auto"
    assert review_pr.resolve_reviewer("glm") == "glm"
    assert review_pr.resolve_reviewer("grok") == "grok"
    assert review_pr.resolve_reviewer("kimi") == "kimi"


def test_formal_review_authority_key_is_bounded_and_opaque() -> None:
    key = review_pr._formal_review_authority_key(
        "learn-ukrainian/learn-ukrainian.github.io",
        6191,
        "a" * 40,
        "b" * 64,
    )
    assert key.startswith("formal-review:")
    assert len(key) == len("formal-review:") + 64
    assert "/" not in key


def test_evidence_metrics_extracts_only_non_negative_integer_receipts() -> None:
    dossier = {
        "evidence_metrics": {
            "unique_evidence_bytes": 123,
            "legacy_inline_serialized_bytes": 456,
            "invalid_bool": True,
            "invalid_negative": -1,
        }
    }
    evidence = (
        "prefix\nAUTHORITATIVE SEALED REVIEW EVIDENCE\n"
        f"{json.dumps(dossier)}\n"
        "END AUTHORITATIVE SEALED REVIEW EVIDENCE\n"
    )

    assert review_pr._evidence_metrics(evidence) == {
        "unique_evidence_bytes": 123,
        "legacy_inline_serialized_bytes": 456,
    }


def test_transport_failure_receipt_is_bounded_and_body_free() -> None:
    result = type(
        "ResultFixture",
        (),
        {
            "usage_record": {"failure_code": "result_invalid"},
            "stderr_excerpt": "diagnostic" * 100,
        },
    )()

    receipt = review_pr._transport_failure_receipt(
        classification="transport_error",
        result=result,
        exc=None,
    )

    assert receipt["provider_failure_code"] == "result_invalid"
    assert len(receipt["diagnostic"]) == 500
    assert "response" not in receipt


def test_canonical_review_response_unwraps_only_single_json_object() -> None:
    payload = '{"schema_version":"code-review-findings.v1"}'
    assert review_pr._canonical_review_response_text(f"```json\n{payload}\n```") == payload
    leading_text = f"Reviewed the exact head.\n{payload}"
    assert review_pr._canonical_review_response_text(leading_text) == payload
    wrapped_fence = f"Here is the verdict:\n```json\n{payload}\n```"
    assert review_pr._canonical_review_response_text(wrapped_fence) == payload
    trailing_text = f"{payload}\nThis is extra."
    assert review_pr._canonical_review_response_text(trailing_text) == trailing_text
    fenced_trailing_text = f"Here is the verdict:\n```json\n{payload}\n```\nThis is extra."
    assert review_pr._canonical_review_response_text(fenced_trailing_text) == fenced_trailing_text
    multiple_fences = f"First:\n```json\n{payload}\n```\n```json\n{payload}\n```"
    assert review_pr._canonical_review_response_text(multiple_fences) == multiple_fences
    long_prefix = f"{'x' * 501}\n```json\n{payload}\n```"
    assert review_pr._canonical_review_response_text(long_prefix) == long_prefix


def test_authority_terminalization_conflict_is_reported_without_traceback() -> None:
    from scripts.fleet_comms.authority import AuthorityStaleLeaseError

    class LostLeaseAuthority:
        def finish_job(self, *_args, **_kwargs):
            raise AuthorityStaleLeaseError("terminalization_conflict")

    assert review_pr._finish_authority_job_once(
        LostLeaseAuthority(),
        "job_fixture",
        worker_id="worker_fixture",
        fence_token=1,
        state="failed",
        result=b"fixture",
    ) is False


def test_routing_settlement_cleanup_race_is_reported_without_traceback() -> None:
    from scripts.fleet_comms.routing_reservations import RoutingReservationError

    class MissingReservationLedger:
        def settle(self, *_args, **_kwargs):
            raise RoutingReservationError("reservation_not_found")

    assert review_pr._settle_routing_reservation_once(
        MissingReservationLedger(),
        "reservation_fixture",
        status="cancelled",
    ) is False


def test_review_routing_budget_requires_fresh_codexbar(monkeypatch) -> None:
    from scripts.api import codexbar_usage, state_router

    observed: list[bool] = []
    refreshed: list[tuple[tuple[str, ...], float]] = []
    monkeypatch.setattr(state_router, "SUBSCRIPTION_LANES", ("kimi",))
    monkeypatch.setattr(
        state_router,
        "compute_routing_budget",
        lambda *, fresh_codexbar: observed.append(fresh_codexbar)
        or {
            "agents": {
                "kimi": {"status": "unavailable" if fresh_codexbar else "cool"}
            }
        },
    )
    monkeypatch.setattr(
        codexbar_usage,
        "refresh_provider_usage_data",
        lambda providers, *, timeout_s: refreshed.append((tuple(providers), timeout_s)) or {},
    )

    assert review_pr._compute_review_routing_budget()["agents"]["kimi"]["status"] == "cool"
    assert observed == [True, False]
    assert refreshed == [(('kimi',), 5.0)]


def test_build_review_pr_prompt_has_contract_and_cap() -> None:
    model, effort = review_pr.formal_cf_pin("codex")
    prompt = review_pr.build_review_pr_prompt(
        5443,
        reviewer="codex",
        model=model,
        effort=effort,
    )
    assert "READ-ONLY REVIEW CONTRACT" in prompt
    assert "pull/5443" in prompt
    assert "code-review-findings.v1" in prompt
    assert "gpt-5.6-terra" in prompt
    assert "effort=high" in prompt
    assert "confidence` value MUST be a JSON number" in prompt
    assert '`"P0"`, `"P1"`, `"P2"`, or `"P3"`' in prompt
    assert '`"maintainability"` invalidate' in prompt
    assert '`["none"]` when no external source applies' in prompt
    assert 'correctness":"correct"' in prompt
    assert 'enum aliases such as `"pass"`' in prompt
    assert "never add\n`claim_type` at the finding root" in prompt


def test_acpx_parser_preserves_sealed_tool_coverage_trace() -> None:
    payload = {
        "path": ".review-bundle/patch.diff",
        "sha256": "a" * 64,
        "offset": 0,
        "chunk_bytes": 3,
        "chunk_sha256": "b" * 64,
        "next_offset": 3,
        "total_bytes": 3,
        "eof": True,
        "content": "abc",
    }
    events = [
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "update": {
                    "sessionUpdate": "tool_call",
                    "toolCallId": "call-1",
                    "name": "mcp__sealed_review__read_file",
                    "rawInput": {"path": ".review-bundle/patch.diff", "offset": 0, "max_bytes": 65536},
                }
            },
        },
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "update": {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": "call-1",
                    "status": "completed",
                    "rawOutput": payload,
                }
            },
        },
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "update": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": "{}"},
                }
            },
        },
        {"jsonrpc": "2.0", "id": 2, "result": {"stopReason": "end_turn"}},
    ]

    parsed = AcpxAdapter().parse_response(
        stdout="\n".join(json.dumps(event) for event in events),
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert parsed.ok is True
    assert parsed.tool_calls == [
        {
            "id": "call-1",
            "name": "mcp__sealed_review__read_file",
            "title": "",
            "arguments": {"path": ".review-bundle/patch.diff", "offset": 0, "max_bytes": 65536},
            "result": payload,
            "status": "completed",
        }
    ]


def test_acpx_parser_normalizes_grok_use_tool_to_sealed_operation(tmp_path: Path) -> None:
    from ai_agent_bridge._review_worktree import verify_clean_review_evidence_reads

    bundle = tmp_path / ".review-bundle"
    bundle.mkdir()
    files = {
        ".review-bundle/manifest.json": b"{}",
        ".review-bundle/patch.diff": b"diff fixture",
    }
    chunks = []
    for path, content in files.items():
        (tmp_path / path).write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        chunks.append(
            {
                "path": path,
                "sha256": digest,
                "offset": 0,
                "chunk_bytes": len(content),
                "chunk_sha256": digest,
                "next_offset": len(content),
                "total_bytes": len(content),
                "eof": True,
                "content": content.decode("utf-8"),
            }
        )
    payload = {
        "required_path_count": len(chunks),
        "total_bytes": sum(len(content) for content in files.values()),
        "eof": True,
        "chunks": chunks,
    }
    grok_wrapper = {
        "type": "MCP",
        "tool_name": "read_required_all",
        "server_name": "sealed_review",
        "output": {"OkayOutput": json.dumps(payload)},
    }
    events = [
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "update": {
                    "sessionUpdate": "tool_call",
                    "toolCallId": "call-grok-1",
                    "title": "use_tool",
                    "rawInput": {
                        "tool_name": "sealed_review__read_required_all",
                        "tool_input": {},
                    },
                }
            },
        },
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "update": {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": "call-grok-1",
                    "title": "sealed_review__read_required_all",
                    "status": "completed",
                    "rawInput": {
                        "variant": "UseTool",
                        "tool_name": "sealed_review__read_required_all",
                        "tool_input": {},
                    },
                    "rawOutput": grok_wrapper,
                }
            },
        },
        {"jsonrpc": "2.0", "id": 2, "result": {"stopReason": "end_turn"}},
    ]

    parsed = AcpxAdapter().parse_response(
        stdout="\n".join(json.dumps(event) for event in events),
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert parsed.ok is True
    assert parsed.tool_calls == [
        {
            "id": "call-grok-1",
            "name": "sealed_review__read_required_all",
            "title": "sealed_review__read_required_all",
            "arguments": {},
            "result": payload,
            "status": "completed",
        }
    ]
    coverage = verify_clean_review_evidence_reads(
        parsed,
        engine="acp",
        evidence_root=tmp_path,
        changed_paths=(),
    )
    assert coverage["covered_paths"] == list(files)
    assert coverage["covered_path_count"] == 2


def test_acpx_sealed_review_confinement_allows_only_parent_reader_tools() -> None:
    command = _confinement_prefix_argv(
        "/trusted/acpx",
        Path("/private/review"),
        sealed_review_mcp_config="/private/review-config.json",
    )

    assert "--deny-all" not in command
    assert command[command.index("--mcp-config") + 1] == "/private/review-config.json"
    allowed = command[command.index("--allowed-tools") + 1].split(",")
    assert allowed == [
        "mcp__sealed_review__list_files",
        "mcp__sealed_review__read_file",
        "mcp__sealed_review__read_required",
        "mcp__sealed_review__read_required_all",
        "mcp__sealed_review__search_text",
    ]
    assert "--no-fs" in command and "--no-terminal" in command
    assert command[command.index("--max-turns") + 1] == "1"
    assert command[command.index("--prompt-retries") + 1] == "0"
    policy = json.loads(command[command.index("--permission-policy") + 1])
    assert policy["autoApprove"] == [
        *allowed,
        "sealed_review__list_files",
        "sealed_review__read_file",
        "sealed_review__read_required",
        "sealed_review__read_required_all",
        "sealed_review__search_text",
    ]
    assert policy["defaultAction"] == "deny"


def test_failure_classification_preserves_typed_acp_failure() -> None:
    result = type(
        "ResultFixture",
        (),
        {"rate_limited": False, "stalled": False, "usage_record": {"failure_code": "acp_turn_limit"}},
    )()

    assert review_pr._failure_classification(result) == "acp_turn_limit"


def test_automatic_failover_and_explicit_no_silent_provider_change() -> None:
    assert review_pr._fallback_permitted(route_mode="auto", allow_explicit_fallback=False) is True
    assert review_pr._fallback_permitted(route_mode="explicit", allow_explicit_fallback=False) is False
    assert review_pr._fallback_permitted(route_mode="explicit", allow_explicit_fallback=True) is True


def test_routing_attempt_seed_never_reuses_a_prior_authority_attempt() -> None:
    assert review_pr._routing_attempt_seed(type("Job", (), {"attempt_count": 3})()) == 3
    assert review_pr._routing_attempt_seed(type("Job", (), {"attempt_count": True})()) == 0
    assert review_pr._routing_attempt_seed(object()) == 0


def test_glm_opencode_config_exposes_only_sealed_tools_for_formal_review() -> None:
    adapter = AcpxGlmShadowAdapter()
    ordinary = json.loads(adapter._env_overrides()["OPENCODE_CONFIG_CONTENT"])
    sealed = json.loads(
        adapter._env_overrides(
            sealed_review_mcp_config="/private/review-config.json",
        )["OPENCODE_CONFIG_CONTENT"]
    )

    assert ordinary == {"permission": {"*": "deny"}, "tools": {"*": False}}
    assert sealed == {
        "permission": {"*": "deny", "sealed_review_*": "allow"},
        "tool_output": {"max_bytes": 3 * 1024 * 1024, "max_lines": 100_000},
    }


def test_acpx_parser_preserves_standard_title_without_unstable_name() -> None:
    payload = {"path": "review.txt", "content": "ok"}
    events = [
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "update": {
                    "sessionUpdate": "tool_call",
                    "toolCallId": "call-title-only",
                    "title": "Read sealed review evidence",
                    "kind": "read",
                    "rawInput": {"path": "review.txt"},
                }
            },
        },
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "update": {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": "call-title-only",
                    "status": "completed",
                    "rawOutput": payload,
                }
            },
        },
        {"jsonrpc": "2.0", "id": 2, "result": {"stopReason": "end_turn"}},
    ]

    parsed = AcpxAdapter().parse_response(
        stdout="\n".join(json.dumps(event) for event in events),
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert parsed.ok is True
    assert parsed.tool_calls == [
        {
            "id": "call-title-only",
            "name": "",
            "title": "Read sealed review evidence",
            "arguments": {"path": "review.txt"},
            "result": payload,
            "status": "completed",
        }
    ]
