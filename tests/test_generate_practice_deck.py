from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit.generate_practice_deck import (
    BuildConfig,
    JsonVesumVerifier,
    ReviewedSourceAllowlist,
    apply_size_budgets,
    build_practice_shards,
    main,
    read_manifest,
    validate_option_set,
)

FIXTURES = Path("tests/fixtures")
MANIFEST = FIXTURES / "lexicon-practice-manifest.json"
ALLOWLIST = FIXTURES / "lexicon-practice-reviewed-allowlist.json"
VESUM = FIXTURES / "lexicon-practice-vesum.json"


def _build(config: BuildConfig | None = None):
    entries = read_manifest(MANIFEST)
    allowlist = ReviewedSourceAllowlist.from_path(ALLOWLIST)
    verifier = JsonVesumVerifier.from_path(VESUM)
    return build_practice_shards(entries, allowlist, verifier, config or BuildConfig())


def test_fixture_build_emits_sharded_schema() -> None:
    shards = _build(BuildConfig(fixture_note="fixture sample", source_label="fixture"))
    apply_size_budgets(shards, raw_limit=50_000, gzip_limit=15_000)

    assert set(shards) == {"A1"}
    a1 = shards["A1"]
    assert set(a1) == {"index", "lexemes", "cloze"}
    assert a1["index"]["schema"] == "atlas-practice-index"
    assert a1["lexemes"]["schema"] == "atlas-practice-lexemes"
    assert a1["cloze"]["schema"] == "atlas-practice-cloze"
    assert a1["index"]["fixtureNote"] == "fixture sample"
    assert a1["index"]["counts"]["lexemes"] == 5
    assert a1["index"]["counts"]["cloze"] == 2
    assert a1["index"]["counts"]["clozeCoverage"] == 0.4

    lexeme = next(item for item in a1["lexemes"]["lexemes"] if item["lemmaId"] == "knyha")
    assert lexeme["lemma"] == "книга"
    assert lexeme["lemmaPlain"] == "книга"
    assert lexeme["paradigm"]["cases"]["accusative"]["singular"] == "книгу"
    assert lexeme["heritage"] == "inherited"
    assert lexeme["severity"] == "standard"


def test_reviewed_allowlist_and_vesum_ambiguity_fail_closed() -> None:
    shards = _build()
    cloze = shards["A1"]["cloze"]["cloze"]
    cloze_lemma_ids = {item["lemmaId"] for item in cloze}

    assert cloze_lemma_ids == {"knyha", "misto"}
    assert "robota" not in cloze_lemma_ids
    assert "shkola" not in cloze_lemma_ids

    entries = read_manifest(MANIFEST)
    empty_allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier.from_path(VESUM)
    no_sources = build_practice_shards(entries, empty_allowlist, verifier)
    assert no_sources["A1"]["cloze"]["cloze"] == []


def test_option_sets_are_valid_and_anti_gaming() -> None:
    shards = _build()
    for cloze in shards["A1"]["cloze"]["cloze"]:
        assert validate_option_set(cloze) == []
        labels = [option["label"] for option in cloze["options"]]
        assert labels.count(cloze["form"]) == 1
        root_counts: dict[str, int] = {}
        for option in cloze["options"]:
            root_counts[option["lemmaId"]] = root_counts.get(option["lemmaId"], 0) + 1
        assert sum(1 for count in root_counts.values() if count >= 2) != 1


def test_size_budget_failure_is_explicit() -> None:
    shards = _build()
    with pytest.raises(ValueError, match="exceeds size budget"):
        apply_size_budgets(shards, raw_limit=10, gzip_limit=10)


def test_cli_writes_fixture_shards(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--manifest",
            str(MANIFEST),
            "--reviewed-allowlist",
            str(ALLOWLIST),
            "--vesum-fixture",
            str(VESUM),
            "--out-dir",
            str(tmp_path),
            "--fixture-note",
            "fixture sample; finalizer regenerates with hydrated manifest",
            "--target",
            "10",
        ]
    )

    assert exit_code == 0
    index_path = tmp_path / "lexicon-practice-index.A1.json"
    lexeme_path = tmp_path / "lexicon-practice-lexemes.A1.json"
    cloze_path = tmp_path / "lexicon-practice-cloze.A1.json"
    assert index_path.exists()
    assert lexeme_path.exists()
    assert cloze_path.exists()
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "atlas-practice-index"
    assert payload["source"] == "fixture"
