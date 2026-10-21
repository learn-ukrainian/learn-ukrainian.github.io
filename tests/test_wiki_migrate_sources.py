"""Tests for wiki source migration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

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
        ("Джерело: ``", [], ["unknown"]),
        (
            "напр., адаптований уривок з Source 5",
            ["ext-foo-1"] * 4 + ["ext-ulp_youtube-99"],
            ["ext-ulp_youtube-99"],
        ),
        (
            "Source 34: *лінгвістика* (наук.) — *мовознавство* (публ.)",
            ["ext-foo-1"] * 33 + ["ext-style-example-34"],
            ["ext-style-example-34"],
        ),
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


def test_rewrite_mixed_parenthetical_preserves_prose() -> None:
    from wiki.migrate_sources import LegacyCitationMatch, _render_citation_replacement

    citation = LegacyCitationMatch(
        start=0,
        end=0,
        raw="(напр., адаптований уривок з Source 5)",
        body="напр., адаптований уривок з Source 5",
        files=["ext-ulp_youtube-99"],
        warning=None,
    )

    replacement = _render_citation_replacement(
        citation,
        {"ext-ulp_youtube-99": "S5"},
        ["ext-foo-1"] * 4 + ["ext-ulp_youtube-99"],
        {5: "ext-ulp_youtube-99"},
    )

    assert replacement == "(напр., адаптований уривок з [S5])"


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


def test_rerun_preserves_existing_registry_for_short_citations(tmp_path: Path) -> None:
    from wiki.migrate_sources import migrate_article, verify_articles
    from wiki.sources_schema import WikiSourceEntry, WikiSourcesRegistry, registry_path_for, save_sources_registry

    article_path = tmp_path / "wiki" / "periods" / "demo.md"
    article_path.parent.mkdir(parents=True)
    article_path.write_text(
        "# Demo\n\n"
        "<!-- wiki-meta\n"
        "slug: demo\n"
        "domain: periods\n"
        "tracks: [hist]\n"
        "compiled: 2026-04-18\n"
        "-->\n\n"
        "Факт [S1].\n",
        encoding="utf-8",
    )
    save_sources_registry(
        registry_path_for(article_path),
        WikiSourcesRegistry(
            sources=[
                WikiSourceEntry(id="S1", file="ext-foo-1", type="external"),
            ]
        ),
        article_path=article_path,
    )

    result = migrate_article(article_path)
    article_path.write_text(result.updated_text, encoding="utf-8")
    save_sources_registry(registry_path_for(article_path), result.registry, article_path=article_path)

    assert [entry.id for entry in result.registry.sources] == ["S1"]
    assert [entry.file for entry in result.registry.sources] == ["ext-foo-1"]
    assert verify_articles([article_path]) == []


def test_rerun_backfills_missing_short_citation_registry_entries(tmp_path: Path) -> None:
    from wiki.migrate_sources import migrate_article, verify_articles

    article_path = tmp_path / "wiki" / "periods" / "demo.md"
    article_path.parent.mkdir(parents=True)
    article_path.write_text(
        "# Demo\n\n"
        "<!-- wiki-meta\n"
        "slug: demo\n"
        "domain: periods\n"
        "tracks: [hist]\n"
        "compiled: 2026-04-18\n"
        "-->\n\n"
        "Факт [S1] і факт [S2].\n",
        encoding="utf-8",
    )

    result = migrate_article(article_path)
    article_path.write_text(result.updated_text, encoding="utf-8")

    assert [entry.id for entry in result.registry.sources] == ["S1", "S2"]
    assert [entry.file for entry in result.registry.sources] == [
        "unknown-citation-s1",
        "unknown-citation-s2",
    ]
    from wiki.sources_schema import registry_path_for, save_sources_registry

    save_sources_registry(registry_path_for(article_path), result.registry, article_path=article_path)
    assert verify_articles([article_path]) == []
