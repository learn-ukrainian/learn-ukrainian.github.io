from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.audit.atlas_hub_coverage_census import (
    build_hub_coverage_census,
    format_markdown_table,
)
from tests.project_python import project_python


def _entry(**overrides: object) -> dict:
    entry = {
        "lemma": "слово",
        "url_slug": "слово",
        "gloss": "word",
        "pos": "noun",
        "primary_source": "test",
        "course_usage": [],
    }
    entry.update(overrides)
    return entry


def test_empty_manifest() -> None:
    census = build_hub_coverage_census({"entries": []})
    assert census["metadata"]["total_entries"] == 0
    for layer in census["p0_layers"]:
        assert layer["non_empty"] == 0
        assert layer["empty"] == 0
        assert layer["missing"] == 0
        assert layer["pct"] == 0.0


def test_definition_cards_breakdown() -> None:
    manifest = {
        "entries": [
            # 1: Has VTS and SUM-20
            _entry(
                lemma="сонце",
                enrichment={
                    "definition_cards": [
                        {"id": "vts", "source": "ВТС", "definitions": ["Центральне світило"]},
                        {"id": "sum20", "source": "СУМ-20", "definitions": ["Небесне тіло"]},
                    ]
                },
            ),
            # 2: Has Grinchenko only
            _entry(
                lemma="байдики",
                enrichment={
                    "definition_cards": [
                        {"id": "grinchenko", "source": "Грінченко", "definitions": ["Дрібні цурки"]},
                    ]
                },
            ),
            # 3: Has empty definition_cards list
            _entry(
                lemma="пустий",
                enrichment={"definition_cards": []},
            ),
            # 4: Missing definition_cards key
            _entry(lemma="безкарток", enrichment={}),
            # 5: Missing enrichment block
            _entry(lemma="безенричу"),
        ]
    }

    census = build_hub_coverage_census(manifest)
    assert census["metadata"]["total_entries"] == 5

    layers_by_key = {row["key"]: row for row in census["p0_layers"]}

    # any card: entries 1 and 2 are non-empty; entry 3 is empty; entries 4 and 5 are missing
    assert layers_by_key["enrichment.definition_cards"]["non_empty"] == 2
    assert layers_by_key["enrichment.definition_cards"]["empty"] == 1
    assert layers_by_key["enrichment.definition_cards"]["missing"] == 2
    assert layers_by_key["enrichment.definition_cards"]["pct"] == 40.0

    # VTS: entry 1 is non-empty; entries 2 and 3 have cards block but no VTS -> empty; 4 and 5 missing
    assert layers_by_key["enrichment.definition_cards.vts"]["non_empty"] == 1
    assert layers_by_key["enrichment.definition_cards.vts"]["empty"] == 2
    assert layers_by_key["enrichment.definition_cards.vts"]["missing"] == 2

    # SUM-20: entry 1 is non-empty; entries 2 and 3 empty; 4 and 5 missing
    assert layers_by_key["enrichment.definition_cards.sum20"]["non_empty"] == 1
    assert layers_by_key["enrichment.definition_cards.sum20"]["empty"] == 2
    assert layers_by_key["enrichment.definition_cards.sum20"]["missing"] == 2

    # Grinchenko: entry 2 is non-empty; entries 1 and 3 empty; 4 and 5 missing
    assert layers_by_key["enrichment.definition_cards.grinchenko"]["non_empty"] == 1
    assert layers_by_key["enrichment.definition_cards.grinchenko"]["empty"] == 2
    assert layers_by_key["enrichment.definition_cards.grinchenko"]["missing"] == 2


def test_synonyms_items_and_synsets() -> None:
    manifest = {
        "entries": [
            # 1: Has both items and synsets
            _entry(
                lemma="гарний",
                sections={
                    "synonyms": {
                        "items": ["красивий", "прекрасний"],
                        "synsets": [
                            {
                                "id": 1,
                                "members": [{"lemma": "красивий"}, {"lemma": "прекрасний"}],
                            }
                        ],
                    }
                },
            ),
            # 2: Has flat items only
            _entry(
                lemma="швидкий",
                sections={"synonyms": {"items": ["прудкий", "хуткий"]}},
            ),
            # 3: Synonyms present but empty
            _entry(
                lemma="німий",
                sections={"synonyms": {"items": [], "synsets": []}},
            ),
            # 4: Missing synonyms
            _entry(lemma="самотній", sections={}),
        ]
    }

    census = build_hub_coverage_census(manifest)
    layers_by_key = {row["key"]: row for row in census["p0_layers"]}

    assert layers_by_key["sections.synonyms"]["non_empty"] == 2
    assert layers_by_key["sections.synonyms"]["empty"] == 1
    assert layers_by_key["sections.synonyms"]["missing"] == 1

    assert layers_by_key["sections.synonyms.items"]["non_empty"] == 2
    assert layers_by_key["sections.synonyms.items"]["empty"] == 1
    assert layers_by_key["sections.synonyms.items"]["missing"] == 1

    assert layers_by_key["sections.synonyms.synsets"]["non_empty"] == 1
    assert layers_by_key["sections.synonyms.synsets"]["empty"] == 2
    assert layers_by_key["sections.synonyms.synsets"]["missing"] == 1


def test_idioms_proverbs_usage_notes() -> None:
    manifest = {
        "entries": [
            _entry(
                lemma="байдики",
                sections={
                    "idioms": {"items": [{"phrase": "бити байдики", "definition": "ледарювати"}]},
                    "proverbs": {"items": [{"text": "Без труда нема плода"}]},
                    "usage_notes": {"items": [{"title": "Байдики", "text": "Есе"}]},
                },
            ),
            _entry(
                lemma="пусто",
                sections={
                    "idioms": {"items": []},
                    "proverbs": {},
                    "usage_notes": None,
                },
            ),
            _entry(lemma="нічого"),
        ]
    }

    census = build_hub_coverage_census(manifest)
    layers_by_key = {row["key"]: row for row in census["p0_layers"]}

    for key in ("sections.idioms.items", "sections.proverbs.items", "sections.usage_notes.items"):
        assert layers_by_key[key]["non_empty"] == 1
        assert layers_by_key[key]["empty"] == 1
        assert layers_by_key[key]["missing"] == 1


def test_residual_analysis_identifies_thinnest() -> None:
    manifest = {
        "entries": [
            _entry(
                lemma="слово1",
                sections={"usage_notes": {"items": [{"text": "note"}]}},
                enrichment={"definition_cards": [{"id": "vts", "definitions": ["def"]}]},
            ),
            _entry(
                lemma="слово2",
                enrichment={"definition_cards": [{"id": "vts", "definitions": ["def"]}]},
            ),
            _entry(
                lemma="слово3",
                enrichment={"definition_cards": [{"id": "vts", "definitions": ["def"]}]},
            ),
        ]
    }

    census = build_hub_coverage_census(manifest)
    residual = census["residual_analysis"]

    assert (
        residual["thinnest_layer_key"] == "enrichment.definition_cards.sum20" or residual["thinnest_layer_count"] == 0
    )
    assert len(residual["thinnest_p0_layers"]) == 3


def test_markdown_formatter_renders_table() -> None:
    manifest = {
        "version": "0.1",
        "generated_at": "2026-08-31T00:00:00Z",
        "entries": [
            _entry(
                lemma="слово",
                enrichment={"definition_cards": [{"id": "vts", "definitions": ["def"]}]},
            )
        ],
    }
    census = build_hub_coverage_census(manifest)
    md = format_markdown_table(census)

    assert "## Word Atlas — Slovnyk Hub Layer Coverage Census" in md
    assert "2026-08-31T00:00:00Z" in md
    assert "| **Definitions (any card)** | `enrichment.definition_cards` |" in md
    assert "### Residual & Priority Analysis" in md


def test_cli_emits_json_and_markdown(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "generated_at": "2026-08-31T12:00:00Z",
                "entries": [
                    _entry(
                        lemma="слово",
                        sections={"synonyms": {"items": ["лексема"]}},
                        enrichment={"definition_cards": [{"id": "vts", "definitions": ["def"]}]},
                    )
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    json_result = subprocess.run(
        [
            str(project_python()),
            "scripts/audit/atlas_hub_coverage_census.py",
            "--manifest",
            str(manifest_path),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    data = json.loads(json_result.stdout)
    assert data["metadata"]["total_entries"] == 1
    assert data["residual_analysis"] is not None

    md_result = subprocess.run(
        [
            str(project_python()),
            "scripts/audit/atlas_hub_coverage_census.py",
            "--manifest",
            str(manifest_path),
            "--format",
            "markdown",
            "--p0-only",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "## Word Atlas — Slovnyk Hub Layer Coverage Census" in md_result.stdout
    assert "P1 & Structural Hub Layers" not in md_result.stdout
