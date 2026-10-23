"""Tests for scripts/build/miyklas.py — МійКлас grammar integration (#1040).

Covers: _tokenize, _extract_plan_keywords, find_matching_topics,
        build_miyklas_resource_entries, build_miyklas_knowledge_section.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# Fixtures — synthetic index entries used across tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _tokenize — text normalization
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _extract_plan_keywords — keyword extraction from plan dict
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# find_matching_topics — scoring + filtering
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# build_miyklas_resource_entries — resource tab entries
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# build_miyklas_knowledge_section — knowledge packet markdown
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _load_index — file loading edge cases (tested via find_matching_topics)
# ---------------------------------------------------------------------------


class TestLoadIndex:
    def test_malformed_yaml_returns_empty(self, tmp_path):
        """Malformed YAML file gracefully returns []."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text(": : : invalid yaml [[[", "utf-8")
        with patch("build.miyklas._INDEX_PATH", bad_file):
            from build.miyklas import _load_index
            result = _load_index()
            assert result == []
