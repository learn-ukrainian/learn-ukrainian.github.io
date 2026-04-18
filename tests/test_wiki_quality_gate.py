"""Tests for wiki quality gate citation and source-section checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


def _write_article(tmp_path: Path, body: str) -> Path:
    article_path = tmp_path / "wiki" / "linguistics" / "oes" / "walls-speak-intro.md"
    article_path.parent.mkdir(parents=True)
    article_path.write_text(body, encoding="utf-8")
    return article_path


def _write_registry(article_path: Path, body: str) -> None:
    article_path.with_suffix(".sources.yaml").write_text(body, encoding="utf-8")


@pytest.fixture
def quality_gate_module(monkeypatch):
    from wiki import quality_gate

    monkeypatch.setitem(quality_gate.MIN_WORDS, "oes", 0)
    return quality_gate


def test_check_article_flags_forbidden_sources_section(tmp_path: Path, quality_gate_module) -> None:
    article_path = _write_article(
        tmp_path,
        "# Заголовок\n\nТекст [S1].\n\n## Джерела\n* [S1] Example.\n",
    )
    _write_registry(
        article_path,
        "sources:\n  - id: S1\n    file: ext-example-1\n    type: external\n",
    )

    issues = quality_gate_module.check_article(article_path, "oes")

    assert "SOURCES_SECTION_PRESENT" in issues


def test_check_article_flags_orphan_inline_ref(tmp_path: Path, quality_gate_module) -> None:
    article_path = _write_article(tmp_path, "# Заголовок\n\nТекст [S1][S99].\n")
    _write_registry(
        article_path,
        "sources:\n  - id: S1\n    file: ext-example-1\n    type: external\n",
    )

    issues = quality_gate_module.check_article(article_path, "oes")

    assert "ORPHAN_INLINE_REF (S99)" in issues


def test_check_article_flags_unused_registry_source(tmp_path: Path, quality_gate_module) -> None:
    article_path = _write_article(tmp_path, "# Заголовок\n\nТекст [S1].\n")
    _write_registry(
        article_path,
        (
            "sources:\n"
            "  - id: S1\n"
            "    file: ext-example-1\n"
            "    type: external\n"
            "  - id: S2\n"
            "    file: ext-example-2\n"
            "    type: external\n"
        ),
    )

    issues = quality_gate_module.check_article(article_path, "oes")

    assert "UNUSED_SOURCE (S2)" in issues


def test_check_article_flags_missing_sources_yaml_when_refs_exist(
    tmp_path: Path, quality_gate_module
) -> None:
    article_path = _write_article(tmp_path, "# Заголовок\n\nТекст [S1].\n")

    issues = quality_gate_module.check_article(article_path, "oes")

    assert "MISSING_SOURCES_YAML (walls-speak-intro.sources.yaml)" in issues


def test_check_article_preserves_legacy_behavior_without_refs(
    tmp_path: Path, quality_gate_module
) -> None:
    article_path = _write_article(tmp_path, "# Заголовок\n\nПросто текст без цитат.\n")

    issues = quality_gate_module.check_article(article_path, "oes")

    assert "MISSING_SOURCES_YAML (walls-speak-intro.sources.yaml)" not in issues
    assert issues == []


def test_check_article_flags_malformed_sources_yaml(tmp_path: Path, quality_gate_module) -> None:
    article_path = _write_article(tmp_path, "# Заголовок\n\nТекст [S1].\n")
    _write_registry(article_path, "sources:\n  - id: S1\n    file: [broken\n")

    issues = quality_gate_module.check_article(article_path, "oes")

    assert any(issue.startswith("MALFORMED_SOURCES_YAML (walls-speak-intro.sources.yaml:") for issue in issues)
