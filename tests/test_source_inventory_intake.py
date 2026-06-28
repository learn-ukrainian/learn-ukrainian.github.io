from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit.source_inventory_intake import (
    SourceInventoryError,
    read_source_inventory,
    source_inventory_candidates,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_structured_inventory_preserves_source_provenance(tmp_path) -> None:
    inventory = tmp_path / "ulp.yaml"
    inventory.write_text(
        """
version: 1
kind: atlas_source_inventory
sources:
  - id: ulp-001
    source_family: ULP
    extraction_mode: curated_headword
    title: Ukrainian Lessons Podcast 1
    url: https://example.test/ulp-001
    locator: episode 1 vocabulary
    notes: curated external list
    headwords:
      - lemma: авто́
        pos: noun
        locator: 00:10
        context: lesson headword list
      - ревю
""".lstrip(),
        encoding="utf-8",
    )

    records = read_source_inventory(inventory, project_root=tmp_path)

    assert [record.lemma for record in records] == ["авто", "ревю"]
    assert records[0].source_family == "ulp"
    assert records[0].extraction_mode == "curated_headword"
    assert records[0].pos == "noun"
    assert records[0].provenance_payload() == {
        "source_family": "ulp",
        "extraction_mode": "curated_headword",
        "inventory_path": "ulp.yaml",
        "inventory_locator": "sources[1].headwords[1]",
        "source_id": "ulp-001",
        "source_title": "Ukrainian Lessons Podcast 1",
        "source_url": "https://example.test/ulp-001",
        "source_locator": "00:10",
        "context": "lesson headword list",
        "notes": "curated external list",
    }
    assert records[1].source_locator == "episode 1 vocabulary"


def test_flat_inventory_dedupes_stressed_variants_and_merges_provenance(tmp_path) -> None:
    inventory = tmp_path / "headwords.csv"
    inventory.write_text(
        "\n".join(
            [
                "lemma,source_family,source_id,source_title,extraction_mode,source_path,context,pos",
                "авто́,textbook,tb-1,Textbook 1,headword_inventory,data/textbook.txt,row one,noun",
                "авто,textbook,tb-2,Textbook 2,headword_inventory,data/textbook-2.txt,row two,noun",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    records = read_source_inventory(inventory, project_root=tmp_path)
    candidates = source_inventory_candidates(records)

    assert len(candidates) == 1
    assert candidates[0].lemma == "авто"
    assert candidates[0].pos == "noun"
    assert [item["source_id"] for item in candidates[0].source_provenance] == ["tb-1", "tb-2"]
    assert [item["inventory_locator"] for item in candidates[0].source_provenance] == [
        "row 2",
        "row 3",
    ]


def test_flat_inventory_accepts_utf8_bom(tmp_path) -> None:
    inventory = tmp_path / "headwords.csv"
    inventory.write_text(
        "\ufefflemma,source_family,extraction_mode\n"
        "авто,ulp,curated_headword\n",
        encoding="utf-8",
    )

    records = read_source_inventory(inventory, project_root=tmp_path)

    assert records[0].lemma == "авто"
    assert records[0].source_family == "ulp"


def test_inventory_rejects_unknown_fields(tmp_path) -> None:
    inventory = tmp_path / "bad.csv"
    inventory.write_text(
        "lemma,source_family,extraction_mode,source_titel\n"
        "авто,ulp,curated_headword,typo\n",
        encoding="utf-8",
    )

    with pytest.raises(SourceInventoryError, match="unknown field"):
        read_source_inventory(inventory, project_root=tmp_path)


def test_structured_inventory_rejects_noncanonical_keys(tmp_path) -> None:
    inventory = tmp_path / "bad.yaml"
    inventory.write_text(
        """
Version: 1
kind: atlas_source_inventory
sources: []
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(SourceInventoryError, match="unknown field 'Version'"):
        read_source_inventory(inventory, project_root=tmp_path)


def test_inventory_rejects_conflicting_pos_after_canonicalization(tmp_path) -> None:
    inventory = tmp_path / "bad.jsonl"
    inventory.write_text(
        "\n".join(
            [
                '{"lemma":"авто́","source_family":"ulp","extraction_mode":"curated_headword","pos":"noun"}',
                '{"lemma":"авто","source_family":"ohoiko","extraction_mode":"headword_inventory","pos":"verb"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    records = read_source_inventory(inventory, project_root=tmp_path)
    with pytest.raises(SourceInventoryError, match="conflicting pos"):
        source_inventory_candidates(records)


def test_committed_source_inventory_files_are_valid() -> None:
    inventory_dir = PROJECT_ROOT / "data" / "lexicon" / "source-inventory"
    supported_suffixes = {".csv", ".tsv", ".jsonl", ".json", ".yaml", ".yml"}
    inventory_paths = sorted(
        path
        for path in inventory_dir.iterdir()
        if path.suffix.lower() in supported_suffixes
    )

    assert inventory_paths

    records = []
    for inventory_path in inventory_paths:
        records.extend(read_source_inventory(inventory_path, project_root=PROJECT_ROOT))

    candidates = source_inventory_candidates(records)
    assert candidates

    for candidate in candidates:
        assert candidate.source_provenance
        for provenance in candidate.source_provenance:
            assert provenance["inventory_path"].startswith(
                "data/lexicon/source-inventory/"
            )
            assert provenance.get("source_id")
            assert provenance.get("source_title")
