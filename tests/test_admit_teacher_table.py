"""Tests for the re-runnable private teacher-table Atlas intake."""

import json
from pathlib import Path

import pytest

from scripts.lexicon.admit_teacher_table import (
    TableRow,
    _read_extract,
    admit_and_enrich,
    main,
    measure_table_coverage,
)


def _vesum_lookup(words: list[str], _db: Path) -> dict[str, list[dict[str, str]]]:
    analyses = {
        "нове": [{"lemma": "нове", "pos": "adj"}],
        "двозначне": [{"lemma": "двозначне", "pos": "adj"}, {"lemma": "двозначне", "pos": "noun"}],
    }
    return {word: analyses.get(word, []) for word in words}


def _dictionary(lemma: str, _pos: str, _english: str) -> dict[str, object] | None:
    if lemma == "нове":
        return {"en": ["new"], "source": "dmklinger UK-EN"}
    return None


def test_admit_and_enrich_keeps_expressions_and_accounts_for_single_token_residuals() -> None:
    rows = [
        TableRow("наявне", "available"),
        TableRow("тонке", "thin"),
        TableRow("нове", "new"),
        TableRow("у дорозі", "on the road"),
        TableRow("двозначне", "ambiguous"),
    ]
    manifest = {
        "entries": [
            {"lemma": "наявне", "url_slug": "наявне", "enrichment": {"translation": {"en": ["available"]}}},
            {"lemma": "тонке", "url_slug": "тонке", "enrichment": {}},
        ]
    }

    staged, artifacts = admit_and_enrich(
        rows=rows,
        manifest=manifest,
        vesum_db=Path("fixture-vesum.db"),
        vesum_lookup=_vesum_lookup,
        dictionary_lookup=_dictionary,
    )

    entries = {entry["lemma"]: entry for entry in staged["entries"]}
    assert entries["нове"]["pos"] == "adjective"
    assert entries["нове"]["enrichment"]["translation"]["source"] == "dmklinger UK-EN"
    assert entries["у дорозі"]["entry_type"] == "expression"
    assert entries["у дорозі"]["pos"] == "phrase"
    assert entries["тонке"]["enrichment"]["translation"] == {
        "en": ["thin"],
        "source": "teacher table #3 English gloss",
    }
    assert artifacts["counts"] == {
        "before_missing_atlas": 3,
        "before_present_without_en": 1,
        "admitted": 2,
        "canonical_links": 0,
        "re_enriched": 1,
        "after_missing_atlas": 1,
        "after_present_without_en": 0,
        "residuals": 1,
    }
    assert artifacts["residuals"] == [
        {
            "uk": "двозначне",
            "en": "ambiguous",
            "stage": "admit",
            "reason": "vesum_ambiguous_lemma_or_pos",
            "proof": {"vesum_db": "fixture-vesum.db", "analysis_count": 2, "canonical_lemma_count": 1},
        }
    ]


def test_rerun_is_a_noop_after_admission_and_translation_seed() -> None:
    rows = [TableRow("нове", "new"), TableRow("у дорозі", "on the road")]
    manifest = {"entries": []}

    staged, first = admit_and_enrich(
        rows=rows,
        manifest=manifest,
        vesum_db=Path("fixture-vesum.db"),
        vesum_lookup=_vesum_lookup,
        dictionary_lookup=None,
    )
    rerun, second = admit_and_enrich(
        rows=rows,
        manifest=staged,
        vesum_db=Path("fixture-vesum.db"),
        vesum_lookup=_vesum_lookup,
        dictionary_lookup=None,
    )

    assert first["counts"]["admitted"] == 2
    assert second["counts"]["admitted"] == 0
    assert second["counts"]["re_enriched"] == 0
    assert second["residuals"] == []
    assert measure_table_coverage(rows, rerun) == {"missing": [], "thin": [], "covered": rows}


def test_slug_collision_keeps_the_table_expression_on_a_stable_disambiguated_route() -> None:
    rows = [TableRow("у дорозі", "on the road")]
    manifest = {"entries": [{"lemma": "інший вираз", "url_slug": "у-дорозі", "enrichment": {}}]}

    staged, artifacts = admit_and_enrich(
        rows=rows,
        manifest=manifest,
        vesum_db=Path("fixture-vesum.db"),
        vesum_lookup=_vesum_lookup,
        dictionary_lookup=None,
    )

    assert staged["entries"][-1]["url_slug"] == "у-дорозі-teacher-table"
    assert artifacts["counts"]["admitted"] == 1
    assert artifacts["residuals"] == []


def test_single_token_uses_the_vesum_citation_lemma_and_preserves_table_membership() -> None:
    rows = [TableRow("поверхневе", "superficial")]
    manifest = {"entries": []}

    def surface_lookup(words: list[str], _db: Path) -> dict[str, list[dict[str, str]]]:
        return {word: [{"lemma": "поверхневий", "pos": "adj"}] for word in words}

    staged, artifacts = admit_and_enrich(
        rows=rows,
        manifest=manifest,
        vesum_db=Path("fixture-vesum.db"),
        vesum_lookup=surface_lookup,
        dictionary_lookup=None,
    )

    assert staged["entries"][0]["lemma"] == "поверхневий"
    assert staged["entries"][0]["teacher_table_keys"] == ["поверхневе"]
    assert measure_table_coverage(rows, staged) == {"missing": [], "thin": [], "covered": rows}
    assert artifacts["counts"]["admitted"] == 1


def test_surface_resolved_to_an_existing_canonical_entry_is_linked_and_enriched() -> None:
    rows = [TableRow("поверхневе", "superficial")]
    manifest = {"entries": [{"lemma": "поверхневий", "url_slug": "поверхневий", "enrichment": {}}]}

    def surface_lookup(words: list[str], _db: Path) -> dict[str, list[dict[str, str]]]:
        return {word: [{"lemma": "поверхневий", "pos": "adj"}] for word in words}

    staged, artifacts = admit_and_enrich(
        rows=rows,
        manifest=manifest,
        vesum_db=Path("fixture-vesum.db"),
        vesum_lookup=surface_lookup,
        dictionary_lookup=None,
    )

    existing = staged["entries"][0]
    assert existing["teacher_table_keys"] == ["поверхневе"]
    assert existing["enrichment"]["translation"] == {
        "en": ["superficial"],
        "source": "teacher table #3 English gloss",
    }
    assert artifacts["counts"]["admitted"] == 0
    assert artifacts["counts"]["canonical_links"] == 1
    assert artifacts["counts"]["re_enriched"] == 1
    assert measure_table_coverage(rows, staged) == {"missing": [], "thin": [], "covered": rows}


def test_cli_refuses_to_overwrite_its_manifest_input(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"entries": []}', encoding="utf-8")

    with pytest.raises(SystemExit):
        main(
            [
                "--extract",
                str(tmp_path / "missing-extract.json"),
                "--manifest-in",
                str(manifest),
                "--manifest-out",
                str(manifest),
                "--write",
            ]
        )


def test_extract_rejects_conflicting_english_glosses_for_one_normalized_key(tmp_path) -> None:
    extract = tmp_path / "teacher-table.json"
    extract.write_text(
        json.dumps({"entries": [{"uk": "нове", "en": "new"}, {"uk": "нове", "en": "novel"}]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="conflicting English glosses"):
        _read_extract(extract)
