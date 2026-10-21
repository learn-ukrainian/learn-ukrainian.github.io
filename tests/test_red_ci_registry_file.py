"""Tests for the checked-in red-CI known-failures registry file (P11)."""

from __future__ import annotations

from pathlib import Path

from scripts.orchestration.red_ci_known_failures import (
    load_and_validate_registry,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = (
    PROJECT_ROOT / "scripts" / "config" / "trails" / "red-ci-known-failures.yaml"
)


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
