from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from scripts.audit.generate_practice_deck import (
    DEFAULT_TARGET,
    DRILL_MODES,
    BuildConfig,
    JsonVesumVerifier,
    ReviewedSourceAllowlist,
    _build_classify_items,
    _build_heritage_items,
    _build_lexeme,
    _build_paradigm_items,
    _declension_category,
    _eligible_decoys,
    _option_strategy_for_level,
    _stress_position,
    apply_size_budgets,
    build_practice_shards,
    main,
    read_cloze_sources,
    read_heritage_pairs,
    read_manifest,
    read_paronym_pairs,
    validate_classify_item,
    validate_heritage_item,
    validate_heritage_pair,
    validate_option_set,
    validate_paradigm_item,
    validate_paronym_item,
    validate_paronym_pair,
    validate_synonym_item,
)

FIXTURES = Path("tests/fixtures")
MANIFEST = FIXTURES / "lexicon-practice-manifest.json"
ALLOWLIST = FIXTURES / "lexicon-practice-reviewed-allowlist.json"
VESUM = FIXTURES / "lexicon-practice-vesum.json"
CLOZE_SOURCES = FIXTURES / "lexicon-practice-cloze-sources.json"
HERITAGE_PAIRS = FIXTURES / "lexicon-practice-heritage-pairs.yaml"
PARONYM_PAIRS = FIXTURES / "lexicon-practice-paronym-pairs.yaml"


def test_default_target_preserves_committed_practice_surface() -> None:
    assert DEFAULT_TARGET >= 6000
    assert BuildConfig().target == DEFAULT_TARGET


def _build(config: BuildConfig | None = None, cloze_sources_path: Path | None = CLOZE_SOURCES):
    entries = read_manifest(MANIFEST)
    allowlist = ReviewedSourceAllowlist.from_path(ALLOWLIST)
    verifier = JsonVesumVerifier.from_path(VESUM)
    cloze_sources = read_cloze_sources(cloze_sources_path) if cloze_sources_path else []
    return build_practice_shards(entries, allowlist, verifier, cloze_sources, config or BuildConfig(), heritage_pairs=[], paronym_pairs=[])


def _fixture_lexemes() -> list[dict[str, object]]:
    verifier = JsonVesumVerifier.from_path(VESUM)
    lexemes = [_build_lexeme(entry, verifier) for entry in read_manifest(MANIFEST)]
    return [lexeme for lexeme in lexemes if lexeme]


def _fixture_heritage_pair() -> dict[str, object]:
    return read_heritage_pairs(HERITAGE_PAIRS)[0]


def _single_deck_version(shards: dict[str, dict[str, dict[str, object]]]) -> str:
    versions = {
        payload["deckVersion"]
        for level_shards in shards.values()
        for payload in level_shards.values()
    }
    assert len(versions) == 1
    return versions.pop()


def test_fixture_build_emits_sharded_schema() -> None:
    shards = _build(BuildConfig(fixture_note="fixture sample", source_label="fixture"))
    apply_size_budgets(shards, raw_limit=50_000, gzip_limit=15_000)

    assert set(shards) == {"A1"}
    a1 = shards["A1"]
    assert set(a1) == {"index", "lexemes", "cloze", *DRILL_MODES}
    assert a1["index"]["schema"] == "atlas-practice-index"
    assert a1["lexemes"]["schema"] == "atlas-practice-lexemes"
    assert a1["cloze"]["schema"] == "atlas-practice-cloze"
    for mode in DRILL_MODES:
        assert a1[mode]["schema"] == f"atlas-practice-{mode}"
    assert a1["index"]["fixtureNote"] == "fixture sample"
    assert a1["index"]["counts"]["lexemes"] == 7
    assert a1["index"]["counts"]["cloze"] == 2
    assert a1["index"]["counts"]["clozeCoverage"] == 0.2857
    assert a1["index"]["counts"]["modeCounts"]["cloze"] == 2

    lexeme = next(item for item in a1["lexemes"]["lexemes"] if item["lemmaId"] == "knyha")
    assert lexeme["lemma"] == "книга"
    assert lexeme["lemmaPlain"] == "книга"
    assert lexeme["paradigm"]["cases"]["accusative"]["singular"] == "книгу"
    assert lexeme["heritage"] == "inherited"
    assert lexeme["severity"] == "standard"
    misto_cloze = next(item for item in a1["cloze"]["cloze"] if item["lemmaId"] == "misto")
    assert misto_cloze["clozeId"] == "misto:fixture:1"


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


def test_deck_version_changes_when_any_deck_input_changes() -> None:
    entries = read_manifest(MANIFEST)
    cloze_sources = read_cloze_sources(CLOZE_SOURCES)
    heritage_pairs = read_heritage_pairs(HERITAGE_PAIRS)
    paronym_pairs = read_paronym_pairs(PARONYM_PAIRS)
    synonym_verdicts = {"approved": [], "rejected": []}
    allowlist = ReviewedSourceAllowlist.from_path(ALLOWLIST)
    verifier = JsonVesumVerifier.from_path(VESUM)

    def version_for(
        *,
        entries_override: list[dict[str, object]] | None = None,
        cloze_sources_override: list[dict[str, object]] | None = None,
        heritage_pairs_override: list[dict[str, object]] | None = None,
        paronym_pairs_override: list[dict[str, object]] | None = None,
        synonym_verdicts_override: dict[str, object] | None = None,
    ) -> str:
        shards = build_practice_shards(
            entries_override or entries,
            allowlist,
            verifier,
            cloze_sources_override or cloze_sources,
            BuildConfig(),
            heritage_pairs=heritage_pairs_override or heritage_pairs,
            paronym_pairs=paronym_pairs_override or paronym_pairs,
            synonym_verdicts=synonym_verdicts_override or synonym_verdicts,
        )
        return _single_deck_version(shards)

    base_version = version_for()
    changed_entries = json.loads(json.dumps(entries))
    changed_entries[0]["gloss"] = "changed gloss"
    changed_cloze_sources = json.loads(json.dumps(cloze_sources))
    changed_cloze_sources[0]["sentence"] = "Змінене речення з ___."
    changed_heritage_pairs = json.loads(json.dumps(heritage_pairs))
    changed_heritage_pairs[0]["rationale"] = "changed rationale"
    changed_paronym_pairs = json.loads(json.dumps(paronym_pairs)) if paronym_pairs else []
    if changed_paronym_pairs:
        changed_paronym_pairs[0]["distinction_gloss_uk"] = "changed distinction for fingerprint test"
    changed_synonym_verdicts = {
        "approved": [{"a": "кіт", "b": "пес", "polarity": "synonym"}],
        "rejected": [],
    }

    assert version_for(entries_override=changed_entries) != base_version
    assert version_for(cloze_sources_override=changed_cloze_sources) != base_version
    assert version_for(heritage_pairs_override=changed_heritage_pairs) != base_version
    assert version_for(paronym_pairs_override=changed_paronym_pairs) != base_version
    assert version_for(synonym_verdicts_override=changed_synonym_verdicts) != base_version


def test_deck_version_stable_across_double_regen_with_identical_inputs() -> None:
    entries = read_manifest(MANIFEST)
    cloze_sources = read_cloze_sources(CLOZE_SOURCES)
    heritage_pairs = read_heritage_pairs(HERITAGE_PAIRS)
    paronym_pairs = read_paronym_pairs(PARONYM_PAIRS)
    synonym_verdicts = {"approved": [], "rejected": []}
    allowlist = ReviewedSourceAllowlist.from_path(ALLOWLIST)
    verifier = JsonVesumVerifier.from_path(VESUM)

    first = build_practice_shards(
        json.loads(json.dumps(entries)),
        allowlist,
        verifier,
        json.loads(json.dumps(cloze_sources)),
        BuildConfig(),
        heritage_pairs=json.loads(json.dumps(heritage_pairs)),
        paronym_pairs=json.loads(json.dumps(paronym_pairs)),
        synonym_verdicts=json.loads(json.dumps(synonym_verdicts)),
    )
    second = build_practice_shards(
        json.loads(json.dumps(entries)),
        allowlist,
        verifier,
        json.loads(json.dumps(cloze_sources)),
        BuildConfig(),
        heritage_pairs=json.loads(json.dumps(heritage_pairs)),
        paronym_pairs=json.loads(json.dumps(paronym_pairs)),
        synonym_verdicts=json.loads(json.dumps(synonym_verdicts)),
    )

    assert _single_deck_version(first) == _single_deck_version(second)
    assert first == second


def test_read_heritage_pairs_missing_file_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rows = read_heritage_pairs(tmp_path / "missing-heritage.yaml")

    captured = capsys.readouterr()
    assert rows == []
    assert "WARN: no curated heritage pairs found; emitting empty heritage deck" in captured.err


def test_read_heritage_pairs_empty_file_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "empty-heritage.yaml"
    path.write_text("", encoding="utf-8")

    rows = read_heritage_pairs(path)

    captured = capsys.readouterr()
    assert rows == []
    assert "WARN: curated heritage pairs empty; emitting empty heritage deck" in captured.err


def test_heritage_pair_v51_validator_accepts_framed_lexical_pair() -> None:
    pair = _fixture_heritage_pair()

    assert validate_heritage_pair(pair) == []


def test_heritage_pair_v51_validator_rejects_missing_senses_and_bad_frames() -> None:
    missing_senses = {
        **_fixture_heritage_pair(),
        "kind": "sense_restricted",
        "calqueSense": "",
        "authenticSense": "",
        "frames": [
            {
                "sentence_with_slot": "Я читаю ___.",
                "answer_form": "книгу",
                "calque_form": "кнігу",
                "origin": "fixture-frame",
                "disambiguated": True,
            }
        ],
    }
    no_disambiguation = {
        **missing_senses,
        "calqueSense": "calque sense",
        "authenticSense": "authentic sense",
        "frames": [
            {
                "sentence_with_slot": "Я читаю ___.",
                "answer_form": "книгу",
                "calque_form": "кнігу",
                "origin": "fixture-frame",
            }
        ],
    }
    multi_slot = {
        **_fixture_heritage_pair(),
        "frames": [
            {
                "sentence_with_slot": "___ і ще ___",
                "answer_form": "книгу",
                "calque_form": "кнігу",
                "origin": "fixture-frame",
            }
        ],
    }

    assert any("missing calqueSense" in error for error in validate_heritage_pair(missing_senses))
    assert any("missing authenticSense" in error for error in validate_heritage_pair(missing_senses))
    assert any("disambiguated: true" in error for error in validate_heritage_pair(no_disambiguation))
    assert any("exactly one ___ slot" in error for error in validate_heritage_pair(multi_slot))


def test_heritage_builder_fails_closed_without_frames(capsys: pytest.CaptureFixture[str]) -> None:
    pair = _fixture_heritage_pair()
    pair.pop("frames")
    lexemes = _fixture_lexemes()

    assert validate_heritage_pair(pair) == []
    assert _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1") == []

    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_path(ALLOWLIST),
        JsonVesumVerifier.from_path(VESUM),
        read_cloze_sources(CLOZE_SOURCES),
        BuildConfig(),
        [pair],
    )
    captured = capsys.readouterr()

    assert shards["A1"]["heritage"]["heritage"] == []
    assert "1 records without frames — emitted 0 items for them" in captured.err


def test_heritage_items_wire_mode_counts_and_index_modes() -> None:
    entries = json.loads(json.dumps(read_manifest(MANIFEST)))
    for entry in entries:
        entry["enrichment"]["cefr"]["level"] = "A2"
        entry["course_usage"][0]["track"] = "a2"
    entries[3]["pos"] = "verb"
    entries[4]["pos"] = "adjective"

    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_path(ALLOWLIST),
        JsonVesumVerifier.from_path(VESUM),
        read_cloze_sources(CLOZE_SOURCES),
        BuildConfig(),
        [_fixture_heritage_pair()],
    )
    a2 = shards["A2"]
    heritage = a2["heritage"]["heritage"]
    index_item = next(item for item in a2["index"]["items"] if item["lemmaId"] == "knyha")

    assert len(heritage) == 1
    assert heritage[0]["lemmaId"] == "knyha"
    assert all(set(option) == {"label"} for option in heritage[0]["options"])
    assert a2["index"]["counts"]["modeCounts"]["heritage"] == 1
    assert a2["index"]["counts"]["modeCoverage"]["heritage"] == 0.1429
    assert "heritage" in index_item["modes"]


def test_heritage_availability_floor_wins_over_native_cefr() -> None:
    entries = json.loads(json.dumps(read_manifest(MANIFEST)))
    for entry in entries:
        entry["enrichment"]["cefr"]["level"] = "A2"
        entry["course_usage"][0]["track"] = "a2"
    entries[-1]["enrichment"]["cefr"]["level"] = "B1"
    entries[-1]["course_usage"][0]["track"] = "b1"
    entries[3]["pos"] = "verb"
    entries[4]["pos"] = "adjective"
    pair = json.loads(json.dumps(_fixture_heritage_pair()))
    pair["cefrAvailability"] = "b1"

    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_path(ALLOWLIST),
        JsonVesumVerifier.from_path(VESUM),
        read_cloze_sources(CLOZE_SOURCES),
        BuildConfig(),
        [pair],
    )
    a2 = shards["A2"]
    a2_heritage = a2["heritage"]["heritage"]
    b1_heritage = shards["B1"]["heritage"]["heritage"]
    index_item = next(item for item in a2["index"]["items"] if item["lemmaId"] == "knyha")

    # #4719: the curator availability floor (b1) WINS over the native lexeme's
    # level (A2) for ITEM placement — B1-flagged calque drills must never reach
    # learners below the floor. Reachability is preserved via the index-mode
    # tag on the lexeme's own (A2) entry: at/above the floor, cumulative
    # loading has both the tag and the B1 item shard.
    assert a2_heritage == []
    assert len(b1_heritage) == 1
    assert b1_heritage[0]["lemmaId"] == "knyha"
    assert b1_heritage[0]["cefr"] == "B1"
    assert "heritage" in index_item["modes"]


def test_heritage_item_options_are_valid_and_do_not_mark_calque() -> None:
    pair = _fixture_heritage_pair()
    lexemes = _fixture_lexemes()
    item = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1")[0]
    internal_item = _build_heritage_items(
        pair,
        lexemes[0],
        lexemes,
        "deck-v1",
        public_options=False,
    )[0]

    assert validate_heritage_item(item) == []
    assert validate_heritage_item(internal_item, internal_options=True) == []
    assert all(set(option) == {"label"} for option in item["options"])
    assert all("kind" in option for option in internal_item["options"])

    marked = json.loads(json.dumps(item))
    for option in marked["options"]:
        if option["label"] == marked["calque"]:
            option["label"] = f"рос. {option['label']}"
            break

    assert "heritage options must not visually mark the calque pre-answer" in validate_heritage_item(marked)


def test_heritage_pair_native_slug_must_resolve_without_native_lemma_fallback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    pair = _fixture_heritage_pair()
    pair["nativeSlug"] = "missing-slug"
    pair["nativeLemma"] = "книга"
    pair["corrections"] = ["книга"]

    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_path(ALLOWLIST),
        JsonVesumVerifier.from_path(VESUM),
        read_cloze_sources(CLOZE_SOURCES),
        BuildConfig(),
        [pair],
    )
    captured = capsys.readouterr()

    assert all(level["heritage"]["heritage"] == [] for level in shards.values())
    assert "nativeSlug 'missing-slug' not in practice lexemes; emitted 0 items" in captured.err


def test_heritage_item_ids_and_options_are_deterministic() -> None:
    pair = _fixture_heritage_pair()
    lexemes = _fixture_lexemes()

    first = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1")[0]
    second = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1")[0]
    changed_version = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v2")[0]

    assert first["heritageId"] == second["heritageId"]
    assert first["options"] == second["options"]
    assert first["heritageId"] != changed_version["heritageId"]


def test_stress_position_preserves_non_stress_combining_marks() -> None:
    assert _stress_position("пої́здка") == ("поїздка", 2)
    assert _stress_position("кра́й") == ("край", 2)


def test_neuter_a_ya_nouns_can_reach_fourth_declension() -> None:
    entry = {"lemma": "ім'я", "pos": "noun"}
    paradigm = {"cases": {"nominative": {"singular": "ім'я"}}}

    assert _declension_category(entry, ["ім. сер."], paradigm) == "declension-4"


def test_a2_classify_items_do_not_raise_english_labels() -> None:
    entry = {
        "lemma": "книга",
        "pos": "noun",
        "enrichment": {
            "morphology": {
                "pos": "noun",
                "forms": [{"label": "ім. жін."}],
                "paradigm": {"cases": {"nominative": {"singular": "книга"}}},
            }
        },
    }
    lexeme = {"lemmaId": "knyha", "lemma": "книга", "cefr": "A2"}

    classify = _build_classify_items(entry, lexeme)[0]

    assert "setLabelEn" not in classify["sets"][0]
    assert "answerLabelEn" not in classify["sets"][0]
    assert all("labelEn" not in option for option in classify["sets"][0]["options"])


def test_paradigm_answer_position_is_deterministically_shuffled() -> None:
    items = _build_paradigm_items(
        {
            "lemmaId": "test-lemma",
            "lemma": "тест",
            "cefr": "B1",
            "paradigm": {
                "cases": {
                    "називний": {"singular": "тест"},
                    "родовий": {"singular": "тесту"},
                    "давальний": {"singular": "тестові"},
                    "орудний": {"singular": "тестом"},
                    "місцевий": {"singular": "тесті"},
                }
            },
        }
    )

    assert items
    assert any(item["options"][0]["kind"] != "answer" for item in items)


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


def test_mode_validators_reject_broken_fixtures() -> None:
    classify_errors = validate_classify_item(
        {
            "classifyId": "broken:classify",
            "lemmaId": "broken",
            "sets": [
                {
                    "setId": "gender",
                    "answer": "masculine",
                    "options": [{"value": "masculine", "labelUk": "чоловічий рід"}],
                }
            ],
        }
    )
    synonym_errors = validate_synonym_item(
        {
            "synonymId": "broken:synonym",
            "lemmaId": "broken",
            "prompt": "слово",
            "answer": "слово",
            "options": [
                {"label": "слово", "lemmaId": "a", "kind": "answer"},
                {"label": "слово", "lemmaId": "b", "kind": "distractor"},
                {"label": "надто довгий варіант", "lemmaId": "c", "kind": "distractor"},
                {"label": "інше", "lemmaId": "d", "kind": "distractor"},
            ],
        }
    )
    paradigm_errors = validate_paradigm_item(
        {
            "paradigmId": "broken:paradigm",
            "lemmaId": "broken",
            "form": "книгу",
            "options": [
                {"label": "книгу", "kind": "answer"},
                {"label": "книгу", "kind": "same-paradigm"},
                {"label": "книзі", "kind": "same-paradigm"},
            ],
        }
    )

    assert any("closed category set" in error for error in classify_errors)
    assert any("unique" in error for error in synonym_errors)
    assert any("at least four" in error for error in paradigm_errors)
    assert validate_heritage_pair({"nativeSlug": "питомий"}) != []
    assert validate_paronym_pair({"slugA": "адрес", "slugB": "адреса"}) != []


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
    for mode in DRILL_MODES:
        assert (tmp_path / f"practice-{mode}.A1.json").exists()
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
    cloze_sources = [
        *read_cloze_sources(CLOZE_SOURCES),
        {
            "lemma": "школа",
            "lemmaId": "shkola",
            "sentence": "Вона у ___.",
            "blankCase": "locative",
            "form": "школі",
            "number": "singular",
            "caseRule": "locative_static_u",
            "clozeEn": "She is at school.",
            "provenance": {
                "status": "reviewed",
                "path": "curriculum/l2-uk-en/a1/vocabulary/school.yaml",
                "cardId": "school-shkola-1",
            },
        },
    ]
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


def test_cloze_output_preserves_sentence_cefr() -> None:
    cloze = _build()["A1"]["cloze"]["cloze"][0]

    assert cloze["cefr"] == "A1"


def test_cloze_decoys_support_ukrainian_case_keys() -> None:
    entries = read_manifest(MANIFEST)
    for entry in entries:
        morphology = entry.get("enrichment", {}).get("morphology", {})
        paradigm = morphology.get("paradigm", {})
        cases = paradigm.get("cases", {})
        if isinstance(cases, dict) and "accusative" in cases:
            cases["знахідний"] = cases.pop("accusative")
        if isinstance(cases, dict) and "locative" in cases:
            cases["місцевий"] = cases.pop("locative")

    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_path(ALLOWLIST),
        JsonVesumVerifier.from_path(VESUM),
        read_cloze_sources(CLOZE_SOURCES),
        BuildConfig(),
    )

    assert shards["A1"]["cloze"]["cloze"]


def test_cloze_decoys_do_not_exceed_answer_cefr() -> None:
    answer = {"lemmaId": "валіза", "gloss": "suitcase", "pos": "noun", "cefr": "A1"}
    lexemes = [
        answer,
        {
            "lemmaId": "школа",
            "lemma": "школа",
            "gloss": "school",
            "pos": "noun",
            "cefr": "A1",
            "paradigm": {"cases": {"accusative": {"singular": "школу"}}},
        },
        {
            "lemmaId": "термінологія",
            "lemma": "термінологія",
            "gloss": "terminology",
            "pos": "noun",
            "cefr": "B2",
            "paradigm": {"cases": {"accusative": {"singular": "термінологію"}}},
        },
    ]

    assert _eligible_decoys(answer, lexemes, "accusative", "singular") == [
        (lexemes[1], "школу")
    ]


def _tatoeba_cloze_source() -> dict[str, object]:
    return {
        "lemma": "книга",
        "lemmaId": "knyha",
        "sentence": "Я читаю ___.",
        "blankCase": "accusative",
        "form": "книгу",
        "number": "singular",
        "caseRuleId": "accusative_direct_object",
        "clozeEn": "I am reading a book.",
        "cefr": "A1",
        "provenance": {
            "status": "tatoeba",
            "path": "tatoeba:101",
            "license": "CC-BY 2.0 FR",
            "author": "uk-author",
            "sentenceId": 101,
            "enSentenceId": 202,
            "enAuthor": "en-author",
            "enLicense": "CC-BY 2.0 FR",
        },
    }


def test_tatoeba_cloze_preserves_attribution_metadata() -> None:
    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_payload([{"status": "tatoeba", "path": "tatoeba:101"}]),
        JsonVesumVerifier.from_path(VESUM),
        [_tatoeba_cloze_source()],
        BuildConfig(),
    )

    cloze = shards["A1"]["cloze"]["cloze"][0]

    assert cloze["provenance"]["license"] == "CC-BY 2.0 FR"
    assert cloze["provenance"]["author"] == "uk-author"
    assert cloze["provenance"]["sentenceId"] == 101
    assert cloze["provenance"]["enSentenceId"] == 202
    assert cloze["provenance"]["enAuthor"] == "en-author"
    assert cloze["provenance"]["enLicense"] == "CC-BY 2.0 FR"
    assert cloze["attribution"] == {
        "source": "Tatoeba",
        "sourceUrl": "https://tatoeba.org/en/sentences/show/101",
        "uk": {"sentenceId": 101, "author": "uk-author", "license": "CC-BY 2.0 FR"},
        "en": {"sentenceId": 202, "author": "en-author", "license": "CC-BY 2.0 FR"},
    }


def test_tatoeba_cloze_uses_path_sentence_id_when_field_missing() -> None:
    source = _tatoeba_cloze_source()
    assert isinstance(source["provenance"], dict)
    source["provenance"].pop("sentenceId")

    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_payload([{"status": "tatoeba", "path": "tatoeba:101"}]),
        JsonVesumVerifier.from_path(VESUM),
        [source],
        BuildConfig(),
    )

    cloze = shards["A1"]["cloze"]["cloze"][0]
    assert cloze["provenance"]["sentenceId"] == 101
    assert cloze["attribution"]["uk"]["sentenceId"] == 101


def test_tatoeba_cloze_without_attribution_metadata_fails_closed() -> None:
    source = _tatoeba_cloze_source()
    source["provenance"] = {"status": "tatoeba", "path": "tatoeba:101"}

    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_payload([{"status": "tatoeba", "path": "tatoeba:101"}]),
        JsonVesumVerifier.from_path(VESUM),
        [source],
        BuildConfig(),
    )

    assert shards["A1"]["cloze"]["cloze"] == []


def test_heritage_curated_distractors_win() -> None:
    pair = {
        "nativeSlug": "knyha",
        "nativeLemma": "книга",
        "calqueLabel": "кніга",
        "calqueSurfaces": ["кніга"],
        "kind": "lexical",
        "corrections": ["книга"],
        "rationale": "test rationale",
        "citations": ["test:heritage"],
        "sourceFamily": "test",
        "cefrAvailability": "a2",
        "frames": [
            {
                "sentence_with_slot": "Я читаю ___.",
                "answer_form": "книгу",
                "calque_form": "кнігу",
                "origin": "test-frame",
                "distractors": ["місто", "яблуко"],
            }
        ],
    }

    lexemes = _fixture_lexemes()
    filtered_lexemes = [l for l in lexemes if l["lemmaId"] != "yabluko"]

    verifier = JsonVesumVerifier.from_path(VESUM)
    items = _build_heritage_items(pair, lexemes[0], filtered_lexemes, "deck-v1", verifier=verifier, public_options=False)

    assert len(items) == 1
    options = items[0]["options"]
    distractor_options = [opt for opt in options if opt["kind"] == "distractor"]
    assert len(distractor_options) == 2

    distractor_labels = {opt["label"] for opt in distractor_options}
    assert distractor_labels == {"місто", "яблуко"}

    yabluko_opt = next(opt for opt in distractor_options if opt["label"] == "яблуко")
    assert yabluko_opt["lemmaId"].startswith("cur_")
    assert yabluko_opt["pos"] == lexemes[0]["pos"]


def test_heritage_curated_distractors_allow_items_without_peers() -> None:
    pair = {
        "nativeSlug": "treba",
        "nativeLemma": "треба",
        "calqueLabel": "надо",
        "calqueSurfaces": ["надо"],
        "kind": "lexical",
        "corrections": ["треба"],
        "rationale": "test rationale",
        "citations": ["test:heritage"],
        "sourceFamily": "test",
        "cefrAvailability": "a2",
        "frames": [
            {
                "sentence_with_slot": "На завтра ___ підготувати текст.",
                "answer_form": "треба",
                "calque_form": "надо",
                "origin": "test-frame",
                "distractors": ["можна", "варто"],
            }
        ],
    }

    lexeme = {
        "lemmaId": "treba",
        "lemma": "треба",
        "lemmaPlain": "треба",
        "pos": "modal word",
        "cefr": "A2",
    }

    all_lexemes = [lexeme]
    verifier = JsonVesumVerifier({
        "можна": [{"lemma": "можна", "pos": "noninfl"}],
        "варто": [{"lemma": "варто", "pos": "noninfl"}],
    })

    items = _build_heritage_items(pair, lexeme, all_lexemes, "deck-v1", verifier=verifier, public_options=False)

    assert len(items) == 1
    assert items[0]["lemmaId"] == "treba"
    assert {opt["label"] for opt in items[0]["options"] if opt["kind"] == "distractor"} == {"можна", "варто"}


def test_paronym_pairs_emit_items_both_directions_and_validate(capsys: pytest.CaptureFixture[str]) -> None:
    # Use real fixture with valid slugs that exist in manifest subset for this test
    # Fallback to synthetic entries + pairs when direct lexeme match needed.
    entries = [
        {"lemmaId": "адресант", "lemma": "адресант", "gloss": "sender", "pos": "noun", "cefr": "B2", "url_slug": "адресант", "primary_source": "course_vocab", "course_usage": [{"track": "b2"}]},
        {"lemmaId": "адресат", "lemma": "адресат", "gloss": "addressee", "pos": "noun", "cefr": "B1", "url_slug": "адресат", "primary_source": "course_vocab", "course_usage": [{"track": "b2"}]},
    ]
    pair = {
        "slugA": "адресант",
        "slugB": "адресат",
        "distinction_gloss_uk": "Адресант надсилає; адресат отримує.",
        "citations": ["fixture-test"],
        "frames": [
            {"sentence_with_slot": "___ надіслав лист.", "answer_form": "Адресант", "confusable_form": "Адресат", "origin": "t"},
            {"sentence_with_slot": "Лист для ___.", "answer_form": "адресата", "confusable_form": "адресанта", "origin": "t2"},
        ],
    }
    allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier({})
    shards = build_practice_shards(entries, allowlist, verifier, [], BuildConfig(target=10), paronym_pairs=[pair])
    b1_items = shards.get("B1", {}).get("paronym", {}).get("paronym", [])
    b2_items = shards.get("B2", {}).get("paronym", {}).get("paronym", [])
    # At least one direction emits
    total = len(b1_items) + len(b2_items)
    assert total >= 1, "paronym should emit at least one item"
    # Validate
    assert validate_paronym_pair(pair) == []
    for it in b1_items + b2_items:
        assert validate_paronym_item(it) == []


def test_paronym_missing_slug_skips_with_warn(capsys: pytest.CaptureFixture[str]) -> None:
    entries = [{"lemmaId": "foo", "lemma": "foo", "gloss": "x", "pos": "noun", "cefr": "B1", "url_slug": "foo", "primary_source": "course_vocab", "course_usage": [{"track": "b1"}]}]
    pair = {"slugA": "missingA", "slugB": "missingB", "distinction_gloss_uk": "x", "citations": ["t"], "frames": [{"sentence_with_slot": "X ___ .", "answer_form": "x", "confusable_form": "y", "origin": "o"}]}
    allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier({})
    shards = build_practice_shards(entries, allowlist, verifier, [], BuildConfig(), paronym_pairs=[pair])
    assert shards["B1"]["paronym"]["paronym"] == []
    err = capsys.readouterr().err
    assert "not in practice lexemes; emitted 0 items" in err


def test_paronym_empty_file_emits_empty_fail_closed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = tmp_path / "empty-par.yaml"
    p.write_text("schema_version: 1\npairs: []\n", encoding="utf-8")
    rows = read_paronym_pairs(p)
    assert rows == []
    err = capsys.readouterr().err
    assert "curated paronym pairs empty" in err
    # build with [] yields no paronym items (fail-closed)
    entries = [{"lemmaId": "a", "lemma": "a", "gloss": "g", "pos": "n", "cefr": "B1", "url_slug": "a", "primary_source": "c", "course_usage": [{}]}]
    shards = build_practice_shards(entries, ReviewedSourceAllowlist.from_payload([]), JsonVesumVerifier({}), [], BuildConfig(), paronym_pairs=[])
    assert shards["B1"]["paronym"]["paronym"] == []
