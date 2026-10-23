"""Tests for scripts/lint/lint_prompts.py — prompt template linting."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "lint"))

from lint_prompts import (
    extract_curriculum_level_keys,
    extract_curriculum_level_types,
)

pytestmark = pytest.mark.repo_wide

# ---------- Unit tests for individual rules ----------


# ---------- Template variable tests ----------


# ---------- Integration tests ----------


# ---------- Orchestrator suite contract tests ----------


class TestOrchestratorSuiteContracts:
    """Tests for docs/prompts/orchestrators suite hardening."""

    def test_extract_curriculum_level_keys(self, tmp_path: Path):
        manifest = tmp_path / "curriculum.yaml"
        manifest.write_text(
            "version: '1.0'\n"
            "levels:\n"
            "  c1:\n"
            "    type: core\n"
            "# column-zero comments should not end levels parsing\n"
            "  lit-humor:\n"
            "    type: seminar\n"
            "other: ignored\n",
            encoding="utf-8",
        )
        assert extract_curriculum_level_keys(manifest) == {"c1", "lit-humor"}
        assert extract_curriculum_level_types(manifest) == {
            "c1": "core",
            "lit-humor": "seminar",
        }
