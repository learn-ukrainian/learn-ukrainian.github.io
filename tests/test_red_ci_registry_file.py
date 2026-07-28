"""Tests for the checked-in red-CI known-failures registry file (P11)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.orchestration.red_ci_known_failures import (
    RedCIKnownFailuresValidationError,
    load_and_validate_registry,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = (
    PROJECT_ROOT / "scripts" / "config" / "trails" / "red-ci-known-failures.yaml"
)
MAX_REVIEW_HORIZON_DAYS = 30
REQUIRED_EVIDENCE_FIELDS = {
    "run_id",
    "run_attempt",
    "pr_number",
    "head_sha",
    "observed_at",
    "signature_sha256",
}


def _parse_iso_instant(value: Any) -> datetime:
    """Parse a YAML/JSON timestamp string or a pre-parsed datetime into a UTC instant."""
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if text.endswith("Z") or text.endswith("z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _load_registry_data() -> dict[str, Any]:
    """Load raw registry data so mutation tests can operate on a copy."""
    with REGISTRY_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _valid_sample_entry(*, review_by: str = "2026-08-27T11:00:00Z") -> dict[str, Any]:
    """Return a schema-valid, domain-valid registry entry for mutation tests."""
    return {
        "id": "sample-known-failure",
        "matcher": {
            "check_name": {"exact": "CI / Test (pytest)"},
            "lines": {
                "required": [
                    {
                        "type": "regex",
                        "value": r"^FAILED tests/test_sample\.py::test_sample .*$",
                    }
                ],
                "accepted": [
                    {
                        "type": "regex",
                        "value": r"^FAILED tests/test_sample\.py::test_sample .*$",
                    }
                ],
                "require_full_coverage": True,
            },
        },
        "action": {"kind": "retry-once"},
        "owning_issue": 5885,
        "evidence": [
            {
                "run_id": 123456789,
                "run_attempt": 1,
                "pr_number": 1234,
                "head_sha": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4",
                "observed_at": "2026-07-28T10:00:00Z",
                "signature_sha256": (
                    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                ),
            }
        ],
        "governance": {
            "added_by": "developer1",
            "added_at": "2026-07-28T10:00:00Z",
            "added_in_pr": 6000,
            "reviewed_by": ["reviewer1"],
            "reviewed_at": "2026-07-28T11:00:00Z",
            "review_by": review_by,
        },
    }


def test_registry_file_exists() -> None:
    """The checked-in registry must exist at the path the trail expects."""
    assert REGISTRY_PATH.is_file(), f"Registry not found at {REGISTRY_PATH}"


def test_registry_file_validates_via_stage1_stage2_code_path() -> None:
    """The checked-in registry parses and validates through the shared module."""
    summary = load_and_validate_registry(
        REGISTRY_PATH,
        as_of="2100-01-01T00:00:00Z",
        allow_expired=False,
    )
    assert summary["ok"] is True
    assert summary["schema_version"] == "red-ci-known-failures.v1"
    assert isinstance(summary["data"].get("entries"), list)


def test_registry_entries_expire_within_30_days() -> None:
    """Operator decision: review_by must be within 30 days of added_at and reviewed_at."""
    data = _load_registry_data()
    horizon = timedelta(days=MAX_REVIEW_HORIZON_DAYS)
    for entry in data.get("entries", []):
        governance = entry["governance"]
        added_at = _parse_iso_instant(governance["added_at"])
        reviewed_at = _parse_iso_instant(governance["reviewed_at"])
        review_by = _parse_iso_instant(governance["review_by"])

        assert review_by <= added_at + horizon, (
            f"Entry '{entry['id']}': review_by {review_by.isoformat()} is more than "
            f"{MAX_REVIEW_HORIZON_DAYS} days after added_at {added_at.isoformat()}"
        )
        assert review_by <= reviewed_at + horizon, (
            f"Entry '{entry['id']}': review_by {review_by.isoformat()} is more than "
            f"{MAX_REVIEW_HORIZON_DAYS} days after reviewed_at {reviewed_at.isoformat()}"
        )


def test_registry_entries_have_required_provenance() -> None:
    """Every entry requires run reference + signature-receipt evidence."""
    data = _load_registry_data()
    for entry in data.get("entries", []):
        evidence = entry.get("evidence", [])
        assert evidence, f"Entry '{entry['id']}' has no evidence"
        for idx, item in enumerate(evidence):
            missing = REQUIRED_EVIDENCE_FIELDS - set(item.keys())
            assert not missing, (
                f"Entry '{entry['id']}' evidence[{idx}] missing provenance fields: "
                f"{sorted(missing)}"
            )


def test_registry_rejects_expired_entry_in_copy(tmp_path: Path) -> None:
    """Mutation-honest negative: an expired entry must fail validation."""
    data = _load_registry_data()
    expired = _valid_sample_entry(review_by="2000-01-01T00:00:00Z")
    data["entries"] = [*list(data.get("entries", [])), expired]

    mutated_path = tmp_path / "registry-expired.json"
    mutated_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(RedCIKnownFailuresValidationError, match="expired at review_by"):
        load_and_validate_registry(
            mutated_path, as_of="2026-08-01T00:00:00Z", allow_expired=False
        )


def test_registry_rejects_provenance_free_entry_in_copy(tmp_path: Path) -> None:
    """Mutation-honest negative: an entry without evidence must fail schema validation."""
    data = _load_registry_data()
    entry = _valid_sample_entry()
    entry["evidence"] = []
    data["entries"] = [*list(data.get("entries", [])), entry]

    mutated_path = tmp_path / "registry-no-evidence.json"
    mutated_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(
        RedCIKnownFailuresValidationError, match="Registry schema violation"
    ):
        load_and_validate_registry(
            mutated_path, as_of="2026-08-01T00:00:00Z", allow_expired=False
        )


def test_registry_rejects_unknown_field_in_copy(tmp_path: Path) -> None:
    """Mutation-honest negative: unknown fields are not silently accepted."""
    data = _load_registry_data()
    entry = _valid_sample_entry()
    entry["unknown_field"] = "must-be-rejected"
    data["entries"] = [*list(data.get("entries", [])), entry]

    mutated_path = tmp_path / "registry-unknown-field.json"
    mutated_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(
        RedCIKnownFailuresValidationError, match="Registry schema violation"
    ):
        load_and_validate_registry(
            mutated_path, as_of="2026-08-01T00:00:00Z", allow_expired=False
        )


def test_registry_unknown_top_level_field_in_copy(tmp_path: Path) -> None:
    """Mutation-honest negative: unknown top-level fields are also rejected."""
    data = _load_registry_data()
    data["extra_top_level"] = "rejected"

    mutated_path = tmp_path / "registry-extra-top-level.json"
    mutated_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(
        RedCIKnownFailuresValidationError, match="Registry schema violation"
    ):
        load_and_validate_registry(
            mutated_path, as_of="2026-08-01T00:00:00Z", allow_expired=False
        )
