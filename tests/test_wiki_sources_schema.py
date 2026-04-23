"""Tests for sibling wiki source registries."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


def test_assign_source_ids_is_stable_across_reruns() -> None:
    from wiki.sources_schema import WikiSourceEntry, WikiSourcesRegistry, assign_source_ids

    existing = WikiSourcesRegistry(
        sources=[
            WikiSourceEntry(id="S1", file="ext-foo-1", type="external"),
            WikiSourceEntry(id="S2", file="11-klas-ukrmova-avramenko-2019_s0075", type="textbook"),
        ]
    )

    registry = assign_source_ids(
        [
            "11-klas-ukrmova-avramenko-2019_s0075",
            "ext-foo-1",
            "feaa5fa7_c0001",
        ],
        existing=existing,
    )

    assert [(entry.id, entry.file) for entry in registry.sources] == [
        ("S1", "ext-foo-1"),
        ("S2", "11-klas-ukrmova-avramenko-2019_s0075"),
        ("S3", "feaa5fa7_c0001"),
    ]


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("11-klas-ukrmova-avramenko-2019_s0075", "textbook"),
        ("11-клас-istoriya-ukr-galimov-2024_s0238", "textbook"),
        ("ext-ulp_youtube-19", "external"),
        ("ext-wikipedia-kyiv", "wikipedia"),
        ("ukrainian_wiki/academic-writing_root", "ukrainian_wiki"),
        ("pravopys-2019-paragraph-42", "pravopys"),
        ("sum11-слово", "dictionary"),
        ("feaa5fa7_c3124", "literary"),
        ("unknown", "unknown"),
    ],
)
def test_infer_source_type(filename: str, expected: str) -> None:
    from wiki.sources_schema import _infer_source_type

    assert _infer_source_type(filename) == expected


def test_extract_short_citation_ids_supports_single_and_grouped_refs() -> None:
    from wiki.sources_schema import extract_short_citation_ids

    text = "Один факт [S1]. Інший [S2][S3]. Група [S4, S5]."
    assert extract_short_citation_ids(text) == ["S1", "S2", "S3", "S4", "S5"]


def test_validate_sources_registry_allows_meta_preserved_entries() -> None:
    from wiki.sources_schema import WikiSourceEntry, WikiSourcesRegistry, validate_sources_registry

    registry = WikiSourcesRegistry(
        sources=[
            WikiSourceEntry(id="S1", file="ext-foo-1", type="external"),
            WikiSourceEntry(
                id="S2",
                file="11-klas-ukrmova-avramenko-2019_s0075",
                type="textbook",
                preserved_from_meta=True,
            ),
        ]
    )

    issues = validate_sources_registry("Текст [S1].", registry)
    assert issues == []


def test_validate_sources_registry_flags_orphans() -> None:
    from wiki.sources_schema import WikiSourceEntry, WikiSourcesRegistry, validate_sources_registry

    registry = WikiSourcesRegistry(
        sources=[WikiSourceEntry(id="S1", file="ext-foo-1", type="external")]
    )

    issues = validate_sources_registry("Текст [S1][S2].", registry)
    assert "Missing registry entry for citation S2" in issues


def test_registry_round_trip(tmp_path: Path) -> None:
    from wiki.sources_schema import (
        WikiSourceEntry,
        WikiSourcesRegistry,
        load_sources_registry,
        save_sources_registry,
    )

    article_path = tmp_path / "wiki" / "periods" / "afhanistan.md"
    article_path.parent.mkdir(parents=True)
    path = article_path.with_suffix(".sources.yaml")
    registry = WikiSourcesRegistry(
        sources=[
            WikiSourceEntry(id="S1", file="11-klas-istoriya-ukr-galimov-2024_s0238", type="textbook"),
            WikiSourceEntry(
                id="S2",
                file="https://www.youtube.com/watch?v=abc123&t=15s",
                type="external",
                title="Podcast episode",
                url="https://www.youtube.com/watch?v=abc123&t=15s",
                video_id="abc123",
                ts_start=15,
                ts_end=29,
                preserved_from_meta=True,
            ),
        ]
    )

    save_sources_registry(path, registry, article_path=article_path)
    loaded = load_sources_registry(path)

    assert [(entry.id, entry.file, entry.type, entry.preserved_from_meta) for entry in loaded.sources] == [
        ("S1", "11-klas-istoriya-ukr-galimov-2024_s0238", "textbook", False),
        ("S2", "https://www.youtube.com/watch?v=abc123&t=15s", "external", True),
    ]
    assert loaded.sources[1].title == "Podcast episode"
    assert loaded.sources[1].video_id == "abc123"
    assert loaded.sources[1].ts_start == 15
    assert loaded.sources[1].ts_end == 29
    assert path.read_text(encoding="utf-8").startswith("# Source registry for wiki/periods/afhanistan.md")
