"""Tests for red-CI known-failures registry and signature-receipt stage 1 validation."""

from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.orchestration.red_ci_known_failures import (
    RedCIKnownFailuresValidationError,
    aggregate_lookup_results,
    compute_signature_digest,
    extract_signature_receipt,
    load_and_validate_receipt,
    load_and_validate_registry,
    main,
)
from tests.project_python import project_python

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
        "digest": compute_signature_digest(
            ["FAILED tests/test_cache.py::test_parallel_cache - AssertError"]
        ),
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


def test_negative_unpublished_stop_code(tmp_path) -> None:
    """codex F001: a stop entry with a code outside the published STOP-code
    contract (e.g. a typo) must fail validation — consumers cannot interpret it."""
    data = _get_valid_registry_data()
    data["entries"][0]["action"] = {"kind": "stop", "stop_code": "STOP-typo"}

    reg_path = tmp_path / "bad_stop_code.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")

    assert "Unknown stop_code" in str(exc_info.value)


def test_stop_entry_with_published_code_validates(tmp_path) -> None:
    """Positive twin: a stop entry using a published code passes."""
    data = _get_valid_registry_data()
    data["entries"][0]["action"] = {"kind": "stop", "stop_code": "STOP-manual-intervention"}

    reg_path = tmp_path / "good_stop_code.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    res = load_and_validate_registry(reg_path, as_of="2026-07-28T12:00:00Z")
    assert res["ok"] is True


def test_negative_naive_datetime_as_of(tmp_path) -> None:
    """codex F001: a NAIVE datetime as_of must be rejected like naive strings —
    silently assuming UTC evaluates expiry at the wrong instant for local-time
    callers."""
    from datetime import datetime as _dt

    data = _get_valid_registry_data()
    reg_path = tmp_path / "naive_asof.json"
    reg_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError) as exc_info:
        load_and_validate_registry(reg_path, as_of=_dt(2026, 7, 28, 12, 0, 0))

    assert "timezone-aware" in str(exc_info.value)


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


def _write_json(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _lookup_args(
    registry_path: Path,
    receipt_path: Path,
    output_path: Path,
    *,
    repository_id: str = "100",
    pr: int = 1234,
    run_id: int = 123456789,
    as_of: str = "2026-07-28T12:00:00Z",
) -> list[str]:
    return [
        "lookup",
        "--registry",
        str(registry_path),
        "--receipt",
        str(receipt_path),
        "--repository-id",
        repository_id,
        "--pr",
        str(pr),
        "--run-id",
        str(run_id),
        "--as-of",
        as_of,
        "--output",
        str(output_path),
    ]


def _write_lookup_inputs(tmp_path: Path) -> tuple[Path, Path]:
    registry_path = _write_json(tmp_path / "registry.json", _get_valid_registry_data())
    receipt_path = _write_json(tmp_path / "receipt.json", _get_valid_receipt_data())
    return registry_path, receipt_path


def test_extract_signature_receipt_only_strips_ansi_and_normalizes_crlf() -> None:
    """Extraction preserves case and whitespace while producing a bound digest."""
    source = {
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
        "extraction_version": "1.0.0",
        "timestamp": "2026-07-28T10:00:00Z",
        "raw_signature_lines": [
            "\x1b[31mFAILED TeSt  keep  spaces\x1b[0m\r\nsecond line",
        ],
    }

    receipt = extract_signature_receipt(source)

    assert receipt["normalized_signature_lines"] == [
        "FAILED TeSt  keep  spaces",
        "second line",
    ]
    assert receipt["digest"] == compute_signature_digest(receipt["normalized_signature_lines"])


def test_extract_cli_writes_a_valid_signature_receipt(tmp_path, capsys) -> None:
    """The receipt CLI is file-only and leaves no actionable stdout."""
    source = {
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
        "extraction_version": "1.0.0",
        "timestamp": "2026-07-28T10:00:00Z",
        "raw_signature_lines": ["FAILED tests/test_cache.py::test_parallel_cache - AssertError"],
    }
    input_path = _write_json(tmp_path / "source.json", source)
    output_path = tmp_path / "receipt.json"

    rc = main(["extract", "--input", str(input_path), "--output", str(output_path)])

    assert rc == 0
    assert capsys.readouterr().out == ""
    assert json.loads(output_path.read_text(encoding="utf-8"))["schema_version"] == "red-ci-signature-receipt.v1"


def test_extract_rejects_non_string_source_field_names() -> None:
    """Malformed YAML mapping keys cannot bypass structured-source validation."""
    with pytest.raises(RedCIKnownFailuresValidationError, match="fields must all be strings"):
        extract_signature_receipt({1: "not-a-valid-source"})


def test_negative_receipt_digest_must_bind_signature_lines(tmp_path) -> None:
    """A valid-looking hash for different text cannot authorize a lookup."""
    data = _get_valid_receipt_data()
    data["normalized_signature_lines"].append("additional unknown failure")
    receipt_path = _write_json(tmp_path / "wrong-digest.json", data)

    with pytest.raises(RedCIKnownFailuresValidationError, match="does not bind"):
        load_and_validate_receipt(receipt_path)


def test_lookup_cli_matched_writes_quoted_receipt(tmp_path, capsys) -> None:
    """Exit 0 writes the exact matched receipt contract, not stdout action data."""
    registry_path, receipt_path = _write_lookup_inputs(tmp_path)
    output_path = tmp_path / "lookup.json"

    rc = main(_lookup_args(registry_path, receipt_path, output_path))

    assert rc == 0
    assert capsys.readouterr().out == ""
    lookup_receipt = json.loads(output_path.read_text(encoding="utf-8"))
    assert lookup_receipt["status"] == "matched"
    assert lookup_receipt["entry_id"] == "pytest-cache-race"
    assert lookup_receipt["action"] == {"kind": "retry-once"}
    assert lookup_receipt["as_of_epoch"] == 1785240000


def test_lookup_cli_no_match_is_successful_table_unknown(tmp_path, capsys) -> None:
    """Exit 0 is also correct for a valid no-match receipt."""
    registry_path, receipt_path = _write_lookup_inputs(tmp_path)
    receipt = _get_valid_receipt_data()
    receipt["check_name"] = "CI / unrelated"
    _write_json(receipt_path, receipt)
    output_path = tmp_path / "lookup.json"

    rc = main(_lookup_args(registry_path, receipt_path, output_path))

    assert rc == 0
    assert capsys.readouterr().out == ""
    assert json.loads(output_path.read_text(encoding="utf-8")) == {
        "reason": "no-match",
        "schema_version": "red-ci-lookup-receipt.v1",
        "status": "table-unknown",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(
            lambda registry, receipt: registry.clear(), id="malformed-registry"
        ),
        pytest.param(
            lambda registry, receipt: receipt.update({"schema_version": "receipt.v2"}),
            id="unsupported-receipt-schema",
        ),
        pytest.param(
            lambda registry, receipt: registry["entries"][0]["matcher"]["lines"][
                "required"
            ][0].update({"value": "FAILED unanchored"}),
            id="unsafe-regex",
        ),
    ],
)
def test_lookup_cli_invalid_inputs_fail_nonzero_without_stdout(
    tmp_path, capsys, mutation
) -> None:
    """Malformed, unsupported, and unsafe input never yields actionable stdout."""
    registry = _get_valid_registry_data()
    receipt = _get_valid_receipt_data()
    mutation(registry, receipt)
    registry_path = _write_json(tmp_path / "registry.json", registry)
    receipt_path = _write_json(tmp_path / "receipt.json", receipt)
    output_path = tmp_path / "lookup.json"

    rc = main(_lookup_args(registry_path, receipt_path, output_path))

    captured = capsys.readouterr()
    assert rc != 0
    assert captured.out == ""
    assert captured.err.startswith("red-CI known-failures error:")
    assert not output_path.exists()


def test_lookup_cli_identity_mismatch_fails_nonzero_without_stdout(tmp_path, capsys) -> None:
    """A receipt for another PR cannot be reused against this lookup identity."""
    registry_path, receipt_path = _write_lookup_inputs(tmp_path)
    output_path = tmp_path / "lookup.json"

    rc = main(_lookup_args(registry_path, receipt_path, output_path, pr=9999))

    captured = capsys.readouterr()
    assert rc != 0
    assert captured.out == ""
    assert "does not equal the CLI pr" in captured.err
    assert not output_path.exists()


def test_lookup_cli_empty_repository_identity_fails_nonzero_without_stdout(tmp_path, capsys) -> None:
    """An empty identity must not compare equal to a malformed receipt value."""
    registry_path, receipt_path = _write_lookup_inputs(tmp_path)
    output_path = tmp_path / "lookup.json"

    rc = main(
        _lookup_args(registry_path, receipt_path, output_path, repository_id="   ")
    )

    captured = capsys.readouterr()
    assert rc != 0
    assert captured.out == ""
    assert "repository-id must be non-empty" in captured.err
    assert not output_path.exists()


def test_lookup_cli_io_failure_is_nonzero_without_stdout(tmp_path, capsys) -> None:
    """Output failures cannot leave a caller with an implied action."""
    registry_path, receipt_path = _write_lookup_inputs(tmp_path)
    non_directory = tmp_path / "not-a-directory"
    non_directory.write_text("file", encoding="utf-8")

    rc = main(_lookup_args(registry_path, receipt_path, non_directory / "lookup.json"))

    captured = capsys.readouterr()
    assert rc != 0
    assert captured.out == ""
    assert "I/O error" in captured.err


def test_lookup_ambiguous_entries_never_select_by_file_order(tmp_path) -> None:
    """Two active matches must remain table-unknown regardless of entry order."""
    registry = _get_valid_registry_data()
    second_entry = deepcopy(registry["entries"][0])
    second_entry["id"] = "pytest-cache-race-second"
    registry["entries"].append(second_entry)
    registry_path = _write_json(tmp_path / "registry.json", registry)
    receipt_path = _write_json(tmp_path / "receipt.json", _get_valid_receipt_data())
    output_path = tmp_path / "lookup.json"

    assert main(_lookup_args(registry_path, receipt_path, output_path)) == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["reason"] == "ambiguous"


def test_lookup_expired_match_overrides_active_overlap(tmp_path) -> None:
    """An expired overlap blocks a current matching action instead of authorizing it."""
    registry = _get_valid_registry_data()
    expired_entry = deepcopy(registry["entries"][0])
    expired_entry["id"] = "expired-pytest-cache-race"
    expired_entry["governance"]["review_by"] = "2026-07-01T00:00:00Z"
    registry["entries"].append(expired_entry)
    registry_path = _write_json(tmp_path / "registry.json", registry)
    receipt_path = _write_json(tmp_path / "receipt.json", _get_valid_receipt_data())
    output_path = tmp_path / "lookup.json"

    assert main(_lookup_args(registry_path, receipt_path, output_path)) == 0
    lookup_receipt = json.loads(output_path.read_text(encoding="utf-8"))
    assert lookup_receipt["status"] == "table-unknown"
    assert lookup_receipt["reason"] == "expired-match"


def test_lookup_ignores_an_expired_entry_that_does_not_match(tmp_path) -> None:
    """An expired unrelated entry is registry hygiene for CI, not a false match."""
    registry = _get_valid_registry_data()
    registry["entries"][0]["governance"]["review_by"] = "2026-07-01T00:00:00Z"
    registry_path = _write_json(tmp_path / "registry.json", registry)
    receipt = _get_valid_receipt_data()
    receipt["check_name"] = "CI / unrelated"
    receipt_path = _write_json(tmp_path / "receipt.json", receipt)
    output_path = tmp_path / "lookup.json"

    assert main(_lookup_args(registry_path, receipt_path, output_path)) == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["reason"] == "no-match"


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        pytest.param({"kind": "note-and-proceed"}, {"kind": "note-and-proceed"}),
        pytest.param(
            {"kind": "stop", "stop_code": "STOP-manual-intervention"},
            {"kind": "stop", "stop_code": "STOP-manual-intervention"},
        ),
    ],
)
def test_lookup_returns_registered_actions_only_as_data(tmp_path, action, expected) -> None:
    """Non-retry actions remain receipt data; lookup never executes them."""
    registry = _get_valid_registry_data()
    registry["entries"][0]["action"] = action
    registry_path = _write_json(tmp_path / "registry.json", registry)
    receipt_path = _write_json(tmp_path / "receipt.json", _get_valid_receipt_data())
    output_path = tmp_path / "lookup.json"

    assert main(_lookup_args(registry_path, receipt_path, output_path)) == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["action"] == expected


def test_direct_lookup_cli_handles_a_stop_action_without_stdout(tmp_path) -> None:
    """The documented script-path CLI has no hidden validator import dependency."""
    registry = _get_valid_registry_data()
    registry["entries"][0]["action"] = {
        "kind": "stop",
        "stop_code": "STOP-manual-intervention",
    }
    registry_path = _write_json(tmp_path / "registry.json", registry)
    receipt_path = _write_json(tmp_path / "receipt.json", _get_valid_receipt_data())
    output_path = tmp_path / "lookup.json"

    completed = subprocess.run(
        [
            str(project_python()),
            str(PROJECT_ROOT / "scripts/orchestration/red_ci_known_failures.py"),
            *_lookup_args(registry_path, receipt_path, output_path),
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert json.loads(output_path.read_text(encoding="utf-8"))["action"] == registry["entries"][0]["action"]


def test_lookup_mixed_offset_expiry_never_uses_lexicographic_order(tmp_path) -> None:
    """The same instant in Z/+02:00 forms must detect expiry by epoch value."""
    registry = _get_valid_registry_data()
    registry["entries"][0]["governance"]["review_by"] = "2026-07-28T12:00:00+02:00"
    registry_path = _write_json(tmp_path / "registry.json", registry)
    receipt_path = _write_json(tmp_path / "receipt.json", _get_valid_receipt_data())
    output_path = tmp_path / "lookup.json"

    assert (
        main(
            _lookup_args(
                registry_path,
                receipt_path,
                output_path,
                as_of="2026-07-28T11:00:00Z",
            )
        )
        == 0
    )
    assert json.loads(output_path.read_text(encoding="utf-8"))["reason"] == "expired-match"


def test_lookup_full_coverage_rejects_an_additional_unknown_failure(tmp_path) -> None:
    """An accepted familiar line cannot hide an unknown additional failure line."""
    registry_path = _write_json(tmp_path / "registry.json", _get_valid_registry_data())
    receipt = _get_valid_receipt_data()
    receipt["normalized_signature_lines"].append("ERROR unknown additional failure")
    receipt["digest"] = compute_signature_digest(receipt["normalized_signature_lines"])
    receipt_path = _write_json(tmp_path / "receipt.json", receipt)
    output_path = tmp_path / "lookup.json"

    assert main(_lookup_args(registry_path, receipt_path, output_path)) == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["reason"] == "no-match"


@pytest.mark.parametrize(
    ("results", "expected"),
    [
        pytest.param([], {"kind": "stop", "reason": "malformed"}, id="empty"),
        pytest.param(
            [{"status": "table-unknown", "reason": "no-match"}],
            {"kind": "stop", "reason": "no-match"},
            id="unknown",
        ),
        pytest.param(
            [{"status": "table-unknown", "reason": "ambiguous"}],
            {"kind": "stop", "reason": "ambiguous"},
            id="ambiguous",
        ),
        pytest.param(
            [{"status": "table-unknown", "reason": "expired-match"}],
            {"kind": "stop", "reason": "expired-match"},
            id="expired-match",
        ),
        pytest.param(
            [{"status": "matched", "action": {"kind": "stop"}}],
            {"kind": "stop", "reason": "stop"},
            id="stop-action",
        ),
        pytest.param(
            [
                {"status": "matched", "action": {"kind": "note-and-proceed"}},
                {"status": "matched", "action": {"kind": "retry-once"}},
            ],
            {"kind": "retry-once"},
            id="retry-once-dominates-notes",
        ),
        pytest.param(
            [
                {"status": "matched", "action": {"kind": "note-and-proceed"}},
                {"status": "matched", "action": {"kind": "note-and-proceed"}},
            ],
            {"kind": "note-and-proceed"},
            id="all-notes",
        ),
    ],
)
def test_aggregate_lookup_results_is_fail_closed(results, expected) -> None:
    """Aggregation preserves the adopted stop/retry/note precedence exactly."""
    assert aggregate_lookup_results(results) == expected
