"""Tests for pointer-only review-pr entrypoint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from agent_runtime.adapters.acpx import (
    AcpxAdapter,
    AcpxGlmShadowAdapter,
    _confinement_prefix_argv,
)
from ai_agent_bridge import _review_pr as review_pr
from ai_agent_bridge._review_safety import ReviewSafetyError


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
    assert command[command.index("--max-turns") + 1] == "3"
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
