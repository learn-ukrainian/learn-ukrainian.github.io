from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from scripts.audit.generate_practice_deck import (
    BuildConfig,
    JsonVesumVerifier,
    ReviewedSourceAllowlist,
    _build_lexeme,
    _option_strategy_for_level,
    apply_size_budgets,
    build_practice_shards,
    main,
    read_cloze_sources,
    read_manifest,
    validate_option_set,
)

FIXTURES = Path("tests/fixtures")
MANIFEST = FIXTURES / "lexicon-practice-manifest.json"
ALLOWLIST = FIXTURES / "lexicon-practice-reviewed-allowlist.json"
VESUM = FIXTURES / "lexicon-practice-vesum.json"
CLOZE_SOURCES = FIXTURES / "lexicon-practice-cloze-sources.json"


def _build(config: BuildConfig | None = None, cloze_sources_path: Path | None = CLOZE_SOURCES):
    entries = read_manifest(MANIFEST)
    allowlist = ReviewedSourceAllowlist.from_path(ALLOWLIST)
    verifier = JsonVesumVerifier.from_path(VESUM)
    cloze_sources = read_cloze_sources(cloze_sources_path) if cloze_sources_path else []
    return build_practice_shards(entries, allowlist, verifier, cloze_sources, config or BuildConfig())


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
    assert a1["index"]["counts"]["lexemes"] == 7
    assert a1["index"]["counts"]["cloze"] == 2
    assert a1["index"]["counts"]["clozeCoverage"] == 0.2857

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

    entries = read_manifest(MANIFEST)
    empty_allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier.from_path(VESUM)
    no_sources = build_practice_shards(entries, empty_allowlist, verifier)
    assert no_sources["A1"]["cloze"]["cloze"] == []


def test_manifest_cloze_fields_are_ignored_without_curated_sources() -> None:
    shards = _build(cloze_sources_path=None)

    assert shards["A1"]["index"]["counts"]["lexemes"] == 7
    assert shards["A1"]["index"]["counts"]["cloze"] == 0
    assert shards["A1"]["cloze"]["cloze"] == []


def test_meaning_mc_eligibility_marks_clean_and_messy_glosses() -> None:
    shards = _build()
    a1 = shards["A1"]
    lexemes = {item["lemmaId"]: item for item in a1["lexemes"]["lexemes"]}
    index_items = {item["lemmaId"]: item for item in a1["index"]["items"]}

    assert lexemes["knyha"]["glossClean"] == "book"
    assert lexemes["knyha"]["meaningMcEligible"] is True
    assert {"matching", "choice"}.issubset(set(index_items["knyha"]["modes"]))

    assert lexemes["ta"]["glossClean"] == "and"
    assert lexemes["ta"]["meaningMcEligible"] is False
    assert index_items["ta"]["modes"] == ["flashcards"]

    assert lexemes["borshch"]["glossClean"] == "borshch"
    assert lexemes["borshch"]["meaningMcEligible"] is False
    assert index_items["borshch"]["modes"] == ["flashcards"]


def test_option_set_validator_rejects_phrase_labels() -> None:
    cloze = json.loads(json.dumps(_build()["A1"]["cloze"]["cloze"][0]))
    cloze["options"][1]["label"] = "and yours? formal"

    assert "option labels must not be phrase glosses" in validate_option_set(cloze)


def test_option_set_validator_rejects_capitalization_leak() -> None:
    cloze = {
        "form": "Книгу",
        "blankCase": "accusative",
        "options": [
            {"label": "Книгу", "kind": "answer", "case": "accusative", "lemmaId": "knyha", "pos": "noun"},
            {"label": "місто", "kind": "decoy", "case": "accusative", "lemmaId": "misto", "pos": "noun"},
            {"label": "школу", "kind": "decoy", "case": "accusative", "lemmaId": "shkola", "pos": "noun"},
            {"label": "роботу", "kind": "decoy", "case": "accusative", "lemmaId": "robota", "pos": "noun"},
        ],
    }

    assert "answer capitalization must not uniquely reveal the answer" in validate_option_set(cloze)


def test_option_set_validator_allows_nominative_answer_without_oblique_pair() -> None:
    cloze = {
        "form": "книга",
        "blankCase": "nominative",
        "options": [
            {"label": "книга", "kind": "answer", "case": "nominative", "lemmaId": "knyha", "pos": "noun"},
            {"label": "місто", "kind": "decoy", "case": "nominative", "lemmaId": "misto", "pos": "noun"},
            {"label": "школа", "kind": "decoy", "case": "nominative", "lemmaId": "shkola", "pos": "noun"},
            {"label": "робота", "kind": "decoy", "case": "nominative", "lemmaId": "robota", "pos": "noun"},
        ],
    }

    assert "option set must contain at least two oblique-looking forms" not in validate_option_set(cloze)


def test_multi_sense_gloss_first_sense_is_meaning_mc_eligible() -> None:
    # A multi-sense content word ("forest; woods") has a clean concise first sense and
    # must stay eligible for Choice/Matching. The raw-gloss `;` check used to over-exclude
    # any multi-sense gloss even when its first sense was a perfect single-concept meaning.
    entries = [
        {
            "lemma": "ліс",
            "url_slug": "lis",
            "gloss": "forest; woods",
            "pos": "noun",
            "primary_source": "course_vocab",
            "cefr": "A1",
        },
    ]
    shards = build_practice_shards(
        entries, ReviewedSourceAllowlist.from_payload([]), JsonVesumVerifier({})
    )
    lexeme = shards["A1"]["lexemes"]["lexemes"][0]
    assert lexeme["glossClean"] == "forest"
    assert lexeme["meaningMcEligible"] is True
    assert {"matching", "choice"}.issubset(set(shards["A1"]["index"]["items"][0]["modes"]))


def test_real_manifest_shapes_still_yield_recognition_lexemes() -> None:
    entries = [
        {
            "lemma": "трава",
            "url_slug": "trava",
            "gloss": "grass",
            "pos": "noun",
            "primary_source": "course_vocab",
            "cefr": "A1",
        },
        {
            "lemma": "ніч",
            "url_slug": "nich",
            "gloss": "night",
            "pos": "noun",
            "primary_source": "course_vocab",
            "enrichment": {"cefr": {"level": "A2"}},
        },
        {
            "lemma": "пам'ять",
            "url_slug": "pamiat",
            "gloss": "memory",
            "pos": "noun",
            "primary_source": "course_vocab",
            "course_usage": [{"track": "b1", "slug": "memory"}],
            "enrichment": {},
        },
    ]
    allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier({})

    shards = build_practice_shards(entries, allowlist, verifier)

    assert set(shards) == {"A1", "A2", "B1"}
    a1_item = shards["A1"]["index"]["items"][0]
    assert a1_item["lemmaId"] == "trava"
    assert {"matching", "choice"}.issubset(set(a1_item["modes"]))
    assert shards["A1"]["lexemes"]["lexemes"][0]["paradigm"] == {"cases": {}}
    assert shards["B1"]["index"]["items"][0]["lemmaId"] == "pamiat"


def test_option_sets_are_valid_and_anti_gaming() -> None:
    shards = _build()
    for cloze in shards["A1"]["cloze"]["cloze"]:
        assert validate_option_set(cloze) == []
        labels = [option["label"] for option in cloze["options"]]
        assert labels.count(cloze["form"]) == 1
        assert sum(1 for option in cloze["options"] if option.get("case") != "nominative") >= 2
        assert {option.get("pos") for option in cloze["options"]} == {"noun"}
        root_counts: dict[str, int] = {}
        for option in cloze["options"]:
            root_counts[option["lemmaId"]] = root_counts.get(option["lemmaId"], 0) + 1
        assert sum(1 for count in root_counts.values() if count >= 2) != 1


def test_option_strategy_cefr_ramp_snapshot() -> None:
    counts = {}
    for level in ("A1", "A2", "B1", "B2", "C1", "C2"):
        rng = random.Random(f"20260624:{level}")
        counts[level] = sum(1 for _ in range(100) if _option_strategy_for_level(level, rng) == "no-pair")

    assert counts == {"A1": 70, "A2": 64, "B1": 54, "B2": 45, "C1": 47, "C2": 39}


def test_size_budget_warns_and_trims_per_level(capsys: pytest.CaptureFixture[str]) -> None:
    shards = _build()
    apply_size_budgets(shards, raw_limit=10, gzip_limit=10)

    captured = capsys.readouterr()
    assert "WARN:" in captured.err
    assert shards["A1"]["index"]["counts"]["lexemes"] < 5


def test_cli_writes_fixture_shards(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--manifest",
            str(MANIFEST),
            "--reviewed-allowlist",
            str(ALLOWLIST),
            "--cloze-sources",
            str(CLOZE_SOURCES),
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
    index_path = tmp_path / "practice-index.A1.json"
    lexeme_path = tmp_path / "practice-lexemes.A1.json"
    cloze_path = tmp_path / "practice-cloze.A1.json"
    assert index_path.exists()
    assert lexeme_path.exists()
    assert cloze_path.exists()
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "atlas-practice-index"
    assert payload["source"] == "fixture"


def test_word_without_paradigm_is_recognition_eligible() -> None:
    # Recognition (matching/choice) needs only lemma+gloss+level. A word with no morphological
    # paradigm must still produce a lexeme (regression for the 1413->312 over-gating collapse).
    verifier = JsonVesumVerifier.from_path(VESUM)
    entry = {"lemma": "тому", "gloss": "therefore", "enrichment": {"cefr": {"level": "A1"}}}
    lexeme = _build_lexeme(entry, verifier)
    assert lexeme is not None
    assert lexeme["gloss"] == "therefore"
    assert lexeme["paradigm"] == {"cases": {}}


def test_unverified_paradigm_is_blanked_not_dropped() -> None:
    # A paradigm whose forms do NOT VESUM-verify must be BLANKED (so the flashcard never shows an
    # unverified declension) while the word itself is still kept as a recognition lexeme.
    verifier = JsonVesumVerifier.from_path(VESUM)
    entry = {
        "lemma": "видумане",
        "gloss": "made-up",
        "pos": "noun",
        "enrichment": {
            "cefr": {"level": "A1"},
            "morphology": {"paradigm": {"cases": {"nominative": {"singular": "видуманеформа"}}}},
        },
    }
    lexeme = _build_lexeme(entry, verifier)
    assert lexeme is not None  # word kept
    assert lexeme["paradigm"] == {"cases": {}}  # unverified paradigm blanked



def test_source_inventory_rows_stay_out_of_practice_by_default() -> None:
    entries = read_manifest(MANIFEST)
    source_entry = json.loads(json.dumps(entries[0]))
    source_entry["primary_source"] = "source_inventory_grow"
    source_entry["course_usage"] = []
    source_entry.pop("surface_admission", None)

    shards = build_practice_shards(
        [source_entry],
        ReviewedSourceAllowlist.from_payload([]),
        JsonVesumVerifier.from_path(VESUM),
        [],
        BuildConfig(),
    )

    assert shards == {}


def test_source_inventory_cloze_requires_explicit_cloze_admission() -> None:
    entries = read_manifest(MANIFEST)
    for entry in entries:
        if entry["lemma"] == "книга":
            entry["primary_source"] = "source_inventory_grow"
            entry["course_usage"] = []
            entry["surface_admission"] = {"practice": True}
            break

    allowlist = ReviewedSourceAllowlist.from_path(ALLOWLIST)
    verifier = JsonVesumVerifier.from_path(VESUM)
    cloze_sources = read_cloze_sources(CLOZE_SOURCES)
    shards = build_practice_shards(entries, allowlist, verifier, cloze_sources, BuildConfig())
    cloze_ids = {
        item["lemmaId"]
        for level in shards.values()
        for item in level["cloze"]["cloze"]
    }
    assert "knyha" not in cloze_ids

    for entry in entries:
        if entry["lemma"] == "книга":
            entry["surface_admission"]["cloze"] = True
            break

    shards = build_practice_shards(entries, allowlist, verifier, cloze_sources, BuildConfig())
    cloze_ids = {
        item["lemmaId"]
        for level in shards.values()
        for item in level["cloze"]["cloze"]
    }
    assert "knyha" in cloze_ids
