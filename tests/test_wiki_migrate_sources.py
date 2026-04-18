"""Tests for wiki source migration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


@pytest.mark.parametrize(
    ("body", "meta_sources", "expected"),
    [
        ("Source 50: `11-klas-istoriya-ukr-galimov-2024_s0238`", [], ["11-klas-istoriya-ukr-galimov-2024_s0238"]),
        ("Source 50: `11-клас-istoriya-ukr-galimov-2024_s0238`", [], ["11-klas-istoriya-ukr-galimov-2024_s0238"]),
        ("Джерело: 11-klas-ukrajinska-mova-voron-2019_s0340", [], ["11-klas-ukrajinska-mova-voron-2019_s0340"]),
        ("Джерело: 2", ["ext-foo-1", "11-klas-ukrmova-avramenko-2019_s0075"], ["11-klas-ukrmova-avramenko-2019_s0075"]),
        (
            "Source 6: 10-klas-ukrajinska-mova-zabolotnij-2018_s0213; Source 10: 11-klas-ukrajinska-mova-avramenko-2019_s0256",
            [],
            ["10-klas-ukrajinska-mova-zabolotnij-2018_s0213", "11-klas-ukrajinska-mova-avramenko-2019_s0256"],
        ),
        (
            "Джерела: 9-klas-ukrajinska-mova-voron-2017_s0104, 11-klas-ukrajinska-mova-voron-2019_s0288",
            [],
            ["9-klas-ukrajinska-mova-voron-2017_s0104", "11-klas-ukrajinska-mova-voron-2019_s0288"],
        ),
        (
            "Source 30, 31",
            ["ext-foo-1"] * 29 + ["11-klas-ukrmova-avramenko-2019_s0030", "11-klas-ukrmova-avramenko-2019_s0031"],
            ["11-klas-ukrmova-avramenko-2019_s0030", "11-klas-ukrmova-avramenko-2019_s0031"],
        ),
        (
            "Перефразовано з Source 14",
            ["ext-foo-1"] * 13 + ["11-klas-ukrmova-avramenko-2019_s0014"],
            ["11-klas-ukrmova-avramenko-2019_s0014"],
        ),
        ("Адаптовано з Джерела: `5-klas-ukrmova-uhor-2022-1_s0037`", [], ["5-klas-ukrmova-uhor-2022-1_s0037"]),
    ],
)
def test_resolve_legacy_citation_body_variants(
    body: str,
    meta_sources: list[str],
    expected: list[str],
) -> None:
    from wiki.migrate_sources import _resolve_legacy_citation_body

    files, warning = _resolve_legacy_citation_body(body, meta_sources)
    assert warning is None
    assert files == expected


def test_migrate_then_verify_roundtrip(tmp_path: Path) -> None:
    from wiki.migrate_sources import migrate_article, verify_articles
    from wiki.sources_schema import registry_path_for, save_sources_registry

    article_path = tmp_path / "wiki" / "periods" / "demo.md"
    article_path.parent.mkdir(parents=True)
    article_path.write_text(
        "# Demo\n\n"
        "<!-- wiki-meta\n"
        "slug: demo\n"
        "domain: periods\n"
        "tracks: [hist]\n"
        "sources: [ext-foo-1, 11-klas-ukrmova-avramenko-2019_s0075]\n"
        "compiled: 2026-04-18\n"
        "-->\n\n"
        "Факт один (Джерело: 2). Факт два (Source 1: `ext-foo-1`).\n",
        encoding="utf-8",
    )

    result = migrate_article(article_path)
    article_path.write_text(result.updated_text, encoding="utf-8")
    save_sources_registry(registry_path_for(article_path), result.registry, article_path=article_path)

    assert "[S1]" in result.updated_text or "[S2]" in result.updated_text
    assert "sources:" not in result.updated_text
    assert verify_articles([article_path]) == []


def test_render_diff_replaces_legacy_citations(tmp_path: Path, monkeypatch) -> None:
    from wiki import migrate_sources

    wiki_dir = tmp_path / "wiki"
    periods_dir = wiki_dir / "periods"
    periods_dir.mkdir(parents=True)
    article_path = periods_dir / "demo.md"
    article_path.write_text(
        "# Demo\n\n"
        "<!-- wiki-meta\nslug: demo\ndomain: periods\ntracks: [hist]\n"
        "sources: [11-klas-istoriya-ukr-galimov-2024_s0238]\ncompiled: 2026-04-18\n-->\n\n"
        "Речення (Source 50: `11-klas-istoriya-ukr-galimov-2024_s0238`).\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(migrate_sources, "WIKI_DIR", wiki_dir)
    result = migrate_sources.migrate_article(article_path)
    diff = migrate_sources.render_diff(result)

    assert "[S1]" in diff
    assert "(Source 50:" not in result.updated_text


def test_dry_run_on_real_articles_from_multiple_domains() -> None:
    from wiki.migrate_sources import migrate_article, render_diff

    candidate_paths = [
        Path(_project_root) / "wiki" / "pedagogy" / "a1" / "how-many.md",
        Path(_project_root) / "wiki" / "grammar" / "a2" / "dative-nouns.md",
        Path(_project_root) / "wiki" / "periods" / "afhanistan.md",
        Path(_project_root) / "wiki" / "figures" / "ahatanhel-krymskyi.md",
        Path(_project_root) / "wiki" / "mastery" / "c2" / "capstone-topic-selection.md",
    ]
    if not all(path.exists() for path in candidate_paths):
        pytest.skip("Expected real wiki fixture articles are not available in this checkout")

    results = [migrate_article(path) for path in candidate_paths]
    diffs = [render_diff(result) for result in results]
    assert all("[S" in diff for diff in diffs)
    assert all("(Source " not in result.updated_text for result in results)
