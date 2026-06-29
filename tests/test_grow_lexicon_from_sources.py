from __future__ import annotations

import json
from contextlib import nullcontext
from typing import Any

from scripts.audit import grow_lexicon_from_sources as grow


def test_generate_candidates_from_source_inventory_retains_provenance(
    tmp_path,
    monkeypatch,
) -> None:
    inventory = tmp_path / "sources.yaml"
    inventory.write_text(
        """
version: 1
kind: atlas_source_inventory
sources:
  - id: ulp-001
    source_family: ulp
    extraction_mode: curated_headword
    title: ULP Lesson 1
    url: https://example.test/ulp-001
    headwords:
      - lemma: авто
        gloss: car
        context: lesson headword
      - lemma: ревю
        context: lesson headword
""".lstrip(),
        encoding="utf-8",
    )
    out = tmp_path / "grow_candidates.json"
    seen: list[str] = []

    monkeypatch.setattr(grow, "_source_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(grow, "_preserve_wiki_reference_cache", lambda: nullcontext())
    monkeypatch.setattr(grow.enrich_manifest, "_load_kaikki_lookup", lambda: {"fixture": True})
    monkeypatch.setattr(grow.enrich_manifest, "_sum11_has_flag_columns", lambda conn: False)
    monkeypatch.setattr(
        grow,
        "build_skeleton_entry",
        lambda lemma: {"lemma": lemma, "pos": "noun"},
    )

    def fake_enrich_entry(
        entry: dict[str, Any],
        conn: object,
        kaikki_lookup: dict[str, bool],
        *,
        has_sum11_flags: bool,
    ) -> bool:
        seen.append(entry["lemma"])
        entry["heritage_status"] = {
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
        }
        if entry["lemma"] == "авто":
            entry["enrichment"] = {
                "meaning": {
                    "definitions": ["автомобіль"],
                    "source": "fixture",
                }
            }
            return True
        return False

    monkeypatch.setattr(grow.enrich_manifest, "enrich_entry", fake_enrich_entry)

    payload = grow.generate_candidates(inventory_paths=[inventory], limit=2, out=out)
    written = json.loads(out.read_text(encoding="utf-8"))

    assert payload == written
    assert seen == ["авто", "ревю"]
    assert written["generated_from"] == grow.GENERATED_FROM
    assert written["counts"] == {
        "total_delta": 2,
        "processed": 2,
        "auto_merge": 1,
        "needs_review": 1,
    }
    auto_entry = written["auto_merge"][0]
    held_entry = written["needs_review"][0]["entry"]
    assert auto_entry["primary_source"] == grow.PRIMARY_SOURCE
    assert auto_entry["gloss"] == "car"
    assert auto_entry["source_provenance"][0]["source_family"] == "ulp"
    assert auto_entry["source_provenance"][0]["source_id"] == "ulp-001"
    assert auto_entry["source_provenance"][0]["context"] == "lesson headword"
    assert held_entry["source_provenance"][0]["source_title"] == "ULP Lesson 1"
    assert not list(tmp_path.glob("*daily*"))
    assert not list(tmp_path.glob("*practice*"))
    assert not list(tmp_path.glob("*cloze*"))


def test_malformed_inventory_does_not_write_candidates(tmp_path, capsys) -> None:
    inventory = tmp_path / "bad.csv"
    inventory.write_text(
        "lemma,source_family,extraction_mode,unknown\n"
        "авто,ulp,curated_headword,nope\n",
        encoding="utf-8",
    )
    out = tmp_path / "grow_candidates.json"

    status = grow.main(["--inventory", str(inventory), "--out", str(out)])

    assert status == 2
    assert not out.exists()
    assert "unknown field" in capsys.readouterr().err
