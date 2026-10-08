"""Private policy/public projection regression controls for #10154.

Synthetic component controls only; the driver's independent 40-case oracle is
withheld and is not executed here. Original test collection is frozen separately.
"""

from __future__ import annotations

import copy
import json
import os
import traceback
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.fleet import router_policy as policy

NOW = "2035-01-01T00:00:00Z"
SENTINEL = "PRIVATE_SENTINEL_TOKEN_AND_PATH"


def document():
    return {
        "schema_version": policy.SCHEMA_VERSION, "policy_epoch": 1,
        "campaigns": [{"id": "campaign", "models": ["gpt-6.1-sol"], "lanes": ["codex"],
                       "starts_at": NOW, "expires_at": "2035-01-01T01:00:00Z"}],
        "window_metadata": [{"id": "window", "starts_at": NOW,
                             "resets_at": "2035-01-01T01:00:00Z", "duration_seconds": 3600}],
    }


def test_load_retains_complete_private_policy_and_defaults_spend_off(tmp_path):
    path = tmp_path / "policy.json"
    original = document()
    path.write_text(json.dumps(original))
    for clock in (NOW, "2035-01-01T01:00:00Z", "2034-01-01T00:00:00Z"):
        loaded = policy.load_policy(path, now=clock)
        assert loaded == {**original, "manual_spend_authorization": {"enabled": False}}
    assert json.loads(path.read_text()) == original
    original["manual_spend_authorization"] = {"enabled": True}
    path.write_text(json.dumps(original))
    assert policy.load_policy(path, now=NOW) == original


@pytest.mark.parametrize("mutation", [
    "unknown", "nested_secret", "wrong_version", "bool_epoch", "empty_scope", "override",
    "duplicate_id", "reverse_time", "naive_time", "bad_time", "bad_spend", "bad_window", "array", "unknown_model", "unknown_lane",
])
def test_policy_closed_schema_failures_are_content_free(tmp_path, mutation):
    value = document()
    campaign = value["campaigns"][0]
    if mutation == "unknown":
        value[SENTINEL] = SENTINEL
    elif mutation == "nested_secret":
        campaign["token"] = SENTINEL
    elif mutation == "wrong_version":
        value["schema_version"] = SENTINEL
    elif mutation == "bool_epoch":
        value["policy_epoch"] = True
    elif mutation == "empty_scope":
        campaign.pop("models")
        campaign.pop("lanes")
    elif mutation == "override":
        campaign["override_hard_rules"] = True
    elif mutation == "duplicate_id":
        value["campaigns"].append(copy.deepcopy(campaign))
    elif mutation == "reverse_time":
        campaign["expires_at"] = NOW
    elif mutation == "naive_time":
        campaign["starts_at"] = "2035-01-01T00:00:00"
    elif mutation == "bad_time":
        campaign["starts_at"] = "2035-99-01T00:00:00Z"
    elif mutation == "bad_spend":
        value["manual_spend_authorization"] = {"enabled": True, "api_key": SENTINEL}
    elif mutation == "bad_window":
        value["window_metadata"][0]["resets_at"] = NOW
    elif mutation == "unknown_model":
        campaign["models"] = [SENTINEL]
    elif mutation == "unknown_lane":
        campaign["lanes"] = [SENTINEL]
    else:
        value = []
    path = tmp_path / SENTINEL
    path.write_text(json.dumps(value))
    with pytest.raises(policy.RouterPolicyError) as error:
        policy.load_policy(path, now=NOW)
    assert str(error.value) == "POLICY_INVALID"
    assert SENTINEL not in "".join(traceback.format_exception(error.value))


@pytest.mark.parametrize("raw", ["{", '{"schema_version":1,"schema_version":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e309}', b"\xff", '"private"'])
def test_malformed_json_fails_closed(tmp_path, raw):
    path = tmp_path / SENTINEL
    path.write_bytes(raw if isinstance(raw, bytes) else raw.encode())
    with pytest.raises(policy.RouterPolicyError, match="POLICY_INVALID"):
        policy.load_policy(path, now=NOW)


@pytest.mark.parametrize("kind", ["missing", "leaf_link", "parent_link", "directory", "fifo", "large", "control", "parent", "denied"])
def test_unsafe_path_refusals_hide_os_errors(tmp_path, monkeypatch, kind):
    path = tmp_path / SENTINEL
    real = tmp_path / "real"
    real.mkdir()
    (real / "policy.json").write_text(json.dumps(document()))
    if kind == "leaf_link":
        path.symlink_to(real / "policy.json")
    elif kind == "parent_link":
        path.symlink_to(real, target_is_directory=True)
        path = path / "policy.json"
    elif kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "large":
        path.write_bytes(b"x" * (policy.MAX_POLICY_BYTES + 1))
    elif kind == "control":
        path = str(path) + "\n"
    elif kind == "parent":
        path = f"{real}/../{SENTINEL}"
    elif kind == "denied":
        def denied(*args, **kwargs):
            raise PermissionError(SENTINEL)
        monkeypatch.setattr(policy.os, "open", denied)
    with pytest.raises(policy.RouterPolicyError) as error:
        policy.load_policy(path, now=NOW)
    assert SENTINEL not in "".join(traceback.format_exception(error.value))


def test_relative_reader_and_growing_file_are_bounded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("policy.json").write_text(json.dumps(document()))
    assert policy.load_policy("policy.json", now=NOW)["policy_epoch"] == 1
    monkeypatch.setattr(policy.os, "read", lambda _fd, size: b"x" * size)
    with pytest.raises(policy.RouterPolicyError, match="POLICY_UNSAFE"):
        policy.read_private_bytes("policy.json", limit=3)


def test_closed_public_decision_and_schema():
    raw = {
        "status": "selected", "code": "SELECTED", "model": "gpt-6.1-sol", "family": "openai",
        "harness": "codex", "transport": "native_codex", "effort": "high",
        "target_sha": "a" * 40, "policy_sha256": "b" * 64, "observed_at": NOW,
        "rule_ids": ["SELECTED", SENTINEL],
        "trace": {"evidence": SENTINEL}, "quota": {"reason": SENTINEL},
        "private_policy": document(), "exception": SENTINEL,
    }
    output = policy.public_decision(raw)
    assert output["model"] == "gpt-6.1-sol"
    assert output["rule_ids"] == ["SELECTED"]
    assert SENTINEL not in json.dumps(output)
    schema = json.loads(Path("schemas/model-router-receipt.schema.json").read_text())
    Draft202012Validator(schema).validate(output)
    assert not Draft202012Validator(schema).is_valid({**output, "trace": {}})
    for key in ("model", "family", "harness", "code", "status", "effort", "observed_at", "target_sha"):
        unsafe = policy.public_decision({key: {"secret": SENTINEL}})
        assert SENTINEL not in json.dumps(unsafe)
    assert policy.public_decision(None)["status"] == "unknown"


def test_catalog_failure_remains_unknown(monkeypatch):
    def unavailable(_signature):
        raise OSError(SENTINEL)
    monkeypatch.setattr(policy, "_public_identity_sets", unavailable)
    assert policy.public_identity("gpt-6.1-sol") is None


def test_scalar_validators_and_closed_legacy_record():
    assert policy.timestamp(datetime(2035, 1, 1, tzinfo=UTC)) == NOW
    for raw in (None, "2035-01-01", "2035-01-01T01:00:00+01:00", SENTINEL):
        assert policy.timestamp(raw) is None
    for raw in (True, float("nan"), float("inf"), -1, SENTINEL):
        assert policy.finite_number(raw) is None
    assert policy.finite_number(0) == 0
    record = policy.public_routing_record({
        "authority_key": SENTINEL, "trace": {"nested": SENTINEL}, "evidence": {"reason": SENTINEL},
        "requested": {"role": "review", "risk": "critical", "route_mode": "auto"},
        "retry": {"attempt": 0, "failure_classification": SENTINEL},
        "lifecycle": {"status": "complete", "settled_at": NOW}, "event_history": [None, {"state": "complete"}],
        "latest_event": None, "automatic": True, "duration_s": float("nan"), "unknown": SENTINEL,
    })
    assert SENTINEL not in json.dumps(record)
    assert record["retry"]["failure_classification"] is None
    assert record["requested"]["risk"] == "critical"
    assert policy.public_routing_record(record) == record


def test_policy_schema_dependency_and_invalid_clock_fail_closed(tmp_path, monkeypatch):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(document()))
    with pytest.raises(policy.RouterPolicyError, match="POLICY_INVALID"):
        policy.load_policy(path, now=SENTINEL)
    monkeypatch.setattr(policy, "_SCHEMA", tmp_path / "missing")
    with pytest.raises(policy.RouterPolicyError, match="POLICY_INVALID"):
        policy.load_policy(path, now=NOW)


def test_strict_json_keeps_finite_float():
    assert policy.strict_json('{"reading":1.25}') == {"reading": 1.25}
