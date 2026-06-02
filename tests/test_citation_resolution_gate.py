"""Tests for scripts/validate/check_citation_resolution.py."""

from __future__ import annotations

import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))

from validate.check_citation_resolution import check_citation_resolution_text


def test_citation_resolution_flags_inline_s_markers_without_source_list():
    text = "# Стаття\n\nТвердження з посиланням [S1] і ще одне [S2].\n"

    finding = check_citation_resolution_text(text, path="wiki/figures/example.md")

    assert finding is not None
    assert finding.path == "wiki/figures/example.md"
    assert finding.cited_ids == ["S1", "S2"]


def test_citation_resolution_accepts_visible_source_mapping():
    text = (
        "# Стаття\n\n"
        "Твердження з посиланням [S1].\n\n"
        "## Джерела\n"
        "- [S1] Енциклопедія Сучасної України, стаття про постать.\n"
    )

    assert check_citation_resolution_text(text) is None


def test_citation_resolution_ignores_articles_without_s_markers():
    assert check_citation_resolution_text("# Стаття\n\nТекст без коротких джерел.\n") is None
