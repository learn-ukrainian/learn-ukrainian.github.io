"""Tests for red-CI known-failures registry and signature-receipt stage 1 validation."""

from __future__ import annotations

import json
from typing import Any

import pytest
import yaml

from scripts.orchestration.red_ci_known_failures import (
    RedCIKnownFailuresValidationError,
    load_and_validate_receipt,
    load_and_validate_registry,
)


def _get_valid_registry_data() -> dict[str, Any]:
    return {
        "schema_version": "red-ci-known-failures.v1",
        "registry_version": "1.0.0",
        "entries": [
            {
                "id": "pytest-cache-race",
                "matcher": {
                    "check_name": {
                        "exact": "CI / Test (pytest)",
                    },
                    "lines": {
                        "required": [
                            {
                                "type": "regex",
                                "value": r"^FAILED tests/test_cache\.py::test_parallel_cache .*$",
                            }
                        ],
                        "accepted": [
                            {
                                "type": "regex",
                                "value": r"^FAILED tests/test_cache\.py::test_parallel_cache .*$",
                            }
                        ],
                        "require_full_coverage": True,
                    },
                },
                "action": {
                    "kind": "retry-once",
                },
                "owning_issue": 5885,
                "evidence": [
                    {
                        "run_id": 123456789,
                        "run_attempt": 1,
                        "pr_number": 1234,
                        "head_sha": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4",
                        "observed_at": "2026-07-28T10:00:00Z",
                        "signature_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    }
                ],
                "governance": {
                    "added_by": "developer1",
                    "added_at": "2026-07-28T10:00:00Z",
                    "added_in_pr": 6000,
                    "reviewed_by": ["reviewer1"],
                    "reviewed_at": "2026-07-28T11:00:00Z",
                    "review_by": "2026-08-27T11:00:00Z",
                },
            }
        ],
    }


def _get_valid_receipt_data() -> dict[str, Any]:
    return {
        "schema_version": "red-ci-signature-receipt.v1",
        "repository_id": 100,
        "repository_name": "learn-ukrainian",
        "pr_number": 1234,
        "run_id": 123456789,
        "run_attempt": 1,
        "head_sha": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4",
        "job_id": 987654321,
        "job_name": "test",
        "check_id": 987654321,
        "check_name": "CI / Test (pytest)",
        "normalized_signature_lines": [
            "FAILED tests/test_cache.py::test_parallel_cache - AssertError"
        ],
        "extraction_version": "1.0.0",
        "timestamp": "2026-07-28T10:00:00Z",
        "digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    }


def test_happy_path_registry(tmp_path) -> None:
    """Happy path: valid registry fixture passes validation."""
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_get_valid_registry_data()), encoding="utf-8")

    res = load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")
    assert res["ok"] is True
    assert res["entries_count"] == 1
    assert res["registry_version"] == "1.0.0"


def test_negative_duplicate_id(tmp_path) -> None:
    """Negative domain test: duplicate entry IDs cause validation failure."""
    data = _get_valid_registry_data()
    # Add a duplicate entry with the same ID
    data["entries"].append(data["entries"][0].copy())

    reg_path = tmp_path / "dup_registry.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")

    assert "Duplicate entry id" in str(exc_info.value)
    assert "pytest-cache-race" in str(exc_info.value)


def test_negative_unanchored_regex(tmp_path) -> None:
    """Negative domain test: unanchored regex matcher (missing ^ or $) is rejected."""
    data = _get_valid_registry_data()
    data["entries"][0]["matcher"]["lines"]["required"][0]["value"] = (
        r"FAILED tests/test_cache\.py::test_parallel_cache .*"
    )

    reg_path = tmp_path / "unanchored.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")

    assert "Unanchored regex" in str(exc_info.value)
    assert "pytest-cache-race" in str(exc_info.value)


def test_negative_substring_style_matcher(tmp_path) -> None:
    """Negative domain test: substring-style regex matcher (unanchored at start or end) is rejected."""
    data = _get_valid_registry_data()

    # Missing end anchor $
    data["entries"][0]["matcher"]["lines"]["required"][0]["value"] = (
        r"^FAILED tests/test_cache\.py::test_parallel_cache"
    )

    reg_path = tmp_path / "substring.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")

    assert "Unanchored regex" in str(exc_info.value)


def test_negative_missing_evidence(tmp_path) -> None:
    """Negative schema test: entry with empty evidence array fails schema validation."""
    data = _get_valid_registry_data()
    data["entries"][0]["evidence"] = []

    reg_path = tmp_path / "no_evidence.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")

    assert "Registry schema violation" in str(exc_info.value)


def test_negative_missing_governance(tmp_path) -> None:
    """Negative schema test: entry missing governance object fails schema validation."""
    data = _get_valid_registry_data()
    del data["entries"][0]["governance"]

    reg_path = tmp_path / "no_gov.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")

    assert "Registry schema violation" in str(exc_info.value)


def test_negative_stop_without_stop_code(tmp_path) -> None:
    """Negative schema test: kind 'stop' without stop_code or 'retry-once' with stop_code fails schema validation."""
    data = _get_valid_registry_data()
    data["entries"][0]["action"] = {"kind": "stop"}

    reg_path = tmp_path / "stop_no_code.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")

    assert "Registry schema violation" in str(exc_info.value)


def test_negative_retry_once_with_stop_code(tmp_path) -> None:
    """Negative schema test: 'retry-once' carrying a stop_code fails schema validation
    (split from the stop-without-code case — one test, one invariant)."""
    data2 = _get_valid_registry_data()
    data2["entries"][0]["action"] = {"kind": "retry-once", "stop_code": "STOP-ci-red"}

    reg_path2 = tmp_path / "retry_with_code.json"
    reg_path2.write_text(json.dumps(data2), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info2:
        load_and_validate_registry(reg_path2, as_of="2026-07-28T12:00:00Z")

    assert "Registry schema violation" in str(exc_info2.value)


def test_yaml_unquoted_timestamps_validate(tmp_path) -> None:
    """codex F001: a normal YAML registry with UNQUOTED ISO timestamps must
    validate — PyYAML's implicit timestamp coercion would hand datetime objects
    to the string-typed schema and reject the documented format."""
    data = _get_valid_registry_data()
    reg_path = tmp_path / "unquoted.yaml"
    yaml_text = yaml.safe_dump(data, default_flow_style=False)
    # safe_dump quotes nothing datetime-like here (values are strings), so
    # strip quotes around timestamps to force the unquoted form PyYAML coerces.
    yaml_text = yaml_text.replace("'2026-", "2026-").replace("Z'", "Z")
    assert "'" not in yaml_text.split("added_at:")[1].splitlines()[0]
    reg_path.write_text(yaml_text, encoding="utf-8")

    res = load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")
    assert res["ok"] is True


def test_negative_malformed_regex(tmp_path) -> None:
    """Negative domain test (codex F001): an anchored but syntactically invalid
    regex (e.g. '^($') must fail at VALIDATION time, not detonate when the
    registry is consumed."""
    data = _get_valid_registry_data()
    data["entries"][0]["matcher"]["lines"]["required"][0] = {"type": "regex", "value": "^($"}

    reg_path = tmp_path / "malformed_regex.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")

    assert "Malformed regex" in str(exc_info.value)


def test_negative_empty_required_matchers(tmp_path) -> None:
    """Negative schema test (codex re-review F001): an entry whose
    matcher.lines.required is EMPTY would match on check_name alone, classifying
    every failure of that check as known — minItems 1 must reject it."""
    data = _get_valid_registry_data()
    data["entries"][0]["matcher"]["lines"]["required"] = []

    reg_path = tmp_path / "empty_required.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")

    assert "Registry schema violation" in str(exc_info.value)


def test_negative_receipt_empty_signature_lines(tmp_path) -> None:
    """Negative schema test: a receipt with zero normalized signature lines is not a
    signature (glm F3) — minItems 1 must reject it."""
    data = _get_valid_receipt_data()
    data["normalized_signature_lines"] = []

    rec_path = tmp_path / "empty_lines.json"
    rec_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError):
        load_and_validate_receipt(rec_path)


def test_negative_expired_entry(tmp_path) -> None:
    """Negative domain test: expired entry (review_by < as_of) fails validation."""
    data = _get_valid_registry_data()
    data["entries"][0]["governance"]["review_by"] = "2026-08-01T00:00:00Z"

    reg_path = tmp_path / "expired.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-08-02T00:00:00Z")

    assert "expired at review_by" in str(exc_info.value)
    assert "pytest-cache-race" in str(exc_info.value)


def test_mixed_timezone_instants_compared_correctly(tmp_path) -> None:
    """Mixed Z/offset ISO timestamps are compared by instant, not string ordering.

    Case:
      review_by = "2026-07-28T12:00:00+02:00"  (10:00:00 UTC)
      as_of     = "2026-07-28T11:00:00Z"       (11:00:00 UTC)

    String comparison: "2026-07-28T12:00:00+02:00" < "2026-07-28T11:00:00Z" is False.
    Instant comparison: 10:00 UTC < 11:00 UTC is True (entry IS expired).

    Instant comparison must catch this expiration.
    """
    data = _get_valid_registry_data()
    data["entries"][0]["governance"]["review_by"] = "2026-07-28T12:00:00+02:00"

    reg_path = tmp_path / "tz_instant.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T11:00:00Z")

    assert "expired at review_by" in str(exc_info.value)


def test_happy_path_receipt(tmp_path) -> None:
    """Happy path: valid signature receipt fixture passes validation."""
    rcpt_path = tmp_path / "receipt.json"
    rcpt_path.write_text(json.dumps(_get_valid_receipt_data()), encoding="utf-8")

    res = load_and_validate_receipt(rcpt_path)
    assert res["ok"] is True
    assert res["head_sha"] == "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4"
    assert len(res["digest"]) == 64


def test_negative_receipt_bad_hex(tmp_path) -> None:
    """Negative test: receipt with bad hex in head_sha or digest fails validation."""
    data = _get_valid_receipt_data()
    data["head_sha"] = "A1B2C3D4E5F67890A1B2C3D4E5F67890A1B2C3D4"  # uppercase

    rcpt_path = tmp_path / "bad_sha.json"
    rcpt_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_receipt(rcpt_path)

    assert "head_sha" in str(exc_info.value) or "Signature receipt schema violation" in str(exc_info.value)

    # Bad digest length
    data2 = _get_valid_receipt_data()
    data2["digest"] = "12345"

    rcpt_path2 = tmp_path / "bad_digest.json"
    rcpt_path2.write_text(json.dumps(data2), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info2:
        load_and_validate_receipt(rcpt_path2)

    assert "digest" in str(exc_info2.value) or "Signature receipt schema violation" in str(exc_info2.value)
