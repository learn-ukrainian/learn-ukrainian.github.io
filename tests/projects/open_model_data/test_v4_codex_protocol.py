"""Codex protocol evidence and refusal cases; no provider or linguistic claims."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from learn_ukrainian_v4_runtime.child_runtime import (
    CapturedChild,
    _CodexProtocol,
    parse_child,
)
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, canonical_bytes, digest


def binding():
    return {"request_id": "fixture-request", "expected_harness": "codex",
            "expected_seat_or_model": "gpt-6-astra", "role": "reviewer",
            "prompt_sha256": digest(b"fixture prompt")}


def events():
    return [
        {"id": 1, "result": {"userAgent": "fixture"}},
        {"method": "remoteControl/status/changed", "params": {"status": "disabled"}},
        {"id": 2, "result": {"model": "gpt-6-astra", "modelProvider": "openai",
            "approvalPolicy": "never", "cwd": "/work", "sandbox": {"type": "readOnly"},
            "thread": {"id": "fixture-thread"}}},
        {"id": 3, "result": {"data": [{"name": "sources", "tools": {
            name: {} for name in ("verify_word", "verify_words", "verify_lemma", "verify_stress", "check_modern_form")
        }}], "nextCursor": None}},
        {"id": 4, "result": {"turn": {"id": "fixture-turn", "status": "inProgress"}}},
        {"method": "item/completed", "params": {"threadId": "fixture-thread", "turnId": "fixture-turn",
            "item": {"type": "agentMessage", "id": "fixture-message", "text": "V4-REVIEW-VERDICT: PASS"}}},
        {"method": "turn/completed", "params": {"threadId": "fixture-thread",
            "turn": {"id": "fixture-turn", "status": "completed", "error": None}}},
    ]


def capture(rows, *, returncode=0):
    return CapturedChild("fixture-request", "fixture-attempt", "a" * 64, binding()["prompt_sha256"],
                         b"".join(canonical_bytes(row) + b"\n" for row in rows), b"", returncode, "codex")


def test_resolved_model_sources_inventory_and_same_turn_produce_review():
    result = parse_child(capture(events()), binding())
    assert result == {"model": "gpt-6-astra", "session_id": "fixture-thread",
                      "response": "V4-REVIEW-VERDICT: PASS", "verdict": "PASS"}


@pytest.mark.parametrize("mutation", [
    "model", "missing_model", "provider", "sandbox", "approval", "cwd", "remote",
    "missing_remote", "missing_tool", "extra_server", "pagination", "thread",
    "turn", "failed", "error", "reroute", "duplicate_response", "duplicate_message",
    "deltas_only", "missing_completion", "duplicate_completion", "out_of_order",
])
def test_identity_capability_and_terminal_failures_refuse(mutation):
    rows = deepcopy(events())
    header = rows[2]["result"]
    if mutation == "model":
        header["model"] = "other-model"
    elif mutation == "missing_model":
        del header["model"]
    elif mutation == "provider":
        header["modelProvider"] = "other-provider"
    elif mutation == "sandbox":
        header["sandbox"]["type"] = "dangerFullAccess"
    elif mutation == "approval":
        header["approvalPolicy"] = "on-request"
    elif mutation == "cwd":
        header["cwd"] = "/elsewhere"
    elif mutation == "remote":
        rows[1]["params"]["status"] = "connected"
    elif mutation == "missing_remote":
        rows.pop(1)
    elif mutation == "missing_tool":
        del rows[3]["result"]["data"][0]["tools"]["verify_stress"]
    elif mutation == "extra_server":
        rows[3]["result"]["data"].append({"name": "other", "tools": {}})
    elif mutation == "pagination":
        rows[3]["result"]["nextCursor"] = "more"
    elif mutation == "thread":
        rows[5]["params"]["threadId"] = "other-thread"
    elif mutation == "turn":
        rows[5]["params"]["turnId"] = "other-turn"
    elif mutation == "failed":
        rows[6]["params"]["turn"]["status"] = "failed"
    elif mutation in ("error", "reroute"):
        rows.insert(5, {"method": "error" if mutation == "error" else "model/rerouted",
                        "params": {"threadId": "fixture-thread", "turnId": "fixture-turn"}})
    elif mutation == "duplicate_response":
        rows.insert(3, deepcopy(rows[2]))
    elif mutation == "duplicate_message":
        rows.insert(6, deepcopy(rows[5]))
    elif mutation == "deltas_only":
        rows[5] = {"method": "item/agentMessage/delta", "params": {
            "threadId": "fixture-thread", "turnId": "fixture-turn", "delta": "V4-REVIEW-VERDICT: PASS"}}
    elif mutation == "missing_completion":
        rows.pop()
    elif mutation == "duplicate_completion":
        rows.append(deepcopy(rows[-1]))
    else:
        rows[3], rows[4] = rows[4], rows[3]
    with pytest.raises(OperationRefused):
        parse_child(capture(rows), binding())


def test_stock_exec_jsonl_cannot_claim_resolved_model():
    rows = [{"type": "thread.started", "thread_id": "fixture-thread", "model": "gpt-6-astra"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "V4-REVIEW-VERDICT: PASS"}},
            {"type": "turn.completed", "usage": {}}]
    with pytest.raises(OperationRefused):
        parse_child(capture(rows), binding())


def test_nonzero_exit_refuses_even_with_complete_protocol():
    with pytest.raises(OperationRefused, match="child_unsuccessful"):
        parse_child(capture(events(), returncode=1), binding())


def test_byte_fragmented_protocol_preserves_capture_and_fixed_request_order():
    protocol = _CodexProtocol(binding(), "fixture prompt")
    outgoing = bytearray(protocol.initial())
    raw = capture(events()).stdout
    for byte in raw:
        outgoing.extend(protocol.feed(bytes([byte])))
    requests = [json.loads(line) for line in outgoing.splitlines()]
    assert [row["method"] for row in requests] == [
        "initialize", "initialized", "thread/start", "mcpServerStatus/list", "turn/start"]
    assert requests[-1]["params"]["input"] == [{"type": "text", "text": "fixture prompt"}]
    assert requests[-1]["params"]["threadId"] == "fixture-thread"
    assert protocol.result()["model"] == "gpt-6-astra"


def test_server_request_is_rejected_without_echoing_arguments_and_never_passes():
    protocol = _CodexProtocol(binding())
    request = {"id": 77, "method": "item/commandExecution/requestApproval",
               "params": {"arguments": "must-not-echo"}}
    response = protocol.feed(canonical_bytes(request) + b"\n")
    assert b"must-not-echo" not in response
    assert json.loads(response)["error"]["code"] == -32601
    assert protocol.finished
    with pytest.raises(OperationRefused):
        protocol.result()


def test_unterminated_json_record_is_not_terminal_evidence():
    raw = capture(events())
    damaged = CapturedChild(raw.request_id, raw.attempt_id, raw.argv_sha256, raw.prompt_sha256,
                            raw.stdout.rstrip(b"\n"), raw.stderr, 0, raw.harness)
    with pytest.raises(OperationRefused):
        parse_child(damaged, binding())


@pytest.mark.parametrize("request_id", [None, True, [], {}, "", "x" * 257])
def test_invalid_server_request_identifier_is_not_echoed(request_id):
    with pytest.raises(OperationRefused, match="child_event_invalid"):
        _CodexProtocol(binding()).feed(canonical_bytes({
            "id": request_id, "method": "item/commandExecution/requestApproval", "params": {},
        }) + b"\n")


def test_missing_native_tool_runner_warning_refuses():
    rows = events()
    rows.insert(3, {"method": "warning", "params": {
        "message": "Code Mode is unavailable because the host executable was not found",
    }})
    with pytest.raises(OperationRefused, match="child_sources_tools_unavailable"):
        parse_child(capture(rows), binding())


def test_recorded_native_protocol_projection_matches_actual_event_order():
    # Actual 0.153.4 stdio controls, with opaque IDs mapped and payload bodies
    # omitted. This records wire shape/order, not a linguistic or provider proof.
    rows = json.loads(Path(__file__).with_name("_v4_codex_recorded_protocol.json").read_text())
    result = parse_child(capture(rows), binding())
    assert result["model"] == "gpt-6-astra"
    assert result["verdict"] == "PASS"
    calls = [row["params"]["item"] for row in rows if row.get("method") == "item/completed"
             and row["params"]["item"]["type"] == "mcpToolCall"]
    assert len(calls) == 1
    assert (calls[0]["server"], calls[0]["tool"], calls[0]["status"]) == ("sources", "verify_word", "completed")


@pytest.mark.parametrize("raw", [b"not-json-secret\n", b"\xffinvalid-utf8\n", b"[" * 20000 + b"\n"])
def test_malformed_child_bytes_are_not_chained_into_public_refusal(raw):
    with pytest.raises(OperationRefused, match="child_capture_invalid") as error:
        _CodexProtocol(binding()).feed(raw)
    assert error.value.__cause__ is None
    assert error.value.__suppress_context__ is True
