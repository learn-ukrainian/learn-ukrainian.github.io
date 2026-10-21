"""Tests for fix_external_resources.py — audit and clean external_resources.yaml."""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "tools"))

from fix_external_resources import (
    audit,
)

# ── Detection functions ───────────────────────────────────────────────


# ── URL usage map ─────────────────────────────────────────────────────


# ── Audit ─────────────────────────────────────────────────────────────


# ── Clean ─────────────────────────────────────────────────────────────


# ── Integration ───────────────────────────────────────────────────────


class TestIntegration:
    def test_audit_on_real_file(self):
        """Smoke test: audit the actual external_resources.yaml."""
        resources_path = (
            Path(__file__).parent.parent
            / "docs"
            / "resources"
            / "external_resources.yaml"
        )
        if not resources_path.exists():
            pytest.skip("external_resources.yaml not found")

        data = yaml.safe_load(resources_path.read_text("utf-8"))
        resources = data.get("resources", {})
        report = audit(resources)

        assert report["total_entries"] > 0
        assert report["total_modules"] > 0
        # After #752 cleanup, no YouTube search URLs should remain
        assert len(report["youtube_search"]) == 0
