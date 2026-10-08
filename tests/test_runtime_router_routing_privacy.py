"""Exercise actual Runtime serializers and HTTP routing boundary (#10154)."""

from __future__ import annotations

import json
import sqlite3
import types

import pytest
from fastapi.testclient import TestClient

from scripts.api import runtime_router as runtime
from scripts.api.main import app
from scripts.fleet.router_policy import opaque_id

SENTINEL = "PRIVATE_RUNTIME_ROUTING_SENTINEL"


def row():
    nested = {"trace": {"evidence": {"quota": {"reason": {"exception": SENTINEL}}}}}
    return {
        "decision_id": "decision", "reservation_id": "reservation", "authority_key": SENTINEL,
        "event_type": "settled", "state": "failed", "created_at": "2035-01-01T00:00:10Z",
        "reason": SENTINEL, "evidence": nested,
        "requested": {"initiator": SENTINEL, "author_model": "gpt-6.1-sol", "author_family": "openai",
                      "role": "review", "profile": "code", "risk": "critical", "route_mode": "auto"},
        "resolved": {"model": "claude-opus-5-5", "family": "anthropic", "route": "claude",
                     "trace": {"gates": nested, "substitution_note": SENTINEL}},
        "quota": {"bucket": SENTINEL, "credential_bucket": SENTINEL, "snapshot": nested,
                  "freshness": nested, "headroom_band": nested},
        "retry": {"reason": SENTINEL, "exception": nested, "attempt": 1},
        "replay": {"authority_key": SENTINEL, "idempotency_key": SENTINEL, "completed": False},
        "lifecycle": {"status": "failed", "started_at": "2035-01-01T00:00:00Z",
                      "settled_at": "2035-01-01T00:00:10Z", "failure_classification": SENTINEL},
        "cache": nested, "retry_chain": nested, "failover_chain": nested,
    }


def test_actual_assignment_event_reason_and_aggregate_projection():
    record = row()
    item = runtime._routing_assignment_item(record)
    assert SENTINEL not in json.dumps(item)
    assert item["resolved_model"] == "claude-opus-5-5"
    assert item["source_authority_id"] == opaque_id("reservation")
    assert item["selection_trace"] is None
    assert item["retry_chain"] is None
    assert item["duration_s"] == 10
    assert runtime._routing_selection_reason(record) is None
    assert runtime._routing_event_item(record)["event_type"] == "settled"
    assert runtime._routing_capacity_evidence([record], record["quota"]["snapshot"]) is None
    aggregate = runtime._routing_assignment_aggregate([record])
    assert SENTINEL not in json.dumps(aggregate)
    assert aggregate["current_state"] == "failed"
    assert aggregate["latest_event"]["state"] == "failed"
    assert aggregate["event_count"] == 1


@pytest.mark.parametrize("field", ["selection_reason", "reason", "evidence", "requested", "resolved", "quota", "lifecycle", "retry", "replay", "event_type", "automatic", "state", "duration_s"])
def test_malformed_nested_shapes_cannot_leak_or_break_serializer(field):
    record = row()
    record[field] = {"private": SENTINEL}
    assert SENTINEL not in json.dumps(runtime._routing_assignment_item(record))
    assert SENTINEL not in json.dumps(runtime._routing_assignment_aggregate([record]))


@pytest.mark.parametrize("state", ["complete", "failed", "running"])
def test_actual_http_output_has_closed_privacy_boundary(monkeypatch, state):
    record = row()
    record["state"] = record["lifecycle"]["status"] = state
    monkeypatch.setattr(runtime.importlib, "import_module", lambda _name: types.SimpleNamespace(list_routing_decisions=lambda **kwargs: [record]))
    monkeypatch.setattr(runtime, "_routing_plane_status", lambda *args: {"mode": "authority"})
    response = TestClient(app).get("/api/runtime/routing-assignments")
    assert response.status_code == 200
    assert SENTINEL not in response.text
    assert response.json()["assignments"][0]["current_state"] == state


@pytest.mark.parametrize("exception", [sqlite3.OperationalError(SENTINEL), ValueError(SENTINEL), RuntimeError(SENTINEL)])
def test_actual_reader_failure_does_not_echo_exception(monkeypatch, exception):
    def fail(**kwargs):
        raise exception
    monkeypatch.setattr(runtime.importlib, "import_module", lambda _name: types.SimpleNamespace(list_routing_decisions=fail))
    monkeypatch.setattr(runtime, "_routing_plane_status", lambda *args: {"mode": "authority"})
    response = TestClient(app).get("/api/runtime/routing-assignments")
    assert response.status_code == 200
    assert response.json()["availability"] == "unavailable"
    assert SENTINEL not in response.text


def test_typed_reason_codes_survive_and_arbitrary_evidence_does_not():
    assert runtime._routing_selection_reason({"reason": "CAPACITY_UNKNOWN"}) == "CAPACITY_UNKNOWN"
    assert runtime._routing_selection_reason({"event_type": "reserved", "evidence": {"reason": SENTINEL}}) is None
    assert runtime._routing_selection_reason({"event_type": "settled", "evidence": {"reason": "SELECTED"}}) is None


@pytest.mark.parametrize("raw", [{"mode": SENTINEL, "enabled": SENTINEL}, {"mode": "authority", "enabled": True}])
def test_plane_projection_has_typed_mode_and_enabled(monkeypatch, raw):
    monkeypatch.setattr(runtime, "read_plane_status", lambda **kwargs: raw)
    result = runtime._routing_plane_status()
    assert SENTINEL not in json.dumps(result)
    if raw["mode"] == SENTINEL:
        assert result["mode"] == "unavailable"
        assert result["authority"] == "unknown"
        assert result["enabled"] is False
    else:
        assert result["authority"] == "fleet_comms_authoritative"


def test_plane_exception_is_unknown_without_private_detail(monkeypatch):
    def unavailable(**kwargs):
        raise OSError(SENTINEL)
    monkeypatch.setattr(runtime, "read_plane_status", unavailable)
    result = runtime._routing_plane_status()
    assert result["authority"] == "unknown"
    assert SENTINEL not in json.dumps(result)


def test_explicit_automatic_boolean_is_preserved():
    record = row()
    record["automatic"] = False
    assert runtime._routing_assignment_item(record)["automatic"] is False
