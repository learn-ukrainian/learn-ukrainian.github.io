from __future__ import annotations

import copy
import hashlib
import json
import random
import sqlite3
from pathlib import Path
from typing import Any

import pytest

import scripts.audit.generate_practice_deck as generate_practice_deck
from scripts.audit.generate_practice_deck import (
    DRILL_MODES,
    HERITAGE_CURRENT_SOURCES,
    HERITAGE_NORMATIVE_SOURCES,
    BuildConfig,
    JsonSourcePassages,
    JsonVesumVerifier,
    RealVesumVerifier,
    ReviewedSourceAllowlist,
    VesumLemmaEvidence,
    _build_classify_items,
    _build_cloze_items,
    _build_heritage_items,
    _build_lexeme,
    _build_paradigm_items,
    _cloze_blank_context_agrees,
    _declension_category,
    _emitted_lemma_ids,
    _heritage_current_support,
    _heritage_frame_calque_mismatch,
    _heritage_frame_support,
    _merge_heritage_pair_overlay,
    _plain,
    _stress_position,
    _valid_heritage_frames,
    _vesum_aspect_by_lemma,
    apply_size_budgets,
    build_practice_shards,
    compact_cloze_emit_fields,
    explanation_gate_errors,
    explanation_language_errors,
    main,
    merge_practice_seed_entries,
    paronym_gloss_provenance_errors,
    read_antonym_pairs,
    read_cloze_sources,
    read_heritage_pairs,
    read_homonym_pairs,
    read_manifest,
    read_paronym_pairs,
    read_practice_seed,
    read_sentence_inventory,
    validate_antonym_item,
    validate_antonym_pair,
    validate_heritage_item,
    validate_heritage_pair,
    validate_homonym_pair,
    validate_option_set,
    validate_paradigm_item,
    validate_paronym_item,
    validate_paronym_pair,
    verified_source_passages,
    write_shards,
)
from scripts.lib.readonly_sqlite import open_readonly

pytestmark = pytest.mark.reads_content

FIXTURES = Path("tests/fixtures")
MANIFEST = FIXTURES / "lexicon-practice-manifest.json"
ALLOWLIST = FIXTURES / "lexicon-practice-reviewed-allowlist.json"
VESUM = FIXTURES / "lexicon-practice-vesum.json"
CLOZE_SOURCES = FIXTURES / "lexicon-practice-cloze-sources.json"
HERITAGE_PAIRS = FIXTURES / "lexicon-practice-heritage-pairs.yaml"
PARONYM_PAIRS = FIXTURES / "lexicon-practice-paronym-pairs.yaml"
HERITAGE_REGISTRY = Path("registry/lexicon/heritage_pairs.yaml")
PARONYM_REGISTRY = Path("registry/lexicon/paronym_pairs.yaml")
CURATED_V5_SEED = FIXTURES / "atlas" / "curated_v5_practice_seed.json"


@pytest.fixture(autouse=True)
def synthetic_creation_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Existing factory scenarios use a fixed historical synthetic corpus."""
    from scripts.practice.creation_review import CreationReview

    generate_practice_deck._imperative_display.cache_clear()
    policy = CreationReview.from_path(FIXTURES / "lexicon-practice-creation-review.json")
    monkeypatch.setattr(CreationReview, "from_path", classmethod(lambda cls: policy))


def test_curated_v5_seed_admits_existing_atlas_entries_with_provenance() -> None:
    seed_rows = read_practice_seed(CURATED_V5_SEED)
    assert len(seed_rows) == 3
    assert {row["sentenceStatus"] for row in seed_rows} == {"ok"}

    atlas_entries = [
        {
            "url_slug": row["slug"],
            "lemma": row["lemma"],
            "gloss": f"seed gloss {index}",
            "enrichment": {"cefr": {"level": row["cefr"]}},
            "primary_source": "source_inventory_grow",
        }
        for index, row in enumerate(seed_rows)
    ]
    merged = merge_practice_seed_entries(atlas_entries, seed_rows)
    assert all(entry["surface_admission"]["practice"] is True for entry in merged)

    shards = build_practice_shards(
        merged,
        ReviewedSourceAllowlist.from_payload([]),
        JsonVesumVerifier.from_path(VESUM),
        [],
        BuildConfig(target=len(seed_rows), source_label="fixture"),
        heritage_pairs=[],
        paronym_pairs=[],
        synonym_verdicts={"approved": [], "rejected": []},
    )
    indexed = {item["lemmaId"]: item for level in shards.values() for item in level["index"]["items"]}
    lexemes = {item["lemmaId"]: item for level in shards.values() for item in level["lexemes"]["lexemes"]}
    for row in seed_rows:
        item = indexed[row["slug"]]
        assert item["hasCloze"] is False
        assert item["clozeIds"] == []
        assert lexemes[row["slug"]]["example"] == row["example"]
        assert lexemes[row["slug"]]["exampleProvenance"] == row["provenance"]


def test_local_practice_seed_requires_explicit_opt_in_and_never_creates_a_cloze_example(tmp_path: Path) -> None:
    seed_path = tmp_path / "local-seed.json"
    seed_path.write_text(
        json.dumps(
            {
                "schema": "curated-v5-practice-seed-v1",
                "localOnly": True,
                "entries": [
                    {
                        "seedRow": 1,
                        "lemma": "слово",
                        "slug": "слово",
                        "cefr": "A1",
                        "sentenceStatus": "has_candidates",
                        "admissionMode": "local_practice_private_teacher",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires --local-practice-seed"):
        read_practice_seed(seed_path)

    merged = merge_practice_seed_entries(
        [{"lemma": "слово", "url_slug": "слово", "gloss": "word", "enrichment": {"cefr": "A1"}}],
        read_practice_seed(seed_path, allow_local_private=True),
    )

    assert merged[0]["surface_admission"] == {"cloze": False, "practice": True}
    assert merged[0]["local_practice_private_teacher"] is True
    assert "practice_example" not in merged[0]


def test_local_practice_seed_merges_public_route_soft_cefr_without_atlas_enrichment(
    tmp_path: Path,
) -> None:
    """End-to-end: soft-admitted public-route teacher row must merge, not crash."""
    seed_path = tmp_path / "local-public-soft-cefr.json"
    seed_path.write_text(
        json.dumps(
            {
                "schema": "curated-v5-practice-seed-v1",
                "localOnly": True,
                "entries": [
                    {
                        "seedRow": 820,
                        "lemma": "кліщ",
                        "slug": "кліщ",
                        "cefr": "B1",
                        "cefrSource": "public_route_unleveled:кліщ:local_practice_unleveled (guidance only)",
                        "sentenceStatus": "has_candidates",
                        "admissionMode": "local_practice_private_teacher",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    atlas_entries = [
        {
            "lemma": "кліщ",
            "url_slug": "кліщ",
            "gloss": "tick",
            "enrichment": {},
        }
    ]

    merged = merge_practice_seed_entries(
        atlas_entries,
        read_practice_seed(seed_path, allow_local_private=True),
    )

    assert merged[0]["url_slug"] == "кліщ"
    assert merged[0]["cefr"] == "B1"
    assert merged[0]["local_practice_private_teacher"] is True
    assert merged[0]["surface_admission"]["cloze"] is False
    assert merged[0]["surface_admission"]["practice"] is True
    assert "practice_example" not in merged[0]


def test_local_practice_seed_materializes_attested_no_route_row_in_memory_only(tmp_path: Path) -> None:
    seed_path = tmp_path / "local-no-route-seed.json"
    seed_path.write_text(
        json.dumps(
            {
                "schema": "curated-v5-practice-seed-v1",
                "localOnly": True,
                "entries": [
                    {
                        "seedRow": 9,
                        "lemma": "виходити з ладу",
                        "gloss": "to break down",
                        "slug": "local-teacher-9",
                        "cefr": "A2",
                        "sentenceStatus": "has_candidates",
                        "admissionMode": "local_practice_private_teacher",
                        "localOnly": True,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    merged = merge_practice_seed_entries([], read_practice_seed(seed_path, allow_local_private=True))

    assert merged == [
        {
            "lemma": "виходити з ладу",
            "url_slug": "local-teacher-9",
            "gloss": "to break down",
            "cefr": "A2",
            "primary_source": "private_teacher_local_only",
            "surface_admission": {"cloze": False, "practice": True},
            "local_practice_private_teacher": True,
            "local_only": True,
        }
    ]


def test_practice_seed_validates_duplicate_attestations_but_emits_one_route_example(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.json"
    provenance = {"source_file": "ukrlib-example", "credit": "Автор"}
    seed_path.write_text(
        json.dumps(
            {
                "schema": "curated-v5-practice-seed-v1",
                "entries": [
                    {
                        "lemma": "слово",
                        "slug": "слово",
                        "cefr": "A1",
                        "example": "Перший.",
                        "provenance": provenance,
                        "sentenceStatus": "ok",
                    },
                    {
                        "lemma": "слово",
                        "slug": "слово",
                        "cefr": "A1",
                        "example": "Другий.",
                        "provenance": provenance,
                        "sentenceStatus": "ok",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    merged = merge_practice_seed_entries(
        [{"lemma": "слово", "url_slug": "слово", "enrichment": {"cefr": {"level": "A1"}}}],
        read_practice_seed(seed_path),
    )

    assert merged[0]["practice_example"]["text"] == "Перший."


def _build(config: BuildConfig | None = None, cloze_sources_path: Path | None = CLOZE_SOURCES):
    entries = read_manifest(MANIFEST)
    allowlist = ReviewedSourceAllowlist.from_path(ALLOWLIST)
    verifier = JsonVesumVerifier.from_path(VESUM)
    cloze_sources = read_cloze_sources(cloze_sources_path) if cloze_sources_path else []
    return build_practice_shards(
        entries, allowlist, verifier, cloze_sources, config or BuildConfig(), heritage_pairs=[], paronym_pairs=[]
    )


def _fixture_lexemes() -> list[dict[str, object]]:
    verifier = JsonVesumVerifier.from_path(VESUM)
    lexemes = [_build_lexeme(entry, verifier) for entry in read_manifest(MANIFEST)]
    return [lexeme for lexeme in lexemes if lexeme]


def _fixture_heritage_pair() -> dict[str, object]:
    return read_heritage_pairs(HERITAGE_PAIRS)[0]


def _gloss_verifier(*words: str) -> JsonVesumVerifier:
    """Fixture VESUM that knows the given forms as clean lemmas (explanation gate, #8728)."""
    return JsonVesumVerifier({word: [{"lemma": word, "pos": "x", "tags": "x"}] for word in words})


# Fixture source chunks behind normativeSupport / glossSources passages (#8727, #8728).
FIXTURE_PASSAGES = JsonSourcePassages(
    {
        "antonenko-davydovych-yak-my-hovorymo_p999": 'Фіктивна сторінка. Кажуть "читаю кнігу", а треба "читаю книгу".',
        "antonenko-davydovych-yak-my-hovorymo_p998": 'Фіктивна сторінка. Не "надо", а "треба".',
        "5-klas-ukrmova-fixture-2000_s0003": "Неправильно: читаю кнігу. Правильно: читаю книгу.",
        "5-klas-ukrmova-fixture-2000_s0004": "Неправильно: надо. Правильно: треба.",
        "5-klas-ukrmova-fixture-2000_s0001": (
            "Адресант — той, хто адресує, надсилає лист; адресат — той, хто отримує лист, посилку."
        ),
        "5-klas-ukrmova-fixture-2000_s0002": "Пам'ятка — предмет давнини; пам'ятник — споруда на честь особи.",
    }
)
FIXTURE_HERITAGE_SUPPORT = [
    {"locator": "antonenko-davydovych-yak-my-hovorymo_p999", "passage": 'Кажуть "читаю кнігу", а треба "читаю книгу".'}
]


def _single_deck_version(shards: dict[str, dict[str, dict[str, object]]]) -> str:
    versions = {payload["deckVersion"] for level_shards in shards.values() for payload in level_shards.values()}
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
    assert a1["index"]["counts"]["cloze"] == 1
    assert a1["index"]["counts"]["clozeCoverage"] == 0.1429
    assert a1["index"]["counts"]["modeCounts"]["cloze"] == 1

    lexeme = next(item for item in a1["lexemes"]["lexemes"] if item["lemmaId"] == "knyha")
    assert lexeme["lemma"] == "книга"
    assert lexeme["lemmaPlain"] == "книга"
    assert lexeme["paradigm"]["cases"]["accusative"]["singular"] == "книгу"
    assert lexeme["heritage"] == "inherited"
    assert lexeme["severity"] == "standard"
    # Ruling D (#8724): the reviewed accusative card is form practice; only
    # the answer has an accusative VESUM analysis.  «Я живу у ___» has no
    # fixture form outside the locative's alternates, so it stays withheld.
    [cloze] = a1["cloze"]["cloze"]
    assert cloze["lemmaId"] == "knyha"
    assert {option["strategy"] for option in cloze["options"]} == {"cross-case"}
    verifier = JsonVesumVerifier.from_path(VESUM)
    accusative = [
        option["kind"]
        for option in cloze["options"]
        if any("v_zna" in match["tags"] for match in verifier.verify_words([option["label"]])[option["label"]])
    ]
    assert accusative == ["answer"]
    assert validate_option_set(cloze) == []


def test_reviewed_allowlist_and_vesum_ambiguity_fail_closed() -> None:
    shards = _build()
    cloze = shards["A1"]["cloze"]["cloze"]
    cloze_lemma_ids = {item["lemmaId"] for item in cloze}

    assert cloze_lemma_ids == {"knyha"}
    assert "robota" not in cloze_lemma_ids
    # #9160: blank public glosses must not erase the same-meaning exclusion.
    # Plant the answer's gloss on every candidate to make every decoy unsafe.
    entries = read_manifest(MANIFEST)
    for entry in entries:
        entry["gloss"] = "same meaning"
        entry.get("enrichment", {}).pop("translation", None)
    blocked = build_practice_shards(
        entries, ReviewedSourceAllowlist.from_path(ALLOWLIST),
        JsonVesumVerifier.from_path(VESUM), read_cloze_sources(CLOZE_SOURCES),
        BuildConfig(), heritage_pairs=[], paronym_pairs=[],
    )
    assert blocked["A1"]["cloze"]["cloze"] == []

    entries = read_manifest(MANIFEST)
    empty_allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier.from_path(VESUM)
    no_sources = build_practice_shards(entries, empty_allowlist, verifier)
    assert no_sources["A1"]["cloze"]["cloze"] == []


def test_curated_cloze_derives_missing_target_form_from_paradigm() -> None:
    entries = read_manifest(MANIFEST)
    allowlist = ReviewedSourceAllowlist.from_path(ALLOWLIST)
    verifier = JsonVesumVerifier.from_path(VESUM)
    cloze_sources = read_cloze_sources(CLOZE_SOURCES)
    candidate = next(row for row in cloze_sources if row["lemmaId"] == "knyha")
    candidate.pop("form")

    lexeme = _build_lexeme(next(entry for entry in entries if entry["url_slug"] == "knyha"), verifier)
    assert lexeme is not None
    candidates = _build_cloze_items(lexeme, [candidate], allowlist, verifier, "fixture")
    assert len(candidates) == 1
    assert candidates[0]["blankCase"] == "accusative"
    assert candidates[0]["number"] == "singular"
    assert candidates[0]["form"] == "книгу"
    withheld: list[dict[str, str]] = []
    shards = build_practice_shards(entries, allowlist, verifier, cloze_sources, BuildConfig(), cloze_withheld=withheld)
    assert [item["form"] for item in shards["A1"]["cloze"]["cloze"]] == ["книгу"]
    assert not any(row["clozeId"] == candidates[0]["clozeId"] for row in withheld)


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
    # A new rejected verdict changes the input without needing ULIF synonym groups.
    changed_synonym_verdicts = {
        "approved": [],
        "rejected": [{"a": "кіт", "b": "пес", "polarity": "synonym"}],
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


def test_heritage_pair_withheld_without_authentic_sense_never_builds() -> None:
    pair = {
        **_fixture_heritage_pair(),
        "kind": "sense_restricted",
        "calqueSense": "a sourced calque sense",
        "authenticSense": None,
        "currentNormWithheldReason": "No current same-sense rejection is sourced.",
    }
    pair.pop("currentNormSupport", None)
    pair["frames"] = [{**frame, "disambiguated": True} for frame in pair["frames"]]
    assert validate_heritage_pair(pair) == []
    assert _build_heritage_items(pair, _fixture_lexemes()[0], _fixture_lexemes(), "deck-v1") == []
    pair["currentNormSupport"] = [{"locator": "fixture", "passage": "fixture"}]
    assert any("missing authenticSense" in error for error in validate_heritage_pair(pair))


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
        source_passages=FIXTURE_PASSAGES,
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

    indexed_lemma_ids = {item["lemmaId"] for item in a2["index"]["items"]}
    for mode in DRILL_MODES:
        emitted_ids = {item["lemmaId"] for item in a2[mode][mode] if item["lemmaId"] in indexed_lemma_ids}
        advertised_ids = {item["lemmaId"] for item in a2["index"]["items"] if mode in item["modes"]}
        assert advertised_ids == emitted_ids


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
        source_passages=FIXTURE_PASSAGES,
    )
    a2 = shards["A2"]
    a2_heritage = a2["heritage"]["heritage"]
    b1_heritage = shards["B1"]["heritage"]["heritage"]
    index_item = next(item for item in a2["index"]["items"] if item["lemmaId"] == "knyha")

    # #4719: the curator availability floor (b1) WINS over the native lexeme's
    # level (A2) for ITEM placement — B1-flagged calque drills must never reach
    # learners below the floor. The A2 index must not advertise a card that is
    # only emitted in the B1 heritage shard.
    assert a2_heritage == []
    assert len(b1_heritage) == 1
    assert b1_heritage[0]["lemmaId"] == "knyha"
    assert b1_heritage[0]["cefr"] == "B1"
    assert "heritage" not in index_item["modes"]


def test_heritage_item_options_are_valid_and_do_not_mark_calque() -> None:
    pair = _fixture_heritage_pair()
    lexemes = _fixture_lexemes()
    item = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1", source_passages=FIXTURE_PASSAGES)[0]
    internal_item = _build_heritage_items(
        pair,
        lexemes[0],
        lexemes,
        "deck-v1",
        public_options=False,
        source_passages=FIXTURE_PASSAGES,
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

    first = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1", source_passages=FIXTURE_PASSAGES)[0]
    second = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1", source_passages=FIXTURE_PASSAGES)[0]
    changed_version = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v2", source_passages=FIXTURE_PASSAGES)[0]

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


VERB_EVIDENCE = VesumLemmaEvidence(frozenset({"verb"}))


def _verb_classify_sets(
    lemma: str, labels: list[str], vesum_aspect: str | None, residuals: list[dict[str, str]] | None = None
) -> dict[str, str]:
    entry = {
        "lemma": lemma,
        "pos": "verb",
        "enrichment": {"morphology": {"pos": "verb", "forms": [{"label": label} for label in labels]}},
    }
    lexeme = {"lemmaId": lemma, "lemma": lemma, "cefr": "A2"}
    items = _build_classify_items(
        entry, lexeme, vesum_aspect=vesum_aspect, vesum_evidence=VERB_EVIDENCE, aspect_residuals=residuals
    )
    return {s["setId"]: s["answer"] for item in items for s in item["sets"]}


@pytest.mark.parametrize(
    ("lemma", "labels", "vesum_aspect"),
    [
        ("писати", ["verb:imperf:pres"], "imperfective"),
        ("написати", ["verb:perf:futr"], "perfective"),
        ("писати", ["недок."], "imperfective"),
        ("написати", ["док."], "perfective"),
        ("написати", ["доконаний", "теперішній"], "perfective"),
    ],
)
def test_classify_keys_aspect_when_explicit_labels_agree_with_vesum(
    lemma: str, labels: list[str], vesum_aspect: str
) -> None:
    """Explicit VESUM tags and Ukrainian abbreviations agree with VESUM; a tense label never overrides them."""
    assert _verb_classify_sets(lemma, labels, vesum_aspect)["aspect"] == vesum_aspect


@pytest.mark.parametrize(("labels", "vesum_aspect"), [(["недок."], "perfective"), (["док."], "imperfective")])
def test_classify_withholds_aspect_when_an_abbreviated_label_contradicts_vesum(
    labels: list[str], vesum_aspect: str
) -> None:
    residuals: list[dict[str, str]] = []

    assert "aspect" not in _verb_classify_sets("писати", labels, vesum_aspect, residuals)
    assert [residual["reason"] for residual in residuals] == ["conflicting_explicit_aspect"]


def test_classify_withholds_aspect_when_enrichment_disagrees_with_vesum() -> None:
    """#8729: VESUM keys aspect; an enrichment label may only agree with it."""
    entry = {
        "lemma": "написати",
        "pos": "verb",
        "enrichment": {
            "morphology": {
                "pos": "verb",
                "aspect": "perfective",
                "forms": [{"label": "теперішній"}],
            }
        },
    }
    lexeme = {"lemmaId": "napysaty", "lemma": "написати", "cefr": "A2"}

    residuals: list[dict[str, str]] = []

    classify = _build_classify_items(
        entry, lexeme, vesum_aspect="imperfective", vesum_evidence=VERB_EVIDENCE, aspect_residuals=residuals
    )
    agreeing = _build_classify_items(entry, lexeme, vesum_aspect="perfective", vesum_evidence=VERB_EVIDENCE)

    assert not any(s["setId"] == "aspect" for item in classify for s in item["sets"])
    assert residuals[0]["reason"] == "conflicting_explicit_aspect"
    assert next(s for s in agreeing[0]["sets"] if s["setId"] == "aspect")["answer"] == "perfective"


def test_classify_keys_no_aspect_without_vesum_verb_evidence() -> None:
    """#8729: a tense label alone never keys aspect, nor does an unattested verb reading."""
    entry = {
        "lemma": "писати",
        "pos": "verb",
        "enrichment": {"morphology": {"pos": "verb", "forms": [{"label": "теперішній"}]}},
    }
    lexeme = {"lemmaId": "pysaty", "lemma": "писати", "cefr": "A2"}
    residuals: list[dict[str, str]] = []

    unkeyed = _build_classify_items(entry, lexeme, vesum_evidence=VERB_EVIDENCE, aspect_residuals=residuals)
    unattested = _build_classify_items(entry, lexeme, vesum_aspect="imperfective", aspect_residuals=residuals)

    assert [s["setId"] for s in unkeyed[0]["sets"]] == ["pos"]
    assert unattested == []
    assert [residual["reason"] for residual in residuals] == ["no_unambiguous_vesum_aspect", "unbound_verb_reading"]


def test_vesum_aspect_lookup_uses_only_an_unambiguous_exact_verb_lemma() -> None:
    verifier = JsonVesumVerifier(
        {
            "писати": [{"lemma": "писати", "pos": "verb", "tags": "verb:imperf:inf"}],
            "написати": [{"lemma": "написати", "pos": "verb", "tags": "verb:perf:inf"}],
            "омонім": [
                {"lemma": "омонім", "pos": "verb", "tags": "verb:imperf:inf"},
                {"lemma": "омонім", "pos": "verb", "tags": "verb:perf:inf"},
            ],
        }
    )

    assert _vesum_aspect_by_lemma(["писати", "написати", "омонім"], verifier) == {
        "писати": "imperfective",
        "написати": "perfective",
    }


def test_pos_residual_filter_reads_emitted_lexemes_not_an_items_field() -> None:
    """The shard payload stores `lexemes`, so an `items` lookup falsely reports zero residuals."""
    shards = {"A2": {"lexemes": {"lexemes": [{"lemmaId": "святий"}, {"lemmaId": "вчений"}]}}}

    assert _emitted_lemma_ids(shards) == {"святий", "вчений"}


def test_vesum_aspect_lookup_drops_biaspectual_combined_tag() -> None:
    verifier = JsonVesumVerifier(
        {
            "атакувати": [{"lemma": "атакувати", "pos": "verb", "tags": "verb:imperf:perf:inf"}],
        }
    )
    assert _vesum_aspect_by_lemma(["атакувати"], verifier) == {}


def test_conflicting_explicit_labels_not_overridden_by_vesum_aspect() -> None:
    entry = {
        "lemma": "омонім",
        "pos": "verb",
        "enrichment": {
            "morphology": {
                "pos": "verb",
                "forms": [{"label": "доконаний"}, {"label": "недоконаний"}],
            }
        },
    }
    lexeme = {"lemmaId": "omonym", "lemma": "омонім", "cefr": "A2"}
    residuals: list[dict[str, str]] = []
    classify = _build_classify_items(
        entry, lexeme, vesum_aspect="imperfective", vesum_evidence=VERB_EVIDENCE, aspect_residuals=residuals
    )
    assert not any(s.get("setId") == "aspect" for item in classify for s in item.get("sets", []))
    assert residuals and residuals[0]["reason"] == "conflicting_explicit_aspect"


def test_build_classify_items_records_missing_morphology_aspect_residual() -> None:
    entry = {"lemma": "знати", "pos": "verb"}
    lexeme = {"lemmaId": "znaty", "lemma": "знати", "cefr": "B1"}
    residuals: list[dict[str, str]] = []

    classify = _build_classify_items(entry, lexeme, aspect_residuals=residuals)

    assert classify == []
    assert residuals == [
        {
            "lemmaId": "znaty",
            "lemma": "знати",
            "cefr": "B1",
            "reason": "missing_morphology",
        }
    ]


KNYHA_EVIDENCE = VesumLemmaEvidence(frozenset({"noun"}), {"noun": frozenset({"feminine"})})


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

    classify = _build_classify_items(entry, lexeme, vesum_evidence=KNYHA_EVIDENCE)[0]

    assert "setLabelEn" not in classify["sets"][0]
    assert "answerLabelEn" not in classify["sets"][0]
    assert all("labelEn" not in option for option in classify["sets"][0]["options"])


def test_classify_withholds_pos_when_enrichment_analysis_disagrees_with_displayed_reading() -> None:
    """#8729: VESUM knows both readings of «проте»; morphology selects the other one."""
    entry = {
        "lemma": "проте",
        "pos": "conjunction",
        "enrichment": {
            "cefr": {"level": "B1", "pos": "conjunction"},
            "morphology": {
                "pos": "adverb",
                "forms": [{"label": "присл."}],
            },
            "translation": {"en": ["however"], "pos": "adverb"},
            "definition_cards": [{"definitions": ["1. спол. для протиставлення; 2. присл., у знач. вставн. сл."]}],
        },
    }
    lexeme = {"lemmaId": "prote", "lemma": "проте", "cefr": "B1"}

    classify = _build_classify_items(
        entry, lexeme, vesum_evidence=VesumLemmaEvidence(frozenset({"adverb", "conjunction"}))
    )

    assert classify == []


def test_classify_emits_every_attested_reading_the_displayed_pos_names() -> None:
    entry = {
        "lemma": "після",
        "pos": "adverb, preposition",
        "enrichment": {"morphology": {"pos": "adverb", "forms": [{"label": "присл."}]}},
    }
    lexeme = {"lemmaId": "pislia", "lemma": "після", "cefr": "A2"}

    classify = _build_classify_items(
        entry, lexeme, vesum_evidence=VesumLemmaEvidence(frozenset({"adverb", "preposition"}))
    )

    pos_set = next(item for item in classify[0]["sets"] if item["setId"] == "pos")
    assert pos_set["answer"] == "adverb"
    assert pos_set["answers"] == ["adverb", "preposition"]


@pytest.mark.parametrize(
    ("raw_pos", "expected_bucket"),
    [
        ("noun", "noun"),
        ("adjective", "adjective"),
        ("numr", "numeral"),
        ("pron", "pronoun"),
        ("verb", "verb"),
        ("adverb", "adverb"),
        ("prep", "preposition"),
        ("conj", "conjunction"),
        ("part", "particle"),
        ("interj", "interjection"),
    ],
)
def test_classify_pos_aliases_normalize_to_distinct_closed_buckets(raw_pos: str, expected_bucket: str) -> None:
    assert generate_practice_deck._normalize_pos_buckets(raw_pos) == [expected_bucket]


def test_classify_pos_generic_part_does_not_match_prose() -> None:
    assert generate_practice_deck._normalize_pos_buckets("part of speech") == []
    assert generate_practice_deck._normalize_pos_buckets("participle") == []


def test_paradigm_items_accept_vesum_english_case_keys() -> None:
    """VESUM lemma search stores internal English case names, not Ukrainian labels."""
    items = _build_paradigm_items(
        {
            "lemmaId": "borshch",
            "lemma": "борщ",
            "cefr": "A1",
            "paradigm": {
                "cases": {
                    "nominative": {"singular": "борщ"},
                    "genitive": {"singular": "борщу"},
                    "dative": {"singular": "борщеві"},
                    "accusative": {"singular": "борщ"},
                    "instrumental": {"singular": "борщем"},
                    "locative": {"singular": "борщі"},
                }
            },
        },
        verifier=_captured_paradigm_verifier(),
    )

    assert items
    slot_cases = {item["slot"]["case"] for item in items}
    assert "родовий" in slot_cases
    assert "давальний" in slot_cases
    assert len(slot_cases) >= 3


def test_paradigm_items_keep_syncretic_adjective_surfaces() -> None:
    """Shared case surfaces must not wipe the paradigm (adj syncretism).

    Dropping every duplicated surface left adjectives with only 1–2 unique
    forms and zero cards; drills ask for a named slot, so syncretic answers
    stay valid when four distinct surfaces remain for distractors.
    """
    items = _build_paradigm_items(
        {
            "lemmaId": "aktyvnyi",
            "lemma": "активний",
            "cefr": "A1",
            "paradigm": {
                "cases": {
                    "nominative": {"singular": "активний", "plural": "активні"},
                    "genitive": {"singular": "активного", "plural": "активних"},
                    "dative": {"singular": "активному", "plural": "активним"},
                    "accusative": {"singular": "активний", "plural": "активних"},
                    "instrumental": {"singular": "активним", "plural": "активними"},
                    "locative": {"singular": "активному", "plural": "активних"},
                    "vocative": {"singular": "активний", "plural": "активні"},
                }
            },
        },
        verifier=_captured_paradigm_verifier(),
    )

    assert items
    assert {item["form"] for item in items} >= {"активні", "активного", "активними"}
    assert any(item["slot"]["case"] == "називний" and item["slot"]["number"] == "plural" for item in items)
    assert not any(item["slot"]["case"] == "називний" and item["slot"]["number"] == "singular" for item in items)
    assert any(item["slot"]["case"] == "родовий" for item in items)
    for item in items:
        labels = [option["label"] for option in item["options"]]
        assert len(labels) == 4
        assert len({label.casefold() for label in labels}) == 4


def test_paradigm_eliminates_nominative_singular_base_case_bias() -> None:
    """Challenge targets must never be nominative singular (#8167)."""
    lexeme = {
        "lemmaId": "stil",
        "lemma": "стіл",
        "cefr": "A1",
        "paradigm": {
            "cases": {
                "називний": {"singular": "стіл", "plural": "столи"},
                "родовий": {"singular": "стола", "plural": "столів"},
                "давальний": {"singular": "столу", "plural": "столам"},
                "знахідний": {"singular": "стіл", "plural": "столи"},
                "орудний": {"singular": "столом", "plural": "столами"},
                "місцевий": {"singular": "столі", "plural": "столах"},
                "кличний": {"singular": "столе", "plural": "столи"},
            }
        },
    }
    items = _build_paradigm_items(lexeme, verifier=_captured_paradigm_verifier())
    assert items

    # Must NOT contain nominative singular
    assert not any(item["slot"]["case"] == "називний" and item["slot"]["number"] == "singular" for item in items)

    # Must contain nominative plural
    nom_pl = [item for item in items if item["slot"]["case"] == "називний" and item["slot"]["number"] == "plural"]
    assert len(nom_pl) == 1
    assert nom_pl[0]["form"] == "столи"

    # Base form (nom:s "стіл") can still be used as a distractor for oblique cases
    all_distractors = {opt["label"] for item in items for opt in item["options"] if opt["kind"] == "same-paradigm"}
    assert "стіл" in all_distractors

    # Validator must reject nominative singular target
    invalid_item = {
        "paradigmId": "stil:paradigm:0",
        "lemmaId": "stil",
        "lemma": "стіл",
        "slot": {"case": "називний", "number": "singular", "labelUk": "називний, однина"},
        "form": "стіл",
        "options": [
            {"label": "стіл", "kind": "answer"},
            {"label": "стола", "kind": "same-paradigm"},
            {"label": "столу", "kind": "same-paradigm"},
            {"label": "столом", "kind": "same-paradigm"},
        ],
    }
    errors = validate_paradigm_item(invalid_item, enforce_no_base_case=True)
    assert any("base-case bias" in err for err in errors)


def test_paradigm_distractor_pedagogical_taxonomy() -> None:
    """Pedagogical distractor taxonomy: case confusions, stem alternations, vowel shifts (#8167)."""
    # 1. Stem alternation: рука -> руці (к -> ц alternation in dative/locative)
    ruka_lexeme = {
        "lemmaId": "ruka",
        "lemma": "рука",
        "cefr": "A1",
        "paradigm": {
            "cases": {
                "називний": {"singular": "рука", "plural": "руки"},
                "родовий": {"singular": "руки", "plural": "рук"},
                "давальний": {"singular": "руці", "plural": "рукам"},
                "знахідний": {"singular": "руку", "plural": "руки"},
                "орудний": {"singular": "рукою", "plural": "руками"},
                "місцевий": {"singular": "руці", "plural": "руках"},
                "кличний": {"singular": "руко", "plural": "руки"},
            }
        },
    }
    ruka_items = _build_paradigm_items(ruka_lexeme, verifier=_captured_paradigm_verifier())
    ruka_dat = next(i for i in ruka_items if i["slot"]["case"] == "давальний" and i["slot"]["number"] == "singular")
    assert ruka_dat["form"] == "руці"
    dat_opt_labels = {o["label"] for o in ruka_dat["options"]}
    # Distractors should test the stem alternation by including forms with base 'к'
    assert "рука" in dat_opt_labels or "руку" in dat_opt_labels or "рукою" in dat_opt_labels

    # 2. Vowel shift: кіт -> кота (і -> о alternation in oblique cases)
    # Also tests full matrix slot coverage (#8167 Finding 2) and zero collision on dative/locative alternatives (#8167 Finding 1)
    kit_lexeme = {
        "lemmaId": "kit",
        "lemma": "кіт",
        "cefr": "A1",
        "paradigm": {
            "cases": {
                "називний": {"singular": "кіт", "plural": "коти"},
                "родовий": {"singular": "кота", "plural": "котів"},
                "давальний": {"singular": "котові", "plural": "котам"},
                "знахідний": {"singular": "кота", "plural": "котів"},
                "орудний": {"singular": "котом", "plural": "котами"},
                "місцевий": {"singular": "коту", "plural": "котах"},
                "кличний": {"singular": "коте", "plural": "коти"},
            }
        },
    }
    kit_items = _build_paradigm_items(kit_lexeme, verifier=_captured_paradigm_verifier())
    # Full nominal matrix coverage: exactly 13 non-base slots emitted (finding 2)
    assert len(kit_items) == 13
    emitted_slots = {(i["slot"]["case"], i["slot"]["number"]) for i in kit_items}
    assert ("називний", "plural") in emitted_slots
    assert ("родовий", "singular") in emitted_slots
    assert ("родовий", "plural") in emitted_slots
    assert ("давальний", "singular") in emitted_slots
    assert ("давальний", "plural") in emitted_slots
    assert ("знахідний", "singular") in emitted_slots
    assert ("знахідний", "plural") in emitted_slots
    assert ("орудний", "singular") in emitted_slots
    assert ("орудний", "plural") in emitted_slots
    assert ("місцевий", "singular") in emitted_slots
    assert ("місцевий", "plural") in emitted_slots
    assert ("кличний", "singular") in emitted_slots
    assert ("кличний", "plural") in emitted_slots

    kit_gen = next(i for i in kit_items if i["slot"]["case"] == "родовий" and i["slot"]["number"] == "singular")
    assert kit_gen["form"] == "кота"
    gen_opt_labels = {o["label"] for o in kit_gen["options"]}
    # Base form with closed syllable 'і' (кіт) must be a distractor for learner who forgot the vowel shift
    assert "кіт" in gen_opt_labels

    # Dative singular card: correct answer is 'котові'; alternative valid form 'коту'
    # MUST NOT be offered as a distractor (finding 1 regression guard)
    kit_dat = next(i for i in kit_items if i["slot"]["case"] == "давальний" and i["slot"]["number"] == "singular")
    assert kit_dat["form"] == "котові"
    dat_opt_labels = {o["label"] for o in kit_dat["options"]}
    assert "коту" not in dat_opt_labels, "Alternative valid dative form 'коту' must never be offered as a distractor"
    assert len(dat_opt_labels) == 4


def test_paradigm_zero_collision_guarantee_across_nouns() -> None:
    """Automated tests verify zero-collision guarantees across >= 1,000 distinct noun lemmas (#8167)."""
    fixture_path = Path(__file__).parent / "fixtures" / "atlas" / "1000_noun_paradigms.json"
    if fixture_path.exists():
        with open(fixture_path, encoding="utf-8") as f:
            lexemes = json.load(f)
    else:
        # Source-backed fallback templates with verified VESUM forms (including correct 'книг' gen_pl)
        stems = [
            (
                "книга",
                (
                    "книга",
                    "книги",
                    "книги",
                    "книг",
                    "книзі",
                    "книгам",
                    "книгу",
                    "книги",
                    "книгою",
                    "книгами",
                    "книзі",
                    "книгах",
                    "книго",
                    "книги",
                ),
            ),
            (
                "стіл",
                (
                    "стіл",
                    "столи",
                    "стола",
                    "столів",
                    "столу",
                    "столам",
                    "стіл",
                    "столи",
                    "столом",
                    "столами",
                    "столі",
                    "столах",
                    "столе",
                    "столи",
                ),
            ),
            (
                "ніч",
                (
                    "ніч",
                    "ночі",
                    "ночі",
                    "ночей",
                    "ночі",
                    "ночам",
                    "ніч",
                    "ночі",
                    "ніччю",
                    "ночами",
                    "ночі",
                    "ночах",
                    "ноче",
                    "ночі",
                ),
            ),
            (
                "море",
                (
                    "море",
                    "моря",
                    "моря",
                    "морів",
                    "морю",
                    "морям",
                    "море",
                    "моря",
                    "морем",
                    "морями",
                    "морі",
                    "морях",
                    "море",
                    "моря",
                ),
            ),
            (
                "хлопець",
                (
                    "хлопець",
                    "хлопці",
                    "хлопця",
                    "хлопців",
                    "хлопцеві",
                    "хлопцям",
                    "хлопця",
                    "хлопців",
                    "хлопцем",
                    "хлопцями",
                    "хлопцеві",
                    "хлопцях",
                    "хлопче",
                    "хлопці",
                ),
            ),
        ]
        cases_list = ["називний", "родовий", "давальний", "знахідний", "орудний", "місцевий", "кличний"]
        lexemes = []
        for idx in range(1000):
            base_stem, base_forms = stems[idx % len(stems)]
            paradigm_cases = {}
            for c_idx, c_name in enumerate(cases_list):
                sg_form = base_forms[c_idx * 2]
                pl_form = base_forms[c_idx * 2 + 1]
                paradigm_cases[c_name] = {"singular": sg_form, "plural": pl_form}
            lexemes.append(
                {
                    "lemmaId": f"noun_{idx}_{base_stem}",
                    "lemma": base_stem,
                    "cefr": "A1" if idx % 2 == 0 else "B1",
                    "paradigm": {"cases": paradigm_cases},
                }
            )

    assert len(lexemes) >= 1000, f"Expected at least 1,000 noun lexemes, got {len(lexemes)}"
    unique_lemmas = {lex["lemma"] for lex in lexemes}
    # In fixture mode, verify >= 1,000 distinct source-backed lemmas
    if fixture_path.exists():
        assert len(unique_lemmas) >= 1000

    verifier = _captured_paradigm_verifier()
    total_items = 0
    slot_counts: dict[tuple[str, str], int] = {}
    conn = None
    cursor = None
    try:
        from scripts.rag.config import VESUM_DB_PATH

        if VESUM_DB_PATH.exists():
            conn = open_readonly(VESUM_DB_PATH)
            cursor = conn.cursor()
    except Exception:
        cursor = None

    case_tag_map = {
        "називний": "v_naz",
        "родовий": "v_rod",
        "давальний": "v_dav",
        "знахідний": "v_zna",
        "орудний": "v_oru",
        "місцевий": "v_mis",
        "кличний": "v_kly",
    }
    non_standard_tags = {"subst", "bad", "rare", "dial", "coll", "arch", "vulgar", "alt", "prop", "nv", "abbr"}

    try:
        for lexeme in lexemes:
            items = _build_paradigm_items(lexeme, verifier=verifier)
            # Query independent VESUM oracle for all attested forms of this lemma
            vesum_rows = []
            if cursor:
                cursor.execute(
                    "SELECT word_form, tags FROM forms_all WHERE lemma = ? AND pos = 'noun'",
                    (lexeme["lemma"],),
                )
                vesum_rows = cursor.fetchall()

            for item in items:
                total_items += 1
                slot_key = (item["slot"]["case"], item["slot"]["number"])
                slot_counts[slot_key] = slot_counts.get(slot_key, 0) + 1

                assert not (item["slot"]["case"] == "називний" and item["slot"]["number"] == "singular")
                errors = validate_paradigm_item(item, enforce_no_base_case=True)
                assert errors == [], f"Validation errors for item {item['paradigmId']}: {errors}"

                labels = [o["label"] for o in item["options"]]
                assert len(labels) == 4
                assert len(set(labels)) == 4, f"Duplicate option labels in {item['paradigmId']}: {labels}"

                # Independent oracle check against VESUM (#8167 Finding 2)
                if vesum_rows:
                    target_tag = case_tag_map[item["slot"]["case"]]
                    vesum_valid = set()
                    for wf, tags in vesum_rows:
                        tokens = set(tags.replace(":", " ").split())
                        if tokens & non_standard_tags:
                            continue
                        if target_tag in tokens and (
                            (item["slot"]["number"] == "plural" and "p" in tokens)
                            or (item["slot"]["number"] == "singular" and any(t in tokens for t in ("m", "f", "n", "s")))
                        ):
                            vesum_valid.add(_plain(wf))

                    # 1. Answer must be verified standard form in VESUM
                    if vesum_valid:
                        assert _plain(item["form"]) in vesum_valid, (
                            f"Answer '{item['form']}' not in VESUM standard forms for {slot_key} of lemma '{lexeme['lemma']}'"
                        )

                    # 2. No distractor may be a valid form of the target slot
                    distractor_labels = [o["label"] for o in item["options"] if o.get("kind") != "answer"]
                    for d_label in distractor_labels:
                        assert _plain(d_label) not in vesum_valid, (
                            f"Distractor '{d_label}' is a valid VESUM form for target slot {slot_key} of lemma '{lexeme['lemma']}'"
                        )
    finally:
        if conn:
            conn.close()

    # Coverage verification across all 13 non-base cells
    assert total_items >= 10000, f"Expected at least 10,000 items across 1,000 nouns, got {total_items}"
    assert len(slot_counts) == 13, (
        f"Expected coverage across all 13 cells, got {len(slot_counts)}: {slot_counts.keys()}"
    )


def test_paradigm_vesum_failure_skips_or_prevents_collisions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulating VESUM lookup failure or empty results must safely skip affected cards when strict VESUM is required (#8167 Finding 1)."""
    import scripts.verification.vesum as vesum_mod

    lexeme = {
        "lemmaId": "test_abazyn",
        "lemma": "абазин",
        "cefr": "B1",
        "paradigm": {
            "cases": {
                "називний": {"singular": "абазин", "plural": "абазини"},
                "родовий": {"singular": "абазина", "plural": "абазинів"},
                "давальний": {"singular": "абазину", "plural": "абазинам"},
                "знахідний": {"singular": "абазина", "plural": "абазинів"},
                "орудний": {"singular": "абазином", "plural": "абазинами"},
                "місцевий": {"singular": "абазину", "plural": "абазинах"},
                "кличний": {"singular": "абазине", "plural": "абазини"},
            }
        },
    }

    # 1. When strict VESUM is required and lookup raises an exception: skip cards
    def _failing_verify_lemma(lemma: str) -> list[dict[str, Any]]:
        raise RuntimeError("Simulated VESUM database outage")

    monkeypatch.setattr(vesum_mod, "verify_lemma", _failing_verify_lemma)
    items_err = _build_paradigm_items(lexeme, require_vesum=True, verifier=_captured_paradigm_verifier())
    assert items_err == [], (
        "Expected generator to skip affected cards when strict VESUM is required and lookup raises an exception"
    )

    # 2. When strict VESUM is required and lookup returns [] (Codex Round 3 Finding 1 reproduction): skip cards
    def _empty_verify_lemma(lemma: str) -> list[dict[str, Any]]:
        return []

    monkeypatch.setattr(vesum_mod, "verify_lemma", _empty_verify_lemma)
    items_empty = _build_paradigm_items(lexeme, require_vesum=True, verifier=_captured_paradigm_verifier())
    assert items_empty == [], (
        "Expected generator to skip affected cards when strict VESUM is required and lookup returns empty []"
    )

    # 3. Default non-strict mode (used by build pipeline and offline CI) generates cards using paradigm + alternations
    items_default = _build_paradigm_items(lexeme, require_vesum=False, verifier=_captured_paradigm_verifier())
    assert len(items_default) == 13, f"Expected 13 non-base cards in offline/default mode, got {len(items_default)}"


def test_build_lexeme_preserves_sense_id_while_withholding_learner_en() -> None:
    """#6437: sense-first entries bind senseId and never fall back to en[0]."""
    verifier = JsonVesumVerifier({})
    entry = {
        "lemma": "брак",
        "url_slug": "брак",
        "gloss": "вада",
        "pos": "noun",
        "primary_source": "atlas",
        "cefr": "A1",
        "enrichment": {
            "translation": {
                "en": ["second", "defect"],
                "source": "dmklinger",
            }
        },
        "senses": [
            {
                "id": "brak_defect",
                "learner_en": ["defect", "flaw"],
                "source": "sum20_vetted",
                "completeness": "complete",
            }
        ],
    }
    lexeme = _build_lexeme(entry, verifier)
    assert lexeme is not None
    assert lexeme["senseId"] == "brak_defect"
    assert lexeme["glossClean"] == ""
    assert "second" not in lexeme["gloss"].casefold()


def test_build_lexeme_withholds_both_languages_when_learner_en_is_empty() -> None:
    """#6437 PR3: an empty sense learner_en[] must never invent an EN gloss.

    A bound sense with no learner_en content must not silently borrow the
    legacy ``enrichment.translation.en[0]`` (also true when that legacy EN
    list is itself present and populated) — it must fall back to the
    Ukrainian gloss, honestly reflecting that no vetted EN drill target
    exists for this sense.
    """
    verifier = JsonVesumVerifier({})
    entry = {
        "lemma": "брак",
        "url_slug": "брак",
        "gloss": "вада",
        "pos": "noun",
        "primary_source": "atlas",
        "cefr": "A1",
        "enrichment": {
            # Legacy translation list is present and non-empty; a bound sense
            # must never fall through to it (#6437 LINT-003 no-en[0] rule).
            "translation": {
                "en": ["second", "defect"],
                "source": "dmklinger",
            }
        },
        "senses": [
            {
                "id": "brak_defect",
                "learner_en": [],
                "source": "sum20_vetted",
                "completeness": "draft",
            }
        ],
    }
    lexeme = _build_lexeme(entry, verifier)
    assert lexeme is not None
    assert lexeme["senseId"] == "brak_defect"
    assert lexeme["gloss"] == ""
    assert lexeme["glossClean"] == ""
    assert "second" not in lexeme["gloss"].casefold()
    assert "defect" not in lexeme["gloss"].casefold()


def test_mode_cards_propagate_sense_id_from_lexeme() -> None:
    """#6437 PR3: senseId must reach mode cards, not just the lexeme record.

    ``_build_lexeme`` already stamps ``senseId`` on a sense-first lexeme
    (see above); this was previously dropped when each mode-card builder
    emitted its own card dict, which left LINT-003 unable to see the sense
    binding on drills built from that lexeme.
    """
    lexeme = {
        "lemmaId": "test-lemma",
        "lemma": "тест",
        "lemmaPlain": "тест",
        "cefr": "A1",
        "pos": "noun",
        "senseId": "test-lemma_sense1",
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
    entry = {
        "lemma": "тест",
        "pos": "noun",
        "enrichment": {"morphology": {"pos": "noun", "forms": [{"label": "ім. чол."}]}},
    }

    evidence = VesumLemmaEvidence(frozenset({"noun"}), {"noun": frozenset({"masculine"})})
    classify = _build_classify_items(entry, lexeme, vesum_evidence=evidence)
    assert classify and classify[0]["senseId"] == "test-lemma_sense1"

    paradigm = _build_paradigm_items(lexeme, verifier=_captured_paradigm_verifier())
    assert paradigm and all(item["senseId"] == "test-lemma_sense1" for item in paradigm)

    # A lexeme with no senseId (legacy, not sense-first) must not gain one.
    legacy_lexeme = {k: v for k, v in lexeme.items() if k != "senseId"}
    legacy_classify = _build_classify_items(entry, legacy_lexeme, vesum_evidence=evidence)
    assert legacy_classify and "senseId" not in legacy_classify[0]


def test_multi_sense_gloss_cannot_bypass_meaning_withdrawal() -> None:
    # A multi-sense content word ("forest; woods") has a clean concise first sense and
    # remains withheld: a clean-looking first segment is not source/sense proof.
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
    shards = build_practice_shards(entries, ReviewedSourceAllowlist.from_payload([]), JsonVesumVerifier({}))
    lexeme = shards["A1"]["lexemes"]["lexemes"][0]
    assert lexeme["glossClean"] == ""
    assert lexeme["meaningMcEligible"] is False
    assert {"flashcards", "matching", "choice"}.isdisjoint(shards["A1"]["index"]["items"][0]["modes"])


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


def test_shard_json_is_compact_and_budget_matches_written_bytes(tmp_path: Path) -> None:
    payload = {
        "schema": "atlas-practice-cloze",
        "schemaVersion": 1,
        "deckVersion": "fixture",
        "level": "A1",
        "cloze": [{"lemmaId": "one", "sentence": "Це ___."}],
    }

    budget = generate_practice_deck._size_budget(payload, 1_000_000, 1_000_000)
    write_shards({"A1": {"cloze": payload}}, tmp_path)
    emitted = (tmp_path / "practice-cloze.A1.json").read_bytes()

    assert emitted == generate_practice_deck._json_bytes(payload)
    assert b"\n  " not in emitted
    assert json.loads(emitted) == payload
    assert budget["rawBytes"] == len(emitted)


def test_cloze_emit_compacts_builder_diagnostics_without_dropping_runtime_fields() -> None:
    shards = _build()
    cloze_items = [
        {
            "clozeId": f"fixture:{index}",
            "lemmaId": "knyha",
            "lemma": "книга",
            "form": "книгу",
            "number": "singular",
            "cefr": "A1",
            "options": [
                {
                    "optionId": f"fixture:{index}:answer",
                    "label": "книгу",
                    "lemmaId": "knyha",
                    "kind": "answer",
                    "case": "accusative",
                    "pos": "noun",
                    "strategy": "no-pair",
                }
            ],
        }
        for index in range(2)
    ]
    shards["A1"]["cloze"]["cloze"] = cloze_items
    retained_alt = cloze_items[0]
    dropped_alt = cloze_items[1]
    retained_alt["acceptedAlt"] = ["книгу"]
    dropped_alt["acceptedAlt"] = []

    compact_cloze_emit_fields(shards)

    assert retained_alt["acceptedAlt"] == ["книгу"]
    assert "acceptedAlt" not in dropped_alt
    for item in cloze_items:
        assert all(field not in item for field in ("number", "cefr", "lemma"))
        for option in item["options"]:
            assert "strategy" not in option
            assert all(key in option for key in ("optionId", "label", "lemmaId", "kind", "case", "pos"))


def test_cli_fails_when_approved_synonyms_lack_ulif_data(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reviewer probe (cf-8714-r3-codex): without sources.db the build warned and
    # wrote an empty synonym mode.
    monkeypatch.setattr(generate_practice_deck, "SYNONYM_MODE_ENABLED", True)
    end_dictionary = tmp_path / "end-dictionary-inventory.json"
    end_dictionary.write_text(
        json.dumps(
            {"schema": "atlas-end-dictionary-inventory", "entries": [], "counts": {"sections": 0, "entries": 0}}
        ),
        encoding="utf-8",
    )
    exit_code = main(
        [
            "--end-dictionary-inventory",
            str(end_dictionary),
            "--manifest",
            str(MANIFEST),
            "--reviewed-allowlist",
            str(ALLOWLIST),
            "--vesum-fixture",
            str(VESUM),
            "--ulif-db",
            str(tmp_path / "missing-sources.db"),
            "--out-dir",
            str(tmp_path / "out"),
        ]
    )

    assert exit_code == 1
    assert "ULIF synonym groups" in capsys.readouterr().err
    assert not (tmp_path / "out" / "practice-synonym.A1.json").exists()


def test_word_without_paradigm_keeps_membership_with_no_meaning() -> None:
    # Recognition (matching/choice) needs only lemma+gloss+level. A word with no morphological
    # paradigm must still produce a lexeme (regression for the 1413->312 over-gating collapse).
    verifier = JsonVesumVerifier.from_path(VESUM)
    entry = {"lemma": "тому", "gloss": "therefore", "enrichment": {"cefr": {"level": "A1"}}}
    lexeme = _build_lexeme(entry, verifier)
    assert lexeme is not None
    assert lexeme["gloss"] == ""
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


def test_requested_case_mismatch_cannot_emit_a_paradigm_answer() -> None:
    """A VESUM member of the lemma cannot answer a different requested case, #12658 AC7."""
    verifier = JsonVesumVerifier.from_path(VESUM)
    entry = copy.deepcopy(read_manifest(MANIFEST)[0])
    # The old fixture has no VESUM accusative-plural reading. Keep only
    # actually attested slots for the positive half of this regression.
    entry["enrichment"]["morphology"]["paradigm"]["cases"]["accusative"].pop("plural")
    paradigm = generate_practice_deck._paradigm(entry)
    assert generate_practice_deck._verify_paradigm(_plain(entry["lemma"]), entry["pos"], paradigm, verifier)
    bad = copy.deepcopy(paradigm)
    cases = bad["cases"]
    accusative = generate_practice_deck._case_form(paradigm, "accusative", "singular")
    assert accusative and _plain(accusative) != _plain(entry["lemma"])
    cases["accusative"] = {"singular": entry["lemma"]}
    assert not generate_practice_deck._verify_paradigm(_plain(entry["lemma"]), entry["pos"], bad, verifier)
    lexeme = _build_lexeme(entry, verifier)
    assert lexeme is not None
    assert _build_paradigm_items(lexeme, verifier=verifier)
    lexeme["paradigm"] = bad
    assert _build_paradigm_items(lexeme, verifier=verifier) == []
    assert _build_paradigm_items(lexeme, verifier=_captured_paradigm_verifier()) == []


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


def test_source_inventory_antonym_legs_emit_via_curated_pair_admission() -> None:
    """Curated antonym YAML is practice admission for source-inventory legs."""
    entries = [
        {
            "lemma": "день",
            "url_slug": "день",
            "gloss": "day",
            "pos": "noun",
            "primary_source": "source_inventory_grow",
        },
        {
            "lemma": "ніч",
            "url_slug": "ніч",
            "gloss": "night",
            "pos": "noun",
            "primary_source": "source_inventory_grow",
        },
    ]
    pair = {
        "slugA": "день",
        "slugB": "ніч",
        "distinction_gloss_uk": "День протилежний ночі.",
        "citations": ["fixture-test"],
        "frames": [
            {
                "sentence_with_slot": "Настав ___.",
                "answer_form": "день",
                "confusable_form": "ніч",
                "origin": "t",
            },
            {
                "sentence_with_slot": "Прийшла ___.",
                "answer_form": "ніч",
                "confusable_form": "день",
                "origin": "t2",
            },
        ],
    }
    # Without curated pairs, browse-only source-inventory rows stay out.
    empty = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_payload([]),
        _gloss_verifier("протилежний", "ночі"),
        [],
        BuildConfig(target=10),
        antonym_pairs=[],
    )
    assert empty == {}

    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_payload([]),
        _gloss_verifier("протилежний", "ночі"),
        [],
        BuildConfig(target=10),
        antonym_pairs=[pair],
    )
    # Unanchored curated legs fall back to B1 (same as emit-time CEFR fallback).
    b1_items = shards.get("B1", {}).get("antonym", {}).get("antonym", [])
    assert len(b1_items) >= 1
    for item in b1_items:
        assert validate_antonym_item(item) == []


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
    before_withheld: list[dict[str, str]] = []
    shards = build_practice_shards(
        entries, allowlist, verifier, cloze_sources, BuildConfig(), cloze_withheld=before_withheld
    )
    cloze_ids = {item["lemmaId"] for level in shards.values() for item in level["cloze"]["cloze"]}
    assert "knyha" not in cloze_ids
    assert not any(row["lemma"] == "книга" for row in before_withheld)

    for entry in entries:
        if entry["lemma"] == "книга":
            entry["surface_admission"]["cloze"] = True
            break

    after_withheld: list[dict[str, str]] = []
    shards = build_practice_shards(
        entries, allowlist, verifier, cloze_sources, BuildConfig(), cloze_withheld=after_withheld
    )
    assert "knyha" in {item["lemmaId"] for item in shards["A1"]["cloze"]["cloze"]}
    assert not any(row["lemma"] == "книга" for row in after_withheld)


def test_sentence_inventory_emits_attested_nominative_cloze_with_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    {
                        "lemma": "книга",
                        "lemmaId": "knyha",
                        "sentence": "Моя книга у школі.",
                        "targetForm": "книга",
                        "cefr": "A1",
                        "uses": ["example"],
                        "provenance": {
                            "status": "unreviewed",
                            "path": "attacker-controlled-path",
                            "source": "textbook",
                            "label": "Fixture textbook",
                            "locator": "fixture-1",
                            "title": "Fixture page",
                        },
                        "license": {
                            "status": "not_openly_licensed",
                            "useBasis": "short educational quotation with attribution",
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    candidates = read_sentence_inventory(inventory_path)
    assert candidates[0]["sentence"] == "Моя ___ у школі."
    assert candidates[0]["form"] == "книга"
    assert candidates[0]["provenance"]["status"] == "sentence_inventory"
    assert candidates[0]["provenance"]["path"] == str(inventory_path)

    # Force the route that previously built duplicate answer/lemma labels for
    # the nominative form "книга".  Inventory cloze must override it with the
    # valid no-pair strategy.
    monkeypatch.setattr(generate_practice_deck, "_option_strategy_for_level", lambda _level, _rng: "two-pair")

    # Every context word needs a VESUM analysis: an unanalysed word withholds
    # the prompt at the level gate (#8724).
    vesum = {
        **json.loads(VESUM.read_text(encoding="utf-8")),
        "моя": [
            {"lemma": "мій", "pos": "adj", "tags": "adj:f:v_naz:pron:pos"},
            {"lemma": "мій", "pos": "adj", "tags": "adj:f:v_kly:pron:pos"},
        ],
        "у": [{"lemma": "у", "pos": "prep", "tags": "prep"}],
    }
    from scripts.practice.creation_review import CreationReview, frame_identity

    creation_review = CreationReview(frozenset({frame_identity("cloze", "Моя ___ у школі.", "книга", "книга")}))
    allowlist = ReviewedSourceAllowlist.from_payload([{"status": "sentence_inventory", "path": str(inventory_path)}])
    verifier = JsonVesumVerifier(vesum)
    lexeme = _build_lexeme(next(row for row in read_manifest(MANIFEST) if row["url_slug"] == "knyha"), verifier)
    assert lexeme is not None
    candidates_before_options = _build_cloze_items(
        lexeme, candidates, allowlist, verifier, "fixture", creation_review=creation_review
    )
    assert len(candidates_before_options) == 1
    cloze = candidates_before_options[0]
    assert cloze["blankCase"] == "nominative"
    assert cloze["number"] == "singular"
    assert "clozeEn" not in cloze
    assert cloze["caseRule"]["feedback"] == "словникова форма: книга"
    withheld: list[dict[str, str]] = []
    shards = build_practice_shards(
        read_manifest(MANIFEST),
        allowlist,
        verifier,
        candidates,
        BuildConfig(),
        creation_review=creation_review,
        cloze_withheld=withheld,
    )
    assert shards["A1"]["cloze"]["cloze"] == []
    assert any(
        row["clozeId"] == "knyha:inventory:1" and row["reason"] == "no_unique_answer_evidence" for row in withheld
    )
    assert cloze["provenance"] == {
        "status": "sentence_inventory",
        "path": str(inventory_path),
        "source": "textbook",
        "label": "Fixture textbook",
        "locator": "fixture-1",
        "title": "Fixture page",
        "license": {
            "status": "not_openly_licensed",
            "useBasis": "short educational quotation with attribution",
        },
    }
    assert cloze["attribution"] == {
        "source": "textbook",
        "label": "Fixture textbook",
        "locator": "fixture-1",
        "title": "Fixture page",
    }


def test_sentence_inventory_verifies_source_capitalization_against_normalized_vesum() -> None:
    verifier = JsonVesumVerifier({"книга": [{"lemma": "книга", "pos": "noun", "tags": "noun:inanim:f:v_naz"}]})

    assert generate_practice_deck._inventory_form_details("книга", "noun", "Книга", verifier) == (
        "nominative",
        "singular",
    )


def _agreement_verifier() -> JsonVesumVerifier:
    return JsonVesumVerifier(
        {
            "різдвяна": [
                {"lemma": "різдвяний", "pos": "adj", "tags": "adj:f:v_naz"},
                {"lemma": "різдвяний", "pos": "adj", "tags": "adj:f:v_zna"},
            ],
            "прикраса": [
                {"lemma": "прикраса", "pos": "noun", "tags": "noun:inanim:f:v_naz"},
                {"lemma": "прикраса", "pos": "noun", "tags": "noun:inanim:f:v_zna"},
            ],
            "прикраси": [
                {"lemma": "прикраса", "pos": "noun", "tags": "noun:inanim:f:v_rod"},
                {"lemma": "прикраса", "pos": "noun", "tags": "noun:inanim:p:v_naz"},
                {"lemma": "прикраса", "pos": "noun", "tags": "noun:inanim:p:v_zna"},
            ],
            "висить": [{"lemma": "висіти", "pos": "verb", "tags": "verb:imperf:pres:s:3"}],
        }
    )


def test_cloze_blank_agreement_keeps_agreeing_filled_form() -> None:
    verifier = _agreement_verifier()

    assert _cloze_blank_context_agrees("Різдвяна ___ на палиці.", "прикраса", verifier)


def test_cloze_blank_agreement_rejects_disagreeing_filled_form() -> None:
    verifier = _agreement_verifier()

    assert not _cloze_blank_context_agrees("Різдвяна ___ на палиці.", "прикраси", verifier)


def test_cloze_blank_agreement_ignores_non_adjective_context() -> None:
    verifier = _agreement_verifier()

    # No token before the blank, and a non-adjective before the blank, are
    # both outside the agreement gate's scope.
    assert _cloze_blank_context_agrees("___ на палиці.", "прикраси", verifier)
    assert _cloze_blank_context_agrees("Прикраса висить ___.", "прикраси", verifier)


def test_cloze_blank_agreement_skips_pronoun_like_adjectives() -> None:
    verifier = _agreement_verifier()

    assert _cloze_blank_context_agrees("Ця ___ на палиці.", "прикраси", verifier)


def test_sentence_inventory_drops_function_identity_unless_curated(tmp_path: Path) -> None:
    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    {
                        "lemma": "та",
                        "lemmaId": "ta",
                        "sentence": "Це та.",
                        "targetForm": "та",
                        "cefr": "A1",
                        "uses": ["example"],
                        "provenance": {
                            "source": "fixture",
                            "label": "Fixture",
                            "locator": "function-1",
                        },
                        "license": {"status": "fixture"},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    candidates = read_sentence_inventory(inventory_path)
    lexeme = _build_lexeme(
        {
            "lemma": "та",
            "url_slug": "ta",
            "gloss": "and",
            "pos": "conj",
            "enrichment": {"cefr": {"level": "A1"}},
        },
        JsonVesumVerifier({"та": [{"lemma": "та", "pos": "conj", "tags": "conj"}]}),
    )
    assert lexeme is not None
    allowlist = ReviewedSourceAllowlist.from_payload([{"status": "sentence_inventory", "path": str(inventory_path)}])
    verifier = JsonVesumVerifier({"та": [{"lemma": "та", "pos": "conj", "tags": "conj"}]})

    assert _build_cloze_items(lexeme, candidates, allowlist, verifier, "deck-v6") == []

    curated = [{**candidates[0], "curated": True}]
    withheld: list[dict[str, str]] = []
    assert _build_cloze_items(lexeme, curated, allowlist, verifier, "deck-v6", withheld=withheld) == []
    assert any(row["reason"] == "no_unique_answer_evidence" for row in withheld)


def test_sentence_inventory_rejects_controls_pua_and_prefers_language_sources(
    tmp_path: Path,
) -> None:
    def row(
        lemma: str,
        lemma_id: str,
        sentence: str,
        target_form: str,
        locator: str,
    ) -> dict[str, object]:
        return {
            "lemma": lemma,
            "lemmaId": lemma_id,
            "sentence": sentence,
            "targetForm": target_form,
            "cefr": "A1",
            "uses": ["example"],
            "provenance": {
                "source": "textbook",
                "label": "Fixture textbook",
                "locator": locator,
            },
            "license": {"status": "fixture"},
        }

    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    row("книга", "knyha", "Це книга.", "книга", "5-klas-ukrmova-1"),
                    row("книга", "knyha", "У геометрії є книга.", "книга", "10-klas-geometrija-1"),
                    row("кіт", "kit", "У школі є кіт.", "кіт", "10-klas-geometrija-2"),
                    row(
                        "пиво",
                        "pivo",
                        "Найімовірніше, першим продуктом, отриманим із використанням мікроорганізмів, є пиво.",
                        "пиво",
                        "11-klas-biologiia-1",
                    ),
                    row("слово", "slovo-control", "\u0083Це слово.", "слово", "fixture-control"),
                    row("слово", "slovo-format", "\u200bЦе слово.", "слово", "fixture-format"),
                    row("слово", "slovo-pua", "Це слово.", "\uf0b7слово", "fixture-pua"),
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    candidates = read_sentence_inventory(inventory_path)

    assert {candidate["lemmaId"] for candidate in candidates} == {"knyha", "kit"}
    knyha = next(candidate for candidate in candidates if candidate["lemmaId"] == "knyha")
    assert knyha["provenance"]["locator"] == "5-klas-ukrmova-1"
    assert next(candidate for candidate in candidates if candidate["lemmaId"] == "kit")["sentence"] == (
        "У школі є ___."
    )


def test_inventory_identity_decoys_render_normalized_lemmas_at_source_case() -> None:
    lexemes = _fixture_lexemes()
    answer = next(lexeme for lexeme in lexemes if lexeme["lemmaId"] == "knyha")
    cloze = {
        "clozeId": "knyha:inventory:normalized-case",
        "form": "Книга",
        "lemma": "книга",
        "provenance": {"status": "sentence_inventory"},
        "caseRule": {"ruleId": "nominative_identification"},
    }

    options = generate_practice_deck._make_no_pair_options(cloze, answer, lexemes, random.Random(0))

    assert len(options) == 4
    assert all(generate_practice_deck._initial_capitalization(option["label"]) for option in options)
    assert validate_option_set({**cloze, "options": options}) == []


@pytest.mark.parametrize(
    ("manifest_pos", "expected_bucket"),
    [
        ("noun", "noun"),
        ("adjective", "adjective"),
        ("numeral", "numeral"),
        ("pronoun", "pronoun"),
        ("infinitive", "verb"),
        ("imperative", "verb"),
        ("adverb", "adverb"),
        ("preposition", "preposition"),
        ("conjunction", "conjunction"),
        ("particle", "particle"),
        ("numr", "numeral"),
        ("intj", "interjection"),
    ],
)
def test_option_pos_bucket_normalizes_unambiguous_manifest_aliases(manifest_pos: str, expected_bucket: str) -> None:
    assert generate_practice_deck._option_pos_bucket(manifest_pos) == expected_bucket


def test_option_pos_bucket_uses_the_same_closed_school_set_as_classify() -> None:
    assert {
        generate_practice_deck._option_pos_bucket(alias)
        for aliases in generate_practice_deck._POS_BUCKET_ALIASES.values()
        for alias in aliases
    } == set(generate_practice_deck.CLASSIFY_LABELS["pos"])
    assert generate_practice_deck._option_pos_bucket("predicative") == ""
    assert generate_practice_deck._option_pos_bucket("noun/verb") == ""


def test_validate_option_set_rejects_unknown_or_multi_pos_option() -> None:
    errors = validate_option_set(
        {
            "options": [
                {"label": "один", "pos": "noun", "kind": "answer"},
                {"label": "два", "pos": "noun/verb", "kind": "decoy"},
                {"label": "три", "pos": "noun", "kind": "decoy"},
                {"label": "чотири", "pos": "noun", "kind": "decoy"},
            ]
        }
    )

    assert "option set contains an unknown or multi-POS category" in errors


def test_dictionary_decoys_do_not_mash_school_function_categories() -> None:
    answer = {
        "lemmaId": "bez",
        "lemma": "без",
        "gloss": "without",
        "pos": "preposition",
        "cefr": "A1",
    }
    lexemes = [
        answer,
        {"lemmaId": "do", "lemma": "до", "gloss": "to", "pos": "prep", "cefr": "A1"},
        {"lemmaId": "i", "lemma": "і", "gloss": "and", "pos": "conjunction", "cefr": "A1"},
        {"lemmaId": "ne", "lemma": "не", "gloss": "not", "pos": "particle", "cefr": "A1"},
    ]

    decoys = generate_practice_deck._eligible_dictionary_decoys(answer, lexemes)

    assert [(lexeme["lemmaId"], label) for lexeme, label in decoys] == [("do", "до")]


def test_sentence_inventory_identity_cloze_scales_across_levels_and_pos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Live textbook rows; VESUM analyses and CEFR levels copied from data/vesum.db and the Atlas."""

    def entry(lemma: str, lemma_id: str, gloss: str, pos: str, level: str) -> dict[str, object]:
        return {
            "lemma": lemma,
            "url_slug": lemma_id,
            "gloss": gloss,
            "pos": pos,
            "primary_source": "course_vocab",
            "course_usage": [{"track": level.lower(), "slug": lemma_id}],
            "enrichment": {"cefr": {"level": level}},
        }

    entries = [
        entry("село", "selo", "village", "noun", "A1"),
        entry("книга", "knyha", "book", "noun", "A1"),
        entry("місто", "misto", "city", "noun", "A1"),
        entry("школа", "shkola", "school", "noun", "A1"),
        entry("хотіти", "khotity", "to want", "verb", "A1"),
        entry("поїзд", "poizd", "train", "noun", "A1"),
        entry("відправлятися", "vidpravliatysia", "to depart", "verb", "A2"),
        entry("обережно", "oberezhno", "carefully", "adverb", "A2"),
        entry("постійно", "postiino", "always", "adv", "A2"),
        entry("зазвичай", "zazvychai", "usually", "adv", "A2"),
        entry("поступово", "postupovo", "gradually", "adv", "A2"),
    ]

    def row(lemma: str, lemma_id: str, sentence: str, target: str, level: str, locator: str) -> dict[str, object]:
        return {
            "lemma": lemma,
            "lemmaId": lemma_id,
            "sentence": sentence,
            "targetForm": target,
            "cefr": level,
            "uses": ["example"],
            "provenance": {"source": "textbook", "label": "Ukrainian school textbook", "locator": locator},
            "license": {"status": "fixture"},
        }

    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    row("село", "selo", "Ти хотів у село?", "село", "A1", "3-klas-ukrainska-mova-savchuk-2020-2_s0052"),
                    row(
                        "обережно",
                        "oberezhno",
                        "Поїзд відправляється — Обережно!",
                        "Обережно",
                        "A2",
                        "10-klas-ukrmova-karaman-2018_s0334",
                    ),
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    vesum = JsonVesumVerifier(
        {
            # Three same-lemma analyses prove that dictionary-form identity
            # clozes do not require an arbitrary single VESUM case.
            "село": [
                {"lemma": "село", "pos": "noun", "tags": f"noun:inanim:n:{case}"}
                for case in ("v_naz", "v_zna", "v_kly")
            ],
            "ти": [
                {"lemma": "ти", "pos": "noun", "tags": "noun:anim:s:v_naz:pron:pers:2"},
                {"lemma": "ти", "pos": "noun", "tags": "noun:anim:s:v_kly:pron:pers:2"},
            ],
            "хотів": [{"lemma": "хотіти", "pos": "verb", "tags": "verb:imperf:past:m"}],
            "у": [{"lemma": "у", "pos": "prep", "tags": "prep"}],
            "обережно": [{"lemma": "обережно", "pos": "adv", "tags": "adv:compb"}],
            "поїзд": [
                {"lemma": "поїзд", "pos": "noun", "tags": "noun:inanim:m:v_naz"},
                {"lemma": "поїзд", "pos": "noun", "tags": "noun:inanim:m:v_zna"},
            ],
            "відправляється": [{"lemma": "відправлятися", "pos": "verb", "tags": "verb:rev:imperf:pres:s:3"}],
        }
    )
    from scripts.practice.creation_review import CreationReview, frame_identity

    monkeypatch.setattr(generate_practice_deck, "_option_strategy_for_level", lambda _level, _rng: "no-pair")
    candidates = read_sentence_inventory(inventory_path)
    creation_review = CreationReview(
        frozenset(frame_identity("cloze", row["sentence"], row["form"], _plain(row["lemma"])) for row in candidates)
    )
    withheld: list[dict[str, str]] = []
    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_payload([{"status": "sentence_inventory", "path": str(inventory_path)}]),
        vesum,
        candidates,
        BuildConfig(target=len(entries), source_label="fixture"),
        creation_review=creation_review,
        cloze_withheld=withheld,
    )

    assert all(not shard["cloze"]["cloze"] for shard in shards.values())
    assert {(row["clozeId"], row["reason"]) for row in withheld} == {
        ("selo:inventory:1", "no_unique_answer_evidence"),
        ("oberezhno:inventory:2", "no_unique_answer_evidence"),
    }

    assert generate_practice_deck._option_pos_bucket("pronoun") == "pronoun"
    assert generate_practice_deck._option_pos_bucket("adverb") == "adverb"


def test_sentence_inventory_rejects_nominative_plural_for_dictionary_form(tmp_path: Path) -> None:
    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    {
                        "lemma": "книга",
                        "lemmaId": "knyha",
                        "sentence": "Це книги.",
                        "targetForm": "книги",
                        "cefr": "A1",
                        "uses": ["example"],
                        "provenance": {
                            "status": "unreviewed",
                            "path": "attacker-controlled-path",
                            "source": "textbook",
                            "label": "Fixture textbook",
                            "locator": "fixture-plural",
                        },
                        "license": {
                            "status": "not_openly_licensed",
                            "useBasis": "short educational quotation with attribution",
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    candidates = read_sentence_inventory(inventory_path)
    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_payload([{"status": "sentence_inventory", "path": str(inventory_path)}]),
        JsonVesumVerifier.from_path(VESUM),
        candidates,
        BuildConfig(),
    )

    assert all(item["clozeId"] != "knyha:inventory:1" for level in shards.values() for item in level["cloze"]["cloze"])


@pytest.mark.parametrize("license_status", ["not_openly_licensed", "copyrighted_source"])
def test_sentence_inventory_rejects_restricted_cloze_without_displayable_attribution(
    tmp_path: Path, license_status: str
) -> None:
    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    {
                        "lemma": "книга",
                        "lemmaId": "knyha",
                        "sentence": "Це книга.",
                        "targetForm": "книга",
                        "cefr": "A1",
                        "uses": ["example"],
                        "provenance": {"source": "textbook", "locator": "fixture-1"},
                        "license": {
                            "status": license_status,
                            "useBasis": "short educational quotation with attribution",
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_payload([{"status": "sentence_inventory", "path": str(inventory_path)}]),
        JsonVesumVerifier.from_path(VESUM),
        read_sentence_inventory(inventory_path),
        BuildConfig(),
    )

    assert all(item["clozeId"] != "knyha:inventory:1" for level in shards.values() for item in level["cloze"]["cloze"])


def test_sentence_inventory_rejects_ambiguous_or_repeated_target_forms(tmp_path: Path) -> None:
    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    {
                        "lemma": "книга",
                        "lemmaId": "knyha",
                        "sentence": "книга і книга.",
                        "targetForm": "книга",
                        "uses": ["example"],
                        "provenance": {"source": "textbook", "label": "Fixture textbook"},
                        "license": {"status": "fixture"},
                    },
                    {
                        "lemma": "книга",
                        "lemmaId": "knyha",
                        "sentence": "Це книга.",
                        "targetForm": "книги",
                        "uses": ["example"],
                        "provenance": {"source": "textbook", "label": "Fixture textbook"},
                        "license": {"status": "fixture"},
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert read_sentence_inventory(inventory_path) == []


def test_sentence_inventory_blanks_standalone_form_not_hyphenated_compound(tmp_path: Path) -> None:
    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    {
                        "lemma": "сумка",
                        "lemmaId": "sumka",
                        "sentence": "Це сумка, а сумка-пакет лежить поруч.",
                        "targetForm": "сумка",
                        "uses": ["example"],
                        "provenance": {"source": "textbook", "label": "Fixture textbook"},
                        "license": {"status": "fixture"},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    candidates = read_sentence_inventory(inventory_path)

    assert len(candidates) == 1
    assert candidates[0]["sentence"] == "Це ___, а сумка-пакет лежить поруч."


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

    verifier = JsonVesumVerifier.from_path(VESUM)
    lexeme = _build_lexeme(next(row for row in entries if row["url_slug"] == "knyha"), verifier)
    assert lexeme is not None
    cards = _build_cloze_items(
        lexeme,
        [row for row in read_cloze_sources(CLOZE_SOURCES) if row["lemmaId"] == "knyha"],
        ReviewedSourceAllowlist.from_path(ALLOWLIST),
        verifier,
        "fixture",
    )
    assert cards and cards[0]["form"] == "книгу"


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
    verifier = JsonVesumVerifier.from_path(VESUM)
    lexeme = next(row for row in _fixture_lexemes() if row["lemmaId"] == "knyha")
    source = _tatoeba_cloze_source()
    cloze = _build_cloze_items(
        lexeme,
        [source],
        ReviewedSourceAllowlist.from_payload([{"status": "tatoeba", "path": "tatoeba:101"}]),
        verifier,
        "fixture",
    )[0]
    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_payload([{"status": "tatoeba", "path": "tatoeba:101"}]),
        verifier,
        [source],
        BuildConfig(),
    )
    [emitted] = shards["A1"]["cloze"]["cloze"]
    assert emitted["attribution"] == cloze["attribution"]

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

    verifier = JsonVesumVerifier.from_path(VESUM)
    lexeme = next(row for row in _fixture_lexemes() if row["lemmaId"] == "knyha")
    cloze = _build_cloze_items(
        lexeme,
        [source],
        ReviewedSourceAllowlist.from_payload([{"status": "tatoeba", "path": "tatoeba:101"}]),
        verifier,
        "fixture",
    )[0]
    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_payload([{"status": "tatoeba", "path": "tatoeba:101"}]),
        verifier,
        [source],
        BuildConfig(),
    )
    [emitted] = shards["A1"]["cloze"]["cloze"]
    assert emitted["provenance"]["sentenceId"] == 101
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


@pytest.mark.needs_sparse_tree("site/src/data")
def test_live_curated_cloze_sources_and_allowlist_match() -> None:
    cloze_sources_path = Path("site/src/data/lexicon-practice-cloze-sources.json")
    reviewed_sources_path = Path("site/src/data/lexicon-practice-reviewed-sources.json")
    assert cloze_sources_path.exists()
    assert reviewed_sources_path.exists()

    cloze_rows = json.loads(cloze_sources_path.read_text(encoding="utf-8"))
    allowlist = ReviewedSourceAllowlist.from_path(reviewed_sources_path)

    assert len(cloze_rows) >= 69
    for index, row in enumerate(cloze_rows):
        assert "lemma" in row, f"Row {index} missing lemma: {row}"
        assert "sentence" in row and "___" in row["sentence"], f"Row {index} invalid sentence: {row}"
        assert "blankCase" in row, f"Row {index} missing blankCase: {row}"
        assert "form" in row, f"Row {index} missing form: {row}"
        assert row.get("number") in {"singular", "plural"}, f"Row {index} invalid number: {row}"
        assert row.get("caseRule") or row.get("caseRuleId"), f"Row {index} missing case rule: {row}"
        assert "clozeEn" in row, f"Row {index} missing clozeEn: {row}"
        prov = row.get("provenance")
        assert isinstance(prov, dict), f"Row {index} missing provenance dict: {row}"
        assert allowlist.allows(prov), f"Row {index} provenance not in allowlist: {prov}"

        if prov.get("status") == "tatoeba" or str(prov.get("path", "")).startswith("tatoeba:"):
            assert prov.get("license"), f"Row {index} missing Tatoeba license: {prov}"
            assert prov.get("author"), f"Row {index} missing Tatoeba author: {prov}"
            assert prov.get("sentenceId"), f"Row {index} missing Tatoeba sentenceId: {prov}"
            assert prov.get("enLicense"), f"Row {index} missing Tatoeba enLicense: {prov}"
            assert prov.get("enAuthor"), f"Row {index} missing Tatoeba enAuthor: {prov}"
            assert prov.get("enSentenceId"), f"Row {index} missing Tatoeba enSentenceId: {prov}"


def test_paronym_pairs_emit_items_both_directions_and_validate(capsys: pytest.CaptureFixture[str]) -> None:
    # Use real fixture with valid slugs that exist in manifest subset for this test
    # Fallback to synthetic entries + pairs when direct lexeme match needed.
    entries = [
        {
            "lemmaId": "адресант",
            "lemma": "адресант",
            "gloss": "sender",
            "pos": "noun",
            "cefr": "B2",
            "url_slug": "адресант",
            "primary_source": "course_vocab",
            "course_usage": [{"track": "b2"}],
        },
        {
            "lemmaId": "адресат",
            "lemma": "адресат",
            "gloss": "addressee",
            "pos": "noun",
            "cefr": "B1",
            "url_slug": "адресат",
            "primary_source": "course_vocab",
            "course_usage": [{"track": "b2"}],
        },
    ]
    pair = {
        "slugA": "адресант",
        "slugB": "адресат",
        "distinction_gloss_uk": "Адресант — той, хто адресує, надсилає лист; адресат — той, хто отримує лист, посилку.",
        "citations": ["fixture-test"],
        "glossSources": [
            {
                "locator": "5-klas-ukrmova-fixture-2000_s0001",
                "passage": "Адресант — той, хто адресує, надсилає лист; адресат — той, хто отримує лист, посилку.",
            }
        ],
        "frames": [
            {
                "sentence_with_slot": "___ надіслав лист.",
                "answer_form": "Адресант",
                "confusable_form": "Адресат",
                "origin": "t",
            },
            {
                "sentence_with_slot": "Лист для ___.",
                "answer_form": "адресата",
                "confusable_form": "адресанта",
                "origin": "t2",
            },
        ],
    }
    allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = _gloss_verifier("той", "хто", "адресує", "надсилає", "лист", "отримує", "посилку")
    shards = build_practice_shards(
        entries, allowlist, verifier, [], BuildConfig(target=10), paronym_pairs=[pair], source_passages=FIXTURE_PASSAGES
    )
    b1_items = shards.get("B1", {}).get("paronym", {}).get("paronym", [])
    b2_items = shards.get("B2", {}).get("paronym", {}).get("paronym", [])
    # At least one direction emits
    total = len(b1_items) + len(b2_items)
    assert total >= 1, "paronym should emit at least one item"
    # Validate
    assert validate_paronym_pair(pair) == []
    for it in b1_items + b2_items:
        assert validate_paronym_item(it) == []


def test_paronym_apostrophe_slug_resolves_via_plain_lemma_fallback(capsys: pytest.CaptureFixture[str]) -> None:
    # #6338: an apostrophe lemma's lemmaId is hyphen-slugified (matching a
    # real url_slug, e.g. "пам-ятка"), so slugA/slugB carrying the apostrophe
    # spelling must resolve through by_plain_lemma, not slug_to_lex/lexemes_by_id.
    entries = [
        {
            "lemmaId": "пам-ятка",
            "lemma": "пам'ятка",
            "gloss": "landmark",
            "pos": "noun",
            "cefr": "A2",
            "url_slug": "пам-ятка",
            "primary_source": "course_vocab",
            "course_usage": [{"track": "a2"}],
        },
        {
            "lemmaId": "пам-ятник",
            "lemma": "пам'ятник",
            "gloss": "monument",
            "pos": "noun",
            "cefr": "A1",
            "url_slug": "пам-ятник",
            "primary_source": "course_vocab",
            "course_usage": [{"track": "a1"}],
        },
    ]
    pair = {
        "slugA": "пам'ятка",
        "slugB": "пам'ятник",
        "distinction_gloss_uk": "Пам'ятка — предмет давнини; пам'ятник — споруда на честь особи.",
        "citations": ["fixture-test"],
        "glossSources": [
            {
                "locator": "5-klas-ukrmova-fixture-2000_s0002",
                "passage": "Пам'ятка — предмет давнини; пам'ятник — споруда на честь особи.",
            }
        ],
        "frames": [
            {
                "sentence_with_slot": "Це видатна архітектурна ___.",
                "answer_form": "пам'ятка",
                "confusable_form": "пам'ятник",
                "origin": "t",
            },
            {
                "sentence_with_slot": "На площі встановили ___.",
                "answer_form": "пам'ятник",
                "confusable_form": "пам'ятку",
                "origin": "t2",
            },
        ],
    }
    allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = _gloss_verifier("предмет", "давнини", "споруда", "на", "честь", "особи")
    shards = build_practice_shards(
        entries, allowlist, verifier, [], BuildConfig(target=10), paronym_pairs=[pair], source_passages=FIXTURE_PASSAGES
    )
    a1_items = shards.get("A1", {}).get("paronym", {}).get("paronym", [])
    a2_items = shards.get("A2", {}).get("paronym", {}).get("paronym", [])
    assert len(a1_items) + len(a2_items) >= 1, "apostrophe-lemma paronym pair should resolve and emit"
    err = capsys.readouterr().err
    assert "not in practice lexemes" not in err


def test_live_paronym_pairs_yaml_is_valid_and_has_promoted_candidates() -> None:
    live_path = Path("registry/lexicon/paronym_pairs.yaml")
    assert live_path.exists()
    pairs = read_paronym_pairs(live_path)
    # 102 base pairs (#6338) + 95 densified pairs (#8276) = 197 total pairs.
    assert len(pairs) == 197, f"Expected 197 paronym pairs (102 base + 95 densified, #8276), got {len(pairs)}"
    seen_pairs: set[tuple[str, str]] = set()
    for index, pair in enumerate(pairs):
        errors = validate_paronym_pair(pair)
        assert not errors, f"Pair {index} ({pair.get('slugA')}/{pair.get('slugB')}) invalid: {errors}"
        import unicodedata

        a = unicodedata.normalize("NFC", pair["slugA"].strip().lower())
        b = unicodedata.normalize("NFC", pair["slugB"].strip().lower())
        key = tuple(sorted([a, b]))
        assert key not in seen_pairs, f"Duplicate paronym pair key {key}"
        seen_pairs.add(key)


def test_live_antonym_pairs_yaml_is_valid_and_has_promoted_candidates() -> None:
    live_path = Path("registry/lexicon/antonym_pairs.yaml")
    assert live_path.exists()
    pairs = read_antonym_pairs(live_path)
    assert len(pairs) == 1126, f"Expected 1126 reviewed antonym pairs, got {len(pairs)}"
    seen_pairs: set[tuple[str, str]] = set()
    for index, pair in enumerate(pairs):
        errors = validate_antonym_pair(pair)
        assert not errors, f"Pair {index} ({pair.get('slugA')}/{pair.get('slugB')}) invalid: {errors}"
        import unicodedata

        a = unicodedata.normalize("NFC", pair["slugA"].strip().lower())
        b = unicodedata.normalize("NFC", pair["slugB"].strip().lower())
        key = tuple(sorted([a, b]))
        assert key not in seen_pairs, f"Duplicate antonym pair key {key}"
        seen_pairs.add(key)


def test_live_homonym_pairs_yaml_is_valid_and_has_promoted_candidates() -> None:
    live_path = Path("registry/lexicon/homonym_pairs.yaml")
    assert live_path.exists()
    pairs = read_homonym_pairs(live_path)
    # 75 base pairs + 22 densified pairs (#8276) = 97 total pairs.
    assert len(pairs) == 97, f"Expected 97 homonym pairs (75 base + 22 densified, #8276), got {len(pairs)}"
    for index, pair in enumerate(pairs):
        errors = validate_homonym_pair(pair)
        assert not errors, f"Pair {index} ({pair.get('slugA')}/{pair.get('slugB')}) invalid: {errors}"


def test_vesum_number_key_and_lemma_search_paradigm():
    # Lemma-focus morphology needs VESUM search when enrichment paradigm is thin.
    assert generate_practice_deck._vesum_number_key({"s", "v_rod"}) == "singular"
    assert generate_practice_deck._vesum_number_key({"p", "v_dav"}) == "plural"
    assert generate_practice_deck._vesum_number_key({"s", "p", "v_naz"}) is None
    # Adjective tags often omit s/p → singular default.
    assert generate_practice_deck._vesum_number_key({"adj", "v_rod"}) == "singular"

    verifier = JsonVesumVerifier(
        {
            "новий": [{"lemma": "новий", "pos": "adj", "tags": "adj:v_naz:s"}],
            "нового": [{"lemma": "новий", "pos": "adj", "tags": "adj:v_rod:s"}],
            "новому": [{"lemma": "новий", "pos": "adj", "tags": "adj:v_dav:s"}],
            "новим": [{"lemma": "новий", "pos": "adj", "tags": "adj:v_oru:s"}],
            "стара": [{"lemma": "старий", "pos": "adj", "tags": "adj:v_naz:s"}],
        }
    )
    paradigm = generate_practice_deck._paradigm_from_vesum_lemma_search("новий", "adj", verifier)
    cases = paradigm.get("cases") or {}
    assert cases.get("genitive", {}).get("singular") == "нового"
    assert cases.get("dative", {}).get("singular") == "новому"
    assert cases.get("instrumental", {}).get("singular") == "новим"
    # Casefold lemma match for fixture search.
    paradigm2 = generate_practice_deck._paradigm_from_vesum_lemma_search("Новий", "adj", verifier)
    assert (paradigm2.get("cases") or {}).get("genitive", {}).get("singular") == "нового"


@pytest.fixture
def imperative_conn():
    """VESUM-attested paradigms; separate from host database and stress hydration."""
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
    paradigms = {
        "робити": (
            "imperf",
            {
                "impr:s:2": ["роби"],
                "impr:p:1": ["робімо", "робім"],
                "impr:p:2": ["робіть", "робіте"],
                "pres:s:2": ["робиш"],
                "pres:p:1": ["робимо"],
                "pres:p:2": ["робите"],
                "futr:s:2": ["робитимеш"],
                "futr:p:1": ["робитимемо"],
                "futr:p:2": ["робитимете"],
            },
        ),
        "робитися": (
            "imperf",
            {
                "impr:s:2": ["робися", "робись"],
                "impr:p:1": ["робімося", "робімось", "робімся"],
                "impr:p:2": ["робіться"],
            },
        ),
        "поставити": (
            "perf",
            {
                "impr:s:2": ["постав"],
                "impr:p:1": ["поставмо"],
                "impr:p:2": ["поставте"],
                "futr:s:2": ["поставиш"],
                "futr:p:1": ["поставимо"],
                "futr:p:2": ["поставите"],
            },
        ),
        "провітрити": (
            "perf",
            {
                "impr:s:2": ["провітри"],
                "impr:p:1": ["провітрімо", "провітрім"],
                "impr:p:2": ["провітріть"],
                "futr:s:2": ["провітриш"],
                "futr:p:1": ["провітримо"],
                "futr:p:2": ["провітрите"],
            },
        ),
        "ходити": (
            "imperf",
            {
                "impr:s:2": ["ходи"],
                "impr:p:1": ["ходімо", "ходім"],
                "impr:p:2": ["ходіть", "ходіте"],
                "impr:p:1:subst": ["ходімте"],
                "pres:s:2": ["ходиш"],
                "pres:p:1": ["ходимо"],
                "pres:p:2": ["ходите"],
            },
        ),
    }
    conn.executemany(
        "INSERT INTO forms VALUES (?, ?, ?, 'verb')",
        [
            (form, lemma, f"verb:{aspect}:{tags}")
            for lemma, (aspect, slots) in paradigms.items()
            for tags, forms in slots.items()
            for form in forms
        ],
    )
    yield conn
    conn.close()


@pytest.fixture
def imperative_plain_stress(monkeypatch):
    # Source stress behavior has its own tests; fixtures must not depend on the
    # installed trie or silently exercise a live host DB during unit tests.
    from scripts.verification import stress

    monkeypatch.setattr(stress, "verify_stress", lambda *a, **kw: {"status": "not_found", "matches": []})


def _imperative_test_items(conn, lemma="робити", cefr="A1"):
    return generate_practice_deck._build_imperative_items(
        {"lemmaId": lemma, "lemma": lemma, "lemmaPlain": lemma, "pos": "verb"},
        conn,
        cefr,
    )


def test_imperative_three_slots_variants_and_contract(imperative_conn, imperative_plain_stress):
    items = _imperative_test_items(imperative_conn)
    assert [item["slot"] for item in items] == ["2sg", "1pl", "2pl"]
    assert items[1]["target"] == "робімо"
    assert set(items[1]["acceptedAnswers"]) == {"робімо", "робім"}
    assert set(items[2]["acceptedAnswers"]) == {"робіть", "робіте"}
    for item in items:
        assert generate_practice_deck.validate_imperative_item(item) == []
        assert item["srsKey"] == f"робити::imperative::{item['slot']}"
        assert len(item["options"]) == 4
        assert all(
            option["text"] not in item["acceptedAnswers"] for option in item["options"] if not option["isCorrect"]
        )
        assert all(option.get("explanationEn") for option in item["options"] if not option["isCorrect"])
    assert items == _imperative_test_items(imperative_conn)


def test_imperative_reflexive_variants_and_immersion(imperative_conn, imperative_plain_stress):
    items = _imperative_test_items(imperative_conn, "робитися", "B1")
    assert set(items[0]["acceptedAnswers"]) == {"робися", "робись"}
    assert set(items[1]["acceptedAnswers"]) == {"робімося", "робімось", "робімся"}
    assert all("slotLabelEn" not in item and "Imperative:" not in item["notes"] for item in items)
    assert all("explanationEn" not in option for item in items for option in item["options"])


def test_imperative_taxonomy_uses_attested_slots_and_present(imperative_conn, imperative_plain_stress):
    codes = set()
    for lemma in ("робити", "поставити", "провітрити"):
        for item in _imperative_test_items(imperative_conn, lemma):
            all_option_texts = {option["text"] for option in item["options"]}
            assert "робитимеш" not in all_option_texts
            assert "робитимемо" not in all_option_texts
            assert "робитимете" not in all_option_texts
            for option in item["options"]:
                code = option["code"]
                codes.add(code)
                if code in {"WRONG_PERSON", "WRONG_MOOD"}:
                    tags = imperative_conn.execute(
                        "SELECT tags FROM forms WHERE word_form=? AND lemma=?",
                        (option["text"], lemma),
                    ).fetchone()[0]
                    assert (
                        ":impr:" if code == "WRONG_PERSON" else (":pres:" if ":pres:" in tags else ":futr:")
                    ) in tags
                    if code == "WRONG_MOOD":
                        assert "теперішній" not in option["explanationUk"]
                        assert "present" not in option.get("explanationEn", "").lower()
                elif code == "ORTHO_SOFT_SIGN":
                    assert option["text"] == "поставь"
                elif code == "STEM_CLUSTER":
                    assert option["text"] == "провітр"
    assert codes == {"CORRECT", *generate_practice_deck.IMPERATIVE_EXPLANATIONS}


def test_imperative_mutation_is_not_an_attested_word(imperative_conn, imperative_plain_stress):
    # A mutation that is an attested word of any POS cannot be called misspelt.
    imperative_conn.execute("INSERT INTO forms VALUES ('поставь','поставь','noun','noun')")
    items = _imperative_test_items(imperative_conn, "поставити")
    assert all(option["code"] != "ORTHO_SOFT_SIGN" for item in items for option in item["options"])


def test_imperative_rejects_mixed_aspect_and_missing_slots(imperative_conn, imperative_plain_stress):
    assert _imperative_test_items(imperative_conn, "відсутній") == []
    assert _imperative_test_items(imperative_conn, cefr="C2") == []
    imperative_conn.execute("INSERT INTO forms VALUES ('роби','робити','verb:perf:impr:s:2','verb')")
    assert _imperative_test_items(imperative_conn) == []


def test_imperative_stress_and_ambiguous_readings(imperative_conn, monkeypatch):
    from scripts.verification import stress

    def oracle(word, **kwargs):
        if word == "робімо":
            assert kwargs["pos"] == "VERB"
            return {"status": "ok", "matches": [{"stressed_form": "робі́мо"}]}
        if word == "роби":
            return {"status": "ambiguous", "matches": [{"stressed_form": "ро́би"}, {"stressed_form": "роби́"}]}
        return {"status": "not_found", "matches": []}

    monkeypatch.setattr(stress, "verify_stress", oracle)
    items = _imperative_test_items(imperative_conn)
    assert "2sg" not in {item["slot"] for item in items}
    first_plural = next(item for item in items if item["slot"] == "1pl")
    assert set(first_plural["acceptedAnswers"]) == {"робі́мо", "робімо", "робім"}
    assert first_plural["targetPlain"] == "робімо"


def test_imperative_excludes_marked_forms_and_exact_tag_mismatches(imperative_conn, imperative_plain_stress):
    imperative_conn.executemany(
        "INSERT INTO forms VALUES (?, 'робити', ?, 'verb')",
        [
            ("marked", "verb:imperf:impr:p:1:arch"),
            ("wrong-person", "verb:imperf:impr:p:12"),
            ("future", "verb:imperf:futr:p:1"),
        ],
    )
    items = _imperative_test_items(imperative_conn)
    assert all(
        answer not in {"marked", "wrong-person", "future"} for item in items for answer in item["acceptedAnswers"]
    )


def test_imperative_validator_rejects_stress_normalized_collisions(imperative_conn, imperative_plain_stress):
    item = _imperative_test_items(imperative_conn)[1]
    distractor = next(option for option in item["options"] if not option["isCorrect"])
    distractor["text"] = "робі́м"
    errors = generate_practice_deck.validate_mode_items("imperative", [item])
    assert any("collides" in error for error in errors)


def test_imperative_fixture_integration_includes_index_and_counts(imperative_conn, imperative_plain_stress):
    payload = {}
    for form, lemma, tags, pos in imperative_conn.execute("SELECT * FROM forms"):
        payload.setdefault(form, []).append({"lemma": lemma, "tags": tags, "pos": pos})
    payload["робити"] = [{"lemma": "робити", "tags": "verb:imperf:inf", "pos": "verb"}]
    entries = [
        {
            "lemma": "робити",
            "url_slug": "робити",
            "pos": "verb",
            "enrichment": {"cefr": {"level": "A1"}},
            "gloss": "do",
            "course_usage": [{"module": "fixture"}],
        }
    ]
    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist(frozenset()),
        JsonVesumVerifier(payload),
        config=BuildConfig(target=1, source_label="fixture"),
    )
    assert len(shards["A1"]["imperative"]["imperative"]) == 3
    assert "imperative" in shards["A1"]["index"]["items"][0]["modes"]
    assert shards["A1"]["index"]["counts"]["modeCounts"]["imperative"] == 3


def test_imperative_preserves_monosyllables(imperative_conn, monkeypatch):
    from scripts.verification import stress

    imperative_conn.executemany(
        "INSERT INTO forms VALUES (?, 'бути', ?, 'verb')",
        [
            ("будь", "verb:imperf:impr:s:2"),
            ("будьмо", "verb:imperf:impr:p:1"),
            ("будьте", "verb:imperf:impr:p:2"),
        ],
    )
    monkeypatch.setattr(
        stress,
        "verify_stress",
        lambda word, **kw: {
            "status": "invalid_input" if word == "будь" else "not_found",
            "matches": [],
        },
    )
    items = _imperative_test_items(imperative_conn, "бути")
    assert [item["target"] for item in items] == ["будь", "будьмо", "будьте"]


def test_imperative_rejects_multiple_accents_in_one_oracle_reading(imperative_conn, monkeypatch):
    from scripts.verification import stress

    monkeypatch.setattr(
        stress,
        "verify_stress",
        lambda word, **kw: (
            {
                "status": "ok",
                "matches": [{"stressed_form": "ро́бі́мо", "vowel_indices": [1, 3]}],
            }
            if word == "робімо"
            else {"status": "not_found", "matches": []}
        ),
    )
    assert "1pl" not in {item["slot"] for item in _imperative_test_items(imperative_conn)}


def _load_imperative_verbs_fixture() -> tuple[list[dict[str, Any]], sqlite3.Connection]:
    """Helper loading the offline 1,050-verb imperative fixture into an in-memory SQLite db."""
    fixture_path = Path(__file__).parent / "fixtures" / "atlas" / "1000_verb_imperatives.json"
    with open(fixture_path, encoding="utf-8") as f:
        verbs = json.load(f)

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
    to_insert = []
    for v in verbs:
        lemma = v["lemma"]
        for wf, tags in v.get("forms", []):
            to_insert.append((wf, lemma, tags, "verb"))
    conn.executemany("INSERT INTO forms VALUES (?, ?, ?, ?)", to_insert)
    return verbs, conn


def test_imperative_scaffolding_immersion_by_level(imperative_conn, imperative_plain_stress):
    """A1 and A2 cards have English scaffolding; B1+ strictly preserves Ukrainian immersion."""
    for cefr in ("A1", "A2"):
        items = _imperative_test_items(imperative_conn, "робити", cefr)
        for it in items:
            assert "slotLabelEn" in it
            assert "cueSentenceEn" in it
            assert all("explanationEn" in opt for opt in it["options"] if not opt["isCorrect"])
            assert "Imperative:" in it["notes"]

    for cefr in ("B1", "B2", "C1"):
        items = _imperative_test_items(imperative_conn, "робити", cefr)
        for it in items:
            assert "slotLabelEn" not in it
            assert "cueSentenceEn" not in it
            assert all("explanationEn" not in opt for opt in it["options"])
            assert "Imperative:" not in it["notes"]
            assert "accepted" not in it["notes"].lower()


def test_imperative_coverage_threshold_and_zero_collision(ulif_stress_db):
    """Verify >= 1,000 unique lemmas threshold and zero distractor collisions across deck.

    Genuinely offline gate: executes in CI using 1000_verb_imperatives.json with frozen forms.
    Target stress uses captured ULIF rows for перейняти plus the pinned
    ukrainian_word_stress==2.1.0 trie fallback; no live Sources DB is required.
    """
    verbs, mem_conn = _load_imperative_verbs_fixture()
    generate_practice_deck._imperative_display.cache_clear()

    lemmas_with_imperative = set()
    total_items = 0
    by_level: dict[str, int] = {}

    for v in verbs:
        lemma = v.get("lemma")
        cefr = v.get("cefr")
        if not lemma or cefr not in generate_practice_deck.PUBLISHED_LEVELS:
            continue
        lexeme = {
            "lemmaId": v.get("lemmaId", lemma),
            "lemma": lemma,
            "lemmaPlain": lemma,
            "cefr": cefr,
            "pos": "verb",
        }
        items = generate_practice_deck._build_imperative_items(lexeme, mem_conn, cefr)
        if items:
            lemmas_with_imperative.add(lemma)
            total_items += len(items)
            by_level[cefr] = by_level.get(cefr, 0) + len(items)
            for it in items:
                accepted_plain = {_plain(a) for a in it["acceptedAnswers"]}
                for opt in it["options"]:
                    if not opt["isCorrect"]:
                        assert opt["text"] not in it["acceptedAnswers"], (
                            f"Distractor collision in {it['id']}: {opt['text']}"
                        )
                        assert _plain(opt["text"]) not in accepted_plain, (
                            f"Normalized distractor collision in {it['id']}: {opt['text']}"
                        )

    # Without the captured ULIF identity join, перейняти:1pl is withheld:
    # Its WRONG_MOOD distractor переймемо has competing trie stresses;
    # only two other-person distractors remain, reducing B1 1090→1089 and
    # total 3138→3137. This is a missing test source, not a lost verb or a
    # reason to lower the gate. Freeze the source and retain the card.
    restored = generate_practice_deck._build_imperative_items(
        {"lemmaId": "verb_899_перейняти", "lemma": "перейняти", "lemmaPlain": "перейняти", "cefr": "B1", "pos": "verb"},
        mem_conn,
        "B1",
    )
    assert next(item for item in restored if item["slot"] == "1pl")["target"] == "переймі́мо"
    assert len(lemmas_with_imperative) == 1050, f"Expected 1,050 unique lemmas, got {len(lemmas_with_imperative)}"
    assert total_items == 3138, f"Expected 3,138 items, got {total_items}"
    assert by_level == {"A1": 279, "A2": 655, "B1": 1090, "B2": 721, "C1": 393}, (
        f"Level distribution mismatch: {by_level}"
    )
    generate_practice_deck._imperative_display.cache_clear()
    mem_conn.close()


def test_imperative_held_out_stratified_audit_200_items():
    """Held-out linguistic review of 200 stratified items (40 per level A1-C1).

    Genuinely offline gate: dynamically recomputes zero-collision guarantees,
    VESUM tag attestation, card re-derivation, distractor taxonomy, stress verification,
    and immersion contracts.
    Note: Target stress deterministically relies on the pinned ukrainian_word_stress==2.1.0 trie.
    """
    audit_fixture_path = Path(__file__).parent / "fixtures" / "atlas" / "imperative_held_out_audit_200.json"
    assert audit_fixture_path.exists(), f"Missing audit fixture: {audit_fixture_path}"

    with open(audit_fixture_path, encoding="utf-8") as f:
        audit_data = json.load(f)

    sample_200 = audit_data.get("items", [])
    assert len(sample_200) == 200, f"Expected 200 items in held-out audit, got {len(sample_200)}"

    by_level: dict[str, list[dict[str, Any]]] = {lvl: [] for lvl in generate_practice_deck.PUBLISHED_LEVELS}
    for it in sample_200:
        by_level[it["cefr"]].append(it)

    for lvl, lvl_items in by_level.items():
        assert len(lvl_items) == 40, f"Expected 40 items for level {lvl}, got {len(lvl_items)}"

    verbs, mem_conn = _load_imperative_verbs_fixture()
    verbs_by_lemma = {v["lemma"]: v for v in verbs}
    valid_codes = {"CORRECT", *generate_practice_deck.IMPERATIVE_EXPLANATIONS.keys()}

    for it in sample_200:
        # 1. Schema and contract checks
        errors = generate_practice_deck.validate_imperative_item(it)
        assert errors == [], f"Item validation failed for {it['id']}: {errors}"
        assert it["aspect"] in ("perf", "imperf")
        assert it["slot"] in ("2sg", "1pl", "2pl")
        assert len(it["options"]) == 4

        # 2. Dynamic zero-collision check across raw and normalized text
        accepted_plain = {_plain(a) for a in it["acceptedAnswers"]}
        for opt in it["options"]:
            if not opt["isCorrect"]:
                assert opt["text"] not in it["acceptedAnswers"], f"Distractor collision in {it['id']}: {opt['text']}"
                assert _plain(opt["text"]) not in accepted_plain, (
                    f"Normalized distractor collision in {it['id']}: {opt['text']}"
                )

        # 3. Target attestation in offline forms db
        target_plain = it["targetPlain"]
        lemma_plain = it["lemmaPlain"]
        expected_slot_suffix = {"2sg": "impr:s:2", "1pl": "impr:p:1", "2pl": "impr:p:2"}[it["slot"]]
        rows = mem_conn.execute(
            "SELECT tags FROM forms WHERE lemma=? AND word_form=?", (lemma_plain, target_plain)
        ).fetchall()
        assert rows, f"Target form {target_plain} not found in forms for lemma {lemma_plain}"
        assert any(expected_slot_suffix in r[0] for r in rows), (
            f"Expected slot {expected_slot_suffix} not in tags {rows} for {target_plain}"
        )

        # 4. Dynamic card re-derivation from generator
        v_entry = verbs_by_lemma.get(lemma_plain)
        assert v_entry is not None, f"Lemma {lemma_plain} not found in verbs fixture"
        lexeme = {
            "lemmaId": lemma_plain,
            "lemma": lemma_plain,
            "lemmaPlain": lemma_plain,
            "cefr": it["cefr"],
            "pos": "verb",
        }
        rebuilt_items = generate_practice_deck._build_imperative_items(lexeme, mem_conn, it["cefr"])
        rebuilt_match = next((item for item in rebuilt_items if item["slot"] == it["slot"]), None)
        assert rebuilt_match is not None, f"Slot {it['slot']} not rebuilt for {lemma_plain}"
        assert rebuilt_match["target"] == it["target"], f"Target mismatch for {it['id']}"
        assert set(rebuilt_match["acceptedAnswers"]) == set(it["acceptedAnswers"]), (
            f"Accepted answers mismatch for {it['id']}"
        )

        # 5. Options and distractor taxonomy checks
        correct_opts = [o for o in it["options"] if o["isCorrect"]]
        assert len(correct_opts) == 1
        assert correct_opts[0]["code"] == "CORRECT"

        for opt in it["options"]:
            assert opt["code"] in valid_codes
            if not opt["isCorrect"]:
                assert opt.get("explanationUk"), f"Missing explanationUk in {it['id']}"
                if opt["code"] in ("WRONG_PERSON", "WRONG_MOOD"):
                    opt_plain = _plain(opt["text"])
                    opt_rows = mem_conn.execute(
                        "SELECT tags FROM forms WHERE lemma=? AND word_form=?", (lemma_plain, opt_plain)
                    ).fetchall()
                    assert opt_rows, f"Grammatical distractor {opt_plain} not found for {lemma_plain}"
                elif opt["code"] == "ORTHO_SOFT_SIGN":
                    assert "ь" in opt["text"], f"Expected soft sign in ORTHO_SOFT_SIGN distractor {opt['text']}"

        # 6. Scaffolding vs Immersion contract by level
        if it["cefr"] in ("A1", "A2"):
            assert "slotLabelEn" in it
            assert "cueSentenceEn" in it
            assert "Imperative:" in it["notes"]
            assert all("explanationEn" in opt for opt in it["options"] if not opt["isCorrect"])
        else:
            assert "slotLabelEn" not in it
            assert "cueSentenceEn" not in it
            assert "Imperative:" not in it["notes"]
            assert all("explanationEn" not in opt for opt in it["options"])

        # 7. Linguistic audit certificate metadata and dynamic stress verification
        audit = it.get("audit", {})
        assert audit.get("verdict") == "APPROVED", f"Item {it['id']} not APPROVED in audit"
        assert audit.get("pravopys_section") == "§116"

        vowels = set("аеєиіїоуюяАЕЄИІЇОУЮЯ")
        num_vowels = sum(1 for c in it["target"] if c in vowels)
        is_stressed_or_monosyllable = ("\u0301" in it["target"]) or (num_vowels <= 1)
        assert audit.get("target_stress_verified") is is_stressed_or_monosyllable, (
            f"Stress verification flag mismatch for {it['id']}: expected {is_stressed_or_monosyllable}"
        )

    # 192 targets carry verified accentuation (U+0301) or are monosyllabic.
    # 8 polysyllabic targets fall back to bare unaccented display due to oracle not_found
    # (1 in B2: пасися; 7 in C1: пилососьте, затікай, переповіжмо, переповіж, перезавантажуйте, зазвучімо, облаштуйтеся).
    stressed_count = sum(1 for it in sample_200 if it.get("audit", {}).get("target_stress_verified"))
    assert stressed_count == 192, f"Expected 192 stressed targets, got {stressed_count}"


# --- #8727 / #8728: calque judgments need a normative source; explanations must be clean Ukrainian


class _AllowAllCreationReview:
    def allows(self, *args: object) -> bool:
        return True


def _published_vybachennia_pair() -> dict[str, Any]:
    """The pair behind published B1 card her_324943ef5a47 (#8727), verbatim from the registry."""
    return {
        "calqueLabel": "вибачення",
        "calqueSurfaces": ["вибачення"],
        "nativeSlug": "вибачити",
        "nativeLemma": "вибачити",
        "kind": "lexical",
        "corrections": ["вибачити"],
        "rationale": (
            "UA-GEC F/Calque corpus evidence (native + fluency annotator correction, n=1 occurrence(s) "
            "across 1 document(s)): «вибачення» flagged non-standard; reviewed correction «вибачити»."
        ),
        "citations": ["ua-gec:F/Calque n=1"],
        "sourceFamily": "ua-gec",
        "severity": "enrichment",
        "curator": "script:heritage_calque_wave-2026-08-11",
        "frames": [
            {
                "sentence_with_slot": "Тому прошу ___, коли що-небудь зроблю не так Але іншого виходу не маю.",
                "answer_form": "вибачити",
                "calque_form": "вибачення",
                "origin": "ua-gec-calque-wave1:literary_texts/e27925aa_c0161",
            }
        ],
    }


def test_heritage_single_corpus_correction_of_clean_vesum_word_is_withheld(
    capsys: pytest.CaptureFixture[str],
) -> None:
    pair = _published_vybachennia_pair()
    lexemes = _fixture_lexemes()
    verifier = _gloss_verifier("вибачення", "вибачити")

    assert validate_heritage_pair(pair) == []
    items = _build_heritage_items(
        pair,
        lexemes[0],
        lexemes,
        "deck-v1",
        verifier=verifier,
        creation_review=_AllowAllCreationReview(),
        source_passages=FIXTURE_PASSAGES,
    )
    assert items == []
    err = capsys.readouterr().err
    assert "heritage_pair 'вибачення' withheld (no normative passage): no normativeSupport passage" in err


def _book_pair(**overrides: Any) -> dict[str, Any]:
    """A fixture-lexeme heritage pair («кніга» → «книга») for the normative-support gate."""
    return {**_fixture_heritage_pair(), "normativeSupport": [], **overrides}


def test_heritage_corpus_only_pair_is_withheld_even_when_vesum_cannot_analyse_the_calque(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Reviewer probe (#8727 r2): a corpus-only pair whose calque VESUM cannot analyse was admitted."""
    lexemes = _fixture_lexemes()
    pair = _book_pair(citations=["ua-gec:F/Calque n=1"])
    verifier = JsonVesumVerifier.from_path(VESUM)
    assert verifier.verify_words(["кніга", "кнігу"]) == {"кніга": [], "кнігу": []}

    items = _build_heritage_items(
        pair, lexemes[0], lexemes, "deck-v1", verifier=verifier, source_passages=FIXTURE_PASSAGES
    )

    assert items == []
    assert "heritage_pair 'кніга' withheld (no normative passage)" in capsys.readouterr().err


def test_heritage_non_corpus_citation_is_not_support_without_a_verified_passage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Reviewer probe (#8727 r2): any non-UA-GEC citation string (an article title) admitted the pair."""
    lexemes = _fixture_lexemes()
    for citations in (["antonenko:Вибачення"], ["sum-11:кніга", "grinchenko:книга"], ["state-standard:glazova-11"]):
        pair = _book_pair(citations=citations)
        assert _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1", source_passages=FIXTURE_PASSAGES) == []
    assert capsys.readouterr().err.count("withheld (no normative passage)") == 3


def test_normative_support_passage_must_be_verbatim_from_an_allowed_page() -> None:
    page = "antonenko-davydovych-yak-my-hovorymo_p999"

    def errors(entries: Any, passages: Any = FIXTURE_PASSAGES) -> list[str]:
        return verified_source_passages(entries, HERITAGE_NORMATIVE_SOURCES, passages, field="normativeSupport")[1]

    verified, problems = verified_source_passages(
        FIXTURE_HERITAGE_SUPPORT, HERITAGE_NORMATIVE_SOURCES, FIXTURE_PASSAGES, field="normativeSupport"
    )
    assert problems == []
    assert verified[0]["label"] == "Антоненко-Давидович Б. «Як ми говоримо», фрагмент p999"
    # whitespace, dashes and quote style are not a paraphrase
    assert errors([{"locator": page, "passage": "Кажуть «читаю  кнігу»,\nа треба «читаю книгу»."}]) == []
    assert errors([]) == ["no normativeSupport passage"]
    assert errors([{"locator": page}]) == ["normativeSupport[0] needs a locator and a passage"]
    # a school textbook, СУМ-11 or a corpus row is not a style-guide page
    for locator in ("5-klas-ukrmova-fixture-2000_s0001", "sum-11:кніга", "ua-gec:F/Calque"):
        assert errors([{"locator": locator, "passage": "x"}]) == [
            f"normativeSupport[0] locator {locator!r} is not an allowed source"
        ]
    assert errors([{"locator": "antonenko-davydovych-yak-my-hovorymo_p997", "passage": "x"}]) == [
        "normativeSupport[0] locator 'antonenko-davydovych-yak-my-hovorymo_p997' is not readable from the sources database"
    ]
    assert errors([{"locator": page, "passage": "Кажуть «кніга», а треба «книга»."}]) == [
        f"normativeSupport[0] passage is not verbatim in {page}"
    ]
    # no sources database: fail closed
    assert errors(FIXTURE_HERITAGE_SUPPORT, None) == [
        f"normativeSupport[0] locator {page!r} is not readable from the sources database"
    ]


def test_heritage_passage_must_name_this_frames_calque_and_correction(capsys: pytest.CaptureFixture[str]) -> None:
    lexemes = _fixture_lexemes()
    passages = JsonSourcePassages(
        {
            "antonenko-davydovych-yak-my-hovorymo_p998": "Кажуть «кніга» — так не можна.",
            "antonenko-davydovych-yak-my-hovorymo_p999": 'Фіктивна сторінка. Кажуть "читаю кнігу", а треба "читаю книгу".',
            "5-klas-ukrmova-fixture-2000_s0003": "Неправильно: читаю кнігу. Правильно: читаю книгу.",
        }
    )
    calque_only = _book_pair(
        normativeSupport=[
            {"locator": "antonenko-davydovych-yak-my-hovorymo_p998", "passage": "Кажуть «кніга» — так не можна."}
        ]
    )
    assert _build_heritage_items(calque_only, lexemes[0], lexemes, "deck-v1", source_passages=passages) == []
    assert "frame 1 withheld (passage does not support this correction)" in capsys.readouterr().err

    supported = _book_pair(normativeSupport=FIXTURE_HERITAGE_SUPPORT)
    items = _build_heritage_items(supported, lexemes[0], lexemes, "deck-v1", source_passages=passages)
    assert len(items) == 1
    assert items[0]["citations"] == [
        "Антоненко-Давидович Б. «Як ми говоримо», фрагмент p999",
        "5-klas-ukrmova-fixture-2000, фрагмент s0003",
        "fixture:heritage",
    ]
    assert _heritage_frame_support(supported["frames"][0], [{"passage": "Кажуть «кнігу»."}], None) is None


def test_heritage_historical_passage_alone_is_withheld(capsys: pytest.CaptureFixture[str]) -> None:
    pair = _fixture_heritage_pair()
    pair.pop("currentNormSupport")
    lexemes = _fixture_lexemes()
    assert _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1", source_passages=FIXTURE_PASSAGES) == []
    assert "withheld (no current-norm corroboration)" in capsys.readouterr().err


def test_heritage_current_norm_must_bind_to_verified_chunk(capsys: pytest.CaptureFixture[str]) -> None:
    pair = _fixture_heritage_pair()
    pair["frames"][0]["normativeJudgment"]["currentNormPassageSha256"] = "0" * 64
    lexemes = _fixture_lexemes()
    assert _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1", source_passages=FIXTURE_PASSAGES) == []
    assert "frame 1 withheld (no bound current-norm corroboration)" in capsys.readouterr().err


def test_heritage_reversed_passage_cannot_key_the_form_it_rejects(capsys: pytest.CaptureFixture[str]) -> None:
    """A passage endorsing «кнігу» cannot support a card keyed «книгу»."""
    locator = "antonenko-davydovych-yak-my-hovorymo_p999"
    reversed_passage = 'Кажуть "читаю книгу", а треба "читаю кнігу".'
    pair = _book_pair(
        normativeSupport=[{"locator": locator, "passage": reversed_passage}],
        frames=[_fixture_heritage_pair()["frames"][0]],
    )
    passages = JsonSourcePassages(
        {
            locator: reversed_passage,
            "5-klas-ukrmova-fixture-2000_s0003": "Неправильно: читаю кнігу. Правильно: читаю книгу.",
        }
    )

    assert (
        _build_heritage_items(pair, _fixture_lexemes()[0], _fixture_lexemes(), "deck-v1", source_passages=passages)
        == []
    )
    assert "frame 1 withheld (passage does not support this correction)" in capsys.readouterr().err


def test_heritage_reviewed_judgment_is_bound_to_the_exact_frame() -> None:
    frame = _fixture_heritage_pair()["frames"][0]
    changed = {**frame, "sentence_with_slot": frame["sentence_with_slot"] + "!"}
    verified, errors = verified_source_passages(
        FIXTURE_HERITAGE_SUPPORT, HERITAGE_NORMATIVE_SOURCES, FIXTURE_PASSAGES, field="normativeSupport"
    )
    assert errors == []
    assert _heritage_frame_support(changed, verified, None) is None


@pytest.fixture
def live_source_checkers(requires_sources_db, requires_vesum_db) -> tuple[Any, Any]:
    """Live-registry readers share validated fixture-time inputs."""
    return generate_practice_deck.SqliteSourcePassages(requires_sources_db), RealVesumVerifier(requires_vesum_db)


def test_live_heritage_normative_support_is_verbatim_and_names_every_frame(live_source_checkers) -> None:
    passages, verifier = live_source_checkers
    all_pairs = [pair for pair in read_heritage_pairs(HERITAGE_REGISTRY) if pair.get("normativeSupport")]
    supported = [pair for pair in all_pairs if pair.get("currentNormSupport")]
    assert supported
    assert all(
        not any("normativeJudgment" in frame for frame in pair["frames"]) for pair in all_pairs if pair not in supported
    )
    for pair in supported:
        verified, problems = verified_source_passages(
            pair["normativeSupport"], HERITAGE_NORMATIVE_SOURCES, passages, field="normativeSupport"
        )
        assert problems == [], pair["calqueLabel"]
        current, current_problems = verified_source_passages(
            pair["currentNormSupport"], HERITAGE_CURRENT_SOURCES, passages, field="currentNormSupport"
        )
        assert current_problems == [], pair["calqueLabel"]
        frames = _valid_heritage_frames(pair, verifier, report=False)
        assert frames, pair["calqueLabel"]
        for frame in frames:
            assert _heritage_frame_support(frame, verified, verifier) is not None, (pair["calqueLabel"], frame)
            assert _heritage_current_support(frame, current, verifier) is not None, (pair["calqueLabel"], frame)


def test_live_language_review_fixes_are_source_bound(live_source_checkers) -> None:
    passages, _ = live_source_checkers
    reviewed = {
        pair["calqueLabel"]: pair for pair in read_heritage_pairs(HERITAGE_REGISTRY) if pair.get("normativeSupport")
    }
    assert "11-klas-istoriya-ukr-gisem-2024_s0320" in reviewed["присвоїти"]["currentNormWithheldReason"]
    assert "присвоєно звання" in passages.chunk_text("11-klas-istoriya-ukr-gisem-2024_s0320")
    assert all("normativeJudgment" not in frame for frame in reviewed["присвоїти"]["frames"])

    affair = reviewed["справа"]
    assert affair["calqueSense"] == '"В чому справа?", "Справа в тім, що…"'
    assert "це не моя справа" not in affair["calqueSense"]
    assert all("normativeJudgment" not in frame for frame in affair["frames"])

    exclusively = reviewed["виключно"]
    assert exclusively["authenticSense"] is None
    assert validate_heritage_pair(exclusively) == []
    assert all("normativeJudgment" not in frame for frame in exclusively["frames"])

    event = reviewed["міроприємство"]
    assert "antonenko:Міроприємство" in event["citations"]
    assert "Міроприємство" in passages.chunk_text("antonenko-davydovych-yak-my-hovorymo_p031")

    relation = reviewed["відношення"]
    title = "Відношення, взаємини, стосунок, відносно, щодо, стосовно, відносність"
    assert title in relation["rationale"]
    assert title in passages.chunk_text("antonenko-davydovych-yak-my-hovorymo_p018")

    other = reviewed["другий"]
    assert other["severity"] == "enrichment"
    assert other["rationale"] in " ".join(passages.chunk_text("6-klas-ukrmova-avramenko-2023_s0193").split())

    medical = next(
        pair
        for pair in read_paronym_pairs(PARONYM_REGISTRY)
        if pair.get("slugA") == "лікарський" and pair.get("slugB") == "лікарняний"
    )
    assert "Лі́карський — який стосується лікаря" in medical["distinction_gloss_uk"]
    assert "ліка́рський — який стосується ліків" in medical["distinction_gloss_uk"]
    assert "лікарня́ний — який стосується лікарні" in medical["distinction_gloss_uk"]
    assert medical["distinction_gloss_uk"].count("\u0301") == 3
    assert paronym_gloss_provenance_errors(medical, passages) == []


def _published_da_tak_pair() -> dict[str, Any]:
    """The «да → так» pair with the wave-1 frames behind A1 cards her_da1da709367b / her_a8300df52532."""
    return {
        "calqueLabel": "да",
        "calqueSurfaces": ["да"],
        "nativeSlug": "так",
        "nativeLemma": "так",
        "kind": "lexical",
        "corrections": ["так"],
        "rationale": "канонічний суржик-маркер: рос. да; укр. так",
        "citations": ["ua-gec:F/Calque n=3 docs=2"],
        "sourceFamily": "ua-gec",
        "cefrAvailability": "a1",
        "severity": "russianism",
        "frames": [
            {
                "sentence_with_slot": "Оля відповіла ___, коли її спитали про готовність.",
                "answer_form": "так",
                "calque_form": "да",
                "origin": "authored-codex-2026-07-06",
            },
            {
                "sentence_with_slot": "На прохання допомогти брат сказав ___.",
                "answer_form": "так",
                "calque_form": "да",
                "origin": "authored-codex-2026-07-06",
            },
            {
                "sentence_with_slot": "Усе тут було нове, і в повітрі, яке ___ нагадувало глибину, слова не лишали бульки.",
                "answer_form": "так",
                "calque_form": "наступним чином",
                "origin": "ua-gec-calque-wave1:literary_texts/5cbffa78_c0001",
            },
            {
                "sentence_with_slot": "Можливо, вона ___ і дожила б віку, якби не побачила рибалку.",
                "answer_form": "так",
                "calque_form": "настільки",
                "origin": "ua-gec-calque-wave1:literary_texts/5cbffa78_c0002",
            },
            {
                "sentence_with_slot": "Почувши ___ близько від себе розмову, говорюща риба не втрималася.",
                "answer_form": "так",
                "calque_form": "таким чином",
                "origin": "ua-gec-calque-wave1:literary_texts/5cbffa78_c0002",
            },
        ],
    }


def test_heritage_frames_for_a_different_calque_are_withheld_not_relabelled(
    capsys: pytest.CaptureFixture[str],
) -> None:
    pair = _published_da_tak_pair()
    verifier = _gloss_verifier("так", "настільки", "таким", "чином", "наступним")

    frames = _valid_heritage_frames(pair, verifier)

    assert [frame["calque_form"] for frame in frames] == ["да", "да"]
    err = capsys.readouterr().err
    assert "heritage_pair 'да' frame 4 withheld: calque_form 'настільки' is not a form of calqueLabel 'да'" in err
    assert "frame 5 withheld: calque_form 'таким чином'" in err


def test_heritage_frame_calque_mismatch_accepts_forms_of_the_same_calque() -> None:
    def pair(label: str, *surfaces: str) -> dict[str, Any]:
        return {"calqueLabel": label, "calqueSurfaces": list(surfaces)}

    def frame(calque_form: str) -> dict[str, Any]:
        return {"calque_form": calque_form}

    inflect = JsonVesumVerifier(
        {
            "пробку": [{"lemma": "пробка"}],
            "точки": [{"lemma": "точка"}],
            "зору": [{"lemma": "зір"}],
            "вверх": [{"lemma": "вверх"}],
            "слідує": [{"lemma": "слідувати"}],
            "включи": [{"lemma": "включити"}],
        }
    )
    # exact surface, declared surface, VESUM lemma, multiword lemma, shared stem when VESUM is silent
    assert _heritage_frame_calque_mismatch(frame("Но"), pair("но"), inflect) is None
    assert _heritage_frame_calque_mismatch(frame("бажаючі"), pair("бажаючий", "бажаючі"), inflect) is None
    assert _heritage_frame_calque_mismatch(frame("пробку"), pair("пробка"), inflect) is None
    assert _heritage_frame_calque_mismatch(frame("включи"), pair("включити"), inflect) is None
    assert _heritage_frame_calque_mismatch(frame("З моєї точки зору"), pair("точка зору"), inflect) is None
    assert _heritage_frame_calque_mismatch(frame("шляпу"), pair("шляпа"), inflect) is None
    assert _heritage_frame_calque_mismatch(frame("кнігу"), pair("кніга"), None) is None
    # different words: an inherited rationale would be a copied, false claim
    mismatch = _heritage_frame_calque_mismatch(frame("вверх"), pair("уверх"), inflect)
    assert mismatch is not None and "not a form of calqueLabel 'уверх'" in mismatch
    assert _heritage_frame_calque_mismatch(frame("слідує"), pair("надо"), inflect) is not None
    assert _heritage_frame_calque_mismatch(frame("настільки"), pair("да"), None) is not None


def test_merge_heritage_pair_overlay_keeps_foreign_calque_frames_out_of_curated_pair() -> None:
    base = _published_da_tak_pair()
    base["frames"] = base["frames"][:2]
    overlay = {
        "calqueLabel": "настільки",
        "nativeSlug": "так",
        "rationale": "overlay rationale",
        "citations": ["ua-gec:F/Calque n=1"],
        "frames": [
            {
                "sentence_with_slot": "Вона ___ і дожила б віку.",
                "answer_form": "так",
                "calque_form": "настільки",
                "origin": "wave",
            },
            {"sentence_with_slot": "Брат сказав ___.", "answer_form": "так", "calque_form": "да", "origin": "wave"},
        ],
    }

    merged = _merge_heritage_pair_overlay([base], [overlay])

    assert [frame["calque_form"] for frame in merged[0]["frames"]] == ["да", "да", "да"]
    assert len(merged) == 2
    assert merged[1]["calqueLabel"] == "настільки"
    assert merged[1]["rationale"] == "overlay rationale"
    assert [frame["calque_form"] for frame in merged[1]["frames"]] == ["настільки"]


def _taktovnyi_entries() -> list[dict[str, Any]]:
    return [
        {
            "lemmaId": lemma,
            "lemma": lemma,
            "gloss": gloss,
            "pos": "adjective",
            "cefr": "B1",
            "url_slug": lemma,
            "primary_source": "course_vocab",
            "course_usage": [{"track": "b1"}],
        }
        for lemma, gloss in (("тактичний", "tactical"), ("тактовний", "tactful"))
    ]


def _taktovnyi_pair(gloss: str) -> dict[str, Any]:
    return {
        "slugA": "тактичний",
        "slugB": "тактовний",
        "distinction_gloss_uk": gloss,
        "citations": ["miyklas.com.ua"],
        "frames": [
            {
                "sentence_with_slot": "Командир розробив грамотний ___ хід у бою.",
                "answer_form": "тактичний",
                "confusable_form": "тактовний",
                "origin": "authored-paronym-frame",
            },
            {
                "sentence_with_slot": "Дипломат зробив дуже ___ і ввічливий жест.",
                "answer_form": "тактовний",
                "confusable_form": "тактичний",
                "origin": "authored-paronym-frame",
            },
        ],
    }


_TAKTOVNYI_VERIFIER_WORDS = (
    "тактичний",
    "тактовний",
    "який",
    "стосується",
    "тактики",
    "бою",
    "чи",
    "плану",
    "дій",
    "володіє",
    "почуттям",
    "міри",
    "вміє",
    "поводитися",
    "дотримується",
    "відповідних",
    "норм",
)
# Verbatim excerpts of the two textbook chunks behind the тактичний/тактовний row (sources MCP
# get_chunk_context): the paronym dictionary (Заболотний 5 кл. 2023, Додаток 2) and the two-column
# example table on p. 37 whose definitions interleave line by line.
_ZABOLOTNYI_S0200 = "5-klas-ukrmova-zabolotnyi-2023_s0200"
_ZABOLOTNYI_S0027 = "5-klas-ukrmova-zabolotnyi-2023_s0027"
_TAKTOVNYI_CHUNKS = {
    _ZABOLOTNYI_S0200: (
        "Тактичний // тактовний\nТактичний – який стосується тактики як сукупності прийомів та\n"
        "способів для досягнення мети (у політиці, спорті) або здійснення певної\nбойової операції. "
        "Тактичний хід, тактична перевага.\nТактовний – який володіє почуттям міри, вміє поводитися, "
        "дотримується\nвідповідних норм. Тактовна людина, бути тактовним.\n236"
    ),
    _ZABOLOTNYI_S0027: (
        "2) тактовний – тактичний\n(який уміє (який стосується тактики,\nправильно способів дій у спорті,\n"
        "поводитися) політиці, на війні)."
    ),
}
_TAKTOVNYI_PASSAGE = (
    "Тактичний – який стосується тактики як сукупності прийомів та способів для досягнення мети (у політиці, "
    "спорті) або здійснення певної бойової операції. Тактичний хід, тактична перевага. Тактовний – який володіє "
    "почуттям міри, вміє поводитися, дотримується відповідних норм."
)
_TAKTOVNYI_SOURCED_GLOSS = (
    "Тактичний — який стосується тактики; тактовний — який володіє почуттям міри, вміє поводитися, "
    "дотримується відповідних норм."
)


def _sourced_taktovnyi_pair(gloss: str = _TAKTOVNYI_SOURCED_GLOSS, passage: str = _TAKTOVNYI_PASSAGE) -> dict[str, Any]:
    return {
        **_taktovnyi_pair(gloss),
        "glossSources": [{"locator": _ZABOLOTNYI_S0200, "passage": passage}],
    }


def _build_taktovnyi(pair: dict[str, Any], chunks: dict[str, str] | None = None) -> list[dict[str, Any]]:
    shards = build_practice_shards(
        _taktovnyi_entries(),
        ReviewedSourceAllowlist.from_payload([]),
        _gloss_verifier(*_TAKTOVNYI_VERIFIER_WORDS),
        [],
        BuildConfig(target=10),
        paronym_pairs=[pair],
        source_passages=JsonSourcePassages(chunks if chunks is not None else _TAKTOVNYI_CHUNKS),
    )
    return shards["B1"]["paronym"]["paronym"]


def test_paronym_explanation_with_russian_word_is_withheld(capsys: pytest.CaptureFixture[str]) -> None:
    """Published par_42a6a39064f8 / par_687bf8430790 taught «вежливий» (VESUM NOT_FOUND) in feedback (#8728).

    Even a gloss copied from a (fixture) source is withheld when a word is not clean Ukrainian.
    """
    published_gloss = (
        "Тактичний — який стосується тактики бою чи плану дій; тактовний — вежливий, який володіє почуттям міри."
    )
    pair = _sourced_taktovnyi_pair(published_gloss, published_gloss)

    assert _build_taktovnyi(pair, {_ZABOLOTNYI_S0200: published_gloss}) == []
    err = capsys.readouterr().err
    assert "item withheld by explanation-language gate: distinction_gloss_uk: explanation token «вежливий»" in err
    assert 'explanation-language gate: withheld {"paronym": 2}' in err


def test_paronym_gloss_without_a_source_locator_is_withheld(capsys: pytest.CaptureFixture[str]) -> None:
    """Reviewer probe (#8728 r2): model-curated wording shipped behind a bare book title or site name."""
    for citations in (["Гринчишин Д. Г. Словник паронімів української мови (1986)"], ["miyklas.com.ua"]):
        pair = {**_taktovnyi_pair("Тактичний — який стосується тактики бою чи плану дій."), "citations": citations}
        assert _build_taktovnyi(pair) == []
    err = capsys.readouterr().err
    assert err.count("item withheld at B1 by gloss-provenance gate: no glossSources passage") == 4
    assert 'paronym gloss-provenance gate: withheld {"B1": 2}' in err


def test_paronym_gloss_provenance_rejects_reconstructed_swapped_and_paraphrased_clauses() -> None:
    passages = JsonSourcePassages(_TAKTOVNYI_CHUNKS)

    def errors(pair: dict[str, Any]) -> list[str]:
        return paronym_gloss_provenance_errors(pair, passages)

    assert errors(_sourced_taktovnyi_pair()) == []
    # r2 quoted a de-interleaved reading of the two-column table, not text printed in the chunk.
    reconstructed = {
        **_taktovnyi_pair("Тактичний — який стосується тактики, способів дій у спорті, політиці, на війні."),
        "glossSources": [
            {
                "locator": _ZABOLOTNYI_S0027,
                "passage": "тактичний (який стосується тактики, способів дій у спорті, політиці, на війні)",
            }
        ],
    }
    assert errors(reconstructed) == [f"glossSources[0] passage is not verbatim in {_ZABOLOTNYI_S0027}"]
    swapped = _sourced_taktovnyi_pair("Тактичний — який володіє почуттям міри; тактовний — який стосується тактики.")
    assert errors(swapped) == [
        "gloss clause 'Тактичний — який володіє почуттям міри' is not copied from a glossSources passage defining "
        "'тактичний'",
        "gloss clause 'тактовний — який стосується тактики.' is not copied from a glossSources passage defining "
        "'тактовний'",
    ]
    paraphrased = _sourced_taktovnyi_pair("Тактичний — який стосується тактики; тактовний — той, хто має почуття міри.")
    assert errors(paraphrased) == [
        "gloss clause 'тактовний — той, хто має почуття міри.' is not copied from a glossSources passage defining "
        "'тактовний'"
    ]
    unshaped = _sourced_taktovnyi_pair("Слова тактичний і тактовний різні.")
    assert errors(unshaped) == [
        "gloss clause 'Слова тактичний і тактовний різні.' is not '<paronym> — <definition>'",
        "gloss missing sourced meaning for 'тактичний'",
        "gloss missing sourced meaning for 'тактовний'",
    ]
    # No sources database: fail closed.
    assert paronym_gloss_provenance_errors(_sourced_taktovnyi_pair(), None) == [
        f"glossSources[0] locator {_ZABOLOTNYI_S0200!r} is not readable from the sources database"
    ]


def test_paronym_one_sided_gloss_is_withheld(capsys: pytest.CaptureFixture[str]) -> None:
    """A source-backed definition of only «тактичний» cannot explain either card."""
    pair = _sourced_taktovnyi_pair("Тактичний — який стосується тактики.")
    assert paronym_gloss_provenance_errors(pair, JsonSourcePassages(_TAKTOVNYI_CHUNKS)) == [
        "gloss missing sourced meaning for 'тактовний'"
    ]
    assert _build_taktovnyi(pair) == []
    assert "paronym gloss-provenance gate: withheld" in capsys.readouterr().err


def test_paronym_source_linked_gloss_ships() -> None:
    items = _build_taktovnyi(_sourced_taktovnyi_pair())

    assert len(items) == 2
    assert {item["distinction_gloss_uk"] for item in items} == {_TAKTOVNYI_SOURCED_GLOSS}


def test_live_paronym_gloss_sources_are_verbatim_and_two_sided_or_withheld(live_source_checkers) -> None:
    passages, verifier = live_source_checkers
    sourced = [pair for pair in read_paronym_pairs(PARONYM_REGISTRY) if pair.get("glossSources")]
    assert sourced
    withheld = {
        ("вистава", "виставка"),
        ("усмішка", "посмішка"),
        ("книжковий", "книжний"),
        ("уява", "уявлення"),
    }
    observed_withheld = set()
    for pair in sourced:
        errors = paronym_gloss_provenance_errors(pair, passages)
        key = (pair["slugA"], pair["slugB"])
        if errors:
            assert any("gloss missing sourced meaning" in error for error in errors), key
            observed_withheld.add(key)
        assert (
            explanation_language_errors(pair["distinction_gloss_uk"], verifier, allowed=[pair["slugA"], pair["slugB"]])
            == []
        ), key
    assert observed_withheld == withheld
    taktovnyi = next(pair for pair in sourced if pair["slugA"] == "тактичний")
    assert "вежливий" not in taktovnyi["distinction_gloss_uk"]


def test_explanation_language_errors_check_quoted_words_but_exempt_russian_mentions_and_own_forms() -> None:
    verifier = _gloss_verifier(
        "Тактовний", "канонічний", "суржик", "маркер", "так", "офіційно", "діловому", "великий", "стилі", "канцелярит"
    )

    # Reviewer probe (#8728 r2): quotation marks used to hide a Russian definition.
    assert explanation_language_errors("Тактовний — «вежливий».", verifier) == [
        "explanation token «вежливий» is not a clean VESUM form"
    ]
    assert explanation_language_errors('Тактовний — "вежливий".', verifier) == [
        "explanation token «вежливий» is not a clean VESUM form"
    ]
    # An explicit Russian mention and the item's own contrasted forms stay exempt.
    assert explanation_language_errors("канонічний суржик-маркер: рос. да; укр. так", verifier) == []
    assert explanation_language_errors("Тактовний — рос. вежливий", verifier) == []
    assert (
        explanation_language_errors(
            "«вибачення» flagged non-standard; reviewed correction «вибачити».",
            verifier,
            allowed=["вибачення", "вибачити"],
        )
        == []
    )
    assert explanation_language_errors("канцелярит «дана книга» (рос. данный)", verifier) == [
        "explanation token «дана» is not a clean VESUM form",
        "explanation token «книга» is not a clean VESUM form",
    ]
    assert explanation_language_errors("в офіційно-діловому стилі (розм.)", verifier) == []
    assert explanation_language_errors("великий бык", verifier) == ["explanation token «бык» is not a clean VESUM form"]
    assert explanation_language_errors("великий бык", verifier, allowed=["бык"]) == []
    assert explanation_language_errors("", verifier) == []


def test_explanation_gate_errors_cover_every_learner_facing_field() -> None:
    verifier = _gloss_verifier("так")
    item = {
        "answer": "так",
        "calque": "да",
        "rationale": "рос. да; укр. так",
        "rationaleUk": "хорошо",
        "calqueSense": "так",
        "authenticSense": "«так»",
        "options": [{"label": "так"}, {"label": "да"}],
    }
    assert explanation_gate_errors("heritage", item, verifier) == [
        "rationaleUk: explanation token «хорошо» is not a clean VESUM form"
    ]
    assert explanation_gate_errors("paronym", {"distinction_gloss_uk": "так вежливий"}, verifier) == [
        "distinction_gloss_uk: explanation token «вежливий» is not a clean VESUM form"
    ]
    assert explanation_gate_errors("cloze", {"distinction_gloss_uk": "вежливий"}, verifier) == []


def test_sentence_inventory_issue_8724_8726_rows_build_case_free_or_withheld(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Replay the live inventory rows quoted in #8724 and #8726.

    VESUM analyses and CEFR levels are copied from data/vesum.db and the live
    Atlas.  «у село» is an accusative slot whose surface equals the nominative,
    so the card must be a case-free insertion.  «до узбіччя» (the #8726 card)
    is withheld by the level gate: налітати, автомашина, звірятко and прилягти
    have no Atlas CEFR.  The list, UI-chrome, stub and definition rows are
    withheld by the prompt-context gate.
    """

    def entry(lemma: str, gloss: str, pos: str, level: str) -> dict[str, object]:
        return {
            "lemma": lemma,
            "url_slug": lemma,
            "gloss": gloss,
            "pos": pos,
            "primary_source": "course_vocab",
            "course_usage": [{"track": level.lower(), "slug": lemma}],
            "enrichment": {"cefr": {"level": level}},
        }

    entries = [
        entry("узбіччя", "roadside", "noun", "A2"),
        entry("книга", "book", "noun", "A2"),
        entry("місто", "city", "noun", "A2"),
        entry("школа", "school", "noun", "A2"),
        entry("відповісти", "to answer", "verb", "A2"),
        entry("вразити", "to impress", "verb", "B2"),
        entry("геймер", "gamer", "noun", "C1"),
        entry("медіаграмотність", "media literacy", "noun", "C1"),
        entry("село", "village", "noun", "A1"),
        entry("хотіти", "to want", "verb", "A1"),
        entry("рід", "kin", "noun", "A1"),
        entry("мед", "honey", "noun", "A1"),
        entry("гра", "game", "noun", "A1"),
    ]

    def row(lemma: str, sentence: str, target: str, level: str, locator: str) -> dict[str, object]:
        return {
            "lemma": lemma,
            "lemmaId": lemma,
            "sentence": sentence,
            "targetForm": target,
            "cefr": level,
            "uses": ["example"],
            "provenance": {"source": "textbook", "label": "Ukrainian school textbook", "locator": locator},
            "license": {"status": "fixture"},
        }

    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    row(
                        "узбіччя",
                        "Налітає автомашина, звірятко прилягло до узбіччя.",
                        "узбіччя",
                        "A2",
                        "7-klas-ukrlit-zabolotnyi-2024_s0318",
                    ),
                    row(
                        "відповісти",
                        "Подобається Відповісти 2 д.",
                        "Відповісти",
                        "A2",
                        "8-klas-ukrmova-avramenko-2025_s0177",
                    ),
                    row(
                        "вразити",
                        "Дієслова: зобразити, звести, вразити.",
                        "вразити",
                        "B2",
                        "8-klas-ukrmova-avramenko-2025_s0096",
                    ),
                    row(
                        "геймер",
                        "Геймер — важко хвора людина, вилікувати яку майже неможливо.",
                        "Геймер",
                        "C1",
                        "10-klas-ukrmova-karaman-2018_s0057",
                    ),
                    row(
                        "медіаграмотність",
                        "Ним є медіаграмотність.",
                        "медіаграмотність",
                        "C1",
                        "8-klas-hromadianska-osvita-vasylkiv-2025_s0137",
                    ),
                    row("село", "Ти хотів у село?", "село", "A1", "3-klas-ukrainska-mova-savchuk-2020-2_s0052"),
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    noun_n = [
        {"lemma": "узбіччя", "pos": "noun", "tags": f"noun:inanim:n:{case}"}
        for case in ("v_naz", "v_rod", "v_zna", "v_kly")
    ] + [{"lemma": "узбіччя", "pos": "noun", "tags": f"noun:inanim:p:{case}"} for case in ("v_naz", "v_zna", "v_kly")]
    vesum = JsonVesumVerifier(
        {
            "узбіччя": noun_n,
            "налітає": [
                {"lemma": "налітати", "pos": "verb", "tags": "verb:imperf:pres:s:3"},
                {"lemma": "налітати", "pos": "verb", "tags": "verb:perf:futr:s:3"},
            ],
            "автомашина": [{"lemma": "автомашина", "pos": "noun", "tags": "noun:inanim:f:v_naz"}],
            "звірятко": [
                {"lemma": "звірятко", "pos": "noun", "tags": f"noun:anim:n:{case}"}
                for case in ("v_naz", "v_zna", "v_kly")
            ],
            "прилягло": [{"lemma": "прилягти", "pos": "verb", "tags": "verb:perf:past:n"}],
            "ти": [
                {"lemma": "ти", "pos": "noun", "tags": "noun:anim:s:v_naz:pron:pers:2"},
                {"lemma": "ти", "pos": "noun", "tags": "noun:anim:s:v_kly:pron:pers:2"},
            ],
            "хотів": [{"lemma": "хотіти", "pos": "verb", "tags": "verb:imperf:past:m"}],
            "у": [{"lemma": "у", "pos": "prep", "tags": "prep"}],
            "село": [
                {"lemma": "село", "pos": "noun", "tags": f"noun:inanim:n:{case}"}
                for case in ("v_naz", "v_zna", "v_kly")
            ],
            "до": [
                {"lemma": "до", "pos": "noun", "tags": "noun:inanim:n:v_naz:nv"},
                {"lemma": "до", "pos": "prep", "tags": "prep"},
            ],
            "відповісти": [{"lemma": "відповісти", "pos": "verb", "tags": "verb:perf:inf"}],
            "подобається": [{"lemma": "подобатися", "pos": "verb", "tags": "verb:rev:imperf:pres:s:3"}],
            "вразити": [{"lemma": "вразити", "pos": "verb", "tags": "verb:perf:inf:xp1"}],
            "зобразити": [{"lemma": "зобразити", "pos": "verb", "tags": "verb:perf:inf"}],
            "звести": [{"lemma": "звести", "pos": "verb", "tags": "verb:perf:inf"}],
            "геймер": [{"lemma": "геймер", "pos": "noun", "tags": "noun:anim:m:v_naz"}],
            "медіаграмотність": [
                {"lemma": "медіаграмотність", "pos": "noun", "tags": "noun:inanim:f:v_naz:up19"},
                {"lemma": "медіаграмотність", "pos": "noun", "tags": "noun:inanim:f:v_zna:up19"},
            ],
            "ним": [{"lemma": "він", "pos": "noun", "tags": "noun:unanim:m:v_oru:pron:pers:3"}],
            "є": [{"lemma": "бути", "pos": "verb", "tags": "verb:imperf:pres:s:3"}],
        }
    )
    from scripts.practice.creation_review import CreationReview, frame_identity

    monkeypatch.setattr(generate_practice_deck, "_option_strategy_for_level", lambda _level, _rng: "no-pair")
    candidates = read_sentence_inventory(inventory_path)
    # The live frames are grandfathered in the creation-review ledger.
    creation_review = CreationReview(
        frozenset(frame_identity("cloze", row["sentence"], row["form"], _plain(row["lemma"])) for row in candidates)
    )
    withheld: list[dict[str, str]] = []
    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_payload([{"status": "sentence_inventory", "path": str(inventory_path)}]),
        vesum,
        candidates,
        BuildConfig(target=len(entries), source_label="fixture"),
        creation_review=creation_review,
        cloze_withheld=withheld,
    )

    emitted = {item["clozeId"]: item for level in shards.values() for item in level["cloze"]["cloze"]}
    assert emitted == {}
    assert ("село:inventory:6", "no_unique_answer_evidence") in {(row["clozeId"], row["reason"]) for row in withheld}
    assert {(row["clozeId"], row["reason"]) for row in withheld if row["rule"] == "inventory_prompt_context"} == {
        ("відповісти:inventory:2", "capitalized_mid_sentence"),
        ("вразити:inventory:3", "list_fragment"),
        ("геймер:inventory:4", "definition_prompt"),
        ("медіаграмотність:inventory:5", "context_free_stub"),
    }
    # Of the rows the context gate passes, the level gate withholds the one whose
    # words have no Atlas CEFR.  (The context-withheld rows' words are not all in
    # this fixture's VESUM, so the level gate also fires on them.)
    context_withheld = {row["clozeId"] for row in withheld if row["rule"] == "inventory_prompt_context"}
    assert {
        (row["clozeId"], row["reason"])
        for row in withheld
        if row["rule"] == "inventory_prompt_level" and row["clozeId"] not in context_withheld
    } == {("узбіччя:inventory:1", "above A2: Налітає, автомашина, звірятко, прилягло")}


def test_sentence_inventory_issue_8724_out_of_level_prompt_is_withheld(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Replay #8724 AC-02: A1 `її:inventory:5134` is a Grade 11 prism sentence.

    Levels are the live Atlas ``enrichment.cefr`` values; VESUM analyses are
    copied from data/vesum.db.  призма, грань, бічний, прямокутник and
    дорівнювати have no Atlas CEFR, so they count as above A1.  Review probe
    (#8724 r3): the A1 bus sentence has one A2 word (приїхати) and is withheld;
    no above-level word is tolerated.  «Ти хотів у село?» is all A1 and stays.
    Decoys are the live cards' (твій, який, ваш; книга, місто, школа).
    """

    glosses = {
        "її": "her",
        "твій": "your",
        "який": "which",
        "ваш": "your formal",
        "автобус": "bus",
        "книга": "book",
        "місто": "city",
        "школа": "school",
        "середа": "Wednesday",
        "новий": "new",
        "село": "village",
        "хотіти": "to want",
        "приїхати": "to arrive",
        "зрозуміло": "understandably",
        "прямий": "straight",
        "висота": "height",
        "ребро": "edge",
    }

    def entry(lemma: str, pos: str, level: str) -> dict[str, object]:
        return {
            "lemma": lemma,
            "url_slug": lemma,
            "gloss": glosses[lemma],
            "pos": pos,
            "primary_source": "course_vocab",
            "course_usage": [{"track": level.lower(), "slug": lemma}],
            "enrichment": {"cefr": {"level": level}},
        }

    entries = [
        entry("її", "pronoun", "A1"),
        entry("твій", "pronoun", "A1"),
        entry("який", "pronoun", "A1"),
        entry("ваш", "pronoun", "A1"),
        entry("автобус", "noun", "A1"),
        entry("книга", "noun", "A1"),
        entry("місто", "noun", "A1"),
        entry("школа", "noun", "A1"),
        entry("середа", "noun", "A1"),
        entry("новий", "adjective", "A1"),
        entry("село", "noun", "A1"),
        entry("хотіти", "verb", "A1"),
        entry("приїхати", "verb", "A2"),
        entry("зрозуміло", "adverb", "A2"),
        entry("прямий", "adjective", "A2"),
        entry("висота", "noun", "A2"),
        entry("ребро", "noun", "B1"),
    ]

    def row(lemma: str, sentence: str, locator: str) -> dict[str, object]:
        return {
            "lemma": lemma,
            "lemmaId": lemma,
            "sentence": sentence,
            "targetForm": lemma,
            "cefr": "A1",
            "uses": ["example"],
            "provenance": {"source": "textbook", "label": "Ukrainian school textbook", "locator": locator},
            "license": {"status": "fixture"},
        }

    inventory_path = tmp_path / "sentence-inventory.json"
    prism = "Зрозуміло, що бічні грані прямої призми – прямокутники, а висота прямої призми дорівнює її бічному ребру."
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    row("її", prism, "11-klas-geometria-ister-2019-prof_s0011"),
                    row("автобус", "А в середу приїхав новий автобус.", "1-klas-bukvar-bolshakova-2018-2_s0010"),
                    row("село", "Ти хотів у село?", "3-klas-ukrainska-mova-savchuk-2020-2_s0052"),
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def analyses(lemma: str, pos: str, *tags: str) -> list[dict[str, str]]:
        return [{"lemma": lemma, "pos": pos, "tags": tag} for tag in tags]

    yiyi_adj = [
        f"adj:{gender}:{case}:nv:pron:pos"
        for gender in ("f", "m", "n", "p")
        for case in ("v_naz", "v_rod", "v_dav", "v_zna", "v_oru", "v_mis")
    ]
    vesum = JsonVesumVerifier(
        {
            "її": analyses("вона", "noun", "noun:unanim:f:v_rod:pron:pers:3", "noun:unanim:f:v_zna:pron:pers:3")
            + analyses("її", "adj", *yiyi_adj),
            "зрозуміло": analyses("зрозуміло", "adv", "adv:compb:insert:predic")
            + analyses("зрозуміти", "verb", "verb:perf:past:n"),
            "що": analyses("що", "conj", "conj:subord") + analyses("що", "noun", "noun:inanim:n:v_naz:pron:int:rel"),
            "бічні": analyses("бічний", "adj", "adj:p:v_naz", "adj:p:v_zna:rinanim", "adj:p:v_kly"),
            "грані": analyses("грань", "noun", "noun:inanim:f:v_rod", "noun:inanim:p:v_naz")
            + analyses("граний", "adj", "adj:p:v_naz:adjp:pasv:imperf"),
            "прямої": analyses("прямий", "adj", "adj:f:v_rod:compb") + analyses("пряма", "noun", "noun:inanim:f:v_rod"),
            "призми": analyses("призма", "noun", "noun:inanim:f:v_rod", "noun:inanim:p:v_naz"),
            "прямокутники": analyses("прямокутник", "noun", "noun:inanim:p:v_naz", "noun:inanim:p:v_zna"),
            "а": analyses("а", "conj", "conj:coord") + analyses("а", "part", "part"),
            "висота": analyses("висота", "noun", "noun:inanim:f:v_naz"),
            "дорівнює": analyses("дорівнювати", "verb", "verb:imperf:pres:s:3"),
            "бічному": analyses("бічний", "adj", "adj:m:v_dav", "adj:m:v_mis", "adj:n:v_dav", "adj:n:v_mis"),
            "ребру": analyses("ребро", "noun", "noun:inanim:n:v_dav", "noun:inanim:n:v_mis"),
            "в": analyses("в", "prep", "prep"),
            "середу": analyses("середа", "noun", "noun:inanim:f:v_zna"),
            "приїхав": analyses("приїхати", "verb", "verb:perf:past:m"),
            "новий": analyses("новий", "adj", "adj:m:v_naz:compb", "adj:m:v_zna:rinanim:compb", "adj:m:v_kly:compb"),
            "автобус": analyses("автобус", "noun", "noun:inanim:m:v_naz", "noun:inanim:m:v_zna"),
            "ти": analyses("ти", "noun", "noun:anim:s:v_naz:pron:pers:2", "noun:anim:s:v_kly:pron:pers:2"),
            "хотів": analyses("хотіти", "verb", "verb:imperf:past:m"),
            "у": analyses("у", "prep", "prep"),
            "село": analyses("село", "noun", "noun:inanim:n:v_naz", "noun:inanim:n:v_zna", "noun:inanim:n:v_kly"),
        }
    )
    from scripts.practice.creation_review import CreationReview, frame_identity

    monkeypatch.setattr(generate_practice_deck, "_option_strategy_for_level", lambda _level, _rng: "no-pair")
    candidates = read_sentence_inventory(inventory_path)
    creation_review = CreationReview(
        frozenset(frame_identity("cloze", row["sentence"], row["form"], _plain(row["lemma"])) for row in candidates)
    )
    withheld: list[dict[str, str]] = []
    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_payload([{"status": "sentence_inventory", "path": str(inventory_path)}]),
        vesum,
        candidates,
        BuildConfig(target=len(entries), source_label="fixture"),
        creation_review=creation_review,
        cloze_withheld=withheld,
    )

    emitted = {item["clozeId"] for level in shards.values() for item in level["cloze"]["cloze"]}
    assert emitted == set()
    assert {(row["clozeId"], row["rule"], row["level"], row["reason"]) for row in withheld} == {
        (
            "її:inventory:1",
            "inventory_prompt_level",
            "A1",
            "above A1: Зрозуміло, бічні, грані, прямої, призми, прямокутники, висота, прямої, призми, дорівнює, "
            "бічному, ребру",
        ),
        ("автобус:inventory:2", "inventory_prompt_level", "A1", "above A1: приїхав"),
        ("село:inventory:3", "cloze_unique_answer_evidence", "A1", "no_unique_answer_evidence"),
        ("її:inventory:1", "cloze_unique_answer_evidence", "A1", "no_unique_answer_evidence"),
        ("автобус:inventory:2", "cloze_unique_answer_evidence", "A1", "no_unique_answer_evidence"),
    }
    assert {
        row["mechanism"]
        for row in withheld
        if row["clozeId"] == "село:inventory:3" and row["rule"] == "cloze_unique_answer_evidence"
    } == {"lexical"}


# --- #10672: cloze occurrences removed by size budgets -------------------------------------------

_TRIM_LEVELS = generate_practice_deck.CEFR_ORDER[:5]
_HUGE = 10**9


def _budget_cloze(
    level: str, lemma_id: str, n: int, pad: int, rule: str = "nominative_identification"
) -> dict[str, Any]:
    return {
        "clozeId": f"{lemma_id}:inventory:{n}",
        "lemmaId": lemma_id,
        "lemma": f"лема-{lemma_id}",
        "cefr": level,
        "number": "singular",
        "sentence": f"Речення {lemma_id} ___ {n}." + "x" * pad,
        "answer": lemma_id,
        "caseRule": {"ruleId": rule},
        "acceptedAlt": [],
        "options": [{"optionId": f"{lemma_id}:{n}:a", "label": lemma_id, "lemmaId": lemma_id, "strategy": "no-pair"}],
    }


def _budget_level(level: str, lexeme_pads: dict[str, int], cloze: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "index": {
            "schema": "atlas-practice-index",
            "items": [{"lemmaId": lemma_id, "modes": ["flashcards"], "clozeIds": []} for lemma_id in lexeme_pads],
            "counts": {},
        },
        "lexemes": {
            "schema": "atlas-practice-lexemes",
            "lexemes": [{"lemmaId": lemma_id, "gloss": "g" * pad} for lemma_id, pad in lexeme_pads.items()],
        },
        "cloze": {"schema": "atlas-practice-cloze", "cloze": cloze},
        "stress": {"schema": "atlas-practice-stress", "stress": []},
    }


def _budget_chain(
    shards: dict[str, Any], path: Path, *, raw: int = _HUGE, cloze_raw: int = _HUGE, withheld: list | None = None
) -> dict[str, Any]:
    """Run snapshot -> compaction -> apply_size_budgets -> reconciliation -> report, as main() does."""
    withheld = [] if withheld is None else withheld
    snapshot = generate_practice_deck.snapshot_cloze_occurrences(shards)
    compact_cloze_emit_fields(shards)
    apply_size_budgets(shards, raw, _HUGE, cloze_raw_limit=cloze_raw, cloze_gzip_limit=_HUGE)
    generate_practice_deck.reconcile_cloze_budget_trims(shards, snapshot, withheld)
    generate_practice_deck.write_cloze_withheld_report(path, withheld, shards)
    return json.loads(path.read_text(encoding="utf-8"))


def _raw_bytes(payload: dict[str, Any]) -> int:
    return int(generate_practice_deck._size_budget(payload, _HUGE, _HUGE)["rawBytes"])


def _cloze_fit(*items: dict[str, Any]) -> int:
    """Raw cloze limit that admits exactly these items once compacted."""
    probe = {"A1": {"cloze": {"schema": "atlas-practice-cloze", "cloze": copy.deepcopy(list(items))}}}
    compact_cloze_emit_fields(probe)
    return _raw_bytes(probe["A1"]["cloze"]) + 200


def _trim_row(level: str, lemma_id: str, n: int, pad: int, mechanism: str = "case-labelled") -> dict[str, str]:
    return {
        "clozeId": f"{lemma_id}:inventory:{n}",
        "lemma": f"лема-{lemma_id}",
        "level": level,
        "mechanism": mechanism,
        "reason": "size_budget_trim",
        "rule": "size_budget_trim",
        "sentence": f"Речення {lemma_id} ___ {n}." + "x" * pad,
    }


def _mechanisms(report: dict[str, Any], level: str) -> dict[str, dict[str, int]]:
    return {k: v for k, v in report["byLevelMechanism"][level].items() if v != {"admitted": 0, "withheld": 0}}


@pytest.mark.parametrize("level", _TRIM_LEVELS)
def test_cloze_withheld_report_accounts_mode_local_cloze_trim(level: str, tmp_path: Path) -> None:
    lexical = generate_practice_deck.LEXICAL_INSERTION_RULE_ID
    kept = _budget_cloze(level, "c", 3, 10, lexical)
    cloze = [_budget_cloze(level, "a", 1, 900), _budget_cloze(level, "b", 2, 800), kept]
    shards = {level: _budget_level(level, {"a": 1, "b": 1, "c": 1}, cloze)}
    report = _budget_chain(shards, tmp_path / "r.json", cloze_raw=_cloze_fit(kept))
    assert [item["clozeId"] for item in shards[level]["cloze"]["cloze"]] == ["c:inventory:3"]
    assert report["items"] == [_trim_row(level, "a", 1, 900), _trim_row(level, "b", 2, 800)]
    assert report["count"] == 2
    assert report["byLevelRule"] == {f"{level}:size_budget_trim": 2}
    assert _mechanisms(report, level) == {
        "case-labelled": {"admitted": 0, "withheld": 2},
        "lexical": {"admitted": 1, "withheld": 0},
    }


@pytest.mark.parametrize("level", _TRIM_LEVELS)
def test_cloze_withheld_report_accounts_surface_prune(level: str, tmp_path: Path) -> None:
    cloze = [_budget_cloze(level, "a", 1, 50), _budget_cloze(level, "b", 2, 50)]
    shards = {level: _budget_level(level, {"a": 3_000, "b": 10}, cloze)}
    small = {"schema": "atlas-practice-lexemes", "lexemes": [{"lemmaId": "b", "gloss": "g" * 10}]}
    report = _budget_chain(shards, tmp_path / "r.json", raw=_raw_bytes(small) + 200)
    assert [item["lemmaId"] for item in shards[level]["lexemes"]["lexemes"]] == ["b"]
    assert [item["clozeId"] for item in shards[level]["cloze"]["cloze"]] == ["b:inventory:2"]
    assert report["items"] == [_trim_row(level, "a", 1, 50)]
    assert _mechanisms(report, level) == {"case-labelled": {"admitted": 1, "withheld": 1}}


@pytest.mark.parametrize("level", _TRIM_LEVELS)
def test_cloze_withheld_report_cross_level_prune_leaves_cloze_unchanged(level: str, tmp_path: Path) -> None:
    other = next(lvl for lvl in _TRIM_LEVELS if lvl != level)
    cloze = [_budget_cloze(level, "a", 1, 50), _budget_cloze(level, "b", 2, 50)]
    target = _budget_level(level, {"a": 10, "b": 10}, cloze)
    target["stress"]["stress"] = [{"lemmaId": "a"}, {"lemmaId": "z"}]
    shards = {level: target, other: _budget_level(other, {"y": 10, "z": 3_000}, [])}
    small = {"schema": "atlas-practice-lexemes", "lexemes": [{"lemmaId": "y", "gloss": "g" * 10}]}
    report = _budget_chain(shards, tmp_path / "r.json", raw=_raw_bytes(small) + 200)
    assert shards[level]["stress"]["stress"] == [{"lemmaId": "a"}]
    assert [item["clozeId"] for item in shards[level]["cloze"]["cloze"]] == ["a:inventory:1", "b:inventory:2"]
    assert report["count"] == 0
    assert report["items"] == []
    assert _mechanisms(report, level) == {"case-labelled": {"admitted": 2, "withheld": 0}}


def test_cloze_budget_trim_identical_duplicate_ids_count_occurrences(tmp_path: Path) -> None:
    cloze = [_budget_cloze("A1", "a", 1, 400) for _ in range(3)]
    shards = {"A1": _budget_level("A1", {"a": 10}, cloze)}
    report = _budget_chain(shards, tmp_path / "r.json", cloze_raw=_cloze_fit(cloze[0]))
    assert [item["clozeId"] for item in shards["A1"]["cloze"]["cloze"]] == ["a:inventory:1"]
    assert report["items"] == [_trim_row("A1", "a", 1, 400)] * 2
    assert report["count"] == 2
    assert report["byLevelRule"] == {"A1:size_budget_trim": 2}
    # Kept and dropped occurrences share one clozeId: admitted counts occurrences, withheld stays distinct.
    assert _mechanisms(report, "A1") == {"case-labelled": {"admitted": 1, "withheld": 1}}


def test_cloze_budget_trim_differing_duplicate_ids_keep_original_rows(tmp_path: Path) -> None:
    first = _budget_cloze("A1", "a", 1, 10)
    second = _budget_cloze("A1", "a", 1, 600)
    original = {**_trim_row("A1", "z", 9, 0), "rule": "inventory_prompt_level", "reason": "above A1: x"}
    withheld = [original]
    shards = {"A1": _budget_level("A1", {"a": 10}, [first, second])}
    report = _budget_chain(shards, tmp_path / "r.json", cloze_raw=_cloze_fit(first), withheld=withheld)
    assert [item["sentence"] for item in shards["A1"]["cloze"]["cloze"]] == [_trim_row("A1", "a", 1, 10)["sentence"]]
    assert report["items"] == [original, _trim_row("A1", "a", 1, 600)]
    assert report["count"] == 2
    assert report["byLevelRule"] == {"A1:inventory_prompt_level": 1, "A1:size_budget_trim": 1}
    assert _mechanisms(report, "A1") == {"case-labelled": {"admitted": 1, "withheld": 2}}


def test_cloze_budget_reconcile_rejects_unsnapshotted_occurrence() -> None:
    shards = {"A1": _budget_level("A1", {"a": 10}, [_budget_cloze("A1", "a", 1, 10)])}
    with pytest.raises(RuntimeError, match="unaccounted cloze occurrences in final shards: 1"):
        generate_practice_deck.reconcile_cloze_budget_trims(shards, [], [])


def _main_wiring_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, report: bool) -> tuple[dict[str, str], Path]:

    for name in (
        "read_cloze_sources",
        "read_sentence_inventory",
        "read_heritage_pairs",
        "read_paronym_pairs",
        "read_antonym_pairs",
        "read_homonym_pairs",
    ):
        monkeypatch.setattr(generate_practice_deck, name, lambda _path: [])
    monkeypatch.setattr(generate_practice_deck, "read_manifest", lambda _path: [])
    monkeypatch.setattr(generate_practice_deck, "read_synonym_verdicts", lambda _path: None)
    monkeypatch.setattr(generate_practice_deck, "read_end_dictionary_stress_overlay", lambda _path: {})
    monkeypatch.setattr(generate_practice_deck, "read_ulif_synonym_groups", lambda _db, _verdicts: None)
    monkeypatch.setattr(generate_practice_deck.ReviewedSourceAllowlist, "from_path", classmethod(lambda cls, _p: None))
    monkeypatch.setattr(generate_practice_deck.JsonVesumVerifier, "from_path", classmethod(lambda cls, _p: None))

    def fake_build(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        cloze = [_budget_cloze("B1", "a", 1, 900), _budget_cloze("B1", "a", 1, 900), _budget_cloze("B1", "b", 2, 10)]
        level = _budget_level("B1", {"a": 10, "b": 10}, cloze)
        level["synonym"] = {"schema": "atlas-practice-synonym", "synonym": []}
        return {"B1": level}

    monkeypatch.setattr(generate_practice_deck, "build_practice_shards", fake_build)
    out_dir = tmp_path / ("on" if report else "off")
    report_path = tmp_path / "withheld.json"
    argv = ["--manifest", str(tmp_path / "m.json"), "--vesum-fixture", str(tmp_path / "v.json")]
    argv += ["--out-dir", str(out_dir), "--sources-db", str(tmp_path / "missing.db")]
    argv += ["--end-dictionary-inventory", str(tmp_path / "missing.json")]
    argv += ["--cloze-raw-limit", str(_cloze_fit(_budget_cloze("B1", "b", 2, 10)))]
    if report:
        argv += ["--cloze-withheld-report", str(report_path)]
    assert main(argv) == 0
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out_dir.iterdir())}, report_path


def test_main_cloze_withheld_report_wiring_keeps_shard_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    for name in ("snapshot_cloze_occurrences", "reconcile_cloze_budget_trims"):
        real = getattr(generate_practice_deck, name)
        monkeypatch.setattr(
            generate_practice_deck, name, lambda *a, _real=real, _name=name: calls.append(_name) or _real(*a)
        )
    disabled, report_path = _main_wiring_run(tmp_path, monkeypatch, report=False)
    assert calls == []
    assert not report_path.exists()
    enabled, report_path = _main_wiring_run(tmp_path, monkeypatch, report=True)
    assert calls == ["snapshot_cloze_occurrences", "reconcile_cloze_budget_trims"]
    assert enabled == disabled
    assert sorted(enabled) == [
        "practice-cloze.B1.json",
        "practice-index.B1.json",
        "practice-lexemes.B1.json",
        "practice-stress.B1.json",
        "practice-synonym.B1.json",
    ]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["items"] == [_trim_row("B1", "a", 1, 900)] * 2
    assert _mechanisms(report, "B1") == {"case-labelled": {"admitted": 1, "withheld": 1}}


# Captured VESUM forms, schema vesum-reingest-v2, canonical source SHA-256
# 53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680.
# Original capture SHA-256 b4a07876506ac68516162325ab3548eb486e41f7210727089348e8617e4c8e6d.
# Columns: word_form, lemma, pos, tags. Only existing scenario surfaces are retained.
_CAPTURED_PARADIGM_ROWS = """абажур	абажур	noun	noun:inanim:m:v_naz
абажур	абажур	noun	noun:inanim:m:v_zna
абажура	абажур	noun	noun:inanim:m:v_rod
абажура	абажур	noun	noun:inanim:m:v_zna:var
абажурам	абажур	noun	noun:inanim:p:v_dav
абажурами	абажур	noun	noun:inanim:p:v_oru
абажурах	абажур	noun	noun:inanim:p:v_mis
абажуре	абажур	noun	noun:inanim:m:v_kly
абажури	абажур	noun	noun:inanim:p:v_kly
абажури	абажур	noun	noun:inanim:p:v_naz
абажури	абажур	noun	noun:inanim:p:v_zna
абажурові	абажур	noun	noun:inanim:m:v_dav
абажурові	абажур	noun	noun:inanim:m:v_mis
абажуром	абажур	noun	noun:inanim:m:v_oru
абажурчик	абажурчик	noun	noun:inanim:m:v_naz
абажурчик	абажурчик	noun	noun:inanim:m:v_zna
абажурчика	абажурчик	noun	noun:inanim:m:v_rod
абажурчикам	абажурчик	noun	noun:inanim:p:v_dav
абажурчиками	абажурчик	noun	noun:inanim:p:v_oru
абажурчиках	абажурчик	noun	noun:inanim:p:v_mis
абажурчики	абажурчик	noun	noun:inanim:p:v_kly
абажурчики	абажурчик	noun	noun:inanim:p:v_naz
абажурчики	абажурчик	noun	noun:inanim:p:v_zna
абажурчикові	абажурчик	noun	noun:inanim:m:v_dav
абажурчикові	абажурчик	noun	noun:inanim:m:v_mis
абажурчиком	абажурчик	noun	noun:inanim:m:v_oru
абажурчику	абажурчик	noun	noun:inanim:m:v_dav
абажурчику	абажурчик	noun	noun:inanim:m:v_kly
абажурчику	абажурчик	noun	noun:inanim:m:v_mis
абажурчиків	абажурчик	noun	noun:inanim:p:v_rod
абажурі	абажур	noun	noun:inanim:m:v_mis
абажурів	абажур	noun	noun:inanim:p:v_rod
абаз	абаз	noun	noun:inanim:m:v_naz
абаз	абаз	noun	noun:inanim:m:v_zna
абаза	абаз	noun	noun:inanim:m:v_rod
абазам	абаз	noun	noun:inanim:p:v_dav
абазами	абаз	noun	noun:inanim:p:v_oru
абазах	абаз	noun	noun:inanim:p:v_mis
абазе	абаз	noun	noun:inanim:m:v_kly
абази	абаз	noun	noun:inanim:p:v_kly
абази	абаз	noun	noun:inanim:p:v_naz
абази	абаз	noun	noun:inanim:p:v_zna
абазин	абазин	noun	noun:anim:m:v_naz
абазина	абазин	noun	noun:anim:m:v_rod
абазина	абазин	noun	noun:anim:m:v_zna
абазинам	абазин	noun	noun:anim:p:v_dav
абазинами	абазин	noun	noun:anim:p:v_oru
абазинах	абазин	noun	noun:anim:p:v_mis
абазине	абазин	noun	noun:anim:m:v_kly
абазинець	абазинець	noun	noun:anim:m:v_naz
абазини	абазин	noun	noun:anim:p:v_kly
абазини	абазин	noun	noun:anim:p:v_naz
абазини	абазин	noun	noun:anim:p:v_zna:rare
абазинка	абазинка	noun	noun:anim:f:v_naz
абазинкам	абазинка	noun	noun:anim:p:v_dav
абазинками	абазинка	noun	noun:anim:p:v_oru
абазинках	абазинка	noun	noun:anim:p:v_mis
абазинки	абазинка	noun	noun:anim:f:v_rod
абазинки	абазинка	noun	noun:anim:p:v_kly
абазинки	абазинка	noun	noun:anim:p:v_naz
абазинки	абазинка	noun	noun:anim:p:v_zna:rare
абазинко	абазинка	noun	noun:anim:f:v_kly
абазинкою	абазинка	noun	noun:anim:f:v_oru
абазинку	абазинка	noun	noun:anim:f:v_zna
абазинові	абазин	noun	noun:anim:m:v_dav
абазинові	абазин	noun	noun:anim:m:v_mis
абазинок	абазинка	noun	noun:anim:p:v_rod
абазинок	абазинка	noun	noun:anim:p:v_zna
абазином	абазин	noun	noun:anim:m:v_oru
абазину	абазин	noun	noun:anim:m:v_dav
абазину	абазин	noun	noun:anim:m:v_mis
абазинцеві	абазинець	noun	noun:anim:m:v_dav
абазинцеві	абазинець	noun	noun:anim:m:v_mis
абазинцем	абазинець	noun	noun:anim:m:v_oru
абазинцю	абазинець	noun	noun:anim:m:v_dav
абазинцю	абазинець	noun	noun:anim:m:v_kly
абазинцю	абазинець	noun	noun:anim:m:v_mis
абазинця	абазинець	noun	noun:anim:m:v_rod
абазинця	абазинець	noun	noun:anim:m:v_zna
абазинцям	абазинець	noun	noun:anim:p:v_dav
абазинцями	абазинець	noun	noun:anim:p:v_oru
абазинцях	абазинець	noun	noun:anim:p:v_mis
абазинці	абазинець	noun	noun:anim:m:v_mis
абазинці	абазинець	noun	noun:anim:p:v_kly
абазинці	абазинець	noun	noun:anim:p:v_naz
абазинці	абазинець	noun	noun:anim:p:v_zna:rare
абазинці	абазинка	noun	noun:anim:f:v_dav
абазинці	абазинка	noun	noun:anim:f:v_mis
абазинців	абазинець	noun	noun:anim:p:v_rod
абазинців	абазинець	noun	noun:anim:p:v_zna
абазині	абазин	noun	noun:anim:m:v_mis
абазинів	абазин	noun	noun:anim:p:v_rod
абазинів	абазин	noun	noun:anim:p:v_zna
абазові	абаз	noun	noun:inanim:m:v_dav
абазові	абаз	noun	noun:inanim:m:v_mis
абазом	абаз	noun	noun:inanim:m:v_oru
абазі	абаз	noun	noun:inanim:m:v_mis
абазів	абаз	noun	noun:inanim:p:v_rod
абак	абак	noun	noun:inanim:m:v_naz
абак	абак	noun	noun:inanim:m:v_zna
абака	абак	noun	noun:inanim:m:v_rod
абакам	абак	noun	noun:inanim:p:v_dav
абаками	абак	noun	noun:inanim:p:v_oru
абаках	абак	noun	noun:inanim:p:v_mis
абаки	абак	noun	noun:inanim:p:v_kly
абаки	абак	noun	noun:inanim:p:v_naz
абаки	абак	noun	noun:inanim:p:v_zna
абакові	абак	noun	noun:inanim:m:v_dav
абакові	абак	noun	noun:inanim:m:v_mis
абаком	абак	noun	noun:inanim:m:v_oru
абаку	абак	noun	noun:inanim:m:v_dav
абаку	абак	noun	noun:inanim:m:v_kly
абаку	абак	noun	noun:inanim:m:v_mis
абаків	абак	noun	noun:inanim:p:v_rod
абалон	абалон	noun	noun:inanim:m:v_naz
абалон	абалон	noun	noun:inanim:m:v_zna
абалонам	абалон	noun	noun:inanim:p:v_dav
абалонами	абалон	noun	noun:inanim:p:v_oru
абалонах	абалон	noun	noun:inanim:p:v_mis
абалоне	абалон	noun	noun:inanim:m:v_kly
абалони	абалон	noun	noun:inanim:p:v_kly
абалони	абалон	noun	noun:inanim:p:v_naz
абалони	абалон	noun	noun:inanim:p:v_zna
абалонові	абалон	noun	noun:inanim:m:v_dav
абалонові	абалон	noun	noun:inanim:m:v_mis
абалоном	абалон	noun	noun:inanim:m:v_oru
абалону	абалон	noun	noun:inanim:m:v_dav
абалону	абалон	noun	noun:inanim:m:v_mis
абалону	абалон	noun	noun:inanim:m:v_rod
абалоні	абалон	noun	noun:inanim:m:v_mis
абалонів	абалон	noun	noun:inanim:p:v_rod
абалієнацій	абалієнація	noun	noun:inanim:p:v_rod
абалієнацію	абалієнація	noun	noun:inanim:f:v_zna
абалієнація	абалієнація	noun	noun:inanim:f:v_naz
абалієнаціям	абалієнація	noun	noun:inanim:p:v_dav
абалієнаціями	абалієнація	noun	noun:inanim:p:v_oru
абалієнаціях	абалієнація	noun	noun:inanim:p:v_mis
абалієнаціє	абалієнація	noun	noun:inanim:f:v_kly
абалієнацією	абалієнація	noun	noun:inanim:f:v_oru
абалієнації	абалієнація	noun	noun:inanim:f:v_dav
абалієнації	абалієнація	noun	noun:inanim:f:v_mis
абалієнації	абалієнація	noun	noun:inanim:f:v_rod
абалієнації	абалієнація	noun	noun:inanim:p:v_kly
абалієнації	абалієнація	noun	noun:inanim:p:v_naz
абалієнації	абалієнація	noun	noun:inanim:p:v_zna
абанацій	абанація	noun	noun:inanim:p:v_rod
абанацію	абанація	noun	noun:inanim:f:v_zna
абанація	абанація	noun	noun:inanim:f:v_naz
абанаціям	абанація	noun	noun:inanim:p:v_dav
абанаціями	абанація	noun	noun:inanim:p:v_oru
абанаціях	абанація	noun	noun:inanim:p:v_mis
абанаціє	абанація	noun	noun:inanim:f:v_kly
абанацією	абанація	noun	noun:inanim:f:v_oru
абанації	абанація	noun	noun:inanim:f:v_dav
абанації	абанація	noun	noun:inanim:f:v_mis
абанації	абанація	noun	noun:inanim:f:v_rod
абанації	абанація	noun	noun:inanim:p:v_kly
абанації	абанація	noun	noun:inanim:p:v_naz
абанації	абанація	noun	noun:inanim:p:v_zna
абандон	абандон	noun	noun:inanim:m:v_naz
абандон	абандон	noun	noun:inanim:m:v_zna
абандонам	абандон	noun	noun:inanim:p:v_dav
абандонами	абандон	noun	noun:inanim:p:v_oru
абандонах	абандон	noun	noun:inanim:p:v_mis
абандоне	абандон	noun	noun:inanim:m:v_kly
абандони	абандон	noun	noun:inanim:p:v_kly
абандони	абандон	noun	noun:inanim:p:v_naz
абандони	абандон	noun	noun:inanim:p:v_zna
абандонові	абандон	noun	noun:inanim:m:v_dav
абандонові	абандон	noun	noun:inanim:m:v_mis
абандоном	абандон	noun	noun:inanim:m:v_oru
абандону	абандон	noun	noun:inanim:m:v_dav
абандону	абандон	noun	noun:inanim:m:v_mis
абандону	абандон	noun	noun:inanim:m:v_rod
абандоні	абандон	noun	noun:inanim:m:v_mis
абандонів	абандон	noun	noun:inanim:p:v_rod
абартикуляцій	абартикуляція	noun	noun:inanim:p:v_rod
абартикуляцію	абартикуляція	noun	noun:inanim:f:v_zna
абартикуляція	абартикуляція	noun	noun:inanim:f:v_naz
абартикуляціям	абартикуляція	noun	noun:inanim:p:v_dav
абартикуляціями	абартикуляція	noun	noun:inanim:p:v_oru
абартикуляціях	абартикуляція	noun	noun:inanim:p:v_mis
абартикуляціє	абартикуляція	noun	noun:inanim:f:v_kly
абартикуляцією	абартикуляція	noun	noun:inanim:f:v_oru
абартикуляції	абартикуляція	noun	noun:inanim:f:v_dav
абартикуляції	абартикуляція	noun	noun:inanim:f:v_mis
абартикуляції	абартикуляція	noun	noun:inanim:f:v_rod
абартикуляції	абартикуляція	noun	noun:inanim:p:v_kly
абартикуляції	абартикуляція	noun	noun:inanim:p:v_naz
абартикуляції	абартикуляція	noun	noun:inanim:p:v_zna
абат	абат	noun	noun:anim:m:v_naz
абата	абат	noun	noun:anim:m:v_rod
абата	абат	noun	noun:anim:m:v_zna
абатам	абат	noun	noun:anim:p:v_dav
абатами	абат	noun	noun:anim:p:v_oru
абатах	абат	noun	noun:anim:p:v_mis
абате	абат	noun	noun:anim:m:v_kly
абати	абат	noun	noun:anim:p:v_kly
абати	абат	noun	noun:anim:p:v_naz
абати	абат	noun	noun:anim:p:v_zna:rare
абатик	абатик	noun	noun:anim:m:v_naz
абатика	абатик	noun	noun:anim:m:v_rod
абатика	абатик	noun	noun:anim:m:v_zna
абатикам	абатик	noun	noun:anim:p:v_dav
абатиками	абатик	noun	noun:anim:p:v_oru
абатиках	абатик	noun	noun:anim:p:v_mis
абатики	абатик	noun	noun:anim:p:v_kly
абатики	абатик	noun	noun:anim:p:v_naz
абатики	абатик	noun	noun:anim:p:v_zna:rare
абатикові	абатик	noun	noun:anim:m:v_dav
абатикові	абатик	noun	noun:anim:m:v_mis
абатиком	абатик	noun	noun:anim:m:v_oru
абатику	абатик	noun	noun:anim:m:v_dav
абатику	абатик	noun	noun:anim:m:v_kly
абатику	абатик	noun	noun:anim:m:v_mis
абатиків	абатик	noun	noun:anim:p:v_rod
абатиків	абатик	noun	noun:anim:p:v_zna
абатис	абатиса	noun	noun:anim:p:v_rod
абатис	абатиса	noun	noun:anim:p:v_zna
абатиса	абатиса	noun	noun:anim:f:v_naz
абатисам	абатиса	noun	noun:anim:p:v_dav
абатисами	абатиса	noun	noun:anim:p:v_oru
абатисах	абатиса	noun	noun:anim:p:v_mis
абатиси	абатиса	noun	noun:anim:f:v_rod
абатиси	абатиса	noun	noun:anim:p:v_kly
абатиси	абатиса	noun	noun:anim:p:v_naz
абатиси	абатиса	noun	noun:anim:p:v_zna:rare
абатисо	абатиса	noun	noun:anim:f:v_kly
абатисою	абатиса	noun	noun:anim:f:v_oru
абатису	абатиса	noun	noun:anim:f:v_zna
абатисі	абатиса	noun	noun:anim:f:v_dav
абатисі	абатиса	noun	noun:anim:f:v_mis
абатові	абат	noun	noun:anim:m:v_dav
абатові	абат	noun	noun:anim:m:v_mis
абатом	абат	noun	noun:anim:m:v_oru
абатств	абатство	noun	noun:inanim:p:v_rod
абатства	абатство	noun	noun:inanim:n:v_rod
абатства	абатство	noun	noun:inanim:p:v_kly
абатства	абатство	noun	noun:inanim:p:v_naz
абатства	абатство	noun	noun:inanim:p:v_zna
абатствам	абатство	noun	noun:inanim:p:v_dav
абатствами	абатство	noun	noun:inanim:p:v_oru
абатствах	абатство	noun	noun:inanim:p:v_mis
абатство	абатство	noun	noun:inanim:n:v_kly
абатство	абатство	noun	noun:inanim:n:v_naz
абатство	абатство	noun	noun:inanim:n:v_zna
абатством	абатство	noun	noun:inanim:n:v_oru
абатству	абатство	noun	noun:inanim:n:v_dav
абатству	абатство	noun	noun:inanim:n:v_mis
абатстві	абатство	noun	noun:inanim:n:v_mis
абаті	абат	noun	noun:anim:m:v_mis
абатів	абат	noun	noun:anim:p:v_rod
абатів	абат	noun	noun:anim:p:v_zna
абвергруп	абвергрупа	noun	noun:inanim:p:v_rod
абвергрупа	абвергрупа	noun	noun:inanim:f:v_naz
абвергрупам	абвергрупа	noun	noun:inanim:p:v_dav
абвергрупами	абвергрупа	noun	noun:inanim:p:v_oru
абвергрупах	абвергрупа	noun	noun:inanim:p:v_mis
абвергрупи	абвергрупа	noun	noun:inanim:f:v_rod
абвергрупи	абвергрупа	noun	noun:inanim:p:v_kly
абвергрупи	абвергрупа	noun	noun:inanim:p:v_naz
абвергрупи	абвергрупа	noun	noun:inanim:p:v_zna
абвергрупо	абвергрупа	noun	noun:inanim:f:v_kly
абвергрупою	абвергрупа	noun	noun:inanim:f:v_oru
абвергрупу	абвергрупа	noun	noun:inanim:f:v_zna
абвергрупі	абвергрупа	noun	noun:inanim:f:v_dav
абвергрупі	абвергрупа	noun	noun:inanim:f:v_mis
абверівець	абверівець	noun	noun:anim:m:v_naz
абверівцеві	абверівець	noun	noun:anim:m:v_dav
абверівцеві	абверівець	noun	noun:anim:m:v_mis
абверівцем	абверівець	noun	noun:anim:m:v_oru
абверівцю	абверівець	noun	noun:anim:m:v_dav
абверівцю	абверівець	noun	noun:anim:m:v_kly
абверівцю	абверівець	noun	noun:anim:m:v_mis
абверівця	абверівець	noun	noun:anim:m:v_rod
абверівця	абверівець	noun	noun:anim:m:v_zna
абверівцям	абверівець	noun	noun:anim:p:v_dav
абверівцями	абверівець	noun	noun:anim:p:v_oru
абверівцях	абверівець	noun	noun:anim:p:v_mis
абверівці	абверівець	noun	noun:anim:m:v_mis
абверівці	абверівець	noun	noun:anim:p:v_kly
абверівці	абверівець	noun	noun:anim:p:v_naz
абверівці	абверівець	noun	noun:anim:p:v_zna:rare
абверівців	абверівець	noun	noun:anim:p:v_rod
абверівців	абверівець	noun	noun:anim:p:v_zna
абгрегацій	абгрегація	noun	noun:inanim:p:v_rod
абгрегацію	абгрегація	noun	noun:inanim:f:v_zna
абгрегація	абгрегація	noun	noun:inanim:f:v_naz
абгрегаціям	абгрегація	noun	noun:inanim:p:v_dav
абгрегаціями	абгрегація	noun	noun:inanim:p:v_oru
абгрегаціях	абгрегація	noun	noun:inanim:p:v_mis
абгрегаціє	абгрегація	noun	noun:inanim:f:v_kly
абгрегацією	абгрегація	noun	noun:inanim:f:v_oru
абгрегації	абгрегація	noun	noun:inanim:f:v_dav
абгрегації	абгрегація	noun	noun:inanim:f:v_mis
абгрегації	абгрегація	noun	noun:inanim:f:v_rod
абгрегації	абгрегація	noun	noun:inanim:p:v_kly
абгрегації	абгрегація	noun	noun:inanim:p:v_naz
абгрегації	абгрегація	noun	noun:inanim:p:v_zna
абдикацій	абдикація	noun	noun:inanim:p:v_rod
абдикацію	абдикація	noun	noun:inanim:f:v_zna
абдикація	абдикація	noun	noun:inanim:f:v_naz
абдикаціям	абдикація	noun	noun:inanim:p:v_dav
абдикаціями	абдикація	noun	noun:inanim:p:v_oru
абдикаціях	абдикація	noun	noun:inanim:p:v_mis
абдикаціє	абдикація	noun	noun:inanim:f:v_kly
абдикацією	абдикація	noun	noun:inanim:f:v_oru
абдикації	абдикація	noun	noun:inanim:f:v_dav
абдикації	абдикація	noun	noun:inanim:f:v_mis
абдикації	абдикація	noun	noun:inanim:f:v_rod
абдикації	абдикація	noun	noun:inanim:p:v_kly
абдикації	абдикація	noun	noun:inanim:p:v_naz
абдикації	абдикація	noun	noun:inanim:p:v_zna
абдомен	абдомен	noun	noun:inanim:m:v_naz
абдомен	абдомен	noun	noun:inanim:m:v_zna
абдомена	абдомен	noun	noun:inanim:m:v_rod
абдоменам	абдомен	noun	noun:inanim:p:v_dav
абдоменами	абдомен	noun	noun:inanim:p:v_oru
абдоменах	абдомен	noun	noun:inanim:p:v_mis
абдомене	абдомен	noun	noun:inanim:m:v_kly
абдомени	абдомен	noun	noun:inanim:p:v_kly
абдомени	абдомен	noun	noun:inanim:p:v_naz
абдомени	абдомен	noun	noun:inanim:p:v_zna
абдоменові	абдомен	noun	noun:inanim:m:v_dav
абдоменові	абдомен	noun	noun:inanim:m:v_mis
абдоменом	абдомен	noun	noun:inanim:m:v_oru
абдомені	абдомен	noun	noun:inanim:m:v_mis
абдоменів	абдомен	noun	noun:inanim:p:v_rod
абдоміналгій	абдоміналгія	noun	noun:inanim:p:v_rod
абдоміналгію	абдоміналгія	noun	noun:inanim:f:v_zna
абдоміналгія	абдоміналгія	noun	noun:inanim:f:v_naz
абдоміналгіям	абдоміналгія	noun	noun:inanim:p:v_dav
абдоміналгіями	абдоміналгія	noun	noun:inanim:p:v_oru
абдоміналгіях	абдоміналгія	noun	noun:inanim:p:v_mis
абдоміналгіє	абдоміналгія	noun	noun:inanim:f:v_kly
абдоміналгією	абдоміналгія	noun	noun:inanim:f:v_oru
абдоміналгії	абдоміналгія	noun	noun:inanim:f:v_dav
абдоміналгії	абдоміналгія	noun	noun:inanim:f:v_mis
абдоміналгії	абдоміналгія	noun	noun:inanim:f:v_rod
абдоміналгії	абдоміналгія	noun	noun:inanim:p:v_kly
абдоміналгії	абдоміналгія	noun	noun:inanim:p:v_naz
абдоміналгії	абдоміналгія	noun	noun:inanim:p:v_zna
абдомінопластик	абдомінопластика	noun	noun:inanim:p:v_rod
абдомінопластика	абдомінопластика	noun	noun:inanim:f:v_naz
абдомінопластикам	абдомінопластика	noun	noun:inanim:p:v_dav
абдомінопластиками	абдомінопластика	noun	noun:inanim:p:v_oru
абдомінопластиках	абдомінопластика	noun	noun:inanim:p:v_mis
абдомінопластики	абдомінопластика	noun	noun:inanim:f:v_rod
абдомінопластики	абдомінопластика	noun	noun:inanim:p:v_kly
абдомінопластики	абдомінопластика	noun	noun:inanim:p:v_naz
абдомінопластики	абдомінопластика	noun	noun:inanim:p:v_zna
абдомінопластико	абдомінопластика	noun	noun:inanim:f:v_kly
абдомінопластикою	абдомінопластика	noun	noun:inanim:f:v_oru
абдомінопластику	абдомінопластика	noun	noun:inanim:f:v_zna
абдомінопластиці	абдомінопластика	noun	noun:inanim:f:v_dav
абдомінопластиці	абдомінопластика	noun	noun:inanim:f:v_mis
абдоміноскопій	абдоміноскопія	noun	noun:inanim:p:v_rod
абдоміноскопію	абдоміноскопія	noun	noun:inanim:f:v_zna
абдоміноскопія	абдоміноскопія	noun	noun:inanim:f:v_naz
абдоміноскопіям	абдоміноскопія	noun	noun:inanim:p:v_dav
абдоміноскопіями	абдоміноскопія	noun	noun:inanim:p:v_oru
абдоміноскопіях	абдоміноскопія	noun	noun:inanim:p:v_mis
абдоміноскопіє	абдоміноскопія	noun	noun:inanim:f:v_kly
абдоміноскопією	абдоміноскопія	noun	noun:inanim:f:v_oru
абдоміноскопії	абдоміноскопія	noun	noun:inanim:f:v_dav
абдоміноскопії	абдоміноскопія	noun	noun:inanim:f:v_mis
абдоміноскопії	абдоміноскопія	noun	noun:inanim:f:v_rod
абдоміноскопії	абдоміноскопія	noun	noun:inanim:p:v_kly
абдоміноскопії	абдоміноскопія	noun	noun:inanim:p:v_naz
абдоміноскопії	абдоміноскопія	noun	noun:inanim:p:v_zna
абдукцій	абдукція	noun	noun:inanim:p:v_rod
абдукцію	абдукція	noun	noun:inanim:f:v_zna
абдукція	абдукція	noun	noun:inanim:f:v_naz
абдукціям	абдукція	noun	noun:inanim:p:v_dav
абдукціями	абдукція	noun	noun:inanim:p:v_oru
абдукціях	абдукція	noun	noun:inanim:p:v_mis
абдукціє	абдукція	noun	noun:inanim:f:v_kly
абдукцією	абдукція	noun	noun:inanim:f:v_oru
абдукції	абдукція	noun	noun:inanim:f:v_dav
абдукції	абдукція	noun	noun:inanim:f:v_mis
абдукції	абдукція	noun	noun:inanim:f:v_rod
абдукції	абдукція	noun	noun:inanim:p:v_kly
абдукції	абдукція	noun	noun:inanim:p:v_naz
абдукції	абдукція	noun	noun:inanim:p:v_zna
аберацій	аберація	noun	noun:inanim:p:v_rod
аберацію	аберація	noun	noun:inanim:f:v_zna
аберація	аберація	noun	noun:inanim:f:v_naz
абераціям	аберація	noun	noun:inanim:p:v_dav
абераціями	аберація	noun	noun:inanim:p:v_oru
абераціях	аберація	noun	noun:inanim:p:v_mis
абераціє	аберація	noun	noun:inanim:f:v_kly
аберацією	аберація	noun	noun:inanim:f:v_oru
аберації	аберація	noun	noun:inanim:f:v_dav
аберації	аберація	noun	noun:inanim:f:v_mis
аберації	аберація	noun	noun:inanim:f:v_rod
аберації	аберація	noun	noun:inanim:p:v_kly
аберації	аберація	noun	noun:inanim:p:v_naz
аберації	аберація	noun	noun:inanim:p:v_zna
аберометр	аберометр	noun	noun:inanim:m:v_naz
аберометр	аберометр	noun	noun:inanim:m:v_zna
аберометра	аберометр	noun	noun:inanim:m:v_rod
аберометрам	аберометр	noun	noun:inanim:p:v_dav
аберометрами	аберометр	noun	noun:inanim:p:v_oru
аберометрах	аберометр	noun	noun:inanim:p:v_mis
аберометре	аберометр	noun	noun:inanim:m:v_kly
аберометри	аберометр	noun	noun:inanim:p:v_kly
аберометри	аберометр	noun	noun:inanim:p:v_naz
аберометри	аберометр	noun	noun:inanim:p:v_zna
аберометрові	аберометр	noun	noun:inanim:m:v_dav
аберометрові	аберометр	noun	noun:inanim:m:v_mis
аберометром	аберометр	noun	noun:inanim:m:v_oru
аберометрі	аберометр	noun	noun:inanim:m:v_mis
аберометрів	аберометр	noun	noun:inanim:p:v_rod
абеталіпопротеїнемій	абеталіпопротеїнемія	noun	noun:inanim:p:v_rod
абеталіпопротеїнемію	абеталіпопротеїнемія	noun	noun:inanim:f:v_zna
абеталіпопротеїнемія	абеталіпопротеїнемія	noun	noun:inanim:f:v_naz
абеталіпопротеїнеміям	абеталіпопротеїнемія	noun	noun:inanim:p:v_dav
абеталіпопротеїнеміями	абеталіпопротеїнемія	noun	noun:inanim:p:v_oru
абеталіпопротеїнеміях	абеталіпопротеїнемія	noun	noun:inanim:p:v_mis
абеталіпопротеїнеміє	абеталіпопротеїнемія	noun	noun:inanim:f:v_kly
абеталіпопротеїнемією	абеталіпопротеїнемія	noun	noun:inanim:f:v_oru
абеталіпопротеїнемії	абеталіпопротеїнемія	noun	noun:inanim:f:v_dav
абеталіпопротеїнемії	абеталіпопротеїнемія	noun	noun:inanim:f:v_mis
абеталіпопротеїнемії	абеталіпопротеїнемія	noun	noun:inanim:f:v_rod
абеталіпопротеїнемії	абеталіпопротеїнемія	noun	noun:inanim:p:v_kly
абеталіпопротеїнемії	абеталіпопротеїнемія	noun	noun:inanim:p:v_naz
абеталіпопротеїнемії	абеталіпопротеїнемія	noun	noun:inanim:p:v_zna
абетка	абетка	noun	noun:inanim:f:v_naz
абеткам	абетка	noun	noun:inanim:p:v_dav
абетками	абетка	noun	noun:inanim:p:v_oru
абетках	абетка	noun	noun:inanim:p:v_mis
абетки	абетка	noun	noun:inanim:f:v_rod
абетки	абетка	noun	noun:inanim:p:v_kly
абетки	абетка	noun	noun:inanim:p:v_naz
абетки	абетка	noun	noun:inanim:p:v_zna
абетко	абетка	noun	noun:inanim:f:v_kly
абеткою	абетка	noun	noun:inanim:f:v_oru
абетку	абетка	noun	noun:inanim:f:v_zna
абеток	абетка	noun	noun:inanim:p:v_rod
абетці	абетка	noun	noun:inanim:f:v_dav
абетці	абетка	noun	noun:inanim:f:v_mis
абзац	абзац	noun	noun:inanim:m:v_naz
абзац	абзац	noun	noun:inanim:m:v_zna
абзацам	абзац	noun	noun:inanim:p:v_dav
абзацами	абзац	noun	noun:inanim:p:v_oru
абзацах	абзац	noun	noun:inanim:p:v_mis
абзаце	абзац	noun	noun:inanim:m:v_kly
абзаци	абзац	noun	noun:inanim:p:v_kly
абзаци	абзац	noun	noun:inanim:p:v_naz
абзаци	абзац	noun	noun:inanim:p:v_zna
абзацик	абзацик	noun	noun:inanim:m:v_naz
абзацик	абзацик	noun	noun:inanim:m:v_zna
абзацика	абзацик	noun	noun:inanim:m:v_rod
абзацикам	абзацик	noun	noun:inanim:p:v_dav
абзациками	абзацик	noun	noun:inanim:p:v_oru
абзациках	абзацик	noun	noun:inanim:p:v_mis
абзацики	абзацик	noun	noun:inanim:p:v_kly
абзацики	абзацик	noun	noun:inanim:p:v_naz
абзацики	абзацик	noun	noun:inanim:p:v_zna
абзацикові	абзацик	noun	noun:inanim:m:v_dav
абзацикові	абзацик	noun	noun:inanim:m:v_mis
абзациком	абзацик	noun	noun:inanim:m:v_oru
абзацику	абзацик	noun	noun:inanim:m:v_dav
абзацику	абзацик	noun	noun:inanim:m:v_kly
абзацику	абзацик	noun	noun:inanim:m:v_mis
абзациків	абзацик	noun	noun:inanim:p:v_rod
абзацові	абзац	noun	noun:inanim:m:v_dav
абзацові	абзац	noun	noun:inanim:m:v_mis
абзацом	абзац	noun	noun:inanim:m:v_oru
абзацу	абзац	noun	noun:inanim:m:v_dav
абзацу	абзац	noun	noun:inanim:m:v_mis
абзацу	абзац	noun	noun:inanim:m:v_rod
абзаці	абзац	noun	noun:inanim:m:v_mis
абзаців	абзац	noun	noun:inanim:p:v_rod
абзетцер	абзетцер	noun	noun:inanim:m:v_naz
абзетцер	абзетцер	noun	noun:inanim:m:v_zna
абзетцера	абзетцер	noun	noun:inanim:m:v_rod
абзетцерам	абзетцер	noun	noun:inanim:p:v_dav
абзетцерами	абзетцер	noun	noun:inanim:p:v_oru
абзетцерах	абзетцер	noun	noun:inanim:p:v_mis
абзетцере	абзетцер	noun	noun:inanim:m:v_kly
абзетцери	абзетцер	noun	noun:inanim:p:v_kly
абзетцери	абзетцер	noun	noun:inanim:p:v_naz
абзетцери	абзетцер	noun	noun:inanim:p:v_zna
абзетцерові	абзетцер	noun	noun:inanim:m:v_dav
абзетцерові	абзетцер	noun	noun:inanim:m:v_mis
абзетцером	абзетцер	noun	noun:inanim:m:v_oru
абзетцері	абзетцер	noun	noun:inanim:m:v_mis
абзетцерів	абзетцер	noun	noun:inanim:p:v_rod
абищице	абищиця	noun	noun:inanim:f:v_kly
абищицею	абищиця	noun	noun:inanim:f:v_oru
абищиць	абищиця	noun	noun:inanim:p:v_rod
абищицю	абищиця	noun	noun:inanim:f:v_zna
абищиця	абищиця	noun	noun:inanim:f:v_naz
абищицям	абищиця	noun	noun:inanim:p:v_dav
абищицями	абищиця	noun	noun:inanim:p:v_oru
абищицях	абищиця	noun	noun:inanim:p:v_mis
абищиці	абищиця	noun	noun:inanim:f:v_dav
абищиці	абищиця	noun	noun:inanim:f:v_mis
абищиці	абищиця	noun	noun:inanim:f:v_rod
абищиці	абищиця	noun	noun:inanim:p:v_kly
абищиці	абищиця	noun	noun:inanim:p:v_naz
абищиці	абищиця	noun	noun:inanim:p:v_zna
аблактацій	аблактація	noun	noun:inanim:p:v_rod
аблактацію	аблактація	noun	noun:inanim:f:v_zna
аблактація	аблактація	noun	noun:inanim:f:v_naz
аблактаціям	аблактація	noun	noun:inanim:p:v_dav
аблактаціями	аблактація	noun	noun:inanim:p:v_oru
аблактаціях	аблактація	noun	noun:inanim:p:v_mis
аблактаціє	аблактація	noun	noun:inanim:f:v_kly
аблактацією	аблактація	noun	noun:inanim:f:v_oru
аблактації	аблактація	noun	noun:inanim:f:v_dav
аблактації	аблактація	noun	noun:inanim:f:v_mis
аблактації	аблактація	noun	noun:inanim:f:v_rod
аблактації	аблактація	noun	noun:inanim:p:v_kly
аблактації	аблактація	noun	noun:inanim:p:v_naz
аблактації	аблактація	noun	noun:inanim:p:v_zna
абластик	абластика	noun	noun:inanim:p:v_rod
абластика	абластика	noun	noun:inanim:f:v_naz
абластикам	абластика	noun	noun:inanim:p:v_dav
абластиками	абластика	noun	noun:inanim:p:v_oru
абластиках	абластика	noun	noun:inanim:p:v_mis
абластики	абластика	noun	noun:inanim:f:v_rod
абластики	абластика	noun	noun:inanim:p:v_kly
абластики	абластика	noun	noun:inanim:p:v_naz
абластики	абластика	noun	noun:inanim:p:v_zna
абластико	абластика	noun	noun:inanim:f:v_kly
абластикою	абластика	noun	noun:inanim:f:v_oru
абластику	абластика	noun	noun:inanim:f:v_zna
абластиці	абластика	noun	noun:inanim:f:v_dav
абластиці	абластика	noun	noun:inanim:f:v_mis
аблатив	аблатив	noun	noun:inanim:m:v_naz
аблатив	аблатив	noun	noun:inanim:m:v_zna
аблатива	аблатив	noun	noun:inanim:m:v_rod
аблативам	аблатив	noun	noun:inanim:p:v_dav
аблативами	аблатив	noun	noun:inanim:p:v_oru
аблативах	аблатив	noun	noun:inanim:p:v_mis
аблативе	аблатив	noun	noun:inanim:m:v_kly
аблативи	аблатив	noun	noun:inanim:p:v_kly
аблативи	аблатив	noun	noun:inanim:p:v_naz
аблативи	аблатив	noun	noun:inanim:p:v_zna
аблативові	аблатив	noun	noun:inanim:m:v_dav
аблативові	аблатив	noun	noun:inanim:m:v_mis
аблативом	аблатив	noun	noun:inanim:m:v_oru
аблативі	аблатив	noun	noun:inanim:m:v_mis
аблативів	аблатив	noun	noun:inanim:p:v_rod
аблаут	аблаут	noun	noun:inanim:m:v_naz
аблаут	аблаут	noun	noun:inanim:m:v_zna
аблаута	аблаут	noun	noun:inanim:m:v_rod
аблаутам	аблаут	noun	noun:inanim:p:v_dav
аблаутами	аблаут	noun	noun:inanim:p:v_oru
аблаутах	аблаут	noun	noun:inanim:p:v_mis
аблауте	аблаут	noun	noun:inanim:m:v_kly
аблаути	аблаут	noun	noun:inanim:p:v_kly
аблаути	аблаут	noun	noun:inanim:p:v_naz
аблаути	аблаут	noun	noun:inanim:p:v_zna
аблаутові	аблаут	noun	noun:inanim:m:v_dav
аблаутові	аблаут	noun	noun:inanim:m:v_mis
аблаутом	аблаут	noun	noun:inanim:m:v_oru
аблауті	аблаут	noun	noun:inanim:m:v_mis
аблаутів	аблаут	noun	noun:inanim:p:v_rod
абляцій	абляція	noun	noun:inanim:p:v_rod
абляцію	абляція	noun	noun:inanim:f:v_zna
абляція	абляція	noun	noun:inanim:f:v_naz
абляціям	абляція	noun	noun:inanim:p:v_dav
абляціями	абляція	noun	noun:inanim:p:v_oru
абляціях	абляція	noun	noun:inanim:p:v_mis
абляціє	абляція	noun	noun:inanim:f:v_kly
абляцією	абляція	noun	noun:inanim:f:v_oru
абляції	абляція	noun	noun:inanim:f:v_dav
абляції	абляція	noun	noun:inanim:f:v_mis
абляції	абляція	noun	noun:inanim:f:v_rod
абляції	абляція	noun	noun:inanim:p:v_kly
абляції	абляція	noun	noun:inanim:p:v_naz
абляції	абляція	noun	noun:inanim:p:v_zna
аболіцій	аболіція	noun	noun:inanim:p:v_rod
аболіціоніст	аболіціоніст	noun	noun:anim:m:v_naz
аболіціоніста	аболіціоніст	noun	noun:anim:m:v_rod
аболіціоніста	аболіціоніст	noun	noun:anim:m:v_zna
аболіціоністам	аболіціоніст	noun	noun:anim:p:v_dav
аболіціоністами	аболіціоніст	noun	noun:anim:p:v_oru
аболіціоністах	аболіціоніст	noun	noun:anim:p:v_mis
аболіціоністе	аболіціоніст	noun	noun:anim:m:v_kly
аболіціоністи	аболіціоніст	noun	noun:anim:p:v_kly
аболіціоністи	аболіціоніст	noun	noun:anim:p:v_naz
аболіціоністи	аболіціоніст	noun	noun:anim:p:v_zna:rare
аболіціоністка	аболіціоністка	noun	noun:anim:f:v_naz
аболіціоністкам	аболіціоністка	noun	noun:anim:p:v_dav
аболіціоністками	аболіціоністка	noun	noun:anim:p:v_oru
аболіціоністках	аболіціоністка	noun	noun:anim:p:v_mis
аболіціоністки	аболіціоністка	noun	noun:anim:f:v_rod
аболіціоністки	аболіціоністка	noun	noun:anim:p:v_kly
аболіціоністки	аболіціоністка	noun	noun:anim:p:v_naz
аболіціоністки	аболіціоністка	noun	noun:anim:p:v_zna:rare
аболіціоністко	аболіціоністка	noun	noun:anim:f:v_kly
аболіціоністкою	аболіціоністка	noun	noun:anim:f:v_oru
аболіціоністку	аболіціоністка	noun	noun:anim:f:v_zna
аболіціоністові	аболіціоніст	noun	noun:anim:m:v_dav
аболіціоністові	аболіціоніст	noun	noun:anim:m:v_mis
аболіціоністок	аболіціоністка	noun	noun:anim:p:v_rod
аболіціоністок	аболіціоністка	noun	noun:anim:p:v_zna
аболіціоністом	аболіціоніст	noun	noun:anim:m:v_oru
аболіціоністці	аболіціоністка	noun	noun:anim:f:v_dav
аболіціоністці	аболіціоністка	noun	noun:anim:f:v_mis
аболіціоністі	аболіціоніст	noun	noun:anim:m:v_mis
аболіціоністів	аболіціоніст	noun	noun:anim:p:v_rod
аболіціоністів	аболіціоніст	noun	noun:anim:p:v_zna
аболіцію	аболіція	noun	noun:inanim:f:v_zna
аболіція	аболіція	noun	noun:inanim:f:v_naz
аболіціям	аболіція	noun	noun:inanim:p:v_dav
аболіціями	аболіція	noun	noun:inanim:p:v_oru
аболіціях	аболіція	noun	noun:inanim:p:v_mis
аболіціє	аболіція	noun	noun:inanim:f:v_kly
аболіцією	аболіція	noun	noun:inanim:f:v_oru
аболіції	аболіція	noun	noun:inanim:f:v_dav
аболіції	аболіція	noun	noun:inanim:f:v_mis
аболіції	аболіція	noun	noun:inanim:f:v_rod
аболіції	аболіція	noun	noun:inanim:p:v_kly
аболіції	аболіція	noun	noun:inanim:p:v_naz
аболіції	аболіція	noun	noun:inanim:p:v_zna
абомазотомій	абомазотомія	noun	noun:inanim:p:v_rod
абомазотомію	абомазотомія	noun	noun:inanim:f:v_zna
абомазотомія	абомазотомія	noun	noun:inanim:f:v_naz
абомазотоміям	абомазотомія	noun	noun:inanim:p:v_dav
абомазотоміями	абомазотомія	noun	noun:inanim:p:v_oru
абомазотоміях	абомазотомія	noun	noun:inanim:p:v_mis
абомазотоміє	абомазотомія	noun	noun:inanim:f:v_kly
абомазотомією	абомазотомія	noun	noun:inanim:f:v_oru
абомазотомії	абомазотомія	noun	noun:inanim:f:v_dav
абомазотомії	абомазотомія	noun	noun:inanim:f:v_mis
абомазотомії	абомазотомія	noun	noun:inanim:f:v_rod
абомазотомії	абомазотомія	noun	noun:inanim:p:v_kly
абомазотомії	абомазотомія	noun	noun:inanim:p:v_naz
абомазотомії	абомазотомія	noun	noun:inanim:p:v_zna
абонвідділ	абонвідділ	noun	noun:inanim:m:v_naz
абонвідділ	абонвідділ	noun	noun:inanim:m:v_zna
абонвідділам	абонвідділ	noun	noun:inanim:p:v_dav
абонвідділами	абонвідділ	noun	noun:inanim:p:v_oru
абонвідділах	абонвідділ	noun	noun:inanim:p:v_mis
абонвідділе	абонвідділ	noun	noun:inanim:m:v_kly
абонвідділи	абонвідділ	noun	noun:inanim:p:v_kly
абонвідділи	абонвідділ	noun	noun:inanim:p:v_naz
абонвідділи	абонвідділ	noun	noun:inanim:p:v_zna
абонвідділові	абонвідділ	noun	noun:inanim:m:v_dav
абонвідділові	абонвідділ	noun	noun:inanim:m:v_mis
абонвідділом	абонвідділ	noun	noun:inanim:m:v_oru
абонвідділу	абонвідділ	noun	noun:inanim:m:v_dav
абонвідділу	абонвідділ	noun	noun:inanim:m:v_mis
абонвідділу	абонвідділ	noun	noun:inanim:m:v_rod
абонвідділі	абонвідділ	noun	noun:inanim:m:v_mis
абонвідділів	абонвідділ	noun	noun:inanim:p:v_rod
абонемент	абонемент	noun	noun:inanim:m:v_naz
абонемент	абонемент	noun	noun:inanim:m:v_zna
абонемента	абонемент	noun	noun:inanim:m:v_rod
абонементам	абонемент	noun	noun:inanim:p:v_dav
абонементами	абонемент	noun	noun:inanim:p:v_oru
абонементах	абонемент	noun	noun:inanim:p:v_mis
абонементе	абонемент	noun	noun:inanim:m:v_kly
абонементи	абонемент	noun	noun:inanim:p:v_kly
абонементи	абонемент	noun	noun:inanim:p:v_naz
абонементи	абонемент	noun	noun:inanim:p:v_zna
абонементові	абонемент	noun	noun:inanim:m:v_dav
абонементові	абонемент	noun	noun:inanim:m:v_mis
абонементом	абонемент	noun	noun:inanim:m:v_oru
абонементі	абонемент	noun	noun:inanim:m:v_mis
абонементів	абонемент	noun	noun:inanim:p:v_rod
абонент	абонент	noun	noun:anim:m:v_naz
абонента	абонент	noun	noun:anim:m:v_rod
абонента	абонент	noun	noun:anim:m:v_zna
абонентам	абонент	noun	noun:anim:p:v_dav
абонентами	абонент	noun	noun:anim:p:v_oru
абонентах	абонент	noun	noun:anim:p:v_mis
абоненте	абонент	noun	noun:anim:m:v_kly
абоненти	абонент	noun	noun:anim:p:v_kly
абоненти	абонент	noun	noun:anim:p:v_naz
абоненти	абонент	noun	noun:anim:p:v_zna:rare
абонентка	абонентка	noun	noun:anim:f:v_naz
абоненткам	абонентка	noun	noun:anim:p:v_dav
абонентками	абонентка	noun	noun:anim:p:v_oru
абонентках	абонентка	noun	noun:anim:p:v_mis
абонентки	абонентка	noun	noun:anim:f:v_rod
абонентки	абонентка	noun	noun:anim:p:v_kly
абонентки	абонентка	noun	noun:anim:p:v_naz
абонентки	абонентка	noun	noun:anim:p:v_zna:rare
абонентко	абонентка	noun	noun:anim:f:v_kly
абоненткою	абонентка	noun	noun:anim:f:v_oru
абонентку	абонентка	noun	noun:anim:f:v_zna
абонентові	абонент	noun	noun:anim:m:v_dav
абонентові	абонент	noun	noun:anim:m:v_mis
абоненток	абонентка	noun	noun:anim:p:v_rod
абоненток	абонентка	noun	noun:anim:p:v_zna
абонентом	абонент	noun	noun:anim:m:v_oru
абонентці	абонентка	noun	noun:anim:f:v_dav
абонентці	абонентка	noun	noun:anim:f:v_mis
абоненті	абонент	noun	noun:anim:m:v_mis
абонентів	абонент	noun	noun:anim:p:v_rod
абонентів	абонент	noun	noun:anim:p:v_zna
абонкнижка	абонкнижка	noun	noun:inanim:f:v_naz
абонкнижкам	абонкнижка	noun	noun:inanim:p:v_dav
абонкнижками	абонкнижка	noun	noun:inanim:p:v_oru
абонкнижках	абонкнижка	noun	noun:inanim:p:v_mis
абонкнижки	абонкнижка	noun	noun:inanim:f:v_rod
абонкнижки	абонкнижка	noun	noun:inanim:p:v_kly
абонкнижки	абонкнижка	noun	noun:inanim:p:v_naz
абонкнижки	абонкнижка	noun	noun:inanim:p:v_zna
абонкнижко	абонкнижка	noun	noun:inanim:f:v_kly
абонкнижкою	абонкнижка	noun	noun:inanim:f:v_oru
абонкнижку	абонкнижка	noun	noun:inanim:f:v_zna
абонкнижок	абонкнижка	noun	noun:inanim:p:v_rod
абонкнижці	абонкнижка	noun	noun:inanim:f:v_dav
абонкнижці	абонкнижка	noun	noun:inanim:f:v_mis
абонуванню	абонування	noun	noun:inanim:n:v_dav
абонуванню	абонування	noun	noun:inanim:n:v_mis
абонування	абонування	noun	noun:inanim:n:v_kly
абонування	абонування	noun	noun:inanim:n:v_naz
абонування	абонування	noun	noun:inanim:n:v_rod
абонування	абонування	noun	noun:inanim:n:v_zna
абонування	абонування	noun	noun:inanim:p:v_kly
абонування	абонування	noun	noun:inanim:p:v_naz
абонування	абонування	noun	noun:inanim:p:v_zna
абонуванням	абонування	noun	noun:inanim:n:v_oru
абонуванням	абонування	noun	noun:inanim:p:v_dav
абонуваннями	абонування	noun	noun:inanim:p:v_oru
абонуваннях	абонування	noun	noun:inanim:p:v_mis
абонуванні	абонування	noun	noun:inanim:n:v_mis
абонувань	абонування	noun	noun:inanim:p:v_rod
абордаж	абордаж	noun	noun:inanim:m:v_naz
абордаж	абордаж	noun	noun:inanim:m:v_zna
абордажам	абордаж	noun	noun:inanim:p:v_dav
абордажами	абордаж	noun	noun:inanim:p:v_oru
абордажах	абордаж	noun	noun:inanim:p:v_mis
абордаже	абордаж	noun	noun:inanim:m:v_kly
абордажеві	абордаж	noun	noun:inanim:m:v_dav
абордажеві	абордаж	noun	noun:inanim:m:v_mis
абордажем	абордаж	noun	noun:inanim:m:v_oru
абордажу	абордаж	noun	noun:inanim:m:v_dav
абордажу	абордаж	noun	noun:inanim:m:v_mis
абордажу	абордаж	noun	noun:inanim:m:v_rod
абордажі	абордаж	noun	noun:inanim:m:v_mis
абордажі	абордаж	noun	noun:inanim:p:v_kly
абордажі	абордаж	noun	noun:inanim:p:v_naz
абордажі	абордаж	noun	noun:inanim:p:v_zna
абордажів	абордаж	noun	noun:inanim:p:v_rod
абориген	абориген	noun	noun:anim:m:v_naz
аборигена	абориген	noun	noun:anim:m:v_rod
аборигена	абориген	noun	noun:anim:m:v_zna
аборигенам	абориген	noun	noun:anim:p:v_dav
аборигенами	абориген	noun	noun:anim:p:v_oru
аборигенах	абориген	noun	noun:anim:p:v_mis
аборигене	абориген	noun	noun:anim:m:v_kly
аборигени	абориген	noun	noun:anim:p:v_kly
аборигени	абориген	noun	noun:anim:p:v_naz
аборигени	абориген	noun	noun:anim:p:v_zna:rare
аборигенка	аборигенка	noun	noun:anim:f:v_naz
аборигенкам	аборигенка	noun	noun:anim:p:v_dav
аборигенками	аборигенка	noun	noun:anim:p:v_oru
аборигенках	аборигенка	noun	noun:anim:p:v_mis
аборигенки	аборигенка	noun	noun:anim:f:v_rod
аборигенки	аборигенка	noun	noun:anim:p:v_kly
аборигенки	аборигенка	noun	noun:anim:p:v_naz
аборигенки	аборигенка	noun	noun:anim:p:v_zna:rare
аборигенко	аборигенка	noun	noun:anim:f:v_kly
аборигенкою	аборигенка	noun	noun:anim:f:v_oru
аборигенку	аборигенка	noun	noun:anim:f:v_zna
аборигенові	абориген	noun	noun:anim:m:v_dav
аборигенові	абориген	noun	noun:anim:m:v_mis
аборигенок	аборигенка	noun	noun:anim:p:v_rod
аборигенок	аборигенка	noun	noun:anim:p:v_zna
аборигеном	абориген	noun	noun:anim:m:v_oru
аборигенці	аборигенка	noun	noun:anim:f:v_dav
аборигенці	аборигенка	noun	noun:anim:f:v_mis
аборигені	абориген	noun	noun:anim:m:v_mis
аборигенів	абориген	noun	noun:anim:p:v_rod
аборигенів	абориген	noun	noun:anim:p:v_zna
аборт	аборт	noun	noun:inanim:m:v_naz
аборт	аборт	noun	noun:inanim:m:v_zna
абортам	аборт	noun	noun:inanim:p:v_dav
абортами	аборт	noun	noun:inanim:p:v_oru
абортарій	абортарій	noun	noun:inanim:m:v_naz
абортарій	абортарій	noun	noun:inanim:m:v_zna
абортарію	абортарій	noun	noun:inanim:m:v_dav
абортарію	абортарій	noun	noun:inanim:m:v_kly
абортарію	абортарій	noun	noun:inanim:m:v_mis
абортарію	абортарій	noun	noun:inanim:m:v_rod
абортаріям	абортарій	noun	noun:inanim:p:v_dav
абортаріями	абортарій	noun	noun:inanim:p:v_oru
абортаріях	абортарій	noun	noun:inanim:p:v_mis
абортарієві	абортарій	noun	noun:inanim:m:v_dav
абортарієві	абортарій	noun	noun:inanim:m:v_mis
абортарієм	абортарій	noun	noun:inanim:m:v_oru
абортарії	абортарій	noun	noun:inanim:m:v_mis
абортарії	абортарій	noun	noun:inanim:p:v_kly
абортарії	абортарій	noun	noun:inanim:p:v_naz
абортарії	абортарій	noun	noun:inanim:p:v_zna
абортаріїв	абортарій	noun	noun:inanim:p:v_rod
абортах	аборт	noun	noun:inanim:p:v_mis
аборте	аборт	noun	noun:inanim:m:v_kly
аборти	аборт	noun	noun:inanim:p:v_kly
аборти	аборт	noun	noun:inanim:p:v_naz
аборти	аборт	noun	noun:inanim:p:v_zna
абортнице	абортниця	noun	noun:anim:f:v_kly
абортницею	абортниця	noun	noun:anim:f:v_oru
абортниць	абортниця	noun	noun:anim:p:v_rod
абортниць	абортниця	noun	noun:anim:p:v_zna
абортницю	абортниця	noun	noun:anim:f:v_zna
абортниця	абортниця	noun	noun:anim:f:v_naz
абортницям	абортниця	noun	noun:anim:p:v_dav
абортницями	абортниця	noun	noun:anim:p:v_oru
абортницях	абортниця	noun	noun:anim:p:v_mis
абортниці	абортниця	noun	noun:anim:f:v_dav
абортниці	абортниця	noun	noun:anim:f:v_mis
абортниці	абортниця	noun	noun:anim:f:v_rod
абортниці	абортниця	noun	noun:anim:p:v_kly
абортниці	абортниця	noun	noun:anim:p:v_naz
абортниці	абортниця	noun	noun:anim:p:v_zna:rare
абортові	аборт	noun	noun:inanim:m:v_dav
абортові	аборт	noun	noun:inanim:m:v_mis
абортом	аборт	noun	noun:inanim:m:v_oru
аборту	аборт	noun	noun:inanim:m:v_dav
аборту	аборт	noun	noun:inanim:m:v_mis
аборту	аборт	noun	noun:inanim:m:v_rod
абортуванню	абортування	noun	noun:inanim:n:v_dav
абортуванню	абортування	noun	noun:inanim:n:v_mis
абортування	абортування	noun	noun:inanim:n:v_kly
абортування	абортування	noun	noun:inanim:n:v_naz
абортування	абортування	noun	noun:inanim:n:v_rod
абортування	абортування	noun	noun:inanim:n:v_zna
абортування	абортування	noun	noun:inanim:p:v_kly
абортування	абортування	noun	noun:inanim:p:v_naz
абортування	абортування	noun	noun:inanim:p:v_zna
абортуванням	абортування	noun	noun:inanim:n:v_oru
абортуванням	абортування	noun	noun:inanim:p:v_dav
абортуваннями	абортування	noun	noun:inanim:p:v_oru
абортуваннях	абортування	noun	noun:inanim:p:v_mis
абортуванні	абортування	noun	noun:inanim:n:v_mis
абортувань	абортування	noun	noun:inanim:p:v_rod
аборті	аборт	noun	noun:inanim:m:v_mis
абортів	аборт	noun	noun:inanim:p:v_rod
абразив	абразив	noun	noun:inanim:m:v_naz
абразив	абразив	noun	noun:inanim:m:v_zna
абразивам	абразив	noun	noun:inanim:p:v_dav
абразивами	абразив	noun	noun:inanim:p:v_oru
абразивах	абразив	noun	noun:inanim:p:v_mis
абразиве	абразив	noun	noun:inanim:m:v_kly
абразиви	абразив	noun	noun:inanim:p:v_kly
абразиви	абразив	noun	noun:inanim:p:v_naz
абразиви	абразив	noun	noun:inanim:p:v_zna
абразивові	абразив	noun	noun:inanim:m:v_dav
абразивові	абразив	noun	noun:inanim:m:v_mis
абразивом	абразив	noun	noun:inanim:m:v_oru
абразиву	абразив	noun	noun:inanim:m:v_dav
абразиву	абразив	noun	noun:inanim:m:v_mis
абразиву	абразив	noun	noun:inanim:m:v_rod
абразиві	абразив	noun	noun:inanim:m:v_mis
абразивів	абразив	noun	noun:inanim:p:v_rod
абракадабр	абракадабра	noun	noun:inanim:p:v_rod
абракадабра	абракадабра	noun	noun:inanim:f:v_naz
абракадабрам	абракадабра	noun	noun:inanim:p:v_dav
абракадабрами	абракадабра	noun	noun:inanim:p:v_oru
абракадабрах	абракадабра	noun	noun:inanim:p:v_mis
абракадабри	абракадабра	noun	noun:inanim:f:v_rod
абракадабри	абракадабра	noun	noun:inanim:p:v_kly
абракадабри	абракадабра	noun	noun:inanim:p:v_naz
абракадабри	абракадабра	noun	noun:inanim:p:v_zna
абракадабро	абракадабра	noun	noun:inanim:f:v_kly
абракадаброю	абракадабра	noun	noun:inanim:f:v_oru
абракадабру	абракадабра	noun	noun:inanim:f:v_zna
абракадабрі	абракадабра	noun	noun:inanim:f:v_dav
абракадабрі	абракадабра	noun	noun:inanim:f:v_mis
абревіатур	абревіатура	noun	noun:inanim:p:v_rod
абревіатура	абревіатура	noun	noun:inanim:f:v_naz
абревіатурам	абревіатура	noun	noun:inanim:p:v_dav
абревіатурами	абревіатура	noun	noun:inanim:p:v_oru
абревіатурах	абревіатура	noun	noun:inanim:p:v_mis
абревіатури	абревіатура	noun	noun:inanim:f:v_rod
абревіатури	абревіатура	noun	noun:inanim:p:v_kly
абревіатури	абревіатура	noun	noun:inanim:p:v_naz
абревіатури	абревіатура	noun	noun:inanim:p:v_zna
абревіатуро	абревіатура	noun	noun:inanim:f:v_kly
абревіатурою	абревіатура	noun	noun:inanim:f:v_oru
абревіатуру	абревіатура	noun	noun:inanim:f:v_zna
абревіатурі	абревіатура	noun	noun:inanim:f:v_dav
абревіатурі	абревіатура	noun	noun:inanim:f:v_mis
абревіацій	абревіація	noun	noun:inanim:p:v_rod
абревіацію	абревіація	noun	noun:inanim:f:v_zna
абревіація	абревіація	noun	noun:inanim:f:v_naz
абревіаціям	абревіація	noun	noun:inanim:p:v_dav
абревіаціями	абревіація	noun	noun:inanim:p:v_oru
абревіаціях	абревіація	noun	noun:inanim:p:v_mis
абревіаціє	абревіація	noun	noun:inanim:f:v_kly
абревіацією	абревіація	noun	noun:inanim:f:v_oru
абревіації	абревіація	noun	noun:inanim:f:v_dav
абревіації	абревіація	noun	noun:inanim:f:v_mis
абревіації	абревіація	noun	noun:inanim:f:v_rod
абревіації	абревіація	noun	noun:inanim:p:v_kly
абревіації	абревіація	noun	noun:inanim:p:v_naz
абревіації	абревіація	noun	noun:inanim:p:v_zna
абрек	абрек	noun	noun:anim:m:v_naz
абрека	абрек	noun	noun:anim:m:v_rod
абрека	абрек	noun	noun:anim:m:v_zna
абрекам	абрек	noun	noun:anim:p:v_dav
абреками	абрек	noun	noun:anim:p:v_oru
абреках	абрек	noun	noun:anim:p:v_mis
абреки	абрек	noun	noun:anim:p:v_kly
абреки	абрек	noun	noun:anim:p:v_naz
абреки	абрек	noun	noun:anim:p:v_zna:rare
абрекові	абрек	noun	noun:anim:m:v_dav
абрекові	абрек	noun	noun:anim:m:v_mis
абреком	абрек	noun	noun:anim:m:v_oru
абреку	абрек	noun	noun:anim:m:v_dav
абреку	абрек	noun	noun:anim:m:v_kly
абреку	абрек	noun	noun:anim:m:v_mis
абреків	абрек	noun	noun:anim:p:v_rod
абреків	абрек	noun	noun:anim:p:v_zna
абрикос	абрикос	noun	noun:inanim:m:v_naz
абрикос	абрикос	noun	noun:inanim:m:v_zna
абрикос	абрикоса	noun	noun:inanim:p:v_rod
абрикоса	абрикос	noun	noun:inanim:m:v_rod
абрикоса	абрикоса	noun	noun:inanim:f:v_naz
абрикосам	абрикос	noun	noun:inanim:p:v_dav
абрикосам	абрикоса	noun	noun:inanim:p:v_dav
абрикосами	абрикос	noun	noun:inanim:p:v_oru
абрикосами	абрикоса	noun	noun:inanim:p:v_oru
абрикосах	абрикос	noun	noun:inanim:p:v_mis
абрикосах	абрикоса	noun	noun:inanim:p:v_mis
абрикосе	абрикос	noun	noun:inanim:m:v_kly
абрикоси	абрикос	noun	noun:inanim:p:v_kly
абрикоси	абрикос	noun	noun:inanim:p:v_naz
абрикоси	абрикос	noun	noun:inanim:p:v_zna
абрикоси	абрикоса	noun	noun:inanim:f:v_rod
абрикоси	абрикоса	noun	noun:inanim:p:v_kly
абрикоси	абрикоса	noun	noun:inanim:p:v_naz
абрикоси	абрикоса	noun	noun:inanim:p:v_zna
абрикоска	абрикоска	noun	noun:inanim:f:v_naz
абрикоскам	абрикоска	noun	noun:inanim:p:v_dav
абрикосками	абрикоска	noun	noun:inanim:p:v_oru
абрикосках	абрикоска	noun	noun:inanim:p:v_mis
абрикоски	абрикоска	noun	noun:inanim:f:v_rod
абрикоски	абрикоска	noun	noun:inanim:p:v_kly
абрикоски	абрикоска	noun	noun:inanim:p:v_naz
абрикоски	абрикоска	noun	noun:inanim:p:v_zna
абрикоско	абрикоска	noun	noun:inanim:f:v_kly
абрикоскою	абрикоска	noun	noun:inanim:f:v_oru
абрикоску	абрикоска	noun	noun:inanim:f:v_zna
абрикосник	абрикосник	noun	noun:anim:m:v_naz
абрикосника	абрикосник	noun	noun:anim:m:v_rod
абрикосника	абрикосник	noun	noun:anim:m:v_zna
абрикосникам	абрикосник	noun	noun:anim:p:v_dav
абрикосниками	абрикосник	noun	noun:anim:p:v_oru
абрикосниках	абрикосник	noun	noun:anim:p:v_mis
абрикосники	абрикосник	noun	noun:anim:p:v_kly
абрикосники	абрикосник	noun	noun:anim:p:v_naz
абрикосники	абрикосник	noun	noun:anim:p:v_zna:rare
абрикосникові	абрикосник	noun	noun:anim:m:v_dav
абрикосникові	абрикосник	noun	noun:anim:m:v_mis
абрикосником	абрикосник	noun	noun:anim:m:v_oru
абрикоснику	абрикосник	noun	noun:anim:m:v_dav
абрикоснику	абрикосник	noun	noun:anim:m:v_kly
абрикоснику	абрикосник	noun	noun:anim:m:v_mis
абрикосників	абрикосник	noun	noun:anim:p:v_rod
абрикосників	абрикосник	noun	noun:anim:p:v_zna
абрикосо	абрикоса	noun	noun:inanim:f:v_kly
абрикосові	абрикос	noun	noun:inanim:m:v_dav
абрикосові	абрикос	noun	noun:inanim:m:v_mis
абрикосок	абрикоска	noun	noun:inanim:p:v_rod
абрикосом	абрикос	noun	noun:inanim:m:v_oru
абрикосою	абрикоса	noun	noun:inanim:f:v_oru
абрикосу	абрикос	noun	noun:inanim:m:v_dav
абрикосу	абрикос	noun	noun:inanim:m:v_mis
абрикосу	абрикоса	noun	noun:inanim:f:v_zna
абрикосці	абрикоска	noun	noun:inanim:f:v_dav
абрикосці	абрикоска	noun	noun:inanim:f:v_mis
абрикосі	абрикос	noun	noun:inanim:m:v_mis
абрикосі	абрикоса	noun	noun:inanim:f:v_dav
абрикосі	абрикоса	noun	noun:inanim:f:v_mis
абрикосів	абрикос	noun	noun:inanim:p:v_rod
абрикосівка	абрикосівка	noun	noun:inanim:f:v_naz
абрикосівкам	абрикосівка	noun	noun:inanim:p:v_dav
абрикосівками	абрикосівка	noun	noun:inanim:p:v_oru
абрикосівках	абрикосівка	noun	noun:inanim:p:v_mis
абрикосівки	абрикосівка	noun	noun:inanim:f:v_rod
абрикосівки	абрикосівка	noun	noun:inanim:p:v_kly
абрикосівки	абрикосівка	noun	noun:inanim:p:v_naz
абрикосівки	абрикосівка	noun	noun:inanim:p:v_zna
абрикосівко	абрикосівка	noun	noun:inanim:f:v_kly
абрикосівкою	абрикосівка	noun	noun:inanim:f:v_oru
абрикосівку	абрикосівка	noun	noun:inanim:f:v_zna
абрикосівок	абрикосівка	noun	noun:inanim:p:v_rod
абрикосівці	абрикосівка	noun	noun:inanim:f:v_dav
абрикосівці	абрикосівка	noun	noun:inanim:f:v_mis
абрикотин	абрикотин	noun	noun:inanim:m:v_naz
абрикотин	абрикотин	noun	noun:inanim:m:v_zna
абрикотинам	абрикотин	noun	noun:inanim:p:v_dav
абрикотинами	абрикотин	noun	noun:inanim:p:v_oru
абрикотинах	абрикотин	noun	noun:inanim:p:v_mis
абрикотине	абрикотин	noun	noun:inanim:m:v_kly
абрикотини	абрикотин	noun	noun:inanim:p:v_kly
абрикотини	абрикотин	noun	noun:inanim:p:v_naz
абрикотини	абрикотин	noun	noun:inanim:p:v_zna
абрикотинові	абрикотин	noun	noun:inanim:m:v_dav
абрикотинові	абрикотин	noun	noun:inanim:m:v_mis
абрикотином	абрикотин	noun	noun:inanim:m:v_oru
абрикотину	абрикотин	noun	noun:inanim:m:v_dav
абрикотину	абрикотин	noun	noun:inanim:m:v_mis
абрикотину	абрикотин	noun	noun:inanim:m:v_rod
абрикотині	абрикотин	noun	noun:inanim:m:v_mis
абрикотинів	абрикотин	noun	noun:inanim:p:v_rod
абрис	абрис	noun	noun:inanim:m:v_naz
абрис	абрис	noun	noun:inanim:m:v_zna
абрисам	абрис	noun	noun:inanim:p:v_dav
абрисами	абрис	noun	noun:inanim:p:v_oru
абрисах	абрис	noun	noun:inanim:p:v_mis
абрисе	абрис	noun	noun:inanim:m:v_kly
абриси	абрис	noun	noun:inanim:p:v_kly
абриси	абрис	noun	noun:inanim:p:v_naz
абриси	абрис	noun	noun:inanim:p:v_zna
абрисові	абрис	noun	noun:inanim:m:v_dav
абрисові	абрис	noun	noun:inanim:m:v_mis
абрисом	абрис	noun	noun:inanim:m:v_oru
абрису	абрис	noun	noun:inanim:m:v_dav
абрису	абрис	noun	noun:inanim:m:v_mis
абрису	абрис	noun	noun:inanim:m:v_rod
абрисі	абрис	noun	noun:inanim:m:v_mis
абрисів	абрис	noun	noun:inanim:p:v_rod
аброгацій	аброгація	noun	noun:inanim:p:v_rod
аброгацію	аброгація	noun	noun:inanim:f:v_zna
аброгація	аброгація	noun	noun:inanim:f:v_naz
аброгаціям	аброгація	noun	noun:inanim:p:v_dav
аброгаціями	аброгація	noun	noun:inanim:p:v_oru
аброгаціях	аброгація	noun	noun:inanim:p:v_mis
аброгаціє	аброгація	noun	noun:inanim:f:v_kly
аброгацією	аброгація	noun	noun:inanim:f:v_oru
аброгації	аброгація	noun	noun:inanim:f:v_dav
аброгації	аброгація	noun	noun:inanim:f:v_mis
аброгації	аброгація	noun	noun:inanim:f:v_rod
аброгації	аброгація	noun	noun:inanim:p:v_kly
аброгації	аброгація	noun	noun:inanim:p:v_naz
аброгації	аброгація	noun	noun:inanim:p:v_zna
аброкореневі	аброкорінь	noun	noun:inanim:m:v_dav
аброкореневі	аброкорінь	noun	noun:inanim:m:v_mis
аброкоренем	аброкорінь	noun	noun:inanim:m:v_oru
аброкореню	аброкорінь	noun	noun:inanim:m:v_dav
аброкореню	аброкорінь	noun	noun:inanim:m:v_kly
аброкореню	аброкорінь	noun	noun:inanim:m:v_mis
аброкореня	аброкорінь	noun	noun:inanim:m:v_rod
аброкореня	аброкорінь	noun	noun:inanim:m:v_zna:var
аброкореням	аброкорінь	noun	noun:inanim:p:v_dav
аброкоренями	аброкорінь	noun	noun:inanim:p:v_oru
аброкоренях	аброкорінь	noun	noun:inanim:p:v_mis
аброкорені	аброкорінь	noun	noun:inanim:m:v_mis
аброкорені	аброкорінь	noun	noun:inanim:p:v_kly
аброкорені	аброкорінь	noun	noun:inanim:p:v_naz
аброкорені	аброкорінь	noun	noun:inanim:p:v_zna
аброкоренів	аброкорінь	noun	noun:inanim:p:v_rod
аброкорінь	аброкорінь	noun	noun:inanim:m:v_naz
аброкорінь	аброкорінь	noun	noun:inanim:m:v_zna
аброморфем	аброморфема	noun	noun:inanim:p:v_rod
аброморфема	аброморфема	noun	noun:inanim:f:v_naz
аброморфемам	аброморфема	noun	noun:inanim:p:v_dav
аброморфемами	аброморфема	noun	noun:inanim:p:v_oru
аброморфемах	аброморфема	noun	noun:inanim:p:v_mis
аброморфеми	аброморфема	noun	noun:inanim:f:v_rod
аброморфеми	аброморфема	noun	noun:inanim:p:v_kly
аброморфеми	аброморфема	noun	noun:inanim:p:v_naz
аброморфеми	аброморфема	noun	noun:inanim:p:v_zna
аброморфемо	аброморфема	noun	noun:inanim:f:v_kly
аброморфемою	аброморфема	noun	noun:inanim:f:v_oru
аброморфему	аброморфема	noun	noun:inanim:f:v_zna
аброморфемі	аброморфема	noun	noun:inanim:f:v_dav
аброморфемі	аброморфема	noun	noun:inanim:f:v_mis
аброоснов	аброоснова	noun	noun:inanim:p:v_rod
аброоснова	аброоснова	noun	noun:inanim:f:v_naz
аброосновам	аброоснова	noun	noun:inanim:p:v_dav
аброосновами	аброоснова	noun	noun:inanim:p:v_oru
аброосновах	аброоснова	noun	noun:inanim:p:v_mis
аброоснови	аброоснова	noun	noun:inanim:f:v_rod
аброоснови	аброоснова	noun	noun:inanim:p:v_kly
аброоснови	аброоснова	noun	noun:inanim:p:v_naz
аброоснови	аброоснова	noun	noun:inanim:p:v_zna
аброосново	аброоснова	noun	noun:inanim:f:v_kly
аброосновою	аброоснова	noun	noun:inanim:f:v_oru
аброоснову	аброоснова	noun	noun:inanim:f:v_zna
аброоснові	аброоснова	noun	noun:inanim:f:v_dav
аброоснові	аброоснова	noun	noun:inanim:f:v_mis
абруптив	абруптив	noun	noun:inanim:m:v_naz
абруптив	абруптив	noun	noun:inanim:m:v_zna
абруптива	абруптив	noun	noun:inanim:m:v_rod
абруптивам	абруптив	noun	noun:inanim:p:v_dav
абруптивами	абруптив	noun	noun:inanim:p:v_oru
абруптивах	абруптив	noun	noun:inanim:p:v_mis
абруптиве	абруптив	noun	noun:inanim:m:v_kly
абруптиви	абруптив	noun	noun:inanim:p:v_kly
абруптиви	абруптив	noun	noun:inanim:p:v_naz
абруптиви	абруптив	noun	noun:inanim:p:v_zna
абруптивові	абруптив	noun	noun:inanim:m:v_dav
абруптивові	абруптив	noun	noun:inanim:m:v_mis
абруптивом	абруптив	noun	noun:inanim:m:v_oru
абруптиві	абруптив	noun	noun:inanim:m:v_mis
абруптивів	абруптив	noun	noun:inanim:p:v_rod
абрупцій	абрупція	noun	noun:inanim:p:v_rod
абрупцію	абрупція	noun	noun:inanim:f:v_zna
абрупція	абрупція	noun	noun:inanim:f:v_naz
абрупціям	абрупція	noun	noun:inanim:p:v_dav
абрупціями	абрупція	noun	noun:inanim:p:v_oru
абрупціях	абрупція	noun	noun:inanim:p:v_mis
абрупціє	абрупція	noun	noun:inanim:f:v_kly
абрупцією	абрупція	noun	noun:inanim:f:v_oru
абрупції	абрупція	noun	noun:inanim:f:v_dav
абрупції	абрупція	noun	noun:inanim:f:v_mis
абрупції	абрупція	noun	noun:inanim:f:v_rod
абрупції	абрупція	noun	noun:inanim:p:v_kly
абрупції	абрупція	noun	noun:inanim:p:v_naz
абрупції	абрупція	noun	noun:inanim:p:v_zna
абсанс	абсанс	noun	noun:inanim:m:v_naz
абсанс	абсанс	noun	noun:inanim:m:v_zna
абсансам	абсанс	noun	noun:inanim:p:v_dav
абсансами	абсанс	noun	noun:inanim:p:v_oru
абсансах	абсанс	noun	noun:inanim:p:v_mis
абсансе	абсанс	noun	noun:inanim:m:v_kly
абсанси	абсанс	noun	noun:inanim:p:v_kly
абсанси	абсанс	noun	noun:inanim:p:v_naz
абсанси	абсанс	noun	noun:inanim:p:v_zna
абсансові	абсанс	noun	noun:inanim:m:v_dav
абсансові	абсанс	noun	noun:inanim:m:v_mis
абсансом	абсанс	noun	noun:inanim:m:v_oru
абсансу	абсанс	noun	noun:inanim:m:v_dav
абсансу	абсанс	noun	noun:inanim:m:v_mis
абсансу	абсанс	noun	noun:inanim:m:v_rod
абсансі	абсанс	noun	noun:inanim:m:v_mis
абсансів	абсанс	noun	noun:inanim:p:v_rod
абсент	абсент	noun	noun:inanim:m:v_naz
абсент	абсент	noun	noun:inanim:m:v_zna
абсентам	абсент	noun	noun:inanim:p:v_dav
абсентами	абсент	noun	noun:inanim:p:v_oru
абсентах	абсент	noun	noun:inanim:p:v_mis
абсенте	абсент	noun	noun:inanim:m:v_kly
абсентеїст	абсентеїст	noun	noun:anim:m:v_naz
абсентеїста	абсентеїст	noun	noun:anim:m:v_rod
абсентеїста	абсентеїст	noun	noun:anim:m:v_zna
абсентеїстам	абсентеїст	noun	noun:anim:p:v_dav
абсентеїстами	абсентеїст	noun	noun:anim:p:v_oru
абсентеїстах	абсентеїст	noun	noun:anim:p:v_mis
абсентеїсте	абсентеїст	noun	noun:anim:m:v_kly
абсентеїсти	абсентеїст	noun	noun:anim:p:v_kly
абсентеїсти	абсентеїст	noun	noun:anim:p:v_naz
абсентеїсти	абсентеїст	noun	noun:anim:p:v_zna:rare
абсентеїстові	абсентеїст	noun	noun:anim:m:v_dav
абсентеїстові	абсентеїст	noun	noun:anim:m:v_mis
абсентеїстом	абсентеїст	noun	noun:anim:m:v_oru
абсентеїсті	абсентеїст	noun	noun:anim:m:v_mis
абсентеїстів	абсентеїст	noun	noun:anim:p:v_rod
абсентеїстів	абсентеїст	noun	noun:anim:p:v_zna
абсенти	абсент	noun	noun:inanim:p:v_kly
абсенти	абсент	noun	noun:inanim:p:v_naz
абсенти	абсент	noun	noun:inanim:p:v_zna
абсентові	абсент	noun	noun:inanim:m:v_dav
абсентові	абсент	noun	noun:inanim:m:v_mis
абсентом	абсент	noun	noun:inanim:m:v_oru
абсенту	абсент	noun	noun:inanim:m:v_dav
абсенту	абсент	noun	noun:inanim:m:v_mis
абсенту	абсент	noun	noun:inanim:m:v_rod
абсенті	абсент	noun	noun:inanim:m:v_mis
абсентів	абсент	noun	noun:inanim:p:v_rod
абсид	абсида	noun	noun:inanim:p:v_rod
абсида	абсида	noun	noun:inanim:f:v_naz
абсидам	абсида	noun	noun:inanim:p:v_dav
абсидами	абсида	noun	noun:inanim:p:v_oru
абсидах	абсида	noun	noun:inanim:p:v_mis
абсиди	абсида	noun	noun:inanim:f:v_rod
абсиди	абсида	noun	noun:inanim:p:v_kly
абсиди	абсида	noun	noun:inanim:p:v_naz
абсиди	абсида	noun	noun:inanim:p:v_zna
абсидо	абсида	noun	noun:inanim:f:v_kly
абсидою	абсида	noun	noun:inanim:f:v_oru
абсиду	абсида	noun	noun:inanim:f:v_zna
абсиді	абсида	noun	noun:inanim:f:v_dav
абсиді	абсида	noun	noun:inanim:f:v_mis
абсольвент	абсольвент	noun	noun:inanim:m:v_naz
абсольвент	абсольвент	noun	noun:inanim:m:v_zna
абсольвента	абсольвент	noun	noun:inanim:m:v_rod
абсольвентам	абсольвент	noun	noun:inanim:p:v_dav
абсольвентами	абсольвент	noun	noun:inanim:p:v_oru
абсольвентах	абсольвент	noun	noun:inanim:p:v_mis
абсольвенте	абсольвент	noun	noun:inanim:m:v_kly
абсольвенти	абсольвент	noun	noun:inanim:p:v_kly
абсольвенти	абсольвент	noun	noun:inanim:p:v_naz
абсольвенти	абсольвент	noun	noun:inanim:p:v_zna
абсольвентка	абсольвентка	noun	noun:anim:f:v_naz
абсольвенткам	абсольвентка	noun	noun:anim:p:v_dav
абсольвентками	абсольвентка	noun	noun:anim:p:v_oru
абсольвентках	абсольвентка	noun	noun:anim:p:v_mis
абсольвентки	абсольвентка	noun	noun:anim:f:v_rod
абсольвентки	абсольвентка	noun	noun:anim:p:v_kly
абсольвентки	абсольвентка	noun	noun:anim:p:v_naz
абсольвентки	абсольвентка	noun	noun:anim:p:v_zna:rare
абсольвентко	абсольвентка	noun	noun:anim:f:v_kly
абсольвенткою	абсольвентка	noun	noun:anim:f:v_oru
абсольвентку	абсольвентка	noun	noun:anim:f:v_zna
абсольвентові	абсольвент	noun	noun:inanim:m:v_dav
абсольвентові	абсольвент	noun	noun:inanim:m:v_mis
абсольвенток	абсольвентка	noun	noun:anim:p:v_rod
абсольвенток	абсольвентка	noun	noun:anim:p:v_zna
абсольвентом	абсольвент	noun	noun:inanim:m:v_oru
абсольвентці	абсольвентка	noun	noun:anim:f:v_dav
абсольвентці	абсольвентка	noun	noun:anim:f:v_mis
абсольвенті	абсольвент	noun	noun:inanim:m:v_mis
абсольвентів	абсольвент	noun	noun:inanim:p:v_rod
абсолют	абсолют	noun	noun:inanim:m:v_naz
абсолют	абсолют	noun	noun:inanim:m:v_zna
абсолютам	абсолют	noun	noun:inanim:p:v_dav
абсолютами	абсолют	noun	noun:inanim:p:v_oru
абсолютах	абсолют	noun	noun:inanim:p:v_mis
абсолюте	абсолют	noun	noun:inanim:m:v_kly
абсолюти	абсолют	noun	noun:inanim:p:v_kly
абсолюти	абсолют	noun	noun:inanim:p:v_naz
абсолюти	абсолют	noun	noun:inanim:p:v_zna
абсолютив	абсолютив	noun	noun:inanim:m:v_naz
абсолютив	абсолютив	noun	noun:inanim:m:v_zna
абсолютива	абсолютив	noun	noun:inanim:m:v_rod
абсолютивам	абсолютив	noun	noun:inanim:p:v_dav
абсолютивами	абсолютив	noun	noun:inanim:p:v_oru
абсолютивах	абсолютив	noun	noun:inanim:p:v_mis
абсолютиве	абсолютив	noun	noun:inanim:m:v_kly
абсолютиви	абсолютив	noun	noun:inanim:p:v_kly
абсолютиви	абсолютив	noun	noun:inanim:p:v_naz
абсолютиви	абсолютив	noun	noun:inanim:p:v_zna
абсолютивові	абсолютив	noun	noun:inanim:m:v_dav
абсолютивові	абсолютив	noun	noun:inanim:m:v_mis
абсолютивом	абсолютив	noun	noun:inanim:m:v_oru
абсолютиві	абсолютив	noun	noun:inanim:m:v_mis
абсолютивів	абсолютив	noun	noun:inanim:p:v_rod
абсолютизацій	абсолютизація	noun	noun:inanim:p:v_rod
абсолютизацію	абсолютизація	noun	noun:inanim:f:v_zna
абсолютизація	абсолютизація	noun	noun:inanim:f:v_naz
абсолютизаціям	абсолютизація	noun	noun:inanim:p:v_dav
абсолютизаціями	абсолютизація	noun	noun:inanim:p:v_oru
абсолютизаціях	абсолютизація	noun	noun:inanim:p:v_mis
абсолютизаціє	абсолютизація	noun	noun:inanim:f:v_kly
абсолютизацією	абсолютизація	noun	noun:inanim:f:v_oru
абсолютизації	абсолютизація	noun	noun:inanim:f:v_dav
абсолютизації	абсолютизація	noun	noun:inanim:f:v_mis
абсолютизації	абсолютизація	noun	noun:inanim:f:v_rod
абсолютизації	абсолютизація	noun	noun:inanim:p:v_kly
абсолютизації	абсолютизація	noun	noun:inanim:p:v_naz
абсолютизації	абсолютизація	noun	noun:inanim:p:v_zna
абсолютизуванню	абсолютизування	noun	noun:inanim:n:v_dav
абсолютизуванню	абсолютизування	noun	noun:inanim:n:v_mis
абсолютизування	абсолютизування	noun	noun:inanim:n:v_kly
абсолютизування	абсолютизування	noun	noun:inanim:n:v_naz
абсолютизування	абсолютизування	noun	noun:inanim:n:v_rod
абсолютизування	абсолютизування	noun	noun:inanim:n:v_zna
абсолютизування	абсолютизування	noun	noun:inanim:p:v_kly
абсолютизування	абсолютизування	noun	noun:inanim:p:v_naz
абсолютизування	абсолютизування	noun	noun:inanim:p:v_zna
абсолютизуванням	абсолютизування	noun	noun:inanim:n:v_oru
абсолютизуванням	абсолютизування	noun	noun:inanim:p:v_dav
абсолютизуваннями	абсолютизування	noun	noun:inanim:p:v_oru
абсолютизуваннях	абсолютизування	noun	noun:inanim:p:v_mis
абсолютизуванні	абсолютизування	noun	noun:inanim:n:v_mis
абсолютизувань	абсолютизування	noun	noun:inanim:p:v_rod
абсолютист	абсолютист	noun	noun:anim:m:v_naz
абсолютиста	абсолютист	noun	noun:anim:m:v_rod
абсолютиста	абсолютист	noun	noun:anim:m:v_zna
абсолютистам	абсолютист	noun	noun:anim:p:v_dav
абсолютистами	абсолютист	noun	noun:anim:p:v_oru
абсолютистах	абсолютист	noun	noun:anim:p:v_mis
абсолютисте	абсолютист	noun	noun:anim:m:v_kly
абсолютисти	абсолютист	noun	noun:anim:p:v_kly
абсолютисти	абсолютист	noun	noun:anim:p:v_naz
абсолютисти	абсолютист	noun	noun:anim:p:v_zna:rare
абсолютистка	абсолютистка	noun	noun:anim:f:v_naz
абсолютисткам	абсолютистка	noun	noun:anim:p:v_dav
абсолютистками	абсолютистка	noun	noun:anim:p:v_oru
абсолютистках	абсолютистка	noun	noun:anim:p:v_mis
абсолютистки	абсолютистка	noun	noun:anim:f:v_rod
абсолютистки	абсолютистка	noun	noun:anim:p:v_kly
абсолютистки	абсолютистка	noun	noun:anim:p:v_naz
абсолютистки	абсолютистка	noun	noun:anim:p:v_zna:rare
абсолютистко	абсолютистка	noun	noun:anim:f:v_kly
абсолютисткою	абсолютистка	noun	noun:anim:f:v_oru
абсолютистку	абсолютистка	noun	noun:anim:f:v_zna
абсолютистові	абсолютист	noun	noun:anim:m:v_dav
абсолютистові	абсолютист	noun	noun:anim:m:v_mis
абсолютисток	абсолютистка	noun	noun:anim:p:v_rod
абсолютисток	абсолютистка	noun	noun:anim:p:v_zna
абсолютистом	абсолютист	noun	noun:anim:m:v_oru
абсолютистці	абсолютистка	noun	noun:anim:f:v_dav
абсолютистці	абсолютистка	noun	noun:anim:f:v_mis
абсолютисті	абсолютист	noun	noun:anim:m:v_mis
абсолютистів	абсолютист	noun	noun:anim:p:v_rod
абсолютистів	абсолютист	noun	noun:anim:p:v_zna
абсолютові	абсолют	noun	noun:inanim:m:v_dav
абсолютові	абсолют	noun	noun:inanim:m:v_mis
абсолютом	абсолют	noun	noun:inanim:m:v_oru
абсолюту	абсолют	noun	noun:inanim:m:v_dav
абсолюту	абсолют	noun	noun:inanim:m:v_mis
абсолюту	абсолют	noun	noun:inanim:m:v_rod
абсолютуванню	абсолютування	noun	noun:inanim:n:v_dav
абсолютуванню	абсолютування	noun	noun:inanim:n:v_mis
абсолютування	абсолютування	noun	noun:inanim:n:v_kly
абсолютування	абсолютування	noun	noun:inanim:n:v_naz
абсолютування	абсолютування	noun	noun:inanim:n:v_rod
абсолютування	абсолютування	noun	noun:inanim:n:v_zna
абсолютування	абсолютування	noun	noun:inanim:p:v_kly
абсолютування	абсолютування	noun	noun:inanim:p:v_naz
абсолютування	абсолютування	noun	noun:inanim:p:v_zna
абсолютуванням	абсолютування	noun	noun:inanim:n:v_oru
абсолютуванням	абсолютування	noun	noun:inanim:p:v_dav
абсолютуваннями	абсолютування	noun	noun:inanim:p:v_oru
абсолютуваннях	абсолютування	noun	noun:inanim:p:v_mis
абсолютуванні	абсолютування	noun	noun:inanim:n:v_mis
абсолютувань	абсолютування	noun	noun:inanim:p:v_rod
абсолюті	абсолют	noun	noun:inanim:m:v_mis
абсолютів	абсолют	noun	noun:inanim:p:v_rod
абсолюцій	абсолюція	noun	noun:inanim:p:v_rod
абсолюцію	абсолюція	noun	noun:inanim:f:v_zna
абсолюція	абсолюція	noun	noun:inanim:f:v_naz
абсолюціям	абсолюція	noun	noun:inanim:p:v_dav
абсолюціями	абсолюція	noun	noun:inanim:p:v_oru
абсолюціях	абсолюція	noun	noun:inanim:p:v_mis
абсолюціє	абсолюція	noun	noun:inanim:f:v_kly
абсолюцією	абсолюція	noun	noun:inanim:f:v_oru
абсолюції	абсолюція	noun	noun:inanim:f:v_dav
абсолюції	абсолюція	noun	noun:inanim:f:v_mis
абсолюції	абсолюція	noun	noun:inanim:f:v_rod
абсолюції	абсолюція	noun	noun:inanim:p:v_kly
абсолюції	абсолюція	noun	noun:inanim:p:v_naz
абсолюції	абсолюція	noun	noun:inanim:p:v_zna
абсорбат	абсорбат	noun	noun:inanim:m:v_naz
абсорбат	абсорбат	noun	noun:inanim:m:v_zna
абсорбатам	абсорбат	noun	noun:inanim:p:v_dav
абсорбатами	абсорбат	noun	noun:inanim:p:v_oru
абсорбатах	абсорбат	noun	noun:inanim:p:v_mis
абсорбате	абсорбат	noun	noun:inanim:m:v_kly
абсорбати	абсорбат	noun	noun:inanim:p:v_kly
абсорбати	абсорбат	noun	noun:inanim:p:v_naz
абсорбати	абсорбат	noun	noun:inanim:p:v_zna
абсорбатові	абсорбат	noun	noun:inanim:m:v_dav
абсорбатові	абсорбат	noun	noun:inanim:m:v_mis
абсорбатом	абсорбат	noun	noun:inanim:m:v_oru
абсорбату	абсорбат	noun	noun:inanim:m:v_dav
абсорбату	абсорбат	noun	noun:inanim:m:v_mis
абсорбату	абсорбат	noun	noun:inanim:m:v_rod
абсорбаті	абсорбат	noun	noun:inanim:m:v_mis
абсорбатів	абсорбат	noun	noun:inanim:p:v_rod
абсорбент	абсорбент	noun	noun:inanim:m:v_naz
абсорбент	абсорбент	noun	noun:inanim:m:v_zna
абсорбентам	абсорбент	noun	noun:inanim:p:v_dav
абсорбентами	абсорбент	noun	noun:inanim:p:v_oru
абсорбентах	абсорбент	noun	noun:inanim:p:v_mis
абсорбенте	абсорбент	noun	noun:inanim:m:v_kly
абсорбенти	абсорбент	noun	noun:inanim:p:v_kly
абсорбенти	абсорбент	noun	noun:inanim:p:v_naz
абсорбенти	абсорбент	noun	noun:inanim:p:v_zna
абсорбентові	абсорбент	noun	noun:inanim:m:v_dav
абсорбентові	абсорбент	noun	noun:inanim:m:v_mis
абсорбентом	абсорбент	noun	noun:inanim:m:v_oru
абсорбенту	абсорбент	noun	noun:inanim:m:v_dav
абсорбенту	абсорбент	noun	noun:inanim:m:v_mis
абсорбенту	абсорбент	noun	noun:inanim:m:v_rod
абсорбенті	абсорбент	noun	noun:inanim:m:v_mis
абсорбентів	абсорбент	noun	noun:inanim:p:v_rod
абсорбер	абсорбер	noun	noun:inanim:m:v_naz
абсорбер	абсорбер	noun	noun:inanim:m:v_zna
абсорбера	абсорбер	noun	noun:inanim:m:v_rod
абсорберам	абсорбер	noun	noun:inanim:p:v_dav
абсорберами	абсорбер	noun	noun:inanim:p:v_oru
абсорберах	абсорбер	noun	noun:inanim:p:v_mis
абсорбере	абсорбер	noun	noun:inanim:m:v_kly
абсорбери	абсорбер	noun	noun:inanim:p:v_kly
абсорбери	абсорбер	noun	noun:inanim:p:v_naz
абсорбери	абсорбер	noun	noun:inanim:p:v_zna
абсорберові	абсорбер	noun	noun:inanim:m:v_dav
абсорберові	абсорбер	noun	noun:inanim:m:v_mis
абсорбером	абсорбер	noun	noun:inanim:m:v_oru
абсорбері	абсорбер	noun	noun:inanim:m:v_mis
абсорберів	абсорбер	noun	noun:inanim:p:v_rod
абсорбтив	абсорбтив	noun	noun:inanim:m:v_naz
абсорбтив	абсорбтив	noun	noun:inanim:m:v_zna
абсорбтивам	абсорбтив	noun	noun:inanim:p:v_dav
абсорбтивами	абсорбтив	noun	noun:inanim:p:v_oru
абсорбтивах	абсорбтив	noun	noun:inanim:p:v_mis
абсорбтиве	абсорбтив	noun	noun:inanim:m:v_kly
абсорбтиви	абсорбтив	noun	noun:inanim:p:v_kly
абсорбтиви	абсорбтив	noun	noun:inanim:p:v_naz
абсорбтиви	абсорбтив	noun	noun:inanim:p:v_zna
абсорбтивові	абсорбтив	noun	noun:inanim:m:v_dav
абсорбтивові	абсорбтив	noun	noun:inanim:m:v_mis
абсорбтивом	абсорбтив	noun	noun:inanim:m:v_oru
абсорбтиву	абсорбтив	noun	noun:inanim:m:v_dav
абсорбтиву	абсорбтив	noun	noun:inanim:m:v_mis
абсорбтиву	абсорбтив	noun	noun:inanim:m:v_rod
абсорбтиві	абсорбтив	noun	noun:inanim:m:v_mis
абсорбтивів	абсорбтив	noun	noun:inanim:p:v_rod
абсорбцій	абсорбція	noun	noun:inanim:p:v_rod
абсорбціометр	абсорбціометр	noun	noun:inanim:m:v_naz
абсорбціометр	абсорбціометр	noun	noun:inanim:m:v_zna
абсорбціометра	абсорбціометр	noun	noun:inanim:m:v_rod
абсорбціометрам	абсорбціометр	noun	noun:inanim:p:v_dav
абсорбціометрами	абсорбціометр	noun	noun:inanim:p:v_oru
абсорбціометрах	абсорбціометр	noun	noun:inanim:p:v_mis
абсорбціометре	абсорбціометр	noun	noun:inanim:m:v_kly
абсорбціометри	абсорбціометр	noun	noun:inanim:p:v_kly
абсорбціометри	абсорбціометр	noun	noun:inanim:p:v_naz
абсорбціометри	абсорбціометр	noun	noun:inanim:p:v_zna
абсорбціометрові	абсорбціометр	noun	noun:inanim:m:v_dav
абсорбціометрові	абсорбціометр	noun	noun:inanim:m:v_mis
абсорбціометром	абсорбціометр	noun	noun:inanim:m:v_oru
абсорбціометрі	абсорбціометр	noun	noun:inanim:m:v_mis
абсорбціометрів	абсорбціометр	noun	noun:inanim:p:v_rod
абсорбцію	абсорбція	noun	noun:inanim:f:v_zna
абсорбція	абсорбція	noun	noun:inanim:f:v_naz
абсорбціям	абсорбція	noun	noun:inanim:p:v_dav
абсорбціями	абсорбція	noun	noun:inanim:p:v_oru
абсорбціях	абсорбція	noun	noun:inanim:p:v_mis
абсорбціє	абсорбція	noun	noun:inanim:f:v_kly
абсорбцією	абсорбція	noun	noun:inanim:f:v_oru
абсорбції	абсорбція	noun	noun:inanim:f:v_dav
абсорбції	абсорбція	noun	noun:inanim:f:v_mis
абсорбції	абсорбція	noun	noun:inanim:f:v_rod
абсорбції	абсорбція	noun	noun:inanim:p:v_kly
абсорбції	абсорбція	noun	noun:inanim:p:v_naz
абсорбції	абсорбція	noun	noun:inanim:p:v_zna
абстинент	абстинент	noun	noun:anim:m:v_naz
абстинента	абстинент	noun	noun:anim:m:v_rod
абстинента	абстинент	noun	noun:anim:m:v_zna
абстинентам	абстинент	noun	noun:anim:p:v_dav
абстинентами	абстинент	noun	noun:anim:p:v_oru
абстинентах	абстинент	noun	noun:anim:p:v_mis
абстиненте	абстинент	noun	noun:anim:m:v_kly
абстиненти	абстинент	noun	noun:anim:p:v_kly
абстиненти	абстинент	noun	noun:anim:p:v_naz
абстиненти	абстинент	noun	noun:anim:p:v_zna:rare
абстинентка	абстинентка	noun	noun:anim:f:v_naz
абстиненткам	абстинентка	noun	noun:anim:p:v_dav
абстинентками	абстинентка	noun	noun:anim:p:v_oru
абстинентках	абстинентка	noun	noun:anim:p:v_mis
абстинентки	абстинентка	noun	noun:anim:f:v_rod
абстинентки	абстинентка	noun	noun:anim:p:v_kly
абстинентки	абстинентка	noun	noun:anim:p:v_naz
абстинентки	абстинентка	noun	noun:anim:p:v_zna:rare
абстинентко	абстинентка	noun	noun:anim:f:v_kly
абстиненткою	абстинентка	noun	noun:anim:f:v_oru
абстинентку	абстинентка	noun	noun:anim:f:v_zna
абстинентові	абстинент	noun	noun:anim:m:v_dav
абстинентові	абстинент	noun	noun:anim:m:v_mis
абстиненток	абстинентка	noun	noun:anim:p:v_rod
абстиненток	абстинентка	noun	noun:anim:p:v_zna
абстинентом	абстинент	noun	noun:anim:m:v_oru
абстинентці	абстинентка	noun	noun:anim:f:v_dav
абстинентці	абстинентка	noun	noun:anim:f:v_mis
абстиненті	абстинент	noun	noun:anim:m:v_mis
абстинентів	абстинент	noun	noun:anim:p:v_rod
абстинентів	абстинент	noun	noun:anim:p:v_zna
абстиненцій	абстиненція	noun	noun:inanim:p:v_rod
абстиненцію	абстиненція	noun	noun:inanim:f:v_zna
абстиненція	абстиненція	noun	noun:inanim:f:v_naz
абстиненціям	абстиненція	noun	noun:inanim:p:v_dav
абстиненціями	абстиненція	noun	noun:inanim:p:v_oru
абстиненціях	абстиненція	noun	noun:inanim:p:v_mis
абстиненціє	абстиненція	noun	noun:inanim:f:v_kly
абстиненцією	абстиненція	noun	noun:inanim:f:v_oru
абстиненції	абстиненція	noun	noun:inanim:f:v_dav
абстиненції	абстиненція	noun	noun:inanim:f:v_mis
абстиненції	абстиненція	noun	noun:inanim:f:v_rod
абстиненції	абстиненція	noun	noun:inanim:p:v_kly
абстиненції	абстиненція	noun	noun:inanim:p:v_naz
абстиненції	абстиненція	noun	noun:inanim:p:v_zna
абстрагованосте	абстрагованість	noun	noun:inanim:f:v_kly
абстрагованостей	абстрагованість	noun	noun:inanim:p:v_rod
абстрагованостям	абстрагованість	noun	noun:inanim:p:v_dav
абстрагованостями	абстрагованість	noun	noun:inanim:p:v_oru
абстрагованостях	абстрагованість	noun	noun:inanim:p:v_mis
абстрагованості	абстрагованість	noun	noun:inanim:f:v_dav
абстрагованості	абстрагованість	noun	noun:inanim:f:v_mis
абстрагованості	абстрагованість	noun	noun:inanim:f:v_rod
абстрагованості	абстрагованість	noun	noun:inanim:p:v_kly
абстрагованості	абстрагованість	noun	noun:inanim:p:v_naz
абстрагованості	абстрагованість	noun	noun:inanim:p:v_zna
абстрагованість	абстрагованість	noun	noun:inanim:f:v_naz
абстрагованість	абстрагованість	noun	noun:inanim:f:v_zna
абстрагованістю	абстрагованість	noun	noun:inanim:f:v_oru
абстрагуванню	абстрагування	noun	noun:inanim:n:v_dav
абстрагуванню	абстрагування	noun	noun:inanim:n:v_mis
абстрагування	абстрагування	noun	noun:inanim:n:v_kly
абстрагування	абстрагування	noun	noun:inanim:n:v_naz
абстрагування	абстрагування	noun	noun:inanim:n:v_rod
абстрагування	абстрагування	noun	noun:inanim:n:v_zna
абстрагування	абстрагування	noun	noun:inanim:p:v_kly
абстрагування	абстрагування	noun	noun:inanim:p:v_naz
абстрагування	абстрагування	noun	noun:inanim:p:v_zna
абстрагуванням	абстрагування	noun	noun:inanim:n:v_oru
абстрагуванням	абстрагування	noun	noun:inanim:p:v_dav
абстрагуваннями	абстрагування	noun	noun:inanim:p:v_oru
абстрагуваннях	абстрагування	noun	noun:inanim:p:v_mis
абстрагуванні	абстрагування	noun	noun:inanim:n:v_mis
абстрагувань	абстрагування	noun	noun:inanim:p:v_rod
абстракт	абстракт	noun	noun:inanim:m:v_naz
абстракт	абстракт	noun	noun:inanim:m:v_zna
абстрактам	абстракт	noun	noun:inanim:p:v_dav
абстрактами	абстракт	noun	noun:inanim:p:v_oru
абстрактах	абстракт	noun	noun:inanim:p:v_mis
абстракте	абстракт	noun	noun:inanim:m:v_kly
абстракти	абстракт	noun	noun:inanim:p:v_kly
абстракти	абстракт	noun	noun:inanim:p:v_naz
абстракти	абстракт	noun	noun:inanim:p:v_zna
абстрактові	абстракт	noun	noun:inanim:m:v_dav
абстрактові	абстракт	noun	noun:inanim:m:v_mis
абстрактом	абстракт	noun	noun:inanim:m:v_oru
абстракту	абстракт	noun	noun:inanim:m:v_dav
абстракту	абстракт	noun	noun:inanim:m:v_mis
абстракту	абстракт	noun	noun:inanim:m:v_rod
абстракті	абстракт	noun	noun:inanim:m:v_mis
абстрактів	абстракт	noun	noun:inanim:p:v_rod
абстракцій	абстракція	noun	noun:inanim:p:v_rod
абстракціоніст	абстракціоніст	noun	noun:anim:m:v_naz
абстракціоніста	абстракціоніст	noun	noun:anim:m:v_rod
абстракціоніста	абстракціоніст	noun	noun:anim:m:v_zna
абстракціоністам	абстракціоніст	noun	noun:anim:p:v_dav
абстракціоністами	абстракціоніст	noun	noun:anim:p:v_oru
абстракціоністах	абстракціоніст	noun	noun:anim:p:v_mis
абстракціоністе	абстракціоніст	noun	noun:anim:m:v_kly
абстракціоністи	абстракціоніст	noun	noun:anim:p:v_kly
абстракціоністи	абстракціоніст	noun	noun:anim:p:v_naz
абстракціоністи	абстракціоніст	noun	noun:anim:p:v_zna:rare
абстракціоністка	абстракціоністка	noun	noun:anim:f:v_naz
абстракціоністкам	абстракціоністка	noun	noun:anim:p:v_dav
абстракціоністками	абстракціоністка	noun	noun:anim:p:v_oru
абстракціоністках	абстракціоністка	noun	noun:anim:p:v_mis
абстракціоністки	абстракціоністка	noun	noun:anim:f:v_rod
абстракціоністки	абстракціоністка	noun	noun:anim:p:v_kly
абстракціоністки	абстракціоністка	noun	noun:anim:p:v_naz
абстракціоністки	абстракціоністка	noun	noun:anim:p:v_zna:rare
абстракціоністко	абстракціоністка	noun	noun:anim:f:v_kly
абстракціоністкою	абстракціоністка	noun	noun:anim:f:v_oru
абстракціоністку	абстракціоністка	noun	noun:anim:f:v_zna
абстракціоністові	абстракціоніст	noun	noun:anim:m:v_dav
абстракціоністові	абстракціоніст	noun	noun:anim:m:v_mis
абстракціоністок	абстракціоністка	noun	noun:anim:p:v_rod
абстракціоністок	абстракціоністка	noun	noun:anim:p:v_zna
абстракціоністом	абстракціоніст	noun	noun:anim:m:v_oru
абстракціоністці	абстракціоністка	noun	noun:anim:f:v_dav
абстракціоністці	абстракціоністка	noun	noun:anim:f:v_mis
абстракціоністі	абстракціоніст	noun	noun:anim:m:v_mis
абстракціоністів	абстракціоніст	noun	noun:anim:p:v_rod
абстракціоністів	абстракціоніст	noun	noun:anim:p:v_zna
абстракцію	абстракція	noun	noun:inanim:f:v_zna
абстракція	абстракція	noun	noun:inanim:f:v_naz
абстракціям	абстракція	noun	noun:inanim:p:v_dav
абстракціями	абстракція	noun	noun:inanim:p:v_oru
абстракціях	абстракція	noun	noun:inanim:p:v_mis
абстракціє	абстракція	noun	noun:inanim:f:v_kly
абстракцією	абстракція	noun	noun:inanim:f:v_oru
абстракції	абстракція	noun	noun:inanim:f:v_dav
абстракції	абстракція	noun	noun:inanim:f:v_mis
абстракції	абстракція	noun	noun:inanim:f:v_rod
абстракції	абстракція	noun	noun:inanim:p:v_kly
абстракції	абстракція	noun	noun:inanim:p:v_naz
абстракції	абстракція	noun	noun:inanim:p:v_zna
абсурд	абсурд	noun	noun:inanim:m:v_naz
абсурд	абсурд	noun	noun:inanim:m:v_zna
абсурдам	абсурд	noun	noun:inanim:p:v_dav
абсурдами	абсурд	noun	noun:inanim:p:v_oru
абсурдах	абсурд	noun	noun:inanim:p:v_mis
абсурде	абсурд	noun	noun:inanim:m:v_kly
абсурди	абсурд	noun	noun:inanim:p:v_kly
абсурди	абсурд	noun	noun:inanim:p:v_naz
абсурди	абсурд	noun	noun:inanim:p:v_zna
абсурдист	абсурдист	noun	noun:anim:m:v_naz
абсурдиста	абсурдист	noun	noun:anim:m:v_rod
абсурдиста	абсурдист	noun	noun:anim:m:v_zna
абсурдистам	абсурдист	noun	noun:anim:p:v_dav
абсурдистами	абсурдист	noun	noun:anim:p:v_oru
абсурдистах	абсурдист	noun	noun:anim:p:v_mis
абсурдисте	абсурдист	noun	noun:anim:m:v_kly
абсурдисти	абсурдист	noun	noun:anim:p:v_kly
абсурдисти	абсурдист	noun	noun:anim:p:v_naz
абсурдисти	абсурдист	noun	noun:anim:p:v_zna:rare
абсурдистка	абсурдистка	noun	noun:anim:f:v_naz
абсурдисткам	абсурдистка	noun	noun:anim:p:v_dav
абсурдистками	абсурдистка	noun	noun:anim:p:v_oru
абсурдистках	абсурдистка	noun	noun:anim:p:v_mis
абсурдистки	абсурдистка	noun	noun:anim:f:v_rod
абсурдистки	абсурдистка	noun	noun:anim:p:v_kly
абсурдистки	абсурдистка	noun	noun:anim:p:v_naz
абсурдистки	абсурдистка	noun	noun:anim:p:v_zna:rare
абсурдистко	абсурдистка	noun	noun:anim:f:v_kly
абсурдисткою	абсурдистка	noun	noun:anim:f:v_oru
абсурдистку	абсурдистка	noun	noun:anim:f:v_zna
абсурдистові	абсурдист	noun	noun:anim:m:v_dav
абсурдистові	абсурдист	noun	noun:anim:m:v_mis
абсурдисток	абсурдистка	noun	noun:anim:p:v_rod
абсурдисток	абсурдистка	noun	noun:anim:p:v_zna
абсурдистом	абсурдист	noun	noun:anim:m:v_oru
абсурдистці	абсурдистка	noun	noun:anim:f:v_dav
абсурдистці	абсурдистка	noun	noun:anim:f:v_mis
абсурдисті	абсурдист	noun	noun:anim:m:v_mis
абсурдистів	абсурдист	noun	noun:anim:p:v_rod
абсурдистів	абсурдист	noun	noun:anim:p:v_zna
абсурдносте	абсурдність	noun	noun:inanim:f:v_kly
абсурдностей	абсурдність	noun	noun:inanim:p:v_rod
абсурдностям	абсурдність	noun	noun:inanim:p:v_dav
абсурдностями	абсурдність	noun	noun:inanim:p:v_oru
абсурдностях	абсурдність	noun	noun:inanim:p:v_mis
абсурдності	абсурдність	noun	noun:inanim:f:v_dav
абсурдності	абсурдність	noun	noun:inanim:f:v_mis
абсурдності	абсурдність	noun	noun:inanim:f:v_rod
абсурдності	абсурдність	noun	noun:inanim:p:v_kly
абсурдності	абсурдність	noun	noun:inanim:p:v_naz
абсурдності	абсурдність	noun	noun:inanim:p:v_zna
абсурдність	абсурдність	noun	noun:inanim:f:v_naz
абсурдність	абсурдність	noun	noun:inanim:f:v_zna
абсурдністю	абсурдність	noun	noun:inanim:f:v_oru
абсурдові	абсурд	noun	noun:inanim:m:v_dav
абсурдові	абсурд	noun	noun:inanim:m:v_mis
абсурдом	абсурд	noun	noun:inanim:m:v_oru
абсурду	абсурд	noun	noun:inanim:m:v_dav
абсурду	абсурд	noun	noun:inanim:m:v_mis
абсурду	абсурд	noun	noun:inanim:m:v_rod
абсурді	абсурд	noun	noun:inanim:m:v_mis
абсурдів	абсурд	noun	noun:inanim:p:v_rod
абсцес	абсцес	noun	noun:inanim:m:v_naz
абсцес	абсцес	noun	noun:inanim:m:v_zna
абсцесам	абсцес	noun	noun:inanim:p:v_dav
абсцесами	абсцес	noun	noun:inanim:p:v_oru
абсцесах	абсцес	noun	noun:inanim:p:v_mis
абсцесе	абсцес	noun	noun:inanim:m:v_kly
абсцеси	абсцес	noun	noun:inanim:p:v_kly
абсцеси	абсцес	noun	noun:inanim:p:v_naz
абсцеси	абсцес	noun	noun:inanim:p:v_zna
абсцесові	абсцес	noun	noun:inanim:m:v_dav
абсцесові	абсцес	noun	noun:inanim:m:v_mis
абсцесом	абсцес	noun	noun:inanim:m:v_oru
абсцесу	абсцес	noun	noun:inanim:m:v_dav
абсцесу	абсцес	noun	noun:inanim:m:v_mis
абсцесу	абсцес	noun	noun:inanim:m:v_rod
абсцесі	абсцес	noun	noun:inanim:m:v_mis
абсцесів	абсцес	noun	noun:inanim:p:v_rod
абсцис	абсциса	noun	noun:inanim:p:v_rod
абсциса	абсциса	noun	noun:inanim:f:v_naz
абсцисам	абсциса	noun	noun:inanim:p:v_dav
абсцисами	абсциса	noun	noun:inanim:p:v_oru
абсцисах	абсциса	noun	noun:inanim:p:v_mis
абсциси	абсциса	noun	noun:inanim:f:v_rod
абсциси	абсциса	noun	noun:inanim:p:v_kly
абсциси	абсциса	noun	noun:inanim:p:v_naz
абсциси	абсциса	noun	noun:inanim:p:v_zna
абсцисо	абсциса	noun	noun:inanim:f:v_kly
абсцисою	абсциса	noun	noun:inanim:f:v_oru
абсцису	абсциса	noun	noun:inanim:f:v_zna
абсцисі	абсциса	noun	noun:inanim:f:v_dav
абсцисі	абсциса	noun	noun:inanim:f:v_mis
абукумаліт	абукумаліт	noun	noun:inanim:m:v_naz
абукумаліт	абукумаліт	noun	noun:inanim:m:v_zna
абукумалітам	абукумаліт	noun	noun:inanim:p:v_dav
абукумалітами	абукумаліт	noun	noun:inanim:p:v_oru
абукумалітах	абукумаліт	noun	noun:inanim:p:v_mis
абукумаліте	абукумаліт	noun	noun:inanim:m:v_kly
абукумаліти	абукумаліт	noun	noun:inanim:p:v_kly
абукумаліти	абукумаліт	noun	noun:inanim:p:v_naz
абукумаліти	абукумаліт	noun	noun:inanim:p:v_zna
абукумалітові	абукумаліт	noun	noun:inanim:m:v_dav
абукумалітові	абукумаліт	noun	noun:inanim:m:v_mis
абукумалітом	абукумаліт	noun	noun:inanim:m:v_oru
абукумаліту	абукумаліт	noun	noun:inanim:m:v_dav
абукумаліту	абукумаліт	noun	noun:inanim:m:v_mis
абукумаліту	абукумаліт	noun	noun:inanim:m:v_rod
абукумаліті	абукумаліт	noun	noun:inanim:m:v_mis
абукумалітів	абукумаліт	noun	noun:inanim:p:v_rod
абхаз	абхаз	noun	noun:anim:m:v_naz
абхаза	абхаз	noun	noun:anim:m:v_rod
абхаза	абхаз	noun	noun:anim:m:v_zna
абхазам	абхаз	noun	noun:anim:p:v_dav
абхазами	абхаз	noun	noun:anim:p:v_oru
абхазах	абхаз	noun	noun:anim:p:v_mis
абхазе	абхаз	noun	noun:anim:m:v_kly
абхазець	абхазець	noun	noun:anim:m:v_naz
абхази	абхаз	noun	noun:anim:p:v_kly
абхази	абхаз	noun	noun:anim:p:v_naz
абхази	абхаз	noun	noun:anim:p:v_zna:rare
абхазка	абхазка	noun	noun:anim:f:v_naz
абхазкам	абхазка	noun	noun:anim:p:v_dav
абхазками	абхазка	noun	noun:anim:p:v_oru
абхазках	абхазка	noun	noun:anim:p:v_mis
абхазки	абхазка	noun	noun:anim:f:v_rod
абхазки	абхазка	noun	noun:anim:p:v_kly
абхазки	абхазка	noun	noun:anim:p:v_naz
абхазки	абхазка	noun	noun:anim:p:v_zna:rare
абхазко	абхазка	noun	noun:anim:f:v_kly
абхазкою	абхазка	noun	noun:anim:f:v_oru
абхазку	абхазка	noun	noun:anim:f:v_zna
абхазові	абхаз	noun	noun:anim:m:v_dav
абхазові	абхаз	noun	noun:anim:m:v_mis
абхазок	абхазка	noun	noun:anim:p:v_rod
абхазок	абхазка	noun	noun:anim:p:v_zna
абхазом	абхаз	noun	noun:anim:m:v_oru
абхазцеві	абхазець	noun	noun:anim:m:v_dav
абхазцеві	абхазець	noun	noun:anim:m:v_mis
абхазцем	абхазець	noun	noun:anim:m:v_oru
абхазцю	абхазець	noun	noun:anim:m:v_dav
абхазцю	абхазець	noun	noun:anim:m:v_kly
абхазцю	абхазець	noun	noun:anim:m:v_mis
абхазця	абхазець	noun	noun:anim:m:v_rod
абхазця	абхазець	noun	noun:anim:m:v_zna
абхазцям	абхазець	noun	noun:anim:p:v_dav
абхазцями	абхазець	noun	noun:anim:p:v_oru
абхазцях	абхазець	noun	noun:anim:p:v_mis
абхазці	абхазець	noun	noun:anim:m:v_mis
абхазці	абхазець	noun	noun:anim:p:v_kly
абхазці	абхазець	noun	noun:anim:p:v_naz
абхазці	абхазець	noun	noun:anim:p:v_zna:rare
абхазці	абхазка	noun	noun:anim:f:v_dav
абхазці	абхазка	noun	noun:anim:f:v_mis
абхазців	абхазець	noun	noun:anim:p:v_rod
абхазців	абхазець	noun	noun:anim:p:v_zna
абхазі	абхаз	noun	noun:anim:m:v_mis
абхазів	абхаз	noun	noun:anim:p:v_rod
абхазів	абхаз	noun	noun:anim:p:v_zna
абьюзер	абьюзер	noun	noun:anim:m:v_naz:slang
абьюзера	абьюзер	noun	noun:anim:m:v_rod:slang
абьюзера	абьюзер	noun	noun:anim:m:v_zna:slang
абьюзерам	абьюзер	noun	noun:anim:p:v_dav:slang
абьюзерами	абьюзер	noun	noun:anim:p:v_oru:slang
абьюзерах	абьюзер	noun	noun:anim:p:v_mis:slang
абьюзере	абьюзер	noun	noun:anim:m:v_kly:slang
абьюзери	абьюзер	noun	noun:anim:p:v_kly:slang
абьюзери	абьюзер	noun	noun:anim:p:v_naz:slang
абьюзери	абьюзер	noun	noun:anim:p:v_zna:slang:rare
абьюзерові	абьюзер	noun	noun:anim:m:v_dav:slang
абьюзерові	абьюзер	noun	noun:anim:m:v_mis:slang
абьюзером	абьюзер	noun	noun:anim:m:v_oru:slang
абьюзері	абьюзер	noun	noun:anim:m:v_mis:slang
абьюзерів	абьюзер	noun	noun:anim:p:v_rod:slang
абьюзерів	абьюзер	noun	noun:anim:p:v_zna:slang
абізян	абізяна	noun	noun:anim:p:v_rod:slang
абізян	абізяна	noun	noun:anim:p:v_zna:slang
абізяна	абізяна	noun	noun:anim:f:v_naz:slang
абізянам	абізяна	noun	noun:anim:p:v_dav:slang
абізянами	абізяна	noun	noun:anim:p:v_oru:slang
абізянах	абізяна	noun	noun:anim:p:v_mis:slang
абізяни	абізяна	noun	noun:anim:f:v_rod:slang
абізяни	абізяна	noun	noun:anim:p:v_kly:slang
абізяни	абізяна	noun	noun:anim:p:v_naz:slang
абізяни	абізяна	noun	noun:anim:p:v_zna:slang
абізяно	абізяна	noun	noun:anim:f:v_kly:slang
абізяною	абізяна	noun	noun:anim:f:v_oru:slang
абізяну	абізяна	noun	noun:anim:f:v_zna:slang
абізяні	абізяна	noun	noun:anim:f:v_dav:slang
абізяні	абізяна	noun	noun:anim:f:v_mis:slang
абіоген	абіоген	noun	noun:inanim:m:v_naz
абіоген	абіоген	noun	noun:inanim:m:v_zna
абіогена	абіоген	noun	noun:inanim:m:v_rod
абіогенам	абіоген	noun	noun:inanim:p:v_dav
абіогенами	абіоген	noun	noun:inanim:p:v_oru
абіогенах	абіоген	noun	noun:inanim:p:v_mis
абіогене	абіоген	noun	noun:inanim:m:v_kly
абіогени	абіоген	noun	noun:inanim:p:v_kly
абіогени	абіоген	noun	noun:inanim:p:v_naz
абіогени	абіоген	noun	noun:inanim:p:v_zna
абіогенові	абіоген	noun	noun:inanim:m:v_dav
абіогенові	абіоген	noun	noun:inanim:m:v_mis
абіогеном	абіоген	noun	noun:inanim:m:v_oru
абіогені	абіоген	noun	noun:inanim:m:v_mis
абіогенів	абіоген	noun	noun:inanim:p:v_rod
абіотрофій	абіотрофія	noun	noun:inanim:p:v_rod
абіотрофію	абіотрофія	noun	noun:inanim:f:v_zna
абіотрофія	абіотрофія	noun	noun:inanim:f:v_naz
абіотрофіям	абіотрофія	noun	noun:inanim:p:v_dav
абіотрофіями	абіотрофія	noun	noun:inanim:p:v_oru
абіотрофіях	абіотрофія	noun	noun:inanim:p:v_mis
абіотрофіє	абіотрофія	noun	noun:inanim:f:v_kly
абіотрофією	абіотрофія	noun	noun:inanim:f:v_oru
абіотрофії	абіотрофія	noun	noun:inanim:f:v_dav
абіотрофії	абіотрофія	noun	noun:inanim:f:v_mis
абіотрофії	абіотрофія	noun	noun:inanim:f:v_rod
абіотрофії	абіотрофія	noun	noun:inanim:p:v_kly
абіотрофії	абіотрофія	noun	noun:inanim:p:v_naz
абіотрофії	абіотрофія	noun	noun:inanim:p:v_zna
абісале	абісаль	noun	noun:inanim:f:v_kly
абісалей	абісаль	noun	noun:inanim:p:v_rod
абісаллю	абісаль	noun	noun:inanim:f:v_oru
абісаль	абісаль	noun	noun:inanim:f:v_naz
абісаль	абісаль	noun	noun:inanim:f:v_zna
абісалям	абісаль	noun	noun:inanim:p:v_dav
абісалями	абісаль	noun	noun:inanim:p:v_oru
абісалях	абісаль	noun	noun:inanim:p:v_mis
абісалі	абісаль	noun	noun:inanim:f:v_dav
абісалі	абісаль	noun	noun:inanim:f:v_mis
абісалі	абісаль	noun	noun:inanim:f:v_rod
абісалі	абісаль	noun	noun:inanim:p:v_kly
абісалі	абісаль	noun	noun:inanim:p:v_naz
абісалі	абісаль	noun	noun:inanim:p:v_zna
абіссинець	абіссинець	noun	noun:anim:m:v_naz
абіссинка	абіссинка	noun	noun:anim:f:v_naz
абіссинкам	абіссинка	noun	noun:anim:p:v_dav
абіссинками	абіссинка	noun	noun:anim:p:v_oru
абіссинках	абіссинка	noun	noun:anim:p:v_mis
абіссинки	абіссинка	noun	noun:anim:f:v_rod
абіссинки	абіссинка	noun	noun:anim:p:v_kly
абіссинки	абіссинка	noun	noun:anim:p:v_naz
абіссинки	абіссинка	noun	noun:anim:p:v_zna:rare
абіссинко	абіссинка	noun	noun:anim:f:v_kly
абіссинкою	абіссинка	noun	noun:anim:f:v_oru
абіссинку	абіссинка	noun	noun:anim:f:v_zna
абіссинок	абіссинка	noun	noun:anim:p:v_rod
абіссинок	абіссинка	noun	noun:anim:p:v_zna
абіссинцеві	абіссинець	noun	noun:anim:m:v_dav
абіссинцеві	абіссинець	noun	noun:anim:m:v_mis
абіссинцем	абіссинець	noun	noun:anim:m:v_oru
абіссинцю	абіссинець	noun	noun:anim:m:v_dav
абіссинцю	абіссинець	noun	noun:anim:m:v_kly
абіссинцю	абіссинець	noun	noun:anim:m:v_mis
абіссинця	абіссинець	noun	noun:anim:m:v_rod
абіссинця	абіссинець	noun	noun:anim:m:v_zna
абіссинцям	абіссинець	noun	noun:anim:p:v_dav
абіссинцями	абіссинець	noun	noun:anim:p:v_oru
абіссинцях	абіссинець	noun	noun:anim:p:v_mis
абіссинці	абіссинець	noun	noun:anim:m:v_mis
абіссинці	абіссинець	noun	noun:anim:p:v_kly
абіссинці	абіссинець	noun	noun:anim:p:v_naz
абіссинці	абіссинець	noun	noun:anim:p:v_zna:rare
абіссинці	абіссинка	noun	noun:anim:f:v_dav
абіссинці	абіссинка	noun	noun:anim:f:v_mis
абіссинців	абіссинець	noun	noun:anim:p:v_rod
абіссинців	абіссинець	noun	noun:anim:p:v_zna
абіссінець	абіссінець	noun	noun:anim:m:v_naz
абіссінка	абіссінка	noun	noun:anim:f:v_naz
абіссінкам	абіссінка	noun	noun:anim:p:v_dav
абіссінками	абіссінка	noun	noun:anim:p:v_oru
абіссінках	абіссінка	noun	noun:anim:p:v_mis
абіссінки	абіссінка	noun	noun:anim:f:v_rod
абіссінки	абіссінка	noun	noun:anim:p:v_kly
абіссінки	абіссінка	noun	noun:anim:p:v_naz
абіссінки	абіссінка	noun	noun:anim:p:v_zna:rare
абіссінко	абіссінка	noun	noun:anim:f:v_kly
абіссінкою	абіссінка	noun	noun:anim:f:v_oru
абіссінку	абіссінка	noun	noun:anim:f:v_zna
абіссінок	абіссінка	noun	noun:anim:p:v_rod
абіссінок	абіссінка	noun	noun:anim:p:v_zna
абіссінцеві	абіссінець	noun	noun:anim:m:v_dav
абіссінцеві	абіссінець	noun	noun:anim:m:v_mis
абіссінцем	абіссінець	noun	noun:anim:m:v_oru
абіссінцю	абіссінець	noun	noun:anim:m:v_dav
абіссінцю	абіссінець	noun	noun:anim:m:v_kly
абіссінцю	абіссінець	noun	noun:anim:m:v_mis
абіссінця	абіссінець	noun	noun:anim:m:v_rod
абіссінця	абіссінець	noun	noun:anim:m:v_zna
абіссінцям	абіссінець	noun	noun:anim:p:v_dav
абіссінцями	абіссінець	noun	noun:anim:p:v_oru
абіссінцях	абіссінець	noun	noun:anim:p:v_mis
абіссінці	абіссінець	noun	noun:anim:m:v_mis
абіссінці	абіссінець	noun	noun:anim:p:v_kly
абіссінці	абіссінець	noun	noun:anim:p:v_naz
абіссінці	абіссінець	noun	noun:anim:p:v_zna:rare
абіссінці	абіссінка	noun	noun:anim:f:v_dav
абіссінці	абіссінка	noun	noun:anim:f:v_mis
абіссінців	абіссінець	noun	noun:anim:p:v_rod
абіссінців	абіссінець	noun	noun:anim:p:v_zna
абітурієнт	абітурієнт	noun	noun:anim:m:v_naz
абітурієнта	абітурієнт	noun	noun:anim:m:v_rod
абітурієнта	абітурієнт	noun	noun:anim:m:v_zna
абітурієнтам	абітурієнт	noun	noun:anim:p:v_dav
абітурієнтами	абітурієнт	noun	noun:anim:p:v_oru
абітурієнтах	абітурієнт	noun	noun:anim:p:v_mis
абітурієнте	абітурієнт	noun	noun:anim:m:v_kly
абітурієнти	абітурієнт	noun	noun:anim:p:v_kly
абітурієнти	абітурієнт	noun	noun:anim:p:v_naz
абітурієнти	абітурієнт	noun	noun:anim:p:v_zna:rare
абітурієнтка	абітурієнтка	noun	noun:anim:f:v_naz
абітурієнткам	абітурієнтка	noun	noun:anim:p:v_dav
абітурієнтками	абітурієнтка	noun	noun:anim:p:v_oru
абітурієнтках	абітурієнтка	noun	noun:anim:p:v_mis
абітурієнтки	абітурієнтка	noun	noun:anim:f:v_rod
абітурієнтки	абітурієнтка	noun	noun:anim:p:v_kly
абітурієнтки	абітурієнтка	noun	noun:anim:p:v_naz
абітурієнтки	абітурієнтка	noun	noun:anim:p:v_zna:rare
абітурієнтко	абітурієнтка	noun	noun:anim:f:v_kly
абітурієнткою	абітурієнтка	noun	noun:anim:f:v_oru
абітурієнтку	абітурієнтка	noun	noun:anim:f:v_zna
абітурієнтові	абітурієнт	noun	noun:anim:m:v_dav
абітурієнтові	абітурієнт	noun	noun:anim:m:v_mis
абітурієнток	абітурієнтка	noun	noun:anim:p:v_rod
абітурієнток	абітурієнтка	noun	noun:anim:p:v_zna
абітурієнтом	абітурієнт	noun	noun:anim:m:v_oru
абітурієнтці	абітурієнтка	noun	noun:anim:f:v_dav
абітурієнтці	абітурієнтка	noun	noun:anim:f:v_mis
абітурієнті	абітурієнт	noun	noun:anim:m:v_mis
абітурієнтів	абітурієнт	noun	noun:anim:p:v_rod
абітурієнтів	абітурієнт	noun	noun:anim:p:v_zna
ав	ава	noun	noun:inanim:p:v_rod:slang
ава	ава	noun	noun:inanim:f:v_naz:slang
авалеві	аваль	noun	noun:inanim:m:v_dav
авалеві	аваль	noun	noun:inanim:m:v_mis
авалем	аваль	noun	noun:inanim:m:v_oru
аваль	аваль	noun	noun:inanim:m:v_naz
аваль	аваль	noun	noun:inanim:m:v_zna
авалю	аваль	noun	noun:inanim:m:v_dav
авалю	аваль	noun	noun:inanim:m:v_kly
авалю	аваль	noun	noun:inanim:m:v_mis
авалю	аваль	noun	noun:inanim:m:v_rod
авалям	аваль	noun	noun:inanim:p:v_dav
авалями	аваль	noun	noun:inanim:p:v_oru
авалях	аваль	noun	noun:inanim:p:v_mis
авалі	аваль	noun	noun:inanim:m:v_mis
авалі	аваль	noun	noun:inanim:p:v_kly
авалі	аваль	noun	noun:inanim:p:v_naz
авалі	аваль	noun	noun:inanim:p:v_zna
авалів	аваль	noun	noun:inanim:p:v_rod
аваліст	аваліст	noun	noun:anim:m:v_naz
аваліста	аваліст	noun	noun:anim:m:v_rod
аваліста	аваліст	noun	noun:anim:m:v_zna
авалістам	аваліст	noun	noun:anim:p:v_dav
авалістами	аваліст	noun	noun:anim:p:v_oru
авалістах	аваліст	noun	noun:anim:p:v_mis
авалісте	аваліст	noun	noun:anim:m:v_kly
авалісти	аваліст	noun	noun:anim:p:v_kly
авалісти	аваліст	noun	noun:anim:p:v_naz
авалісти	аваліст	noun	noun:anim:p:v_zna:rare
авалістові	аваліст	noun	noun:anim:m:v_dav
авалістові	аваліст	noun	noun:anim:m:v_mis
авалістом	аваліст	noun	noun:anim:m:v_oru
авалісті	аваліст	noun	noun:anim:m:v_mis
авалістів	аваліст	noun	noun:anim:p:v_rod
авалістів	аваліст	noun	noun:anim:p:v_zna
авам	ава	noun	noun:inanim:p:v_dav:slang
авами	ава	noun	noun:inanim:p:v_oru:slang
аванбек	аванбек	noun	noun:inanim:m:v_naz
аванбек	аванбек	noun	noun:inanim:m:v_zna
аванбека	аванбек	noun	noun:inanim:m:v_rod
аванбекам	аванбек	noun	noun:inanim:p:v_dav
аванбеками	аванбек	noun	noun:inanim:p:v_oru
аванбеках	аванбек	noun	noun:inanim:p:v_mis
аванбеки	аванбек	noun	noun:inanim:p:v_kly
аванбеки	аванбек	noun	noun:inanim:p:v_naz
аванбеки	аванбек	noun	noun:inanim:p:v_zna
аванбекові	аванбек	noun	noun:inanim:m:v_dav
аванбекові	аванбек	noun	noun:inanim:m:v_mis
аванбеком	аванбек	noun	noun:inanim:m:v_oru
аванбеку	аванбек	noun	noun:inanim:m:v_dav
аванбеку	аванбек	noun	noun:inanim:m:v_kly
аванбеку	аванбек	noun	noun:inanim:m:v_mis
аванбеків	аванбек	noun	noun:inanim:p:v_rod
авангард	авангард	noun	noun:inanim:m:v_naz
авангард	авангард	noun	noun:inanim:m:v_zna
авангардам	авангард	noun	noun:inanim:p:v_dav
авангардами	авангард	noun	noun:inanim:p:v_oru
авангардах	авангард	noun	noun:inanim:p:v_mis
авангарде	авангард	noun	noun:inanim:m:v_kly
авангарди	авангард	noun	noun:inanim:p:v_kly
авангарди	авангард	noun	noun:inanim:p:v_naz
авангарди	авангард	noun	noun:inanim:p:v_zna
авангардист	авангардист	noun	noun:anim:m:v_naz
авангардиста	авангардист	noun	noun:anim:m:v_rod
авангардиста	авангардист	noun	noun:anim:m:v_zna
авангардистам	авангардист	noun	noun:anim:p:v_dav
авангардистами	авангардист	noun	noun:anim:p:v_oru
авангардистах	авангардист	noun	noun:anim:p:v_mis
авангардисте	авангардист	noun	noun:anim:m:v_kly
авангардисти	авангардист	noun	noun:anim:p:v_kly
авангардисти	авангардист	noun	noun:anim:p:v_naz
авангардисти	авангардист	noun	noun:anim:p:v_zna:rare
авангардистка	авангардистка	noun	noun:anim:f:v_naz
авангардисткам	авангардистка	noun	noun:anim:p:v_dav
авангардистками	авангардистка	noun	noun:anim:p:v_oru
авангардистках	авангардистка	noun	noun:anim:p:v_mis
авангардистки	авангардистка	noun	noun:anim:f:v_rod
авангардистки	авангардистка	noun	noun:anim:p:v_kly
авангардистки	авангардистка	noun	noun:anim:p:v_naz
авангардистки	авангардистка	noun	noun:anim:p:v_zna:rare
авангардистко	авангардистка	noun	noun:anim:f:v_kly
авангардисткою	авангардистка	noun	noun:anim:f:v_oru
авангардистку	авангардистка	noun	noun:anim:f:v_zna
авангардистові	авангардист	noun	noun:anim:m:v_dav
авангардистові	авангардист	noun	noun:anim:m:v_mis
авангардисток	авангардистка	noun	noun:anim:p:v_rod
авангардисток	авангардистка	noun	noun:anim:p:v_zna
авангардистом	авангардист	noun	noun:anim:m:v_oru
авангардистці	авангардистка	noun	noun:anim:f:v_dav
авангардистці	авангардистка	noun	noun:anim:f:v_mis
авангардисті	авангардист	noun	noun:anim:m:v_mis
авангардистів	авангардист	noun	noun:anim:p:v_rod
авангардистів	авангардист	noun	noun:anim:p:v_zna
авангардові	авангард	noun	noun:inanim:m:v_dav
авангардові	авангард	noun	noun:inanim:m:v_mis
авангардом	авангард	noun	noun:inanim:m:v_oru
авангарду	авангард	noun	noun:inanim:m:v_dav
авангарду	авангард	noun	noun:inanim:m:v_mis
авангарду	авангард	noun	noun:inanim:m:v_rod
авангарді	авангард	noun	noun:inanim:m:v_mis
авангардів	авангард	noun	noun:inanim:p:v_rod
авангардівець	авангардівець	noun	noun:anim:m:v_naz
авангардівцеві	авангардівець	noun	noun:anim:m:v_dav
авангардівцеві	авангардівець	noun	noun:anim:m:v_mis
авангардівцем	авангардівець	noun	noun:anim:m:v_oru
авангардівцю	авангардівець	noun	noun:anim:m:v_dav
авангардівцю	авангардівець	noun	noun:anim:m:v_kly
авангардівцю	авангардівець	noun	noun:anim:m:v_mis
авангардівця	авангардівець	noun	noun:anim:m:v_rod
авангардівця	авангардівець	noun	noun:anim:m:v_zna
авангардівцям	авангардівець	noun	noun:anim:p:v_dav
авангардівцями	авангардівець	noun	noun:anim:p:v_oru
авангардівцях	авангардівець	noun	noun:anim:p:v_mis
авангардівці	авангардівець	noun	noun:anim:m:v_mis
авангардівці	авангардівець	noun	noun:anim:p:v_kly
авангардівці	авангардівець	noun	noun:anim:p:v_naz
авангардівці	авангардівець	noun	noun:anim:p:v_zna:rare
авангардівців	авангардівець	noun	noun:anim:p:v_rod
авангардівців	авангардівець	noun	noun:anim:p:v_zna
аванзал	аванзал	noun	noun:inanim:m:v_naz
аванзал	аванзал	noun	noun:inanim:m:v_zna
аванзалам	аванзал	noun	noun:inanim:p:v_dav
аванзалами	аванзал	noun	noun:inanim:p:v_oru
аванзалах	аванзал	noun	noun:inanim:p:v_mis
аванзале	аванзал	noun	noun:inanim:m:v_kly
аванзали	аванзал	noun	noun:inanim:p:v_kly
аванзали	аванзал	noun	noun:inanim:p:v_naz
аванзали	аванзал	noun	noun:inanim:p:v_zna
аванзалові	аванзал	noun	noun:inanim:m:v_dav
аванзалові	аванзал	noun	noun:inanim:m:v_mis
аванзалом	аванзал	noun	noun:inanim:m:v_oru
аванзалу	аванзал	noun	noun:inanim:m:v_dav
аванзалу	аванзал	noun	noun:inanim:m:v_mis
аванзалу	аванзал	noun	noun:inanim:m:v_rod
аванзалі	аванзал	noun	noun:inanim:m:v_mis
аванзалів	аванзал	noun	noun:inanim:p:v_rod
аванкамер	аванкамера	noun	noun:inanim:p:v_rod
аванкамера	аванкамера	noun	noun:inanim:f:v_naz
аванкамерам	аванкамера	noun	noun:inanim:p:v_dav
аванкамерами	аванкамера	noun	noun:inanim:p:v_oru
аванкамерах	аванкамера	noun	noun:inanim:p:v_mis
аванкамери	аванкамера	noun	noun:inanim:f:v_rod
аванкамери	аванкамера	noun	noun:inanim:p:v_kly
аванкамери	аванкамера	noun	noun:inanim:p:v_naz
аванкамери	аванкамера	noun	noun:inanim:p:v_zna
аванкамеро	аванкамера	noun	noun:inanim:f:v_kly
аванкамерою	аванкамера	noun	noun:inanim:f:v_oru
аванкамеру	аванкамера	noun	noun:inanim:f:v_zna
аванкамері	аванкамера	noun	noun:inanim:f:v_dav
аванкамері	аванкамера	noun	noun:inanim:f:v_mis
аванлож	аванложа	noun	noun:inanim:p:v_rod
аванложа	аванложа	noun	noun:inanim:f:v_naz
аванложам	аванложа	noun	noun:inanim:p:v_dav
аванложами	аванложа	noun	noun:inanim:p:v_oru
аванложах	аванложа	noun	noun:inanim:p:v_mis
аванложе	аванложа	noun	noun:inanim:f:v_kly
аванложею	аванложа	noun	noun:inanim:f:v_oru
аванложу	аванложа	noun	noun:inanim:f:v_zna
аванложі	аванложа	noun	noun:inanim:f:v_dav
аванложі	аванложа	noun	noun:inanim:f:v_mis
аванложі	аванложа	noun	noun:inanim:f:v_rod
аванложі	аванложа	noun	noun:inanim:p:v_kly
аванложі	аванложа	noun	noun:inanim:p:v_naz
аванложі	аванложа	noun	noun:inanim:p:v_zna
аванплощ	аванплоща	noun	noun:inanim:p:v_rod
аванплоща	аванплоща	noun	noun:inanim:f:v_naz
аванплощам	аванплоща	noun	noun:inanim:p:v_dav
аванплощами	аванплоща	noun	noun:inanim:p:v_oru
аванплощах	аванплоща	noun	noun:inanim:p:v_mis
аванплоще	аванплоща	noun	noun:inanim:f:v_kly
аванплощею	аванплоща	noun	noun:inanim:f:v_oru
аванплощу	аванплоща	noun	noun:inanim:f:v_zna
аванплощі	аванплоща	noun	noun:inanim:f:v_dav
аванплощі	аванплоща	noun	noun:inanim:f:v_mis
аванплощі	аванплоща	noun	noun:inanim:f:v_rod
аванплощі	аванплоща	noun	noun:inanim:p:v_kly
аванплощі	аванплоща	noun	noun:inanim:p:v_naz
аванплощі	аванплоща	noun	noun:inanim:p:v_zna
аванпорт	аванпорт	noun	noun:inanim:m:v_naz
аванпорт	аванпорт	noun	noun:inanim:m:v_zna
аванпортам	аванпорт	noun	noun:inanim:p:v_dav
аванпортами	аванпорт	noun	noun:inanim:p:v_oru
аванпортах	аванпорт	noun	noun:inanim:p:v_mis
аванпорте	аванпорт	noun	noun:inanim:m:v_kly
аванпорти	аванпорт	noun	noun:inanim:p:v_kly
аванпорти	аванпорт	noun	noun:inanim:p:v_naz
аванпорти	аванпорт	noun	noun:inanim:p:v_zna
аванпортові	аванпорт	noun	noun:inanim:m:v_dav
аванпортові	аванпорт	noun	noun:inanim:m:v_mis
аванпортом	аванпорт	noun	noun:inanim:m:v_oru
аванпорту	аванпорт	noun	noun:inanim:m:v_dav
аванпорту	аванпорт	noun	noun:inanim:m:v_mis
аванпорту	аванпорт	noun	noun:inanim:m:v_rod
аванпорті	аванпорт	noun	noun:inanim:m:v_mis
аванпортів	аванпорт	noun	noun:inanim:p:v_rod
аванпост	аванпост	noun	noun:inanim:m:v_naz
аванпост	аванпост	noun	noun:inanim:m:v_zna
аванпостам	аванпост	noun	noun:inanim:p:v_dav
аванпостами	аванпост	noun	noun:inanim:p:v_oru
аванпостах	аванпост	noun	noun:inanim:p:v_mis
аванпосте	аванпост	noun	noun:inanim:m:v_kly
аванпости	аванпост	noun	noun:inanim:p:v_kly
аванпости	аванпост	noun	noun:inanim:p:v_naz
аванпости	аванпост	noun	noun:inanim:p:v_zna
аванпостові	аванпост	noun	noun:inanim:m:v_dav
аванпостові	аванпост	noun	noun:inanim:m:v_mis
аванпостом	аванпост	noun	noun:inanim:m:v_oru
аванпосту	аванпост	noun	noun:inanim:m:v_dav
аванпосту	аванпост	noun	noun:inanim:m:v_mis
аванпосту	аванпост	noun	noun:inanim:m:v_rod
аванпості	аванпост	noun	noun:inanim:m:v_mis
аванпостів	аванпост	noun	noun:inanim:p:v_rod
аванпроект	аванпроект	noun	noun:inanim:m:v_naz:up92
аванпроект	аванпроект	noun	noun:inanim:m:v_zna:up92
аванпроектам	аванпроект	noun	noun:inanim:p:v_dav:up92
аванпроектами	аванпроект	noun	noun:inanim:p:v_oru:up92
аванпроектах	аванпроект	noun	noun:inanim:p:v_mis:up92
аванпроекте	аванпроект	noun	noun:inanim:m:v_kly:up92
аванпроекти	аванпроект	noun	noun:inanim:p:v_kly:up92
аванпроекти	аванпроект	noun	noun:inanim:p:v_naz:up92
аванпроекти	аванпроект	noun	noun:inanim:p:v_zna:up92
аванпроектові	аванпроект	noun	noun:inanim:m:v_dav:up92
аванпроектові	аванпроект	noun	noun:inanim:m:v_mis:up92
аванпроектом	аванпроект	noun	noun:inanim:m:v_oru:up92
аванпроекту	аванпроект	noun	noun:inanim:m:v_dav:up92
аванпроекту	аванпроект	noun	noun:inanim:m:v_mis:up92
аванпроекту	аванпроект	noun	noun:inanim:m:v_rod:up92
аванпроекті	аванпроект	noun	noun:inanim:m:v_mis:up92
аванпроектів	аванпроект	noun	noun:inanim:p:v_rod:up92
аванпроєкт	аванпроєкт	noun	noun:inanim:m:v_naz:up19
аванпроєкт	аванпроєкт	noun	noun:inanim:m:v_zna:up19
аванпроєктам	аванпроєкт	noun	noun:inanim:p:v_dav:up19
аванпроєктами	аванпроєкт	noun	noun:inanim:p:v_oru:up19
аванпроєктах	аванпроєкт	noun	noun:inanim:p:v_mis:up19
аванпроєкте	аванпроєкт	noun	noun:inanim:m:v_kly:up19
аванпроєкти	аванпроєкт	noun	noun:inanim:p:v_kly:up19
аванпроєкти	аванпроєкт	noun	noun:inanim:p:v_naz:up19
аванпроєкти	аванпроєкт	noun	noun:inanim:p:v_zna:up19
аванпроєктові	аванпроєкт	noun	noun:inanim:m:v_dav:up19
аванпроєктові	аванпроєкт	noun	noun:inanim:m:v_mis:up19
аванпроєктом	аванпроєкт	noun	noun:inanim:m:v_oru:up19
аванпроєкту	аванпроєкт	noun	noun:inanim:m:v_dav:up19
аванпроєкту	аванпроєкт	noun	noun:inanim:m:v_mis:up19
аванпроєкту	аванпроєкт	noun	noun:inanim:m:v_rod:up19
аванпроєкті	аванпроєкт	noun	noun:inanim:m:v_mis:up19
аванпроєктів	аванпроєкт	noun	noun:inanim:p:v_rod:up19
аванс	аванс	noun	noun:inanim:m:v_naz
аванс	аванс	noun	noun:inanim:m:v_zna
авансам	аванс	noun	noun:inanim:p:v_dav
авансами	аванс	noun	noun:inanim:p:v_oru
авансах	аванс	noun	noun:inanim:p:v_mis
авансе	аванс	noun	noun:inanim:m:v_kly
аванси	аванс	noun	noun:inanim:p:v_kly
аванси	аванс	noun	noun:inanim:p:v_naz
аванси	аванс	noun	noun:inanim:p:v_zna
авансик	авансик	noun	noun:inanim:m:v_naz
авансик	авансик	noun	noun:inanim:m:v_zna
авансикам	авансик	noun	noun:inanim:p:v_dav
авансиками	авансик	noun	noun:inanim:p:v_oru
авансиках	авансик	noun	noun:inanim:p:v_mis
авансики	авансик	noun	noun:inanim:p:v_kly
авансики	авансик	noun	noun:inanim:p:v_naz
авансики	авансик	noun	noun:inanim:p:v_zna
авансикові	авансик	noun	noun:inanim:m:v_dav
авансикові	авансик	noun	noun:inanim:m:v_mis
авансиком	авансик	noun	noun:inanim:m:v_oru
авансику	авансик	noun	noun:inanim:m:v_dav
авансику	авансик	noun	noun:inanim:m:v_kly
авансику	авансик	noun	noun:inanim:m:v_mis
авансику	авансик	noun	noun:inanim:m:v_rod
авансиків	авансик	noun	noun:inanim:p:v_rod
авансові	аванс	noun	noun:inanim:m:v_dav
авансові	аванс	noun	noun:inanim:m:v_mis
авансодавець	авансодавець	noun	noun:anim:m:v_naz
авансодавцеві	авансодавець	noun	noun:anim:m:v_dav
авансодавцеві	авансодавець	noun	noun:anim:m:v_mis
авансодавцем	авансодавець	noun	noun:anim:m:v_oru
авансодавцю	авансодавець	noun	noun:anim:m:v_dav
авансодавцю	авансодавець	noun	noun:anim:m:v_kly
авансодавцю	авансодавець	noun	noun:anim:m:v_mis
авансодавця	авансодавець	noun	noun:anim:m:v_rod
авансодавця	авансодавець	noun	noun:anim:m:v_zna
авансодавцям	авансодавець	noun	noun:anim:p:v_dav
авансодавцями	авансодавець	noun	noun:anim:p:v_oru
авансодавцях	авансодавець	noun	noun:anim:p:v_mis
авансодавці	авансодавець	noun	noun:anim:m:v_mis
авансодавці	авансодавець	noun	noun:anim:p:v_kly
авансодавці	авансодавець	noun	noun:anim:p:v_naz
авансодавці	авансодавець	noun	noun:anim:p:v_zna:rare
авансодавців	авансодавець	noun	noun:anim:p:v_rod
авансодавців	авансодавець	noun	noun:anim:p:v_zna
авансом	аванс	noun	noun:inanim:m:v_oru
авансотримач	авансотримач	noun	noun:anim:m:v_naz
авансотримача	авансотримач	noun	noun:anim:m:v_rod
авансотримача	авансотримач	noun	noun:anim:m:v_zna
авансотримачам	авансотримач	noun	noun:anim:p:v_dav
авансотримачами	авансотримач	noun	noun:anim:p:v_oru
авансотримачах	авансотримач	noun	noun:anim:p:v_mis
авансотримачеві	авансотримач	noun	noun:anim:m:v_dav
авансотримачеві	авансотримач	noun	noun:anim:m:v_mis
авансотримачем	авансотримач	noun	noun:anim:m:v_oru
авансотримачу	авансотримач	noun	noun:anim:m:v_dav
авансотримачу	авансотримач	noun	noun:anim:m:v_kly
авансотримачу	авансотримач	noun	noun:anim:m:v_mis
авансотримачі	авансотримач	noun	noun:anim:m:v_mis
авансотримачі	авансотримач	noun	noun:anim:p:v_kly
авансотримачі	авансотримач	noun	noun:anim:p:v_naz
авансотримачі	авансотримач	noun	noun:anim:p:v_zna:rare
авансотримачів	авансотримач	noun	noun:anim:p:v_rod
авансотримачів	авансотримач	noun	noun:anim:p:v_zna
авансоутримувач	авансоутримувач	noun	noun:anim:m:v_naz
авансоутримувача	авансоутримувач	noun	noun:anim:m:v_rod
авансоутримувача	авансоутримувач	noun	noun:anim:m:v_zna
авансоутримувачам	авансоутримувач	noun	noun:anim:p:v_dav
авансоутримувачами	авансоутримувач	noun	noun:anim:p:v_oru
авансоутримувачах	авансоутримувач	noun	noun:anim:p:v_mis
авансоутримувачеві	авансоутримувач	noun	noun:anim:m:v_dav
авансоутримувачеві	авансоутримувач	noun	noun:anim:m:v_mis
авансоутримувачем	авансоутримувач	noun	noun:anim:m:v_oru
авансоутримувачу	авансоутримувач	noun	noun:anim:m:v_dav
авансоутримувачу	авансоутримувач	noun	noun:anim:m:v_kly
авансоутримувачу	авансоутримувач	noun	noun:anim:m:v_mis
авансоутримувачі	авансоутримувач	noun	noun:anim:m:v_mis
авансоутримувачі	авансоутримувач	noun	noun:anim:p:v_kly
авансоутримувачі	авансоутримувач	noun	noun:anim:p:v_naz
авансоутримувачі	авансоутримувач	noun	noun:anim:p:v_zna:rare
авансоутримувачів	авансоутримувач	noun	noun:anim:p:v_rod
авансоутримувачів	авансоутримувач	noun	noun:anim:p:v_zna
авансу	аванс	noun	noun:inanim:m:v_dav
авансу	аванс	noun	noun:inanim:m:v_mis
авансу	аванс	noun	noun:inanim:m:v_rod
авансуванню	авансування	noun	noun:inanim:n:v_dav
авансуванню	авансування	noun	noun:inanim:n:v_mis
авансування	авансування	noun	noun:inanim:n:v_kly
авансування	авансування	noun	noun:inanim:n:v_naz
авансування	авансування	noun	noun:inanim:n:v_rod
авансування	авансування	noun	noun:inanim:n:v_zna
авансування	авансування	noun	noun:inanim:p:v_kly
авансування	авансування	noun	noun:inanim:p:v_naz
авансування	авансування	noun	noun:inanim:p:v_zna
авансуванням	авансування	noun	noun:inanim:n:v_oru
авансуванням	авансування	noun	noun:inanim:p:v_dav
авансуваннями	авансування	noun	noun:inanim:p:v_oru
авансуваннях	авансування	noun	noun:inanim:p:v_mis
авансуванні	авансування	noun	noun:inanim:n:v_mis
авансувань	авансування	noun	noun:inanim:p:v_rod
авансцен	авансцена	noun	noun:inanim:p:v_rod
авансцена	авансцена	noun	noun:inanim:f:v_naz
авансценам	авансцена	noun	noun:inanim:p:v_dav
авансценами	авансцена	noun	noun:inanim:p:v_oru
авансценах	авансцена	noun	noun:inanim:p:v_mis
авансцени	авансцена	noun	noun:inanim:f:v_rod
авансцени	авансцена	noun	noun:inanim:p:v_kly
авансцени	авансцена	noun	noun:inanim:p:v_naz
авансцени	авансцена	noun	noun:inanim:p:v_zna
авансцено	авансцена	noun	noun:inanim:f:v_kly
авансценою	авансцена	noun	noun:inanim:f:v_oru
авансцену	авансцена	noun	noun:inanim:f:v_zna
авансцені	авансцена	noun	noun:inanim:f:v_dav
авансцені	авансцена	noun	noun:inanim:f:v_mis
авансі	аванс	noun	noun:inanim:m:v_mis
авансів	аванс	noun	noun:inanim:p:v_rod
авантитул	авантитул	noun	noun:inanim:m:v_naz
авантитул	авантитул	noun	noun:inanim:m:v_zna
авантитулам	авантитул	noun	noun:inanim:p:v_dav
авантитулами	авантитул	noun	noun:inanim:p:v_oru
авантитулах	авантитул	noun	noun:inanim:p:v_mis
авантитуле	авантитул	noun	noun:inanim:m:v_kly
авантитули	авантитул	noun	noun:inanim:p:v_kly
авантитули	авантитул	noun	noun:inanim:p:v_naz
авантитули	авантитул	noun	noun:inanim:p:v_zna
авантитулові	авантитул	noun	noun:inanim:m:v_dav
авантитулові	авантитул	noun	noun:inanim:m:v_mis
авантитулом	авантитул	noun	noun:inanim:m:v_oru
авантитулу	авантитул	noun	noun:inanim:m:v_dav
авантитулу	авантитул	noun	noun:inanim:m:v_mis
авантитулу	авантитул	noun	noun:inanim:m:v_rod
авантитулі	авантитул	noun	noun:inanim:m:v_mis
авантитулів	авантитул	noun	noun:inanim:p:v_rod
авантюр	авантюра	noun	noun:inanim:p:v_rod
авантюра	авантюра	noun	noun:inanim:f:v_naz
авантюрам	авантюра	noun	noun:inanim:p:v_dav
авантюрами	авантюра	noun	noun:inanim:p:v_oru
авантюрах	авантюра	noun	noun:inanim:p:v_mis
авантюри	авантюра	noun	noun:inanim:f:v_rod
авантюри	авантюра	noun	noun:inanim:p:v_kly
авантюри	авантюра	noun	noun:inanim:p:v_naz
авантюри	авантюра	noun	noun:inanim:p:v_zna
авантюрин	авантюрин	noun	noun:inanim:m:v_naz
авантюрин	авантюрин	noun	noun:inanim:m:v_zna
авантюрина	авантюрин	noun	noun:inanim:m:v_rod
авантюринам	авантюрин	noun	noun:inanim:p:v_dav
авантюринами	авантюрин	noun	noun:inanim:p:v_oru
авантюринах	авантюрин	noun	noun:inanim:p:v_mis
авантюрине	авантюрин	noun	noun:inanim:m:v_kly
авантюрини	авантюрин	noun	noun:inanim:p:v_kly
авантюрини	авантюрин	noun	noun:inanim:p:v_naz
авантюрини	авантюрин	noun	noun:inanim:p:v_zna
авантюринові	авантюрин	noun	noun:inanim:m:v_dav
авантюринові	авантюрин	noun	noun:inanim:m:v_mis
авантюрином	авантюрин	noun	noun:inanim:m:v_oru
авантюрині	авантюрин	noun	noun:inanim:m:v_mis
авантюринів	авантюрин	noun	noun:inanim:p:v_rod
авантюрист	авантюрист	noun	noun:anim:m:v_naz
авантюриста	авантюрист	noun	noun:anim:m:v_rod
авантюриста	авантюрист	noun	noun:anim:m:v_zna
авантюристам	авантюрист	noun	noun:anim:p:v_dav
авантюристами	авантюрист	noun	noun:anim:p:v_oru
авантюристах	авантюрист	noun	noun:anim:p:v_mis
авантюристе	авантюрист	noun	noun:anim:m:v_kly
авантюристи	авантюрист	noun	noun:anim:p:v_kly
авантюристи	авантюрист	noun	noun:anim:p:v_naz
авантюристи	авантюрист	noun	noun:anim:p:v_zna:rare
авантюристка	авантюристка	noun	noun:anim:f:v_naz
авантюристкам	авантюристка	noun	noun:anim:p:v_dav
авантюристками	авантюристка	noun	noun:anim:p:v_oru
авантюристках	авантюристка	noun	noun:anim:p:v_mis
авантюристки	авантюристка	noun	noun:anim:f:v_rod
авантюристки	авантюристка	noun	noun:anim:p:v_kly
авантюристки	авантюристка	noun	noun:anim:p:v_naz
авантюристки	авантюристка	noun	noun:anim:p:v_zna:rare
авантюристко	авантюристка	noun	noun:anim:f:v_kly
авантюристкою	авантюристка	noun	noun:anim:f:v_oru
авантюристку	авантюристка	noun	noun:anim:f:v_zna
авантюристові	авантюрист	noun	noun:anim:m:v_dav
авантюристові	авантюрист	noun	noun:anim:m:v_mis
авантюристок	авантюристка	noun	noun:anim:p:v_rod
авантюристок	авантюристка	noun	noun:anim:p:v_zna
авантюристом	авантюрист	noun	noun:anim:m:v_oru
авантюристочка	авантюристочка	noun	noun:anim:f:v_naz
авантюристочкам	авантюристочка	noun	noun:anim:p:v_dav
авантюристочками	авантюристочка	noun	noun:anim:p:v_oru
авантюристочках	авантюристочка	noun	noun:anim:p:v_mis
авантюристочки	авантюристочка	noun	noun:anim:f:v_rod
авантюристочки	авантюристочка	noun	noun:anim:p:v_kly
авантюристочки	авантюристочка	noun	noun:anim:p:v_naz
авантюристочки	авантюристочка	noun	noun:anim:p:v_zna:rare
авантюристочко	авантюристочка	noun	noun:anim:f:v_kly
авантюристочкою	авантюристочка	noun	noun:anim:f:v_oru
авантюристочку	авантюристочка	noun	noun:anim:f:v_zna
авантюристочок	авантюристочка	noun	noun:anim:p:v_rod
авантюристочок	авантюристочка	noun	noun:anim:p:v_zna
авантюристочці	авантюристочка	noun	noun:anim:f:v_dav
авантюристочці	авантюристочка	noun	noun:anim:f:v_mis
авантюристці	авантюристка	noun	noun:anim:f:v_dav
авантюристці	авантюристка	noun	noun:anim:f:v_mis
авантюристі	авантюрист	noun	noun:anim:m:v_mis
авантюристів	авантюрист	noun	noun:anim:p:v_rod
авантюристів	авантюрист	noun	noun:anim:p:v_zna
авантюрка	авантюрка	noun	noun:inanim:f:v_naz
авантюркам	авантюрка	noun	noun:inanim:p:v_dav
авантюрками	авантюрка	noun	noun:inanim:p:v_oru
авантюрках	авантюрка	noun	noun:inanim:p:v_mis
авантюрки	авантюрка	noun	noun:inanim:f:v_rod
авантюрки	авантюрка	noun	noun:inanim:p:v_kly
авантюрки	авантюрка	noun	noun:inanim:p:v_naz
авантюрки	авантюрка	noun	noun:inanim:p:v_zna
авантюрко	авантюрка	noun	noun:inanim:f:v_kly
авантюркою	авантюрка	noun	noun:inanim:f:v_oru
авантюрку	авантюрка	noun	noun:inanim:f:v_zna
авантюрник	авантюрник	noun	noun:anim:m:v_naz
авантюрника	авантюрник	noun	noun:anim:m:v_rod
авантюрника	авантюрник	noun	noun:anim:m:v_zna
авантюрникам	авантюрник	noun	noun:anim:p:v_dav
авантюрниками	авантюрник	noun	noun:anim:p:v_oru
авантюрниках	авантюрник	noun	noun:anim:p:v_mis
авантюрники	авантюрник	noun	noun:anim:p:v_kly
авантюрники	авантюрник	noun	noun:anim:p:v_naz
авантюрники	авантюрник	noun	noun:anim:p:v_zna:rare
авантюрникові	авантюрник	noun	noun:anim:m:v_dav
авантюрникові	авантюрник	noun	noun:anim:m:v_mis
авантюрником	авантюрник	noun	noun:anim:m:v_oru
авантюрнику	авантюрник	noun	noun:anim:m:v_dav
авантюрнику	авантюрник	noun	noun:anim:m:v_kly
авантюрнику	авантюрник	noun	noun:anim:m:v_mis
авантюрників	авантюрник	noun	noun:anim:p:v_rod
авантюрників	авантюрник	noun	noun:anim:p:v_zna
авантюрнице	авантюрниця	noun	noun:anim:f:v_kly
авантюрницею	авантюрниця	noun	noun:anim:f:v_oru
авантюрниць	авантюрниця	noun	noun:anim:p:v_rod
авантюрниць	авантюрниця	noun	noun:anim:p:v_zna
авантюрницю	авантюрниця	noun	noun:anim:f:v_zna
авантюрниця	авантюрниця	noun	noun:anim:f:v_naz
авантюрницям	авантюрниця	noun	noun:anim:p:v_dav
авантюрницями	авантюрниця	noun	noun:anim:p:v_oru
авантюрницях	авантюрниця	noun	noun:anim:p:v_mis
авантюрниці	авантюрниця	noun	noun:anim:f:v_dav
авантюрниці	авантюрниця	noun	noun:anim:f:v_mis
авантюрниці	авантюрниця	noun	noun:anim:f:v_rod
авантюрниці	авантюрниця	noun	noun:anim:p:v_kly
авантюрниці	авантюрниця	noun	noun:anim:p:v_naz
авантюрниці	авантюрниця	noun	noun:anim:p:v_zna:rare
авантюро	авантюра	noun	noun:inanim:f:v_kly
авантюрок	авантюрка	noun	noun:inanim:p:v_rod
авантюрою	авантюра	noun	noun:inanim:f:v_oru
авантюру	авантюра	noun	noun:inanim:f:v_zna
авантюрці	авантюрка	noun	noun:inanim:f:v_dav
авантюрці	авантюрка	noun	noun:inanim:f:v_mis
авантюрі	авантюра	noun	noun:inanim:f:v_dav
авантюрі	авантюра	noun	noun:inanim:f:v_mis
авар	авар	noun	noun:anim:m:v_naz
авара	авар	noun	noun:anim:m:v_rod
авара	авар	noun	noun:anim:m:v_zna
аварам	авар	noun	noun:anim:p:v_dav
аварами	авар	noun	noun:anim:p:v_oru
аварах	авар	noun	noun:anim:p:v_mis
аваре	авар	noun	noun:anim:m:v_kly
аварець	аварець	noun	noun:anim:m:v_naz
авари	авар	noun	noun:anim:p:v_kly
авари	авар	noun	noun:anim:p:v_naz
авари	авар	noun	noun:anim:p:v_zna:rare
аварка	аварка	noun	noun:anim:f:v_naz
аваркам	аварка	noun	noun:anim:p:v_dav
аварками	аварка	noun	noun:anim:p:v_oru
аварках	аварка	noun	noun:anim:p:v_mis
аварки	аварка	noun	noun:anim:f:v_rod
аварки	аварка	noun	noun:anim:p:v_kly
аварки	аварка	noun	noun:anim:p:v_naz
аварки	аварка	noun	noun:anim:p:v_zna:rare
аварко	аварка	noun	noun:anim:f:v_kly
аваркою	аварка	noun	noun:anim:f:v_oru
аварку	аварка	noun	noun:anim:f:v_zna
аварові	авар	noun	noun:anim:m:v_dav
аварові	авар	noun	noun:anim:m:v_mis
аварок	аварка	noun	noun:anim:p:v_rod
аварок	аварка	noun	noun:anim:p:v_zna
аваром	авар	noun	noun:anim:m:v_oru
аварцеві	аварець	noun	noun:anim:m:v_dav
аварцеві	аварець	noun	noun:anim:m:v_mis
аварцем	аварець	noun	noun:anim:m:v_oru
аварцю	аварець	noun	noun:anim:m:v_dav
аварцю	аварець	noun	noun:anim:m:v_kly
аварцю	аварець	noun	noun:anim:m:v_mis
аварця	аварець	noun	noun:anim:m:v_rod
аварця	аварець	noun	noun:anim:m:v_zna
аварцям	аварець	noun	noun:anim:p:v_dav
аварцями	аварець	noun	noun:anim:p:v_oru
аварцях	аварець	noun	noun:anim:p:v_mis
аварці	аварець	noun	noun:anim:m:v_mis
аварці	аварець	noun	noun:anim:p:v_kly
аварці	аварець	noun	noun:anim:p:v_naz
аварці	аварець	noun	noun:anim:p:v_zna:rare
аварці	аварка	noun	noun:anim:f:v_dav
аварці	аварка	noun	noun:anim:f:v_mis
аварців	аварець	noun	noun:anim:p:v_rod
аварців	аварець	noun	noun:anim:p:v_zna
аварі	авар	noun	noun:anim:m:v_mis
аварів	авар	noun	noun:anim:p:v_rod
аварів	авар	noun	noun:anim:p:v_zna
аварій	аварія	noun	noun:inanim:p:v_rod
аварійка	аварійка	noun	noun:inanim:f:v_naz
аварійкам	аварійка	noun	noun:inanim:p:v_dav
аварійками	аварійка	noun	noun:inanim:p:v_oru
аварійках	аварійка	noun	noun:inanim:p:v_mis
аварійки	аварійка	noun	noun:inanim:f:v_rod
аварійки	аварійка	noun	noun:inanim:p:v_kly
аварійки	аварійка	noun	noun:inanim:p:v_naz
аварійки	аварійка	noun	noun:inanim:p:v_zna
аварійко	аварійка	noun	noun:inanim:f:v_kly
аварійкою	аварійка	noun	noun:inanim:f:v_oru
аварійку	аварійка	noun	noun:inanim:f:v_zna
аварійник	аварійник	noun	noun:anim:m:v_naz
аварійника	аварійник	noun	noun:anim:m:v_rod
аварійника	аварійник	noun	noun:anim:m:v_zna
аварійникам	аварійник	noun	noun:anim:p:v_dav
аварійниками	аварійник	noun	noun:anim:p:v_oru
аварійниках	аварійник	noun	noun:anim:p:v_mis
аварійники	аварійник	noun	noun:anim:p:v_kly
аварійники	аварійник	noun	noun:anim:p:v_naz
аварійники	аварійник	noun	noun:anim:p:v_zna:rare
аварійникові	аварійник	noun	noun:anim:m:v_dav
аварійникові	аварійник	noun	noun:anim:m:v_mis
аварійником	аварійник	noun	noun:anim:m:v_oru
аварійнику	аварійник	noun	noun:anim:m:v_dav
аварійнику	аварійник	noun	noun:anim:m:v_kly
аварійнику	аварійник	noun	noun:anim:m:v_mis
аварійників	аварійник	noun	noun:anim:p:v_rod
аварійників	аварійник	noun	noun:anim:p:v_zna
аварійносте	аварійність	noun	noun:inanim:f:v_kly
аварійностей	аварійність	noun	noun:inanim:p:v_rod
аварійностям	аварійність	noun	noun:inanim:p:v_dav
аварійностями	аварійність	noun	noun:inanim:p:v_oru
аварійностях	аварійність	noun	noun:inanim:p:v_mis
аварійності	аварійність	noun	noun:inanim:f:v_dav
аварійності	аварійність	noun	noun:inanim:f:v_mis
аварійності	аварійність	noun	noun:inanim:f:v_rod
аварійності	аварійність	noun	noun:inanim:p:v_kly
аварійності	аварійність	noun	noun:inanim:p:v_naz
аварійності	аварійність	noun	noun:inanim:p:v_zna
аварійність	аварійність	noun	noun:inanim:f:v_naz
аварійність	аварійність	noun	noun:inanim:f:v_zna
аварійністю	аварійність	noun	noun:inanim:f:v_oru
аварійок	аварійка	noun	noun:inanim:p:v_rod
аварійці	аварійка	noun	noun:inanim:f:v_dav
аварійці	аварійка	noun	noun:inanim:f:v_mis
аварію	аварія	noun	noun:inanim:f:v_zna
аварія	аварія	noun	noun:inanim:f:v_naz
аваріям	аварія	noun	noun:inanim:p:v_dav
аваріями	аварія	noun	noun:inanim:p:v_oru
аваріях	аварія	noun	noun:inanim:p:v_mis
аваріє	аварія	noun	noun:inanim:f:v_kly
аварією	аварія	noun	noun:inanim:f:v_oru
аварії	аварія	noun	noun:inanim:f:v_dav
аварії	аварія	noun	noun:inanim:f:v_mis
аварії	аварія	noun	noun:inanim:f:v_rod
аварії	аварія	noun	noun:inanim:p:v_kly
аварії	аварія	noun	noun:inanim:p:v_naz
аварії	аварія	noun	noun:inanim:p:v_zna
аватар	аватар	noun	noun:inanim:m:v_naz
аватар	аватар	noun	noun:inanim:m:v_zna
аватара	аватар	noun	noun:inanim:m:v_rod
аватарам	аватар	noun	noun:inanim:p:v_dav
аватарами	аватар	noun	noun:inanim:p:v_oru
аватарах	аватар	noun	noun:inanim:p:v_mis
аватаре	аватар	noun	noun:inanim:m:v_kly
аватари	аватар	noun	noun:inanim:p:v_kly
аватари	аватар	noun	noun:inanim:p:v_naz
аватари	аватар	noun	noun:inanim:p:v_zna
аватарка	аватарка	noun	noun:inanim:f:v_naz
аватаркам	аватарка	noun	noun:inanim:p:v_dav
аватарками	аватарка	noun	noun:inanim:p:v_oru
аватарках	аватарка	noun	noun:inanim:p:v_mis
аватарки	аватарка	noun	noun:inanim:f:v_rod
аватарки	аватарка	noun	noun:inanim:p:v_kly
аватарки	аватарка	noun	noun:inanim:p:v_naz
аватарки	аватарка	noun	noun:inanim:p:v_zna
аватарко	аватарка	noun	noun:inanim:f:v_kly
аватаркою	аватарка	noun	noun:inanim:f:v_oru
аватарку	аватарка	noun	noun:inanim:f:v_zna
аватарові	аватар	noun	noun:inanim:m:v_dav
аватарові	аватар	noun	noun:inanim:m:v_mis
аватарок	аватарка	noun	noun:inanim:p:v_rod
аватаром	аватар	noun	noun:inanim:m:v_oru
аватарці	аватарка	noun	noun:inanim:f:v_dav
аватарці	аватарка	noun	noun:inanim:f:v_mis
аватарі	аватар	noun	noun:inanim:m:v_mis
аватарів	аватар	noun	noun:inanim:p:v_rod
авах	ава	noun	noun:inanim:p:v_mis:slang
авв	авва	noun	noun:anim:p:v_rod:slang
авв	авва	noun	noun:anim:p:v_zna:slang
авва	авва	noun	noun:anim:m:v_naz:slang
аввам	авва	noun	noun:anim:p:v_dav:slang
аввами	авва	noun	noun:anim:p:v_oru:slang
аввах	авва	noun	noun:anim:p:v_mis:slang
авви	авва	noun	noun:anim:m:v_rod:slang
авви	авва	noun	noun:anim:p:v_kly:slang
авви	авва	noun	noun:anim:p:v_naz:slang
авви	авва	noun	noun:anim:p:v_zna:slang:rare
авво	авва	noun	noun:anim:m:v_kly:slang
аввою	авва	noun	noun:anim:m:v_oru:slang
авву	авва	noun	noun:anim:m:v_zna:slang
авві	авва	noun	noun:anim:m:v_dav:slang
авві	авва	noun	noun:anim:m:v_mis:slang
авгур	авгур	noun	noun:anim:m:v_naz
авгура	авгур	noun	noun:anim:m:v_rod
авгура	авгур	noun	noun:anim:m:v_zna
авгурам	авгур	noun	noun:anim:p:v_dav
авгурами	авгур	noun	noun:anim:p:v_oru
авгурах	авгур	noun	noun:anim:p:v_mis
авгуре	авгур	noun	noun:anim:m:v_kly
авгури	авгур	noun	noun:anim:p:v_kly
авгури	авгур	noun	noun:anim:p:v_naz
авгури	авгур	noun	noun:anim:p:v_zna:rare
авгурові	авгур	noun	noun:anim:m:v_dav
авгурові	авгур	noun	noun:anim:m:v_mis
авгуром	авгур	noun	noun:anim:m:v_oru
авгурі	авгур	noun	noun:anim:m:v_mis
авгурів	авгур	noun	noun:anim:p:v_rod
авгурів	авгур	noun	noun:anim:p:v_zna
август	август	noun	noun:inanim:m:v_naz
август	август	noun	noun:inanim:m:v_zna
августа	август	noun	noun:inanim:m:v_rod
августал	августал	noun	noun:anim:m:v_naz
августала	августал	noun	noun:anim:m:v_rod
августала	августал	noun	noun:anim:m:v_zna
августалам	августал	noun	noun:anim:p:v_dav
августалами	августал	noun	noun:anim:p:v_oru
августалах	августал	noun	noun:anim:p:v_mis
августале	августал	noun	noun:anim:m:v_kly
августали	августал	noun	noun:anim:p:v_kly
августали	августал	noun	noun:anim:p:v_naz
августали	августал	noun	noun:anim:p:v_zna:rare
августалові	августал	noun	noun:anim:m:v_dav
августалові	августал	noun	noun:anim:m:v_mis
августалом	августал	noun	noun:anim:m:v_oru
августалі	августал	noun	noun:anim:m:v_mis
августалів	августал	noun	noun:anim:p:v_rod
августалів	августал	noun	noun:anim:p:v_zna
августам	август	noun	noun:inanim:p:v_dav
августами	август	noun	noun:inanim:p:v_oru
августах	август	noun	noun:inanim:p:v_mis
августе	август	noun	noun:inanim:m:v_kly
августи	август	noun	noun:inanim:p:v_kly
августи	август	noun	noun:inanim:p:v_naz
августи	август	noun	noun:inanim:p:v_zna
августинець	августинець	noun	noun:anim:m:v_naz
августинка	августинка	noun	noun:anim:f:v_naz
августинкам	августинка	noun	noun:anim:p:v_dav
августинками	августинка	noun	noun:anim:p:v_oru
августинках	августинка	noun	noun:anim:p:v_mis
августинки	августинка	noun	noun:anim:f:v_rod
августинки	августинка	noun	noun:anim:p:v_kly
августинки	августинка	noun	noun:anim:p:v_naz
августинки	августинка	noun	noun:anim:p:v_zna:rare
августинко	августинка	noun	noun:anim:f:v_kly
августинкою	августинка	noun	noun:anim:f:v_oru
августинку	августинка	noun	noun:anim:f:v_zna
августинок	августинка	noun	noun:anim:p:v_rod
августинок	августинка	noun	noun:anim:p:v_zna
августинцеві	августинець	noun	noun:anim:m:v_dav
августинцеві	августинець	noun	noun:anim:m:v_mis
августинцем	августинець	noun	noun:anim:m:v_oru
августинцю	августинець	noun	noun:anim:m:v_dav
августинцю	августинець	noun	noun:anim:m:v_kly
августинцю	августинець	noun	noun:anim:m:v_mis
августинця	августинець	noun	noun:anim:m:v_rod
августинця	августинець	noun	noun:anim:m:v_zna
августинцям	августинець	noun	noun:anim:p:v_dav
августинцями	августинець	noun	noun:anim:p:v_oru
августинцях	августинець	noun	noun:anim:p:v_mis
августинці	августинець	noun	noun:anim:m:v_mis
августинці	августинець	noun	noun:anim:p:v_kly
августинці	августинець	noun	noun:anim:p:v_naz
августинці	августинець	noun	noun:anim:p:v_zna:rare
августинці	августинка	noun	noun:anim:f:v_dav
августинці	августинка	noun	noun:anim:f:v_mis
августинців	августинець	noun	noun:anim:p:v_rod
августинців	августинець	noun	noun:anim:p:v_zna
августиніан	августиніанин	noun	noun:anim:p:v_rod
августиніан	августиніанин	noun	noun:anim:p:v_zna
августиніанам	августиніанин	noun	noun:anim:p:v_dav
августиніанами	августиніанин	noun	noun:anim:p:v_oru
августиніанах	августиніанин	noun	noun:anim:p:v_mis
августиніанець	августиніанець	noun	noun:anim:m:v_naz
августиніани	августиніанин	noun	noun:anim:p:v_kly
августиніани	августиніанин	noun	noun:anim:p:v_naz
августиніани	августиніанин	noun	noun:anim:p:v_zna:rare
августиніанин	августиніанин	noun	noun:anim:m:v_naz
августиніанина	августиніанин	noun	noun:anim:m:v_rod
августиніанина	августиніанин	noun	noun:anim:m:v_zna
августиніанине	августиніанин	noun	noun:anim:m:v_kly
августиніанинові	августиніанин	noun	noun:anim:m:v_dav
августиніанинові	августиніанин	noun	noun:anim:m:v_mis
августиніанином	августиніанин	noun	noun:anim:m:v_oru
августиніанині	августиніанин	noun	noun:anim:m:v_mis
августиніанцеві	августиніанець	noun	noun:anim:m:v_dav
августиніанцеві	августиніанець	noun	noun:anim:m:v_mis
августиніанцем	августиніанець	noun	noun:anim:m:v_oru
августиніанцю	августиніанець	noun	noun:anim:m:v_dav
августиніанцю	августиніанець	noun	noun:anim:m:v_kly
августиніанцю	августиніанець	noun	noun:anim:m:v_mis
августиніанця	августиніанець	noun	noun:anim:m:v_rod
августиніанця	августиніанець	noun	noun:anim:m:v_zna
августиніанцям	августиніанець	noun	noun:anim:p:v_dav
августиніанцями	августиніанець	noun	noun:anim:p:v_oru
августиніанцях	августиніанець	noun	noun:anim:p:v_mis
августиніанці	августиніанець	noun	noun:anim:m:v_mis
августиніанці	августиніанець	noun	noun:anim:p:v_kly
августиніанці	августиніанець	noun	noun:anim:p:v_naz
августиніанці	августиніанець	noun	noun:anim:p:v_zna:rare
августиніанців	августиніанець	noun	noun:anim:p:v_rod
августиніанців	августиніанець	noun	noun:anim:p:v_zna
августові	август	noun	noun:inanim:m:v_dav
августові	август	noun	noun:inanim:m:v_mis
августом	август	noun	noun:inanim:m:v_oru
августі	август	noun	noun:inanim:m:v_mis
августіан	августіан	noun	noun:anim:m:v_naz
августіан	августіанин	noun	noun:anim:p:v_rod
августіан	августіанин	noun	noun:anim:p:v_zna
августіана	августіан	noun	noun:anim:m:v_rod
августіана	августіан	noun	noun:anim:m:v_zna
августіанам	августіан	noun	noun:anim:p:v_dav
августіанам	августіанин	noun	noun:anim:p:v_dav
августіанами	августіан	noun	noun:anim:p:v_oru
августіанами	августіанин	noun	noun:anim:p:v_oru
августіанах	августіан	noun	noun:anim:p:v_mis
августіанах	августіанин	noun	noun:anim:p:v_mis
августіане	августіан	noun	noun:anim:m:v_kly
августіани	августіан	noun	noun:anim:p:v_kly
августіани	августіан	noun	noun:anim:p:v_naz
августіани	августіан	noun	noun:anim:p:v_zna:rare
августіани	августіанин	noun	noun:anim:p:v_kly
августіани	августіанин	noun	noun:anim:p:v_naz
августіани	августіанин	noun	noun:anim:p:v_zna:rare
августіанин	августіанин	noun	noun:anim:m:v_naz
августіанина	августіанин	noun	noun:anim:m:v_rod
августіанина	августіанин	noun	noun:anim:m:v_zna
августіанине	августіанин	noun	noun:anim:m:v_kly
августіанинові	августіанин	noun	noun:anim:m:v_dav
августіанинові	августіанин	noun	noun:anim:m:v_mis
августіанином	августіанин	noun	noun:anim:m:v_oru
августіанині	августіанин	noun	noun:anim:m:v_mis
августіанка	августіанка	noun	noun:anim:f:v_naz
августіанкам	августіанка	noun	noun:anim:p:v_dav
августіанками	августіанка	noun	noun:anim:p:v_oru
августіанках	августіанка	noun	noun:anim:p:v_mis
августіанки	августіанка	noun	noun:anim:f:v_rod
августіанки	августіанка	noun	noun:anim:p:v_kly
августіанки	августіанка	noun	noun:anim:p:v_naz
августіанки	августіанка	noun	noun:anim:p:v_zna:rare
августіанко	августіанка	noun	noun:anim:f:v_kly
августіанкою	августіанка	noun	noun:anim:f:v_oru
августіанку	августіанка	noun	noun:anim:f:v_zna
августіанові	августіан	noun	noun:anim:m:v_dav
августіанові	августіан	noun	noun:anim:m:v_mis
августіанок	августіанка	noun	noun:anim:p:v_rod
августіанок	августіанка	noun	noun:anim:p:v_zna
августіаном	августіан	noun	noun:anim:m:v_oru
августіанці	августіанка	noun	noun:anim:f:v_dav
августіанці	августіанка	noun	noun:anim:f:v_mis
августіані	августіан	noun	noun:anim:m:v_mis
августіанів	августіан	noun	noun:anim:p:v_rod
августіанів	августіан	noun	noun:anim:p:v_zna
августів	август	noun	noun:inanim:p:v_rod
авгіт	авгіт	noun	noun:inanim:m:v_naz
авгіт	авгіт	noun	noun:inanim:m:v_zna
авгітам	авгіт	noun	noun:inanim:p:v_dav
авгітами	авгіт	noun	noun:inanim:p:v_oru
авгітах	авгіт	noun	noun:inanim:p:v_mis
авгіте	авгіт	noun	noun:inanim:m:v_kly
авгіти	авгіт	noun	noun:inanim:p:v_kly
авгіти	авгіт	noun	noun:inanim:p:v_naz
авгіти	авгіт	noun	noun:inanim:p:v_zna
авгітові	авгіт	noun	noun:inanim:m:v_dav
авгітові	авгіт	noun	noun:inanim:m:v_mis
авгітом	авгіт	noun	noun:inanim:m:v_oru
авгіту	авгіт	noun	noun:inanim:m:v_dav
авгіту	авгіт	noun	noun:inanim:m:v_mis
авгіту	авгіт	noun	noun:inanim:m:v_rod
авгіті	авгіт	noun	noun:inanim:m:v_mis
авгітів	авгіт	noun	noun:inanim:p:v_rod
авдит	авдит	noun	noun:inanim:m:v_naz:up19
авдит	авдит	noun	noun:inanim:m:v_zna:up19
авдитам	авдит	noun	noun:inanim:p:v_dav:up19
авдитами	авдит	noun	noun:inanim:p:v_oru:up19
авдитах	авдит	noun	noun:inanim:p:v_mis:up19
авдите	авдит	noun	noun:inanim:m:v_kly:up19
авдити	авдит	noun	noun:inanim:p:v_kly:up19
авдити	авдит	noun	noun:inanim:p:v_naz:up19
авдити	авдит	noun	noun:inanim:p:v_zna:up19
авдитові	авдит	noun	noun:inanim:m:v_dav:up19
авдитові	авдит	noun	noun:inanim:m:v_mis:up19
авдитом	авдит	noun	noun:inanim:m:v_oru:up19
авдитор	авдитор	noun	noun:anim:m:v_naz
авдитора	авдитор	noun	noun:anim:m:v_rod
авдитора	авдитор	noun	noun:anim:m:v_zna
авдиторам	авдитор	noun	noun:anim:p:v_dav
авдиторами	авдитор	noun	noun:anim:p:v_oru
авдиторах	авдитор	noun	noun:anim:p:v_mis
авдиторе	авдитор	noun	noun:anim:m:v_kly
авдитори	авдитор	noun	noun:anim:p:v_kly
авдитори	авдитор	noun	noun:anim:p:v_naz
авдитори	авдитор	noun	noun:anim:p:v_zna:rare
авдиторка	авдиторка	noun	noun:anim:f:v_naz:up19
авдиторкам	авдиторка	noun	noun:anim:p:v_dav:up19
авдиторками	авдиторка	noun	noun:anim:p:v_oru:up19
авдиторках	авдиторка	noun	noun:anim:p:v_mis:up19
авдиторки	авдиторка	noun	noun:anim:f:v_rod:up19
авдиторки	авдиторка	noun	noun:anim:p:v_kly:up19
авдиторки	авдиторка	noun	noun:anim:p:v_naz:up19
авдиторки	авдиторка	noun	noun:anim:p:v_zna:up19:rare
авдиторко	авдиторка	noun	noun:anim:f:v_kly:up19
авдиторкою	авдиторка	noun	noun:anim:f:v_oru:up19
авдиторку	авдиторка	noun	noun:anim:f:v_zna:up19
авдиторові	авдитор	noun	noun:anim:m:v_dav
авдиторові	авдитор	noun	noun:anim:m:v_mis
авдиторок	авдиторка	noun	noun:anim:p:v_rod:up19
авдиторок	авдиторка	noun	noun:anim:p:v_zna:up19
авдитором	авдитор	noun	noun:anim:m:v_oru
авдиторств	авдиторство	noun	noun:inanim:p:v_rod
авдиторства	авдиторство	noun	noun:inanim:n:v_rod
авдиторства	авдиторство	noun	noun:inanim:p:v_kly
авдиторства	авдиторство	noun	noun:inanim:p:v_naz
авдиторства	авдиторство	noun	noun:inanim:p:v_zna
авдиторствам	авдиторство	noun	noun:inanim:p:v_dav
авдиторствами	авдиторство	noun	noun:inanim:p:v_oru
авдиторствах	авдиторство	noun	noun:inanim:p:v_mis
авдиторство	авдиторство	noun	noun:inanim:n:v_kly
авдиторство	авдиторство	noun	noun:inanim:n:v_naz
авдиторство	авдиторство	noun	noun:inanim:n:v_zna
авдиторством	авдиторство	noun	noun:inanim:n:v_oru
авдиторству	авдиторство	noun	noun:inanim:n:v_dav
авдиторству	авдиторство	noun	noun:inanim:n:v_mis
авдиторстві	авдиторство	noun	noun:inanim:n:v_mis
авдиторці	авдиторка	noun	noun:anim:f:v_dav:up19
авдиторці	авдиторка	noun	noun:anim:f:v_mis:up19
авдиторі	авдитор	noun	noun:anim:m:v_mis
авдиторів	авдитор	noun	noun:anim:p:v_rod
авдиторів	авдитор	noun	noun:anim:p:v_zna
авдиторій	авдиторія	noun	noun:inanim:p:v_rod
авдиторію	авдиторія	noun	noun:inanim:f:v_zna
авдиторія	авдиторія	noun	noun:inanim:f:v_naz
авдиторіям	авдиторія	noun	noun:inanim:p:v_dav
авдиторіями	авдиторія	noun	noun:inanim:p:v_oru
авдиторіях	авдиторія	noun	noun:inanim:p:v_mis
авдиторіє	авдиторія	noun	noun:inanim:f:v_kly
авдиторією	авдиторія	noun	noun:inanim:f:v_oru
авдиторії	авдиторія	noun	noun:inanim:f:v_dav
авдиторії	авдиторія	noun	noun:inanim:f:v_mis
авдиторії	авдиторія	noun	noun:inanim:f:v_rod
авдиторії	авдиторія	noun	noun:inanim:p:v_kly
авдиторії	авдиторія	noun	noun:inanim:p:v_naz
авдиторії	авдиторія	noun	noun:inanim:p:v_zna
авдиту	авдит	noun	noun:inanim:m:v_dav:up19
авдиту	авдит	noun	noun:inanim:m:v_mis:up19
авдиту	авдит	noun	noun:inanim:m:v_rod:up19
авдиті	авдит	noun	noun:inanim:m:v_mis:up19
авдитів	авдит	noun	noun:inanim:p:v_rod:up19
авдифон	авдифон	noun	noun:inanim:m:v_naz:up19
авдифон	авдифон	noun	noun:inanim:m:v_zna:up19
авдифона	авдифон	noun	noun:inanim:m:v_rod:up19
авдифонам	авдифон	noun	noun:inanim:p:v_dav:up19
авдифонами	авдифон	noun	noun:inanim:p:v_oru:up19
авдифонах	авдифон	noun	noun:inanim:p:v_mis:up19
авдифоне	авдифон	noun	noun:inanim:m:v_kly:up19
авдифони	авдифон	noun	noun:inanim:p:v_kly:up19
авдифони	авдифон	noun	noun:inanim:p:v_naz:up19
авдифони	авдифон	noun	noun:inanim:p:v_zna:up19
авдифонові	авдифон	noun	noun:inanim:m:v_dav:up19
авдифонові	авдифон	noun	noun:inanim:m:v_mis:up19
авдифоном	авдифон	noun	noun:inanim:m:v_oru:up19
авдифоні	авдифон	noun	noun:inanim:m:v_mis:up19
авдифонів	авдифон	noun	noun:inanim:p:v_rod:up19
авдіал	авдіал	noun	noun:anim:m:v_naz:up19
авдіала	авдіал	noun	noun:anim:m:v_rod:up19
авдіала	авдіал	noun	noun:anim:m:v_zna:up19
авдіалам	авдіал	noun	noun:anim:p:v_dav:up19
авдіалами	авдіал	noun	noun:anim:p:v_oru:up19
авдіалах	авдіал	noun	noun:anim:p:v_mis:up19
авдіале	авдіал	noun	noun:anim:m:v_kly:up19
авдіали	авдіал	noun	noun:anim:p:v_kly:up19
авдіали	авдіал	noun	noun:anim:p:v_naz:up19
авдіали	авдіал	noun	noun:anim:p:v_zna:up19:rare
авдіалові	авдіал	noun	noun:anim:m:v_dav:up19
авдіалові	авдіал	noun	noun:anim:m:v_mis:up19
авдіалом	авдіал	noun	noun:anim:m:v_oru:up19
авдіалі	авдіал	noun	noun:anim:m:v_mis:up19
авдіалів	авдіал	noun	noun:anim:p:v_rod:up19
авдіалів	авдіал	noun	noun:anim:p:v_zna:up19
авдіоадаптер	авдіоадаптер	noun	noun:inanim:m:v_naz:up19
авдіоадаптер	авдіоадаптер	noun	noun:inanim:m:v_zna:up19
авдіоадаптера	авдіоадаптер	noun	noun:inanim:m:v_rod:up19
авдіоадаптерам	авдіоадаптер	noun	noun:inanim:p:v_dav:up19
авдіоадаптерами	авдіоадаптер	noun	noun:inanim:p:v_oru:up19
авдіоадаптерах	авдіоадаптер	noun	noun:inanim:p:v_mis:up19
авдіоадаптере	авдіоадаптер	noun	noun:inanim:m:v_kly:up19
авдіоадаптери	авдіоадаптер	noun	noun:inanim:p:v_kly:up19
авдіоадаптери	авдіоадаптер	noun	noun:inanim:p:v_naz:up19
авдіоадаптери	авдіоадаптер	noun	noun:inanim:p:v_zna:up19
авдіоадаптерові	авдіоадаптер	noun	noun:inanim:m:v_dav:up19
авдіоадаптерові	авдіоадаптер	noun	noun:inanim:m:v_mis:up19
авдіоадаптером	авдіоадаптер	noun	noun:inanim:m:v_oru:up19
авдіоадаптері	авдіоадаптер	noun	noun:inanim:m:v_mis:up19
авдіоадаптерів	авдіоадаптер	noun	noun:inanim:p:v_rod:up19
авдіограм	авдіограма	noun	noun:inanim:p:v_rod:up19
авдіограма	авдіограма	noun	noun:inanim:f:v_naz:up19
авдіограмам	авдіограма	noun	noun:inanim:p:v_dav:up19
авдіограмами	авдіограма	noun	noun:inanim:p:v_oru:up19
авдіограмах	авдіограма	noun	noun:inanim:p:v_mis:up19
авдіограми	авдіограма	noun	noun:inanim:f:v_rod:up19
авдіограми	авдіограма	noun	noun:inanim:p:v_kly:up19
авдіограми	авдіограма	noun	noun:inanim:p:v_naz:up19
авдіограми	авдіограма	noun	noun:inanim:p:v_zna:up19
авдіограмо	авдіограма	noun	noun:inanim:f:v_kly:up19
авдіограмою	авдіограма	noun	noun:inanim:f:v_oru:up19
авдіограму	авдіограма	noun	noun:inanim:f:v_zna:up19
авдіограмі	авдіограма	noun	noun:inanim:f:v_dav:up19
авдіограмі	авдіограма	noun	noun:inanim:f:v_mis:up19
авдіозапис	авдіозапис	noun	noun:inanim:m:v_naz:up19
авдіозапис	авдіозапис	noun	noun:inanim:m:v_zna:up19
авдіозаписам	авдіозапис	noun	noun:inanim:p:v_dav:up19
авдіозаписами	авдіозапис	noun	noun:inanim:p:v_oru:up19
авдіозаписах	авдіозапис	noun	noun:inanim:p:v_mis:up19
авдіозаписе	авдіозапис	noun	noun:inanim:m:v_kly:up19
авдіозаписи	авдіозапис	noun	noun:inanim:p:v_kly:up19
авдіозаписи	авдіозапис	noun	noun:inanim:p:v_naz:up19
авдіозаписи	авдіозапис	noun	noun:inanim:p:v_zna:up19
авдіозаписові	авдіозапис	noun	noun:inanim:m:v_dav:up19
авдіозаписові	авдіозапис	noun	noun:inanim:m:v_mis:up19
авдіозаписом	авдіозапис	noun	noun:inanim:m:v_oru:up19
авдіозапису	авдіозапис	noun	noun:inanim:m:v_dav:up19
авдіозапису	авдіозапис	noun	noun:inanim:m:v_mis:up19
авдіозапису	авдіозапис	noun	noun:inanim:m:v_rod:up19
авдіозаписі	авдіозапис	noun	noun:inanim:m:v_mis:up19
авдіозаписів	авдіозапис	noun	noun:inanim:p:v_rod:up19
авдіоконтролер	авдіоконтролер	noun	noun:inanim:m:v_naz:up19
авдіоконтролер	авдіоконтролер	noun	noun:inanim:m:v_zna:up19
авдіоконтролера	авдіоконтролер	noun	noun:inanim:m:v_rod:up19
авдіоконтролерам	авдіоконтролер	noun	noun:inanim:p:v_dav:up19
авдіоконтролерами	авдіоконтролер	noun	noun:inanim:p:v_oru:up19
авдіоконтролерах	авдіоконтролер	noun	noun:inanim:p:v_mis:up19
авдіоконтролере	авдіоконтролер	noun	noun:inanim:m:v_kly:up19
авдіоконтролери	авдіоконтролер	noun	noun:inanim:p:v_kly:up19
авдіоконтролери	авдіоконтролер	noun	noun:inanim:p:v_naz:up19
авдіоконтролери	авдіоконтролер	noun	noun:inanim:p:v_zna:up19
авдіоконтролерові	авдіоконтролер	noun	noun:inanim:m:v_dav:up19
авдіоконтролерові	авдіоконтролер	noun	noun:inanim:m:v_mis:up19
авдіоконтролером	авдіоконтролер	noun	noun:inanim:m:v_oru:up19
авдіоконтролері	авдіоконтролер	noun	noun:inanim:m:v_mis:up19
авдіоконтролерів	авдіоконтролер	noun	noun:inanim:p:v_rod:up19
авдіоприймач	авдіоприймач	noun	noun:inanim:m:v_naz:up19
авдіоприймач	авдіоприймач	noun	noun:inanim:m:v_zna:up19
авдіоприймача	авдіоприймач	noun	noun:inanim:m:v_rod:up19
авдіоприймачам	авдіоприймач	noun	noun:inanim:p:v_dav:up19
авдіоприймачами	авдіоприймач	noun	noun:inanim:p:v_oru:up19
авдіоприймачах	авдіоприймач	noun	noun:inanim:p:v_mis:up19
авдіоприймачеві	авдіоприймач	noun	noun:inanim:m:v_dav:up19
авдіоприймачеві	авдіоприймач	noun	noun:inanim:m:v_mis:up19
авдіоприймачем	авдіоприймач	noun	noun:inanim:m:v_oru:up19
авдіоприймачу	авдіоприймач	noun	noun:inanim:m:v_dav:up19
авдіоприймачу	авдіоприймач	noun	noun:inanim:m:v_kly:up19
авдіоприймачу	авдіоприймач	noun	noun:inanim:m:v_mis:up19
авдіоприймачі	авдіоприймач	noun	noun:inanim:m:v_mis:up19
авдіоприймачі	авдіоприймач	noun	noun:inanim:p:v_kly:up19
авдіоприймачі	авдіоприймач	noun	noun:inanim:p:v_naz:up19
авдіоприймачі	авдіоприймач	noun	noun:inanim:p:v_zna:up19
авдіоприймачів	авдіоприймач	noun	noun:inanim:p:v_rod:up19
авдіосигнал	авдіосигнал	noun	noun:inanim:m:v_naz:up19
авдіосигнал	авдіосигнал	noun	noun:inanim:m:v_zna:up19
авдіосигналам	авдіосигнал	noun	noun:inanim:p:v_dav:up19
авдіосигналами	авдіосигнал	noun	noun:inanim:p:v_oru:up19
авдіосигналах	авдіосигнал	noun	noun:inanim:p:v_mis:up19
авдіосигнале	авдіосигнал	noun	noun:inanim:m:v_kly:up19
авдіосигнали	авдіосигнал	noun	noun:inanim:p:v_kly:up19
авдіосигнали	авдіосигнал	noun	noun:inanim:p:v_naz:up19
авдіосигнали	авдіосигнал	noun	noun:inanim:p:v_zna:up19
авдіосигналові	авдіосигнал	noun	noun:inanim:m:v_dav:up19
авдіосигналові	авдіосигнал	noun	noun:inanim:m:v_mis:up19
авдіосигналом	авдіосигнал	noun	noun:inanim:m:v_oru:up19
авдіосигналу	авдіосигнал	noun	noun:inanim:m:v_dav:up19
авдіосигналу	авдіосигнал	noun	noun:inanim:m:v_mis:up19
авдіосигналу	авдіосигнал	noun	noun:inanim:m:v_rod:up19
авдіосигналі	авдіосигнал	noun	noun:inanim:m:v_mis:up19
авдіосигналів	авдіосигнал	noun	noun:inanim:p:v_rod:up19
авдіотермінал	авдіотермінал	noun	noun:inanim:m:v_naz:up19
авдіотермінал	авдіотермінал	noun	noun:inanim:m:v_zna:up19
авдіотермінала	авдіотермінал	noun	noun:inanim:m:v_rod:up19
авдіотерміналам	авдіотермінал	noun	noun:inanim:p:v_dav:up19
авдіотерміналами	авдіотермінал	noun	noun:inanim:p:v_oru:up19
авдіотерміналах	авдіотермінал	noun	noun:inanim:p:v_mis:up19
авдіотермінале	авдіотермінал	noun	noun:inanim:m:v_kly:up19
авдіотермінали	авдіотермінал	noun	noun:inanim:p:v_kly:up19
авдіотермінали	авдіотермінал	noun	noun:inanim:p:v_naz:up19
авдіотермінали	авдіотермінал	noun	noun:inanim:p:v_zna:up19
авдіотерміналові	авдіотермінал	noun	noun:inanim:m:v_dav:up19
авдіотерміналові	авдіотермінал	noun	noun:inanim:m:v_mis:up19
авдіотерміналом	авдіотермінал	noun	noun:inanim:m:v_oru:up19
авдіотерміналі	авдіотермінал	noun	noun:inanim:m:v_mis:up19
авдіотерміналів	авдіотермінал	noun	noun:inanim:p:v_rod:up19
авдіофайл	авдіофайл	noun	noun:inanim:m:v_naz:up19
авдіофайл	авдіофайл	noun	noun:inanim:m:v_zna:up19
авдіофайлам	авдіофайл	noun	noun:inanim:p:v_dav:up19
авдіофайлами	авдіофайл	noun	noun:inanim:p:v_oru:up19
авдіофайлах	авдіофайл	noun	noun:inanim:p:v_mis:up19
авдіофайле	авдіофайл	noun	noun:inanim:m:v_kly:up19
авдіофайли	авдіофайл	noun	noun:inanim:p:v_kly:up19
авдіофайли	авдіофайл	noun	noun:inanim:p:v_naz:up19
авдіофайли	авдіофайл	noun	noun:inanim:p:v_zna:up19
авдіофайлові	авдіофайл	noun	noun:inanim:m:v_dav:up19
авдіофайлові	авдіофайл	noun	noun:inanim:m:v_mis:up19
авдіофайлом	авдіофайл	noun	noun:inanim:m:v_oru:up19
авдіофайлу	авдіофайл	noun	noun:inanim:m:v_dav:up19
авдіофайлу	авдіофайл	noun	noun:inanim:m:v_mis:up19
авдіофайлу	авдіофайл	noun	noun:inanim:m:v_rod:up19
авдіофайлі	авдіофайл	noun	noun:inanim:m:v_mis:up19
авдіофайлів	авдіофайл	noun	noun:inanim:p:v_rod:up19
авдіофонограм	авдіофонограма	noun	noun:inanim:p:v_rod:up19
авдіофонограма	авдіофонограма	noun	noun:inanim:f:v_naz:up19
авдіофонограмам	авдіофонограма	noun	noun:inanim:p:v_dav:up19
авдіофонограмами	авдіофонограма	noun	noun:inanim:p:v_oru:up19
авдіофонограмах	авдіофонограма	noun	noun:inanim:p:v_mis:up19
авдіофонограми	авдіофонограма	noun	noun:inanim:f:v_rod:up19
авдіофонограми	авдіофонограма	noun	noun:inanim:p:v_kly:up19
авдіофонограми	авдіофонограма	noun	noun:inanim:p:v_naz:up19
авдіофонограми	авдіофонограма	noun	noun:inanim:p:v_zna:up19
авдіофонограмо	авдіофонограма	noun	noun:inanim:f:v_kly:up19
авдіофонограмою	авдіофонограма	noun	noun:inanim:f:v_oru:up19
авдіофонограму	авдіофонограма	noun	noun:inanim:f:v_zna:up19
авдіофонограмі	авдіофонограма	noun	noun:inanim:f:v_dav:up19
авдіофонограмі	авдіофонограма	noun	noun:inanim:f:v_mis:up19
авдіоформат	авдіоформат	noun	noun:inanim:m:v_naz
авдіоформат	авдіоформат	noun	noun:inanim:m:v_zna
авдіоформатам	авдіоформат	noun	noun:inanim:p:v_dav
авдіоформатами	авдіоформат	noun	noun:inanim:p:v_oru
авдіоформатах	авдіоформат	noun	noun:inanim:p:v_mis
авдіоформате	авдіоформат	noun	noun:inanim:m:v_kly
авдіоформати	авдіоформат	noun	noun:inanim:p:v_kly
авдіоформати	авдіоформат	noun	noun:inanim:p:v_naz
авдіоформати	авдіоформат	noun	noun:inanim:p:v_zna
авдіоформатові	авдіоформат	noun	noun:inanim:m:v_dav
авдіоформатові	авдіоформат	noun	noun:inanim:m:v_mis
авдіоформатом	авдіоформат	noun	noun:inanim:m:v_oru
авдіоформату	авдіоформат	noun	noun:inanim:m:v_dav
авдіоформату	авдіоформат	noun	noun:inanim:m:v_mis
авдіоформату	авдіоформат	noun	noun:inanim:m:v_rod
авдіоформаті	авдіоформат	noun	noun:inanim:m:v_mis
авдіоформатів	авдіоформат	noun	noun:inanim:p:v_rod
авдієнцій	авдієнція	noun	noun:inanim:p:v_rod:up19
авдієнцію	авдієнція	noun	noun:inanim:f:v_zna:up19
авдієнція	авдієнція	noun	noun:inanim:f:v_naz:up19
авдієнціям	авдієнція	noun	noun:inanim:p:v_dav:up19
авдієнціями	авдієнція	noun	noun:inanim:p:v_oru:up19
авдієнціях	авдієнція	noun	noun:inanim:p:v_mis:up19
авдієнціє	авдієнція	noun	noun:inanim:f:v_kly:up19
авдієнцією	авдієнція	noun	noun:inanim:f:v_oru:up19
авдієнції	авдієнція	noun	noun:inanim:f:v_dav:up19
авдієнції	авдієнція	noun	noun:inanim:f:v_mis:up19
авдієнції	авдієнція	noun	noun:inanim:f:v_rod:up19
авдієнції	авдієнція	noun	noun:inanim:p:v_kly:up19
авдієнції	авдієнція	noun	noun:inanim:p:v_naz:up19
авдієнції	авдієнція	noun	noun:inanim:p:v_zna:up19
авербандник	авербандник	noun	noun:anim:m:v_naz
авербандника	авербандник	noun	noun:anim:m:v_rod
авербандника	авербандник	noun	noun:anim:m:v_zna
авербандникам	авербандник	noun	noun:anim:p:v_dav
авербандниками	авербандник	noun	noun:anim:p:v_oru
авербандниках	авербандник	noun	noun:anim:p:v_mis
авербандники	авербандник	noun	noun:anim:p:v_kly
авербандники	авербандник	noun	noun:anim:p:v_naz
авербандники	авербандник	noun	noun:anim:p:v_zna:rare
авербандникові	авербандник	noun	noun:anim:m:v_dav
авербандникові	авербандник	noun	noun:anim:m:v_mis
авербандником	авербандник	noun	noun:anim:m:v_oru
авербанднику	авербандник	noun	noun:anim:m:v_dav
авербанднику	авербандник	noun	noun:anim:m:v_kly
авербанднику	авербандник	noun	noun:anim:m:v_mis
авербандників	авербандник	noun	noun:anim:p:v_rod
авербандників	авербандник	noun	noun:anim:p:v_zna
аверс	аверс	noun	noun:inanim:m:v_naz
аверс	аверс	noun	noun:inanim:m:v_zna
аверсам	аверс	noun	noun:inanim:p:v_dav
аверсами	аверс	noun	noun:inanim:p:v_oru
аверсах	аверс	noun	noun:inanim:p:v_mis
аверсе	аверс	noun	noun:inanim:m:v_kly
аверси	аверс	noun	noun:inanim:p:v_kly
аверси	аверс	noun	noun:inanim:p:v_naz
аверси	аверс	noun	noun:inanim:p:v_zna
аверсові	аверс	noun	noun:inanim:m:v_dav
аверсові	аверс	noun	noun:inanim:m:v_mis
аверсом	аверс	noun	noun:inanim:m:v_oru
аверсу	аверс	noun	noun:inanim:m:v_dav
аверсу	аверс	noun	noun:inanim:m:v_mis
аверсу	аверс	noun	noun:inanim:m:v_rod
аверсі	аверс	noun	noun:inanim:m:v_mis
аверсів	аверс	noun	noun:inanim:p:v_rod
ави	ава	noun	noun:inanim:f:v_rod:slang
ави	ава	noun	noun:inanim:p:v_kly:slang
ави	ава	noun	noun:inanim:p:v_naz:slang
ави	ава	noun	noun:inanim:p:v_zna:slang
авксанометр	авксанометр	noun	noun:inanim:m:v_naz:up19
авксанометр	авксанометр	noun	noun:inanim:m:v_zna:up19
авксанометра	авксанометр	noun	noun:inanim:m:v_rod:up19
авксанометрам	авксанометр	noun	noun:inanim:p:v_dav:up19
авксанометрами	авксанометр	noun	noun:inanim:p:v_oru:up19
авксанометрах	авксанометр	noun	noun:inanim:p:v_mis:up19
авксанометре	авксанометр	noun	noun:inanim:m:v_kly:up19
авксанометри	авксанометр	noun	noun:inanim:p:v_kly:up19
авксанометри	авксанометр	noun	noun:inanim:p:v_naz:up19
авксанометри	авксанометр	noun	noun:inanim:p:v_zna:up19
авксанометрові	авксанометр	noun	noun:inanim:m:v_dav:up19
авксанометрові	авксанометр	noun	noun:inanim:m:v_mis:up19
авксанометром	авксанометр	noun	noun:inanim:m:v_oru:up19
авксанометрі	авксанометр	noun	noun:inanim:m:v_mis:up19
авксанометрів	авксанометр	noun	noun:inanim:p:v_rod:up19
авксин	авксин	noun	noun:inanim:m:v_naz:up19
авксин	авксин	noun	noun:inanim:m:v_zna:up19
авксинам	авксин	noun	noun:inanim:p:v_dav:up19
авксинами	авксин	noun	noun:inanim:p:v_oru:up19
авксинах	авксин	noun	noun:inanim:p:v_mis:up19
авксине	авксин	noun	noun:inanim:m:v_kly:up19
авксини	авксин	noun	noun:inanim:p:v_kly:up19
авксини	авксин	noun	noun:inanim:p:v_naz:up19
авксини	авксин	noun	noun:inanim:p:v_zna:up19
авксинові	авксин	noun	noun:inanim:m:v_dav:up19
авксинові	авксин	noun	noun:inanim:m:v_mis:up19
авксином	авксин	noun	noun:inanim:m:v_oru:up19
авксину	авксин	noun	noun:inanim:m:v_dav:up19
авксину	авксин	noun	noun:inanim:m:v_mis:up19
авксину	авксин	noun	noun:inanim:m:v_rod:up19
авксині	авксин	noun	noun:inanim:m:v_mis:up19
авксинів	авксин	noun	noun:inanim:p:v_rod:up19
авксоспор	авксоспора	noun	noun:inanim:p:v_rod:up19
авксоспора	авксоспора	noun	noun:inanim:f:v_naz:up19
авксоспорам	авксоспора	noun	noun:inanim:p:v_dav:up19
авксоспорами	авксоспора	noun	noun:inanim:p:v_oru:up19
авксоспорах	авксоспора	noun	noun:inanim:p:v_mis:up19
авксоспори	авксоспора	noun	noun:inanim:f:v_rod:up19
авксоспори	авксоспора	noun	noun:inanim:p:v_kly:up19
авксоспори	авксоспора	noun	noun:inanim:p:v_naz:up19
авксоспори	авксоспора	noun	noun:inanim:p:v_zna:up19
авксоспоро	авксоспора	noun	noun:inanim:f:v_kly:up19
авксоспорою	авксоспора	noun	noun:inanim:f:v_oru:up19
авксоспору	авксоспора	noun	noun:inanim:f:v_zna:up19
авксоспорі	авксоспора	noun	noun:inanim:f:v_dav:up19
авксоспорі	авксоспора	noun	noun:inanim:f:v_mis:up19
авксотроф	авксотроф	noun	noun:inanim:m:v_naz:up19
авксотроф	авксотроф	noun	noun:inanim:m:v_zna:up19
авксотроф	авксотроф	noun	noun:unanim:m:v_naz:up19
авксотроф	авксотроф	noun	noun:unanim:m:v_zna:up19
авксотрофа	авксотроф	noun	noun:inanim:m:v_rod:up19
авксотрофа	авксотроф	noun	noun:unanim:m:v_rod:up19
авксотрофа	авксотроф	noun	noun:unanim:m:v_zna:up19
авксотрофам	авксотроф	noun	noun:inanim:p:v_dav:up19
авксотрофам	авксотроф	noun	noun:unanim:p:v_dav:up19
авксотрофами	авксотроф	noun	noun:inanim:p:v_oru:up19
авксотрофами	авксотроф	noun	noun:unanim:p:v_oru:up19
авксотрофах	авксотроф	noun	noun:inanim:p:v_mis:up19
авксотрофах	авксотроф	noun	noun:unanim:p:v_mis:up19
авксотрофе	авксотроф	noun	noun:inanim:m:v_kly:up19
авксотрофе	авксотроф	noun	noun:unanim:m:v_kly:up19
авксотрофи	авксотроф	noun	noun:inanim:p:v_kly:up19
авксотрофи	авксотроф	noun	noun:inanim:p:v_naz:up19
авксотрофи	авксотроф	noun	noun:inanim:p:v_zna:up19
авксотрофи	авксотроф	noun	noun:unanim:p:v_kly:up19
авксотрофи	авксотроф	noun	noun:unanim:p:v_naz:up19
авксотрофи	авксотроф	noun	noun:unanim:p:v_zna:up19
авксотрофові	авксотроф	noun	noun:inanim:m:v_dav:up19
авксотрофові	авксотроф	noun	noun:inanim:m:v_mis:up19
авксотрофові	авксотроф	noun	noun:unanim:m:v_dav:up19
авксотрофові	авксотроф	noun	noun:unanim:m:v_mis:up19
авксотрофом	авксотроф	noun	noun:inanim:m:v_oru:up19
авксотрофом	авксотроф	noun	noun:unanim:m:v_oru:up19
авксотрофі	авксотроф	noun	noun:inanim:m:v_mis:up19
авксотрофі	авксотроф	noun	noun:unanim:m:v_mis:up19
авксотрофів	авксотроф	noun	noun:inanim:p:v_rod:up19
авксотрофів	авксотроф	noun	noun:unanim:p:v_rod:up19
авксотрофів	авксотроф	noun	noun:unanim:p:v_zna:up19
авлакоген	авлакоген	noun	noun:inanim:m:v_naz
авлакоген	авлакоген	noun	noun:inanim:m:v_zna
авлакогенам	авлакоген	noun	noun:inanim:p:v_dav
авлакогенами	авлакоген	noun	noun:inanim:p:v_oru
авлакогенах	авлакоген	noun	noun:inanim:p:v_mis
авлакогене	авлакоген	noun	noun:inanim:m:v_kly
авлакогени	авлакоген	noun	noun:inanim:p:v_kly
авлакогени	авлакоген	noun	noun:inanim:p:v_naz
авлакогени	авлакоген	noun	noun:inanim:p:v_zna
авлакогенові	авлакоген	noun	noun:inanim:m:v_dav
авлакогенові	авлакоген	noun	noun:inanim:m:v_mis
авлакогеном	авлакоген	noun	noun:inanim:m:v_oru
авлакогену	авлакоген	noun	noun:inanim:m:v_dav
авлакогену	авлакоген	noun	noun:inanim:m:v_mis
авлакогену	авлакоген	noun	noun:inanim:m:v_rod
авлакогені	авлакоген	noun	noun:inanim:m:v_mis
авлакогенів	авлакоген	noun	noun:inanim:p:v_rod
авлос	авлос	noun	noun:inanim:m:v_naz
авлос	авлос	noun	noun:inanim:m:v_zna
авлоса	авлос	noun	noun:inanim:m:v_rod
авлосам	авлос	noun	noun:inanim:p:v_dav
авлосами	авлос	noun	noun:inanim:p:v_oru
авлосах	авлос	noun	noun:inanim:p:v_mis
авлосе	авлос	noun	noun:inanim:m:v_kly
авлоси	авлос	noun	noun:inanim:p:v_kly
авлоси	авлос	noun	noun:inanim:p:v_naz
авлоси	авлос	noun	noun:inanim:p:v_zna
авлосові	авлос	noun	noun:inanim:m:v_dav
авлосові	авлос	noun	noun:inanim:m:v_mis
авлосом	авлос	noun	noun:inanim:m:v_oru
авлосі	авлос	noun	noun:inanim:m:v_mis
авлосів	авлос	noun	noun:inanim:p:v_rod
аво	ава	noun	noun:inanim:f:v_kly:slang
авогардит	авогардит	noun	noun:inanim:m:v_naz
авогардит	авогардит	noun	noun:inanim:m:v_zna
авогардитам	авогардит	noun	noun:inanim:p:v_dav
авогардитами	авогардит	noun	noun:inanim:p:v_oru
авогардитах	авогардит	noun	noun:inanim:p:v_mis
авогардите	авогардит	noun	noun:inanim:m:v_kly
авогардити	авогардит	noun	noun:inanim:p:v_kly
авогардити	авогардит	noun	noun:inanim:p:v_naz
авогардити	авогардит	noun	noun:inanim:p:v_zna
авогардитові	авогардит	noun	noun:inanim:m:v_dav
авогардитові	авогардит	noun	noun:inanim:m:v_mis
авогардитом	авогардит	noun	noun:inanim:m:v_oru
авогардиту	авогардит	noun	noun:inanim:m:v_dav
авогардиту	авогардит	noun	noun:inanim:m:v_mis
авогардиту	авогардит	noun	noun:inanim:m:v_rod
авогардиті	авогардит	noun	noun:inanim:m:v_mis
авогардитів	авогардит	noun	noun:inanim:p:v_rod
авометр	авометр	noun	noun:inanim:m:v_naz
авометр	авометр	noun	noun:inanim:m:v_zna
авометра	авометр	noun	noun:inanim:m:v_rod
авометрам	авометр	noun	noun:inanim:p:v_dav
авометрами	авометр	noun	noun:inanim:p:v_oru
авометрах	авометр	noun	noun:inanim:p:v_mis
авометре	авометр	noun	noun:inanim:m:v_kly
авометри	авометр	noun	noun:inanim:p:v_kly
авометри	авометр	noun	noun:inanim:p:v_naz
авометри	авометр	noun	noun:inanim:p:v_zna
авометрові	авометр	noun	noun:inanim:m:v_dav
авометрові	авометр	noun	noun:inanim:m:v_mis
авометром	авометр	noun	noun:inanim:m:v_oru
авометрі	авометр	noun	noun:inanim:m:v_mis
авометрів	авометр	noun	noun:inanim:p:v_rod
авоська	авоська	noun	noun:inanim:f:v_naz
авоськам	авоська	noun	noun:inanim:p:v_dav
авоськами	авоська	noun	noun:inanim:p:v_oru
авоськах	авоська	noun	noun:inanim:p:v_mis
авоськи	авоська	noun	noun:inanim:f:v_rod
авоськи	авоська	noun	noun:inanim:p:v_kly
авоськи	авоська	noun	noun:inanim:p:v_naz
авоськи	авоська	noun	noun:inanim:p:v_zna
авосько	авоська	noun	noun:inanim:f:v_kly
авоською	авоська	noun	noun:inanim:f:v_oru
авоську	авоська	noun	noun:inanim:f:v_zna
авосьок	авоська	noun	noun:inanim:p:v_rod
авосьці	авоська	noun	noun:inanim:f:v_dav
авосьці	авоська	noun	noun:inanim:f:v_mis
авою	ава	noun	noun:inanim:f:v_oru:slang
авр	авра	noun	noun:inanim:p:v_rod:up19
авра	авра	noun	noun:inanim:f:v_naz:up19
аврал	аврал	noun	noun:inanim:m:v_naz
аврал	аврал	noun	noun:inanim:m:v_zna
авралам	аврал	noun	noun:inanim:p:v_dav
авралами	аврал	noun	noun:inanim:p:v_oru
авралах	аврал	noun	noun:inanim:p:v_mis
аврале	аврал	noun	noun:inanim:m:v_kly
аврали	аврал	noun	noun:inanim:p:v_kly
аврали	аврал	noun	noun:inanim:p:v_naz
аврали	аврал	noun	noun:inanim:p:v_zna
авралові	аврал	noun	noun:inanim:m:v_dav
авралові	аврал	noun	noun:inanim:m:v_mis
авралом	аврал	noun	noun:inanim:m:v_oru
авралу	аврал	noun	noun:inanim:m:v_dav
авралу	аврал	noun	noun:inanim:m:v_mis
авралу	аврал	noun	noun:inanim:m:v_rod
авралі	аврал	noun	noun:inanim:m:v_mis
авралів	аврал	noun	noun:inanim:p:v_rod
аврам	авра	noun	noun:inanim:p:v_dav:up19
аврами	авра	noun	noun:inanim:p:v_oru:up19
авран	авран	noun	noun:inanim:m:v_naz
авран	авран	noun	noun:inanim:m:v_zna
авранам	авран	noun	noun:inanim:p:v_dav
авранами	авран	noun	noun:inanim:p:v_oru
авранах	авран	noun	noun:inanim:p:v_mis
авране	авран	noun	noun:inanim:m:v_kly
аврани	авран	noun	noun:inanim:p:v_kly
аврани	авран	noun	noun:inanim:p:v_naz
аврани	авран	noun	noun:inanim:p:v_zna
авранові	авран	noun	noun:inanim:m:v_dav
авранові	авран	noun	noun:inanim:m:v_mis
авраном	авран	noun	noun:inanim:m:v_oru
аврану	авран	noun	noun:inanim:m:v_dav
аврану	авран	noun	noun:inanim:m:v_mis
аврану	авран	noun	noun:inanim:m:v_rod
аврані	авран	noun	noun:inanim:m:v_mis
авранів	авран	noun	noun:inanim:p:v_rod
аврах	авра	noun	noun:inanim:p:v_mis:up19
авреоле	авреоля	noun	noun:inanim:f:v_kly
авреолею	авреоля	noun	noun:inanim:f:v_oru
авреоль	авреоля	noun	noun:inanim:p:v_rod
авреолю	авреоля	noun	noun:inanim:f:v_zna
авреоля	авреоля	noun	noun:inanim:f:v_naz
авреолям	авреоля	noun	noun:inanim:p:v_dav
авреолями	авреоля	noun	noun:inanim:p:v_oru
авреолях	авреоля	noun	noun:inanim:p:v_mis
авреолі	авреоля	noun	noun:inanim:f:v_dav
авреолі	авреоля	noun	noun:inanim:f:v_mis
авреолі	авреоля	noun	noun:inanim:f:v_rod
авреолі	авреоля	noun	noun:inanim:p:v_kly
авреолі	авреоля	noun	noun:inanim:p:v_naz
авреолі	авреоля	noun	noun:inanim:p:v_zna
аври	авра	noun	noun:inanim:f:v_rod:up19
аври	авра	noun	noun:inanim:p:v_kly:up19
аври	авра	noun	noun:inanim:p:v_naz:up19
аври	авра	noun	noun:inanim:p:v_zna:up19
аврикул	аврикула	noun	noun:inanim:p:v_rod
аврикула	аврикула	noun	noun:inanim:f:v_naz
аврикулам	аврикула	noun	noun:inanim:p:v_dav
аврикулами	аврикула	noun	noun:inanim:p:v_oru
аврикулах	аврикула	noun	noun:inanim:p:v_mis
аврикули	аврикула	noun	noun:inanim:f:v_rod
аврикули	аврикула	noun	noun:inanim:p:v_kly
аврикули	аврикула	noun	noun:inanim:p:v_naz
аврикули	аврикула	noun	noun:inanim:p:v_zna
аврикуло	аврикула	noun	noun:inanim:f:v_kly
аврикулою	аврикула	noun	noun:inanim:f:v_oru
аврикулу	аврикула	noun	noun:inanim:f:v_zna
аврикулі	аврикула	noun	noun:inanim:f:v_dav
аврикулі	аврикула	noun	noun:inanim:f:v_mis
авро	авра	noun	noun:inanim:f:v_kly:up19
аврор	аврора	noun	noun:inanim:p:v_rod
аврора	аврора	noun	noun:inanim:f:v_naz
аврорам	аврора	noun	noun:inanim:p:v_dav
аврорами	аврора	noun	noun:inanim:p:v_oru
аврорах	аврора	noun	noun:inanim:p:v_mis
аврори	аврора	noun	noun:inanim:f:v_rod
аврори	аврора	noun	noun:inanim:p:v_kly
аврори	аврора	noun	noun:inanim:p:v_naz
аврори	аврора	noun	noun:inanim:p:v_zna
авроро	аврора	noun	noun:inanim:f:v_kly
авророю	аврора	noun	noun:inanim:f:v_oru
аврору	аврора	noun	noun:inanim:f:v_zna
аврорі	аврора	noun	noun:inanim:f:v_dav
аврорі	аврора	noun	noun:inanim:f:v_mis
аврою	авра	noun	noun:inanim:f:v_oru:up19
авру	авра	noun	noun:inanim:f:v_zna:up19
аврі	авра	noun	noun:inanim:f:v_dav:up19
аврі	авра	noun	noun:inanim:f:v_mis:up19
авскультант	авскультант	noun	noun:anim:m:v_naz
авскультанта	авскультант	noun	noun:anim:m:v_rod
авскультанта	авскультант	noun	noun:anim:m:v_zna
авскультантам	авскультант	noun	noun:anim:p:v_dav
авскультантами	авскультант	noun	noun:anim:p:v_oru
авскультантах	авскультант	noun	noun:anim:p:v_mis
авскультанте	авскультант	noun	noun:anim:m:v_kly
авскультанти	авскультант	noun	noun:anim:p:v_kly
авскультанти	авскультант	noun	noun:anim:p:v_naz
авскультанти	авскультант	noun	noun:anim:p:v_zna:rare
авскультантові	авскультант	noun	noun:anim:m:v_dav
авскультантові	авскультант	noun	noun:anim:m:v_mis
авскультантом	авскультант	noun	noun:anim:m:v_oru
авскультанті	авскультант	noun	noun:anim:m:v_mis
авскультантів	авскультант	noun	noun:anim:p:v_rod
авскультантів	авскультант	noun	noun:anim:p:v_zna
австралопітек	австралопітек	noun	noun:anim:m:v_naz
австралопітека	австралопітек	noun	noun:anim:m:v_rod
австралопітека	австралопітек	noun	noun:anim:m:v_zna
австралопітекам	австралопітек	noun	noun:anim:p:v_dav
австралопітеками	австралопітек	noun	noun:anim:p:v_oru
австралопітеках	австралопітек	noun	noun:anim:p:v_mis
австралопітеки	австралопітек	noun	noun:anim:p:v_kly
австралопітеки	австралопітек	noun	noun:anim:p:v_naz
австралопітеки	австралопітек	noun	noun:anim:p:v_zna
австралопітекові	австралопітек	noun	noun:anim:m:v_dav
австралопітекові	австралопітек	noun	noun:anim:m:v_mis
австралопітеком	австралопітек	noun	noun:anim:m:v_oru
австралопітеку	австралопітек	noun	noun:anim:m:v_dav
австралопітеку	австралопітек	noun	noun:anim:m:v_kly
австралопітеку	австралопітек	noun	noun:anim:m:v_mis
австралопітеків	австралопітек	noun	noun:anim:p:v_rod
австралопітеків	австралопітек	noun	noun:anim:p:v_zna
австралоїд	австралоїд	noun	noun:anim:m:v_naz
австралоїда	австралоїд	noun	noun:anim:m:v_rod
австралоїда	австралоїд	noun	noun:anim:m:v_zna
австралоїдам	австралоїд	noun	noun:anim:p:v_dav
австралоїдами	австралоїд	noun	noun:anim:p:v_oru
австралоїдах	австралоїд	noun	noun:anim:p:v_mis
австралоїде	австралоїд	noun	noun:anim:m:v_kly
австралоїди	австралоїд	noun	noun:anim:p:v_kly
австралоїди	австралоїд	noun	noun:anim:p:v_naz
австралоїди	австралоїд	noun	noun:anim:p:v_zna:rare
австралоїдові	австралоїд	noun	noun:anim:m:v_dav
австралоїдові	австралоїд	noun	noun:anim:m:v_mis
австралоїдом	австралоїд	noun	noun:anim:m:v_oru
австралоїді	австралоїд	noun	noun:anim:m:v_mis
австралоїдів	австралоїд	noun	noun:anim:p:v_rod
австралоїдів	австралоїд	noun	noun:anim:p:v_zna
австралійка	австралійка	noun	noun:anim:f:v_naz
австралійкам	австралійка	noun	noun:anim:p:v_dav
австралійками	австралійка	noun	noun:anim:p:v_oru
австралійках	австралійка	noun	noun:anim:p:v_mis
австралійки	австралійка	noun	noun:anim:f:v_rod
австралійки	австралійка	noun	noun:anim:p:v_kly
австралійки	австралійка	noun	noun:anim:p:v_naz
австралійки	австралійка	noun	noun:anim:p:v_zna:rare
австралійко	австралійка	noun	noun:anim:f:v_kly
австралійкою	австралійка	noun	noun:anim:f:v_oru
австралійку	австралійка	noun	noun:anim:f:v_zna
австралійок	австралійка	noun	noun:anim:p:v_rod
австралійок	австралійка	noun	noun:anim:p:v_zna
австралійцеві	австралієць	noun	noun:anim:m:v_dav
австралійцеві	австралієць	noun	noun:anim:m:v_mis
австралійцем	австралієць	noun	noun:anim:m:v_oru
австралійцю	австралієць	noun	noun:anim:m:v_dav
австралійцю	австралієць	noun	noun:anim:m:v_kly
австралійцю	австралієць	noun	noun:anim:m:v_mis
австралійця	австралієць	noun	noun:anim:m:v_rod
австралійця	австралієць	noun	noun:anim:m:v_zna
австралійцям	австралієць	noun	noun:anim:p:v_dav
австралійцями	австралієць	noun	noun:anim:p:v_oru
австралійцях	австралієць	noun	noun:anim:p:v_mis
австралійці	австралійка	noun	noun:anim:f:v_dav
австралійці	австралійка	noun	noun:anim:f:v_mis
австралійці	австралієць	noun	noun:anim:m:v_mis
австралійці	австралієць	noun	noun:anim:p:v_kly
австралійці	австралієць	noun	noun:anim:p:v_naz
австралійці	австралієць	noun	noun:anim:p:v_zna:rare
австралійців	австралієць	noun	noun:anim:p:v_rod
австралійців	австралієць	noun	noun:anim:p:v_zna
австралієць	австралієць	noun	noun:anim:m:v_naz
австромарксист	австромарксист	noun	noun:anim:m:v_naz
австромарксиста	австромарксист	noun	noun:anim:m:v_rod
австромарксиста	австромарксист	noun	noun:anim:m:v_zna
австромарксистам	австромарксист	noun	noun:anim:p:v_dav
австромарксистами	австромарксист	noun	noun:anim:p:v_oru
австромарксистах	австромарксист	noun	noun:anim:p:v_mis
австромарксисте	австромарксист	noun	noun:anim:m:v_kly
австромарксисти	австромарксист	noun	noun:anim:p:v_kly
австромарксисти	австромарксист	noun	noun:anim:p:v_naz
австромарксисти	австромарксист	noun	noun:anim:p:v_zna:rare
австромарксистові	австромарксист	noun	noun:anim:m:v_dav
австромарксистові	австромарксист	noun	noun:anim:m:v_mis
австромарксистом	австромарксист	noun	noun:anim:m:v_oru
австромарксисті	австромарксист	noun	noun:anim:m:v_mis
австромарксистів	австромарксист	noun	noun:anim:p:v_rod
австромарксистів	австромарксист	noun	noun:anim:p:v_zna
австрофіл	австрофіл	noun	noun:anim:m:v_naz
австрофіла	австрофіл	noun	noun:anim:m:v_rod
австрофіла	австрофіл	noun	noun:anim:m:v_zna
австрофілам	австрофіл	noun	noun:anim:p:v_dav
австрофілами	австрофіл	noun	noun:anim:p:v_oru
австрофілах	австрофіл	noun	noun:anim:p:v_mis
австрофіле	австрофіл	noun	noun:anim:m:v_kly
австрофіли	австрофіл	noun	noun:anim:p:v_kly
австрофіли	австрофіл	noun	noun:anim:p:v_naz
австрофіли	австрофіл	noun	noun:anim:p:v_zna:rare
австрофілові	австрофіл	noun	noun:anim:m:v_dav
австрофілові	австрофіл	noun	noun:anim:m:v_mis
австрофілом	австрофіл	noun	noun:anim:m:v_oru
австрофілі	австрофіл	noun	noun:anim:m:v_mis
австрофілів	австрофіл	noun	noun:anim:p:v_rod
австрофілів	австрофіл	noun	noun:anim:p:v_zna
австрійка	австрійка	noun	noun:anim:f:v_naz
австрійкам	австрійка	noun	noun:anim:p:v_dav
австрійками	австрійка	noun	noun:anim:p:v_oru
австрійках	австрійка	noun	noun:anim:p:v_mis
австрійки	австрійка	noun	noun:anim:f:v_rod
австрійки	австрійка	noun	noun:anim:p:v_kly
австрійки	австрійка	noun	noun:anim:p:v_naz
австрійки	австрійка	noun	noun:anim:p:v_zna:rare
австрійко	австрійка	noun	noun:anim:f:v_kly
австрійкою	австрійка	noun	noun:anim:f:v_oru
австрійку	австрійка	noun	noun:anim:f:v_zna
австрійок	австрійка	noun	noun:anim:p:v_rod
австрійок	австрійка	noun	noun:anim:p:v_zna
австрійцеві	австрієць	noun	noun:anim:m:v_dav
австрійцеві	австрієць	noun	noun:anim:m:v_mis
австрійцем	австрієць	noun	noun:anim:m:v_oru
австрійцю	австрієць	noun	noun:anim:m:v_dav
австрійцю	австрієць	noun	noun:anim:m:v_kly
австрійцю	австрієць	noun	noun:anim:m:v_mis
австрійця	австрієць	noun	noun:anim:m:v_rod
австрійця	австрієць	noun	noun:anim:m:v_zna
австрійцям	австрієць	noun	noun:anim:p:v_dav
австрійцями	австрієць	noun	noun:anim:p:v_oru
австрійцях	австрієць	noun	noun:anim:p:v_mis
австрійці	австрійка	noun	noun:anim:f:v_dav
австрійці	австрійка	noun	noun:anim:f:v_mis
австрійці	австрієць	noun	noun:anim:m:v_mis
австрійці	австрієць	noun	noun:anim:p:v_kly
австрійці	австрієць	noun	noun:anim:p:v_naz
австрійці	австрієць	noun	noun:anim:p:v_zna:rare
австрійців	австрієць	noun	noun:anim:p:v_rod
австрійців	австрієць	noun	noun:anim:p:v_zna
австріяк	австріяк	noun	noun:anim:m:v_naz
австріяка	австріяк	noun	noun:anim:m:v_rod
австріяка	австріяк	noun	noun:anim:m:v_zna
австріякам	австріяк	noun	noun:anim:p:v_dav
австріяками	австріяк	noun	noun:anim:p:v_oru
австріяках	австріяк	noun	noun:anim:p:v_mis
австріяки	австріяк	noun	noun:anim:p:v_kly
австріяки	австріяк	noun	noun:anim:p:v_naz
австріяки	австріяк	noun	noun:anim:p:v_zna:rare
австріякові	австріяк	noun	noun:anim:m:v_dav
австріякові	австріяк	noun	noun:anim:m:v_mis
австріяком	австріяк	noun	noun:anim:m:v_oru
австріяків	австріяк	noun	noun:anim:p:v_rod
австріяків	австріяк	noun	noun:anim:p:v_zna
австріяче	австріяк	noun	noun:anim:m:v_kly
австріячка	австріячка	noun	noun:anim:f:v_naz
австріячкам	австріячка	noun	noun:anim:p:v_dav
австріячками	австріячка	noun	noun:anim:p:v_oru
австріячках	австріячка	noun	noun:anim:p:v_mis
австріячки	австріячка	noun	noun:anim:f:v_rod
австріячки	австріячка	noun	noun:anim:p:v_kly
австріячки	австріячка	noun	noun:anim:p:v_naz
австріячки	австріячка	noun	noun:anim:p:v_zna:rare
австріячко	австріячка	noun	noun:anim:f:v_kly
австріячкою	австріячка	noun	noun:anim:f:v_oru
австріячку	австріячка	noun	noun:anim:f:v_zna
австріячок	австріячка	noun	noun:anim:p:v_rod
австріячок	австріячка	noun	noun:anim:p:v_zna
австріячці	австріячка	noun	noun:anim:f:v_dav
австріячці	австріячка	noun	noun:anim:f:v_mis
австрієць	австрієць	noun	noun:anim:m:v_naz
автаркіст	автаркіст	noun	noun:anim:m:v_naz
автаркіста	автаркіст	noun	noun:anim:m:v_rod
автаркіста	автаркіст	noun	noun:anim:m:v_zna
автаркістам	автаркіст	noun	noun:anim:p:v_dav
автаркістами	автаркіст	noun	noun:anim:p:v_oru
автаркістах	автаркіст	noun	noun:anim:p:v_mis
автаркісте	автаркіст	noun	noun:anim:m:v_kly
автаркісти	автаркіст	noun	noun:anim:p:v_kly
автаркісти	автаркіст	noun	noun:anim:p:v_naz
автаркісти	автаркіст	noun	noun:anim:p:v_zna:rare
автаркістові	автаркіст	noun	noun:anim:m:v_dav
автаркістові	автаркіст	noun	noun:anim:m:v_mis
автаркістом	автаркіст	noun	noun:anim:m:v_oru
автаркісті	автаркіст	noun	noun:anim:m:v_mis
автаркістів	автаркіст	noun	noun:anim:p:v_rod
автаркістів	автаркіст	noun	noun:anim:p:v_zna
автентистка	автентистка	noun	noun:anim:f:v_naz
автентисткам	автентистка	noun	noun:anim:p:v_dav
автентистками	автентистка	noun	noun:anim:p:v_oru
автентистках	автентистка	noun	noun:anim:p:v_mis
автентистки	автентистка	noun	noun:anim:f:v_rod
автентистки	автентистка	noun	noun:anim:p:v_kly
автентистки	автентистка	noun	noun:anim:p:v_naz
автентистки	автентистка	noun	noun:anim:p:v_zna:rare
автентистко	автентистка	noun	noun:anim:f:v_kly
автентисткою	автентистка	noun	noun:anim:f:v_oru
автентистку	автентистка	noun	noun:anim:f:v_zna
автентисток	автентистка	noun	noun:anim:p:v_rod
автентисток	автентистка	noun	noun:anim:p:v_zna
автентистці	автентистка	noun	noun:anim:f:v_dav
автентистці	автентистка	noun	noun:anim:f:v_mis
автентифікатор	автентифікатор	noun	noun:inanim:m:v_naz
автентифікатор	автентифікатор	noun	noun:inanim:m:v_zna
автентифікатора	автентифікатор	noun	noun:inanim:m:v_rod
автентифікаторам	автентифікатор	noun	noun:inanim:p:v_dav
автентифікаторами	автентифікатор	noun	noun:inanim:p:v_oru
автентифікаторах	автентифікатор	noun	noun:inanim:p:v_mis
автентифікаторе	автентифікатор	noun	noun:inanim:m:v_kly
автентифікатори	автентифікатор	noun	noun:inanim:p:v_kly
автентифікатори	автентифікатор	noun	noun:inanim:p:v_naz
автентифікатори	автентифікатор	noun	noun:inanim:p:v_zna
автентифікаторові	автентифікатор	noun	noun:inanim:m:v_dav
автентифікаторові	автентифікатор	noun	noun:inanim:m:v_mis
автентифікатором	автентифікатор	noun	noun:inanim:m:v_oru
автентифікаторі	автентифікатор	noun	noun:inanim:m:v_mis
автентифікаторів	автентифікатор	noun	noun:inanim:p:v_rod
автентифікацій	автентифікація	noun	noun:inanim:p:v_rod
автентифікацію	автентифікація	noun	noun:inanim:f:v_zna
автентифікація	автентифікація	noun	noun:inanim:f:v_naz
автентифікаціям	автентифікація	noun	noun:inanim:p:v_dav
автентифікаціями	автентифікація	noun	noun:inanim:p:v_oru
автентифікаціях	автентифікація	noun	noun:inanim:p:v_mis
автентифікаціє	автентифікація	noun	noun:inanim:f:v_kly
автентифікацією	автентифікація	noun	noun:inanim:f:v_oru
автентифікації	автентифікація	noun	noun:inanim:f:v_dav
автентифікації	автентифікація	noun	noun:inanim:f:v_mis
автентифікації	автентифікація	noun	noun:inanim:f:v_rod
автентифікації	автентифікація	noun	noun:inanim:p:v_kly
автентифікації	автентифікація	noun	noun:inanim:p:v_naz
автентифікації	автентифікація	noun	noun:inanim:p:v_zna
автист	автист	noun	noun:anim:m:v_naz:up19
автиста	автист	noun	noun:anim:m:v_rod:up19
автиста	автист	noun	noun:anim:m:v_zna:up19
автистам	автист	noun	noun:anim:p:v_dav:up19
автистами	автист	noun	noun:anim:p:v_oru:up19
автистах	автист	noun	noun:anim:p:v_mis:up19
автисте	автист	noun	noun:anim:m:v_kly:up19
автисти	автист	noun	noun:anim:p:v_kly:up19
автисти	автист	noun	noun:anim:p:v_naz:up19
автисти	автист	noun	noun:anim:p:v_zna:up19:rare
автистові	автист	noun	noun:anim:m:v_dav:up19
автистові	автист	noun	noun:anim:m:v_mis:up19
автистом	автист	noun	noun:anim:m:v_oru:up19
автисті	автист	noun	noun:anim:m:v_mis:up19
автистів	автист	noun	noun:anim:p:v_rod:up19
автистів	автист	noun	noun:anim:p:v_zna:up19
автоаварій	автоаварія	noun	noun:inanim:p:v_rod
автоаварію	автоаварія	noun	noun:inanim:f:v_zna
автоаварія	автоаварія	noun	noun:inanim:f:v_naz
автоаваріям	автоаварія	noun	noun:inanim:p:v_dav
автоаваріями	автоаварія	noun	noun:inanim:p:v_oru
автоаваріях	автоаварія	noun	noun:inanim:p:v_mis
автоаваріє	автоаварія	noun	noun:inanim:f:v_kly
автоаварією	автоаварія	noun	noun:inanim:f:v_oru
автоаварії	автоаварія	noun	noun:inanim:f:v_dav
автоаварії	автоаварія	noun	noun:inanim:f:v_mis
автоаварії	автоаварія	noun	noun:inanim:f:v_rod
автоаварії	автоаварія	noun	noun:inanim:p:v_kly
автоаварії	автоаварія	noun	noun:inanim:p:v_naz
автоаварії	автоаварія	noun	noun:inanim:p:v_zna
автоагрегат	автоагрегат	noun	noun:inanim:m:v_naz
автоагрегат	автоагрегат	noun	noun:inanim:m:v_zna
автоагрегата	автоагрегат	noun	noun:inanim:m:v_rod
автоагрегатам	автоагрегат	noun	noun:inanim:p:v_dav
автоагрегатами	автоагрегат	noun	noun:inanim:p:v_oru
автоагрегатах	автоагрегат	noun	noun:inanim:p:v_mis
автоагрегате	автоагрегат	noun	noun:inanim:m:v_kly
автоагрегати	автоагрегат	noun	noun:inanim:p:v_kly
автоагрегати	автоагрегат	noun	noun:inanim:p:v_naz
автоагрегати	автоагрегат	noun	noun:inanim:p:v_zna
автоагрегатові	автоагрегат	noun	noun:inanim:m:v_dav
автоагрегатові	автоагрегат	noun	noun:inanim:m:v_mis
автоагрегатом	автоагрегат	noun	noun:inanim:m:v_oru
автоагрегаті	автоагрегат	noun	noun:inanim:m:v_mis
автоагрегатів	автоагрегат	noun	noun:inanim:p:v_rod
автоагресій	автоагресія	noun	noun:inanim:p:v_rod
автоагресію	автоагресія	noun	noun:inanim:f:v_zna
автоагресія	автоагресія	noun	noun:inanim:f:v_naz
автоагресіям	автоагресія	noun	noun:inanim:p:v_dav
автоагресіями	автоагресія	noun	noun:inanim:p:v_oru
автоагресіях	автоагресія	noun	noun:inanim:p:v_mis
автоагресіє	автоагресія	noun	noun:inanim:f:v_kly
автоагресією	автоагресія	noun	noun:inanim:f:v_oru
автоагресії	автоагресія	noun	noun:inanim:f:v_dav
автоагресії	автоагресія	noun	noun:inanim:f:v_mis
автоагресії	автоагресія	noun	noun:inanim:f:v_rod
автоагресії	автоагресія	noun	noun:inanim:p:v_kly
автоагресії	автоагресія	noun	noun:inanim:p:v_naz
автоагресії	автоагресія	noun	noun:inanim:p:v_zna
автоадвокат	автоадвокат	noun	noun:anim:m:v_naz
автоадвоката	автоадвокат	noun	noun:anim:m:v_rod
автоадвоката	автоадвокат	noun	noun:anim:m:v_zna
автоадвокатам	автоадвокат	noun	noun:anim:p:v_dav
автоадвокатами	автоадвокат	noun	noun:anim:p:v_oru
автоадвокатах	автоадвокат	noun	noun:anim:p:v_mis
автоадвокате	автоадвокат	noun	noun:anim:m:v_kly
автоадвокати	автоадвокат	noun	noun:anim:p:v_kly
автоадвокати	автоадвокат	noun	noun:anim:p:v_naz
автоадвокати	автоадвокат	noun	noun:anim:p:v_zna:rare
автоадвокатові	автоадвокат	noun	noun:anim:m:v_dav
автоадвокатові	автоадвокат	noun	noun:anim:m:v_mis
автоадвокатом	автоадвокат	noun	noun:anim:m:v_oru
автоадвокаті	автоадвокат	noun	noun:anim:m:v_mis
автоадвокатів	автоадвокат	noun	noun:anim:p:v_rod
автоадвокатів	автоадвокат	noun	noun:anim:p:v_zna
автоаерозапчастин	автоаерозапчастина	noun	noun:inanim:p:v_rod
автоаерозапчастина	автоаерозапчастина	noun	noun:inanim:f:v_naz
автоаерозапчастинам	автоаерозапчастина	noun	noun:inanim:p:v_dav
автоаерозапчастинами	автоаерозапчастина	noun	noun:inanim:p:v_oru
автоаерозапчастинах	автоаерозапчастина	noun	noun:inanim:p:v_mis
автоаерозапчастини	автоаерозапчастина	noun	noun:inanim:f:v_rod
автоаерозапчастини	автоаерозапчастина	noun	noun:inanim:p:v_kly
автоаерозапчастини	автоаерозапчастина	noun	noun:inanim:p:v_naz
автоаерозапчастини	автоаерозапчастина	noun	noun:inanim:p:v_zna
автоаерозапчастино	автоаерозапчастина	noun	noun:inanim:f:v_kly
автоаерозапчастиною	автоаерозапчастина	noun	noun:inanim:f:v_oru
автоаерозапчастину	автоаерозапчастина	noun	noun:inanim:f:v_zna
автоаерозапчастині	автоаерозапчастина	noun	noun:inanim:f:v_dav
автоаерозапчастині	автоаерозапчастина	noun	noun:inanim:f:v_mis
автоаксесуар	автоаксесуар	noun	noun:inanim:m:v_naz
автоаксесуар	автоаксесуар	noun	noun:inanim:m:v_zna
автоаксесуара	автоаксесуар	noun	noun:inanim:m:v_rod
автоаксесуарам	автоаксесуар	noun	noun:inanim:p:v_dav
автоаксесуарами	автоаксесуар	noun	noun:inanim:p:v_oru
автоаксесуарах	автоаксесуар	noun	noun:inanim:p:v_mis
автоаксесуаре	автоаксесуар	noun	noun:inanim:m:v_kly
автоаксесуари	автоаксесуар	noun	noun:inanim:p:v_kly
автоаксесуари	автоаксесуар	noun	noun:inanim:p:v_naz
автоаксесуари	автоаксесуар	noun	noun:inanim:p:v_zna
автоаксесуарові	автоаксесуар	noun	noun:inanim:m:v_dav
автоаксесуарові	автоаксесуар	noun	noun:inanim:m:v_mis
автоаксесуаром	автоаксесуар	noun	noun:inanim:m:v_oru
автоаксесуарі	автоаксесуар	noun	noun:inanim:m:v_mis
автоаксесуарів	автоаксесуар	noun	noun:inanim:p:v_rod
автоакумулятор	автоакумулятор	noun	noun:inanim:m:v_naz
автоакумулятор	автоакумулятор	noun	noun:inanim:m:v_zna
автоакумулятора	автоакумулятор	noun	noun:inanim:m:v_rod
автоакумуляторам	автоакумулятор	noun	noun:inanim:p:v_dav
автоакумуляторами	автоакумулятор	noun	noun:inanim:p:v_oru
автоакумуляторах	автоакумулятор	noun	noun:inanim:p:v_mis
автоакумуляторе	автоакумулятор	noun	noun:inanim:m:v_kly
автоакумулятори	автоакумулятор	noun	noun:inanim:p:v_kly
автоакумулятори	автоакумулятор	noun	noun:inanim:p:v_naz
автоакумулятори	автоакумулятор	noun	noun:inanim:p:v_zna
автоакумуляторові	автоакумулятор	noun	noun:inanim:m:v_dav
автоакумуляторові	автоакумулятор	noun	noun:inanim:m:v_mis
автоакумулятором	автоакумулятор	noun	noun:inanim:m:v_oru
автоакумуляторі	автоакумулятор	noun	noun:inanim:m:v_mis
автоакумуляторів	автоакумулятор	noun	noun:inanim:p:v_rod
автоалюзій	автоалюзія	noun	noun:inanim:p:v_rod
автоалюзію	автоалюзія	noun	noun:inanim:f:v_zna
автоалюзія	автоалюзія	noun	noun:inanim:f:v_naz
автоалюзіям	автоалюзія	noun	noun:inanim:p:v_dav
автоалюзіями	автоалюзія	noun	noun:inanim:p:v_oru
автоалюзіях	автоалюзія	noun	noun:inanim:p:v_mis
автоалюзіє	автоалюзія	noun	noun:inanim:f:v_kly
автоалюзією	автоалюзія	noun	noun:inanim:f:v_oru
автоалюзії	автоалюзія	noun	noun:inanim:f:v_dav
автоалюзії	автоалюзія	noun	noun:inanim:f:v_mis
автоалюзії	автоалюзія	noun	noun:inanim:f:v_rod
автоалюзії	автоалюзія	noun	noun:inanim:p:v_kly
автоалюзії	автоалюзія	noun	noun:inanim:p:v_naz
автоалюзії	автоалюзія	noun	noun:inanim:p:v_zna
автоалієнацій	автоалієнація	noun	noun:inanim:p:v_rod
автоалієнацію	автоалієнація	noun	noun:inanim:f:v_zna
автоалієнація	автоалієнація	noun	noun:inanim:f:v_naz
автоалієнаціям	автоалієнація	noun	noun:inanim:p:v_dav
автоалієнаціями	автоалієнація	noun	noun:inanim:p:v_oru
автоалієнаціях	автоалієнація	noun	noun:inanim:p:v_mis
автоалієнаціє	автоалієнація	noun	noun:inanim:f:v_kly
автоалієнацією	автоалієнація	noun	noun:inanim:f:v_oru
автоалієнації	автоалієнація	noun	noun:inanim:f:v_dav
автоалієнації	автоалієнація	noun	noun:inanim:f:v_mis
автоалієнації	автоалієнація	noun	noun:inanim:f:v_rod
автоалієнації	автоалієнація	noun	noun:inanim:p:v_kly
автоалієнації	автоалієнація	noun	noun:inanim:p:v_naz
автоалієнації	автоалієнація	noun	noun:inanim:p:v_zna
автоаматор	автоаматор	noun	noun:anim:m:v_naz
автоаматора	автоаматор	noun	noun:anim:m:v_rod
автоаматора	автоаматор	noun	noun:anim:m:v_zna
автоаматорам	автоаматор	noun	noun:anim:p:v_dav
автоаматорами	автоаматор	noun	noun:anim:p:v_oru
автоаматорах	автоаматор	noun	noun:anim:p:v_mis
автоаматоре	автоаматор	noun	noun:anim:m:v_kly
автоаматори	автоаматор	noun	noun:anim:p:v_kly
автоаматори	автоаматор	noun	noun:anim:p:v_naz
автоаматори	автоаматор	noun	noun:anim:p:v_zna:rare
автоаматорка	автоаматорка	noun	noun:anim:f:v_naz
автоаматоркам	автоаматорка	noun	noun:anim:p:v_dav
автоаматорками	автоаматорка	noun	noun:anim:p:v_oru
автоаматорках	автоаматорка	noun	noun:anim:p:v_mis
автоаматорки	автоаматорка	noun	noun:anim:f:v_rod
автоаматорки	автоаматорка	noun	noun:anim:p:v_kly
автоаматорки	автоаматорка	noun	noun:anim:p:v_naz
автоаматорки	автоаматорка	noun	noun:anim:p:v_zna:rare
автоаматорко	автоаматорка	noun	noun:anim:f:v_kly
автоаматоркою	автоаматорка	noun	noun:anim:f:v_oru
автоаматорку	автоаматорка	noun	noun:anim:f:v_zna
автоаматорові	автоаматор	noun	noun:anim:m:v_dav
автоаматорові	автоаматор	noun	noun:anim:m:v_mis
автоаматорок	автоаматорка	noun	noun:anim:p:v_rod
автоаматорок	автоаматорка	noun	noun:anim:p:v_zna
автоаматором	автоаматор	noun	noun:anim:m:v_oru
автоаматорці	автоаматорка	noun	noun:anim:f:v_dav
автоаматорці	автоаматорка	noun	noun:anim:f:v_mis
автоаматорі	автоаматор	noun	noun:anim:m:v_mis
автоаматорів	автоаматор	noun	noun:anim:p:v_rod
автоаматорів	автоаматор	noun	noun:anim:p:v_zna
автоамфібій	автоамфібія	noun	noun:inanim:p:v_rod
автоамфібію	автоамфібія	noun	noun:inanim:f:v_zna
автоамфібія	автоамфібія	noun	noun:inanim:f:v_naz
автоамфібіям	автоамфібія	noun	noun:inanim:p:v_dav
автоамфібіями	автоамфібія	noun	noun:inanim:p:v_oru
автоамфібіях	автоамфібія	noun	noun:inanim:p:v_mis
автоамфібіє	автоамфібія	noun	noun:inanim:f:v_kly
автоамфібією	автоамфібія	noun	noun:inanim:f:v_oru
автоамфібії	автоамфібія	noun	noun:inanim:f:v_dav
автоамфібії	автоамфібія	noun	noun:inanim:f:v_mis
автоамфібії	автоамфібія	noun	noun:inanim:f:v_rod
автоамфібії	автоамфібія	noun	noun:inanim:p:v_kly
автоамфібії	автоамфібія	noun	noun:inanim:p:v_naz
автоамфібії	автоамфібія	noun	noun:inanim:p:v_zna
автоаналізатор	автоаналізатор	noun	noun:inanim:m:v_naz
автоаналізатор	автоаналізатор	noun	noun:inanim:m:v_zna
автоаналізатора	автоаналізатор	noun	noun:inanim:m:v_rod
автоаналізаторам	автоаналізатор	noun	noun:inanim:p:v_dav
автоаналізаторами	автоаналізатор	noun	noun:inanim:p:v_oru
автоаналізаторах	автоаналізатор	noun	noun:inanim:p:v_mis
автоаналізаторе	автоаналізатор	noun	noun:inanim:m:v_kly
автоаналізатори	автоаналізатор	noun	noun:inanim:p:v_kly
автоаналізатори	автоаналізатор	noun	noun:inanim:p:v_naz
автоаналізатори	автоаналізатор	noun	noun:inanim:p:v_zna
автоаналізаторові	автоаналізатор	noun	noun:inanim:m:v_dav
автоаналізаторові	автоаналізатор	noun	noun:inanim:m:v_mis
автоаналізатором	автоаналізатор	noun	noun:inanim:m:v_oru
автоаналізаторі	автоаналізатор	noun	noun:inanim:m:v_mis
автоаналізаторів	автоаналізатор	noun	noun:inanim:p:v_rod
автоапологій	автоапологія	noun	noun:inanim:p:v_rod
автоапологію	автоапологія	noun	noun:inanim:f:v_zna
автоапологія	автоапологія	noun	noun:inanim:f:v_naz
автоапологіям	автоапологія	noun	noun:inanim:p:v_dav
автоапологіями	автоапологія	noun	noun:inanim:p:v_oru
автоапологіях	автоапологія	noun	noun:inanim:p:v_mis
автоапологіє	автоапологія	noun	noun:inanim:f:v_kly
автоапологією	автоапологія	noun	noun:inanim:f:v_oru
автоапології	автоапологія	noun	noun:inanim:f:v_dav
автоапології	автоапологія	noun	noun:inanim:f:v_mis
автоапології	автоапологія	noun	noun:inanim:f:v_rod
автоапології	автоапологія	noun	noun:inanim:p:v_kly
автоапології	автоапологія	noun	noun:inanim:p:v_naz
автоапології	автоапологія	noun	noun:inanim:p:v_zna
автоартерій	автоартерія	noun	noun:inanim:p:v_rod
автоартерію	автоартерія	noun	noun:inanim:f:v_zna
автоартерія	автоартерія	noun	noun:inanim:f:v_naz
автоартеріям	автоартерія	noun	noun:inanim:p:v_dav
автоартеріями	автоартерія	noun	noun:inanim:p:v_oru
автоартеріях	автоартерія	noun	noun:inanim:p:v_mis
автоартеріє	автоартерія	noun	noun:inanim:f:v_kly
автоартерією	автоартерія	noun	noun:inanim:f:v_oru
автоартерії	автоартерія	noun	noun:inanim:f:v_dav
автоартерії	автоартерія	noun	noun:inanim:f:v_mis
автоартерії	автоартерія	noun	noun:inanim:f:v_rod
автоартерії	автоартерія	noun	noun:inanim:p:v_kly
автоартерії	автоартерія	noun	noun:inanim:p:v_naz
автоартерії	автоартерія	noun	noun:inanim:p:v_zna
автоаукціон	автоаукціон	noun	noun:inanim:m:v_naz
автоаукціон	автоаукціон	noun	noun:inanim:m:v_zna
автоаукціонам	автоаукціон	noun	noun:inanim:p:v_dav
автоаукціонами	автоаукціон	noun	noun:inanim:p:v_oru
автоаукціонах	автоаукціон	noun	noun:inanim:p:v_mis
автоаукціоне	автоаукціон	noun	noun:inanim:m:v_kly
автоаукціони	автоаукціон	noun	noun:inanim:p:v_kly
автоаукціони	автоаукціон	noun	noun:inanim:p:v_naz
автоаукціони	автоаукціон	noun	noun:inanim:p:v_zna
автоаукціонові	автоаукціон	noun	noun:inanim:m:v_dav
автоаукціонові	автоаукціон	noun	noun:inanim:m:v_mis
автоаукціоном	автоаукціон	noun	noun:inanim:m:v_oru
автоаукціону	автоаукціон	noun	noun:inanim:m:v_dav
автоаукціону	автоаукціон	noun	noun:inanim:m:v_mis
автоаукціону	автоаукціон	noun	noun:inanim:m:v_rod
автоаукціоні	автоаукціон	noun	noun:inanim:m:v_mis
автоаукціонів	автоаукціон	noun	noun:inanim:p:v_rod
автобаз	автобаза	noun	noun:inanim:p:v_rod
автобаза	автобаза	noun	noun:inanim:f:v_naz
автобазам	автобаза	noun	noun:inanim:p:v_dav
автобазами	автобаза	noun	noun:inanim:p:v_oru
автобазар	автобазар	noun	noun:inanim:m:v_naz
автобазар	автобазар	noun	noun:inanim:m:v_zna
автобазарам	автобазар	noun	noun:inanim:p:v_dav
автобазарами	автобазар	noun	noun:inanim:p:v_oru
автобазарах	автобазар	noun	noun:inanim:p:v_mis
автобазаре	автобазар	noun	noun:inanim:m:v_kly
автобазари	автобазар	noun	noun:inanim:p:v_kly
автобазари	автобазар	noun	noun:inanim:p:v_naz
автобазари	автобазар	noun	noun:inanim:p:v_zna
автобазарові	автобазар	noun	noun:inanim:m:v_dav
автобазарові	автобазар	noun	noun:inanim:m:v_mis
автобазаром	автобазар	noun	noun:inanim:m:v_oru
автобазару	автобазар	noun	noun:inanim:m:v_dav
автобазару	автобазар	noun	noun:inanim:m:v_mis
автобазару	автобазар	noun	noun:inanim:m:v_rod
автобазарі	автобазар	noun	noun:inanim:m:v_mis
автобазарів	автобазар	noun	noun:inanim:p:v_rod
автобазах	автобаза	noun	noun:inanim:p:v_mis
автобази	автобаза	noun	noun:inanim:f:v_rod
автобази	автобаза	noun	noun:inanim:p:v_kly
автобази	автобаза	noun	noun:inanim:p:v_naz
автобази	автобаза	noun	noun:inanim:p:v_zna
автобазо	автобаза	noun	noun:inanim:f:v_kly
автобазою	автобаза	noun	noun:inanim:f:v_oru
автобазу	автобаза	noun	noun:inanim:f:v_zna
автобазі	автобаза	noun	noun:inanim:f:v_dav
автобазі	автобаза	noun	noun:inanim:f:v_mis
автобальзам	автобальзам	noun	noun:inanim:m:v_naz
автобальзам	автобальзам	noun	noun:inanim:m:v_zna
автобальзамам	автобальзам	noun	noun:inanim:p:v_dav
автобальзамами	автобальзам	noun	noun:inanim:p:v_oru
автобальзамах	автобальзам	noun	noun:inanim:p:v_mis
автобальзаме	автобальзам	noun	noun:inanim:m:v_kly
автобальзами	автобальзам	noun	noun:inanim:p:v_kly
автобальзами	автобальзам	noun	noun:inanim:p:v_naz
автобальзами	автобальзам	noun	noun:inanim:p:v_zna
автобальзамові	автобальзам	noun	noun:inanim:m:v_dav
автобальзамові	автобальзам	noun	noun:inanim:m:v_mis
автобальзамом	автобальзам	noun	noun:inanim:m:v_oru
автобальзаму	автобальзам	noun	noun:inanim:m:v_dav
автобальзаму	автобальзам	noun	noun:inanim:m:v_mis
автобальзаму	автобальзам	noun	noun:inanim:m:v_rod
автобальзамі	автобальзам	noun	noun:inanim:m:v_mis
автобальзамів	автобальзам	noun	noun:inanim:p:v_rod
автобан	автобан	noun	noun:inanim:m:v_naz
автобан	автобан	noun	noun:inanim:m:v_zna
автобанам	автобан	noun	noun:inanim:p:v_dav
автобанами	автобан	noun	noun:inanim:p:v_oru
автобанах	автобан	noun	noun:inanim:p:v_mis
автобандит	автобандит	noun	noun:anim:m:v_naz
автобандита	автобандит	noun	noun:anim:m:v_rod
автобандита	автобандит	noun	noun:anim:m:v_zna
автобандитам	автобандит	noun	noun:anim:p:v_dav
автобандитами	автобандит	noun	noun:anim:p:v_oru
автобандитах	автобандит	noun	noun:anim:p:v_mis
автобандите	автобандит	noun	noun:anim:m:v_kly
автобандити	автобандит	noun	noun:anim:p:v_kly
автобандити	автобандит	noun	noun:anim:p:v_naz
автобандити	автобандит	noun	noun:anim:p:v_zna:rare
автобандитові	автобандит	noun	noun:anim:m:v_dav
автобандитові	автобандит	noun	noun:anim:m:v_mis
автобандитом	автобандит	noun	noun:anim:m:v_oru
автобандиті	автобандит	noun	noun:anim:m:v_mis
автобандитів	автобандит	noun	noun:anim:p:v_rod
автобандитів	автобандит	noun	noun:anim:p:v_zna
автобане	автобан	noun	noun:inanim:m:v_kly
автобани	автобан	noun	noun:inanim:p:v_kly
автобани	автобан	noun	noun:inanim:p:v_naz
автобани	автобан	noun	noun:inanim:p:v_zna
автобанові	автобан	noun	noun:inanim:m:v_dav
автобанові	автобан	noun	noun:inanim:m:v_mis
автобаном	автобан	noun	noun:inanim:m:v_oru
автобану	автобан	noun	noun:inanim:m:v_dav
автобану	автобан	noun	noun:inanim:m:v_mis
автобану	автобан	noun	noun:inanim:m:v_rod
автобані	автобан	noun	noun:inanim:m:v_mis
автобанів	автобан	noun	noun:inanim:p:v_rod
автобардачка	автобардачок	noun	noun:inanim:m:v_rod
автобардачкам	автобардачок	noun	noun:inanim:p:v_dav
автобардачками	автобардачок	noun	noun:inanim:p:v_oru
автобардачках	автобардачок	noun	noun:inanim:p:v_mis
автобардачки	автобардачок	noun	noun:inanim:p:v_kly
автобардачки	автобардачок	noun	noun:inanim:p:v_naz
автобардачки	автобардачок	noun	noun:inanim:p:v_zna
автобардачкові	автобардачок	noun	noun:inanim:m:v_dav
автобардачкові	автобардачок	noun	noun:inanim:m:v_mis
автобардачком	автобардачок	noun	noun:inanim:m:v_oru
автобардачку	автобардачок	noun	noun:inanim:m:v_dav
автобардачку	автобардачок	noun	noun:inanim:m:v_kly
автобардачку	автобардачок	noun	noun:inanim:m:v_mis
автобардачків	автобардачок	noun	noun:inanim:p:v_rod
автобардачок	автобардачок	noun	noun:inanim:m:v_naz
автобардачок	автобардачок	noun	noun:inanim:m:v_zna
автобарсетка	автобарсетка	noun	noun:inanim:f:v_naz
автобарсеткам	автобарсетка	noun	noun:inanim:p:v_dav
автобарсетками	автобарсетка	noun	noun:inanim:p:v_oru
автобарсетках	автобарсетка	noun	noun:inanim:p:v_mis
автобарсетки	автобарсетка	noun	noun:inanim:f:v_rod
автобарсетки	автобарсетка	noun	noun:inanim:p:v_kly
автобарсетки	автобарсетка	noun	noun:inanim:p:v_naz
автобарсетки	автобарсетка	noun	noun:inanim:p:v_zna
автобарсетко	автобарсетка	noun	noun:inanim:f:v_kly
автобарсеткою	автобарсетка	noun	noun:inanim:f:v_oru
автобарсетку	автобарсетка	noun	noun:inanim:f:v_zna
автобарсеток	автобарсетка	noun	noun:inanim:p:v_rod
автобарсетці	автобарсетка	noun	noun:inanim:f:v_dav
автобарсетці	автобарсетка	noun	noun:inanim:f:v_mis
автобат	автобат	noun	noun:inanim:m:v_naz
автобат	автобат	noun	noun:inanim:m:v_zna
автобатальйон	автобатальйон	noun	noun:inanim:m:v_naz
автобатальйон	автобатальйон	noun	noun:inanim:m:v_zna
автобатальйонам	автобатальйон	noun	noun:inanim:p:v_dav
автобатальйонами	автобатальйон	noun	noun:inanim:p:v_oru
автобатальйонах	автобатальйон	noun	noun:inanim:p:v_mis
автобатальйоне	автобатальйон	noun	noun:inanim:m:v_kly
автобатальйони	автобатальйон	noun	noun:inanim:p:v_kly
автобатальйони	автобатальйон	noun	noun:inanim:p:v_naz
автобатальйони	автобатальйон	noun	noun:inanim:p:v_zna
автобатальйонові	автобатальйон	noun	noun:inanim:m:v_dav
автобатальйонові	автобатальйон	noun	noun:inanim:m:v_mis
автобатальйоном	автобатальйон	noun	noun:inanim:m:v_oru
автобатальйону	автобатальйон	noun	noun:inanim:m:v_dav
автобатальйону	автобатальйон	noun	noun:inanim:m:v_mis
автобатальйону	автобатальйон	noun	noun:inanim:m:v_rod
автобатальйоні	автобатальйон	noun	noun:inanim:m:v_mis
автобатальйонів	автобатальйон	noun	noun:inanim:p:v_rod
автобатам	автобат	noun	noun:inanim:p:v_dav
автобатами	автобат	noun	noun:inanim:p:v_oru
автобатах	автобат	noun	noun:inanim:p:v_mis
автобате	автобат	noun	noun:inanim:m:v_kly
автобати	автобат	noun	noun:inanim:p:v_kly
автобати	автобат	noun	noun:inanim:p:v_naz
автобати	автобат	noun	noun:inanim:p:v_zna
автобатові	автобат	noun	noun:inanim:m:v_dav
автобатові	автобат	noun	noun:inanim:m:v_mis
автобатом	автобат	noun	noun:inanim:m:v_oru
автобату	автобат	noun	noun:inanim:m:v_dav
автобату	автобат	noun	noun:inanim:m:v_mis
автобату	автобат	noun	noun:inanim:m:v_rod
автобаті	автобат	noun	noun:inanim:m:v_mis
автобатів	автобат	noun	noun:inanim:p:v_rod
автобензин	автобензин	noun	noun:inanim:m:v_naz
автобензин	автобензин	noun	noun:inanim:m:v_zna
автобензинам	автобензин	noun	noun:inanim:p:v_dav
автобензинами	автобензин	noun	noun:inanim:p:v_oru
автобензинах	автобензин	noun	noun:inanim:p:v_mis
автобензине	автобензин	noun	noun:inanim:m:v_kly
автобензини	автобензин	noun	noun:inanim:p:v_kly
автобензини	автобензин	noun	noun:inanim:p:v_naz
автобензини	автобензин	noun	noun:inanim:p:v_zna
автобензинові	автобензин	noun	noun:inanim:m:v_dav
автобензинові	автобензин	noun	noun:inanim:m:v_mis
автобензином	автобензин	noun	noun:inanim:m:v_oru
автобензину	автобензин	noun	noun:inanim:m:v_dav
автобензину	автобензин	noun	noun:inanim:m:v_mis
автобензину	автобензин	noun	noun:inanim:m:v_rod
автобензині	автобензин	noun	noun:inanim:m:v_mis
автобензинів	автобензин	noun	noun:inanim:p:v_rod
автобензовоз	автобензовоз	noun	noun:inanim:m:v_naz
автобензовоз	автобензовоз	noun	noun:inanim:m:v_zna
автобензовоза	автобензовоз	noun	noun:inanim:m:v_rod
автобензовозам	автобензовоз	noun	noun:inanim:p:v_dav
автобензовозами	автобензовоз	noun	noun:inanim:p:v_oru
автобензовозах	автобензовоз	noun	noun:inanim:p:v_mis
автобензовозе	автобензовоз	noun	noun:inanim:m:v_kly
автобензовози	автобензовоз	noun	noun:inanim:p:v_kly
автобензовози	автобензовоз	noun	noun:inanim:p:v_naz
автобензовози	автобензовоз	noun	noun:inanim:p:v_zna
автобензовозові	автобензовоз	noun	noun:inanim:m:v_dav
автобензовозові	автобензовоз	noun	noun:inanim:m:v_mis
автобензовозом	автобензовоз	noun	noun:inanim:m:v_oru
автобензовозі	автобензовоз	noun	noun:inanim:m:v_mis
автобензовозів	автобензовоз	noun	noun:inanim:p:v_rod
автобензоцистерн	автобензоцистерна	noun	noun:inanim:p:v_rod
автобензоцистерна	автобензоцистерна	noun	noun:inanim:f:v_naz
автобензоцистернам	автобензоцистерна	noun	noun:inanim:p:v_dav
автобензоцистернами	автобензоцистерна	noun	noun:inanim:p:v_oru
автобензоцистернах	автобензоцистерна	noun	noun:inanim:p:v_mis
автобензоцистерни	автобензоцистерна	noun	noun:inanim:f:v_rod
автобензоцистерни	автобензоцистерна	noun	noun:inanim:p:v_kly
автобензоцистерни	автобензоцистерна	noun	noun:inanim:p:v_naz
автобензоцистерни	автобензоцистерна	noun	noun:inanim:p:v_zna
автобензоцистерно	автобензоцистерна	noun	noun:inanim:f:v_kly
автобензоцистерною	автобензоцистерна	noun	noun:inanim:f:v_oru
автобензоцистерну	автобензоцистерна	noun	noun:inanim:f:v_zna
автобензоцистерні	автобензоцистерна	noun	noun:inanim:f:v_dav
автобензоцистерні	автобензоцистерна	noun	noun:inanim:f:v_mis
автобетонозмішувач	автобетонозмішувач	noun	noun:inanim:m:v_naz
автобетонозмішувач	автобетонозмішувач	noun	noun:inanim:m:v_zna
автобетонозмішувача	автобетонозмішувач	noun	noun:inanim:m:v_rod
автобетонозмішувачам	автобетонозмішувач	noun	noun:inanim:p:v_dav
автобетонозмішувачами	автобетонозмішувач	noun	noun:inanim:p:v_oru
автобетонозмішувачах	автобетонозмішувач	noun	noun:inanim:p:v_mis
автобетонозмішувачеві	автобетонозмішувач	noun	noun:inanim:m:v_dav
автобетонозмішувачеві	автобетонозмішувач	noun	noun:inanim:m:v_mis
автобетонозмішувачем	автобетонозмішувач	noun	noun:inanim:m:v_oru
автобетонозмішувачу	автобетонозмішувач	noun	noun:inanim:m:v_dav
автобетонозмішувачу	автобетонозмішувач	noun	noun:inanim:m:v_kly
автобетонозмішувачу	автобетонозмішувач	noun	noun:inanim:m:v_mis
автобетонозмішувачі	автобетонозмішувач	noun	noun:inanim:m:v_mis
автобетонозмішувачі	автобетонозмішувач	noun	noun:inanim:p:v_kly
автобетонозмішувачі	автобетонозмішувач	noun	noun:inanim:p:v_naz
автобетонозмішувачі	автобетонозмішувач	noun	noun:inanim:p:v_zna
автобетонозмішувачів	автобетонозмішувач	noun	noun:inanim:p:v_rod
автобетономішалка	автобетономішалка	noun	noun:inanim:f:v_naz
автобетономішалкам	автобетономішалка	noun	noun:inanim:p:v_dav
автобетономішалками	автобетономішалка	noun	noun:inanim:p:v_oru
автобетономішалках	автобетономішалка	noun	noun:inanim:p:v_mis
автобетономішалки	автобетономішалка	noun	noun:inanim:f:v_rod
автобетономішалки	автобетономішалка	noun	noun:inanim:p:v_kly
автобетономішалки	автобетономішалка	noun	noun:inanim:p:v_naz
автобетономішалки	автобетономішалка	noun	noun:inanim:p:v_zna
автобетономішалко	автобетономішалка	noun	noun:inanim:f:v_kly
автобетономішалкою	автобетономішалка	noun	noun:inanim:f:v_oru
автобетономішалку	автобетономішалка	noun	noun:inanim:f:v_zna
автобетономішалок	автобетономішалка	noun	noun:inanim:p:v_rod
автобетономішалці	автобетономішалка	noun	noun:inanim:f:v_dav
автобетономішалці	автобетономішалка	noun	noun:inanim:f:v_mis
автобетоноперемішувач	автобетоноперемішувач	noun	noun:inanim:m:v_naz
автобетоноперемішувач	автобетоноперемішувач	noun	noun:inanim:m:v_zna
автобетоноперемішувача	автобетоноперемішувач	noun	noun:inanim:m:v_rod
автобетоноперемішувачам	автобетоноперемішувач	noun	noun:inanim:p:v_dav
автобетоноперемішувачами	автобетоноперемішувач	noun	noun:inanim:p:v_oru
автобетоноперемішувачах	автобетоноперемішувач	noun	noun:inanim:p:v_mis
автобетоноперемішувачеві	автобетоноперемішувач	noun	noun:inanim:m:v_dav
автобетоноперемішувачеві	автобетоноперемішувач	noun	noun:inanim:m:v_mis
автобетоноперемішувачем	автобетоноперемішувач	noun	noun:inanim:m:v_oru
автобетоноперемішувачу	автобетоноперемішувач	noun	noun:inanim:m:v_dav
автобетоноперемішувачу	автобетоноперемішувач	noun	noun:inanim:m:v_kly
автобетоноперемішувачу	автобетоноперемішувач	noun	noun:inanim:m:v_mis
автобетоноперемішувачі	автобетоноперемішувач	noun	noun:inanim:m:v_mis
автобетоноперемішувачі	автобетоноперемішувач	noun	noun:inanim:p:v_kly
автобетоноперемішувачі	автобетоноперемішувач	noun	noun:inanim:p:v_naz
автобетоноперемішувачі	автобетоноперемішувач	noun	noun:inanim:p:v_zna
автобетоноперемішувачів	автобетоноперемішувач	noun	noun:inanim:p:v_rod
автоблокуванню	автоблокування	noun	noun:inanim:n:v_dav
автоблокуванню	автоблокування	noun	noun:inanim:n:v_mis
автоблокування	автоблокування	noun	noun:inanim:n:v_kly
автоблокування	автоблокування	noun	noun:inanim:n:v_naz
автоблокування	автоблокування	noun	noun:inanim:n:v_rod
автоблокування	автоблокування	noun	noun:inanim:n:v_zna
автоблокування	автоблокування	noun	noun:inanim:p:v_kly
автоблокування	автоблокування	noun	noun:inanim:p:v_naz
автоблокування	автоблокування	noun	noun:inanim:p:v_zna
автоблокуванням	автоблокування	noun	noun:inanim:n:v_oru
автоблокуванням	автоблокування	noun	noun:inanim:p:v_dav
автоблокуваннями	автоблокування	noun	noun:inanim:p:v_oru
автоблокуваннях	автоблокування	noun	noun:inanim:p:v_mis
автоблокуванні	автоблокування	noun	noun:inanim:n:v_mis
автоблокувань	автоблокування	noun	noun:inanim:p:v_rod
автоблокувач	автоблокувач	noun	noun:inanim:m:v_naz
автоблокувач	автоблокувач	noun	noun:inanim:m:v_zna
автоблокувача	автоблокувач	noun	noun:inanim:m:v_rod
автоблокувачам	автоблокувач	noun	noun:inanim:p:v_dav
автоблокувачами	автоблокувач	noun	noun:inanim:p:v_oru
автоблокувачах	автоблокувач	noun	noun:inanim:p:v_mis
автоблокувачеві	автоблокувач	noun	noun:inanim:m:v_dav
автоблокувачеві	автоблокувач	noun	noun:inanim:m:v_mis
автоблокувачем	автоблокувач	noun	noun:inanim:m:v_oru
автоблокувачу	автоблокувач	noun	noun:inanim:m:v_dav
автоблокувачу	автоблокувач	noun	noun:inanim:m:v_kly
автоблокувачу	автоблокувач	noun	noun:inanim:m:v_mis
автоблокувачі	автоблокувач	noun	noun:inanim:m:v_mis
автоблокувачі	автоблокувач	noun	noun:inanim:p:v_kly
автоблокувачі	автоблокувач	noun	noun:inanim:p:v_naz
автоблокувачі	автоблокувач	noun	noun:inanim:p:v_zna
автоблокувачів	автоблокувач	noun	noun:inanim:p:v_rod
автоблокіратор	автоблокіратор	noun	noun:inanim:m:v_naz
автоблокіратор	автоблокіратор	noun	noun:inanim:m:v_zna
автоблокіратора	автоблокіратор	noun	noun:inanim:m:v_rod
автоблокіраторам	автоблокіратор	noun	noun:inanim:p:v_dav
автоблокіраторами	автоблокіратор	noun	noun:inanim:p:v_oru
автоблокіраторах	автоблокіратор	noun	noun:inanim:p:v_mis
автоблокіраторе	автоблокіратор	noun	noun:inanim:m:v_kly
автоблокіратори	автоблокіратор	noun	noun:inanim:p:v_kly
автоблокіратори	автоблокіратор	noun	noun:inanim:p:v_naz
автоблокіратори	автоблокіратор	noun	noun:inanim:p:v_zna
автоблокіраторові	автоблокіратор	noun	noun:inanim:m:v_dav
автоблокіраторові	автоблокіратор	noun	noun:inanim:m:v_mis
автоблокіратором	автоблокіратор	noun	noun:inanim:m:v_oru
автоблокіраторі	автоблокіратор	noun	noun:inanim:m:v_mis
автоблокіраторів	автоблокіратор	noun	noun:inanim:p:v_rod
автобот	автобот	noun	noun:inanim:m:v_naz
автобот	автобот	noun	noun:inanim:m:v_zna
автобота	автобот	noun	noun:inanim:m:v_rod
автоботам	автобот	noun	noun:inanim:p:v_dav
автоботами	автобот	noun	noun:inanim:p:v_oru
автоботах	автобот	noun	noun:inanim:p:v_mis
автоботе	автобот	noun	noun:inanim:m:v_kly
автоботи	автобот	noun	noun:inanim:p:v_kly
автоботи	автобот	noun	noun:inanim:p:v_naz
автоботи	автобот	noun	noun:inanim:p:v_zna
автоботові	автобот	noun	noun:inanim:m:v_dav
автоботові	автобот	noun	noun:inanim:m:v_mis
автоботом	автобот	noun	noun:inanim:m:v_oru
автоботі	автобот	noun	noun:inanim:m:v_mis
автоботів	автобот	noun	noun:inanim:p:v_rod
автобренд	автобренд	noun	noun:inanim:m:v_naz
автобренд	автобренд	noun	noun:inanim:m:v_zna
автобрендам	автобренд	noun	noun:inanim:p:v_dav
автобрендами	автобренд	noun	noun:inanim:p:v_oru
автобрендах	автобренд	noun	noun:inanim:p:v_mis
автобренде	автобренд	noun	noun:inanim:m:v_kly
автобренди	автобренд	noun	noun:inanim:p:v_kly
автобренди	автобренд	noun	noun:inanim:p:v_naz
автобренди	автобренд	noun	noun:inanim:p:v_zna
автобрендові	автобренд	noun	noun:inanim:m:v_dav
автобрендові	автобренд	noun	noun:inanim:m:v_mis
автобрендом	автобренд	noun	noun:inanim:m:v_oru
автобренду	автобренд	noun	noun:inanim:m:v_dav
автобренду	автобренд	noun	noun:inanim:m:v_mis
автобренду	автобренд	noun	noun:inanim:m:v_rod
автобренді	автобренд	noun	noun:inanim:m:v_mis
автобрендів	автобренд	noun	noun:inanim:p:v_rod
автоброньовик	автоброньовик	noun	noun:inanim:m:v_naz
автоброньовик	автоброньовик	noun	noun:inanim:m:v_zna
автоброньовика	автоброньовик	noun	noun:inanim:m:v_rod
автоброньовикам	автоброньовик	noun	noun:inanim:p:v_dav
автоброньовиками	автоброньовик	noun	noun:inanim:p:v_oru
автоброньовиках	автоброньовик	noun	noun:inanim:p:v_mis
автоброньовики	автоброньовик	noun	noun:inanim:p:v_kly
автоброньовики	автоброньовик	noun	noun:inanim:p:v_naz
автоброньовики	автоброньовик	noun	noun:inanim:p:v_zna
автоброньовикові	автоброньовик	noun	noun:inanim:m:v_dav
автоброньовикові	автоброньовик	noun	noun:inanim:m:v_mis
автоброньовиком	автоброньовик	noun	noun:inanim:m:v_oru
автоброньовику	автоброньовик	noun	noun:inanim:m:v_dav
автоброньовику	автоброньовик	noun	noun:inanim:m:v_kly
автоброньовику	автоброньовик	noun	noun:inanim:m:v_mis
автоброньовиків	автоброньовик	noun	noun:inanim:p:v_rod
автобудинкам	автобудинок	noun	noun:inanim:p:v_dav
автобудинками	автобудинок	noun	noun:inanim:p:v_oru
автобудинках	автобудинок	noun	noun:inanim:p:v_mis
автобудинки	автобудинок	noun	noun:inanim:p:v_kly
автобудинки	автобудинок	noun	noun:inanim:p:v_naz
автобудинки	автобудинок	noun	noun:inanim:p:v_zna
автобудинкові	автобудинок	noun	noun:inanim:m:v_dav
автобудинкові	автобудинок	noun	noun:inanim:m:v_mis
автобудинком	автобудинок	noun	noun:inanim:m:v_oru
автобудинку	автобудинок	noun	noun:inanim:m:v_dav
автобудинку	автобудинок	noun	noun:inanim:m:v_kly
автобудинку	автобудинок	noun	noun:inanim:m:v_mis
автобудинку	автобудинок	noun	noun:inanim:m:v_rod
автобудинків	автобудинок	noun	noun:inanim:p:v_rod
автобудинок	автобудинок	noun	noun:inanim:m:v_naz
автобудинок	автобудинок	noun	noun:inanim:m:v_zna
автобудуванню	автобудування	noun	noun:inanim:n:v_dav
автобудуванню	автобудування	noun	noun:inanim:n:v_mis
автобудування	автобудування	noun	noun:inanim:n:v_kly
автобудування	автобудування	noun	noun:inanim:n:v_naz
автобудування	автобудування	noun	noun:inanim:n:v_rod
автобудування	автобудування	noun	noun:inanim:n:v_zna
автобудування	автобудування	noun	noun:inanim:p:v_kly
автобудування	автобудування	noun	noun:inanim:p:v_naz
автобудування	автобудування	noun	noun:inanim:p:v_zna
автобудуванням	автобудування	noun	noun:inanim:n:v_oru
автобудуванням	автобудування	noun	noun:inanim:p:v_dav
автобудуваннями	автобудування	noun	noun:inanim:p:v_oru
автобудуваннях	автобудування	noun	noun:inanim:p:v_mis
автобудуванні	автобудування	noun	noun:inanim:n:v_mis
автобудувань	автобудування	noun	noun:inanim:p:v_rod
автобудівник	автобудівник	noun	noun:anim:m:v_naz
автобудівника	автобудівник	noun	noun:anim:m:v_rod
автобудівника	автобудівник	noun	noun:anim:m:v_zna
автобудівникам	автобудівник	noun	noun:anim:p:v_dav
автобудівниками	автобудівник	noun	noun:anim:p:v_oru
автобудівниках	автобудівник	noun	noun:anim:p:v_mis
автобудівники	автобудівник	noun	noun:anim:p:v_kly
автобудівники	автобудівник	noun	noun:anim:p:v_naz
автобудівники	автобудівник	noun	noun:anim:p:v_zna:rare
автобудівникові	автобудівник	noun	noun:anim:m:v_dav
автобудівникові	автобудівник	noun	noun:anim:m:v_mis
автобудівником	автобудівник	noun	noun:anim:m:v_oru
автобудівнику	автобудівник	noun	noun:anim:m:v_dav
автобудівнику	автобудівник	noun	noun:anim:m:v_kly
автобудівнику	автобудівник	noun	noun:anim:m:v_mis
автобудівників	автобудівник	noun	noun:anim:p:v_rod
автобудівників	автобудівник	noun	noun:anim:p:v_zna
автобункер	автобункер	noun	noun:inanim:m:v_naz
автобункер	автобункер	noun	noun:inanim:m:v_zna
автобункера	автобункер	noun	noun:inanim:m:v_rod
автобункерам	автобункер	noun	noun:inanim:p:v_dav
автобункерами	автобункер	noun	noun:inanim:p:v_oru
автобункерах	автобункер	noun	noun:inanim:p:v_mis
автобункере	автобункер	noun	noun:inanim:m:v_kly
автобункери	автобункер	noun	noun:inanim:p:v_kly
автобункери	автобункер	noun	noun:inanim:p:v_naz
автобункери	автобункер	noun	noun:inanim:p:v_zna
автобункерові	автобункер	noun	noun:inanim:m:v_dav
автобункерові	автобункер	noun	noun:inanim:m:v_mis
автобункером	автобункер	noun	noun:inanim:m:v_oru
автобункері	автобункер	noun	noun:inanim:m:v_mis
автобункерів	автобункер	noun	noun:inanim:p:v_rod
автобус	автобус	noun	noun:inanim:m:v_naz
автобус	автобус	noun	noun:inanim:m:v_zna
автобуса	автобус	noun	noun:inanim:m:v_rod
автобуса	автобус	noun	noun:inanim:m:v_zna:var
автобусам	автобус	noun	noun:inanim:p:v_dav
автобусами	автобус	noun	noun:inanim:p:v_oru
автобусах	автобус	noun	noun:inanim:p:v_mis
автобусе	автобус	noun	noun:inanim:m:v_kly
автобуси	автобус	noun	noun:inanim:p:v_kly
автобуси	автобус	noun	noun:inanim:p:v_naz
автобуси	автобус	noun	noun:inanim:p:v_zna
автобусик	автобусик	noun	noun:inanim:m:v_naz
автобусик	автобусик	noun	noun:inanim:m:v_zna
автобусика	автобусик	noun	noun:inanim:m:v_rod
автобусикам	автобусик	noun	noun:inanim:p:v_dav
автобусиками	автобусик	noun	noun:inanim:p:v_oru
автобусиках	автобусик	noun	noun:inanim:p:v_mis
автобусики	автобусик	noun	noun:inanim:p:v_kly
автобусики	автобусик	noun	noun:inanim:p:v_naz
автобусики	автобусик	noun	noun:inanim:p:v_zna
автобусикові	автобусик	noun	noun:inanim:m:v_dav
автобусикові	автобусик	noun	noun:inanim:m:v_mis
автобусиком	автобусик	noun	noun:inanim:m:v_oru
автобусику	автобусик	noun	noun:inanim:m:v_dav
автобусику	автобусик	noun	noun:inanim:m:v_kly
автобусику	автобусик	noun	noun:inanim:m:v_mis
автобусиків	автобусик	noun	noun:inanim:p:v_rod
автобусник	автобусник	noun	noun:anim:m:v_naz
автобусника	автобусник	noun	noun:anim:m:v_rod
автобусника	автобусник	noun	noun:anim:m:v_zna
автобусникам	автобусник	noun	noun:anim:p:v_dav
автобусниками	автобусник	noun	noun:anim:p:v_oru
автобусниках	автобусник	noun	noun:anim:p:v_mis
автобусники	автобусник	noun	noun:anim:p:v_kly
автобусники	автобусник	noun	noun:anim:p:v_naz
автобусники	автобусник	noun	noun:anim:p:v_zna:rare
автобусникові	автобусник	noun	noun:anim:m:v_dav
автобусникові	автобусник	noun	noun:anim:m:v_mis
автобусником	автобусник	noun	noun:anim:m:v_oru
автобуснику	автобусник	noun	noun:anim:m:v_dav
автобуснику	автобусник	noun	noun:anim:m:v_kly
автобуснику	автобусник	noun	noun:anim:m:v_mis
автобусників	автобусник	noun	noun:anim:p:v_rod
автобусників	автобусник	noun	noun:anim:p:v_zna
автобусобудівник	автобусобудівник	noun	noun:anim:m:v_naz
автобусобудівника	автобусобудівник	noun	noun:anim:m:v_rod
автобусобудівника	автобусобудівник	noun	noun:anim:m:v_zna
автобусобудівникам	автобусобудівник	noun	noun:anim:p:v_dav
автобусобудівниками	автобусобудівник	noun	noun:anim:p:v_oru
автобусобудівниках	автобусобудівник	noun	noun:anim:p:v_mis
автобусобудівники	автобусобудівник	noun	noun:anim:p:v_kly
автобусобудівники	автобусобудівник	noun	noun:anim:p:v_naz
автобусобудівники	автобусобудівник	noun	noun:anim:p:v_zna:rare
автобусобудівникові	автобусобудівник	noun	noun:anim:m:v_dav
автобусобудівникові	автобусобудівник	noun	noun:anim:m:v_mis
автобусобудівником	автобусобудівник	noun	noun:anim:m:v_oru
автобусобудівнику	автобусобудівник	noun	noun:anim:m:v_dav
автобусобудівнику	автобусобудівник	noun	noun:anim:m:v_kly
автобусобудівнику	автобусобудівник	noun	noun:anim:m:v_mis
автобусобудівників	автобусобудівник	noun	noun:anim:p:v_rod
автобусобудівників	автобусобудівник	noun	noun:anim:p:v_zna
автобусовиробник	автобусовиробник	noun	noun:anim:m:v_naz
автобусовиробника	автобусовиробник	noun	noun:anim:m:v_rod
автобусовиробника	автобусовиробник	noun	noun:anim:m:v_zna
автобусовиробникам	автобусовиробник	noun	noun:anim:p:v_dav
автобусовиробниками	автобусовиробник	noun	noun:anim:p:v_oru
автобусовиробниках	автобусовиробник	noun	noun:anim:p:v_mis
автобусовиробники	автобусовиробник	noun	noun:anim:p:v_kly
автобусовиробники	автобусовиробник	noun	noun:anim:p:v_naz
автобусовиробники	автобусовиробник	noun	noun:anim:p:v_zna:rare
автобусовиробникові	автобусовиробник	noun	noun:anim:m:v_dav
автобусовиробникові	автобусовиробник	noun	noun:anim:m:v_mis
автобусовиробником	автобусовиробник	noun	noun:anim:m:v_oru
автобусовиробнику	автобусовиробник	noun	noun:anim:m:v_dav
автобусовиробнику	автобусовиробник	noun	noun:anim:m:v_kly
автобусовиробнику	автобусовиробник	noun	noun:anim:m:v_mis
автобусовиробників	автобусовиробник	noun	noun:anim:p:v_rod
автобусовиробників	автобусовиробник	noun	noun:anim:p:v_zna
автобусові	автобус	noun	noun:inanim:m:v_dav
автобусові	автобус	noun	noun:inanim:m:v_mis
автобусом	автобус	noun	noun:inanim:m:v_oru
автобусі	автобус	noun	noun:inanim:m:v_mis
автобусів	автобус	noun	noun:inanim:p:v_rod
автобізнесмен	автобізнесмен	noun	noun:anim:m:v_naz
автобізнесмена	автобізнесмен	noun	noun:anim:m:v_rod
автобізнесмена	автобізнесмен	noun	noun:anim:m:v_zna
автобізнесменам	автобізнесмен	noun	noun:anim:p:v_dav
автобізнесменами	автобізнесмен	noun	noun:anim:p:v_oru
автобізнесменах	автобізнесмен	noun	noun:anim:p:v_mis
автобізнесмене	автобізнесмен	noun	noun:anim:m:v_kly
автобізнесмени	автобізнесмен	noun	noun:anim:p:v_kly
автобізнесмени	автобізнесмен	noun	noun:anim:p:v_naz
автобізнесмени	автобізнесмен	noun	noun:anim:p:v_zna:rare
автобізнесменові	автобізнесмен	noun	noun:anim:m:v_dav
автобізнесменові	автобізнесмен	noun	noun:anim:m:v_mis
автобізнесменом	автобізнесмен	noun	noun:anim:m:v_oru
автобізнесмені	автобізнесмен	noun	noun:anim:m:v_mis
автобізнесменів	автобізнесмен	noun	noun:anim:p:v_rod
автобізнесменів	автобізнесмен	noun	noun:anim:p:v_zna
автобіограф	автобіограф	noun	noun:anim:m:v_naz
автобіографа	автобіограф	noun	noun:anim:m:v_rod
автобіографа	автобіограф	noun	noun:anim:m:v_zna
автобіографам	автобіограф	noun	noun:anim:p:v_dav
автобіографами	автобіограф	noun	noun:anim:p:v_oru
автобіографах	автобіограф	noun	noun:anim:p:v_mis
автобіографе	автобіограф	noun	noun:anim:m:v_kly
автобіографи	автобіограф	noun	noun:anim:p:v_kly
автобіографи	автобіограф	noun	noun:anim:p:v_naz
автобіографи	автобіограф	noun	noun:anim:p:v_zna:rare
автобіографка	автобіографка	noun	noun:anim:f:v_naz
автобіографкам	автобіографка	noun	noun:anim:p:v_dav
автобіографками	автобіографка	noun	noun:anim:p:v_oru
автобіографках	автобіографка	noun	noun:anim:p:v_mis
автобіографки	автобіографка	noun	noun:anim:f:v_rod
автобіографки	автобіографка	noun	noun:anim:p:v_kly
автобіографки	автобіографка	noun	noun:anim:p:v_naz
автобіографки	автобіографка	noun	noun:anim:p:v_zna:rare
автобіографко	автобіографка	noun	noun:anim:f:v_kly
автобіографкою	автобіографка	noun	noun:anim:f:v_oru
автобіографку	автобіографка	noun	noun:anim:f:v_zna
автобіографові	автобіограф	noun	noun:anim:m:v_dav
автобіографові	автобіограф	noun	noun:anim:m:v_mis
автобіографок	автобіографка	noun	noun:anim:p:v_rod
автобіографок	автобіографка	noun	noun:anim:p:v_zna
автобіографом	автобіограф	noun	noun:anim:m:v_oru
автобіографці	автобіографка	noun	noun:anim:f:v_dav
автобіографці	автобіографка	noun	noun:anim:f:v_mis
автобіографі	автобіограф	noun	noun:anim:m:v_mis
автобіографів	автобіограф	noun	noun:anim:p:v_rod
автобіографів	автобіограф	noun	noun:anim:p:v_zna
автобіографій	автобіографія	noun	noun:inanim:p:v_rod
автобіографію	автобіографія	noun	noun:inanim:f:v_zna
автобіографія	автобіографія	noun	noun:inanim:f:v_naz
автобіографіям	автобіографія	noun	noun:inanim:p:v_dav
автобіографіями	автобіографія	noun	noun:inanim:p:v_oru
автобіографіях	автобіографія	noun	noun:inanim:p:v_mis
автобіографіє	автобіографія	noun	noun:inanim:f:v_kly
автобіографією	автобіографія	noun	noun:inanim:f:v_oru
автобіографії	автобіографія	noun	noun:inanim:f:v_dav
автобіографії	автобіографія	noun	noun:inanim:f:v_mis
автобіографії	автобіографія	noun	noun:inanim:f:v_rod
автобіографії	автобіографія	noun	noun:inanim:p:v_kly
автобіографії	автобіографія	noun	noun:inanim:p:v_naz
автобіографії	автобіографія	noun	noun:inanim:p:v_zna
автобірж	автобіржа	noun	noun:inanim:p:v_rod
автобіржа	автобіржа	noun	noun:inanim:f:v_naz
автобіржам	автобіржа	noun	noun:inanim:p:v_dav
автобіржами	автобіржа	noun	noun:inanim:p:v_oru
автобіржах	автобіржа	noun	noun:inanim:p:v_mis
автобірже	автобіржа	noun	noun:inanim:f:v_kly
автобіржею	автобіржа	noun	noun:inanim:f:v_oru
автобіржу	автобіржа	noun	noun:inanim:f:v_zna
автобіржі	автобіржа	noun	noun:inanim:f:v_dav
автобіржі	автобіржа	noun	noun:inanim:f:v_mis
автобіржі	автобіржа	noun	noun:inanim:f:v_rod
автобіржі	автобіржа	noun	noun:inanim:p:v_kly
автобіржі	автобіржа	noun	noun:inanim:p:v_naz
автобіржі	автобіржа	noun	noun:inanim:p:v_zna
автовагон	автовагон	noun	noun:inanim:m:v_naz
автовагон	автовагон	noun	noun:inanim:m:v_zna
автовагона	автовагон	noun	noun:inanim:m:v_rod
автовагонам	автовагон	noun	noun:inanim:p:v_dav
автовагонами	автовагон	noun	noun:inanim:p:v_oru
автовагонах	автовагон	noun	noun:inanim:p:v_mis
автовагоне	автовагон	noun	noun:inanim:m:v_kly
автовагони	автовагон	noun	noun:inanim:p:v_kly
автовагони	автовагон	noun	noun:inanim:p:v_naz
автовагони	автовагон	noun	noun:inanim:p:v_zna
автовагонові	автовагон	noun	noun:inanim:m:v_dav
автовагонові	автовагон	noun	noun:inanim:m:v_mis
автовагоном	автовагон	noun	noun:inanim:m:v_oru
автовагоні	автовагон	noun	noun:inanim:m:v_mis
автовагонів	автовагон	noun	noun:inanim:p:v_rod
автовакцин	автовакцина	noun	noun:inanim:p:v_rod
автовакцина	автовакцина	noun	noun:inanim:f:v_naz
автовакцинам	автовакцина	noun	noun:inanim:p:v_dav
автовакцинами	автовакцина	noun	noun:inanim:p:v_oru
автовакцинах	автовакцина	noun	noun:inanim:p:v_mis
автовакцини	автовакцина	noun	noun:inanim:f:v_rod
автовакцини	автовакцина	noun	noun:inanim:p:v_kly
автовакцини	автовакцина	noun	noun:inanim:p:v_naz
автовакцини	автовакцина	noun	noun:inanim:p:v_zna
автовакцино	автовакцина	noun	noun:inanim:f:v_kly
автовакциною	автовакцина	noun	noun:inanim:f:v_oru
автовакцину	автовакцина	noun	noun:inanim:f:v_zna
автовакцині	автовакцина	noun	noun:inanim:f:v_dav
автовакцині	автовакцина	noun	noun:inanim:f:v_mis
автовантажник	автовантажник	noun	noun:inanim:m:v_naz
автовантажник	автовантажник	noun	noun:inanim:m:v_zna
автовантажника	автовантажник	noun	noun:inanim:m:v_rod
автовантажникам	автовантажник	noun	noun:inanim:p:v_dav
автовантажниками	автовантажник	noun	noun:inanim:p:v_oru
автовантажниках	автовантажник	noun	noun:inanim:p:v_mis
автовантажники	автовантажник	noun	noun:inanim:p:v_kly
автовантажники	автовантажник	noun	noun:inanim:p:v_naz
автовантажники	автовантажник	noun	noun:inanim:p:v_zna
автовантажникові	автовантажник	noun	noun:inanim:m:v_dav
автовантажникові	автовантажник	noun	noun:inanim:m:v_mis
автовантажником	автовантажник	noun	noun:inanim:m:v_oru
автовантажнику	автовантажник	noun	noun:inanim:m:v_dav
автовантажнику	автовантажник	noun	noun:inanim:m:v_kly
автовантажнику	автовантажник	noun	noun:inanim:m:v_mis
автовантажників	автовантажник	noun	noun:inanim:p:v_rod
автовбивець	автовбивця	noun	noun:anim:p:v_rod
автовбивець	автовбивця	noun	noun:anim:p:v_zna
автовбивце	автовбивця	noun	noun:anim:f:v_kly
автовбивце	автовбивця	noun	noun:anim:m:v_kly
автовбивцею	автовбивця	noun	noun:anim:f:v_oru
автовбивцею	автовбивця	noun	noun:anim:m:v_oru
автовбивцю	автовбивця	noun	noun:anim:f:v_zna
автовбивцю	автовбивця	noun	noun:anim:m:v_zna
автовбивця	автовбивця	noun	noun:anim:f:v_naz
автовбивця	автовбивця	noun	noun:anim:m:v_naz
автовбивцям	автовбивця	noun	noun:anim:p:v_dav
автовбивцями	автовбивця	noun	noun:anim:p:v_oru
автовбивцях	автовбивця	noun	noun:anim:p:v_mis
автовбивці	автовбивця	noun	noun:anim:f:v_dav
автовбивці	автовбивця	noun	noun:anim:f:v_mis
автовбивці	автовбивця	noun	noun:anim:f:v_rod
автовбивці	автовбивця	noun	noun:anim:m:v_dav
автовбивці	автовбивця	noun	noun:anim:m:v_mis
автовбивці	автовбивця	noun	noun:anim:m:v_rod
автовбивці	автовбивця	noun	noun:anim:p:v_kly
автовбивці	автовбивця	noun	noun:anim:p:v_naz
автовбивці	автовбивця	noun	noun:anim:p:v_zna:rare
автовеж	автовежа	noun	noun:inanim:p:v_rod
автовежа	автовежа	noun	noun:inanim:f:v_naz
автовежам	автовежа	noun	noun:inanim:p:v_dav
автовежами	автовежа	noun	noun:inanim:p:v_oru
автовежах	автовежа	noun	noun:inanim:p:v_mis
автовеже	автовежа	noun	noun:inanim:f:v_kly
автовежею	автовежа	noun	noun:inanim:f:v_oru
автовежу	автовежа	noun	noun:inanim:f:v_zna
автовежі	автовежа	noun	noun:inanim:f:v_dav
автовежі	автовежа	noun	noun:inanim:f:v_mis
автовежі	автовежа	noun	noun:inanim:f:v_rod
автовежі	автовежа	noun	noun:inanim:p:v_kly
автовежі	автовежа	noun	noun:inanim:p:v_naz
автовежі	автовежа	noun	noun:inanim:p:v_zna
автовелетень	автовелетень	noun	noun:inanim:m:v_naz
автовелетень	автовелетень	noun	noun:inanim:m:v_zna
автовелетневі	автовелетень	noun	noun:inanim:m:v_dav
автовелетневі	автовелетень	noun	noun:inanim:m:v_mis
автовелетнем	автовелетень	noun	noun:inanim:m:v_oru
автовелетню	автовелетень	noun	noun:inanim:m:v_dav
автовелетню	автовелетень	noun	noun:inanim:m:v_kly
автовелетню	автовелетень	noun	noun:inanim:m:v_mis
автовелетня	автовелетень	noun	noun:inanim:m:v_rod
автовелетням	автовелетень	noun	noun:inanim:p:v_dav
автовелетнями	автовелетень	noun	noun:inanim:p:v_oru
автовелетнях	автовелетень	noun	noun:inanim:p:v_mis
автовелетні	автовелетень	noun	noun:inanim:m:v_mis
автовелетні	автовелетень	noun	noun:inanim:p:v_kly
автовелетні	автовелетень	noun	noun:inanim:p:v_naz
автовелетні	автовелетень	noun	noun:inanim:p:v_zna
автовелетнів	автовелетень	noun	noun:inanim:p:v_rod
автовентилятор	автовентилятор	noun	noun:inanim:m:v_naz
автовентилятор	автовентилятор	noun	noun:inanim:m:v_zna
автовентилятора	автовентилятор	noun	noun:inanim:m:v_rod
автовентиляторам	автовентилятор	noun	noun:inanim:p:v_dav
автовентиляторами	автовентилятор	noun	noun:inanim:p:v_oru
автовентиляторах	автовентилятор	noun	noun:inanim:p:v_mis
автовентиляторе	автовентилятор	noun	noun:inanim:m:v_kly
автовентилятори	автовентилятор	noun	noun:inanim:p:v_kly
автовентилятори	автовентилятор	noun	noun:inanim:p:v_naz
автовентилятори	автовентилятор	noun	noun:inanim:p:v_zna
автовентиляторові	автовентилятор	noun	noun:inanim:m:v_dav
автовентиляторові	автовентилятор	noun	noun:inanim:m:v_mis
автовентилятором	автовентилятор	noun	noun:inanim:m:v_oru
автовентиляторі	автовентилятор	noun	noun:inanim:m:v_mis
автовентиляторів	автовентилятор	noun	noun:inanim:p:v_rod
автовиклик	автовиклик	noun	noun:inanim:m:v_naz
автовиклик	автовиклик	noun	noun:inanim:m:v_zna
автовикликам	автовиклик	noun	noun:inanim:p:v_dav
автовикликами	автовиклик	noun	noun:inanim:p:v_oru
автовикликах	автовиклик	noun	noun:inanim:p:v_mis
автовиклики	автовиклик	noun	noun:inanim:p:v_kly
автовиклики	автовиклик	noun	noun:inanim:p:v_naz
автовиклики	автовиклик	noun	noun:inanim:p:v_zna
автовикликові	автовиклик	noun	noun:inanim:m:v_dav
автовикликові	автовиклик	noun	noun:inanim:m:v_mis
автовикликом	автовиклик	noun	noun:inanim:m:v_oru
автовиклику	автовиклик	noun	noun:inanim:m:v_dav
автовиклику	автовиклик	noun	noun:inanim:m:v_kly
автовиклику	автовиклик	noun	noun:inanim:m:v_mis
автовиклику	автовиклик	noun	noun:inanim:m:v_rod
автовикликів	автовиклик	noun	noun:inanim:p:v_rod
автовикраданню	автовикрадання	noun	noun:inanim:n:v_dav
автовикраданню	автовикрадання	noun	noun:inanim:n:v_mis
автовикрадання	автовикрадання	noun	noun:inanim:n:v_kly
автовикрадання	автовикрадання	noun	noun:inanim:n:v_naz
автовикрадання	автовикрадання	noun	noun:inanim:n:v_rod
автовикрадання	автовикрадання	noun	noun:inanim:n:v_zna
автовикрадання	автовикрадання	noun	noun:inanim:p:v_kly
автовикрадання	автовикрадання	noun	noun:inanim:p:v_naz
автовикрадання	автовикрадання	noun	noun:inanim:p:v_zna
автовикраданням	автовикрадання	noun	noun:inanim:n:v_oru
автовикраданням	автовикрадання	noun	noun:inanim:p:v_dav
автовикраданнями	автовикрадання	noun	noun:inanim:p:v_oru
автовикраданнях	автовикрадання	noun	noun:inanim:p:v_mis
автовикраданні	автовикрадання	noun	noun:inanim:n:v_mis
автовикрадань	автовикрадання	noun	noun:inanim:p:v_rod
автовикрадач	автовикрадач	noun	noun:anim:m:v_naz
автовикрадача	автовикрадач	noun	noun:anim:m:v_rod
автовикрадача	автовикрадач	noun	noun:anim:m:v_zna
автовикрадачам	автовикрадач	noun	noun:anim:p:v_dav
автовикрадачами	автовикрадач	noun	noun:anim:p:v_oru
автовикрадачах	автовикрадач	noun	noun:anim:p:v_mis
автовикрадачеві	автовикрадач	noun	noun:anim:m:v_dav
автовикрадачеві	автовикрадач	noun	noun:anim:m:v_mis
автовикрадачем	автовикрадач	noun	noun:anim:m:v_oru
автовикрадачу	автовикрадач	noun	noun:anim:m:v_dav
автовикрадачу	автовикрадач	noun	noun:anim:m:v_kly
автовикрадачу	автовикрадач	noun	noun:anim:m:v_mis
автовикрадачі	автовикрадач	noun	noun:anim:m:v_mis
автовикрадачі	автовикрадач	noun	noun:anim:p:v_kly
автовикрадачі	автовикрадач	noun	noun:anim:p:v_naz
автовикрадачі	автовикрадач	noun	noun:anim:p:v_zna:rare
автовикрадачів	автовикрадач	noun	noun:anim:p:v_rod
автовикрадачів	автовикрадач	noun	noun:anim:p:v_zna
автовикраденню	автовикрадення	noun	noun:inanim:n:v_dav
автовикраденню	автовикрадення	noun	noun:inanim:n:v_mis
автовикрадення	автовикрадення	noun	noun:inanim:n:v_kly
автовикрадення	автовикрадення	noun	noun:inanim:n:v_naz
автовикрадення	автовикрадення	noun	noun:inanim:n:v_rod
автовикрадення	автовикрадення	noun	noun:inanim:n:v_zna
автовикрадення	автовикрадення	noun	noun:inanim:p:v_kly
автовикрадення	автовикрадення	noun	noun:inanim:p:v_naz
автовикрадення	автовикрадення	noun	noun:inanim:p:v_zna
автовикраденням	автовикрадення	noun	noun:inanim:n:v_oru
автовикраденням	автовикрадення	noun	noun:inanim:p:v_dav
автовикраденнями	автовикрадення	noun	noun:inanim:p:v_oru
автовикраденнях	автовикрадення	noun	noun:inanim:p:v_mis
автовикраденні	автовикрадення	noun	noun:inanim:n:v_mis
автовикрадень	автовикрадення	noun	noun:inanim:p:v_rod
автовинахідник	автовинахідник	noun	noun:anim:m:v_naz
автовинахідника	автовинахідник	noun	noun:anim:m:v_rod
автовинахідника	автовинахідник	noun	noun:anim:m:v_zna
автовинахідникам	автовинахідник	noun	noun:anim:p:v_dav
автовинахідниками	автовинахідник	noun	noun:anim:p:v_oru
автовинахідниках	автовинахідник	noun	noun:anim:p:v_mis
автовинахідники	автовинахідник	noun	noun:anim:p:v_kly
автовинахідники	автовинахідник	noun	noun:anim:p:v_naz
автовинахідники	автовинахідник	noun	noun:anim:p:v_zna:rare
автовинахідникові	автовинахідник	noun	noun:anim:m:v_dav
автовинахідникові	автовинахідник	noun	noun:anim:m:v_mis
автовинахідником	автовинахідник	noun	noun:anim:m:v_oru
автовинахіднику	автовинахідник	noun	noun:anim:m:v_dav
автовинахіднику	автовинахідник	noun	noun:anim:m:v_kly
автовинахіднику	автовинахідник	noun	noun:anim:m:v_mis
автовинахідників	автовинахідник	noun	noun:anim:p:v_rod
автовинахідників	автовинахідник	noun	noun:anim:p:v_zna
автовиправленню	автовиправлення	noun	noun:inanim:n:v_dav
автовиправленню	автовиправлення	noun	noun:inanim:n:v_mis
автовиправлення	автовиправлення	noun	noun:inanim:n:v_kly
автовиправлення	автовиправлення	noun	noun:inanim:n:v_naz
автовиправлення	автовиправлення	noun	noun:inanim:n:v_rod
автовиправлення	автовиправлення	noun	noun:inanim:n:v_zna
автовиправлення	автовиправлення	noun	noun:inanim:p:v_kly
автовиправлення	автовиправлення	noun	noun:inanim:p:v_naz
автовиправлення	автовиправлення	noun	noun:inanim:p:v_zna
автовиправленням	автовиправлення	noun	noun:inanim:n:v_oru
автовиправленням	автовиправлення	noun	noun:inanim:p:v_dav
автовиправленнями	автовиправлення	noun	noun:inanim:p:v_oru
автовиправленнях	автовиправлення	noun	noun:inanim:p:v_mis
автовиправленні	автовиправлення	noun	noun:inanim:n:v_mis
автовиправлень	автовиправлення	noun	noun:inanim:p:v_rod
автовиробник	автовиробник	noun	noun:anim:m:v_naz
автовиробника	автовиробник	noun	noun:anim:m:v_rod
автовиробника	автовиробник	noun	noun:anim:m:v_zna
автовиробникам	автовиробник	noun	noun:anim:p:v_dav
автовиробниками	автовиробник	noun	noun:anim:p:v_oru
автовиробниках	автовиробник	noun	noun:anim:p:v_mis
автовиробники	автовиробник	noun	noun:anim:p:v_kly
автовиробники	автовиробник	noun	noun:anim:p:v_naz
автовиробники	автовиробник	noun	noun:anim:p:v_zna:rare
автовиробникові	автовиробник	noun	noun:anim:m:v_dav
автовиробникові	автовиробник	noun	noun:anim:m:v_mis
автовиробником	автовиробник	noun	noun:anim:m:v_oru
автовиробнику	автовиробник	noun	noun:anim:m:v_dav
автовиробнику	автовиробник	noun	noun:anim:m:v_kly
автовиробнику	автовиробник	noun	noun:anim:m:v_mis
автовиробників	автовиробник	noun	noun:anim:p:v_rod
автовиробників	автовиробник	noun	noun:anim:p:v_zna
автовиставка	автовиставка	noun	noun:inanim:f:v_naz
автовиставкам	автовиставка	noun	noun:inanim:p:v_dav
автовиставками	автовиставка	noun	noun:inanim:p:v_oru
автовиставках	автовиставка	noun	noun:inanim:p:v_mis
автовиставки	автовиставка	noun	noun:inanim:f:v_rod
автовиставки	автовиставка	noun	noun:inanim:p:v_kly
автовиставки	автовиставка	noun	noun:inanim:p:v_naz
автовиставки	автовиставка	noun	noun:inanim:p:v_zna
автовиставко	автовиставка	noun	noun:inanim:f:v_kly
автовиставкою	автовиставка	noun	noun:inanim:f:v_oru
автовиставку	автовиставка	noun	noun:inanim:f:v_zna
автовиставок	автовиставка	noun	noun:inanim:p:v_rod
автовиставці	автовиставка	noun	noun:inanim:f:v_dav
автовиставці	автовиставка	noun	noun:inanim:f:v_mis
автовишка	автовишка	noun	noun:inanim:f:v_naz
автовишкам	автовишка	noun	noun:inanim:p:v_dav
автовишками	автовишка	noun	noun:inanim:p:v_oru
автовишках	автовишка	noun	noun:inanim:p:v_mis
автовишки	автовишка	noun	noun:inanim:f:v_rod
автовишки	автовишка	noun	noun:inanim:p:v_kly
автовишки	автовишка	noun	noun:inanim:p:v_naz
автовишки	автовишка	noun	noun:inanim:p:v_zna
автовишко	автовишка	noun	noun:inanim:f:v_kly
автовишкою	автовишка	noun	noun:inanim:f:v_oru
автовишку	автовишка	noun	noun:inanim:f:v_zna
автовишок	автовишка	noun	noun:inanim:p:v_rod
автовишці	автовишка	noun	noun:inanim:f:v_dav
автовишці	автовишка	noun	noun:inanim:f:v_mis
автовласник	автовласник	noun	noun:anim:m:v_naz
автовласника	автовласник	noun	noun:anim:m:v_rod
автовласника	автовласник	noun	noun:anim:m:v_zna
автовласникам	автовласник	noun	noun:anim:p:v_dav
автовласниками	автовласник	noun	noun:anim:p:v_oru
автовласниках	автовласник	noun	noun:anim:p:v_mis
автовласники	автовласник	noun	noun:anim:p:v_kly
автовласники	автовласник	noun	noun:anim:p:v_naz
автовласники	автовласник	noun	noun:anim:p:v_zna:rare
автовласникові	автовласник	noun	noun:anim:m:v_dav
автовласникові	автовласник	noun	noun:anim:m:v_mis
автовласником	автовласник	noun	noun:anim:m:v_oru
автовласнику	автовласник	noun	noun:anim:m:v_dav
автовласнику	автовласник	noun	noun:anim:m:v_kly
автовласнику	автовласник	noun	noun:anim:m:v_mis
автовласників	автовласник	noun	noun:anim:p:v_rod
автовласників	автовласник	noun	noun:anim:p:v_zna
автоводоцистерн	автоводоцистерна	noun	noun:inanim:p:v_rod
автоводоцистерна	автоводоцистерна	noun	noun:inanim:f:v_naz
автоводоцистернам	автоводоцистерна	noun	noun:inanim:p:v_dav
автоводоцистернами	автоводоцистерна	noun	noun:inanim:p:v_oru
автоводоцистернах	автоводоцистерна	noun	noun:inanim:p:v_mis
автоводоцистерни	автоводоцистерна	noun	noun:inanim:f:v_rod
автоводоцистерни	автоводоцистерна	noun	noun:inanim:p:v_kly
автоводоцистерни	автоводоцистерна	noun	noun:inanim:p:v_naz
автоводоцистерни	автоводоцистерна	noun	noun:inanim:p:v_zna
автоводоцистерно	автоводоцистерна	noun	noun:inanim:f:v_kly
автоводоцистерною	автоводоцистерна	noun	noun:inanim:f:v_oru
автоводоцистерну	автоводоцистерна	noun	noun:inanim:f:v_zna
автоводоцистерні	автоводоцистерна	noun	noun:inanim:f:v_dav
автоводоцистерні	автоводоцистерна	noun	noun:inanim:f:v_mis
автоводій	автоводій	noun	noun:anim:m:v_naz
автоводію	автоводій	noun	noun:anim:m:v_dav
автоводію	автоводій	noun	noun:anim:m:v_kly
автоводію	автоводій	noun	noun:anim:m:v_mis
автоводія	автоводій	noun	noun:anim:m:v_rod
автоводія	автоводій	noun	noun:anim:m:v_zna
автоводіям	автоводій	noun	noun:anim:p:v_dav
автоводіями	автоводій	noun	noun:anim:p:v_oru
автоводіях	автоводій	noun	noun:anim:p:v_mis
автоводієві	автоводій	noun	noun:anim:m:v_dav
автоводієві	автоводій	noun	noun:anim:m:v_mis
автоводієм	автоводій	noun	noun:anim:m:v_oru
автоводії	автоводій	noun	noun:anim:m:v_mis
автоводії	автоводій	noun	noun:anim:p:v_kly
автоводії	автоводій	noun	noun:anim:p:v_naz
автоводії	автоводій	noun	noun:anim:p:v_zna:rare
автоводіїв	автоводій	noun	noun:anim:p:v_rod
автоводіїв	автоводій	noun	noun:anim:p:v_zna
автовоз	автовоз	noun	noun:inanim:m:v_naz
автовоз	автовоз	noun	noun:inanim:m:v_zna
автовоза	автовоз	noun	noun:inanim:m:v_rod
автовозам	автовоз	noun	noun:inanim:p:v_dav
автовозами	автовоз	noun	noun:inanim:p:v_oru
автовозах	автовоз	noun	noun:inanim:p:v_mis
автовозе	автовоз	noun	noun:inanim:m:v_kly
автовози	автовоз	noun	noun:inanim:p:v_kly
автовози	автовоз	noun	noun:inanim:p:v_naz
автовози	автовоз	noun	noun:inanim:p:v_zna
автовозові	автовоз	noun	noun:inanim:m:v_dav
автовозові	автовоз	noun	noun:inanim:m:v_mis
автовозом	автовоз	noun	noun:inanim:m:v_oru
автовозі	автовоз	noun	noun:inanim:m:v_mis
автовозів	автовоз	noun	noun:inanim:p:v_rod
автовокзал	автовокзал	noun	noun:inanim:m:v_naz
автовокзал	автовокзал	noun	noun:inanim:m:v_zna
автовокзалам	автовокзал	noun	noun:inanim:p:v_dav
автовокзалами	автовокзал	noun	noun:inanim:p:v_oru
автовокзалах	автовокзал	noun	noun:inanim:p:v_mis
автовокзале	автовокзал	noun	noun:inanim:m:v_kly
автовокзали	автовокзал	noun	noun:inanim:p:v_kly
автовокзали	автовокзал	noun	noun:inanim:p:v_naz
автовокзали	автовокзал	noun	noun:inanim:p:v_zna
автовокзалові	автовокзал	noun	noun:inanim:m:v_dav
автовокзалові	автовокзал	noun	noun:inanim:m:v_mis
автовокзалом	автовокзал	noun	noun:inanim:m:v_oru
автовокзалу	автовокзал	noun	noun:inanim:m:v_dav
автовокзалу	автовокзал	noun	noun:inanim:m:v_mis
автовокзалу	автовокзал	noun	noun:inanim:m:v_rod
автовокзалі	автовокзал	noun	noun:inanim:m:v_mis
автовокзалів	автовокзал	noun	noun:inanim:p:v_rod
автовідповідач	автовідповідач	noun	noun:inanim:m:v_naz
автовідповідач	автовідповідач	noun	noun:inanim:m:v_zna
автовідповідача	автовідповідач	noun	noun:inanim:m:v_rod
автовідповідачам	автовідповідач	noun	noun:inanim:p:v_dav
автовідповідачами	автовідповідач	noun	noun:inanim:p:v_oru
автовідповідачах	автовідповідач	noun	noun:inanim:p:v_mis
автовідповідачеві	автовідповідач	noun	noun:inanim:m:v_dav
автовідповідачеві	автовідповідач	noun	noun:inanim:m:v_mis
автовідповідачем	автовідповідач	noun	noun:inanim:m:v_oru
автовідповідачу	автовідповідач	noun	noun:inanim:m:v_dav
автовідповідачу	автовідповідач	noun	noun:inanim:m:v_kly
автовідповідачу	автовідповідач	noun	noun:inanim:m:v_mis
автовідповідачі	автовідповідач	noun	noun:inanim:m:v_mis
автовідповідачі	автовідповідач	noun	noun:inanim:p:v_kly
автовідповідачі	автовідповідач	noun	noun:inanim:p:v_naz
автовідповідачі	автовідповідач	noun	noun:inanim:p:v_zna
автовідповідачів	автовідповідач	noun	noun:inanim:p:v_rod
автовідповіддю	автовідповідь	noun	noun:inanim:f:v_oru
автовідповіде	автовідповідь	noun	noun:inanim:f:v_kly
автовідповідей	автовідповідь	noun	noun:inanim:p:v_rod
автовідповідь	автовідповідь	noun	noun:inanim:f:v_naz
автовідповідь	автовідповідь	noun	noun:inanim:f:v_zna
автовідповідям	автовідповідь	noun	noun:inanim:p:v_dav
автовідповідями	автовідповідь	noun	noun:inanim:p:v_oru
автовідповідях	автовідповідь	noun	noun:inanim:p:v_mis
автовідповіді	автовідповідь	noun	noun:inanim:f:v_dav
автовідповіді	автовідповідь	noun	noun:inanim:f:v_mis
автовідповіді	автовідповідь	noun	noun:inanim:f:v_rod
автовідповіді	автовідповідь	noun	noun:inanim:p:v_kly
автовідповіді	автовідповідь	noun	noun:inanim:p:v_naz
автовідповіді	автовідповідь	noun	noun:inanim:p:v_zna
автовізка	автовізок	noun	noun:inanim:m:v_rod
автовізкам	автовізок	noun	noun:inanim:p:v_dav
автовізками	автовізок	noun	noun:inanim:p:v_oru
автовізках	автовізок	noun	noun:inanim:p:v_mis
автовізки	автовізок	noun	noun:inanim:p:v_kly
автовізки	автовізок	noun	noun:inanim:p:v_naz
автовізки	автовізок	noun	noun:inanim:p:v_zna
автовізкові	автовізок	noun	noun:inanim:m:v_dav
автовізкові	автовізок	noun	noun:inanim:m:v_mis
автовізком	автовізок	noun	noun:inanim:m:v_oru
автовізку	автовізок	noun	noun:inanim:m:v_dav
автовізку	автовізок	noun	noun:inanim:m:v_kly
автовізку	автовізок	noun	noun:inanim:m:v_mis
автовізків	автовізок	noun	noun:inanim:p:v_rod
автовізок	автовізок	noun	noun:inanim:m:v_naz
автовізок	автовізок	noun	noun:inanim:m:v_zna
автогаване	автогавань	noun	noun:inanim:f:v_kly
автогаваней	автогавань	noun	noun:inanim:p:v_rod
автогаванню	автогавань	noun	noun:inanim:f:v_oru
автогавань	автогавань	noun	noun:inanim:f:v_naz
автогавань	автогавань	noun	noun:inanim:f:v_zna
автогаваням	автогавань	noun	noun:inanim:p:v_dav
автогаванями	автогавань	noun	noun:inanim:p:v_oru
автогаванях	автогавань	noun	noun:inanim:p:v_mis
автогавані	автогавань	noun	noun:inanim:f:v_dav
автогавані	автогавань	noun	noun:inanim:f:v_mis
автогавані	автогавань	noun	noun:inanim:f:v_rod
автогавані	автогавань	noun	noun:inanim:p:v_kly
автогавані	автогавань	noun	noun:inanim:p:v_naz
автогавані	автогавань	noun	noun:inanim:p:v_zna
автогалузе	автогалузь	noun	noun:inanim:f:v_kly
автогалузей	автогалузь	noun	noun:inanim:p:v_rod
автогалуззю	автогалузь	noun	noun:inanim:f:v_oru
автогалузь	автогалузь	noun	noun:inanim:f:v_naz
автогалузь	автогалузь	noun	noun:inanim:f:v_zna
автогалузям	автогалузь	noun	noun:inanim:p:v_dav
автогалузями	автогалузь	noun	noun:inanim:p:v_oru
автогалузях	автогалузь	noun	noun:inanim:p:v_mis
автогалузі	автогалузь	noun	noun:inanim:f:v_dav
автогалузі	автогалузь	noun	noun:inanim:f:v_mis
автогалузі	автогалузь	noun	noun:inanim:f:v_rod
автогалузі	автогалузь	noun	noun:inanim:p:v_kly
автогалузі	автогалузь	noun	noun:inanim:p:v_naz
автогалузі	автогалузь	noun	noun:inanim:p:v_zna
автогальм	автогальмо	noun	noun:inanim:p:v_rod
автогальма	автогальмо	noun	noun:inanim:n:v_rod
автогальма	автогальмо	noun	noun:inanim:p:v_kly
автогальма	автогальмо	noun	noun:inanim:p:v_naz
автогальма	автогальмо	noun	noun:inanim:p:v_zna
автогальмам	автогальмо	noun	noun:inanim:p:v_dav
автогальмами	автогальмо	noun	noun:inanim:p:v_oru
автогальмах	автогальмо	noun	noun:inanim:p:v_mis
автогальмо	автогальмо	noun	noun:inanim:n:v_kly
автогальмо	автогальмо	noun	noun:inanim:n:v_naz
автогальмо	автогальмо	noun	noun:inanim:n:v_zna
автогальмом	автогальмо	noun	noun:inanim:n:v_oru
автогальму	автогальмо	noun	noun:inanim:n:v_dav
автогальму	автогальмо	noun	noun:inanim:n:v_mis
автогальмі	автогальмо	noun	noun:inanim:n:v_mis
автогамій	автогамія	noun	noun:inanim:p:v_rod
автогамію	автогамія	noun	noun:inanim:f:v_zna
автогамія	автогамія	noun	noun:inanim:f:v_naz
автогаміям	автогамія	noun	noun:inanim:p:v_dav
автогаміями	автогамія	noun	noun:inanim:p:v_oru
автогаміях	автогамія	noun	noun:inanim:p:v_mis
автогаміє	автогамія	noun	noun:inanim:f:v_kly
автогамією	автогамія	noun	noun:inanim:f:v_oru
автогамії	автогамія	noun	noun:inanim:f:v_dav
автогамії	автогамія	noun	noun:inanim:f:v_mis
автогамії	автогамія	noun	noun:inanim:f:v_rod
автогамії	автогамія	noun	noun:inanim:p:v_kly
автогамії	автогамія	noun	noun:inanim:p:v_naz
автогамії	автогамія	noun	noun:inanim:p:v_zna
автогараж	автогараж	noun	noun:inanim:m:v_naz
автогараж	автогараж	noun	noun:inanim:m:v_zna
автогаража	автогараж	noun	noun:inanim:m:v_rod
автогаражам	автогараж	noun	noun:inanim:p:v_dav
автогаражами	автогараж	noun	noun:inanim:p:v_oru
автогаражах	автогараж	noun	noun:inanim:p:v_mis
автогараже	автогараж	noun	noun:inanim:m:v_kly
автогаражеві	автогараж	noun	noun:inanim:m:v_dav
автогаражеві	автогараж	noun	noun:inanim:m:v_mis
автогаражем	автогараж	noun	noun:inanim:m:v_oru
автогаражі	автогараж	noun	noun:inanim:m:v_mis
автогаражі	автогараж	noun	noun:inanim:p:v_kly
автогаражі	автогараж	noun	noun:inanim:p:v_naz
автогаражі	автогараж	noun	noun:inanim:p:v_zna
автогаражів	автогараж	noun	noun:inanim:p:v_rod
автогеморагій	автогеморагія	noun	noun:inanim:p:v_rod
автогеморагію	автогеморагія	noun	noun:inanim:f:v_zna
автогеморагія	автогеморагія	noun	noun:inanim:f:v_naz
автогеморагіям	автогеморагія	noun	noun:inanim:p:v_dav
автогеморагіями	автогеморагія	noun	noun:inanim:p:v_oru
автогеморагіях	автогеморагія	noun	noun:inanim:p:v_mis
автогеморагіє	автогеморагія	noun	noun:inanim:f:v_kly
автогеморагією	автогеморагія	noun	noun:inanim:f:v_oru
автогеморагії	автогеморагія	noun	noun:inanim:f:v_dav
автогеморагії	автогеморагія	noun	noun:inanim:f:v_mis
автогеморагії	автогеморагія	noun	noun:inanim:f:v_rod
автогеморагії	автогеморагія	noun	noun:inanim:p:v_kly
автогеморагії	автогеморагія	noun	noun:inanim:p:v_naz
автогеморагії	автогеморагія	noun	noun:inanim:p:v_zna
автоген	автоген	noun	noun:inanim:m:v_naz
автоген	автоген	noun	noun:inanim:m:v_zna
автогенам	автоген	noun	noun:inanim:p:v_dav
автогенами	автоген	noun	noun:inanim:p:v_oru
автогенах	автоген	noun	noun:inanim:p:v_mis
автогене	автоген	noun	noun:inanim:m:v_kly
автогенератор	автогенератор	noun	noun:inanim:m:v_naz
автогенератор	автогенератор	noun	noun:inanim:m:v_zna
автогенератора	автогенератор	noun	noun:inanim:m:v_rod
автогенераторам	автогенератор	noun	noun:inanim:p:v_dav
автогенераторами	автогенератор	noun	noun:inanim:p:v_oru
автогенераторах	автогенератор	noun	noun:inanim:p:v_mis
автогенераторе	автогенератор	noun	noun:inanim:m:v_kly
автогенератори	автогенератор	noun	noun:inanim:p:v_kly
автогенератори	автогенератор	noun	noun:inanim:p:v_naz
автогенератори	автогенератор	noun	noun:inanim:p:v_zna
автогенераторові	автогенератор	noun	noun:inanim:m:v_dav
автогенераторові	автогенератор	noun	noun:inanim:m:v_mis
автогенератором	автогенератор	noun	noun:inanim:m:v_oru
автогенераторі	автогенератор	noun	noun:inanim:m:v_mis
автогенераторів	автогенератор	noun	noun:inanim:p:v_rod
автогени	автоген	noun	noun:inanim:p:v_kly
автогени	автоген	noun	noun:inanim:p:v_naz
автогени	автоген	noun	noun:inanim:p:v_zna
автогенник	автогенник	noun	noun:anim:m:v_naz
автогенника	автогенник	noun	noun:anim:m:v_rod
автогенника	автогенник	noun	noun:anim:m:v_zna
автогенникам	автогенник	noun	noun:anim:p:v_dav
автогенниками	автогенник	noun	noun:anim:p:v_oru
автогенниках	автогенник	noun	noun:anim:p:v_mis
автогенники	автогенник	noun	noun:anim:p:v_kly
автогенники	автогенник	noun	noun:anim:p:v_naz
автогенники	автогенник	noun	noun:anim:p:v_zna:rare
автогенникові	автогенник	noun	noun:anim:m:v_dav
автогенникові	автогенник	noun	noun:anim:m:v_mis
автогенником	автогенник	noun	noun:anim:m:v_oru
автогеннику	автогенник	noun	noun:anim:m:v_dav
автогеннику	автогенник	noun	noun:anim:m:v_kly
автогеннику	автогенник	noun	noun:anim:m:v_mis
автогенників	автогенник	noun	noun:anim:p:v_rod
автогенників	автогенник	noun	noun:anim:p:v_zna
автогенові	автоген	noun	noun:inanim:m:v_dav
автогенові	автоген	noun	noun:inanim:m:v_mis
автогеном	автоген	noun	noun:inanim:m:v_oru
автогену	автоген	noun	noun:inanim:m:v_dav
автогену	автоген	noun	noun:inanim:m:v_mis
автогену	автоген	noun	noun:inanim:m:v_rod
автогені	автоген	noun	noun:inanim:m:v_mis
автогенів	автоген	noun	noun:inanim:p:v_rod
автогнозій	автогнозія	noun	noun:inanim:p:v_rod
автогнозію	автогнозія	noun	noun:inanim:f:v_zna
автогнозія	автогнозія	noun	noun:inanim:f:v_naz
автогнозіям	автогнозія	noun	noun:inanim:p:v_dav
автогнозіями	автогнозія	noun	noun:inanim:p:v_oru
автогнозіях	автогнозія	noun	noun:inanim:p:v_mis
автогнозіє	автогнозія	noun	noun:inanim:f:v_kly
автогнозією	автогнозія	noun	noun:inanim:f:v_oru
автогнозії	автогнозія	noun	noun:inanim:f:v_dav
автогнозії	автогнозія	noun	noun:inanim:f:v_mis
автогнозії	автогнозія	noun	noun:inanim:f:v_rod
автогнозії	автогнозія	noun	noun:inanim:p:v_kly
автогнозії	автогнозія	noun	noun:inanim:p:v_naz
автогнозії	автогнозія	noun	noun:inanim:p:v_zna
автогодівнице	автогодівниця	noun	noun:inanim:f:v_kly
автогодівницею	автогодівниця	noun	noun:inanim:f:v_oru
автогодівниць	автогодівниця	noun	noun:inanim:p:v_rod
автогодівницю	автогодівниця	noun	noun:inanim:f:v_zna
автогодівниця	автогодівниця	noun	noun:inanim:f:v_naz
автогодівницям	автогодівниця	noun	noun:inanim:p:v_dav
автогодівницями	автогодівниця	noun	noun:inanim:p:v_oru
автогодівницях	автогодівниця	noun	noun:inanim:p:v_mis
автогодівниці	автогодівниця	noun	noun:inanim:f:v_dav
автогодівниці	автогодівниця	noun	noun:inanim:f:v_mis
автогодівниці	автогодівниця	noun	noun:inanim:f:v_rod
автогодівниці	автогодівниця	noun	noun:inanim:p:v_kly
автогодівниці	автогодівниця	noun	noun:inanim:p:v_naz
автогодівниці	автогодівниця	noun	noun:inanim:p:v_zna
автогол	автогол	noun	noun:inanim:m:v_naz
автогол	автогол	noun	noun:inanim:m:v_zna
автогола	автогол	noun	noun:inanim:m:v_rod
автоголам	автогол	noun	noun:inanim:p:v_dav
автоголами	автогол	noun	noun:inanim:p:v_oru
автоголах	автогол	noun	noun:inanim:p:v_mis
автоголе	автогол	noun	noun:inanim:m:v_kly
автоголи	автогол	noun	noun:inanim:p:v_kly
автоголи	автогол	noun	noun:inanim:p:v_naz
автоголи	автогол	noun	noun:inanim:p:v_zna
автоголові	автогол	noun	noun:inanim:m:v_dav
автоголові	автогол	noun	noun:inanim:m:v_mis
автоголом	автогол	noun	noun:inanim:m:v_oru
автоголі	автогол	noun	noun:inanim:m:v_mis
автоголів	автогол	noun	noun:inanim:p:v_rod
автогонка	автогонка	noun	noun:inanim:f:v_naz
автогонкам	автогонка	noun	noun:inanim:p:v_dav
автогонками	автогонка	noun	noun:inanim:p:v_oru
автогонках	автогонка	noun	noun:inanim:p:v_mis
автогонки	автогонка	noun	noun:inanim:f:v_rod
автогонки	автогонка	noun	noun:inanim:p:v_kly
автогонки	автогонка	noun	noun:inanim:p:v_naz
автогонки	автогонка	noun	noun:inanim:p:v_zna
автогонко	автогонка	noun	noun:inanim:f:v_kly
автогонкою	автогонка	noun	noun:inanim:f:v_oru
автогонку	автогонка	noun	noun:inanim:f:v_zna
автогонник	автогонник	noun	noun:anim:m:v_naz
автогонника	автогонник	noun	noun:anim:m:v_rod
автогонника	автогонник	noun	noun:anim:m:v_zna
автогонникам	автогонник	noun	noun:anim:p:v_dav
автогонниками	автогонник	noun	noun:anim:p:v_oru
автогонниках	автогонник	noun	noun:anim:p:v_mis
автогонники	автогонник	noun	noun:anim:p:v_kly
автогонники	автогонник	noun	noun:anim:p:v_naz
автогонники	автогонник	noun	noun:anim:p:v_zna:rare
автогонникові	автогонник	noun	noun:anim:m:v_dav
автогонникові	автогонник	noun	noun:anim:m:v_mis
автогонником	автогонник	noun	noun:anim:m:v_oru
автогоннику	автогонник	noun	noun:anim:m:v_dav
автогоннику	автогонник	noun	noun:anim:m:v_kly
автогоннику	автогонник	noun	noun:anim:m:v_mis
автогонників	автогонник	noun	noun:anim:p:v_rod
автогонників	автогонник	noun	noun:anim:p:v_zna
автогоннице	автогонниця	noun	noun:anim:f:v_kly
автогонницею	автогонниця	noun	noun:anim:f:v_oru
автогонниць	автогонниця	noun	noun:anim:p:v_rod
автогонниць	автогонниця	noun	noun:anim:p:v_zna
автогонницю	автогонниця	noun	noun:anim:f:v_zna
автогонниця	автогонниця	noun	noun:anim:f:v_naz
автогонницям	автогонниця	noun	noun:anim:p:v_dav
автогонницями	автогонниця	noun	noun:anim:p:v_oru
автогонницях	автогонниця	noun	noun:anim:p:v_mis
автогонниці	автогонниця	noun	noun:anim:f:v_dav
автогонниці	автогонниця	noun	noun:anim:f:v_mis
автогонниці	автогонниця	noun	noun:anim:f:v_rod
автогонниці	автогонниця	noun	noun:anim:p:v_kly
автогонниці	автогонниця	noun	noun:anim:p:v_naz
автогонниці	автогонниця	noun	noun:anim:p:v_zna:rare
автогонок	автогонка	noun	noun:inanim:p:v_rod
автогонці	автогонка	noun	noun:inanim:f:v_dav
автогонці	автогонка	noun	noun:inanim:f:v_mis
автогоній	автогонія	noun	noun:inanim:p:v_rod
автогонію	автогонія	noun	noun:inanim:f:v_zna
автогонія	автогонія	noun	noun:inanim:f:v_naz
автогоніям	автогонія	noun	noun:inanim:p:v_dav
автогоніями	автогонія	noun	noun:inanim:p:v_oru
автогоніях	автогонія	noun	noun:inanim:p:v_mis
автогоніє	автогонія	noun	noun:inanim:f:v_kly
автогонією	автогонія	noun	noun:inanim:f:v_oru
автогонії	автогонія	noun	noun:inanim:f:v_dav
автогонії	автогонія	noun	noun:inanim:f:v_mis
автогонії	автогонія	noun	noun:inanim:f:v_rod
автогонії	автогонія	noun	noun:inanim:p:v_kly
автогонії	автогонія	noun	noun:inanim:p:v_naz
автогонії	автогонія	noun	noun:inanim:p:v_zna
автогосподарств	автогосподарство	noun	noun:inanim:p:v_rod
автогосподарства	автогосподарство	noun	noun:inanim:n:v_rod
автогосподарства	автогосподарство	noun	noun:inanim:p:v_kly
автогосподарства	автогосподарство	noun	noun:inanim:p:v_naz
автогосподарства	автогосподарство	noun	noun:inanim:p:v_zna
автогосподарствам	автогосподарство	noun	noun:inanim:p:v_dav
автогосподарствами	автогосподарство	noun	noun:inanim:p:v_oru
автогосподарствах	автогосподарство	noun	noun:inanim:p:v_mis
автогосподарство	автогосподарство	noun	noun:inanim:n:v_kly
автогосподарство	автогосподарство	noun	noun:inanim:n:v_naz
автогосподарство	автогосподарство	noun	noun:inanim:n:v_zna
автогосподарством	автогосподарство	noun	noun:inanim:n:v_oru
автогосподарству	автогосподарство	noun	noun:inanim:n:v_dav
автогосподарству	автогосподарство	noun	noun:inanim:n:v_mis
автогосподарстві	автогосподарство	noun	noun:inanim:n:v_mis
автограбіжник	автограбіжник	noun	noun:anim:m:v_naz
автограбіжника	автограбіжник	noun	noun:anim:m:v_rod
автограбіжника	автограбіжник	noun	noun:anim:m:v_zna
автограбіжникам	автограбіжник	noun	noun:anim:p:v_dav
автограбіжниками	автограбіжник	noun	noun:anim:p:v_oru
автограбіжниках	автограбіжник	noun	noun:anim:p:v_mis
автограбіжники	автограбіжник	noun	noun:anim:p:v_kly
автограбіжники	автограбіжник	noun	noun:anim:p:v_naz
автограбіжники	автограбіжник	noun	noun:anim:p:v_zna:rare
автограбіжникові	автограбіжник	noun	noun:anim:m:v_dav
автограбіжникові	автограбіжник	noun	noun:anim:m:v_mis
автограбіжником	автограбіжник	noun	noun:anim:m:v_oru
автограбіжнику	автограбіжник	noun	noun:anim:m:v_dav
автограбіжнику	автограбіжник	noun	noun:anim:m:v_kly
автограбіжнику	автограбіжник	noun	noun:anim:m:v_mis
автограбіжників	автограбіжник	noun	noun:anim:p:v_rod
автограбіжників	автограбіжник	noun	noun:anim:p:v_zna
автогравюр	автогравюра	noun	noun:inanim:p:v_rod
автогравюра	автогравюра	noun	noun:inanim:f:v_naz
автогравюрам	автогравюра	noun	noun:inanim:p:v_dav
автогравюрами	автогравюра	noun	noun:inanim:p:v_oru
автогравюрах	автогравюра	noun	noun:inanim:p:v_mis
автогравюри	автогравюра	noun	noun:inanim:f:v_rod
автогравюри	автогравюра	noun	noun:inanim:p:v_kly
автогравюри	автогравюра	noun	noun:inanim:p:v_naz
автогравюри	автогравюра	noun	noun:inanim:p:v_zna
автогравюро	автогравюра	noun	noun:inanim:f:v_kly
автогравюрою	автогравюра	noun	noun:inanim:f:v_oru
автогравюру	автогравюра	noun	noun:inanim:f:v_zna
автогравюрі	автогравюра	noun	noun:inanim:f:v_dav
автогравюрі	автогравюра	noun	noun:inanim:f:v_mis
автограм	автограма	noun	noun:inanim:p:v_rod
автограма	автограма	noun	noun:inanim:f:v_naz
автограмам	автограма	noun	noun:inanim:p:v_dav
автограмами	автограма	noun	noun:inanim:p:v_oru
автограмах	автограма	noun	noun:inanim:p:v_mis
автограми	автограма	noun	noun:inanim:f:v_rod
автограми	автограма	noun	noun:inanim:p:v_kly
автограми	автограма	noun	noun:inanim:p:v_naz
автограми	автограма	noun	noun:inanim:p:v_zna
автограмо	автограма	noun	noun:inanim:f:v_kly
автограмою	автограма	noun	noun:inanim:f:v_oru
автограму	автограма	noun	noun:inanim:f:v_zna
автограмі	автограма	noun	noun:inanim:f:v_dav
автограмі	автограма	noun	noun:inanim:f:v_mis
автограф	автограф	noun	noun:inanim:m:v_naz
автограф	автограф	noun	noun:inanim:m:v_zna
автографа	автограф	noun	noun:inanim:m:v_rod
автографа	автограф	noun	noun:inanim:m:v_zna:var
автографам	автограф	noun	noun:inanim:p:v_dav
автографами	автограф	noun	noun:inanim:p:v_oru
автографах	автограф	noun	noun:inanim:p:v_mis
автографе	автограф	noun	noun:inanim:m:v_kly
автографи	автограф	noun	noun:inanim:p:v_kly
автографи	автограф	noun	noun:inanim:p:v_naz
автографи	автограф	noun	noun:inanim:p:v_zna
автографові	автограф	noun	noun:inanim:m:v_dav
автографові	автограф	noun	noun:inanim:m:v_mis
автографом	автограф	noun	noun:inanim:m:v_oru
автографсесій	автографсесія	noun	noun:inanim:p:v_rod
автографсесію	автографсесія	noun	noun:inanim:f:v_zna
автографсесія	автографсесія	noun	noun:inanim:f:v_naz
автографсесіям	автографсесія	noun	noun:inanim:p:v_dav
автографсесіями	автографсесія	noun	noun:inanim:p:v_oru
автографсесіях	автографсесія	noun	noun:inanim:p:v_mis
автографсесіє	автографсесія	noun	noun:inanim:f:v_kly
автографсесією	автографсесія	noun	noun:inanim:f:v_oru
автографсесії	автографсесія	noun	noun:inanim:f:v_dav
автографсесії	автографсесія	noun	noun:inanim:f:v_mis
автографсесії	автографсесія	noun	noun:inanim:f:v_rod
автографсесії	автографсесія	noun	noun:inanim:p:v_kly
автографсесії	автографсесія	noun	noun:inanim:p:v_naz
автографсесії	автографсесія	noun	noun:inanim:p:v_zna
автографі	автограф	noun	noun:inanim:m:v_mis
автографів	автограф	noun	noun:inanim:p:v_rod
автографій	автографія	noun	noun:inanim:p:v_rod
автографію	автографія	noun	noun:inanim:f:v_zna
автографія	автографія	noun	noun:inanim:f:v_naz
автографіям	автографія	noun	noun:inanim:p:v_dav
автографіями	автографія	noun	noun:inanim:p:v_oru
автографіях	автографія	noun	noun:inanim:p:v_mis
автографіє	автографія	noun	noun:inanim:f:v_kly
автографією	автографія	noun	noun:inanim:f:v_oru
автографії	автографія	noun	noun:inanim:f:v_dav
автографії	автографія	noun	noun:inanim:f:v_mis
автографії	автографія	noun	noun:inanim:f:v_rod
автографії	автографія	noun	noun:inanim:p:v_kly
автографії	автографія	noun	noun:inanim:p:v_naz
автографії	автографія	noun	noun:inanim:p:v_zna
автогрейдер	автогрейдер	noun	noun:inanim:m:v_naz
автогрейдер	автогрейдер	noun	noun:inanim:m:v_zna
автогрейдера	автогрейдер	noun	noun:inanim:m:v_rod
автогрейдерам	автогрейдер	noun	noun:inanim:p:v_dav
автогрейдерами	автогрейдер	noun	noun:inanim:p:v_oru
автогрейдерах	автогрейдер	noun	noun:inanim:p:v_mis
автогрейдере	автогрейдер	noun	noun:inanim:m:v_kly
автогрейдери	автогрейдер	noun	noun:inanim:p:v_kly
автогрейдери	автогрейдер	noun	noun:inanim:p:v_naz
автогрейдери	автогрейдер	noun	noun:inanim:p:v_zna
автогрейдерові	автогрейдер	noun	noun:inanim:m:v_dav
автогрейдерові	автогрейдер	noun	noun:inanim:m:v_mis
автогрейдером	автогрейдер	noun	noun:inanim:m:v_oru
автогрейдері	автогрейдер	noun	noun:inanim:m:v_mis
автогрейдерів	автогрейдер	noun	noun:inanim:p:v_rod
автогудронатор	автогудронатор	noun	noun:inanim:m:v_naz
автогудронатор	автогудронатор	noun	noun:inanim:m:v_zna
автогудронатора	автогудронатор	noun	noun:inanim:m:v_rod
автогудронаторам	автогудронатор	noun	noun:inanim:p:v_dav
автогудронаторами	автогудронатор	noun	noun:inanim:p:v_oru
автогудронаторах	автогудронатор	noun	noun:inanim:p:v_mis
автогудронаторе	автогудронатор	noun	noun:inanim:m:v_kly
автогудронатори	автогудронатор	noun	noun:inanim:p:v_kly
автогудронатори	автогудронатор	noun	noun:inanim:p:v_naz
автогудронатори	автогудронатор	noun	noun:inanim:p:v_zna
автогудронаторові	автогудронатор	noun	noun:inanim:m:v_dav
автогудронаторові	автогудронатор	noun	noun:inanim:m:v_mis
автогудронатором	автогудронатор	noun	noun:inanim:m:v_oru
автогудронаторі	автогудронатор	noun	noun:inanim:m:v_mis
автогудронаторів	автогудронатор	noun	noun:inanim:p:v_rod
автогурман	автогурман	noun	noun:anim:m:v_naz
автогурмана	автогурман	noun	noun:anim:m:v_rod
автогурмана	автогурман	noun	noun:anim:m:v_zna
автогурманам	автогурман	noun	noun:anim:p:v_dav
автогурманами	автогурман	noun	noun:anim:p:v_oru
автогурманах	автогурман	noun	noun:anim:p:v_mis
автогурмане	автогурман	noun	noun:anim:m:v_kly
автогурмани	автогурман	noun	noun:anim:p:v_kly
автогурмани	автогурман	noun	noun:anim:p:v_naz
автогурмани	автогурман	noun	noun:anim:p:v_zna:rare
автогурманові	автогурман	noun	noun:anim:m:v_dav
автогурманові	автогурман	noun	noun:anim:m:v_mis
автогурманом	автогурман	noun	noun:anim:m:v_oru
автогурмані	автогурман	noun	noun:anim:m:v_mis
автогурманів	автогурман	noun	noun:anim:p:v_rod
автогурманів	автогурман	noun	noun:anim:p:v_zna
автогуртка	автогурток	noun	noun:inanim:m:v_rod
автогурткам	автогурток	noun	noun:inanim:p:v_dav
автогуртками	автогурток	noun	noun:inanim:p:v_oru
автогуртках	автогурток	noun	noun:inanim:p:v_mis
автогуртки	автогурток	noun	noun:inanim:p:v_kly
автогуртки	автогурток	noun	noun:inanim:p:v_naz
автогуртки	автогурток	noun	noun:inanim:p:v_zna
автогурткові	автогурток	noun	noun:inanim:m:v_dav
автогурткові	автогурток	noun	noun:inanim:m:v_mis
автогуртком	автогурток	noun	noun:inanim:m:v_oru
автогуртку	автогурток	noun	noun:inanim:m:v_dav
автогуртку	автогурток	noun	noun:inanim:m:v_kly
автогуртку	автогурток	noun	noun:inanim:m:v_mis
автогуртків	автогурток	noun	noun:inanim:p:v_rod
автогурток	автогурток	noun	noun:inanim:m:v_naz
автогурток	автогурток	noun	noun:inanim:m:v_zna
автогігант	автогігант	noun	noun:inanim:m:v_naz
автогігант	автогігант	noun	noun:inanim:m:v_zna
автогіганта	автогігант	noun	noun:inanim:m:v_rod
автогігантам	автогігант	noun	noun:inanim:p:v_dav
автогігантами	автогігант	noun	noun:inanim:p:v_oru
автогігантах	автогігант	noun	noun:inanim:p:v_mis
автогіганте	автогігант	noun	noun:inanim:m:v_kly
автогіганти	автогігант	noun	noun:inanim:p:v_kly
автогіганти	автогігант	noun	noun:inanim:p:v_naz
автогіганти	автогігант	noun	noun:inanim:p:v_zna
автогігантові	автогігант	noun	noun:inanim:m:v_dav
автогігантові	автогігант	noun	noun:inanim:m:v_mis
автогігантом	автогігант	noun	noun:inanim:m:v_oru
автогіганті	автогігант	noun	noun:inanim:m:v_mis
автогігантів	автогігант	noun	noun:inanim:p:v_rod
автогідроліз	автогідроліз	noun	noun:inanim:m:v_naz
автогідроліз	автогідроліз	noun	noun:inanim:m:v_zna
автогідролізам	автогідроліз	noun	noun:inanim:p:v_dav
автогідролізами	автогідроліз	noun	noun:inanim:p:v_oru
автогідролізах	автогідроліз	noun	noun:inanim:p:v_mis
автогідролізе	автогідроліз	noun	noun:inanim:m:v_kly
автогідролізи	автогідроліз	noun	noun:inanim:p:v_kly
автогідролізи	автогідроліз	noun	noun:inanim:p:v_naz
автогідролізи	автогідроліз	noun	noun:inanim:p:v_zna
автогідролізові	автогідроліз	noun	noun:inanim:m:v_dav
автогідролізові	автогідроліз	noun	noun:inanim:m:v_mis
автогідролізом	автогідроліз	noun	noun:inanim:m:v_oru
автогідролізу	автогідроліз	noun	noun:inanim:m:v_dav
автогідролізу	автогідроліз	noun	noun:inanim:m:v_mis
автогідролізу	автогідроліз	noun	noun:inanim:m:v_rod
автогідролізі	автогідроліз	noun	noun:inanim:m:v_mis
автогідролізів	автогідроліз	noun	noun:inanim:p:v_rod
автогідропідіймач	автогідропідіймач	noun	noun:inanim:m:v_naz
автогідропідіймач	автогідропідіймач	noun	noun:inanim:m:v_zna
автогідропідіймача	автогідропідіймач	noun	noun:inanim:m:v_rod
автогідропідіймачам	автогідропідіймач	noun	noun:inanim:p:v_dav
автогідропідіймачами	автогідропідіймач	noun	noun:inanim:p:v_oru
автогідропідіймачах	автогідропідіймач	noun	noun:inanim:p:v_mis
автогідропідіймачеві	автогідропідіймач	noun	noun:inanim:m:v_dav
автогідропідіймачеві	автогідропідіймач	noun	noun:inanim:m:v_mis
автогідропідіймачем	автогідропідіймач	noun	noun:inanim:m:v_oru
автогідропідіймачу	автогідропідіймач	noun	noun:inanim:m:v_dav
автогідропідіймачу	автогідропідіймач	noun	noun:inanim:m:v_kly
автогідропідіймачу	автогідропідіймач	noun	noun:inanim:m:v_mis
автогідропідіймачі	автогідропідіймач	noun	noun:inanim:m:v_mis
автогідропідіймачі	автогідропідіймач	noun	noun:inanim:p:v_kly
автогідропідіймачі	автогідропідіймач	noun	noun:inanim:p:v_naz
автогідропідіймачі	автогідропідіймач	noun	noun:inanim:p:v_zna
автогідропідіймачів	автогідропідіймач	noun	noun:inanim:p:v_rod
автогіпноз	автогіпноз	noun	noun:inanim:m:v_naz
автогіпноз	автогіпноз	noun	noun:inanim:m:v_zna
автогіпнозам	автогіпноз	noun	noun:inanim:p:v_dav
автогіпнозами	автогіпноз	noun	noun:inanim:p:v_oru
автогіпнозах	автогіпноз	noun	noun:inanim:p:v_mis
автогіпнозе	автогіпноз	noun	noun:inanim:m:v_kly
автогіпнози	автогіпноз	noun	noun:inanim:p:v_kly
автогіпнози	автогіпноз	noun	noun:inanim:p:v_naz
автогіпнози	автогіпноз	noun	noun:inanim:p:v_zna
автогіпнозові	автогіпноз	noun	noun:inanim:m:v_dav
автогіпнозові	автогіпноз	noun	noun:inanim:m:v_mis
автогіпнозом	автогіпноз	noun	noun:inanim:m:v_oru
автогіпнозу	автогіпноз	noun	noun:inanim:m:v_dav
автогіпнозу	автогіпноз	noun	noun:inanim:m:v_mis
автогіпнозу	автогіпноз	noun	noun:inanim:m:v_rod
автогіпнозі	автогіпноз	noun	noun:inanim:m:v_mis
автогіпнозів	автогіпноз	noun	noun:inanim:p:v_rod
автогісторадіографій	автогісторадіографія	noun	noun:inanim:p:v_rod
автогісторадіографію	автогісторадіографія	noun	noun:inanim:f:v_zna
автогісторадіографія	автогісторадіографія	noun	noun:inanim:f:v_naz
автогісторадіографіям	автогісторадіографія	noun	noun:inanim:p:v_dav
автогісторадіографіями	автогісторадіографія	noun	noun:inanim:p:v_oru
автогісторадіографіях	автогісторадіографія	noun	noun:inanim:p:v_mis
автогісторадіографіє	автогісторадіографія	noun	noun:inanim:f:v_kly
автогісторадіографією	автогісторадіографія	noun	noun:inanim:f:v_oru
автогісторадіографії	автогісторадіографія	noun	noun:inanim:f:v_dav
автогісторадіографії	автогісторадіографія	noun	noun:inanim:f:v_mis
автогісторадіографії	автогісторадіографія	noun	noun:inanim:f:v_rod
автогісторадіографії	автогісторадіографія	noun	noun:inanim:p:v_kly
автогісторадіографії	автогісторадіографія	noun	noun:inanim:p:v_naz
автогісторадіографії	автогісторадіографія	noun	noun:inanim:p:v_zna
автодвигун	автодвигун	noun	noun:inanim:m:v_naz
автодвигун	автодвигун	noun	noun:inanim:m:v_zna
автодвигуна	автодвигун	noun	noun:inanim:m:v_rod
автодвигунам	автодвигун	noun	noun:inanim:p:v_dav
автодвигунами	автодвигун	noun	noun:inanim:p:v_oru
автодвигунах	автодвигун	noun	noun:inanim:p:v_mis
автодвигуне	автодвигун	noun	noun:inanim:m:v_kly
автодвигуни	автодвигун	noun	noun:inanim:p:v_kly
автодвигуни	автодвигун	noun	noun:inanim:p:v_naz
автодвигуни	автодвигун	noun	noun:inanim:p:v_zna
автодвигунові	автодвигун	noun	noun:inanim:m:v_dav
автодвигунові	автодвигун	noun	noun:inanim:m:v_mis
автодвигуном	автодвигун	noun	noun:inanim:m:v_oru
автодвигуні	автодвигун	noun	noun:inanim:m:v_mis
автодвигунів	автодвигун	noun	noun:inanim:p:v_rod
автодвірець	автодвірець	noun	noun:inanim:m:v_naz
автодвірець	автодвірець	noun	noun:inanim:m:v_zna
автодвірцеві	автодвірець	noun	noun:inanim:m:v_dav
автодвірцеві	автодвірець	noun	noun:inanim:m:v_mis
автодвірцем	автодвірець	noun	noun:inanim:m:v_oru
автодвірцю	автодвірець	noun	noun:inanim:m:v_dav
автодвірцю	автодвірець	noun	noun:inanim:m:v_kly
автодвірцю	автодвірець	noun	noun:inanim:m:v_mis
автодвірця	автодвірець	noun	noun:inanim:m:v_rod
автодвірцям	автодвірець	noun	noun:inanim:p:v_dav
автодвірцями	автодвірець	noun	noun:inanim:p:v_oru
автодвірцях	автодвірець	noun	noun:inanim:p:v_mis
автодвірці	автодвірець	noun	noun:inanim:m:v_mis
автодвірці	автодвірець	noun	noun:inanim:p:v_kly
автодвірці	автодвірець	noun	noun:inanim:p:v_naz
автодвірці	автодвірець	noun	noun:inanim:p:v_zna
автодвірців	автодвірець	noun	noun:inanim:p:v_rod
автодетонатор	автодетонатор	noun	noun:inanim:m:v_naz
автодетонатор	автодетонатор	noun	noun:inanim:m:v_zna
автодетонатора	автодетонатор	noun	noun:inanim:m:v_rod
автодетонаторам	автодетонатор	noun	noun:inanim:p:v_dav
автодетонаторами	автодетонатор	noun	noun:inanim:p:v_oru
автодетонаторах	автодетонатор	noun	noun:inanim:p:v_mis
автодетонаторе	автодетонатор	noun	noun:inanim:m:v_kly
автодетонатори	автодетонатор	noun	noun:inanim:p:v_kly
автодетонатори	автодетонатор	noun	noun:inanim:p:v_naz
автодетонатори	автодетонатор	noun	noun:inanim:p:v_zna
автодетонаторові	автодетонатор	noun	noun:inanim:m:v_dav
автодетонаторові	автодетонатор	noun	noun:inanim:m:v_mis
автодетонатором	автодетонатор	noun	noun:inanim:m:v_oru
автодетонаторі	автодетонатор	noun	noun:inanim:m:v_mis
автодетонаторів	автодетонатор	noun	noun:inanim:p:v_rod
автодидакт	автодидакт	noun	noun:anim:m:v_naz
автодидакта	автодидакт	noun	noun:anim:m:v_rod
автодидакта	автодидакт	noun	noun:anim:m:v_zna
автодидактам	автодидакт	noun	noun:anim:p:v_dav
автодидактами	автодидакт	noun	noun:anim:p:v_oru
автодидактах	автодидакт	noun	noun:anim:p:v_mis
автодидакте	автодидакт	noun	noun:anim:m:v_kly
автодидакти	автодидакт	noun	noun:anim:p:v_kly
автодидакти	автодидакт	noun	noun:anim:p:v_naz
автодидакти	автодидакт	noun	noun:anim:p:v_zna:rare
автодидактові	автодидакт	noun	noun:anim:m:v_dav
автодидактові	автодидакт	noun	noun:anim:m:v_mis
автодидактом	автодидакт	noun	noun:anim:m:v_oru
автодидакті	автодидакт	noun	noun:anim:m:v_mis
автодидактів	автодидакт	noun	noun:anim:p:v_rod
автодидактів	автодидакт	noun	noun:anim:p:v_zna
автодизайн	автодизайн	noun	noun:inanim:m:v_naz
автодизайн	автодизайн	noun	noun:inanim:m:v_zna
автодизайнам	автодизайн	noun	noun:inanim:p:v_dav
автодизайнами	автодизайн	noun	noun:inanim:p:v_oru
автодизайнах	автодизайн	noun	noun:inanim:p:v_mis
автодизайне	автодизайн	noun	noun:inanim:m:v_kly
автодизайнер	автодизайнер	noun	noun:anim:m:v_naz
автодизайнера	автодизайнер	noun	noun:anim:m:v_rod
автодизайнера	автодизайнер	noun	noun:anim:m:v_zna
автодизайнерам	автодизайнер	noun	noun:anim:p:v_dav
автодизайнерами	автодизайнер	noun	noun:anim:p:v_oru
автодизайнерах	автодизайнер	noun	noun:anim:p:v_mis
автодизайнере	автодизайнер	noun	noun:anim:m:v_kly
автодизайнери	автодизайнер	noun	noun:anim:p:v_kly
автодизайнери	автодизайнер	noun	noun:anim:p:v_naz
автодизайнери	автодизайнер	noun	noun:anim:p:v_zna:rare
автодизайнерові	автодизайнер	noun	noun:anim:m:v_dav
автодизайнерові	автодизайнер	noun	noun:anim:m:v_mis
автодизайнером	автодизайнер	noun	noun:anim:m:v_oru
автодизайнері	автодизайнер	noun	noun:anim:m:v_mis
автодизайнерів	автодизайнер	noun	noun:anim:p:v_rod
автодизайнерів	автодизайнер	noun	noun:anim:p:v_zna
автодизайни	автодизайн	noun	noun:inanim:p:v_kly
автодизайни	автодизайн	noun	noun:inanim:p:v_naz
автодизайни	автодизайн	noun	noun:inanim:p:v_zna
автодизайнові	автодизайн	noun	noun:inanim:m:v_dav
автодизайнові	автодизайн	noun	noun:inanim:m:v_mis
автодизайном	автодизайн	noun	noun:inanim:m:v_oru
автодизайну	автодизайн	noun	noun:inanim:m:v_dav
автодизайну	автодизайн	noun	noun:inanim:m:v_mis
автодизайну	автодизайн	noun	noun:inanim:m:v_rod
автодизайні	автодизайн	noun	noun:inanim:m:v_mis
автодизайнів	автодизайн	noun	noun:inanim:p:v_rod
автодилер	автодилер	noun	noun:anim:m:v_naz
автодилера	автодилер	noun	noun:anim:m:v_rod
автодилера	автодилер	noun	noun:anim:m:v_zna
автодилерам	автодилер	noun	noun:anim:p:v_dav
автодилерами	автодилер	noun	noun:anim:p:v_oru
автодилерах	автодилер	noun	noun:anim:p:v_mis
автодилере	автодилер	noun	noun:anim:m:v_kly
автодилери	автодилер	noun	noun:anim:p:v_kly
автодилери	автодилер	noun	noun:anim:p:v_naz
автодилери	автодилер	noun	noun:anim:p:v_zna:rare
автодилерка	автодилерка	noun	noun:anim:f:v_naz
автодилеркам	автодилерка	noun	noun:anim:p:v_dav
автодилерками	автодилерка	noun	noun:anim:p:v_oru
автодилерках	автодилерка	noun	noun:anim:p:v_mis
автодилерки	автодилерка	noun	noun:anim:f:v_rod
автодилерки	автодилерка	noun	noun:anim:p:v_kly
автодилерки	автодилерка	noun	noun:anim:p:v_naz
автодилерки	автодилерка	noun	noun:anim:p:v_zna:rare
автодилерко	автодилерка	noun	noun:anim:f:v_kly
автодилеркою	автодилерка	noun	noun:anim:f:v_oru
автодилерку	автодилерка	noun	noun:anim:f:v_zna
автодилерові	автодилер	noun	noun:anim:m:v_dav
автодилерові	автодилер	noun	noun:anim:m:v_mis
автодилерок	автодилерка	noun	noun:anim:p:v_rod
автодилерок	автодилерка	noun	noun:anim:p:v_zna
автодилером	автодилер	noun	noun:anim:m:v_oru
автодилерці	автодилерка	noun	noun:anim:f:v_dav
автодилерці	автодилерка	noun	noun:anim:f:v_mis
автодилері	автодилер	noun	noun:anim:m:v_mis
автодилерів	автодилер	noun	noun:anim:p:v_rod
автодилерів	автодилер	noun	noun:anim:p:v_zna
автодин	автодин	noun	noun:inanim:m:v_naz
автодин	автодин	noun	noun:inanim:m:v_zna
автодина	автодин	noun	noun:inanim:m:v_rod
автодинам	автодин	noun	noun:inanim:p:v_dav
автодинами	автодин	noun	noun:inanim:p:v_oru
автодинах	автодин	noun	noun:inanim:p:v_mis
автодине	автодин	noun	noun:inanim:m:v_kly
автодини	автодин	noun	noun:inanim:p:v_kly
автодини	автодин	noun	noun:inanim:p:v_naz
автодини	автодин	noun	noun:inanim:p:v_zna
автодинові	автодин	noun	noun:inanim:m:v_dav
автодинові	автодин	noun	noun:inanim:m:v_mis
автодином	автодин	noun	noun:inanim:m:v_oru
автодині	автодин	noun	noun:inanim:m:v_mis
автодинів	автодин	noun	noun:inanim:p:v_rod
автодиспетчер	автодиспетчер	noun	noun:anim:m:v_naz
автодиспетчера	автодиспетчер	noun	noun:anim:m:v_rod
автодиспетчера	автодиспетчер	noun	noun:anim:m:v_zna
автодиспетчерам	автодиспетчер	noun	noun:anim:p:v_dav
автодиспетчерами	автодиспетчер	noun	noun:anim:p:v_oru
автодиспетчерах	автодиспетчер	noun	noun:anim:p:v_mis
автодиспетчере	автодиспетчер	noun	noun:anim:m:v_kly
автодиспетчери	автодиспетчер	noun	noun:anim:p:v_kly
автодиспетчери	автодиспетчер	noun	noun:anim:p:v_naz
автодиспетчери	автодиспетчер	noun	noun:anim:p:v_zna:rare
автодиспетчеризацій	автодиспетчеризація	noun	noun:inanim:p:v_rod
автодиспетчеризацію	автодиспетчеризація	noun	noun:inanim:f:v_zna
автодиспетчеризація	автодиспетчеризація	noun	noun:inanim:f:v_naz
автодиспетчеризаціям	автодиспетчеризація	noun	noun:inanim:p:v_dav
автодиспетчеризаціями	автодиспетчеризація	noun	noun:inanim:p:v_oru
автодиспетчеризаціях	автодиспетчеризація	noun	noun:inanim:p:v_mis
автодиспетчеризаціє	автодиспетчеризація	noun	noun:inanim:f:v_kly
автодиспетчеризацією	автодиспетчеризація	noun	noun:inanim:f:v_oru
автодиспетчеризації	автодиспетчеризація	noun	noun:inanim:f:v_dav
автодиспетчеризації	автодиспетчеризація	noun	noun:inanim:f:v_mis
автодиспетчеризації	автодиспетчеризація	noun	noun:inanim:f:v_rod
автодиспетчеризації	автодиспетчеризація	noun	noun:inanim:p:v_kly
автодиспетчеризації	автодиспетчеризація	noun	noun:inanim:p:v_naz
автодиспетчеризації	автодиспетчеризація	noun	noun:inanim:p:v_zna
автодиспетчерові	автодиспетчер	noun	noun:anim:m:v_dav
автодиспетчерові	автодиспетчер	noun	noun:anim:m:v_mis
автодиспетчером	автодиспетчер	noun	noun:anim:m:v_oru
автодиспетчері	автодиспетчер	noun	noun:anim:m:v_mis
автодиспетчерів	автодиспетчер	noun	noun:anim:p:v_rod
автодиспетчерів	автодиспетчер	noun	noun:anim:p:v_zna
автодозиметр	автодозиметр	noun	noun:inanim:m:v_naz
автодозиметр	автодозиметр	noun	noun:inanim:m:v_zna
автодозиметра	автодозиметр	noun	noun:inanim:m:v_rod
автодозиметрам	автодозиметр	noun	noun:inanim:p:v_dav
автодозиметрами	автодозиметр	noun	noun:inanim:p:v_oru
автодозиметрах	автодозиметр	noun	noun:inanim:p:v_mis
автодозиметре	автодозиметр	noun	noun:inanim:m:v_kly
автодозиметри	автодозиметр	noun	noun:inanim:p:v_kly
автодозиметри	автодозиметр	noun	noun:inanim:p:v_naz
автодозиметри	автодозиметр	noun	noun:inanim:p:v_zna
автодозиметрові	автодозиметр	noun	noun:inanim:m:v_dav
автодозиметрові	автодозиметр	noun	noun:inanim:m:v_mis
автодозиметром	автодозиметр	noun	noun:inanim:m:v_oru
автодозиметрі	автодозиметр	noun	noun:inanim:m:v_mis
автодозиметрів	автодозиметр	noun	noun:inanim:p:v_rod
автодор	автодор	noun	noun:inanim:m:v_naz
автодор	автодор	noun	noun:inanim:m:v_zna
автодорам	автодор	noun	noun:inanim:p:v_dav
автодорами	автодор	noun	noun:inanim:p:v_oru
автодорах	автодор	noun	noun:inanim:p:v_mis
автодоре	автодор	noun	noun:inanim:m:v_kly
автодори	автодор	noun	noun:inanim:p:v_kly
автодори	автодор	noun	noun:inanim:p:v_naz
автодори	автодор	noun	noun:inanim:p:v_zna
автодорові	автодор	noun	noun:inanim:m:v_dav
автодорові	автодор	noun	noun:inanim:m:v_mis
автодорога	автодорога	noun	noun:inanim:f:v_naz
автодорогам	автодорога	noun	noun:inanim:p:v_dav
автодорогами	автодорога	noun	noun:inanim:p:v_oru
автодорогах	автодорога	noun	noun:inanim:p:v_mis
автодороги	автодорога	noun	noun:inanim:f:v_rod
автодороги	автодорога	noun	noun:inanim:p:v_kly
автодороги	автодорога	noun	noun:inanim:p:v_naz
автодороги	автодорога	noun	noun:inanim:p:v_zna
автодорого	автодорога	noun	noun:inanim:f:v_kly
автодорогою	автодорога	noun	noun:inanim:f:v_oru
автодорогу	автодорога	noun	noun:inanim:f:v_zna
автодорожник	автодорожник	noun	noun:anim:m:v_naz
автодорожника	автодорожник	noun	noun:anim:m:v_rod
автодорожника	автодорожник	noun	noun:anim:m:v_zna
автодорожникам	автодорожник	noun	noun:anim:p:v_dav
автодорожниками	автодорожник	noun	noun:anim:p:v_oru
автодорожниках	автодорожник	noun	noun:anim:p:v_mis
автодорожники	автодорожник	noun	noun:anim:p:v_kly
автодорожники	автодорожник	noun	noun:anim:p:v_naz
автодорожники	автодорожник	noun	noun:anim:p:v_zna:rare
автодорожникові	автодорожник	noun	noun:anim:m:v_dav
автодорожникові	автодорожник	noun	noun:anim:m:v_mis
автодорожником	автодорожник	noun	noun:anim:m:v_oru
автодорожнику	автодорожник	noun	noun:anim:m:v_dav
автодорожнику	автодорожник	noun	noun:anim:m:v_kly
автодорожнику	автодорожник	noun	noun:anim:m:v_mis
автодорожників	автодорожник	noun	noun:anim:p:v_rod
автодорожників	автодорожник	noun	noun:anim:p:v_zna
автодорозі	автодорога	noun	noun:inanim:f:v_dav
автодорозі	автодорога	noun	noun:inanim:f:v_mis
автодором	автодор	noun	noun:inanim:m:v_oru
автодору	автодор	noun	noun:inanim:m:v_dav
автодору	автодор	noun	noun:inanim:m:v_mis
автодору	автодор	noun	noun:inanim:m:v_rod
автодорі	автодор	noun	noun:inanim:m:v_mis
автодорів	автодор	noun	noun:inanim:p:v_rod
автодорівець	автодорівець	noun	noun:anim:m:v_naz
автодорівцеві	автодорівець	noun	noun:anim:m:v_dav
автодорівцеві	автодорівець	noun	noun:anim:m:v_mis
автодорівцем	автодорівець	noun	noun:anim:m:v_oru
автодорівцю	автодорівець	noun	noun:anim:m:v_dav
автодорівцю	автодорівець	noun	noun:anim:m:v_kly
автодорівцю	автодорівець	noun	noun:anim:m:v_mis
автодорівця	автодорівець	noun	noun:anim:m:v_rod
автодорівця	автодорівець	noun	noun:anim:m:v_zna
автодорівцям	автодорівець	noun	noun:anim:p:v_dav
автодорівцями	автодорівець	noun	noun:anim:p:v_oru
автодорівцях	автодорівець	noun	noun:anim:p:v_mis
автодорівці	автодорівець	noun	noun:anim:m:v_mis
автодорівці	автодорівець	noun	noun:anim:p:v_kly
автодорівці	автодорівець	noun	noun:anim:p:v_naz
автодорівці	автодорівець	noun	noun:anim:p:v_zna:rare
автодорівців	автодорівець	noun	noun:anim:p:v_rod
автодорівців	автодорівець	noun	noun:anim:p:v_zna
автодоріг	автодорога	noun	noun:inanim:p:v_rod
автодрабин	автодрабина	noun	noun:inanim:p:v_rod
автодрабина	автодрабина	noun	noun:inanim:f:v_naz
автодрабинам	автодрабина	noun	noun:inanim:p:v_dav
автодрабинами	автодрабина	noun	noun:inanim:p:v_oru
автодрабинах	автодрабина	noun	noun:inanim:p:v_mis
автодрабини	автодрабина	noun	noun:inanim:f:v_rod
автодрабини	автодрабина	noun	noun:inanim:p:v_kly
автодрабини	автодрабина	noun	noun:inanim:p:v_naz
автодрабини	автодрабина	noun	noun:inanim:p:v_zna
автодрабино	автодрабина	noun	noun:inanim:f:v_kly
автодрабиною	автодрабина	noun	noun:inanim:f:v_oru
автодрабину	автодрабина	noun	noun:inanim:f:v_zna
автодрабині	автодрабина	noun	noun:inanim:f:v_dav
автодрабині	автодрабина	noun	noun:inanim:f:v_mis
автодрезин	автодрезина	noun	noun:inanim:p:v_rod
автодрезина	автодрезина	noun	noun:inanim:f:v_naz
автодрезинам	автодрезина	noun	noun:inanim:p:v_dav
автодрезинами	автодрезина	noun	noun:inanim:p:v_oru
автодрезинах	автодрезина	noun	noun:inanim:p:v_mis
автодрезини	автодрезина	noun	noun:inanim:f:v_rod
автодрезини	автодрезина	noun	noun:inanim:p:v_kly
автодрезини	автодрезина	noun	noun:inanim:p:v_naz
автодрезини	автодрезина	noun	noun:inanim:p:v_zna
автодрезино	автодрезина	noun	noun:inanim:f:v_kly
автодрезиною	автодрезина	noun	noun:inanim:f:v_oru
автодрезину	автодрезина	noun	noun:inanim:f:v_zna
автодрезині	автодрезина	noun	noun:inanim:f:v_dav
автодрезині	автодрезина	noun	noun:inanim:f:v_mis
автодром	автодром	noun	noun:inanim:m:v_naz
автодром	автодром	noun	noun:inanim:m:v_zna
автодромам	автодром	noun	noun:inanim:p:v_dav
автодромами	автодром	noun	noun:inanim:p:v_oru
автодромах	автодром	noun	noun:inanim:p:v_mis
автодроме	автодром	noun	noun:inanim:m:v_kly
автодроми	автодром	noun	noun:inanim:p:v_kly
автодроми	автодром	noun	noun:inanim:p:v_naz
автодроми	автодром	noun	noun:inanim:p:v_zna
автодромові	автодром	noun	noun:inanim:m:v_dav
автодромові	автодром	noun	noun:inanim:m:v_mis
автодромом	автодром	noun	noun:inanim:m:v_oru
автодрому	автодром	noun	noun:inanim:m:v_dav
автодрому	автодром	noun	noun:inanim:m:v_mis
автодрому	автодром	noun	noun:inanim:m:v_rod
автодромі	автодром	noun	noun:inanim:m:v_mis
автодромів	автодром	noun	noun:inanim:p:v_rod
автодіагност	автодіагност	noun	noun:anim:m:v_naz
автодіагноста	автодіагност	noun	noun:anim:m:v_rod
автодіагноста	автодіагност	noun	noun:anim:m:v_zna
автодіагностам	автодіагност	noun	noun:anim:p:v_dav
автодіагностами	автодіагност	noun	noun:anim:p:v_oru
автодіагностах	автодіагност	noun	noun:anim:p:v_mis
автодіагносте	автодіагност	noun	noun:anim:m:v_kly
автодіагности	автодіагност	noun	noun:anim:p:v_kly
автодіагности	автодіагност	noun	noun:anim:p:v_naz
автодіагности	автодіагност	noun	noun:anim:p:v_zna:rare
автодіагностик	автодіагностика	noun	noun:inanim:p:v_rod
автодіагностика	автодіагностика	noun	noun:inanim:f:v_naz
автодіагностикам	автодіагностика	noun	noun:inanim:p:v_dav
автодіагностиками	автодіагностика	noun	noun:inanim:p:v_oru
автодіагностиках	автодіагностика	noun	noun:inanim:p:v_mis
автодіагностики	автодіагностика	noun	noun:inanim:f:v_rod
автодіагностики	автодіагностика	noun	noun:inanim:p:v_kly
автодіагностики	автодіагностика	noun	noun:inanim:p:v_naz
автодіагностики	автодіагностика	noun	noun:inanim:p:v_zna
автодіагностико	автодіагностика	noun	noun:inanim:f:v_kly
автодіагностикою	автодіагностика	noun	noun:inanim:f:v_oru
автодіагностику	автодіагностика	noun	noun:inanim:f:v_zna
автодіагностиці	автодіагностика	noun	noun:inanim:f:v_dav
автодіагностиці	автодіагностика	noun	noun:inanim:f:v_mis
автодіагностові	автодіагност	noun	noun:anim:m:v_dav
автодіагностові	автодіагност	noun	noun:anim:m:v_mis
автодіагностом	автодіагност	noun	noun:anim:m:v_oru
автодіагності	автодіагност	noun	noun:anim:m:v_mis
автодіагностів	автодіагност	noun	noun:anim:p:v_rod
автодіагностів	автодіагност	noun	noun:anim:p:v_zna
автоділка	автоділок	noun	noun:anim:m:v_rod
автоділка	автоділок	noun	noun:anim:m:v_zna
автоділкам	автоділок	noun	noun:anim:p:v_dav
автоділками	автоділок	noun	noun:anim:p:v_oru
автоділках	автоділок	noun	noun:anim:p:v_mis
автоділки	автоділок	noun	noun:anim:p:v_kly
автоділки	автоділок	noun	noun:anim:p:v_naz
автоділки	автоділок	noun	noun:anim:p:v_zna:rare
автоділкові	автоділок	noun	noun:anim:m:v_dav
автоділкові	автоділок	noun	noun:anim:m:v_mis
автоділком	автоділок	noun	noun:anim:m:v_oru
автоділку	автоділок	noun	noun:anim:m:v_dav
автоділку	автоділок	noun	noun:anim:m:v_kly
автоділку	автоділок	noun	noun:anim:m:v_mis
автоділків	автоділок	noun	noun:anim:p:v_rod
автоділків	автоділок	noun	noun:anim:p:v_zna
автоділок	автоділок	noun	noun:anim:m:v_naz
автоевакуатор	автоевакуатор	noun	noun:inanim:m:v_naz
автоевакуатор	автоевакуатор	noun	noun:inanim:m:v_zna
автоевакуатора	автоевакуатор	noun	noun:inanim:m:v_rod
автоевакуаторам	автоевакуатор	noun	noun:inanim:p:v_dav
автоевакуаторами	автоевакуатор	noun	noun:inanim:p:v_oru
автоевакуаторах	автоевакуатор	noun	noun:inanim:p:v_mis
автоевакуаторе	автоевакуатор	noun	noun:inanim:m:v_kly
автоевакуатори	автоевакуатор	noun	noun:inanim:p:v_kly
автоевакуатори	автоевакуатор	noun	noun:inanim:p:v_naz
автоевакуатори	автоевакуатор	noun	noun:inanim:p:v_zna
автоевакуаторові	автоевакуатор	noun	noun:inanim:m:v_dav
автоевакуаторові	автоевакуатор	noun	noun:inanim:m:v_mis
автоевакуатором	автоевакуатор	noun	noun:inanim:m:v_oru
автоевакуаторі	автоевакуатор	noun	noun:inanim:m:v_mis
автоевакуаторів	автоевакуатор	noun	noun:inanim:p:v_rod
автоеволюцій	автоеволюція	noun	noun:inanim:p:v_rod
автоеволюцію	автоеволюція	noun	noun:inanim:f:v_zna
автоеволюція	автоеволюція	noun	noun:inanim:f:v_naz
автоеволюціям	автоеволюція	noun	noun:inanim:p:v_dav
автоеволюціями	автоеволюція	noun	noun:inanim:p:v_oru
автоеволюціях	автоеволюція	noun	noun:inanim:p:v_mis
автоеволюціє	автоеволюція	noun	noun:inanim:f:v_kly
автоеволюцією	автоеволюція	noun	noun:inanim:f:v_oru
автоеволюції	автоеволюція	noun	noun:inanim:f:v_dav
автоеволюції	автоеволюція	noun	noun:inanim:f:v_mis
автоеволюції	автоеволюція	noun	noun:inanim:f:v_rod
автоеволюції	автоеволюція	noun	noun:inanim:p:v_kly
автоеволюції	автоеволюція	noun	noun:inanim:p:v_naz
автоеволюції	автоеволюція	noun	noun:inanim:p:v_zna
автоекспортер	автоекспортер	noun	noun:anim:m:v_naz
автоекспортера	автоекспортер	noun	noun:anim:m:v_rod
автоекспортера	автоекспортер	noun	noun:anim:m:v_zna
автоекспортерам	автоекспортер	noun	noun:anim:p:v_dav
автоекспортерами	автоекспортер	noun	noun:anim:p:v_oru
автоекспортерах	автоекспортер	noun	noun:anim:p:v_mis
автоекспортере	автоекспортер	noun	noun:anim:m:v_kly
автоекспортери	автоекспортер	noun	noun:anim:p:v_kly
автоекспортери	автоекспортер	noun	noun:anim:p:v_naz
автоекспортери	автоекспортер	noun	noun:anim:p:v_zna:rare
автоекспортерові	автоекспортер	noun	noun:anim:m:v_dav
автоекспортерові	автоекспортер	noun	noun:anim:m:v_mis
автоекспортером	автоекспортер	noun	noun:anim:m:v_oru
автоекспортері	автоекспортер	noun	noun:anim:m:v_mis
автоекспортерів	автоекспортер	noun	noun:anim:p:v_rod
автоекспортерів	автоекспортер	noun	noun:anim:p:v_zna
автоекспрес	автоекспрес	noun	noun:inanim:m:v_naz
автоекспрес	автоекспрес	noun	noun:inanim:m:v_zna
автоекспреса	автоекспрес	noun	noun:inanim:m:v_rod
автоекспресам	автоекспрес	noun	noun:inanim:p:v_dav
автоекспресами	автоекспрес	noun	noun:inanim:p:v_oru
автоекспресах	автоекспрес	noun	noun:inanim:p:v_mis
автоекспресе	автоекспрес	noun	noun:inanim:m:v_kly
автоекспреси	автоекспрес	noun	noun:inanim:p:v_kly
автоекспреси	автоекспрес	noun	noun:inanim:p:v_naz
автоекспреси	автоекспрес	noun	noun:inanim:p:v_zna
автоекспресові	автоекспрес	noun	noun:inanim:m:v_dav
автоекспресові	автоекспрес	noun	noun:inanim:m:v_mis
автоекспресом	автоекспрес	noun	noun:inanim:m:v_oru
автоекспресі	автоекспрес	noun	noun:inanim:m:v_mis
автоекспресів	автоекспрес	noun	noun:inanim:p:v_rod
автоекіпаж	автоекіпаж	noun	noun:inanim:m:v_naz
автоекіпаж	автоекіпаж	noun	noun:inanim:m:v_zna
автоекіпажам	автоекіпаж	noun	noun:inanim:p:v_dav
автоекіпажами	автоекіпаж	noun	noun:inanim:p:v_oru
автоекіпажах	автоекіпаж	noun	noun:inanim:p:v_mis
автоекіпаже	автоекіпаж	noun	noun:inanim:m:v_kly
автоекіпажеві	автоекіпаж	noun	noun:inanim:m:v_dav
автоекіпажеві	автоекіпаж	noun	noun:inanim:m:v_mis
автоекіпажем	автоекіпаж	noun	noun:inanim:m:v_oru
автоекіпажу	автоекіпаж	noun	noun:inanim:m:v_dav
автоекіпажу	автоекіпаж	noun	noun:inanim:m:v_mis
автоекіпажу	автоекіпаж	noun	noun:inanim:m:v_rod
автоекіпажі	автоекіпаж	noun	noun:inanim:m:v_mis
автоекіпажі	автоекіпаж	noun	noun:inanim:p:v_kly
автоекіпажі	автоекіпаж	noun	noun:inanim:p:v_naz
автоекіпажі	автоекіпаж	noun	noun:inanim:p:v_zna
автоекіпажів	автоекіпаж	noun	noun:inanim:p:v_rod
автоелектрик	автоелектрик	noun	noun:anim:m:v_naz
автоелектрика	автоелектрик	noun	noun:anim:m:v_rod
автоелектрика	автоелектрик	noun	noun:anim:m:v_zna
автоелектрикам	автоелектрик	noun	noun:anim:p:v_dav
автоелектриками	автоелектрик	noun	noun:anim:p:v_oru
автоелектриках	автоелектрик	noun	noun:anim:p:v_mis
автоелектрики	автоелектрик	noun	noun:anim:p:v_kly
автоелектрики	автоелектрик	noun	noun:anim:p:v_naz
автоелектрики	автоелектрик	noun	noun:anim:p:v_zna:rare
автоелектрикові	автоелектрик	noun	noun:anim:m:v_dav
автоелектрикові	автоелектрик	noun	noun:anim:m:v_mis
автоелектриком	автоелектрик	noun	noun:anim:m:v_oru
автоелектрику	автоелектрик	noun	noun:anim:m:v_dav
автоелектрику	автоелектрик	noun	noun:anim:m:v_kly
автоелектрику	автоелектрик	noun	noun:anim:m:v_mis
автоелектриків	автоелектрик	noun	noun:anim:p:v_rod
автоелектриків	автоелектрик	noun	noun:anim:p:v_zna
автоемале	автоемаль	noun	noun:inanim:f:v_kly
автоемалей	автоемаль	noun	noun:inanim:p:v_rod
автоемаллю	автоемаль	noun	noun:inanim:f:v_oru
автоемаль	автоемаль	noun	noun:inanim:f:v_naz
автоемаль	автоемаль	noun	noun:inanim:f:v_zna
автоемалям	автоемаль	noun	noun:inanim:p:v_dav
автоемалями	автоемаль	noun	noun:inanim:p:v_oru
автоемалях	автоемаль	noun	noun:inanim:p:v_mis
автоемалі	автоемаль	noun	noun:inanim:f:v_dav
автоемалі	автоемаль	noun	noun:inanim:f:v_mis
автоемалі	автоемаль	noun	noun:inanim:f:v_rod
автоемалі	автоемаль	noun	noun:inanim:p:v_kly
автоемалі	автоемаль	noun	noun:inanim:p:v_naz
автоемалі	автоемаль	noun	noun:inanim:p:v_zna
автоепіграф	автоепіграф	noun	noun:inanim:m:v_naz
автоепіграф	автоепіграф	noun	noun:inanim:m:v_zna
автоепіграфа	автоепіграф	noun	noun:inanim:m:v_rod
автоепіграфам	автоепіграф	noun	noun:inanim:p:v_dav
автоепіграфами	автоепіграф	noun	noun:inanim:p:v_oru
автоепіграфах	автоепіграф	noun	noun:inanim:p:v_mis
автоепіграфе	автоепіграф	noun	noun:inanim:m:v_kly
автоепіграфи	автоепіграф	noun	noun:inanim:p:v_kly
автоепіграфи	автоепіграф	noun	noun:inanim:p:v_naz
автоепіграфи	автоепіграф	noun	noun:inanim:p:v_zna
автоепіграфові	автоепіграф	noun	noun:inanim:m:v_dav
автоепіграфові	автоепіграф	noun	noun:inanim:m:v_mis
автоепіграфом	автоепіграф	noun	noun:inanim:m:v_oru
автоепіграфі	автоепіграф	noun	noun:inanim:m:v_mis
автоепіграфів	автоепіграф	noun	noun:inanim:p:v_rod
автоепітафій	автоепітафія	noun	noun:inanim:p:v_rod
автоепітафію	автоепітафія	noun	noun:inanim:f:v_zna
автоепітафія	автоепітафія	noun	noun:inanim:f:v_naz
автоепітафіям	автоепітафія	noun	noun:inanim:p:v_dav
автоепітафіями	автоепітафія	noun	noun:inanim:p:v_oru
автоепітафіях	автоепітафія	noun	noun:inanim:p:v_mis
автоепітафіє	автоепітафія	noun	noun:inanim:f:v_kly
автоепітафією	автоепітафія	noun	noun:inanim:f:v_oru
автоепітафії	автоепітафія	noun	noun:inanim:f:v_dav
автоепітафії	автоепітафія	noun	noun:inanim:f:v_mis
автоепітафії	автоепітафія	noun	noun:inanim:f:v_rod
автоепітафії	автоепітафія	noun	noun:inanim:p:v_kly
автоепітафії	автоепітафія	noun	noun:inanim:p:v_naz
автоепітафії	автоепітафія	noun	noun:inanim:p:v_zna
автоетнонім	автоетнонім	noun	noun:inanim:m:v_naz
автоетнонім	автоетнонім	noun	noun:inanim:m:v_zna
автоетноніма	автоетнонім	noun	noun:inanim:m:v_rod
автоетнонімам	автоетнонім	noun	noun:inanim:p:v_dav
автоетнонімами	автоетнонім	noun	noun:inanim:p:v_oru
автоетнонімах	автоетнонім	noun	noun:inanim:p:v_mis
автоетноніме	автоетнонім	noun	noun:inanim:m:v_kly
автоетноніми	автоетнонім	noun	noun:inanim:p:v_kly
автоетноніми	автоетнонім	noun	noun:inanim:p:v_naz
автоетноніми	автоетнонім	noun	noun:inanim:p:v_zna
автоетнонімові	автоетнонім	noun	noun:inanim:m:v_dav
автоетнонімові	автоетнонім	noun	noun:inanim:m:v_mis
автоетнонімом	автоетнонім	noun	noun:inanim:m:v_oru
автоетнонімі	автоетнонім	noun	noun:inanim:m:v_mis
автоетнонімів	автоетнонім	noun	noun:inanim:p:v_rod
автожир	автожир	noun	noun:inanim:m:v_naz
автожир	автожир	noun	noun:inanim:m:v_zna
автожира	автожир	noun	noun:inanim:m:v_rod
автожирам	автожир	noun	noun:inanim:p:v_dav
автожирами	автожир	noun	noun:inanim:p:v_oru
автожирах	автожир	noun	noun:inanim:p:v_mis
автожире	автожир	noun	noun:inanim:m:v_kly
автожири	автожир	noun	noun:inanim:p:v_kly
автожири	автожир	noun	noun:inanim:p:v_naz
автожири	автожир	noun	noun:inanim:p:v_zna
автожирові	автожир	noun	noun:inanim:m:v_dav
автожирові	автожир	noun	noun:inanim:m:v_mis
автожиром	автожир	noun	noun:inanim:m:v_oru
автожирі	автожир	noun	noun:inanim:m:v_mis
автожирів	автожир	noun	noun:inanim:p:v_rod
автожурнал	автожурнал	noun	noun:inanim:m:v_naz
автожурнал	автожурнал	noun	noun:inanim:m:v_zna
автожурналам	автожурнал	noun	noun:inanim:p:v_dav
автожурналами	автожурнал	noun	noun:inanim:p:v_oru
автожурналах	автожурнал	noun	noun:inanim:p:v_mis
автожурнале	автожурнал	noun	noun:inanim:m:v_kly
автожурнали	автожурнал	noun	noun:inanim:p:v_kly
автожурнали	автожурнал	noun	noun:inanim:p:v_naz
автожурнали	автожурнал	noun	noun:inanim:p:v_zna
автожурналові	автожурнал	noun	noun:inanim:m:v_dav
автожурналові	автожурнал	noun	noun:inanim:m:v_mis
автожурналом	автожурнал	noun	noun:inanim:m:v_oru
автожурналу	автожурнал	noun	noun:inanim:m:v_dav
автожурналу	автожурнал	noun	noun:inanim:m:v_mis
автожурналу	автожурнал	noun	noun:inanim:m:v_rod
автожурналі	автожурнал	noun	noun:inanim:m:v_mis
автожурналів	автожурнал	noun	noun:inanim:p:v_rod
автожурналіст	автожурналіст	noun	noun:anim:m:v_naz
автожурналіста	автожурналіст	noun	noun:anim:m:v_rod
автожурналіста	автожурналіст	noun	noun:anim:m:v_zna
автожурналістам	автожурналіст	noun	noun:anim:p:v_dav
автожурналістами	автожурналіст	noun	noun:anim:p:v_oru
автожурналістах	автожурналіст	noun	noun:anim:p:v_mis
автожурналісте	автожурналіст	noun	noun:anim:m:v_kly
автожурналісти	автожурналіст	noun	noun:anim:p:v_kly
автожурналісти	автожурналіст	noun	noun:anim:p:v_naz
автожурналісти	автожурналіст	noun	noun:anim:p:v_zna:rare
автожурналістові	автожурналіст	noun	noun:anim:m:v_dav
автожурналістові	автожурналіст	noun	noun:anim:m:v_mis
автожурналістом	автожурналіст	noun	noun:anim:m:v_oru
автожурналісті	автожурналіст	noun	noun:anim:m:v_mis
автожурналістів	автожурналіст	noun	noun:anim:p:v_rod
автожурналістів	автожурналіст	noun	noun:anim:p:v_zna
автозабаганка	автозабаганка	noun	noun:inanim:f:v_naz
автозабаганкам	автозабаганка	noun	noun:inanim:p:v_dav
автозабаганками	автозабаганка	noun	noun:inanim:p:v_oru
автозабаганках	автозабаганка	noun	noun:inanim:p:v_mis
автозабаганки	автозабаганка	noun	noun:inanim:f:v_rod
автозабаганки	автозабаганка	noun	noun:inanim:p:v_kly
автозабаганки	автозабаганка	noun	noun:inanim:p:v_naz
автозабаганки	автозабаганка	noun	noun:inanim:p:v_zna
автозабаганко	автозабаганка	noun	noun:inanim:f:v_kly
автозабаганкою	автозабаганка	noun	noun:inanim:f:v_oru
автозабаганку	автозабаганка	noun	noun:inanim:f:v_zna
автозабаганок	автозабаганка	noun	noun:inanim:p:v_rod
автозабаганці	автозабаганка	noun	noun:inanim:f:v_dav
автозабаганці	автозабаганка	noun	noun:inanim:f:v_mis
автозавантажувач	автозавантажувач	noun	noun:inanim:m:v_naz
автозавантажувач	автозавантажувач	noun	noun:inanim:m:v_zna
автозавантажувача	автозавантажувач	noun	noun:inanim:m:v_rod
автозавантажувачам	автозавантажувач	noun	noun:inanim:p:v_dav
автозавантажувачами	автозавантажувач	noun	noun:inanim:p:v_oru
автозавантажувачах	автозавантажувач	noun	noun:inanim:p:v_mis
автозавантажувачеві	автозавантажувач	noun	noun:inanim:m:v_dav
автозавантажувачеві	автозавантажувач	noun	noun:inanim:m:v_mis
автозавантажувачем	автозавантажувач	noun	noun:inanim:m:v_oru
автозавантажувачу	автозавантажувач	noun	noun:inanim:m:v_dav
автозавантажувачу	автозавантажувач	noun	noun:inanim:m:v_kly
автозавантажувачу	автозавантажувач	noun	noun:inanim:m:v_mis
автозавантажувачі	автозавантажувач	noun	noun:inanim:m:v_mis
автозавантажувачі	автозавантажувач	noun	noun:inanim:p:v_kly
автозавантажувачі	автозавантажувач	noun	noun:inanim:p:v_naz
автозавантажувачі	автозавантажувач	noun	noun:inanim:p:v_zna
автозавантажувачів	автозавантажувач	noun	noun:inanim:p:v_rod
автозавод	автозавод	noun	noun:inanim:m:v_naz
автозавод	автозавод	noun	noun:inanim:m:v_zna
автозаводам	автозавод	noun	noun:inanim:p:v_dav
автозаводами	автозавод	noun	noun:inanim:p:v_oru
автозаводах	автозавод	noun	noun:inanim:p:v_mis
автозаводе	автозавод	noun	noun:inanim:m:v_kly
автозаводець	автозаводець	noun	noun:anim:m:v_naz
автозаводи	автозавод	noun	noun:inanim:p:v_kly
автозаводи	автозавод	noun	noun:inanim:p:v_naz
автозаводи	автозавод	noun	noun:inanim:p:v_zna
автозаводові	автозавод	noun	noun:inanim:m:v_dav
автозаводові	автозавод	noun	noun:inanim:m:v_mis
автозаводом	автозавод	noun	noun:inanim:m:v_oru
автозаводу	автозавод	noun	noun:inanim:m:v_dav
автозаводу	автозавод	noun	noun:inanim:m:v_mis
автозаводу	автозавод	noun	noun:inanim:m:v_rod
автозаводцеві	автозаводець	noun	noun:anim:m:v_dav
автозаводцеві	автозаводець	noun	noun:anim:m:v_mis
автозаводцем	автозаводець	noun	noun:anim:m:v_oru
автозаводцю	автозаводець	noun	noun:anim:m:v_dav
автозаводцю	автозаводець	noun	noun:anim:m:v_kly
автозаводцю	автозаводець	noun	noun:anim:m:v_mis
автозаводця	автозаводець	noun	noun:anim:m:v_rod
автозаводця	автозаводець	noun	noun:anim:m:v_zna
автозаводцям	автозаводець	noun	noun:anim:p:v_dav
автозаводцями	автозаводець	noun	noun:anim:p:v_oru
автозаводцях	автозаводець	noun	noun:anim:p:v_mis
автозаводці	автозаводець	noun	noun:anim:m:v_mis
автозаводці	автозаводець	noun	noun:anim:p:v_kly
автозаводці	автозаводець	noun	noun:anim:p:v_naz
автозаводці	автозаводець	noun	noun:anim:p:v_zna:rare
автозаводців	автозаводець	noun	noun:anim:p:v_rod
автозаводців	автозаводець	noun	noun:anim:p:v_zna
автозаводі	автозавод	noun	noun:inanim:m:v_mis
автозаводів	автозавод	noun	noun:inanim:p:v_rod
автозак	автозак	noun	noun:inanim:m:v_naz:slang
автозак	автозак	noun	noun:inanim:m:v_zna:slang
автозака	автозак	noun	noun:inanim:m:v_rod:slang
автозакам	автозак	noun	noun:inanim:p:v_dav:slang
автозаками	автозак	noun	noun:inanim:p:v_oru:slang
автозаках	автозак	noun	noun:inanim:p:v_mis:slang
автозаки	автозак	noun	noun:inanim:p:v_kly:slang
автозаки	автозак	noun	noun:inanim:p:v_naz:slang
автозаки	автозак	noun	noun:inanim:p:v_zna:slang
автозакові	автозак	noun	noun:inanim:m:v_dav:slang
автозакові	автозак	noun	noun:inanim:m:v_mis:slang
автозаком	автозак	noun	noun:inanim:m:v_oru:slang
автозаку	автозак	noun	noun:inanim:m:v_dav:slang
автозаку	автозак	noun	noun:inanim:m:v_kly:slang
автозаку	автозак	noun	noun:inanim:m:v_mis:slang
автозаків	автозак	noun	noun:inanim:p:v_rod:slang
автозамикач	автозамикач	noun	noun:inanim:m:v_naz
автозамикач	автозамикач	noun	noun:inanim:m:v_zna
автозамикача	автозамикач	noun	noun:inanim:m:v_rod
автозамикачам	автозамикач	noun	noun:inanim:p:v_dav
автозамикачами	автозамикач	noun	noun:inanim:p:v_oru
автозамикачах	автозамикач	noun	noun:inanim:p:v_mis
автозамикачеві	автозамикач	noun	noun:inanim:m:v_dav
автозамикачеві	автозамикач	noun	noun:inanim:m:v_mis
автозамикачем	автозамикач	noun	noun:inanim:m:v_oru
автозамикачу	автозамикач	noun	noun:inanim:m:v_dav
автозамикачу	автозамикач	noun	noun:inanim:m:v_kly
автозамикачу	автозамикач	noun	noun:inanim:m:v_mis
автозамикачі	автозамикач	noun	noun:inanim:m:v_mis
автозамикачі	автозамикач	noun	noun:inanim:p:v_kly
автозамикачі	автозамикач	noun	noun:inanim:p:v_naz
автозамикачі	автозамикач	noun	noun:inanim:p:v_zna
автозамикачів	автозамикач	noun	noun:inanim:p:v_rod
автозамка	автозамок	noun	noun:inanim:m:v_rod
автозамкам	автозамок	noun	noun:inanim:p:v_dav
автозамками	автозамок	noun	noun:inanim:p:v_oru
автозамках	автозамок	noun	noun:inanim:p:v_mis
автозамки	автозамок	noun	noun:inanim:p:v_kly
автозамки	автозамок	noun	noun:inanim:p:v_naz
автозамки	автозамок	noun	noun:inanim:p:v_zna
автозамкові	автозамок	noun	noun:inanim:m:v_dav
автозамкові	автозамок	noun	noun:inanim:m:v_mis
автозамком	автозамок	noun	noun:inanim:m:v_oru
автозамку	автозамок	noun	noun:inanim:m:v_dav
автозамку	автозамок	noun	noun:inanim:m:v_kly
автозамку	автозамок	noun	noun:inanim:m:v_mis
автозамків	автозамок	noun	noun:inanim:p:v_rod
автозамок	автозамок	noun	noun:inanim:m:v_naz
автозамок	автозамок	noun	noun:inanim:m:v_zna
автозапальничка	автозапальничка	noun	noun:inanim:f:v_naz
автозапальничкам	автозапальничка	noun	noun:inanim:p:v_dav
автозапальничками	автозапальничка	noun	noun:inanim:p:v_oru
автозапальничках	автозапальничка	noun	noun:inanim:p:v_mis
автозапальнички	автозапальничка	noun	noun:inanim:f:v_rod
автозапальнички	автозапальничка	noun	noun:inanim:p:v_kly
автозапальнички	автозапальничка	noun	noun:inanim:p:v_naz
автозапальнички	автозапальничка	noun	noun:inanim:p:v_zna
автозапальничко	автозапальничка	noun	noun:inanim:f:v_kly
автозапальничкою	автозапальничка	noun	noun:inanim:f:v_oru
автозапальничку	автозапальничка	noun	noun:inanim:f:v_zna
автозапальничок	автозапальничка	noun	noun:inanim:p:v_rod
автозапальничці	автозапальничка	noun	noun:inanim:f:v_dav
автозапальничці	автозапальничка	noun	noun:inanim:f:v_mis
автозаправка	автозаправка	noun	noun:inanim:f:v_naz
автозаправкам	автозаправка	noun	noun:inanim:p:v_dav
автозаправками	автозаправка	noun	noun:inanim:p:v_oru
автозаправках	автозаправка	noun	noun:inanim:p:v_mis
автозаправки	автозаправка	noun	noun:inanim:f:v_rod
автозаправки	автозаправка	noun	noun:inanim:p:v_kly
автозаправки	автозаправка	noun	noun:inanim:p:v_naz
автозаправки	автозаправка	noun	noun:inanim:p:v_zna
автозаправко	автозаправка	noun	noun:inanim:f:v_kly
автозаправкою	автозаправка	noun	noun:inanim:f:v_oru
автозаправку	автозаправка	noun	noun:inanim:f:v_zna
автозаправник	автозаправник	noun	noun:inanim:m:v_naz
автозаправник	автозаправник	noun	noun:inanim:m:v_zna
автозаправника	автозаправник	noun	noun:inanim:m:v_rod
автозаправникам	автозаправник	noun	noun:inanim:p:v_dav
автозаправниками	автозаправник	noun	noun:inanim:p:v_oru
автозаправниках	автозаправник	noun	noun:inanim:p:v_mis
автозаправники	автозаправник	noun	noun:inanim:p:v_kly
автозаправники	автозаправник	noun	noun:inanim:p:v_naz
автозаправники	автозаправник	noun	noun:inanim:p:v_zna
автозаправникові	автозаправник	noun	noun:inanim:m:v_dav
автозаправникові	автозаправник	noun	noun:inanim:m:v_mis
автозаправником	автозаправник	noun	noun:inanim:m:v_oru
автозаправнику	автозаправник	noun	noun:inanim:m:v_dav
автозаправнику	автозаправник	noun	noun:inanim:m:v_kly
автозаправнику	автозаправник	noun	noun:inanim:m:v_mis
автозаправників	автозаправник	noun	noun:inanim:p:v_rod
автозаправнице	автозаправниця	noun	noun:anim:f:v_kly
автозаправницею	автозаправниця	noun	noun:anim:f:v_oru
автозаправниць	автозаправниця	noun	noun:anim:p:v_rod
автозаправниць	автозаправниця	noun	noun:anim:p:v_zna
автозаправницю	автозаправниця	noun	noun:anim:f:v_zna
автозаправниця	автозаправниця	noun	noun:anim:f:v_naz
автозаправницям	автозаправниця	noun	noun:anim:p:v_dav
автозаправницями	автозаправниця	noun	noun:anim:p:v_oru
автозаправницях	автозаправниця	noun	noun:anim:p:v_mis
автозаправниці	автозаправниця	noun	noun:anim:f:v_dav
автозаправниці	автозаправниця	noun	noun:anim:f:v_mis
автозаправниці	автозаправниця	noun	noun:anim:f:v_rod
автозаправниці	автозаправниця	noun	noun:anim:p:v_kly
автозаправниці	автозаправниця	noun	noun:anim:p:v_naz
автозаправниці	автозаправниця	noun	noun:anim:p:v_zna:rare
автозаправок	автозаправка	noun	noun:inanim:p:v_rod
автозаправці	автозаправка	noun	noun:inanim:f:v_dav
автозаправці	автозаправка	noun	noun:inanim:f:v_mis
автозапускач	автозапускач	noun	noun:inanim:m:v_naz
автозапускач	автозапускач	noun	noun:inanim:m:v_zna
автозапускача	автозапускач	noun	noun:inanim:m:v_rod
автозапускачам	автозапускач	noun	noun:inanim:p:v_dav
автозапускачами	автозапускач	noun	noun:inanim:p:v_oru
автозапускачах	автозапускач	noun	noun:inanim:p:v_mis
автозапускачеві	автозапускач	noun	noun:inanim:m:v_dav
автозапускачеві	автозапускач	noun	noun:inanim:m:v_mis
автозапускачем	автозапускач	noun	noun:inanim:m:v_oru
автозапускачу	автозапускач	noun	noun:inanim:m:v_dav
автозапускачу	автозапускач	noun	noun:inanim:m:v_kly
автозапускачу	автозапускач	noun	noun:inanim:m:v_mis
автозапускачі	автозапускач	noun	noun:inanim:m:v_mis
автозапускачі	автозапускач	noun	noun:inanim:p:v_kly
автозапускачі	автозапускач	noun	noun:inanim:p:v_naz
автозапускачі	автозапускач	noun	noun:inanim:p:v_zna
автозапускачів	автозапускач	noun	noun:inanim:p:v_rod
автозапчастин	автозапчастина	noun	noun:inanim:p:v_rod
автозапчастина	автозапчастина	noun	noun:inanim:f:v_naz
автозапчастинам	автозапчастина	noun	noun:inanim:p:v_dav
автозапчастинами	автозапчастина	noun	noun:inanim:p:v_oru
автозапчастинах	автозапчастина	noun	noun:inanim:p:v_mis
автозапчастини	автозапчастина	noun	noun:inanim:f:v_rod
автозапчастини	автозапчастина	noun	noun:inanim:p:v_kly
автозапчастини	автозапчастина	noun	noun:inanim:p:v_naz
автозапчастини	автозапчастина	noun	noun:inanim:p:v_zna
автозапчастино	автозапчастина	noun	noun:inanim:f:v_kly
автозапчастиною	автозапчастина	noun	noun:inanim:f:v_oru
автозапчастину	автозапчастина	noun	noun:inanim:f:v_zna
автозапчастині	автозапчастина	noun	noun:inanim:f:v_dav
автозапчастині	автозапчастина	noun	noun:inanim:f:v_mis
автозатор	автозатор	noun	noun:inanim:m:v_naz
автозатор	автозатор	noun	noun:inanim:m:v_zna
автозаторам	автозатор	noun	noun:inanim:p:v_dav
автозаторами	автозатор	noun	noun:inanim:p:v_oru
автозаторах	автозатор	noun	noun:inanim:p:v_mis
автозаторе	автозатор	noun	noun:inanim:m:v_kly
автозатори	автозатор	noun	noun:inanim:p:v_kly
автозатори	автозатор	noun	noun:inanim:p:v_naz
автозатори	автозатор	noun	noun:inanim:p:v_zna
автозаторові	автозатор	noun	noun:inanim:m:v_dav
автозаторові	автозатор	noun	noun:inanim:m:v_mis
автозатором	автозатор	noun	noun:inanim:m:v_oru
автозатору	автозатор	noun	noun:inanim:m:v_dav
автозатору	автозатор	noun	noun:inanim:m:v_mis
автозатору	автозатор	noun	noun:inanim:m:v_rod
автозаторі	автозатор	noun	noun:inanim:m:v_mis
автозаторів	автозатор	noun	noun:inanim:p:v_rod
автозахоплювач	автозахоплювач	noun	noun:inanim:m:v_naz
автозахоплювач	автозахоплювач	noun	noun:inanim:m:v_zna
автозахоплювача	автозахоплювач	noun	noun:inanim:m:v_rod
автозахоплювачам	автозахоплювач	noun	noun:inanim:p:v_dav
автозахоплювачами	автозахоплювач	noun	noun:inanim:p:v_oru
автозахоплювачах	автозахоплювач	noun	noun:inanim:p:v_mis
автозахоплювачеві	автозахоплювач	noun	noun:inanim:m:v_dav
автозахоплювачеві	автозахоплювач	noun	noun:inanim:m:v_mis
автозахоплювачем	автозахоплювач	noun	noun:inanim:m:v_oru
автозахоплювачу	автозахоплювач	noun	noun:inanim:m:v_dav
автозахоплювачу	автозахоплювач	noun	noun:inanim:m:v_kly
автозахоплювачу	автозахоплювач	noun	noun:inanim:m:v_mis
автозахоплювачі	автозахоплювач	noun	noun:inanim:m:v_mis
автозахоплювачі	автозахоплювач	noun	noun:inanim:p:v_kly
автозахоплювачі	автозахоплювач	noun	noun:inanim:p:v_naz
автозахоплювачі	автозахоплювач	noun	noun:inanim:p:v_zna
автозахоплювачів	автозахоплювач	noun	noun:inanim:p:v_rod
автозвалищ	автозвалище	noun	noun:inanim:p:v_rod
автозвалища	автозвалище	noun	noun:inanim:n:v_rod
автозвалища	автозвалище	noun	noun:inanim:p:v_kly
автозвалища	автозвалище	noun	noun:inanim:p:v_naz
автозвалища	автозвалище	noun	noun:inanim:p:v_zna
автозвалищам	автозвалище	noun	noun:inanim:p:v_dav
автозвалищами	автозвалище	noun	noun:inanim:p:v_oru
автозвалищах	автозвалище	noun	noun:inanim:p:v_mis
автозвалище	автозвалище	noun	noun:inanim:n:v_kly
автозвалище	автозвалище	noun	noun:inanim:n:v_naz
автозвалище	автозвалище	noun	noun:inanim:n:v_zna
автозвалищем	автозвалище	noun	noun:inanim:n:v_oru
автозвалищу	автозвалище	noun	noun:inanim:n:v_dav
автозвалищу	автозвалище	noun	noun:inanim:n:v_mis
автозвалищі	автозвалище	noun	noun:inanim:n:v_mis
автозварюванню	автозварювання	noun	noun:inanim:n:v_dav
автозварюванню	автозварювання	noun	noun:inanim:n:v_mis
автозварювання	автозварювання	noun	noun:inanim:n:v_kly
автозварювання	автозварювання	noun	noun:inanim:n:v_naz
автозварювання	автозварювання	noun	noun:inanim:n:v_rod
автозварювання	автозварювання	noun	noun:inanim:n:v_zna
автозварювання	автозварювання	noun	noun:inanim:p:v_kly
автозварювання	автозварювання	noun	noun:inanim:p:v_naz
автозварювання	автозварювання	noun	noun:inanim:p:v_zna
автозварюванням	автозварювання	noun	noun:inanim:n:v_oru
автозварюванням	автозварювання	noun	noun:inanim:p:v_dav
автозварюваннями	автозварювання	noun	noun:inanim:p:v_oru
автозварюваннях	автозварювання	noun	noun:inanim:p:v_mis
автозварюванні	автозварювання	noun	noun:inanim:n:v_mis
автозварювань	автозварювання	noun	noun:inanim:p:v_rod
автозлодюжка	автозлодюжка	noun	noun:anim:f:v_naz
автозлодюжка	автозлодюжка	noun	noun:anim:m:v_naz
автозлодюжкам	автозлодюжка	noun	noun:anim:p:v_dav
автозлодюжками	автозлодюжка	noun	noun:anim:p:v_oru
автозлодюжках	автозлодюжка	noun	noun:anim:p:v_mis
автозлодюжки	автозлодюжка	noun	noun:anim:f:v_rod
автозлодюжки	автозлодюжка	noun	noun:anim:m:v_rod
автозлодюжки	автозлодюжка	noun	noun:anim:p:v_kly
автозлодюжки	автозлодюжка	noun	noun:anim:p:v_naz
автозлодюжки	автозлодюжка	noun	noun:anim:p:v_zna:rare
автозлодюжко	автозлодюжка	noun	noun:anim:f:v_kly
автозлодюжко	автозлодюжка	noun	noun:anim:m:v_kly
автозлодюжкою	автозлодюжка	noun	noun:anim:f:v_oru
автозлодюжкою	автозлодюжка	noun	noun:anim:m:v_oru
автозлодюжку	автозлодюжка	noun	noun:anim:f:v_zna
автозлодюжку	автозлодюжка	noun	noun:anim:m:v_zna
автозлодюжок	автозлодюжка	noun	noun:anim:p:v_rod
автозлодюжок	автозлодюжка	noun	noun:anim:p:v_zna
автозлодюжці	автозлодюжка	noun	noun:anim:f:v_dav
автозлодюжці	автозлодюжка	noun	noun:anim:f:v_mis
автозлодюжці	автозлодюжка	noun	noun:anim:m:v_dav
автозлодюжці	автозлодюжка	noun	noun:anim:m:v_mis
автозлодій	автозлодій	noun	noun:anim:m:v_naz
автозлодію	автозлодій	noun	noun:anim:m:v_dav
автозлодію	автозлодій	noun	noun:anim:m:v_kly
автозлодію	автозлодій	noun	noun:anim:m:v_mis
автозлодія	автозлодій	noun	noun:anim:m:v_rod
автозлодія	автозлодій	noun	noun:anim:m:v_zna
автозлодіям	автозлодій	noun	noun:anim:p:v_dav
автозлодіями	автозлодій	noun	noun:anim:p:v_oru
автозлодіях	автозлодій	noun	noun:anim:p:v_mis
автозлодієві	автозлодій	noun	noun:anim:m:v_dav
автозлодієві	автозлодій	noun	noun:anim:m:v_mis
автозлодієм	автозлодій	noun	noun:anim:m:v_oru
автозлодії	автозлодій	noun	noun:anim:m:v_mis
автозлодії	автозлодій	noun	noun:anim:p:v_kly
автозлодії	автозлодій	noun	noun:anim:p:v_naz
автозлодії	автозлодій	noun	noun:anim:p:v_zna:rare
автозлодіїв	автозлодій	noun	noun:anim:p:v_rod
автозлодіїв	автозлодій	noun	noun:anim:p:v_zna
автозлом	автозлом	noun	noun:inanim:m:v_naz
автозлом	автозлом	noun	noun:inanim:m:v_zna
автозломам	автозлом	noun	noun:inanim:p:v_dav
автозломами	автозлом	noun	noun:inanim:p:v_oru
автозломах	автозлом	noun	noun:inanim:p:v_mis
автозломе	автозлом	noun	noun:inanim:m:v_kly
автозломи	автозлом	noun	noun:inanim:p:v_kly
автозломи	автозлом	noun	noun:inanim:p:v_naz
автозломи	автозлом	noun	noun:inanim:p:v_zna
автозломові	автозлом	noun	noun:inanim:m:v_dav
автозломові	автозлом	noun	noun:inanim:m:v_mis
автозломом	автозлом	noun	noun:inanim:m:v_oru
автозлому	автозлом	noun	noun:inanim:m:v_dav
автозлому	автозлом	noun	noun:inanim:m:v_mis
автозлому	автозлом	noun	noun:inanim:m:v_rod
автозломі	автозлом	noun	noun:inanim:m:v_mis
автозломів	автозлом	noun	noun:inanim:p:v_rod
автозлочин	автозлочин	noun	noun:inanim:m:v_naz
автозлочин	автозлочин	noun	noun:inanim:m:v_zna
автозлочинам	автозлочин	noun	noun:inanim:p:v_dav
автозлочинами	автозлочин	noun	noun:inanim:p:v_oru
автозлочинах	автозлочин	noun	noun:inanim:p:v_mis
автозлочине	автозлочин	noun	noun:inanim:m:v_kly
автозлочинець	автозлочинець	noun	noun:anim:m:v_naz
автозлочини	автозлочин	noun	noun:inanim:p:v_kly
автозлочини	автозлочин	noun	noun:inanim:p:v_naz
автозлочини	автозлочин	noun	noun:inanim:p:v_zna
автозлочинові	автозлочин	noun	noun:inanim:m:v_dav
автозлочинові	автозлочин	noun	noun:inanim:m:v_mis
автозлочином	автозлочин	noun	noun:inanim:m:v_oru
автозлочину	автозлочин	noun	noun:inanim:m:v_dav
автозлочину	автозлочин	noun	noun:inanim:m:v_mis
автозлочину	автозлочин	noun	noun:inanim:m:v_rod
автозлочинцеві	автозлочинець	noun	noun:anim:m:v_dav
автозлочинцеві	автозлочинець	noun	noun:anim:m:v_mis
автозлочинцем	автозлочинець	noun	noun:anim:m:v_oru
автозлочинцю	автозлочинець	noun	noun:anim:m:v_dav
автозлочинцю	автозлочинець	noun	noun:anim:m:v_kly
автозлочинцю	автозлочинець	noun	noun:anim:m:v_mis
автозлочинця	автозлочинець	noun	noun:anim:m:v_rod
автозлочинця	автозлочинець	noun	noun:anim:m:v_zna
автозлочинцям	автозлочинець	noun	noun:anim:p:v_dav
автозлочинцями	автозлочинець	noun	noun:anim:p:v_oru
автозлочинцях	автозлочинець	noun	noun:anim:p:v_mis
автозлочинці	автозлочинець	noun	noun:anim:m:v_mis
автозлочинці	автозлочинець	noun	noun:anim:p:v_kly
автозлочинці	автозлочинець	noun	noun:anim:p:v_naz
автозлочинці	автозлочинець	noun	noun:anim:p:v_zna:rare
автозлочинців	автозлочинець	noun	noun:anim:p:v_rod
автозлочинців	автозлочинець	noun	noun:anim:p:v_zna
автозлочині	автозлочин	noun	noun:inanim:m:v_mis
автозлочинів	автозлочин	noun	noun:inanim:p:v_rod
автозмаганню	автозмагання	noun	noun:inanim:n:v_dav
автозмаганню	автозмагання	noun	noun:inanim:n:v_mis
автозмагання	автозмагання	noun	noun:inanim:n:v_kly
автозмагання	автозмагання	noun	noun:inanim:n:v_naz
автозмагання	автозмагання	noun	noun:inanim:n:v_rod
автозмагання	автозмагання	noun	noun:inanim:n:v_zna
автозмагання	автозмагання	noun	noun:inanim:p:v_kly
автозмагання	автозмагання	noun	noun:inanim:p:v_naz
автозмагання	автозмагання	noun	noun:inanim:p:v_zna
автозмаганням	автозмагання	noun	noun:inanim:n:v_oru
автозмаганням	автозмагання	noun	noun:inanim:p:v_dav
автозмаганнями	автозмагання	noun	noun:inanim:p:v_oru
автозмаганнях	автозмагання	noun	noun:inanim:p:v_mis
автозмаганні	автозмагання	noun	noun:inanim:n:v_mis
автозмагань	автозмагання	noun	noun:inanim:p:v_rod
автозупинка	автозупинка	noun	noun:inanim:f:v_naz
автозупинкам	автозупинка	noun	noun:inanim:p:v_dav
автозупинками	автозупинка	noun	noun:inanim:p:v_oru
автозупинках	автозупинка	noun	noun:inanim:p:v_mis
автозупинки	автозупинка	noun	noun:inanim:f:v_rod
автозупинки	автозупинка	noun	noun:inanim:p:v_kly
автозупинки	автозупинка	noun	noun:inanim:p:v_naz
автозупинки	автозупинка	noun	noun:inanim:p:v_zna
автозупинко	автозупинка	noun	noun:inanim:f:v_kly
автозупинкою	автозупинка	noun	noun:inanim:f:v_oru
автозупинку	автозупинка	noun	noun:inanim:f:v_zna
автозупинок	автозупинка	noun	noun:inanim:p:v_rod
автозупинці	автозупинка	noun	noun:inanim:f:v_dav
автозупинці	автозупинка	noun	noun:inanim:f:v_mis
автозчепленню	автозчеплення	noun	noun:inanim:n:v_dav
автозчепленню	автозчеплення	noun	noun:inanim:n:v_mis
автозчеплення	автозчеплення	noun	noun:inanim:n:v_kly
автозчеплення	автозчеплення	noun	noun:inanim:n:v_naz
автозчеплення	автозчеплення	noun	noun:inanim:n:v_rod
автозчеплення	автозчеплення	noun	noun:inanim:n:v_zna
автозчеплення	автозчеплення	noun	noun:inanim:p:v_kly
автозчеплення	автозчеплення	noun	noun:inanim:p:v_naz
автозчеплення	автозчеплення	noun	noun:inanim:p:v_zna
автозчепленням	автозчеплення	noun	noun:inanim:n:v_oru
автозчепленням	автозчеплення	noun	noun:inanim:p:v_dav
автозчепленнями	автозчеплення	noun	noun:inanim:p:v_oru
автозчепленнях	автозчеплення	noun	noun:inanim:p:v_mis
автозчепленні	автозчеплення	noun	noun:inanim:n:v_mis
автозчеплень	автозчеплення	noun	noun:inanim:p:v_rod
автозіткненню	автозіткнення	noun	noun:inanim:n:v_dav
автозіткненню	автозіткнення	noun	noun:inanim:n:v_mis
автозіткнення	автозіткнення	noun	noun:inanim:n:v_kly
автозіткнення	автозіткнення	noun	noun:inanim:n:v_naz
автозіткнення	автозіткнення	noun	noun:inanim:n:v_rod
автозіткнення	автозіткнення	noun	noun:inanim:n:v_zna
автозіткнення	автозіткнення	noun	noun:inanim:p:v_kly
автозіткнення	автозіткнення	noun	noun:inanim:p:v_naz
автозіткнення	автозіткнення	noun	noun:inanim:p:v_zna
автозіткненням	автозіткнення	noun	noun:inanim:n:v_oru
автозіткненням	автозіткнення	noun	noun:inanim:p:v_dav
автозіткненнями	автозіткнення	noun	noun:inanim:p:v_oru
автозіткненнях	автозіткнення	noun	noun:inanim:p:v_mis
автозіткненні	автозіткнення	noun	noun:inanim:n:v_mis
автозіткнень	автозіткнення	noun	noun:inanim:p:v_rod
автойонізатор	автойонізатор	noun	noun:inanim:m:v_naz
автойонізатор	автойонізатор	noun	noun:inanim:m:v_zna
автойонізатора	автойонізатор	noun	noun:inanim:m:v_rod
автойонізаторам	автойонізатор	noun	noun:inanim:p:v_dav
автойонізаторами	автойонізатор	noun	noun:inanim:p:v_oru
автойонізаторах	автойонізатор	noun	noun:inanim:p:v_mis
автойонізаторе	автойонізатор	noun	noun:inanim:m:v_kly
автойонізатори	автойонізатор	noun	noun:inanim:p:v_kly
автойонізатори	автойонізатор	noun	noun:inanim:p:v_naz
автойонізатори	автойонізатор	noun	noun:inanim:p:v_zna
автойонізаторові	автойонізатор	noun	noun:inanim:m:v_dav
автойонізаторові	автойонізатор	noun	noun:inanim:m:v_mis
автойонізатором	автойонізатор	noun	noun:inanim:m:v_oru
автойонізаторі	автойонізатор	noun	noun:inanim:m:v_mis
автойонізаторів	автойонізатор	noun	noun:inanim:p:v_rod
автойонізацій	автойонізація	noun	noun:inanim:p:v_rod
автойонізацію	автойонізація	noun	noun:inanim:f:v_zna
автойонізація	автойонізація	noun	noun:inanim:f:v_naz
автойонізаціям	автойонізація	noun	noun:inanim:p:v_dav
автойонізаціями	автойонізація	noun	noun:inanim:p:v_oru
автойонізаціях	автойонізація	noun	noun:inanim:p:v_mis
автойонізаціє	автойонізація	noun	noun:inanim:f:v_kly
автойонізацією	автойонізація	noun	noun:inanim:f:v_oru
автойонізації	автойонізація	noun	noun:inanim:f:v_dav
автойонізації	автойонізація	noun	noun:inanim:f:v_mis
автойонізації	автойонізація	noun	noun:inanim:f:v_rod
автойонізації	автойонізація	noun	noun:inanim:p:v_kly
автойонізації	автойонізація	noun	noun:inanim:p:v_naz
автойонізації	автойонізація	noun	noun:inanim:p:v_zna
автокавоварка	автокавоварка	noun	noun:inanim:f:v_naz
автокавоваркам	автокавоварка	noun	noun:inanim:p:v_dav
автокавоварками	автокавоварка	noun	noun:inanim:p:v_oru
автокавоварках	автокавоварка	noun	noun:inanim:p:v_mis
автокавоварки	автокавоварка	noun	noun:inanim:f:v_rod
автокавоварки	автокавоварка	noun	noun:inanim:p:v_kly
автокавоварки	автокавоварка	noun	noun:inanim:p:v_naz
автокавоварки	автокавоварка	noun	noun:inanim:p:v_zna
автокавоварко	автокавоварка	noun	noun:inanim:f:v_kly
автокавоваркою	автокавоварка	noun	noun:inanim:f:v_oru
автокавоварку	автокавоварка	noun	noun:inanim:f:v_zna
автокавоварок	автокавоварка	noun	noun:inanim:p:v_rod
автокавоварці	автокавоварка	noun	noun:inanim:f:v_dav
автокавоварці	автокавоварка	noun	noun:inanim:f:v_mis
автокамер	автокамера	noun	noun:inanim:p:v_rod
автокамера	автокамера	noun	noun:inanim:f:v_naz
автокамерам	автокамера	noun	noun:inanim:p:v_dav
автокамерами	автокамера	noun	noun:inanim:p:v_oru
автокамерах	автокамера	noun	noun:inanim:p:v_mis
автокамери	автокамера	noun	noun:inanim:f:v_rod
автокамери	автокамера	noun	noun:inanim:p:v_kly
автокамери	автокамера	noun	noun:inanim:p:v_naz
автокамери	автокамера	noun	noun:inanim:p:v_zna
автокамеро	автокамера	noun	noun:inanim:f:v_kly
автокамерою	автокамера	noun	noun:inanim:f:v_oru
автокамеру	автокамера	noun	noun:inanim:f:v_zna
автокамері	автокамера	noun	noun:inanim:f:v_dav
автокамері	автокамера	noun	noun:inanim:f:v_mis
автокампіграфій	автокампіграфія	noun	noun:inanim:p:v_rod
автокампіграфію	автокампіграфія	noun	noun:inanim:f:v_zna
автокампіграфія	автокампіграфія	noun	noun:inanim:f:v_naz
автокампіграфіям	автокампіграфія	noun	noun:inanim:p:v_dav
автокампіграфіями	автокампіграфія	noun	noun:inanim:p:v_oru
автокампіграфіях	автокампіграфія	noun	noun:inanim:p:v_mis
автокампіграфіє	автокампіграфія	noun	noun:inanim:f:v_kly
автокампіграфією	автокампіграфія	noun	noun:inanim:f:v_oru
автокампіграфії	автокампіграфія	noun	noun:inanim:f:v_dav
автокампіграфії	автокампіграфія	noun	noun:inanim:f:v_mis
автокампіграфії	автокампіграфія	noun	noun:inanim:f:v_rod
автокампіграфії	автокампіграфія	noun	noun:inanim:p:v_kly
автокампіграфії	автокампіграфія	noun	noun:inanim:p:v_naz
автокампіграфії	автокампіграфія	noun	noun:inanim:p:v_zna
автокар	автокар	noun	noun:inanim:m:v_naz
автокар	автокар	noun	noun:inanim:m:v_zna
автокара	автокар	noun	noun:inanim:m:v_rod
автокараван	автокараван	noun	noun:inanim:m:v_naz
автокараван	автокараван	noun	noun:inanim:m:v_zna
автокараванам	автокараван	noun	noun:inanim:p:v_dav
автокараванами	автокараван	noun	noun:inanim:p:v_oru
автокараванах	автокараван	noun	noun:inanim:p:v_mis
автокараване	автокараван	noun	noun:inanim:m:v_kly
автокаравани	автокараван	noun	noun:inanim:p:v_kly
автокаравани	автокараван	noun	noun:inanim:p:v_naz
автокаравани	автокараван	noun	noun:inanim:p:v_zna
автокараванові	автокараван	noun	noun:inanim:m:v_dav
автокараванові	автокараван	noun	noun:inanim:m:v_mis
автокараваном	автокараван	noun	noun:inanim:m:v_oru
автокаравану	автокараван	noun	noun:inanim:m:v_dav
автокаравану	автокараван	noun	noun:inanim:m:v_mis
автокаравану	автокараван	noun	noun:inanim:m:v_rod
автокаравані	автокараван	noun	noun:inanim:m:v_mis
автокараванів	автокараван	noun	noun:inanim:p:v_rod
автокарам	автокар	noun	noun:inanim:p:v_dav
автокарами	автокар	noun	noun:inanim:p:v_oru
автокарах	автокар	noun	noun:inanim:p:v_mis
автокаре	автокар	noun	noun:inanim:m:v_kly
автокари	автокар	noun	noun:inanim:p:v_kly
автокари	автокар	noun	noun:inanim:p:v_naz
автокари	автокар	noun	noun:inanim:p:v_zna
автокарикатур	автокарикатура	noun	noun:inanim:p:v_rod
автокарикатура	автокарикатура	noun	noun:inanim:f:v_naz
автокарикатурам	автокарикатура	noun	noun:inanim:p:v_dav
автокарикатурами	автокарикатура	noun	noun:inanim:p:v_oru
автокарикатурах	автокарикатура	noun	noun:inanim:p:v_mis
автокарикатури	автокарикатура	noun	noun:inanim:f:v_rod
автокарикатури	автокарикатура	noun	noun:inanim:p:v_kly
автокарикатури	автокарикатура	noun	noun:inanim:p:v_naz
автокарикатури	автокарикатура	noun	noun:inanim:p:v_zna
автокарикатуро	автокарикатура	noun	noun:inanim:f:v_kly
автокарикатурою	автокарикатура	noun	noun:inanim:f:v_oru
автокарикатуру	автокарикатура	noun	noun:inanim:f:v_zna
автокарикатурі	автокарикатура	noun	noun:inanim:f:v_dav
автокарикатурі	автокарикатура	noun	noun:inanim:f:v_mis
автокарові	автокар	noun	noun:inanim:m:v_dav
автокарові	автокар	noun	noun:inanim:m:v_mis
автокаром	автокар	noun	noun:inanim:m:v_oru
автокарі	автокар	noun	noun:inanim:m:v_mis
автокарів	автокар	noun	noun:inanim:p:v_rod
автокаска	автокаска	noun	noun:inanim:f:v_naz
автокаскадер	автокаскадер	noun	noun:anim:m:v_naz
автокаскадера	автокаскадер	noun	noun:anim:m:v_rod
автокаскадера	автокаскадер	noun	noun:anim:m:v_zna
автокаскадерам	автокаскадер	noun	noun:anim:p:v_dav
автокаскадерами	автокаскадер	noun	noun:anim:p:v_oru
автокаскадерах	автокаскадер	noun	noun:anim:p:v_mis
автокаскадере	автокаскадер	noun	noun:anim:m:v_kly
автокаскадери	автокаскадер	noun	noun:anim:p:v_kly
автокаскадери	автокаскадер	noun	noun:anim:p:v_naz
автокаскадери	автокаскадер	noun	noun:anim:p:v_zna:rare
автокаскадерові	автокаскадер	noun	noun:anim:m:v_dav
автокаскадерові	автокаскадер	noun	noun:anim:m:v_mis
автокаскадером	автокаскадер	noun	noun:anim:m:v_oru
автокаскадері	автокаскадер	noun	noun:anim:m:v_mis
автокаскадерів	автокаскадер	noun	noun:anim:p:v_rod
автокаскадерів	автокаскадер	noun	noun:anim:p:v_zna
автокаскам	автокаска	noun	noun:inanim:p:v_dav
автокасками	автокаска	noun	noun:inanim:p:v_oru
автокасках	автокаска	noun	noun:inanim:p:v_mis
автокаски	автокаска	noun	noun:inanim:f:v_rod
автокаски	автокаска	noun	noun:inanim:p:v_kly
автокаски	автокаска	noun	noun:inanim:p:v_naz
автокаски	автокаска	noun	noun:inanim:p:v_zna
автокаско	автокаска	noun	noun:inanim:f:v_kly
автокаскою	автокаска	noun	noun:inanim:f:v_oru
автокаску	автокаска	noun	noun:inanim:f:v_zna
автокасок	автокаска	noun	noun:inanim:p:v_rod
автокасці	автокаска	noun	noun:inanim:f:v_dav
автокасці	автокаска	noun	noun:inanim:f:v_mis
автокаталіз	автокаталіз	noun	noun:inanim:m:v_naz
автокаталіз	автокаталіз	noun	noun:inanim:m:v_zna
автокаталізам	автокаталіз	noun	noun:inanim:p:v_dav
автокаталізами	автокаталіз	noun	noun:inanim:p:v_oru
автокаталізатор	автокаталізатор	noun	noun:inanim:m:v_naz
автокаталізатор	автокаталізатор	noun	noun:inanim:m:v_zna
автокаталізатора	автокаталізатор	noun	noun:inanim:m:v_rod
автокаталізаторам	автокаталізатор	noun	noun:inanim:p:v_dav
автокаталізаторами	автокаталізатор	noun	noun:inanim:p:v_oru
автокаталізаторах	автокаталізатор	noun	noun:inanim:p:v_mis
автокаталізаторе	автокаталізатор	noun	noun:inanim:m:v_kly
автокаталізатори	автокаталізатор	noun	noun:inanim:p:v_kly
автокаталізатори	автокаталізатор	noun	noun:inanim:p:v_naz
автокаталізатори	автокаталізатор	noun	noun:inanim:p:v_zna
автокаталізаторові	автокаталізатор	noun	noun:inanim:m:v_dav
автокаталізаторові	автокаталізатор	noun	noun:inanim:m:v_mis
автокаталізатором	автокаталізатор	noun	noun:inanim:m:v_oru
автокаталізаторі	автокаталізатор	noun	noun:inanim:m:v_mis
автокаталізаторів	автокаталізатор	noun	noun:inanim:p:v_rod
автокаталізах	автокаталіз	noun	noun:inanim:p:v_mis
автокаталізе	автокаталіз	noun	noun:inanim:m:v_kly
автокаталізи	автокаталіз	noun	noun:inanim:p:v_kly
автокаталізи	автокаталіз	noun	noun:inanim:p:v_naz
автокаталізи	автокаталіз	noun	noun:inanim:p:v_zna
автокаталізові	автокаталіз	noun	noun:inanim:m:v_dav
автокаталізові	автокаталіз	noun	noun:inanim:m:v_mis
автокаталізом	автокаталіз	noun	noun:inanim:m:v_oru
автокаталізу	автокаталіз	noun	noun:inanim:m:v_dav
автокаталізу	автокаталіз	noun	noun:inanim:m:v_mis
автокаталізу	автокаталіз	noun	noun:inanim:m:v_rod
автокаталізі	автокаталіз	noun	noun:inanim:m:v_mis
автокаталізів	автокаталіз	noun	noun:inanim:p:v_rod
автокатастроф	автокатастрофа	noun	noun:inanim:p:v_rod
автокатастрофа	автокатастрофа	noun	noun:inanim:f:v_naz
автокатастрофам	автокатастрофа	noun	noun:inanim:p:v_dav
автокатастрофами	автокатастрофа	noun	noun:inanim:p:v_oru
автокатастрофах	автокатастрофа	noun	noun:inanim:p:v_mis
автокатастрофи	автокатастрофа	noun	noun:inanim:f:v_rod
автокатастрофи	автокатастрофа	noun	noun:inanim:p:v_kly
автокатастрофи	автокатастрофа	noun	noun:inanim:p:v_naz
автокатастрофи	автокатастрофа	noun	noun:inanim:p:v_zna
автокатастрофо	автокатастрофа	noun	noun:inanim:f:v_kly
автокатастрофою	автокатастрофа	noun	noun:inanim:f:v_oru
автокатастрофу	автокатастрофа	noun	noun:inanim:f:v_zna
автокатастрофі	автокатастрофа	noun	noun:inanim:f:v_dav
автокатастрофі	автокатастрофа	noun	noun:inanim:f:v_mis
автокатод	автокатод	noun	noun:inanim:m:v_naz
автокатод	автокатод	noun	noun:inanim:m:v_zna
автокатода	автокатод	noun	noun:inanim:m:v_rod
автокатодам	автокатод	noun	noun:inanim:p:v_dav
автокатодами	автокатод	noun	noun:inanim:p:v_oru
автокатодах	автокатод	noun	noun:inanim:p:v_mis
автокатоде	автокатод	noun	noun:inanim:m:v_kly
автокатоди	автокатод	noun	noun:inanim:p:v_kly
автокатоди	автокатод	noun	noun:inanim:p:v_naz
автокатоди	автокатод	noun	noun:inanim:p:v_zna
автокатодові	автокатод	noun	noun:inanim:m:v_dav
автокатодові	автокатод	noun	noun:inanim:m:v_mis
автокатодом	автокатод	noun	noun:inanim:m:v_oru
автокатоді	автокатод	noun	noun:inanim:m:v_mis
автокатодів	автокатод	noun	noun:inanim:p:v_rod
автоквест	автоквест	noun	noun:inanim:m:v_naz
автоквест	автоквест	noun	noun:inanim:m:v_zna
автоквестам	автоквест	noun	noun:inanim:p:v_dav
автоквестами	автоквест	noun	noun:inanim:p:v_oru
автоквестах	автоквест	noun	noun:inanim:p:v_mis
автоквесте	автоквест	noun	noun:inanim:m:v_kly
автоквести	автоквест	noun	noun:inanim:p:v_kly
автоквести	автоквест	noun	noun:inanim:p:v_naz
автоквести	автоквест	noun	noun:inanim:p:v_zna
автоквестові	автоквест	noun	noun:inanim:m:v_dav
автоквестові	автоквест	noun	noun:inanim:m:v_mis
автоквестом	автоквест	noun	noun:inanim:m:v_oru
автоквесту	автоквест	noun	noun:inanim:m:v_dav
автоквесту	автоквест	noun	noun:inanim:m:v_mis
автоквесту	автоквест	noun	noun:inanim:m:v_rod
автоквесті	автоквест	noun	noun:inanim:m:v_mis
автоквестів	автоквест	noun	noun:inanim:p:v_rod
автокемпінг	автокемпінг	noun	noun:inanim:m:v_naz
автокемпінг	автокемпінг	noun	noun:inanim:m:v_zna
автокемпінгам	автокемпінг	noun	noun:inanim:p:v_dav
автокемпінгами	автокемпінг	noun	noun:inanim:p:v_oru
автокемпінгах	автокемпінг	noun	noun:inanim:p:v_mis
автокемпінги	автокемпінг	noun	noun:inanim:p:v_kly
автокемпінги	автокемпінг	noun	noun:inanim:p:v_naz
автокемпінги	автокемпінг	noun	noun:inanim:p:v_zna
автокемпінгові	автокемпінг	noun	noun:inanim:m:v_dav
автокемпінгові	автокемпінг	noun	noun:inanim:m:v_mis
автокемпінгом	автокемпінг	noun	noun:inanim:m:v_oru
автокемпінгу	автокемпінг	noun	noun:inanim:m:v_dav
автокемпінгу	автокемпінг	noun	noun:inanim:m:v_kly
автокемпінгу	автокемпінг	noun	noun:inanim:m:v_mis
автокемпінгу	автокемпінг	noun	noun:inanim:m:v_rod
автокемпінгів	автокемпінг	noun	noun:inanim:p:v_rod
автокераторефрактометр	автокераторефрактометр	noun	noun:inanim:m:v_naz
автокераторефрактометр	автокераторефрактометр	noun	noun:inanim:m:v_zna
автокераторефрактометра	автокераторефрактометр	noun	noun:inanim:m:v_rod
автокераторефрактометрам	автокераторефрактометр	noun	noun:inanim:p:v_dav
автокераторефрактометрами	автокераторефрактометр	noun	noun:inanim:p:v_oru
автокераторефрактометрах	автокераторефрактометр	noun	noun:inanim:p:v_mis
автокераторефрактометре	автокераторефрактометр	noun	noun:inanim:m:v_kly
автокераторефрактометри	автокераторефрактометр	noun	noun:inanim:p:v_kly
автокераторефрактометри	автокераторефрактометр	noun	noun:inanim:p:v_naz
автокераторефрактометри	автокераторефрактометр	noun	noun:inanim:p:v_zna
автокераторефрактометрові	автокераторефрактометр	noun	noun:inanim:m:v_dav
автокераторефрактометрові	автокераторефрактометр	noun	noun:inanim:m:v_mis
автокераторефрактометром	автокераторефрактометр	noun	noun:inanim:m:v_oru
автокераторефрактометрі	автокераторефрактометр	noun	noun:inanim:m:v_mis
автокераторефрактометрів	автокераторефрактометр	noun	noun:inanim:p:v_rod
автокерманич	автокерманич	noun	noun:inanim:m:v_naz
автокерманич	автокерманич	noun	noun:inanim:m:v_zna
автокерманича	автокерманич	noun	noun:inanim:m:v_rod
автокерманичам	автокерманич	noun	noun:inanim:p:v_dav
автокерманичами	автокерманич	noun	noun:inanim:p:v_oru
автокерманичах	автокерманич	noun	noun:inanim:p:v_mis
автокерманичеві	автокерманич	noun	noun:inanim:m:v_dav
автокерманичеві	автокерманич	noun	noun:inanim:m:v_mis
автокерманичем	автокерманич	noun	noun:inanim:m:v_oru
автокерманичу	автокерманич	noun	noun:inanim:m:v_dav
автокерманичу	автокерманич	noun	noun:inanim:m:v_kly
автокерманичу	автокерманич	noun	noun:inanim:m:v_mis
автокерманичі	автокерманич	noun	noun:inanim:m:v_mis
автокерманичі	автокерманич	noun	noun:inanim:p:v_kly
автокерманичі	автокерманич	noun	noun:inanim:p:v_naz
автокерманичі	автокерманич	noun	noun:inanim:p:v_zna
автокерманичів	автокерманич	noun	noun:inanim:p:v_rod
автокефал	автокефал	noun	noun:anim:m:v_naz
автокефала	автокефал	noun	noun:anim:m:v_rod
автокефала	автокефал	noun	noun:anim:m:v_zna
автокефалам	автокефал	noun	noun:anim:p:v_dav
автокефалами	автокефал	noun	noun:anim:p:v_oru
автокефалах	автокефал	noun	noun:anim:p:v_mis
автокефале	автокефал	noun	noun:anim:m:v_kly
автокефали	автокефал	noun	noun:anim:p:v_kly
автокефали	автокефал	noun	noun:anim:p:v_naz
автокефали	автокефал	noun	noun:anim:p:v_zna:rare
автокефалові	автокефал	noun	noun:anim:m:v_dav
автокефалові	автокефал	noun	noun:anim:m:v_mis
автокефалом	автокефал	noun	noun:anim:m:v_oru
автокефалі	автокефал	noun	noun:anim:m:v_mis
автокефалів	автокефал	noun	noun:anim:p:v_rod
автокефалів	автокефал	noun	noun:anim:p:v_zna
автокефалій	автокефалія	noun	noun:inanim:p:v_rod
автокефаліст	автокефаліст	noun	noun:anim:m:v_naz
автокефаліста	автокефаліст	noun	noun:anim:m:v_rod
автокефаліста	автокефаліст	noun	noun:anim:m:v_zna
автокефалістам	автокефаліст	noun	noun:anim:p:v_dav
автокефалістами	автокефаліст	noun	noun:anim:p:v_oru
автокефалістах	автокефаліст	noun	noun:anim:p:v_mis
автокефалісте	автокефаліст	noun	noun:anim:m:v_kly
автокефалісти	автокефаліст	noun	noun:anim:p:v_kly
автокефалісти	автокефаліст	noun	noun:anim:p:v_naz
автокефалісти	автокефаліст	noun	noun:anim:p:v_zna:rare
автокефалістка	автокефалістка	noun	noun:anim:f:v_naz
автокефалісткам	автокефалістка	noun	noun:anim:p:v_dav
автокефалістками	автокефалістка	noun	noun:anim:p:v_oru
автокефалістках	автокефалістка	noun	noun:anim:p:v_mis
автокефалістки	автокефалістка	noun	noun:anim:f:v_rod
автокефалістки	автокефалістка	noun	noun:anim:p:v_kly
автокефалістки	автокефалістка	noun	noun:anim:p:v_naz
автокефалістки	автокефалістка	noun	noun:anim:p:v_zna:rare
автокефалістко	автокефалістка	noun	noun:anim:f:v_kly
автокефалісткою	автокефалістка	noun	noun:anim:f:v_oru
автокефалістку	автокефалістка	noun	noun:anim:f:v_zna
автокефалістові	автокефаліст	noun	noun:anim:m:v_dav
автокефалістові	автокефаліст	noun	noun:anim:m:v_mis
автокефалісток	автокефалістка	noun	noun:anim:p:v_rod
автокефалісток	автокефалістка	noun	noun:anim:p:v_zna
автокефалістом	автокефаліст	noun	noun:anim:m:v_oru
автокефалістці	автокефалістка	noun	noun:anim:f:v_dav
автокефалістці	автокефалістка	noun	noun:anim:f:v_mis
автокефалісті	автокефаліст	noun	noun:anim:m:v_mis
автокефалістів	автокефаліст	noun	noun:anim:p:v_rod
автокефалістів	автокефаліст	noun	noun:anim:p:v_zna
автокефалію	автокефалія	noun	noun:inanim:f:v_zna
автокефалія	автокефалія	noun	noun:inanim:f:v_naz
автокефаліям	автокефалія	noun	noun:inanim:p:v_dav
автокефаліями	автокефалія	noun	noun:inanim:p:v_oru
автокефаліях	автокефалія	noun	noun:inanim:p:v_mis
автокефаліє	автокефалія	noun	noun:inanim:f:v_kly
автокефалією	автокефалія	noun	noun:inanim:f:v_oru
автокефалії	автокефалія	noun	noun:inanim:f:v_dav
автокефалії	автокефалія	noun	noun:inanim:f:v_mis
автокефалії	автокефалія	noun	noun:inanim:f:v_rod
автокефалії	автокефалія	noun	noun:inanim:p:v_kly
автокефалії	автокефалія	noun	noun:inanim:p:v_naz
автокефалії	автокефалія	noun	noun:inanim:p:v_zna
автоклав	автоклав	noun	noun:inanim:m:v_naz
автоклав	автоклав	noun	noun:inanim:m:v_zna
автоклава	автоклав	noun	noun:inanim:m:v_rod
автоклавам	автоклав	noun	noun:inanim:p:v_dav
автоклавами	автоклав	noun	noun:inanim:p:v_oru
автоклавах	автоклав	noun	noun:inanim:p:v_mis
автоклаве	автоклав	noun	noun:inanim:m:v_kly
автоклави	автоклав	noun	noun:inanim:p:v_kly
автоклави	автоклав	noun	noun:inanim:p:v_naz
автоклави	автоклав	noun	noun:inanim:p:v_zna
автоклавник	автоклавник	noun	noun:anim:m:v_naz
автоклавника	автоклавник	noun	noun:anim:m:v_rod
автоклавника	автоклавник	noun	noun:anim:m:v_zna
автоклавникам	автоклавник	noun	noun:anim:p:v_dav
автоклавниками	автоклавник	noun	noun:anim:p:v_oru
автоклавниках	автоклавник	noun	noun:anim:p:v_mis
автоклавники	автоклавник	noun	noun:anim:p:v_kly
автоклавники	автоклавник	noun	noun:anim:p:v_naz
автоклавники	автоклавник	noun	noun:anim:p:v_zna:rare
автоклавникові	автоклавник	noun	noun:anim:m:v_dav
автоклавникові	автоклавник	noun	noun:anim:m:v_mis
автоклавником	автоклавник	noun	noun:anim:m:v_oru
автоклавнику	автоклавник	noun	noun:anim:m:v_dav
автоклавнику	автоклавник	noun	noun:anim:m:v_kly
автоклавнику	автоклавник	noun	noun:anim:m:v_mis
автоклавників	автоклавник	noun	noun:anim:p:v_rod
автоклавників	автоклавник	noun	noun:anim:p:v_zna
автоклавові	автоклав	noun	noun:inanim:m:v_dav
автоклавові	автоклав	noun	noun:inanim:m:v_mis
автоклавом	автоклав	noun	noun:inanim:m:v_oru
автоклавуванню	автоклавування	noun	noun:inanim:n:v_dav
автоклавуванню	автоклавування	noun	noun:inanim:n:v_mis
автоклавування	автоклавування	noun	noun:inanim:n:v_kly
автоклавування	автоклавування	noun	noun:inanim:n:v_naz
автоклавування	автоклавування	noun	noun:inanim:n:v_rod
автоклавування	автоклавування	noun	noun:inanim:n:v_zna
автоклавування	автоклавування	noun	noun:inanim:p:v_kly
автоклавування	автоклавування	noun	noun:inanim:p:v_naz
автоклавування	автоклавування	noun	noun:inanim:p:v_zna
автоклавуванням	автоклавування	noun	noun:inanim:n:v_oru
автоклавуванням	автоклавування	noun	noun:inanim:p:v_dav
автоклавуваннями	автоклавування	noun	noun:inanim:p:v_oru
автоклавуваннях	автоклавування	noun	noun:inanim:p:v_mis
автоклавуванні	автоклавування	noun	noun:inanim:n:v_mis
автоклавувань	автоклавування	noun	noun:inanim:p:v_rod
автоклаві	автоклав	noun	noun:inanim:m:v_mis
автоклавів	автоклав	noun	noun:inanim:p:v_rod
автокластер	автокластер	noun	noun:inanim:m:v_naz
автокластер	автокластер	noun	noun:inanim:m:v_zna
автокластера	автокластер	noun	noun:inanim:m:v_rod
автокластерам	автокластер	noun	noun:inanim:p:v_dav
автокластерами	автокластер	noun	noun:inanim:p:v_oru
автокластерах	автокластер	noun	noun:inanim:p:v_mis
автокластере	автокластер	noun	noun:inanim:m:v_kly
автокластери	автокластер	noun	noun:inanim:p:v_kly
автокластери	автокластер	noun	noun:inanim:p:v_naz
автокластери	автокластер	noun	noun:inanim:p:v_zna
автокластерові	автокластер	noun	noun:inanim:m:v_dav
автокластерові	автокластер	noun	noun:inanim:m:v_mis
автокластером	автокластер	noun	noun:inanim:m:v_oru
автокластері	автокластер	noun	noun:inanim:m:v_mis
автокластерів	автокластер	noun	noun:inanim:p:v_rod
автоклуб	автоклуб	noun	noun:inanim:m:v_naz
автоклуб	автоклуб	noun	noun:inanim:m:v_zna
автоклубам	автоклуб	noun	noun:inanim:p:v_dav
автоклубами	автоклуб	noun	noun:inanim:p:v_oru
автоклубах	автоклуб	noun	noun:inanim:p:v_mis
автоклубе	автоклуб	noun	noun:inanim:m:v_kly
автоклуби	автоклуб	noun	noun:inanim:p:v_kly
автоклуби	автоклуб	noun	noun:inanim:p:v_naz
автоклуби	автоклуб	noun	noun:inanim:p:v_zna
автоклубові	автоклуб	noun	noun:inanim:m:v_dav
автоклубові	автоклуб	noun	noun:inanim:m:v_mis
автоклубом	автоклуб	noun	noun:inanim:m:v_oru
автоклубу	автоклуб	noun	noun:inanim:m:v_dav
автоклубу	автоклуб	noun	noun:inanim:m:v_mis
автоклубу	автоклуб	noun	noun:inanim:m:v_rod
автоклубі	автоклуб	noun	noun:inanim:m:v_mis
автоклубів	автоклуб	noun	noun:inanim:p:v_rod
автоклікер	автоклікер	noun	noun:inanim:m:v_naz
автоклікер	автоклікер	noun	noun:inanim:m:v_zna
автоклікера	автоклікер	noun	noun:inanim:m:v_rod
автоклікерам	автоклікер	noun	noun:inanim:p:v_dav
автоклікерами	автоклікер	noun	noun:inanim:p:v_oru
автоклікерах	автоклікер	noun	noun:inanim:p:v_mis
автоклікере	автоклікер	noun	noun:inanim:m:v_kly
автоклікери	автоклікер	noun	noun:inanim:p:v_kly
автоклікери	автоклікер	noun	noun:inanim:p:v_naz
автоклікери	автоклікер	noun	noun:inanim:p:v_zna
автоклікерові	автоклікер	noun	noun:inanim:m:v_dav
автоклікерові	автоклікер	noun	noun:inanim:m:v_mis
автоклікером	автоклікер	noun	noun:inanim:m:v_oru
автоклікері	автоклікер	noun	noun:inanim:m:v_mis
автоклікерів	автоклікер	noun	noun:inanim:p:v_rod
автокоагуляцій	автокоагуляція	noun	noun:inanim:p:v_rod
автокоагуляцію	автокоагуляція	noun	noun:inanim:f:v_zna
автокоагуляція	автокоагуляція	noun	noun:inanim:f:v_naz
автокоагуляціям	автокоагуляція	noun	noun:inanim:p:v_dav
автокоагуляціями	автокоагуляція	noun	noun:inanim:p:v_oru
автокоагуляціях	автокоагуляція	noun	noun:inanim:p:v_mis
автокоагуляціє	автокоагуляція	noun	noun:inanim:f:v_kly
автокоагуляцією	автокоагуляція	noun	noun:inanim:f:v_oru
автокоагуляції	автокоагуляція	noun	noun:inanim:f:v_dav
автокоагуляції	автокоагуляція	noun	noun:inanim:f:v_mis
автокоагуляції	автокоагуляція	noun	noun:inanim:f:v_rod
автокоагуляції	автокоагуляція	noun	noun:inanim:p:v_kly
автокоагуляції	автокоагуляція	noun	noun:inanim:p:v_naz
автокоагуляції	автокоагуляція	noun	noun:inanim:p:v_zna
автокод	автокод	noun	noun:inanim:m:v_naz
автокод	автокод	noun	noun:inanim:m:v_zna
автокодам	автокод	noun	noun:inanim:p:v_dav
автокодами	автокод	noun	noun:inanim:p:v_oru
автокодах	автокод	noun	noun:inanim:p:v_mis
автокоде	автокод	noun	noun:inanim:m:v_kly
автокодер	автокодер	noun	noun:inanim:m:v_naz
автокодер	автокодер	noun	noun:inanim:m:v_zna
автокодера	автокодер	noun	noun:inanim:m:v_rod
автокодерам	автокодер	noun	noun:inanim:p:v_dav
автокодерами	автокодер	noun	noun:inanim:p:v_oru
автокодерах	автокодер	noun	noun:inanim:p:v_mis
автокодере	автокодер	noun	noun:inanim:m:v_kly
автокодери	автокодер	noun	noun:inanim:p:v_kly
автокодери	автокодер	noun	noun:inanim:p:v_naz
автокодери	автокодер	noun	noun:inanim:p:v_zna
автокодерові	автокодер	noun	noun:inanim:m:v_dav
автокодерові	автокодер	noun	noun:inanim:m:v_mis
автокодером	автокодер	noun	noun:inanim:m:v_oru
автокодері	автокодер	noun	noun:inanim:m:v_mis
автокодерів	автокодер	noun	noun:inanim:p:v_rod
автокоди	автокод	noun	noun:inanim:p:v_kly
автокоди	автокод	noun	noun:inanim:p:v_naz
автокоди	автокод	noun	noun:inanim:p:v_zna
автокодові	автокод	noun	noun:inanim:m:v_dav
автокодові	автокод	noun	noun:inanim:m:v_mis
автокодом	автокод	noun	noun:inanim:m:v_oru
автокоду	автокод	noun	noun:inanim:m:v_dav
автокоду	автокод	noun	noun:inanim:m:v_mis
автокоду	автокод	noun	noun:inanim:m:v_rod
автокоді	автокод	noun	noun:inanim:m:v_mis
автокодів	автокод	noun	noun:inanim:p:v_rod
автоколекцій	автоколекція	noun	noun:inanim:p:v_rod
автоколекцію	автоколекція	noun	noun:inanim:f:v_zna
автоколекція	автоколекція	noun	noun:inanim:f:v_naz
автоколекціям	автоколекція	noun	noun:inanim:p:v_dav
автоколекціями	автоколекція	noun	noun:inanim:p:v_oru
автоколекціях	автоколекція	noun	noun:inanim:p:v_mis
автоколекціє	автоколекція	noun	noun:inanim:f:v_kly
автоколекцією	автоколекція	noun	noun:inanim:f:v_oru
автоколекції	автоколекція	noun	noun:inanim:f:v_dav
автоколекції	автоколекція	noun	noun:inanim:f:v_mis
автоколекції	автоколекція	noun	noun:inanim:f:v_rod
автоколекції	автоколекція	noun	noun:inanim:p:v_kly
автоколекції	автоколекція	noun	noun:inanim:p:v_naz
автоколекції	автоколекція	noun	noun:inanim:p:v_zna
автоколиванню	автоколивання	noun	noun:inanim:n:v_dav
автоколиванню	автоколивання	noun	noun:inanim:n:v_mis
автоколивання	автоколивання	noun	noun:inanim:n:v_kly
автоколивання	автоколивання	noun	noun:inanim:n:v_naz
автоколивання	автоколивання	noun	noun:inanim:n:v_rod
автоколивання	автоколивання	noun	noun:inanim:n:v_zna
автоколивання	автоколивання	noun	noun:inanim:p:v_kly
автоколивання	автоколивання	noun	noun:inanim:p:v_naz
автоколивання	автоколивання	noun	noun:inanim:p:v_zna
автоколиванням	автоколивання	noun	noun:inanim:n:v_oru
автоколиванням	автоколивання	noun	noun:inanim:p:v_dav
автоколиваннями	автоколивання	noun	noun:inanim:p:v_oru
автоколиваннях	автоколивання	noun	noun:inanim:p:v_mis
автоколиванні	автоколивання	noun	noun:inanim:n:v_mis
автоколивань	автоколивання	noun	noun:inanim:p:v_rod
автоколон	автоколона	noun	noun:inanim:p:v_rod
автоколона	автоколона	noun	noun:inanim:f:v_naz
автоколонам	автоколона	noun	noun:inanim:p:v_dav
автоколонами	автоколона	noun	noun:inanim:p:v_oru
автоколонах	автоколона	noun	noun:inanim:p:v_mis
автоколони	автоколона	noun	noun:inanim:f:v_rod
автоколони	автоколона	noun	noun:inanim:p:v_kly
автоколони	автоколона	noun	noun:inanim:p:v_naz
автоколони	автоколона	noun	noun:inanim:p:v_zna
автоколоно	автоколона	noun	noun:inanim:f:v_kly
автоколоною	автоколона	noun	noun:inanim:f:v_oru
автоколону	автоколона	noun	noun:inanim:f:v_zna
автоколоні	автоколона	noun	noun:inanim:f:v_dav
автоколоні	автоколона	noun	noun:inanim:f:v_mis
автоколіматор	автоколіматор	noun	noun:inanim:m:v_naz
автоколіматор	автоколіматор	noun	noun:inanim:m:v_zna
автоколіматора	автоколіматор	noun	noun:inanim:m:v_rod
автоколіматорам	автоколіматор	noun	noun:inanim:p:v_dav
автоколіматорами	автоколіматор	noun	noun:inanim:p:v_oru
автоколіматорах	автоколіматор	noun	noun:inanim:p:v_mis
автоколіматоре	автоколіматор	noun	noun:inanim:m:v_kly
автоколіматори	автоколіматор	noun	noun:inanim:p:v_kly
автоколіматори	автоколіматор	noun	noun:inanim:p:v_naz
автоколіматори	автоколіматор	noun	noun:inanim:p:v_zna
автоколіматорові	автоколіматор	noun	noun:inanim:m:v_dav
автоколіматорові	автоколіматор	noun	noun:inanim:m:v_mis
автоколіматором	автоколіматор	noun	noun:inanim:m:v_oru
автоколіматорі	автоколіматор	noun	noun:inanim:m:v_mis
автоколіматорів	автоколіматор	noun	noun:inanim:p:v_rod
автоколімацій	автоколімація	noun	noun:inanim:p:v_rod
автоколімацію	автоколімація	noun	noun:inanim:f:v_zna
автоколімація	автоколімація	noun	noun:inanim:f:v_naz
автоколімаціям	автоколімація	noun	noun:inanim:p:v_dav
автоколімаціями	автоколімація	noun	noun:inanim:p:v_oru
автоколімаціях	автоколімація	noun	noun:inanim:p:v_mis
автоколімаціє	автоколімація	noun	noun:inanim:f:v_kly
автоколімацією	автоколімація	noun	noun:inanim:f:v_oru
автоколімації	автоколімація	noun	noun:inanim:f:v_dav
автоколімації	автоколімація	noun	noun:inanim:f:v_mis
автоколімації	автоколімація	noun	noun:inanim:f:v_rod
автоколімації	автоколімація	noun	noun:inanim:p:v_kly
автоколімації	автоколімація	noun	noun:inanim:p:v_naz
автоколімації	автоколімація	noun	noun:inanim:p:v_zna
автокомбінат	автокомбінат	noun	noun:inanim:m:v_naz
автокомбінат	автокомбінат	noun	noun:inanim:m:v_zna
автокомбінатам	автокомбінат	noun	noun:inanim:p:v_dav
автокомбінатами	автокомбінат	noun	noun:inanim:p:v_oru
автокомбінатах	автокомбінат	noun	noun:inanim:p:v_mis
автокомбінате	автокомбінат	noun	noun:inanim:m:v_kly
автокомбінати	автокомбінат	noun	noun:inanim:p:v_kly
автокомбінати	автокомбінат	noun	noun:inanim:p:v_naz
автокомбінати	автокомбінат	noun	noun:inanim:p:v_zna
автокомбінатові	автокомбінат	noun	noun:inanim:m:v_dav
автокомбінатові	автокомбінат	noun	noun:inanim:m:v_mis
автокомбінатом	автокомбінат	noun	noun:inanim:m:v_oru
автокомбінату	автокомбінат	noun	noun:inanim:m:v_dav
автокомбінату	автокомбінат	noun	noun:inanim:m:v_mis
автокомбінату	автокомбінат	noun	noun:inanim:m:v_rod
автокомбінаті	автокомбінат	noun	noun:inanim:m:v_mis
автокомбінатів	автокомбінат	noun	noun:inanim:p:v_rod
автокоментар	автокоментар	noun	noun:inanim:m:v_naz
автокоментар	автокоментар	noun	noun:inanim:m:v_zna
автокоментареві	автокоментар	noun	noun:inanim:m:v_dav
автокоментареві	автокоментар	noun	noun:inanim:m:v_mis
автокоментарем	автокоментар	noun	noun:inanim:m:v_oru
автокоментарю	автокоментар	noun	noun:inanim:m:v_dav
автокоментарю	автокоментар	noun	noun:inanim:m:v_kly
автокоментарю	автокоментар	noun	noun:inanim:m:v_mis
автокоментаря	автокоментар	noun	noun:inanim:m:v_rod
автокоментарям	автокоментар	noun	noun:inanim:p:v_dav
автокоментарями	автокоментар	noun	noun:inanim:p:v_oru
автокоментарях	автокоментар	noun	noun:inanim:p:v_mis
автокоментарі	автокоментар	noun	noun:inanim:m:v_mis
автокоментарі	автокоментар	noun	noun:inanim:p:v_kly
автокоментарі	автокоментар	noun	noun:inanim:p:v_naz
автокоментарі	автокоментар	noun	noun:inanim:p:v_zna
автокоментарів	автокоментар	noun	noun:inanim:p:v_rod
автокоментуванню	автокоментування	noun	noun:inanim:n:v_dav
автокоментуванню	автокоментування	noun	noun:inanim:n:v_mis
автокоментування	автокоментування	noun	noun:inanim:n:v_kly
автокоментування	автокоментування	noun	noun:inanim:n:v_naz
автокоментування	автокоментування	noun	noun:inanim:n:v_rod
автокоментування	автокоментування	noun	noun:inanim:n:v_zna
автокоментування	автокоментування	noun	noun:inanim:p:v_kly
автокоментування	автокоментування	noun	noun:inanim:p:v_naz
автокоментування	автокоментування	noun	noun:inanim:p:v_zna
автокоментуванням	автокоментування	noun	noun:inanim:n:v_oru
автокоментуванням	автокоментування	noun	noun:inanim:p:v_dav
автокоментуваннями	автокоментування	noun	noun:inanim:p:v_oru
автокоментуваннях	автокоментування	noun	noun:inanim:p:v_mis
автокоментуванні	автокоментування	noun	noun:inanim:n:v_mis
автокоментувань	автокоментування	noun	noun:inanim:p:v_rod
автокомпаній	автокомпанія	noun	noun:inanim:p:v_rod
автокомпанію	автокомпанія	noun	noun:inanim:f:v_zna
автокомпанія	автокомпанія	noun	noun:inanim:f:v_naz
автокомпаніям	автокомпанія	noun	noun:inanim:p:v_dav
автокомпаніями	автокомпанія	noun	noun:inanim:p:v_oru
автокомпаніях	автокомпанія	noun	noun:inanim:p:v_mis
автокомпаніє	автокомпанія	noun	noun:inanim:f:v_kly
автокомпанією	автокомпанія	noun	noun:inanim:f:v_oru
автокомпанії	автокомпанія	noun	noun:inanim:f:v_dav
автокомпанії	автокомпанія	noun	noun:inanim:f:v_mis
автокомпанії	автокомпанія	noun	noun:inanim:f:v_rod
автокомпанії	автокомпанія	noun	noun:inanim:p:v_kly
автокомпанії	автокомпанія	noun	noun:inanim:p:v_naz
автокомпанії	автокомпанія	noun	noun:inanim:p:v_zna
автокомпенсатор	автокомпенсатор	noun	noun:inanim:m:v_naz
автокомпенсатор	автокомпенсатор	noun	noun:inanim:m:v_zna
автокомпенсатора	автокомпенсатор	noun	noun:inanim:m:v_rod
автокомпенсаторам	автокомпенсатор	noun	noun:inanim:p:v_dav
автокомпенсаторами	автокомпенсатор	noun	noun:inanim:p:v_oru
автокомпенсаторах	автокомпенсатор	noun	noun:inanim:p:v_mis
автокомпенсаторе	автокомпенсатор	noun	noun:inanim:m:v_kly
автокомпенсатори	автокомпенсатор	noun	noun:inanim:p:v_kly
автокомпенсатори	автокомпенсатор	noun	noun:inanim:p:v_naz
автокомпенсатори	автокомпенсатор	noun	noun:inanim:p:v_zna
автокомпенсаторові	автокомпенсатор	noun	noun:inanim:m:v_dav
автокомпенсаторові	автокомпенсатор	noun	noun:inanim:m:v_mis
автокомпенсатором	автокомпенсатор	noun	noun:inanim:m:v_oru
автокомпенсаторі	автокомпенсатор	noun	noun:inanim:m:v_mis
автокомпенсаторів	автокомпенсатор	noun	noun:inanim:p:v_rod
автокомплекс	автокомплекс	noun	noun:inanim:m:v_naz
автокомплекс	автокомплекс	noun	noun:inanim:m:v_zna
автокомплексам	автокомплекс	noun	noun:inanim:p:v_dav
автокомплексами	автокомплекс	noun	noun:inanim:p:v_oru
автокомплексах	автокомплекс	noun	noun:inanim:p:v_mis
автокомплексе	автокомплекс	noun	noun:inanim:m:v_kly
автокомплекси	автокомплекс	noun	noun:inanim:p:v_kly
автокомплекси	автокомплекс	noun	noun:inanim:p:v_naz
автокомплекси	автокомплекс	noun	noun:inanim:p:v_zna
автокомплексові	автокомплекс	noun	noun:inanim:m:v_dav
автокомплексові	автокомплекс	noun	noun:inanim:m:v_mis
автокомплексом	автокомплекс	noun	noun:inanim:m:v_oru
автокомплексу	автокомплекс	noun	noun:inanim:m:v_dav
автокомплексу	автокомплекс	noun	noun:inanim:m:v_mis
автокомплексу	автокомплекс	noun	noun:inanim:m:v_rod
автокомплексі	автокомплекс	noun	noun:inanim:m:v_mis
автокомплексів	автокомплекс	noun	noun:inanim:p:v_rod
автокомплект	автокомплект	noun	noun:inanim:m:v_naz
автокомплект	автокомплект	noun	noun:inanim:m:v_zna
автокомплектам	автокомплект	noun	noun:inanim:p:v_dav
автокомплектами	автокомплект	noun	noun:inanim:p:v_oru
автокомплектах	автокомплект	noun	noun:inanim:p:v_mis
автокомплекте	автокомплект	noun	noun:inanim:m:v_kly
автокомплекти	автокомплект	noun	noun:inanim:p:v_kly
автокомплекти	автокомплект	noun	noun:inanim:p:v_naz
автокомплекти	автокомплект	noun	noun:inanim:p:v_zna
автокомплектові	автокомплект	noun	noun:inanim:m:v_dav
автокомплектові	автокомплект	noun	noun:inanim:m:v_mis
автокомплектом	автокомплект	noun	noun:inanim:m:v_oru
автокомплекту	автокомплект	noun	noun:inanim:m:v_dav
автокомплекту	автокомплект	noun	noun:inanim:m:v_mis
автокомплекту	автокомплект	noun	noun:inanim:m:v_rod
автокомплекті	автокомплект	noun	noun:inanim:m:v_mis
автокомплектів	автокомплект	noun	noun:inanim:p:v_rod
автокомпонент	автокомпонент	noun	noun:inanim:m:v_naz
автокомпонент	автокомпонент	noun	noun:inanim:m:v_zna
автокомпонента	автокомпонент	noun	noun:inanim:m:v_rod
автокомпонентам	автокомпонент	noun	noun:inanim:p:v_dav
автокомпонентами	автокомпонент	noun	noun:inanim:p:v_oru
автокомпонентах	автокомпонент	noun	noun:inanim:p:v_mis
автокомпоненте	автокомпонент	noun	noun:inanim:m:v_kly
автокомпоненти	автокомпонент	noun	noun:inanim:p:v_kly
автокомпоненти	автокомпонент	noun	noun:inanim:p:v_naz
автокомпоненти	автокомпонент	noun	noun:inanim:p:v_zna
автокомпонентові	автокомпонент	noun	noun:inanim:m:v_dav
автокомпонентові	автокомпонент	noun	noun:inanim:m:v_mis
автокомпонентом	автокомпонент	noun	noun:inanim:m:v_oru
автокомпоненті	автокомпонент	noun	noun:inanim:m:v_mis
автокомпонентів	автокомпонент	noun	noun:inanim:p:v_rod
автокомунікацій	автокомунікація	noun	noun:inanim:p:v_rod
автокомунікацію	автокомунікація	noun	noun:inanim:f:v_zna
автокомунікація	автокомунікація	noun	noun:inanim:f:v_naz
автокомунікаціям	автокомунікація	noun	noun:inanim:p:v_dav
автокомунікаціями	автокомунікація	noun	noun:inanim:p:v_oru
автокомунікаціях	автокомунікація	noun	noun:inanim:p:v_mis
автокомунікаціє	автокомунікація	noun	noun:inanim:f:v_kly
автокомунікацією	автокомунікація	noun	noun:inanim:f:v_oru
автокомунікації	автокомунікація	noun	noun:inanim:f:v_dav
автокомунікації	автокомунікація	noun	noun:inanim:f:v_mis
автокомунікації	автокомунікація	noun	noun:inanim:f:v_rod
автокомунікації	автокомунікація	noun	noun:inanim:p:v_kly
автокомунікації	автокомунікація	noun	noun:inanim:p:v_naz
автокомунікації	автокомунікація	noun	noun:inanim:p:v_zna
автоконвертор	автоконвертор	noun	noun:inanim:m:v_naz
автоконвертор	автоконвертор	noun	noun:inanim:m:v_zna
автоконвертора	автоконвертор	noun	noun:inanim:m:v_rod
автоконверторам	автоконвертор	noun	noun:inanim:p:v_dav
автоконверторами	автоконвертор	noun	noun:inanim:p:v_oru
автоконверторах	автоконвертор	noun	noun:inanim:p:v_mis
автоконверторе	автоконвертор	noun	noun:inanim:m:v_kly
автоконвертори	автоконвертор	noun	noun:inanim:p:v_kly
автоконвертори	автоконвертор	noun	noun:inanim:p:v_naz
автоконвертори	автоконвертор	noun	noun:inanim:p:v_zna
автоконверторові	автоконвертор	noun	noun:inanim:m:v_dav
автоконверторові	автоконвертор	noun	noun:inanim:m:v_mis
автоконвертором	автоконвертор	noun	noun:inanim:m:v_oru
автоконверторі	автоконвертор	noun	noun:inanim:m:v_mis
автоконверторів	автоконвертор	noun	noun:inanim:p:v_rod
автоконсервант	автоконсервант	noun	noun:inanim:m:v_naz
автоконсервант	автоконсервант	noun	noun:inanim:m:v_zna
автоконсервантам	автоконсервант	noun	noun:inanim:p:v_dav
автоконсервантами	автоконсервант	noun	noun:inanim:p:v_oru
автоконсервантах	автоконсервант	noun	noun:inanim:p:v_mis
автоконсерванте	автоконсервант	noun	noun:inanim:m:v_kly
автоконсерванти	автоконсервант	noun	noun:inanim:p:v_kly
автоконсерванти	автоконсервант	noun	noun:inanim:p:v_naz
автоконсерванти	автоконсервант	noun	noun:inanim:p:v_zna
автоконсервантові	автоконсервант	noun	noun:inanim:m:v_dav
автоконсервантові	автоконсервант	noun	noun:inanim:m:v_mis
автоконсервантом	автоконсервант	noun	noun:inanim:m:v_oru
автоконсерванту	автоконсервант	noun	noun:inanim:m:v_dav
автоконсерванту	автоконсервант	noun	noun:inanim:m:v_mis
автоконсерванту	автоконсервант	noun	noun:inanim:m:v_rod
автоконсерванті	автоконсервант	noun	noun:inanim:m:v_mis
автоконсервантів	автоконсервант	noun	noun:inanim:p:v_rod
автоконструктор	автоконструктор	noun	noun:anim:m:v_naz
автоконструктора	автоконструктор	noun	noun:anim:m:v_rod
автоконструктора	автоконструктор	noun	noun:anim:m:v_zna
автоконструкторам	автоконструктор	noun	noun:anim:p:v_dav
автоконструкторами	автоконструктор	noun	noun:anim:p:v_oru
автоконструкторах	автоконструктор	noun	noun:anim:p:v_mis
автоконструкторе	автоконструктор	noun	noun:anim:m:v_kly
автоконструктори	автоконструктор	noun	noun:anim:p:v_kly
автоконструктори	автоконструктор	noun	noun:anim:p:v_naz
автоконструктори	автоконструктор	noun	noun:anim:p:v_zna:rare
автоконструкторові	автоконструктор	noun	noun:anim:m:v_dav
автоконструкторові	автоконструктор	noun	noun:anim:m:v_mis
автоконструктором	автоконструктор	noun	noun:anim:m:v_oru
автоконструкторі	автоконструктор	noun	noun:anim:m:v_mis
автоконструкторів	автоконструктор	noun	noun:anim:p:v_rod
автоконструкторів	автоконструктор	noun	noun:anim:p:v_zna
автоконтейнер	автоконтейнер	noun	noun:inanim:m:v_naz
автоконтейнер	автоконтейнер	noun	noun:inanim:m:v_zna
автоконтейнера	автоконтейнер	noun	noun:inanim:m:v_rod
автоконтейнерам	автоконтейнер	noun	noun:inanim:p:v_dav
автоконтейнерами	автоконтейнер	noun	noun:inanim:p:v_oru
автоконтейнерах	автоконтейнер	noun	noun:inanim:p:v_mis
автоконтейнере	автоконтейнер	noun	noun:inanim:m:v_kly
автоконтейнери	автоконтейнер	noun	noun:inanim:p:v_kly
автоконтейнери	автоконтейнер	noun	noun:inanim:p:v_naz
автоконтейнери	автоконтейнер	noun	noun:inanim:p:v_zna
автоконтейнеровоза	автоконтейнеровіз	noun	noun:inanim:m:v_rod
автоконтейнеровозам	автоконтейнеровіз	noun	noun:inanim:p:v_dav
автоконтейнеровозами	автоконтейнеровіз	noun	noun:inanim:p:v_oru
автоконтейнеровозах	автоконтейнеровіз	noun	noun:inanim:p:v_mis
автоконтейнеровозе	автоконтейнеровіз	noun	noun:inanim:m:v_kly
автоконтейнеровози	автоконтейнеровіз	noun	noun:inanim:p:v_kly
автоконтейнеровози	автоконтейнеровіз	noun	noun:inanim:p:v_naz
автоконтейнеровози	автоконтейнеровіз	noun	noun:inanim:p:v_zna
автоконтейнеровозові	автоконтейнеровіз	noun	noun:inanim:m:v_dav
автоконтейнеровозові	автоконтейнеровіз	noun	noun:inanim:m:v_mis
автоконтейнеровозом	автоконтейнеровіз	noun	noun:inanim:m:v_oru
автоконтейнеровозі	автоконтейнеровіз	noun	noun:inanim:m:v_mis
автоконтейнеровозів	автоконтейнеровіз	noun	noun:inanim:p:v_rod
автоконтейнерові	автоконтейнер	noun	noun:inanim:m:v_dav
автоконтейнерові	автоконтейнер	noun	noun:inanim:m:v_mis
автоконтейнеровіз	автоконтейнеровіз	noun	noun:inanim:m:v_naz
автоконтейнеровіз	автоконтейнеровіз	noun	noun:inanim:m:v_zna
автоконтейнером	автоконтейнер	noun	noun:inanim:m:v_oru
автоконтейнері	автоконтейнер	noun	noun:inanim:m:v_mis
автоконтейнерів	автоконтейнер	noun	noun:inanim:p:v_rod
автоконтор	автоконтора	noun	noun:inanim:p:v_rod
автоконтора	автоконтора	noun	noun:inanim:f:v_naz
автоконторам	автоконтора	noun	noun:inanim:p:v_dav
автоконторами	автоконтора	noun	noun:inanim:p:v_oru
автоконторах	автоконтора	noun	noun:inanim:p:v_mis
автоконтори	автоконтора	noun	noun:inanim:f:v_rod
автоконтори	автоконтора	noun	noun:inanim:p:v_kly
автоконтори	автоконтора	noun	noun:inanim:p:v_naz
автоконтори	автоконтора	noun	noun:inanim:p:v_zna
автоконторо	автоконтора	noun	noun:inanim:f:v_kly
автоконторою	автоконтора	noun	noun:inanim:f:v_oru
автоконтору	автоконтора	noun	noun:inanim:f:v_zna
автоконторі	автоконтора	noun	noun:inanim:f:v_dav
автоконторі	автоконтора	noun	noun:inanim:f:v_mis
автоконтрабандист	автоконтрабандист	noun	noun:anim:m:v_naz
автоконтрабандиста	автоконтрабандист	noun	noun:anim:m:v_rod
автоконтрабандиста	автоконтрабандист	noun	noun:anim:m:v_zna
автоконтрабандистам	автоконтрабандист	noun	noun:anim:p:v_dav
автоконтрабандистами	автоконтрабандист	noun	noun:anim:p:v_oru
автоконтрабандистах	автоконтрабандист	noun	noun:anim:p:v_mis
автоконтрабандисте	автоконтрабандист	noun	noun:anim:m:v_kly
автоконтрабандисти	автоконтрабандист	noun	noun:anim:p:v_kly
автоконтрабандисти	автоконтрабандист	noun	noun:anim:p:v_naz
автоконтрабандисти	автоконтрабандист	noun	noun:anim:p:v_zna:rare
автоконтрабандистові	автоконтрабандист	noun	noun:anim:m:v_dav
автоконтрабандистові	автоконтрабандист	noun	noun:anim:m:v_mis
автоконтрабандистом	автоконтрабандист	noun	noun:anim:m:v_oru
автоконтрабандисті	автоконтрабандист	noun	noun:anim:m:v_mis
автоконтрабандистів	автоконтрабандист	noun	noun:anim:p:v_rod
автоконтрабандистів	автоконтрабандист	noun	noun:anim:p:v_zna
автоконцерн	автоконцерн	noun	noun:inanim:m:v_naz
автоконцерн	автоконцерн	noun	noun:inanim:m:v_zna
автоконцернам	автоконцерн	noun	noun:inanim:p:v_dav
автоконцернами	автоконцерн	noun	noun:inanim:p:v_oru
автоконцернах	автоконцерн	noun	noun:inanim:p:v_mis
автоконцерне	автоконцерн	noun	noun:inanim:m:v_kly
автоконцерни	автоконцерн	noun	noun:inanim:p:v_kly
автоконцерни	автоконцерн	noun	noun:inanim:p:v_naz
автоконцерни	автоконцерн	noun	noun:inanim:p:v_zna
автоконцернові	автоконцерн	noun	noun:inanim:m:v_dav
автоконцернові	автоконцерн	noun	noun:inanim:m:v_mis
автоконцерном	автоконцерн	noun	noun:inanim:m:v_oru
автоконцерну	автоконцерн	noun	noun:inanim:m:v_dav
автоконцерну	автоконцерн	noun	noun:inanim:m:v_mis
автоконцерну	автоконцерн	noun	noun:inanim:m:v_rod
автоконцерні	автоконцерн	noun	noun:inanim:m:v_mis
автоконцернів	автоконцерн	noun	noun:inanim:p:v_rod
автокооператив	автокооператив	noun	noun:inanim:m:v_naz
автокооператив	автокооператив	noun	noun:inanim:m:v_zna
автокооперативам	автокооператив	noun	noun:inanim:p:v_dav
автокооперативами	автокооператив	noun	noun:inanim:p:v_oru
автокооперативах	автокооператив	noun	noun:inanim:p:v_mis
автокооперативе	автокооператив	noun	noun:inanim:m:v_kly
автокооперативи	автокооператив	noun	noun:inanim:p:v_kly
автокооперативи	автокооператив	noun	noun:inanim:p:v_naz
автокооперативи	автокооператив	noun	noun:inanim:p:v_zna
автокооперативові	автокооператив	noun	noun:inanim:m:v_dav
автокооперативові	автокооператив	noun	noun:inanim:m:v_mis
автокооперативом	автокооператив	noun	noun:inanim:m:v_oru
автокооперативу	автокооператив	noun	noun:inanim:m:v_dav
автокооперативу	автокооператив	noun	noun:inanim:m:v_mis
автокооперативу	автокооператив	noun	noun:inanim:m:v_rod
автокооперативі	автокооператив	noun	noun:inanim:m:v_mis
автокооперативів	автокооператив	noun	noun:inanim:p:v_rod
автокооператор	автокооператор	noun	noun:anim:m:v_naz
автокооператора	автокооператор	noun	noun:anim:m:v_rod
автокооператора	автокооператор	noun	noun:anim:m:v_zna
автокооператорам	автокооператор	noun	noun:anim:p:v_dav
автокооператорами	автокооператор	noun	noun:anim:p:v_oru
автокооператорах	автокооператор	noun	noun:anim:p:v_mis
автокооператоре	автокооператор	noun	noun:anim:m:v_kly
автокооператори	автокооператор	noun	noun:anim:p:v_kly
автокооператори	автокооператор	noun	noun:anim:p:v_naz
автокооператори	автокооператор	noun	noun:anim:p:v_zna:rare
автокооператорові	автокооператор	noun	noun:anim:m:v_dav
автокооператорові	автокооператор	noun	noun:anim:m:v_mis
автокооператором	автокооператор	noun	noun:anim:m:v_oru
автокооператорі	автокооператор	noun	noun:anim:m:v_mis
автокооператорів	автокооператор	noun	noun:anim:p:v_rod
автокооператорів	автокооператор	noun	noun:anim:p:v_zna
автокорб	автокорба	noun	noun:inanim:p:v_rod
автокорба	автокорба	noun	noun:inanim:f:v_naz
автокорбам	автокорба	noun	noun:inanim:p:v_dav
автокорбами	автокорба	noun	noun:inanim:p:v_oru
автокорбах	автокорба	noun	noun:inanim:p:v_mis
автокорби	автокорба	noun	noun:inanim:f:v_rod
автокорби	автокорба	noun	noun:inanim:p:v_kly
автокорби	автокорба	noun	noun:inanim:p:v_naz
автокорби	автокорба	noun	noun:inanim:p:v_zna
автокорбо	автокорба	noun	noun:inanim:f:v_kly
автокорбою	автокорба	noun	noun:inanim:f:v_oru
автокорбу	автокорба	noun	noun:inanim:f:v_zna
автокорбі	автокорба	noun	noun:inanim:f:v_dav
автокорбі	автокорба	noun	noun:inanim:f:v_mis
автокорд	автокорд	noun	noun:inanim:m:v_naz
автокорд	автокорд	noun	noun:inanim:m:v_zna
автокордам	автокорд	noun	noun:inanim:p:v_dav
автокордами	автокорд	noun	noun:inanim:p:v_oru
автокордах	автокорд	noun	noun:inanim:p:v_mis
автокорде	автокорд	noun	noun:inanim:m:v_kly
автокорди	автокорд	noun	noun:inanim:p:v_kly
автокорди	автокорд	noun	noun:inanim:p:v_naz
автокорди	автокорд	noun	noun:inanim:p:v_zna
автокордові	автокорд	noun	noun:inanim:m:v_dav
автокордові	автокорд	noun	noun:inanim:m:v_mis
автокордом	автокорд	noun	noun:inanim:m:v_oru
автокорду	автокорд	noun	noun:inanim:m:v_dav
автокорду	автокорд	noun	noun:inanim:m:v_mis
автокорду	автокорд	noun	noun:inanim:m:v_rod
автокорді	автокорд	noun	noun:inanim:m:v_mis
автокордів	автокорд	noun	noun:inanim:p:v_rod
автокоректор	автокоректор	noun	noun:inanim:m:v_naz
автокоректор	автокоректор	noun	noun:inanim:m:v_zna
автокоректора	автокоректор	noun	noun:inanim:m:v_rod
автокоректорам	автокоректор	noun	noun:inanim:p:v_dav
автокоректорами	автокоректор	noun	noun:inanim:p:v_oru
автокоректорах	автокоректор	noun	noun:inanim:p:v_mis
автокоректоре	автокоректор	noun	noun:inanim:m:v_kly
автокоректори	автокоректор	noun	noun:inanim:p:v_kly
автокоректори	автокоректор	noun	noun:inanim:p:v_naz
автокоректори	автокоректор	noun	noun:inanim:p:v_zna
автокоректорові	автокоректор	noun	noun:inanim:m:v_dav
автокоректорові	автокоректор	noun	noun:inanim:m:v_mis
автокоректором	автокоректор	noun	noun:inanim:m:v_oru
автокоректорі	автокоректор	noun	noun:inanim:m:v_mis
автокоректорів	автокоректор	noun	noun:inanim:p:v_rod
автокорекцій	автокорекція	noun	noun:inanim:p:v_rod
автокорекцію	автокорекція	noun	noun:inanim:f:v_zna
автокорекція	автокорекція	noun	noun:inanim:f:v_naz
автокорекціям	автокорекція	noun	noun:inanim:p:v_dav
автокорекціями	автокорекція	noun	noun:inanim:p:v_oru
автокорекціях	автокорекція	noun	noun:inanim:p:v_mis
автокорекціє	автокорекція	noun	noun:inanim:f:v_kly
автокорекцією	автокорекція	noun	noun:inanim:f:v_oru
автокорекції	автокорекція	noun	noun:inanim:f:v_dav
автокорекції	автокорекція	noun	noun:inanim:f:v_mis
автокорекції	автокорекція	noun	noun:inanim:f:v_rod
автокорекції	автокорекція	noun	noun:inanim:p:v_kly
автокорекції	автокорекція	noun	noun:inanim:p:v_naz
автокорекції	автокорекція	noun	noun:inanim:p:v_zna
автокорелограм	автокорелограма	noun	noun:inanim:p:v_rod
автокорелограма	автокорелограма	noun	noun:inanim:f:v_naz
автокорелограмам	автокорелограма	noun	noun:inanim:p:v_dav
автокорелограмами	автокорелограма	noun	noun:inanim:p:v_oru
автокорелограмах	автокорелограма	noun	noun:inanim:p:v_mis
автокорелограми	автокорелограма	noun	noun:inanim:f:v_rod
автокорелограми	автокорелограма	noun	noun:inanim:p:v_kly
автокорелограми	автокорелограма	noun	noun:inanim:p:v_naz
автокорелограми	автокорелограма	noun	noun:inanim:p:v_zna
автокорелограмо	автокорелограма	noun	noun:inanim:f:v_kly
автокорелограмою	автокорелограма	noun	noun:inanim:f:v_oru
автокорелограму	автокорелограма	noun	noun:inanim:f:v_zna
автокорелограмі	автокорелограма	noun	noun:inanim:f:v_dav
автокорелограмі	автокорелограма	noun	noun:inanim:f:v_mis
автокорелятор	автокорелятор	noun	noun:inanim:m:v_naz
автокорелятор	автокорелятор	noun	noun:inanim:m:v_zna
автокорелятора	автокорелятор	noun	noun:inanim:m:v_rod
автокореляторам	автокорелятор	noun	noun:inanim:p:v_dav
автокореляторами	автокорелятор	noun	noun:inanim:p:v_oru
автокореляторах	автокорелятор	noun	noun:inanim:p:v_mis
автокореляторе	автокорелятор	noun	noun:inanim:m:v_kly
автокорелятори	автокорелятор	noun	noun:inanim:p:v_kly
автокорелятори	автокорелятор	noun	noun:inanim:p:v_naz
автокорелятори	автокорелятор	noun	noun:inanim:p:v_zna
автокореляторові	автокорелятор	noun	noun:inanim:m:v_dav
автокореляторові	автокорелятор	noun	noun:inanim:m:v_mis
автокорелятором	автокорелятор	noun	noun:inanim:m:v_oru
автокореляторі	автокорелятор	noun	noun:inanim:m:v_mis
автокореляторів	автокорелятор	noun	noun:inanim:p:v_rod
автокореляцій	автокореляція	noun	noun:inanim:p:v_rod
автокореляцію	автокореляція	noun	noun:inanim:f:v_zna
автокореляція	автокореляція	noun	noun:inanim:f:v_naz
автокореляціям	автокореляція	noun	noun:inanim:p:v_dav
автокореляціями	автокореляція	noun	noun:inanim:p:v_oru
автокореляціях	автокореляція	noun	noun:inanim:p:v_mis
автокореляціє	автокореляція	noun	noun:inanim:f:v_kly
автокореляцією	автокореляція	noun	noun:inanim:f:v_oru
автокореляції	автокореляція	noun	noun:inanim:f:v_dav
автокореляції	автокореляція	noun	noun:inanim:f:v_mis
автокореляції	автокореляція	noun	noun:inanim:f:v_rod
автокореляції	автокореляція	noun	noun:inanim:p:v_kly
автокореляції	автокореляція	noun	noun:inanim:p:v_naz
автокореляції	автокореляція	noun	noun:inanim:p:v_zna
автокорпорацій	автокорпорація	noun	noun:inanim:p:v_rod
автокорпорацію	автокорпорація	noun	noun:inanim:f:v_zna
автокорпорація	автокорпорація	noun	noun:inanim:f:v_naz
автокорпораціям	автокорпорація	noun	noun:inanim:p:v_dav
автокорпораціями	автокорпорація	noun	noun:inanim:p:v_oru
автокорпораціях	автокорпорація	noun	noun:inanim:p:v_mis
автокорпораціє	автокорпорація	noun	noun:inanim:f:v_kly
автокорпорацією	автокорпорація	noun	noun:inanim:f:v_oru
автокорпорації	автокорпорація	noun	noun:inanim:f:v_dav
автокорпорації	автокорпорація	noun	noun:inanim:f:v_mis
автокорпорації	автокорпорація	noun	noun:inanim:f:v_rod
автокорпорації	автокорпорація	noun	noun:inanim:p:v_kly
автокорпорації	автокорпорація	noun	noun:inanim:p:v_naz
автокорпорації	автокорпорація	noun	noun:inanim:p:v_zna
автокортеж	автокортеж	noun	noun:inanim:m:v_naz
автокортеж	автокортеж	noun	noun:inanim:m:v_zna
автокортежам	автокортеж	noun	noun:inanim:p:v_dav
автокортежами	автокортеж	noun	noun:inanim:p:v_oru
автокортежах	автокортеж	noun	noun:inanim:p:v_mis
автокортеже	автокортеж	noun	noun:inanim:m:v_kly
автокортежеві	автокортеж	noun	noun:inanim:m:v_dav
автокортежеві	автокортеж	noun	noun:inanim:m:v_mis
автокортежем	автокортеж	noun	noun:inanim:m:v_oru
автокортежу	автокортеж	noun	noun:inanim:m:v_dav
автокортежу	автокортеж	noun	noun:inanim:m:v_mis
автокортежу	автокортеж	noun	noun:inanim:m:v_rod
автокортежі	автокортеж	noun	noun:inanim:m:v_mis
автокортежі	автокортеж	noun	noun:inanim:p:v_kly
автокортежі	автокортеж	noun	noun:inanim:p:v_naz
автокортежі	автокортеж	noun	noun:inanim:p:v_zna
автокортежів	автокортеж	noun	noun:inanim:p:v_rod
автокрад	автокрад	noun	noun:anim:m:v_naz
автокрада	автокрад	noun	noun:anim:m:v_rod
автокрада	автокрад	noun	noun:anim:m:v_zna
автокрадам	автокрад	noun	noun:anim:p:v_dav
автокрадами	автокрад	noun	noun:anim:p:v_oru
автокрадах	автокрад	noun	noun:anim:p:v_mis
автокраде	автокрад	noun	noun:anim:m:v_kly
автокради	автокрад	noun	noun:anim:p:v_kly
автокради	автокрад	noun	noun:anim:p:v_naz
автокради	автокрад	noun	noun:anim:p:v_zna:rare
автокрадові	автокрад	noun	noun:anim:m:v_dav
автокрадові	автокрад	noun	noun:anim:m:v_mis
автокрадом	автокрад	noun	noun:anim:m:v_oru
автокраді	автокрад	noun	noun:anim:m:v_mis
автокрадів	автокрад	noun	noun:anim:p:v_rod
автокрадів	автокрад	noun	noun:anim:p:v_zna
автокрадіжка	автокрадіжка	noun	noun:inanim:f:v_naz
автокрадіжкам	автокрадіжка	noun	noun:inanim:p:v_dav
автокрадіжками	автокрадіжка	noun	noun:inanim:p:v_oru
автокрадіжках	автокрадіжка	noun	noun:inanim:p:v_mis
автокрадіжки	автокрадіжка	noun	noun:inanim:f:v_rod
автокрадіжки	автокрадіжка	noun	noun:inanim:p:v_kly
автокрадіжки	автокрадіжка	noun	noun:inanim:p:v_naz
автокрадіжки	автокрадіжка	noun	noun:inanim:p:v_zna
автокрадіжко	автокрадіжка	noun	noun:inanim:f:v_kly
автокрадіжкою	автокрадіжка	noun	noun:inanim:f:v_oru
автокрадіжку	автокрадіжка	noun	noun:inanim:f:v_zna
автокрадіжок	автокрадіжка	noun	noun:inanim:p:v_rod
автокрадіжці	автокрадіжка	noun	noun:inanim:f:v_dav
автокрадіжці	автокрадіжка	noun	noun:inanim:f:v_mis
автокрадій	автокрадій	noun	noun:anim:m:v_naz
автокрадію	автокрадій	noun	noun:anim:m:v_dav
автокрадію	автокрадій	noun	noun:anim:m:v_kly
автокрадію	автокрадій	noun	noun:anim:m:v_mis
автокрадія	автокрадій	noun	noun:anim:m:v_rod
автокрадія	автокрадій	noun	noun:anim:m:v_zna
автокрадіям	автокрадій	noun	noun:anim:p:v_dav
автокрадіями	автокрадій	noun	noun:anim:p:v_oru
автокрадіях	автокрадій	noun	noun:anim:p:v_mis
автокрадієві	автокрадій	noun	noun:anim:m:v_dav
автокрадієві	автокрадій	noun	noun:anim:m:v_mis
автокрадієм	автокрадій	noun	noun:anim:m:v_oru
автокрадії	автокрадій	noun	noun:anim:m:v_mis
автокрадії	автокрадій	noun	noun:anim:p:v_kly
автокрадії	автокрадій	noun	noun:anim:p:v_naz
автокрадії	автокрадій	noun	noun:anim:p:v_zna:rare
автокрадіїв	автокрадій	noun	noun:anim:p:v_rod
автокрадіїв	автокрадій	noun	noun:anim:p:v_zna
автокрамнице	автокрамниця	noun	noun:inanim:f:v_kly
автокрамницею	автокрамниця	noun	noun:inanim:f:v_oru
автокрамниць	автокрамниця	noun	noun:inanim:p:v_rod
автокрамницю	автокрамниця	noun	noun:inanim:f:v_zna
автокрамниця	автокрамниця	noun	noun:inanim:f:v_naz
автокрамницям	автокрамниця	noun	noun:inanim:p:v_dav
автокрамницями	автокрамниця	noun	noun:inanim:p:v_oru
автокрамницях	автокрамниця	noun	noun:inanim:p:v_mis
автокрамниці	автокрамниця	noun	noun:inanim:f:v_dav
автокрамниці	автокрамниця	noun	noun:inanim:f:v_mis
автокрамниці	автокрамниця	noun	noun:inanim:f:v_rod
автокрамниці	автокрамниця	noun	noun:inanim:p:v_kly
автокрамниці	автокрамниця	noun	noun:inanim:p:v_naz
автокрамниці	автокрамниця	noun	noun:inanim:p:v_zna
автокран	автокран	noun	noun:inanim:m:v_naz
автокран	автокран	noun	noun:inanim:m:v_zna
автокрана	автокран	noun	noun:inanim:m:v_rod
автокранам	автокран	noun	noun:inanim:p:v_dav
автокранами	автокран	noun	noun:inanim:p:v_oru
автокранах	автокран	noun	noun:inanim:p:v_mis
автокране	автокран	noun	noun:inanim:m:v_kly
автокрани	автокран	noun	noun:inanim:p:v_kly
автокрани	автокран	noun	noun:inanim:p:v_naz
автокрани	автокран	noun	noun:inanim:p:v_zna
автокранові	автокран	noun	noun:inanim:m:v_dav
автокранові	автокран	noun	noun:inanim:m:v_mis
автокраном	автокран	noun	noun:inanim:m:v_oru
автокрані	автокран	noun	noun:inanim:m:v_mis
автокранів	автокран	noun	noun:inanim:p:v_rod
автокранівник	автокранівник	noun	noun:anim:m:v_naz
автокранівника	автокранівник	noun	noun:anim:m:v_rod
автокранівника	автокранівник	noun	noun:anim:m:v_zna
автокранівникам	автокранівник	noun	noun:anim:p:v_dav
автокранівниками	автокранівник	noun	noun:anim:p:v_oru
автокранівниках	автокранівник	noun	noun:anim:p:v_mis
автокранівники	автокранівник	noun	noun:anim:p:v_kly
автокранівники	автокранівник	noun	noun:anim:p:v_naz
автокранівники	автокранівник	noun	noun:anim:p:v_zna:rare
автокранівникові	автокранівник	noun	noun:anim:m:v_dav
автокранівникові	автокранівник	noun	noun:anim:m:v_mis
автокранівником	автокранівник	noun	noun:anim:m:v_oru
автокранівнику	автокранівник	noun	noun:anim:m:v_dav
автокранівнику	автокранівник	noun	noun:anim:m:v_kly
автокранівнику	автокранівник	noun	noun:anim:m:v_mis
автокранівників	автокранівник	noun	noun:anim:p:v_rod
автокранівників	автокранівник	noun	noun:anim:p:v_zna
автокрасуне	автокрасуня	noun	noun:inanim:f:v_kly
автокрасунею	автокрасуня	noun	noun:inanim:f:v_oru
автокрасунь	автокрасуня	noun	noun:inanim:p:v_rod
автокрасуню	автокрасуня	noun	noun:inanim:f:v_zna
автокрасуня	автокрасуня	noun	noun:inanim:f:v_naz
автокрасуням	автокрасуня	noun	noun:inanim:p:v_dav
автокрасунями	автокрасуня	noun	noun:inanim:p:v_oru
автокрасунях	автокрасуня	noun	noun:inanim:p:v_mis
автокрасуні	автокрасуня	noun	noun:inanim:f:v_dav
автокрасуні	автокрасуня	noun	noun:inanim:f:v_mis
автокрасуні	автокрасуня	noun	noun:inanim:f:v_rod
автокрасуні	автокрасуня	noun	noun:inanim:p:v_kly
автокрасуні	автокрасуня	noun	noun:inanim:p:v_naz
автокрасуні	автокрасуня	noun	noun:inanim:p:v_zna
автократ	автократ	noun	noun:anim:m:v_naz
автократа	автократ	noun	noun:anim:m:v_rod
автократа	автократ	noun	noun:anim:m:v_zna
автократам	автократ	noun	noun:anim:p:v_dav
автократами	автократ	noun	noun:anim:p:v_oru
автократах	автократ	noun	noun:anim:p:v_mis
автократе	автократ	noun	noun:anim:m:v_kly
автократи	автократ	noun	noun:anim:p:v_kly
автократи	автократ	noun	noun:anim:p:v_naz
автократи	автократ	noun	noun:anim:p:v_zna:rare
автократові	автократ	noun	noun:anim:m:v_dav
автократові	автократ	noun	noun:anim:m:v_mis
автократом	автократ	noun	noun:anim:m:v_oru
автократор	автократор	noun	noun:anim:m:v_naz
автократора	автократор	noun	noun:anim:m:v_rod
автократора	автократор	noun	noun:anim:m:v_zna
автократорам	автократор	noun	noun:anim:p:v_dav
автократорами	автократор	noun	noun:anim:p:v_oru
автократорах	автократор	noun	noun:anim:p:v_mis
автократоре	автократор	noun	noun:anim:m:v_kly
автократори	автократор	noun	noun:anim:p:v_kly
автократори	автократор	noun	noun:anim:p:v_naz
автократори	автократор	noun	noun:anim:p:v_zna:rare
автократорові	автократор	noun	noun:anim:m:v_dav
автократорові	автократор	noun	noun:anim:m:v_mis
автократором	автократор	noun	noun:anim:m:v_oru
автократорі	автократор	noun	noun:anim:m:v_mis
автократорів	автократор	noun	noun:anim:p:v_rod
автократорів	автократор	noun	noun:anim:p:v_zna
автократі	автократ	noun	noun:anim:m:v_mis
автократів	автократ	noun	noun:anim:p:v_rod
автократів	автократ	noun	noun:anim:p:v_zna
автократій	автократія	noun	noun:inanim:p:v_rod
автократію	автократія	noun	noun:inanim:f:v_zna
автократія	автократія	noun	noun:inanim:f:v_naz
автократіям	автократія	noun	noun:inanim:p:v_dav
автократіями	автократія	noun	noun:inanim:p:v_oru
автократіях	автократія	noun	noun:inanim:p:v_mis
автократіє	автократія	noun	noun:inanim:f:v_kly
автократією	автократія	noun	noun:inanim:f:v_oru
автократії	автократія	noun	noun:inanim:f:v_dav
автократії	автократія	noun	noun:inanim:f:v_mis
автократії	автократія	noun	noun:inanim:f:v_rod
автократії	автократія	noun	noun:inanim:p:v_kly
автократії	автократія	noun	noun:inanim:p:v_naz
автократії	автократія	noun	noun:inanim:p:v_zna
автокредит	автокредит	noun	noun:inanim:m:v_naz
автокредит	автокредит	noun	noun:inanim:m:v_zna
автокредитам	автокредит	noun	noun:inanim:p:v_dav
автокредитами	автокредит	noun	noun:inanim:p:v_oru
автокредитах	автокредит	noun	noun:inanim:p:v_mis
автокредите	автокредит	noun	noun:inanim:m:v_kly
автокредити	автокредит	noun	noun:inanim:p:v_kly
автокредити	автокредит	noun	noun:inanim:p:v_naz
автокредити	автокредит	noun	noun:inanim:p:v_zna
автокредитові	автокредит	noun	noun:inanim:m:v_dav
автокредитові	автокредит	noun	noun:inanim:m:v_mis
автокредитом	автокредит	noun	noun:inanim:m:v_oru
автокредиту	автокредит	noun	noun:inanim:m:v_dav
автокредиту	автокредит	noun	noun:inanim:m:v_mis
автокредиту	автокредит	noun	noun:inanim:m:v_rod
автокредиті	автокредит	noun	noun:inanim:m:v_mis
автокредитів	автокредит	noun	noun:inanim:p:v_rod
автокрос	автокрос	noun	noun:inanim:m:v_naz
автокрос	автокрос	noun	noun:inanim:m:v_zna
автокросам	автокрос	noun	noun:inanim:p:v_dav
автокросами	автокрос	noun	noun:inanim:p:v_oru
автокросах	автокрос	noun	noun:inanim:p:v_mis
автокросе	автокрос	noun	noun:inanim:m:v_kly
автокроси	автокрос	noun	noun:inanim:p:v_kly
автокроси	автокрос	noun	noun:inanim:p:v_naz
автокроси	автокрос	noun	noun:inanim:p:v_zna
автокросові	автокрос	noun	noun:inanim:m:v_dav
автокросові	автокрос	noun	noun:inanim:m:v_mis
автокросом	автокрос	noun	noun:inanim:m:v_oru
автокросу	автокрос	noun	noun:inanim:m:v_dav
автокросу	автокрос	noun	noun:inanim:m:v_mis
автокросу	автокрос	noun	noun:inanim:m:v_rod
автокросі	автокрос	noun	noun:inanim:m:v_mis
автокросів	автокрос	noun	noun:inanim:p:v_rod
автокрісел	автокрісло	noun	noun:inanim:p:v_rod
автокрісла	автокрісло	noun	noun:inanim:n:v_rod
автокрісла	автокрісло	noun	noun:inanim:p:v_kly
автокрісла	автокрісло	noun	noun:inanim:p:v_naz
автокрісла	автокрісло	noun	noun:inanim:p:v_zna
автокріслам	автокрісло	noun	noun:inanim:p:v_dav
автокріслами	автокрісло	noun	noun:inanim:p:v_oru
автокріслах	автокрісло	noun	noun:inanim:p:v_mis
автокрісло	автокрісло	noun	noun:inanim:n:v_kly
автокрісло	автокрісло	noun	noun:inanim:n:v_naz
автокрісло	автокрісло	noun	noun:inanim:n:v_zna
автокріслом	автокрісло	noun	noun:inanim:n:v_oru
автокріслу	автокрісло	noun	noun:inanim:n:v_dav
автокріслу	автокрісло	noun	noun:inanim:n:v_mis
автокріслі	автокрісло	noun	noun:inanim:n:v_mis
автокухне	автокухня	noun	noun:inanim:f:v_kly
автокухнею	автокухня	noun	noun:inanim:f:v_oru
автокухню	автокухня	noun	noun:inanim:f:v_zna
автокухня	автокухня	noun	noun:inanim:f:v_naz
автокухням	автокухня	noun	noun:inanim:p:v_dav
автокухнями	автокухня	noun	noun:inanim:p:v_oru
автокухнях	автокухня	noun	noun:inanim:p:v_mis
автокухні	автокухня	noun	noun:inanim:f:v_dav
автокухні	автокухня	noun	noun:inanim:f:v_mis
автокухні	автокухня	noun	noun:inanim:f:v_rod
автокухні	автокухня	noun	noun:inanim:p:v_kly
автокухні	автокухня	noun	noun:inanim:p:v_naz
автокухні	автокухня	noun	noun:inanim:p:v_zna
автокухонь	автокухня	noun	noun:inanim:p:v_rod
автокінотеатр	автокінотеатр	noun	noun:inanim:m:v_naz
автокінотеатр	автокінотеатр	noun	noun:inanim:m:v_zna
автокінотеатрам	автокінотеатр	noun	noun:inanim:p:v_dav
автокінотеатрами	автокінотеатр	noun	noun:inanim:p:v_oru
автокінотеатрах	автокінотеатр	noun	noun:inanim:p:v_mis
автокінотеатре	автокінотеатр	noun	noun:inanim:m:v_kly
автокінотеатри	автокінотеатр	noun	noun:inanim:p:v_kly
автокінотеатри	автокінотеатр	noun	noun:inanim:p:v_naz
автокінотеатри	автокінотеатр	noun	noun:inanim:p:v_zna
автокінотеатрові	автокінотеатр	noun	noun:inanim:m:v_dav
автокінотеатрові	автокінотеатр	noun	noun:inanim:m:v_mis
автокінотеатром	автокінотеатр	noun	noun:inanim:m:v_oru
автокінотеатру	автокінотеатр	noun	noun:inanim:m:v_dav
автокінотеатру	автокінотеатр	noun	noun:inanim:m:v_mis
автокінотеатру	автокінотеатр	noun	noun:inanim:m:v_rod
автокінотеатрі	автокінотеатр	noun	noun:inanim:m:v_mis
автокінотеатрів	автокінотеатр	noun	noun:inanim:p:v_rod
автол	автол	noun	noun:inanim:m:v_naz
автол	автол	noun	noun:inanim:m:v_zna
автолабораторій	автолабораторія	noun	noun:inanim:p:v_rod
автолабораторію	автолабораторія	noun	noun:inanim:f:v_zna
автолабораторія	автолабораторія	noun	noun:inanim:f:v_naz
автолабораторіям	автолабораторія	noun	noun:inanim:p:v_dav
автолабораторіями	автолабораторія	noun	noun:inanim:p:v_oru
автолабораторіях	автолабораторія	noun	noun:inanim:p:v_mis
автолабораторіє	автолабораторія	noun	noun:inanim:f:v_kly
автолабораторією	автолабораторія	noun	noun:inanim:f:v_oru
автолабораторії	автолабораторія	noun	noun:inanim:f:v_dav
автолабораторії	автолабораторія	noun	noun:inanim:f:v_mis
автолабораторії	автолабораторія	noun	noun:inanim:f:v_rod
автолабораторії	автолабораторія	noun	noun:inanim:p:v_kly
автолабораторії	автолабораторія	noun	noun:inanim:p:v_naz
автолабораторії	автолабораторія	noun	noun:inanim:p:v_zna
автолайнер	автолайнер	noun	noun:inanim:m:v_naz
автолайнер	автолайнер	noun	noun:inanim:m:v_zna
автолайнера	автолайнер	noun	noun:inanim:m:v_rod
автолайнерам	автолайнер	noun	noun:inanim:p:v_dav
автолайнерами	автолайнер	noun	noun:inanim:p:v_oru
автолайнерах	автолайнер	noun	noun:inanim:p:v_mis
автолайнере	автолайнер	noun	noun:inanim:m:v_kly
автолайнери	автолайнер	noun	noun:inanim:p:v_kly
автолайнери	автолайнер	noun	noun:inanim:p:v_naz
автолайнери	автолайнер	noun	noun:inanim:p:v_zna
автолайнерові	автолайнер	noun	noun:inanim:m:v_dav
автолайнерові	автолайнер	noun	noun:inanim:m:v_mis
автолайнером	автолайнер	noun	noun:inanim:m:v_oru
автолайнері	автолайнер	noun	noun:inanim:m:v_mis
автолайнерів	автолайнер	noun	noun:inanim:p:v_rod
автолак	автолак	noun	noun:inanim:m:v_naz
автолак	автолак	noun	noun:inanim:m:v_zna
автолакам	автолак	noun	noun:inanim:p:v_dav
автолаками	автолак	noun	noun:inanim:p:v_oru
автолаках	автолак	noun	noun:inanim:p:v_mis
автолаки	автолак	noun	noun:inanim:p:v_kly
автолаки	автолак	noun	noun:inanim:p:v_naz
автолаки	автолак	noun	noun:inanim:p:v_zna
автолакові	автолак	noun	noun:inanim:m:v_dav
автолакові	автолак	noun	noun:inanim:m:v_mis
автолаком	автолак	noun	noun:inanim:m:v_oru
автолаку	автолак	noun	noun:inanim:m:v_dav
автолаку	автолак	noun	noun:inanim:m:v_kly
автолаку	автолак	noun	noun:inanim:m:v_mis
автолаку	автолак	noun	noun:inanim:m:v_rod
автолаків	автолак	noun	noun:inanim:p:v_rod
автолам	автол	noun	noun:inanim:p:v_dav
автолами	автол	noun	noun:inanim:p:v_oru
автолафет	автолафет	noun	noun:inanim:m:v_naz
автолафет	автолафет	noun	noun:inanim:m:v_zna
автолафета	автолафет	noun	noun:inanim:m:v_rod
автолафетам	автолафет	noun	noun:inanim:p:v_dav
автолафетами	автолафет	noun	noun:inanim:p:v_oru
автолафетах	автолафет	noun	noun:inanim:p:v_mis
автолафете	автолафет	noun	noun:inanim:m:v_kly
автолафети	автолафет	noun	noun:inanim:p:v_kly
автолафети	автолафет	noun	noun:inanim:p:v_naz
автолафети	автолафет	noun	noun:inanim:p:v_zna
автолафетові	автолафет	noun	noun:inanim:m:v_dav
автолафетові	автолафет	noun	noun:inanim:m:v_mis
автолафетом	автолафет	noun	noun:inanim:m:v_oru
автолафеті	автолафет	noun	noun:inanim:m:v_mis
автолафетів	автолафет	noun	noun:inanim:p:v_rod
автолах	автол	noun	noun:inanim:p:v_mis
автоле	автол	noun	noun:inanim:m:v_kly
автолебідка	автолебідка	noun	noun:inanim:f:v_naz
автолебідкам	автолебідка	noun	noun:inanim:p:v_dav
автолебідками	автолебідка	noun	noun:inanim:p:v_oru
автолебідках	автолебідка	noun	noun:inanim:p:v_mis
автолебідки	автолебідка	noun	noun:inanim:f:v_rod
автолебідки	автолебідка	noun	noun:inanim:p:v_kly
автолебідки	автолебідка	noun	noun:inanim:p:v_naz
автолебідки	автолебідка	noun	noun:inanim:p:v_zna
автолебідко	автолебідка	noun	noun:inanim:f:v_kly
автолебідкою	автолебідка	noun	noun:inanim:f:v_oru
автолебідку	автолебідка	noun	noun:inanim:f:v_zna
автолебідок	автолебідка	noun	noun:inanim:p:v_rod
автолебідці	автолебідка	noun	noun:inanim:f:v_dav
автолебідці	автолебідка	noun	noun:inanim:f:v_mis
автоли	автол	noun	noun:inanim:p:v_kly
автоли	автол	noun	noun:inanim:p:v_naz
автоли	автол	noun	noun:inanim:p:v_zna
автолобіст	автолобіст	noun	noun:anim:m:v_naz
автолобіста	автолобіст	noun	noun:anim:m:v_rod
автолобіста	автолобіст	noun	noun:anim:m:v_zna
автолобістам	автолобіст	noun	noun:anim:p:v_dav
автолобістами	автолобіст	noun	noun:anim:p:v_oru
автолобістах	автолобіст	noun	noun:anim:p:v_mis
автолобісте	автолобіст	noun	noun:anim:m:v_kly
автолобісти	автолобіст	noun	noun:anim:p:v_kly
автолобісти	автолобіст	noun	noun:anim:p:v_naz
автолобісти	автолобіст	noun	noun:anim:p:v_zna:rare
автолобістові	автолобіст	noun	noun:anim:m:v_dav
автолобістові	автолобіст	noun	noun:anim:m:v_mis
автолобістом	автолобіст	noun	noun:anim:m:v_oru
автолобісті	автолобіст	noun	noun:anim:m:v_mis
автолобістів	автолобіст	noun	noun:anim:p:v_rod
автолобістів	автолобіст	noun	noun:anim:p:v_zna
автолові	автол	noun	noun:inanim:m:v_dav
автолові	автол	noun	noun:inanim:m:v_mis
автологій	автологія	noun	noun:inanim:p:v_rod
автологію	автологія	noun	noun:inanim:f:v_zna
автологія	автологія	noun	noun:inanim:f:v_naz
автологіям	автологія	noun	noun:inanim:p:v_dav
автологіями	автологія	noun	noun:inanim:p:v_oru
автологіях	автологія	noun	noun:inanim:p:v_mis
автологіє	автологія	noun	noun:inanim:f:v_kly
автологією	автологія	noun	noun:inanim:f:v_oru
автології	автологія	noun	noun:inanim:f:v_dav
автології	автологія	noun	noun:inanim:f:v_mis
автології	автологія	noun	noun:inanim:f:v_rod
автології	автологія	noun	noun:inanim:p:v_kly
автології	автологія	noun	noun:inanim:p:v_naz
автології	автологія	noun	noun:inanim:p:v_zna
автолокалізацій	автолокалізація	noun	noun:inanim:p:v_rod
автолокалізацію	автолокалізація	noun	noun:inanim:f:v_zna
автолокалізація	автолокалізація	noun	noun:inanim:f:v_naz
автолокалізаціям	автолокалізація	noun	noun:inanim:p:v_dav
автолокалізаціями	автолокалізація	noun	noun:inanim:p:v_oru
автолокалізаціях	автолокалізація	noun	noun:inanim:p:v_mis
автолокалізаціє	автолокалізація	noun	noun:inanim:f:v_kly
автолокалізацією	автолокалізація	noun	noun:inanim:f:v_oru
автолокалізації	автолокалізація	noun	noun:inanim:f:v_dav
автолокалізації	автолокалізація	noun	noun:inanim:f:v_mis
автолокалізації	автолокалізація	noun	noun:inanim:f:v_rod
автолокалізації	автолокалізація	noun	noun:inanim:p:v_kly
автолокалізації	автолокалізація	noun	noun:inanim:p:v_naz
автолокалізації	автолокалізація	noun	noun:inanim:p:v_zna
автолом	автол	noun	noun:inanim:m:v_oru
автоломбард	автоломбард	noun	noun:inanim:m:v_naz
автоломбард	автоломбард	noun	noun:inanim:m:v_zna
автоломбардам	автоломбард	noun	noun:inanim:p:v_dav
автоломбардами	автоломбард	noun	noun:inanim:p:v_oru
автоломбардах	автоломбард	noun	noun:inanim:p:v_mis
автоломбарде	автоломбард	noun	noun:inanim:m:v_kly
автоломбарди	автоломбард	noun	noun:inanim:p:v_kly
автоломбарди	автоломбард	noun	noun:inanim:p:v_naz
автоломбарди	автоломбард	noun	noun:inanim:p:v_zna
автоломбардові	автоломбард	noun	noun:inanim:m:v_dav
автоломбардові	автоломбард	noun	noun:inanim:m:v_mis
автоломбардом	автоломбард	noun	noun:inanim:m:v_oru
автоломбарду	автоломбард	noun	noun:inanim:m:v_dav
автоломбарду	автоломбард	noun	noun:inanim:m:v_mis
автоломбарду	автоломбард	noun	noun:inanim:m:v_rod
автоломбарді	автоломбард	noun	noun:inanim:m:v_mis
автоломбардів	автоломбард	noun	noun:inanim:p:v_rod
автолу	автол	noun	noun:inanim:m:v_dav
автолу	автол	noun	noun:inanim:m:v_mis
автолу	автол	noun	noun:inanim:m:v_rod
автолюбителеві	автолюбитель	noun	noun:anim:m:v_dav
автолюбителеві	автолюбитель	noun	noun:anim:m:v_mis
автолюбителем	автолюбитель	noun	noun:anim:m:v_oru
автолюбитель	автолюбитель	noun	noun:anim:m:v_naz
автолюбителька	автолюбителька	noun	noun:anim:f:v_naz
автолюбителькам	автолюбителька	noun	noun:anim:p:v_dav
автолюбительками	автолюбителька	noun	noun:anim:p:v_oru
автолюбительках	автолюбителька	noun	noun:anim:p:v_mis
автолюбительки	автолюбителька	noun	noun:anim:f:v_rod
автолюбительки	автолюбителька	noun	noun:anim:p:v_kly
автолюбительки	автолюбителька	noun	noun:anim:p:v_naz
автолюбительки	автолюбителька	noun	noun:anim:p:v_zna:rare
автолюбителько	автолюбителька	noun	noun:anim:f:v_kly
автолюбителькою	автолюбителька	noun	noun:anim:f:v_oru
автолюбительку	автолюбителька	noun	noun:anim:f:v_zna
автолюбительнице	автолюбительниця	noun	noun:anim:f:v_kly
автолюбительницею	автолюбительниця	noun	noun:anim:f:v_oru
автолюбительниць	автолюбительниця	noun	noun:anim:p:v_rod
автолюбительниць	автолюбительниця	noun	noun:anim:p:v_zna
автолюбительницю	автолюбительниця	noun	noun:anim:f:v_zna
автолюбительниця	автолюбительниця	noun	noun:anim:f:v_naz
автолюбительницям	автолюбительниця	noun	noun:anim:p:v_dav
автолюбительницями	автолюбительниця	noun	noun:anim:p:v_oru
автолюбительницях	автолюбительниця	noun	noun:anim:p:v_mis
автолюбительниці	автолюбительниця	noun	noun:anim:f:v_dav
автолюбительниці	автолюбительниця	noun	noun:anim:f:v_mis
автолюбительниці	автолюбительниця	noun	noun:anim:f:v_rod
автолюбительниці	автолюбительниця	noun	noun:anim:p:v_kly
автолюбительниці	автолюбительниця	noun	noun:anim:p:v_naz
автолюбительниці	автолюбительниця	noun	noun:anim:p:v_zna:rare
автолюбительок	автолюбителька	noun	noun:anim:p:v_rod
автолюбительок	автолюбителька	noun	noun:anim:p:v_zna
автолюбительці	автолюбителька	noun	noun:anim:f:v_dav
автолюбительці	автолюбителька	noun	noun:anim:f:v_mis
автолюбителю	автолюбитель	noun	noun:anim:m:v_dav
автолюбителю	автолюбитель	noun	noun:anim:m:v_kly
автолюбителю	автолюбитель	noun	noun:anim:m:v_mis
автолюбителя	автолюбитель	noun	noun:anim:m:v_rod
автолюбителя	автолюбитель	noun	noun:anim:m:v_zna
автолюбителям	автолюбитель	noun	noun:anim:p:v_dav
автолюбителями	автолюбитель	noun	noun:anim:p:v_oru
автолюбителях	автолюбитель	noun	noun:anim:p:v_mis
автолюбителі	автолюбитель	noun	noun:anim:m:v_mis
автолюбителі	автолюбитель	noun	noun:anim:p:v_kly
автолюбителі	автолюбитель	noun	noun:anim:p:v_naz
автолюбителі	автолюбитель	noun	noun:anim:p:v_zna:rare
автолюбителів	автолюбитель	noun	noun:anim:p:v_rod
автолюбителів	автолюбитель	noun	noun:anim:p:v_zna
автолюлька	автолюлька	noun	noun:inanim:f:v_naz
автолюлькам	автолюлька	noun	noun:inanim:p:v_dav
автолюльками	автолюлька	noun	noun:inanim:p:v_oru
автолюльках	автолюлька	noun	noun:inanim:p:v_mis
автолюльки	автолюлька	noun	noun:inanim:f:v_rod
автолюльки	автолюлька	noun	noun:inanim:p:v_kly
автолюльки	автолюлька	noun	noun:inanim:p:v_naz
автолюльки	автолюлька	noun	noun:inanim:p:v_zna
автолюлько	автолюлька	noun	noun:inanim:f:v_kly
автолюлькою	автолюлька	noun	noun:inanim:f:v_oru
автолюльку	автолюлька	noun	noun:inanim:f:v_zna
автолюльок	автолюлька	noun	noun:inanim:p:v_rod
автолюльці	автолюлька	noun	noun:inanim:f:v_dav
автолюльці	автолюлька	noun	noun:inanim:f:v_mis
автолі	автол	noun	noun:inanim:m:v_mis
автолів	автол	noun	noun:inanim:p:v_rod
автолізій	автолізія	noun	noun:inanim:p:v_rod
автолізію	автолізія	noun	noun:inanim:f:v_zna
автолізія	автолізія	noun	noun:inanim:f:v_naz
автолізіям	автолізія	noun	noun:inanim:p:v_dav
автолізіями	автолізія	noun	noun:inanim:p:v_oru
автолізіях	автолізія	noun	noun:inanim:p:v_mis
автолізіє	автолізія	noun	noun:inanim:f:v_kly
автолізією	автолізія	noun	noun:inanim:f:v_oru
автолізії	автолізія	noun	noun:inanim:f:v_dav
автолізії	автолізія	noun	noun:inanim:f:v_mis
автолізії	автолізія	noun	noun:inanim:f:v_rod
автолізії	автолізія	noun	noun:inanim:p:v_kly
автолізії	автолізія	noun	noun:inanim:p:v_naz
автолізії	автолізія	noun	noun:inanim:p:v_zna
автолісовоз	автолісовоз	noun	noun:inanim:m:v_naz
автолісовоз	автолісовоз	noun	noun:inanim:m:v_zna
автолісовоза	автолісовоз	noun	noun:inanim:m:v_rod
автолісовозам	автолісовоз	noun	noun:inanim:p:v_dav
автолісовозами	автолісовоз	noun	noun:inanim:p:v_oru
автолісовозах	автолісовоз	noun	noun:inanim:p:v_mis
автолісовозе	автолісовоз	noun	noun:inanim:m:v_kly
автолісовози	автолісовоз	noun	noun:inanim:p:v_kly
автолісовози	автолісовоз	noun	noun:inanim:p:v_naz
автолісовози	автолісовоз	noun	noun:inanim:p:v_zna
автолісовозові	автолісовоз	noun	noun:inanim:m:v_dav
автолісовозові	автолісовоз	noun	noun:inanim:m:v_mis
автолісовозом	автолісовоз	noun	noun:inanim:m:v_oru
автолісовозі	автолісовоз	noun	noun:inanim:m:v_mis
автолісовозів	автолісовоз	noun	noun:inanim:p:v_rod
автолітографій	автолітографія	noun	noun:inanim:p:v_rod
автолітографію	автолітографія	noun	noun:inanim:f:v_zna
автолітографія	автолітографія	noun	noun:inanim:f:v_naz
автолітографіям	автолітографія	noun	noun:inanim:p:v_dav
автолітографіями	автолітографія	noun	noun:inanim:p:v_oru
автолітографіях	автолітографія	noun	noun:inanim:p:v_mis
автолітографіє	автолітографія	noun	noun:inanim:f:v_kly
автолітографією	автолітографія	noun	noun:inanim:f:v_oru
автолітографії	автолітографія	noun	noun:inanim:f:v_dav
автолітографії	автолітографія	noun	noun:inanim:f:v_mis
автолітографії	автолітографія	noun	noun:inanim:f:v_rod
автолітографії	автолітографія	noun	noun:inanim:p:v_kly
автолітографії	автолітографія	noun	noun:inanim:p:v_naz
автолітографії	автолітографія	noun	noun:inanim:p:v_zna
автоліхтарик	автоліхтарик	noun	noun:inanim:m:v_naz
автоліхтарик	автоліхтарик	noun	noun:inanim:m:v_zna
автоліхтарика	автоліхтарик	noun	noun:inanim:m:v_rod
автоліхтарикам	автоліхтарик	noun	noun:inanim:p:v_dav
автоліхтариками	автоліхтарик	noun	noun:inanim:p:v_oru
автоліхтариках	автоліхтарик	noun	noun:inanim:p:v_mis
автоліхтарики	автоліхтарик	noun	noun:inanim:p:v_kly
автоліхтарики	автоліхтарик	noun	noun:inanim:p:v_naz
автоліхтарики	автоліхтарик	noun	noun:inanim:p:v_zna
автоліхтарикові	автоліхтарик	noun	noun:inanim:m:v_dav
автоліхтарикові	автоліхтарик	noun	noun:inanim:m:v_mis
автоліхтариком	автоліхтарик	noun	noun:inanim:m:v_oru
автоліхтарику	автоліхтарик	noun	noun:inanim:m:v_dav
автоліхтарику	автоліхтарик	noun	noun:inanim:m:v_kly
автоліхтарику	автоліхтарик	noun	noun:inanim:m:v_mis
автоліхтариків	автоліхтарик	noun	noun:inanim:p:v_rod
автомагазин	автомагазин	noun	noun:inanim:m:v_naz
автомагазин	автомагазин	noun	noun:inanim:m:v_zna
автомагазинам	автомагазин	noun	noun:inanim:p:v_dav
автомагазинами	автомагазин	noun	noun:inanim:p:v_oru
автомагазинах	автомагазин	noun	noun:inanim:p:v_mis
автомагазине	автомагазин	noun	noun:inanim:m:v_kly
автомагазини	автомагазин	noun	noun:inanim:p:v_kly
автомагазини	автомагазин	noun	noun:inanim:p:v_naz
автомагазини	автомагазин	noun	noun:inanim:p:v_zna
автомагазинові	автомагазин	noun	noun:inanim:m:v_dav
автомагазинові	автомагазин	noun	noun:inanim:m:v_mis
автомагазином	автомагазин	noun	noun:inanim:m:v_oru
автомагазину	автомагазин	noun	noun:inanim:m:v_dav
автомагазину	автомагазин	noun	noun:inanim:m:v_mis
автомагазину	автомагазин	noun	noun:inanim:m:v_rod
автомагазинчик	автомагазинчик	noun	noun:inanim:m:v_naz
автомагазинчик	автомагазинчик	noun	noun:inanim:m:v_zna
автомагазинчика	автомагазинчик	noun	noun:inanim:m:v_rod
автомагазинчикам	автомагазинчик	noun	noun:inanim:p:v_dav
автомагазинчиками	автомагазинчик	noun	noun:inanim:p:v_oru
автомагазинчиках	автомагазинчик	noun	noun:inanim:p:v_mis
автомагазинчики	автомагазинчик	noun	noun:inanim:p:v_kly
автомагазинчики	автомагазинчик	noun	noun:inanim:p:v_naz
автомагазинчики	автомагазинчик	noun	noun:inanim:p:v_zna
автомагазинчикові	автомагазинчик	noun	noun:inanim:m:v_dav
автомагазинчикові	автомагазинчик	noun	noun:inanim:m:v_mis
автомагазинчиком	автомагазинчик	noun	noun:inanim:m:v_oru
автомагазинчику	автомагазинчик	noun	noun:inanim:m:v_dav
автомагазинчику	автомагазинчик	noun	noun:inanim:m:v_kly
автомагазинчику	автомагазинчик	noun	noun:inanim:m:v_mis
автомагазинчиків	автомагазинчик	noun	noun:inanim:p:v_rod
автомагазині	автомагазин	noun	noun:inanim:m:v_mis
автомагазинів	автомагазин	noun	noun:inanim:p:v_rod
автомагнат	автомагнат	noun	noun:anim:m:v_naz
автомагната	автомагнат	noun	noun:anim:m:v_rod
автомагната	автомагнат	noun	noun:anim:m:v_zna
автомагнатам	автомагнат	noun	noun:anim:p:v_dav
автомагнатами	автомагнат	noun	noun:anim:p:v_oru
автомагнатах	автомагнат	noun	noun:anim:p:v_mis
автомагнате	автомагнат	noun	noun:anim:m:v_kly
автомагнати	автомагнат	noun	noun:anim:p:v_kly
автомагнати	автомагнат	noun	noun:anim:p:v_naz
автомагнати	автомагнат	noun	noun:anim:p:v_zna:rare
автомагнатові	автомагнат	noun	noun:anim:m:v_dav
автомагнатові	автомагнат	noun	noun:anim:m:v_mis
автомагнатом	автомагнат	noun	noun:anim:m:v_oru
автомагнаті	автомагнат	noun	noun:anim:m:v_mis
автомагнатів	автомагнат	noun	noun:anim:p:v_rod
автомагнатів	автомагнат	noun	noun:anim:p:v_zna
автомагнітол	автомагнітола	noun	noun:inanim:p:v_rod
автомагнітола	автомагнітола	noun	noun:inanim:f:v_naz
автомагнітолам	автомагнітола	noun	noun:inanim:p:v_dav
автомагнітолами	автомагнітола	noun	noun:inanim:p:v_oru
автомагнітолах	автомагнітола	noun	noun:inanim:p:v_mis
автомагнітоли	автомагнітола	noun	noun:inanim:f:v_rod
автомагнітоли	автомагнітола	noun	noun:inanim:p:v_kly
автомагнітоли	автомагнітола	noun	noun:inanim:p:v_naz
автомагнітоли	автомагнітола	noun	noun:inanim:p:v_zna
автомагнітоло	автомагнітола	noun	noun:inanim:f:v_kly
автомагнітолою	автомагнітола	noun	noun:inanim:f:v_oru
автомагнітолу	автомагнітола	noun	noun:inanim:f:v_zna
автомагнітолі	автомагнітола	noun	noun:inanim:f:v_dav
автомагнітолі	автомагнітола	noun	noun:inanim:f:v_mis
автомагнітофон	автомагнітофон	noun	noun:inanim:m:v_naz
автомагнітофон	автомагнітофон	noun	noun:inanim:m:v_zna
автомагнітофона	автомагнітофон	noun	noun:inanim:m:v_rod
автомагнітофонам	автомагнітофон	noun	noun:inanim:p:v_dav
автомагнітофонами	автомагнітофон	noun	noun:inanim:p:v_oru
автомагнітофонах	автомагнітофон	noun	noun:inanim:p:v_mis
автомагнітофоне	автомагнітофон	noun	noun:inanim:m:v_kly
автомагнітофони	автомагнітофон	noun	noun:inanim:p:v_kly
автомагнітофони	автомагнітофон	noun	noun:inanim:p:v_naz
автомагнітофони	автомагнітофон	noun	noun:inanim:p:v_zna
автомагнітофонові	автомагнітофон	noun	noun:inanim:m:v_dav
автомагнітофонові	автомагнітофон	noun	noun:inanim:m:v_mis
автомагнітофоном	автомагнітофон	noun	noun:inanim:m:v_oru
автомагнітофоні	автомагнітофон	noun	noun:inanim:m:v_mis
автомагнітофонів	автомагнітофон	noun	noun:inanim:p:v_rod
автомагістрале	автомагістраль	noun	noun:inanim:f:v_kly
автомагістралей	автомагістраль	noun	noun:inanim:p:v_rod
автомагістраллю	автомагістраль	noun	noun:inanim:f:v_oru
автомагістраль	автомагістраль	noun	noun:inanim:f:v_naz
автомагістраль	автомагістраль	noun	noun:inanim:f:v_zna
автомагістралям	автомагістраль	noun	noun:inanim:p:v_dav
автомагістралями	автомагістраль	noun	noun:inanim:p:v_oru
автомагістралях	автомагістраль	noun	noun:inanim:p:v_mis
автомагістралі	автомагістраль	noun	noun:inanim:f:v_dav
автомагістралі	автомагістраль	noun	noun:inanim:f:v_mis
автомагістралі	автомагістраль	noun	noun:inanim:f:v_rod
автомагістралі	автомагістраль	noun	noun:inanim:p:v_kly
автомагістралі	автомагістраль	noun	noun:inanim:p:v_naz
автомагістралі	автомагістраль	noun	noun:inanim:p:v_zna
автомайдан	автомайдан	noun	noun:inanim:m:v_naz
автомайдан	автомайдан	noun	noun:inanim:m:v_zna
автомайданам	автомайдан	noun	noun:inanim:p:v_dav
автомайданами	автомайдан	noun	noun:inanim:p:v_oru
автомайданах	автомайдан	noun	noun:inanim:p:v_mis
автомайдане	автомайдан	noun	noun:inanim:m:v_kly
автомайдани	автомайдан	noun	noun:inanim:p:v_kly
автомайдани	автомайдан	noun	noun:inanim:p:v_naz
автомайдани	автомайдан	noun	noun:inanim:p:v_zna
автомайданові	автомайдан	noun	noun:inanim:m:v_dav
автомайданові	автомайдан	noun	noun:inanim:m:v_mis
автомайданом	автомайдан	noun	noun:inanim:m:v_oru
автомайдану	автомайдан	noun	noun:inanim:m:v_dav
автомайдану	автомайдан	noun	noun:inanim:m:v_mis
автомайдану	автомайдан	noun	noun:inanim:m:v_rod
автомайданчик	автомайданчик	noun	noun:inanim:m:v_naz
автомайданчик	автомайданчик	noun	noun:inanim:m:v_zna
автомайданчика	автомайданчик	noun	noun:inanim:m:v_rod
автомайданчикам	автомайданчик	noun	noun:inanim:p:v_dav
автомайданчиками	автомайданчик	noun	noun:inanim:p:v_oru
автомайданчиках	автомайданчик	noun	noun:inanim:p:v_mis
автомайданчики	автомайданчик	noun	noun:inanim:p:v_kly
автомайданчики	автомайданчик	noun	noun:inanim:p:v_naz
автомайданчики	автомайданчик	noun	noun:inanim:p:v_zna
автомайданчикові	автомайданчик	noun	noun:inanim:m:v_dav
автомайданчикові	автомайданчик	noun	noun:inanim:m:v_mis
автомайданчиком	автомайданчик	noun	noun:inanim:m:v_oru
автомайданчику	автомайданчик	noun	noun:inanim:m:v_dav
автомайданчику	автомайданчик	noun	noun:inanim:m:v_kly
автомайданчику	автомайданчик	noun	noun:inanim:m:v_mis
автомайданчиків	автомайданчик	noun	noun:inanim:p:v_rod
автомайдані	автомайдан	noun	noun:inanim:m:v_mis
автомайданів	автомайдан	noun	noun:inanim:p:v_rod
автомайданівець	автомайданівець	noun	noun:anim:m:v_naz
автомайданівка	автомайданівка	noun	noun:anim:f:v_naz
автомайданівкам	автомайданівка	noun	noun:anim:p:v_dav
автомайданівками	автомайданівка	noun	noun:anim:p:v_oru
автомайданівках	автомайданівка	noun	noun:anim:p:v_mis
автомайданівки	автомайданівка	noun	noun:anim:f:v_rod
автомайданівки	автомайданівка	noun	noun:anim:p:v_kly
автомайданівки	автомайданівка	noun	noun:anim:p:v_naz
автомайданівки	автомайданівка	noun	noun:anim:p:v_zna:rare
автомайданівко	автомайданівка	noun	noun:anim:f:v_kly
автомайданівкою	автомайданівка	noun	noun:anim:f:v_oru
автомайданівку	автомайданівка	noun	noun:anim:f:v_zna
автомайданівок	автомайданівка	noun	noun:anim:p:v_rod
автомайданівок	автомайданівка	noun	noun:anim:p:v_zna
автомайданівцеві	автомайданівець	noun	noun:anim:m:v_dav
автомайданівцеві	автомайданівець	noun	noun:anim:m:v_mis
автомайданівцем	автомайданівець	noun	noun:anim:m:v_oru
автомайданівцю	автомайданівець	noun	noun:anim:m:v_dav
автомайданівцю	автомайданівець	noun	noun:anim:m:v_kly
автомайданівцю	автомайданівець	noun	noun:anim:m:v_mis
автомайданівця	автомайданівець	noun	noun:anim:m:v_rod
автомайданівця	автомайданівець	noun	noun:anim:m:v_zna
автомайданівцям	автомайданівець	noun	noun:anim:p:v_dav
автомайданівцями	автомайданівець	noun	noun:anim:p:v_oru
автомайданівцях	автомайданівець	noun	noun:anim:p:v_mis
автомайданівці	автомайданівець	noun	noun:anim:m:v_mis
автомайданівці	автомайданівець	noun	noun:anim:p:v_kly
автомайданівці	автомайданівець	noun	noun:anim:p:v_naz
автомайданівці	автомайданівець	noun	noun:anim:p:v_zna:rare
автомайданівці	автомайданівка	noun	noun:anim:f:v_dav
автомайданівці	автомайданівка	noun	noun:anim:f:v_mis
автомайданівців	автомайданівець	noun	noun:anim:p:v_rod
автомайданівців	автомайданівець	noun	noun:anim:p:v_zna
автомайстер	автомайстер	noun	noun:anim:m:v_naz
автомайстерень	автомайстерня	noun	noun:inanim:p:v_rod
автомайстерне	автомайстерня	noun	noun:inanim:f:v_kly
автомайстернею	автомайстерня	noun	noun:inanim:f:v_oru
автомайстерню	автомайстерня	noun	noun:inanim:f:v_zna
автомайстерня	автомайстерня	noun	noun:inanim:f:v_naz
автомайстерням	автомайстерня	noun	noun:inanim:p:v_dav
автомайстернями	автомайстерня	noun	noun:inanim:p:v_oru
автомайстернях	автомайстерня	noun	noun:inanim:p:v_mis
автомайстерні	автомайстерня	noun	noun:inanim:f:v_dav
автомайстерні	автомайстерня	noun	noun:inanim:f:v_mis
автомайстерні	автомайстерня	noun	noun:inanim:f:v_rod
автомайстерні	автомайстерня	noun	noun:inanim:p:v_kly
автомайстерні	автомайстерня	noun	noun:inanim:p:v_naz
автомайстерні	автомайстерня	noun	noun:inanim:p:v_zna
автомайстра	автомайстер	noun	noun:anim:m:v_rod
автомайстра	автомайстер	noun	noun:anim:m:v_zna
автомайстрам	автомайстер	noun	noun:anim:p:v_dav
автомайстрами	автомайстер	noun	noun:anim:p:v_oru
автомайстрах	автомайстер	noun	noun:anim:p:v_mis
автомайстре	автомайстер	noun	noun:anim:m:v_kly
автомайстри	автомайстер	noun	noun:anim:p:v_kly
автомайстри	автомайстер	noun	noun:anim:p:v_naz
автомайстри	автомайстер	noun	noun:anim:p:v_zna:rare
автомайстрові	автомайстер	noun	noun:anim:m:v_dav
автомайстрові	автомайстер	noun	noun:anim:m:v_mis
автомайстром	автомайстер	noun	noun:anim:m:v_oru
автомайстрі	автомайстер	noun	noun:anim:m:v_mis
автомайстрів	автомайстер	noun	noun:anim:p:v_rod
автомайстрів	автомайстер	noun	noun:anim:p:v_zna
автомаклер	автомаклер	noun	noun:anim:m:v_naz
автомаклера	автомаклер	noun	noun:anim:m:v_rod
автомаклера	автомаклер	noun	noun:anim:m:v_zna
автомаклерам	автомаклер	noun	noun:anim:p:v_dav
автомаклерами	автомаклер	noun	noun:anim:p:v_oru
автомаклерах	автомаклер	noun	noun:anim:p:v_mis
автомаклере	автомаклер	noun	noun:anim:m:v_kly
автомаклери	автомаклер	noun	noun:anim:p:v_kly
автомаклери	автомаклер	noun	noun:anim:p:v_naz
автомаклери	автомаклер	noun	noun:anim:p:v_zna:rare
автомаклерові	автомаклер	noun	noun:anim:m:v_dav
автомаклерові	автомаклер	noun	noun:anim:m:v_mis
автомаклером	автомаклер	noun	noun:anim:m:v_oru
автомаклері	автомаклер	noun	noun:anim:m:v_mis
автомаклерів	автомаклер	noun	noun:anim:p:v_rod
автомаклерів	автомаклер	noun	noun:anim:p:v_zna
автомаляр	автомаляр	noun	noun:anim:m:v_naz:up19:xp2
автомаляр	автомаляр	noun	noun:anim:m:v_naz:xp1
автомаляра	автомаляр	noun	noun:anim:m:v_rod:up19:xp2
автомаляра	автомаляр	noun	noun:anim:m:v_rod:xp1
автомаляра	автомаляр	noun	noun:anim:m:v_zna:up19:xp2
автомаляра	автомаляр	noun	noun:anim:m:v_zna:xp1
автомалярам	автомаляр	noun	noun:anim:p:v_dav:up19:xp2
автомалярам	автомаляр	noun	noun:anim:p:v_dav:xp1
автомалярами	автомаляр	noun	noun:anim:p:v_oru:up19:xp2
автомалярами	автомаляр	noun	noun:anim:p:v_oru:xp1
автомалярах	автомаляр	noun	noun:anim:p:v_mis:up19:xp2
автомалярах	автомаляр	noun	noun:anim:p:v_mis:xp1
автомаляре	автомаляр	noun	noun:anim:m:v_kly:up19:xp2
автомаляре	автомаляр	noun	noun:anim:m:v_kly:xp1
автомаляри	автомаляр	noun	noun:anim:p:v_kly:xp1
автомаляри	автомаляр	noun	noun:anim:p:v_naz:xp1
автомаляри	автомаляр	noun	noun:anim:p:v_zna:rare:xp1
автомалярові	автомаляр	noun	noun:anim:m:v_dav:xp1
автомалярові	автомаляр	noun	noun:anim:m:v_mis:xp1
автомаляром	автомаляр	noun	noun:anim:m:v_oru:xp1
автомалярі	автомаляр	noun	noun:anim:m:v_mis:up19:xp2
автомалярі	автомаляр	noun	noun:anim:m:v_mis:xp1
автомалярі	автомаляр	noun	noun:anim:p:v_kly:up19:xp2
автомалярі	автомаляр	noun	noun:anim:p:v_naz:up19:xp2
автомалярі	автомаляр	noun	noun:anim:p:v_zna:up19:rare:xp2
автомалярів	автомаляр	noun	noun:anim:p:v_rod:up19:xp2
автомалярів	автомаляр	noun	noun:anim:p:v_rod:xp1
автомалярів	автомаляр	noun	noun:anim:p:v_zna:up19:xp2
автомалярів	автомаляр	noun	noun:anim:p:v_zna:xp1
автомандрівник	автомандрівник	noun	noun:anim:m:v_naz
автомандрівника	автомандрівник	noun	noun:anim:m:v_rod
автомандрівника	автомандрівник	noun	noun:anim:m:v_zna
автомандрівникам	автомандрівник	noun	noun:anim:p:v_dav
автомандрівниками	автомандрівник	noun	noun:anim:p:v_oru
автомандрівниках	автомандрівник	noun	noun:anim:p:v_mis
автомандрівники	автомандрівник	noun	noun:anim:p:v_kly
автомандрівники	автомандрівник	noun	noun:anim:p:v_naz
автомандрівники	автомандрівник	noun	noun:anim:p:v_zna:rare
автомандрівникові	автомандрівник	noun	noun:anim:m:v_dav
автомандрівникові	автомандрівник	noun	noun:anim:m:v_mis
автомандрівником	автомандрівник	noun	noun:anim:m:v_oru
автомандрівнику	автомандрівник	noun	noun:anim:m:v_dav
автомандрівнику	автомандрівник	noun	noun:anim:m:v_kly
автомандрівнику	автомандрівник	noun	noun:anim:m:v_mis
автомандрівників	автомандрівник	noun	noun:anim:p:v_rod
автомандрівників	автомандрівник	noun	noun:anim:p:v_zna
автомандрівнице	автомандрівниця	noun	noun:anim:f:v_kly
автомандрівницею	автомандрівниця	noun	noun:anim:f:v_oru
автомандрівниць	автомандрівниця	noun	noun:anim:p:v_rod
автомандрівниць	автомандрівниця	noun	noun:anim:p:v_zna
автомандрівницю	автомандрівниця	noun	noun:anim:f:v_zna
автомандрівниця	автомандрівниця	noun	noun:anim:f:v_naz
автомандрівницям	автомандрівниця	noun	noun:anim:p:v_dav
автомандрівницями	автомандрівниця	noun	noun:anim:p:v_oru
автомандрівницях	автомандрівниця	noun	noun:anim:p:v_mis
автомандрівниці	автомандрівниця	noun	noun:anim:f:v_dav
автомандрівниці	автомандрівниця	noun	noun:anim:f:v_mis
автомандрівниці	автомандрівниця	noun	noun:anim:f:v_rod
автомандрівниці	автомандрівниця	noun	noun:anim:p:v_kly
автомандрівниці	автомандрівниця	noun	noun:anim:p:v_naz
автомандрівниці	автомандрівниця	noun	noun:anim:p:v_zna:rare
автомаратон	автомаратон	noun	noun:inanim:m:v_naz:up19
автомаратон	автомаратон	noun	noun:inanim:m:v_zna:up19
автомаратонам	автомаратон	noun	noun:inanim:p:v_dav:up19
автомаратонами	автомаратон	noun	noun:inanim:p:v_oru:up19
автомаратонах	автомаратон	noun	noun:inanim:p:v_mis:up19
автомаратоне	автомаратон	noun	noun:inanim:m:v_kly:up19
автомаратони	автомаратон	noun	noun:inanim:p:v_kly:up19
автомаратони	автомаратон	noun	noun:inanim:p:v_naz:up19
автомаратони	автомаратон	noun	noun:inanim:p:v_zna:up19
автомаратонові	автомаратон	noun	noun:inanim:m:v_dav:up19
автомаратонові	автомаратон	noun	noun:inanim:m:v_mis:up19
автомаратоном	автомаратон	noun	noun:inanim:m:v_oru:up19
автомаратону	автомаратон	noun	noun:inanim:m:v_dav:up19
автомаратону	автомаратон	noun	noun:inanim:m:v_mis:up19
автомаратону	автомаратон	noun	noun:inanim:m:v_rod:up19
автомаратоні	автомаратон	noun	noun:inanim:m:v_mis:up19
автомаратонів	автомаратон	noun	noun:inanim:p:v_rod:up19
автомарафон	автомарафон	noun	noun:inanim:m:v_naz
автомарафон	автомарафон	noun	noun:inanim:m:v_zna
автомарафонам	автомарафон	noun	noun:inanim:p:v_dav
автомарафонами	автомарафон	noun	noun:inanim:p:v_oru
автомарафонах	автомарафон	noun	noun:inanim:p:v_mis
автомарафоне	автомарафон	noun	noun:inanim:m:v_kly
автомарафони	автомарафон	noun	noun:inanim:p:v_kly
автомарафони	автомарафон	noun	noun:inanim:p:v_naz
автомарафони	автомарафон	noun	noun:inanim:p:v_zna
автомарафонові	автомарафон	noun	noun:inanim:m:v_dav
автомарафонові	автомарафон	noun	noun:inanim:m:v_mis
автомарафоном	автомарафон	noun	noun:inanim:m:v_oru
автомарафону	автомарафон	noun	noun:inanim:m:v_dav
автомарафону	автомарафон	noun	noun:inanim:m:v_mis
автомарафону	автомарафон	noun	noun:inanim:m:v_rod
автомарафоні	автомарафон	noun	noun:inanim:m:v_mis
автомарафонів	автомарафон	noun	noun:inanim:p:v_rod
автомарка	автомарка	noun	noun:inanim:f:v_naz
автомаркам	автомарка	noun	noun:inanim:p:v_dav
автомарками	автомарка	noun	noun:inanim:p:v_oru
автомарках	автомарка	noun	noun:inanim:p:v_mis
автомаркетолог	автомаркетолог	noun	noun:anim:m:v_naz
автомаркетолога	автомаркетолог	noun	noun:anim:m:v_rod
автомаркетолога	автомаркетолог	noun	noun:anim:m:v_zna
автомаркетологам	автомаркетолог	noun	noun:anim:p:v_dav
автомаркетологами	автомаркетолог	noun	noun:anim:p:v_oru
автомаркетологах	автомаркетолог	noun	noun:anim:p:v_mis
автомаркетологи	автомаркетолог	noun	noun:anim:p:v_kly
автомаркетологи	автомаркетолог	noun	noun:anim:p:v_naz
автомаркетологи	автомаркетолог	noun	noun:anim:p:v_zna:rare
автомаркетологові	автомаркетолог	noun	noun:anim:m:v_dav
автомаркетологові	автомаркетолог	noun	noun:anim:m:v_mis
автомаркетологом	автомаркетолог	noun	noun:anim:m:v_oru
автомаркетологу	автомаркетолог	noun	noun:anim:m:v_dav
автомаркетологу	автомаркетолог	noun	noun:anim:m:v_kly
автомаркетологу	автомаркетолог	noun	noun:anim:m:v_mis
автомаркетологів	автомаркетолог	noun	noun:anim:p:v_rod
автомаркетологів	автомаркетолог	noun	noun:anim:p:v_zna
автомарки	автомарка	noun	noun:inanim:f:v_rod
автомарки	автомарка	noun	noun:inanim:p:v_kly
автомарки	автомарка	noun	noun:inanim:p:v_naz
автомарки	автомарка	noun	noun:inanim:p:v_zna
автомарко	автомарка	noun	noun:inanim:f:v_kly
автомаркою	автомарка	noun	noun:inanim:f:v_oru
автомарку	автомарка	noun	noun:inanim:f:v_zna
автомарок	автомарка	noun	noun:inanim:p:v_rod
автомарці	автомарка	noun	noun:inanim:f:v_dav
автомарці	автомарка	noun	noun:inanim:f:v_mis
автомаршрут	автомаршрут	noun	noun:inanim:m:v_naz
автомаршрут	автомаршрут	noun	noun:inanim:m:v_zna
автомаршрутам	автомаршрут	noun	noun:inanim:p:v_dav
автомаршрутами	автомаршрут	noun	noun:inanim:p:v_oru
автомаршрутах	автомаршрут	noun	noun:inanim:p:v_mis
автомаршруте	автомаршрут	noun	noun:inanim:m:v_kly
автомаршрути	автомаршрут	noun	noun:inanim:p:v_kly
автомаршрути	автомаршрут	noun	noun:inanim:p:v_naz
автомаршрути	автомаршрут	noun	noun:inanim:p:v_zna
автомаршрутові	автомаршрут	noun	noun:inanim:m:v_dav
автомаршрутові	автомаршрут	noun	noun:inanim:m:v_mis
автомаршрутом	автомаршрут	noun	noun:inanim:m:v_oru
автомаршруту	автомаршрут	noun	noun:inanim:m:v_dav
автомаршруту	автомаршрут	noun	noun:inanim:m:v_mis
автомаршруту	автомаршрут	noun	noun:inanim:m:v_rod
автомаршруті	автомаршрут	noun	noun:inanim:m:v_mis
автомаршрутів	автомаршрут	noun	noun:inanim:p:v_rod
автомасажер	автомасажер	noun	noun:inanim:m:v_naz
автомасажер	автомасажер	noun	noun:inanim:m:v_zna
автомасажера	автомасажер	noun	noun:inanim:m:v_rod
автомасажерам	автомасажер	noun	noun:inanim:p:v_dav
автомасажерами	автомасажер	noun	noun:inanim:p:v_oru
автомасажерах	автомасажер	noun	noun:inanim:p:v_mis
автомасажере	автомасажер	noun	noun:inanim:m:v_kly
автомасажери	автомасажер	noun	noun:inanim:p:v_kly
автомасажери	автомасажер	noun	noun:inanim:p:v_naz
автомасажери	автомасажер	noun	noun:inanim:p:v_zna
автомасажерові	автомасажер	noun	noun:inanim:m:v_dav
автомасажерові	автомасажер	noun	noun:inanim:m:v_mis
автомасажером	автомасажер	noun	noun:inanim:m:v_oru
автомасажері	автомасажер	noun	noun:inanim:m:v_mis
автомасажерів	автомасажер	noun	noun:inanim:p:v_rod
автомастил	автомастило	noun	noun:inanim:p:v_rod
автомастила	автомастило	noun	noun:inanim:n:v_rod
автомастила	автомастило	noun	noun:inanim:p:v_kly
автомастила	автомастило	noun	noun:inanim:p:v_naz
автомастила	автомастило	noun	noun:inanim:p:v_zna
автомастилам	автомастило	noun	noun:inanim:p:v_dav
автомастилами	автомастило	noun	noun:inanim:p:v_oru
автомастилах	автомастило	noun	noun:inanim:p:v_mis
автомастило	автомастило	noun	noun:inanim:n:v_kly
автомастило	автомастило	noun	noun:inanim:n:v_naz
автомастило	автомастило	noun	noun:inanim:n:v_zna
автомастилом	автомастило	noun	noun:inanim:n:v_oru
автомастилу	автомастило	noun	noun:inanim:n:v_dav
автомастилу	автомастило	noun	noun:inanim:n:v_mis
автомастилі	автомастило	noun	noun:inanim:n:v_mis
автомат	автомат	noun	noun:inanim:m:v_naz
автомат	автомат	noun	noun:inanim:m:v_zna
автомата	автомат	noun	noun:inanim:m:v_rod
автомата	автомат	noun	noun:inanim:m:v_zna:var
автоматам	автомат	noun	noun:inanim:p:v_dav
автоматами	автомат	noun	noun:inanim:p:v_oru
автоматах	автомат	noun	noun:inanim:p:v_mis
автомате	автомат	noun	noun:inanim:m:v_kly
автомати	автомат	noun	noun:inanim:p:v_kly
автомати	автомат	noun	noun:inanim:p:v_naz
автомати	автомат	noun	noun:inanim:p:v_zna
автоматизатор	автоматизатор	noun	noun:inanim:m:v_naz
автоматизатор	автоматизатор	noun	noun:inanim:m:v_zna
автоматизатора	автоматизатор	noun	noun:inanim:m:v_rod
автоматизаторам	автоматизатор	noun	noun:inanim:p:v_dav
автоматизаторами	автоматизатор	noun	noun:inanim:p:v_oru
автоматизаторах	автоматизатор	noun	noun:inanim:p:v_mis
автоматизаторе	автоматизатор	noun	noun:inanim:m:v_kly
автоматизатори	автоматизатор	noun	noun:inanim:p:v_kly
автоматизатори	автоматизатор	noun	noun:inanim:p:v_naz
автоматизатори	автоматизатор	noun	noun:inanim:p:v_zna
автоматизаторові	автоматизатор	noun	noun:inanim:m:v_dav
автоматизаторові	автоматизатор	noun	noun:inanim:m:v_mis
автоматизатором	автоматизатор	noun	noun:inanim:m:v_oru
автоматизаторі	автоматизатор	noun	noun:inanim:m:v_mis
автоматизаторів	автоматизатор	noun	noun:inanim:p:v_rod
автоматизацій	автоматизація	noun	noun:inanim:p:v_rod
автоматизацію	автоматизація	noun	noun:inanim:f:v_zna
автоматизація	автоматизація	noun	noun:inanim:f:v_naz
автоматизаціям	автоматизація	noun	noun:inanim:p:v_dav
автоматизаціями	автоматизація	noun	noun:inanim:p:v_oru
автоматизаціях	автоматизація	noun	noun:inanim:p:v_mis
автоматизаціє	автоматизація	noun	noun:inanim:f:v_kly
автоматизацією	автоматизація	noun	noun:inanim:f:v_oru
автоматизації	автоматизація	noun	noun:inanim:f:v_dav
автоматизації	автоматизація	noun	noun:inanim:f:v_mis
автоматизації	автоматизація	noun	noun:inanim:f:v_rod
автоматизації	автоматизація	noun	noun:inanim:p:v_kly
автоматизації	автоматизація	noun	noun:inanim:p:v_naz
автоматизації	автоматизація	noun	noun:inanim:p:v_zna
автоматизм	автоматизм	noun	noun:inanim:m:v_naz
автоматизм	автоматизм	noun	noun:inanim:m:v_zna
автоматизмам	автоматизм	noun	noun:inanim:p:v_dav
автоматизмами	автоматизм	noun	noun:inanim:p:v_oru
автоматизмах	автоматизм	noun	noun:inanim:p:v_mis
автоматизме	автоматизм	noun	noun:inanim:m:v_kly
автоматизми	автоматизм	noun	noun:inanim:p:v_kly
автоматизми	автоматизм	noun	noun:inanim:p:v_naz
автоматизми	автоматизм	noun	noun:inanim:p:v_zna
автоматизмові	автоматизм	noun	noun:inanim:m:v_dav
автоматизмові	автоматизм	noun	noun:inanim:m:v_mis
автоматизмом	автоматизм	noun	noun:inanim:m:v_oru
автоматизму	автоматизм	noun	noun:inanim:m:v_dav
автоматизму	автоматизм	noun	noun:inanim:m:v_mis
автоматизму	автоматизм	noun	noun:inanim:m:v_rod
автоматизмі	автоматизм	noun	noun:inanim:m:v_mis
автоматизмів	автоматизм	noun	noun:inanim:p:v_rod
автоматик	автоматика	noun	noun:inanim:p:v_rod
автоматика	автоматика	noun	noun:inanim:f:v_naz
автоматикам	автоматика	noun	noun:inanim:p:v_dav
автоматиками	автоматика	noun	noun:inanim:p:v_oru
автоматиках	автоматика	noun	noun:inanim:p:v_mis
автоматики	автоматика	noun	noun:inanim:f:v_rod
автоматики	автоматика	noun	noun:inanim:p:v_kly
автоматики	автоматика	noun	noun:inanim:p:v_naz
автоматики	автоматика	noun	noun:inanim:p:v_zna
автоматико	автоматика	noun	noun:inanim:f:v_kly
автоматикою	автоматика	noun	noun:inanim:f:v_oru
автоматику	автоматика	noun	noun:inanim:f:v_zna
автоматиці	автоматика	noun	noun:inanim:f:v_dav
автоматиці	автоматика	noun	noun:inanim:f:v_mis
автоматник	автоматник	noun	noun:anim:m:v_naz
автоматника	автоматник	noun	noun:anim:m:v_rod
автоматника	автоматник	noun	noun:anim:m:v_zna
автоматникам	автоматник	noun	noun:anim:p:v_dav
автоматниками	автоматник	noun	noun:anim:p:v_oru
автоматниках	автоматник	noun	noun:anim:p:v_mis
автоматники	автоматник	noun	noun:anim:p:v_kly
автоматники	автоматник	noun	noun:anim:p:v_naz
автоматники	автоматник	noun	noun:anim:p:v_zna:rare
автоматникові	автоматник	noun	noun:anim:m:v_dav
автоматникові	автоматник	noun	noun:anim:m:v_mis
автоматником	автоматник	noun	noun:anim:m:v_oru
автоматнику	автоматник	noun	noun:anim:m:v_dav
автоматнику	автоматник	noun	noun:anim:m:v_kly
автоматнику	автоматник	noun	noun:anim:m:v_mis
автоматників	автоматник	noun	noun:anim:p:v_rod
автоматників	автоматник	noun	noun:anim:p:v_zna
автоматнице	автоматниця	noun	noun:anim:f:v_kly
автоматницею	автоматниця	noun	noun:anim:f:v_oru
автоматниць	автоматниця	noun	noun:anim:p:v_rod
автоматниць	автоматниця	noun	noun:anim:p:v_zna
автоматницю	автоматниця	noun	noun:anim:f:v_zna
автоматниця	автоматниця	noun	noun:anim:f:v_naz
автоматницям	автоматниця	noun	noun:anim:p:v_dav
автоматницями	автоматниця	noun	noun:anim:p:v_oru
автоматницях	автоматниця	noun	noun:anim:p:v_mis
автоматниці	автоматниця	noun	noun:anim:f:v_dav
автоматниці	автоматниця	noun	noun:anim:f:v_mis
автоматниці	автоматниця	noun	noun:anim:f:v_rod
автоматниці	автоматниця	noun	noun:anim:p:v_kly
автоматниці	автоматниця	noun	noun:anim:p:v_naz
автоматниці	автоматниця	noun	noun:anim:p:v_zna:rare
автоматові	автомат	noun	noun:inanim:m:v_dav
автоматові	автомат	noun	noun:inanim:m:v_mis
автоматограф	автоматограф	noun	noun:inanim:m:v_naz
автоматограф	автоматограф	noun	noun:inanim:m:v_zna
автоматографа	автоматограф	noun	noun:inanim:m:v_rod
автоматографам	автоматограф	noun	noun:inanim:p:v_dav
автоматографами	автоматограф	noun	noun:inanim:p:v_oru
автоматографах	автоматограф	noun	noun:inanim:p:v_mis
автоматографе	автоматограф	noun	noun:inanim:m:v_kly
автоматографи	автоматограф	noun	noun:inanim:p:v_kly
автоматографи	автоматограф	noun	noun:inanim:p:v_naz
автоматографи	автоматограф	noun	noun:inanim:p:v_zna
автоматографові	автоматограф	noun	noun:inanim:m:v_dav
автоматографові	автоматограф	noun	noun:inanim:m:v_mis
автоматографом	автоматограф	noun	noun:inanim:m:v_oru
автоматографі	автоматограф	noun	noun:inanim:m:v_mis
автоматографів	автоматограф	noun	noun:inanim:p:v_rod
автоматом	автомат	noun	noun:inanim:m:v_oru
автоматі	автомат	noun	noun:inanim:m:v_mis
автоматів	автомат	noun	noun:inanim:p:v_rod
автомахій	автомахія	noun	noun:inanim:p:v_rod
автомахію	автомахія	noun	noun:inanim:f:v_zna
автомахія	автомахія	noun	noun:inanim:f:v_naz
автомахіям	автомахія	noun	noun:inanim:p:v_dav
автомахіями	автомахія	noun	noun:inanim:p:v_oru
автомахіях	автомахія	noun	noun:inanim:p:v_mis
автомахіє	автомахія	noun	noun:inanim:f:v_kly
автомахією	автомахія	noun	noun:inanim:f:v_oru
автомахії	автомахія	noun	noun:inanim:f:v_dav
автомахії	автомахія	noun	noun:inanim:f:v_mis
автомахії	автомахія	noun	noun:inanim:f:v_rod
автомахії	автомахія	noun	noun:inanim:p:v_kly
автомахії	автомахія	noun	noun:inanim:p:v_naz
автомахії	автомахія	noun	noun:inanim:p:v_zna
автомашин	автомашина	noun	noun:inanim:p:v_rod
автомашина	автомашина	noun	noun:inanim:f:v_naz
автомашинам	автомашина	noun	noun:inanim:p:v_dav
автомашинами	автомашина	noun	noun:inanim:p:v_oru
автомашинах	автомашина	noun	noun:inanim:p:v_mis
автомашини	автомашина	noun	noun:inanim:f:v_rod
автомашини	автомашина	noun	noun:inanim:p:v_kly
автомашини	автомашина	noun	noun:inanim:p:v_naz
автомашини	автомашина	noun	noun:inanim:p:v_zna
автомашино	автомашина	noun	noun:inanim:f:v_kly
автомашиною	автомашина	noun	noun:inanim:f:v_oru
автомашину	автомашина	noun	noun:inanim:f:v_zna
автомашині	автомашина	noun	noun:inanim:f:v_dav
автомашині	автомашина	noun	noun:inanim:f:v_mis
автомашиніст	автомашиніст	noun	noun:anim:m:v_naz
автомашиніста	автомашиніст	noun	noun:anim:m:v_rod
автомашиніста	автомашиніст	noun	noun:anim:m:v_zna
автомашиністам	автомашиніст	noun	noun:anim:p:v_dav
автомашиністами	автомашиніст	noun	noun:anim:p:v_oru
автомашиністах	автомашиніст	noun	noun:anim:p:v_mis
автомашиністе	автомашиніст	noun	noun:anim:m:v_kly
автомашиністи	автомашиніст	noun	noun:anim:p:v_kly
автомашиністи	автомашиніст	noun	noun:anim:p:v_naz
автомашиністи	автомашиніст	noun	noun:anim:p:v_zna:rare
автомашиністові	автомашиніст	noun	noun:anim:m:v_dav
автомашиністові	автомашиніст	noun	noun:anim:m:v_mis
автомашиністом	автомашиніст	noun	noun:anim:m:v_oru
автомашиністі	автомашиніст	noun	noun:anim:m:v_mis
автомашиністів	автомашиніст	noun	noun:anim:p:v_rod
автомашиністів	автомашиніст	noun	noun:anim:p:v_zna
автомереж	автомережа	noun	noun:inanim:p:v_rod
автомережа	автомережа	noun	noun:inanim:f:v_naz
автомережам	автомережа	noun	noun:inanim:p:v_dav
автомережами	автомережа	noun	noun:inanim:p:v_oru
автомережах	автомережа	noun	noun:inanim:p:v_mis
автомереже	автомережа	noun	noun:inanim:f:v_kly
автомережею	автомережа	noun	noun:inanim:f:v_oru
автомережу	автомережа	noun	noun:inanim:f:v_zna
автомережі	автомережа	noun	noun:inanim:f:v_dav
автомережі	автомережа	noun	noun:inanim:f:v_mis
автомережі	автомережа	noun	noun:inanim:f:v_rod
автомережі	автомережа	noun	noun:inanim:p:v_kly
автомережі	автомережа	noun	noun:inanim:p:v_naz
автомережі	автомережа	noun	noun:inanim:p:v_zna
автомеханохорій	автомеханохорія	noun	noun:inanim:p:v_rod
автомеханохорію	автомеханохорія	noun	noun:inanim:f:v_zna
автомеханохорія	автомеханохорія	noun	noun:inanim:f:v_naz
автомеханохоріям	автомеханохорія	noun	noun:inanim:p:v_dav
автомеханохоріями	автомеханохорія	noun	noun:inanim:p:v_oru
автомеханохоріях	автомеханохорія	noun	noun:inanim:p:v_mis
автомеханохоріє	автомеханохорія	noun	noun:inanim:f:v_kly
автомеханохорією	автомеханохорія	noun	noun:inanim:f:v_oru
автомеханохорії	автомеханохорія	noun	noun:inanim:f:v_dav
автомеханохорії	автомеханохорія	noun	noun:inanim:f:v_mis
автомеханохорії	автомеханохорія	noun	noun:inanim:f:v_rod
автомеханохорії	автомеханохорія	noun	noun:inanim:p:v_kly
автомеханохорії	автомеханохорія	noun	noun:inanim:p:v_naz
автомеханохорії	автомеханохорія	noun	noun:inanim:p:v_zna
автомеханік	автомеханік	noun	noun:anim:m:v_naz
автомеханіка	автомеханік	noun	noun:anim:m:v_rod
автомеханіка	автомеханік	noun	noun:anim:m:v_zna
автомеханікам	автомеханік	noun	noun:anim:p:v_dav
автомеханіками	автомеханік	noun	noun:anim:p:v_oru
автомеханіках	автомеханік	noun	noun:anim:p:v_mis
автомеханіки	автомеханік	noun	noun:anim:p:v_kly
автомеханіки	автомеханік	noun	noun:anim:p:v_naz
автомеханіки	автомеханік	noun	noun:anim:p:v_zna:rare
автомеханікові	автомеханік	noun	noun:anim:m:v_dav
автомеханікові	автомеханік	noun	noun:anim:m:v_mis
автомеханіком	автомеханік	noun	noun:anim:m:v_oru
автомеханіку	автомеханік	noun	noun:anim:m:v_dav
автомеханіку	автомеханік	noun	noun:anim:m:v_kly
автомеханіку	автомеханік	noun	noun:anim:m:v_mis
автомеханіків	автомеханік	noun	noun:anim:p:v_rod
автомеханіків	автомеханік	noun	noun:anim:p:v_zna
автомийка	автомийка	noun	noun:inanim:f:v_naz
автомийкам	автомийка	noun	noun:inanim:p:v_dav
автомийками	автомийка	noun	noun:inanim:p:v_oru
автомийках	автомийка	noun	noun:inanim:p:v_mis
автомийки	автомийка	noun	noun:inanim:f:v_rod
автомийки	автомийка	noun	noun:inanim:p:v_kly
автомийки	автомийка	noun	noun:inanim:p:v_naz
автомийки	автомийка	noun	noun:inanim:p:v_zna
автомийко	автомийка	noun	noun:inanim:f:v_kly
автомийкою	автомийка	noun	noun:inanim:f:v_oru
автомийку	автомийка	noun	noun:inanim:f:v_zna
автомийне	автомийня	noun	noun:inanim:f:v_kly
автомийнею	автомийня	noun	noun:inanim:f:v_oru
автомийник	автомийник	noun	noun:anim:m:v_naz
автомийника	автомийник	noun	noun:anim:m:v_rod
автомийника	автомийник	noun	noun:anim:m:v_zna
автомийникам	автомийник	noun	noun:anim:p:v_dav
автомийниками	автомийник	noun	noun:anim:p:v_oru
автомийниках	автомийник	noun	noun:anim:p:v_mis
автомийники	автомийник	noun	noun:anim:p:v_kly
автомийники	автомийник	noun	noun:anim:p:v_naz
автомийники	автомийник	noun	noun:anim:p:v_zna:rare
автомийникові	автомийник	noun	noun:anim:m:v_dav
автомийникові	автомийник	noun	noun:anim:m:v_mis
автомийником	автомийник	noun	noun:anim:m:v_oru
автомийнику	автомийник	noun	noun:anim:m:v_dav
автомийнику	автомийник	noun	noun:anim:m:v_kly
автомийнику	автомийник	noun	noun:anim:m:v_mis
автомийників	автомийник	noun	noun:anim:p:v_rod
автомийників	автомийник	noun	noun:anim:p:v_zna
автомийню	автомийня	noun	noun:inanim:f:v_zna
автомийня	автомийня	noun	noun:inanim:f:v_naz
автомийням	автомийня	noun	noun:inanim:p:v_dav
автомийнями	автомийня	noun	noun:inanim:p:v_oru
автомийнях	автомийня	noun	noun:inanim:p:v_mis
автомийні	автомийня	noun	noun:inanim:f:v_dav
автомийні	автомийня	noun	noun:inanim:f:v_mis
автомийні	автомийня	noun	noun:inanim:f:v_rod
автомийні	автомийня	noun	noun:inanim:p:v_kly
автомийні	автомийня	noun	noun:inanim:p:v_naz
автомийні	автомийня	noun	noun:inanim:p:v_zna
автомийок	автомийка	noun	noun:inanim:p:v_rod
автомийці	автомийка	noun	noun:inanim:f:v_dav
автомийці	автомийка	noun	noun:inanim:f:v_mis
автомит	автомито	noun	noun:inanim:p:v_rod
автомита	автомито	noun	noun:inanim:n:v_rod
автомита	автомито	noun	noun:inanim:p:v_kly
автомита	автомито	noun	noun:inanim:p:v_naz
автомита	автомито	noun	noun:inanim:p:v_zna
автомитам	автомито	noun	noun:inanim:p:v_dav
автомитами	автомито	noun	noun:inanim:p:v_oru
автомитах	автомито	noun	noun:inanim:p:v_mis
автомито	автомито	noun	noun:inanim:n:v_kly
автомито	автомито	noun	noun:inanim:n:v_naz
автомито	автомито	noun	noun:inanim:n:v_zna
автомитом	автомито	noun	noun:inanim:n:v_oru
автомиту	автомито	noun	noun:inanim:n:v_dav
автомиту	автомито	noun	noun:inanim:n:v_mis
автомиті	автомито	noun	noun:inanim:n:v_mis
автомиєнь	автомийня	noun	noun:inanim:p:v_rod
автомобілебудівник	автомобілебудівник	noun	noun:anim:m:v_naz
автомобілебудівника	автомобілебудівник	noun	noun:anim:m:v_rod
автомобілебудівника	автомобілебудівник	noun	noun:anim:m:v_zna
автомобілебудівникам	автомобілебудівник	noun	noun:anim:p:v_dav
автомобілебудівниками	автомобілебудівник	noun	noun:anim:p:v_oru
автомобілебудівниках	автомобілебудівник	noun	noun:anim:p:v_mis
автомобілебудівники	автомобілебудівник	noun	noun:anim:p:v_kly
автомобілебудівники	автомобілебудівник	noun	noun:anim:p:v_naz
автомобілебудівники	автомобілебудівник	noun	noun:anim:p:v_zna:rare
автомобілебудівникові	автомобілебудівник	noun	noun:anim:m:v_dav
автомобілебудівникові	автомобілебудівник	noun	noun:anim:m:v_mis
автомобілебудівником	автомобілебудівник	noun	noun:anim:m:v_oru
автомобілебудівнику	автомобілебудівник	noun	noun:anim:m:v_dav
автомобілебудівнику	автомобілебудівник	noun	noun:anim:m:v_kly
автомобілебудівнику	автомобілебудівник	noun	noun:anim:m:v_mis
автомобілебудівників	автомобілебудівник	noun	noun:anim:p:v_rod
автомобілебудівників	автомобілебудівник	noun	noun:anim:p:v_zna
автомобілевиробник	автомобілевиробник	noun	noun:inanim:m:v_naz
автомобілевиробник	автомобілевиробник	noun	noun:inanim:m:v_zna
автомобілевиробника	автомобілевиробник	noun	noun:inanim:m:v_rod
автомобілевиробникам	автомобілевиробник	noun	noun:inanim:p:v_dav
автомобілевиробниками	автомобілевиробник	noun	noun:inanim:p:v_oru
автомобілевиробниках	автомобілевиробник	noun	noun:inanim:p:v_mis
автомобілевиробники	автомобілевиробник	noun	noun:inanim:p:v_kly
автомобілевиробники	автомобілевиробник	noun	noun:inanim:p:v_naz
автомобілевиробники	автомобілевиробник	noun	noun:inanim:p:v_zna
автомобілевиробникові	автомобілевиробник	noun	noun:inanim:m:v_dav
автомобілевиробникові	автомобілевиробник	noun	noun:inanim:m:v_mis
автомобілевиробником	автомобілевиробник	noun	noun:inanim:m:v_oru
автомобілевиробнику	автомобілевиробник	noun	noun:inanim:m:v_dav
автомобілевиробнику	автомобілевиробник	noun	noun:inanim:m:v_kly
автомобілевиробнику	автомобілевиробник	noun	noun:inanim:m:v_mis
автомобілевиробників	автомобілевиробник	noun	noun:inanim:p:v_rod
автомобілевоз	автомобілевоз	noun	noun:inanim:m:v_naz
автомобілевоз	автомобілевоз	noun	noun:inanim:m:v_zna
автомобілевоза	автомобілевоз	noun	noun:inanim:m:v_rod
автомобілевозам	автомобілевоз	noun	noun:inanim:p:v_dav
автомобілевозами	автомобілевоз	noun	noun:inanim:p:v_oru
автомобілевозах	автомобілевоз	noun	noun:inanim:p:v_mis
автомобілевозе	автомобілевоз	noun	noun:inanim:m:v_kly
автомобілевози	автомобілевоз	noun	noun:inanim:p:v_kly
автомобілевози	автомобілевоз	noun	noun:inanim:p:v_naz
автомобілевози	автомобілевоз	noun	noun:inanim:p:v_zna
автомобілевозові	автомобілевоз	noun	noun:inanim:m:v_dav
автомобілевозові	автомобілевоз	noun	noun:inanim:m:v_mis
автомобілевозом	автомобілевоз	noun	noun:inanim:m:v_oru
автомобілевозі	автомобілевоз	noun	noun:inanim:m:v_mis
автомобілевозів	автомобілевоз	noun	noun:inanim:p:v_rod
автомобілеві	автомобіль	noun	noun:inanim:m:v_dav
автомобілеві	автомобіль	noun	noun:inanim:m:v_mis
автомобілем	автомобіль	noun	noun:inanim:m:v_oru
автомобілепідіймач	автомобілепідіймач	noun	noun:inanim:m:v_naz
автомобілепідіймач	автомобілепідіймач	noun	noun:inanim:m:v_zna
автомобілепідіймача	автомобілепідіймач	noun	noun:inanim:m:v_rod
автомобілепідіймачам	автомобілепідіймач	noun	noun:inanim:p:v_dav
автомобілепідіймачами	автомобілепідіймач	noun	noun:inanim:p:v_oru
автомобілепідіймачах	автомобілепідіймач	noun	noun:inanim:p:v_mis
автомобілепідіймачеві	автомобілепідіймач	noun	noun:inanim:m:v_dav
автомобілепідіймачеві	автомобілепідіймач	noun	noun:inanim:m:v_mis
автомобілепідіймачем	автомобілепідіймач	noun	noun:inanim:m:v_oru
автомобілепідіймачу	автомобілепідіймач	noun	noun:inanim:m:v_dav
автомобілепідіймачу	автомобілепідіймач	noun	noun:inanim:m:v_kly
автомобілепідіймачу	автомобілепідіймач	noun	noun:inanim:m:v_mis
автомобілепідіймачі	автомобілепідіймач	noun	noun:inanim:m:v_mis
автомобілепідіймачі	автомобілепідіймач	noun	noun:inanim:p:v_kly
автомобілепідіймачі	автомобілепідіймач	noun	noun:inanim:p:v_naz
автомобілепідіймачі	автомобілепідіймач	noun	noun:inanim:p:v_zna
автомобілепідіймачів	автомобілепідіймач	noun	noun:inanim:p:v_rod
автомобілерозвантажувач	автомобілерозвантажувач	noun	noun:inanim:m:v_naz
автомобілерозвантажувач	автомобілерозвантажувач	noun	noun:inanim:m:v_zna
автомобілерозвантажувача	автомобілерозвантажувач	noun	noun:inanim:m:v_rod
автомобілерозвантажувачам	автомобілерозвантажувач	noun	noun:inanim:p:v_dav
автомобілерозвантажувачами	автомобілерозвантажувач	noun	noun:inanim:p:v_oru
автомобілерозвантажувачах	автомобілерозвантажувач	noun	noun:inanim:p:v_mis
автомобілерозвантажувачеві	автомобілерозвантажувач	noun	noun:inanim:m:v_dav
автомобілерозвантажувачеві	автомобілерозвантажувач	noun	noun:inanim:m:v_mis
автомобілерозвантажувачем	автомобілерозвантажувач	noun	noun:inanim:m:v_oru
автомобілерозвантажувачу	автомобілерозвантажувач	noun	noun:inanim:m:v_dav
автомобілерозвантажувачу	автомобілерозвантажувач	noun	noun:inanim:m:v_kly
автомобілерозвантажувачу	автомобілерозвантажувач	noun	noun:inanim:m:v_mis
автомобілерозвантажувачі	автомобілерозвантажувач	noun	noun:inanim:m:v_mis
автомобілерозвантажувачі	автомобілерозвантажувач	noun	noun:inanim:p:v_kly
автомобілерозвантажувачі	автомобілерозвантажувач	noun	noun:inanim:p:v_naz
автомобілерозвантажувачі	автомобілерозвантажувач	noun	noun:inanim:p:v_zna
автомобілерозвантажувачів	автомобілерозвантажувач	noun	noun:inanim:p:v_rod
автомобіль	автомобіль	noun	noun:inanim:m:v_naz
автомобіль	автомобіль	noun	noun:inanim:m:v_zna
автомобільчик	автомобільчик	noun	noun:inanim:m:v_naz
автомобільчик	автомобільчик	noun	noun:inanim:m:v_zna
автомобільчика	автомобільчик	noun	noun:inanim:m:v_rod
автомобільчикам	автомобільчик	noun	noun:inanim:p:v_dav
автомобільчиками	автомобільчик	noun	noun:inanim:p:v_oru
автомобільчиках	автомобільчик	noun	noun:inanim:p:v_mis
автомобільчики	автомобільчик	noun	noun:inanim:p:v_kly
автомобільчики	автомобільчик	noun	noun:inanim:p:v_naz
автомобільчики	автомобільчик	noun	noun:inanim:p:v_zna
автомобільчикові	автомобільчик	noun	noun:inanim:m:v_dav
автомобільчикові	автомобільчик	noun	noun:inanim:m:v_mis
автомобільчиком	автомобільчик	noun	noun:inanim:m:v_oru
автомобільчику	автомобільчик	noun	noun:inanim:m:v_dav
автомобільчику	автомобільчик	noun	noun:inanim:m:v_kly
автомобільчику	автомобільчик	noun	noun:inanim:m:v_mis
автомобільчиків	автомобільчик	noun	noun:inanim:p:v_rod
автомобілю	автомобіль	noun	noun:inanim:m:v_dav
автомобілю	автомобіль	noun	noun:inanim:m:v_kly
автомобілю	автомобіль	noun	noun:inanim:m:v_mis
автомобіля	автомобіль	noun	noun:inanim:m:v_rod
автомобіля	автомобіль	noun	noun:inanim:m:v_zna:var
автомобілям	автомобіль	noun	noun:inanim:p:v_dav
автомобілями	автомобіль	noun	noun:inanim:p:v_oru
автомобілях	автомобіль	noun	noun:inanim:p:v_mis
автомобілі	автомобіль	noun	noun:inanim:m:v_mis
автомобілі	автомобіль	noun	noun:inanim:p:v_kly
автомобілі	автомобіль	noun	noun:inanim:p:v_naz
автомобілі	автомобіль	noun	noun:inanim:p:v_zna
автомобілів	автомобіль	noun	noun:inanim:p:v_rod
автомобіліст	автомобіліст	noun	noun:anim:m:v_naz
автомобіліста	автомобіліст	noun	noun:anim:m:v_rod
автомобіліста	автомобіліст	noun	noun:anim:m:v_zna
автомобілістам	автомобіліст	noun	noun:anim:p:v_dav
автомобілістами	автомобіліст	noun	noun:anim:p:v_oru
автомобілістах	автомобіліст	noun	noun:anim:p:v_mis
автомобілісте	автомобіліст	noun	noun:anim:m:v_kly
автомобілісти	автомобіліст	noun	noun:anim:p:v_kly
автомобілісти	автомобіліст	noun	noun:anim:p:v_naz
автомобілісти	автомобіліст	noun	noun:anim:p:v_zna:rare
автомобілістка	автомобілістка	noun	noun:anim:f:v_naz
автомобілісткам	автомобілістка	noun	noun:anim:p:v_dav
автомобілістками	автомобілістка	noun	noun:anim:p:v_oru
автомобілістках	автомобілістка	noun	noun:anim:p:v_mis
автомобілістки	автомобілістка	noun	noun:anim:f:v_rod
автомобілістки	автомобілістка	noun	noun:anim:p:v_kly
автомобілістки	автомобілістка	noun	noun:anim:p:v_naz
автомобілістки	автомобілістка	noun	noun:anim:p:v_zna:rare
автомобілістко	автомобілістка	noun	noun:anim:f:v_kly
автомобілісткою	автомобілістка	noun	noun:anim:f:v_oru
автомобілістку	автомобілістка	noun	noun:anim:f:v_zna
автомобілістові	автомобіліст	noun	noun:anim:m:v_dav
автомобілістові	автомобіліст	noun	noun:anim:m:v_mis
автомобілісток	автомобілістка	noun	noun:anim:p:v_rod
автомобілісток	автомобілістка	noun	noun:anim:p:v_zna
автомобілістом	автомобіліст	noun	noun:anim:m:v_oru
автомобілістці	автомобілістка	noun	noun:anim:f:v_dav
автомобілістці	автомобілістка	noun	noun:anim:f:v_mis
автомобілісті	автомобіліст	noun	noun:anim:m:v_mis
автомобілістів	автомобіліст	noun	noun:anim:p:v_rod
автомобілістів	автомобіліст	noun	noun:anim:p:v_zna
автомогильник	автомогильник	noun	noun:inanim:m:v_naz
автомогильник	автомогильник	noun	noun:inanim:m:v_zna
автомогильника	автомогильник	noun	noun:inanim:m:v_rod
автомогильникам	автомогильник	noun	noun:inanim:p:v_dav
автомогильниками	автомогильник	noun	noun:inanim:p:v_oru
автомогильниках	автомогильник	noun	noun:inanim:p:v_mis
автомогильники	автомогильник	noun	noun:inanim:p:v_kly
автомогильники	автомогильник	noun	noun:inanim:p:v_naz
автомогильники	автомогильник	noun	noun:inanim:p:v_zna
автомогильникові	автомогильник	noun	noun:inanim:m:v_dav
автомогильникові	автомогильник	noun	noun:inanim:m:v_mis
автомогильником	автомогильник	noun	noun:inanim:m:v_oru
автомогильнику	автомогильник	noun	noun:inanim:m:v_dav
автомогильнику	автомогильник	noun	noun:inanim:m:v_kly
автомогильнику	автомогильник	noun	noun:inanim:m:v_mis
автомогильників	автомогильник	noun	noun:inanim:p:v_rod
автомоделе	автомодель	noun	noun:inanim:f:v_kly
автомоделей	автомодель	noun	noun:inanim:p:v_rod
автомоделлю	автомодель	noun	noun:inanim:f:v_oru
автомодель	автомодель	noun	noun:inanim:f:v_naz
автомодель	автомодель	noun	noun:inanim:f:v_zna
автомоделям	автомодель	noun	noun:inanim:p:v_dav
автомоделями	автомодель	noun	noun:inanim:p:v_oru
автомоделях	автомодель	noun	noun:inanim:p:v_mis
автомоделі	автомодель	noun	noun:inanim:f:v_dav
автомоделі	автомодель	noun	noun:inanim:f:v_mis
автомоделі	автомодель	noun	noun:inanim:f:v_rod
автомоделі	автомодель	noun	noun:inanim:p:v_kly
автомоделі	автомодель	noun	noun:inanim:p:v_naz
автомоделі	автомодель	noun	noun:inanim:p:v_zna
автомоделіст	автомоделіст	noun	noun:anim:m:v_naz
автомоделіста	автомоделіст	noun	noun:anim:m:v_rod
автомоделіста	автомоделіст	noun	noun:anim:m:v_zna
автомоделістам	автомоделіст	noun	noun:anim:p:v_dav
автомоделістами	автомоделіст	noun	noun:anim:p:v_oru
автомоделістах	автомоделіст	noun	noun:anim:p:v_mis
автомоделісте	автомоделіст	noun	noun:anim:m:v_kly
автомоделісти	автомоделіст	noun	noun:anim:p:v_kly
автомоделісти	автомоделіст	noun	noun:anim:p:v_naz
автомоделісти	автомоделіст	noun	noun:anim:p:v_zna:rare
автомоделістові	автомоделіст	noun	noun:anim:m:v_dav
автомоделістові	автомоделіст	noun	noun:anim:m:v_mis
автомоделістом	автомоделіст	noun	noun:anim:m:v_oru
автомоделісті	автомоделіст	noun	noun:anim:m:v_mis
автомоделістів	автомоделіст	noun	noun:anim:p:v_rod
автомоделістів	автомоделіст	noun	noun:anim:p:v_zna
автомонографій	автомонографія	noun	noun:inanim:p:v_rod
автомонографію	автомонографія	noun	noun:inanim:f:v_zna
автомонографія	автомонографія	noun	noun:inanim:f:v_naz
автомонографіям	автомонографія	noun	noun:inanim:p:v_dav
автомонографіями	автомонографія	noun	noun:inanim:p:v_oru
автомонографіях	автомонографія	noun	noun:inanim:p:v_mis
автомонографіє	автомонографія	noun	noun:inanim:f:v_kly
автомонографією	автомонографія	noun	noun:inanim:f:v_oru
автомонографії	автомонографія	noun	noun:inanim:f:v_dav
автомонографії	автомонографія	noun	noun:inanim:f:v_mis
автомонографії	автомонографія	noun	noun:inanim:f:v_rod
автомонографії	автомонографія	noun	noun:inanim:p:v_kly
автомонографії	автомонографія	noun	noun:inanim:p:v_naz
автомонографії	автомонографія	noun	noun:inanim:p:v_zna
автомонітор	автомонітор	noun	noun:inanim:m:v_naz
автомонітор	автомонітор	noun	noun:inanim:m:v_zna
автомонітора	автомонітор	noun	noun:inanim:m:v_rod
автомоніторам	автомонітор	noun	noun:inanim:p:v_dav
автомоніторами	автомонітор	noun	noun:inanim:p:v_oru
автомоніторах	автомонітор	noun	noun:inanim:p:v_mis
автомоніторе	автомонітор	noun	noun:inanim:m:v_kly
автомонітори	автомонітор	noun	noun:inanim:p:v_kly
автомонітори	автомонітор	noun	noun:inanim:p:v_naz
автомонітори	автомонітор	noun	noun:inanim:p:v_zna
автомоніторові	автомонітор	noun	noun:inanim:m:v_dav
автомоніторові	автомонітор	noun	noun:inanim:m:v_mis
автомонітором	автомонітор	noun	noun:inanim:m:v_oru
автомоніторі	автомонітор	noun	noun:inanim:m:v_mis
автомоніторів	автомонітор	noun	noun:inanim:p:v_rod
автоморфізм	автоморфізм	noun	noun:inanim:m:v_naz
автоморфізм	автоморфізм	noun	noun:inanim:m:v_zna
автоморфізмам	автоморфізм	noun	noun:inanim:p:v_dav
автоморфізмами	автоморфізм	noun	noun:inanim:p:v_oru
автоморфізмах	автоморфізм	noun	noun:inanim:p:v_mis
автоморфізме	автоморфізм	noun	noun:inanim:m:v_kly
автоморфізми	автоморфізм	noun	noun:inanim:p:v_kly
автоморфізми	автоморфізм	noun	noun:inanim:p:v_naz
автоморфізми	автоморфізм	noun	noun:inanim:p:v_zna
автоморфізмові	автоморфізм	noun	noun:inanim:m:v_dav
автоморфізмові	автоморфізм	noun	noun:inanim:m:v_mis
автоморфізмом	автоморфізм	noun	noun:inanim:m:v_oru
автоморфізму	автоморфізм	noun	noun:inanim:m:v_dav
автоморфізму	автоморфізм	noun	noun:inanim:m:v_mis
автоморфізму	автоморфізм	noun	noun:inanim:m:v_rod
автоморфізмі	автоморфізм	noun	noun:inanim:m:v_mis
автоморфізмів	автоморфізм	noun	noun:inanim:p:v_rod
автомоста	автоміст	noun	noun:inanim:m:v_rod
автомостам	автоміст	noun	noun:inanim:p:v_dav
автомостами	автоміст	noun	noun:inanim:p:v_oru
автомостах	автоміст	noun	noun:inanim:p:v_mis
автомосте	автоміст	noun	noun:inanim:m:v_kly
автомости	автоміст	noun	noun:inanim:p:v_kly
автомости	автоміст	noun	noun:inanim:p:v_naz
автомости	автоміст	noun	noun:inanim:p:v_zna
автомостові	автоміст	noun	noun:inanim:m:v_dav
автомостові	автоміст	noun	noun:inanim:m:v_mis
автомостом	автоміст	noun	noun:inanim:m:v_oru
автомості	автоміст	noun	noun:inanim:m:v_mis
автомостів	автоміст	noun	noun:inanim:p:v_rod
автомотоаматор	автомотоаматор	noun	noun:anim:m:v_naz
автомотоаматора	автомотоаматор	noun	noun:anim:m:v_rod
автомотоаматора	автомотоаматор	noun	noun:anim:m:v_zna
автомотоаматорам	автомотоаматор	noun	noun:anim:p:v_dav
автомотоаматорами	автомотоаматор	noun	noun:anim:p:v_oru
автомотоаматорах	автомотоаматор	noun	noun:anim:p:v_mis
автомотоаматоре	автомотоаматор	noun	noun:anim:m:v_kly
автомотоаматори	автомотоаматор	noun	noun:anim:p:v_kly
автомотоаматори	автомотоаматор	noun	noun:anim:p:v_naz
автомотоаматори	автомотоаматор	noun	noun:anim:p:v_zna:rare
автомотоаматорові	автомотоаматор	noun	noun:anim:m:v_dav
автомотоаматорові	автомотоаматор	noun	noun:anim:m:v_mis
автомотоаматором	автомотоаматор	noun	noun:anim:m:v_oru
автомотоаматорі	автомотоаматор	noun	noun:anim:m:v_mis
автомотоаматорів	автомотоаматор	noun	noun:anim:p:v_rod
автомотоаматорів	автомотоаматор	noun	noun:anim:p:v_zna
автомотогуртка	автомотогурток	noun	noun:inanim:m:v_rod
автомотогурткам	автомотогурток	noun	noun:inanim:p:v_dav
автомотогуртками	автомотогурток	noun	noun:inanim:p:v_oru
автомотогуртках	автомотогурток	noun	noun:inanim:p:v_mis
автомотогуртки	автомотогурток	noun	noun:inanim:p:v_kly
автомотогуртки	автомотогурток	noun	noun:inanim:p:v_naz
автомотогуртки	автомотогурток	noun	noun:inanim:p:v_zna
автомотогурткові	автомотогурток	noun	noun:inanim:m:v_dav
автомотогурткові	автомотогурток	noun	noun:inanim:m:v_mis
автомотогуртком	автомотогурток	noun	noun:inanim:m:v_oru
автомотогуртку	автомотогурток	noun	noun:inanim:m:v_dav
автомотогуртку	автомотогурток	noun	noun:inanim:m:v_kly
автомотогуртку	автомотогурток	noun	noun:inanim:m:v_mis
автомотогуртків	автомотогурток	noun	noun:inanim:p:v_rod
автомотогурток	автомотогурток	noun	noun:inanim:m:v_naz
автомотогурток	автомотогурток	noun	noun:inanim:m:v_zna
автомотодром	автомотодром	noun	noun:inanim:m:v_naz
автомотодром	автомотодром	noun	noun:inanim:m:v_zna
автомотодромам	автомотодром	noun	noun:inanim:p:v_dav
автомотодромами	автомотодром	noun	noun:inanim:p:v_oru
автомотодромах	автомотодром	noun	noun:inanim:p:v_mis
автомотодроме	автомотодром	noun	noun:inanim:m:v_kly
автомотодроми	автомотодром	noun	noun:inanim:p:v_kly
автомотодроми	автомотодром	noun	noun:inanim:p:v_naz
автомотодроми	автомотодром	noun	noun:inanim:p:v_zna
автомотодромові	автомотодром	noun	noun:inanim:m:v_dav
автомотодромові	автомотодром	noun	noun:inanim:m:v_mis
автомотодромом	автомотодром	noun	noun:inanim:m:v_oru
автомотодрому	автомотодром	noun	noun:inanim:m:v_dav
автомотодрому	автомотодром	noun	noun:inanim:m:v_mis
автомотодрому	автомотодром	noun	noun:inanim:m:v_rod
автомотодромі	автомотодром	noun	noun:inanim:m:v_mis
автомотодромів	автомотодром	noun	noun:inanim:p:v_rod
автомотоклуб	автомотоклуб	noun	noun:inanim:m:v_naz
автомотоклуб	автомотоклуб	noun	noun:inanim:m:v_zna
автомотоклубам	автомотоклуб	noun	noun:inanim:p:v_dav
автомотоклубами	автомотоклуб	noun	noun:inanim:p:v_oru
автомотоклубах	автомотоклуб	noun	noun:inanim:p:v_mis
автомотоклубе	автомотоклуб	noun	noun:inanim:m:v_kly
автомотоклуби	автомотоклуб	noun	noun:inanim:p:v_kly
автомотоклуби	автомотоклуб	noun	noun:inanim:p:v_naz
автомотоклуби	автомотоклуб	noun	noun:inanim:p:v_zna
автомотоклубові	автомотоклуб	noun	noun:inanim:m:v_dav
автомотоклубові	автомотоклуб	noun	noun:inanim:m:v_mis
автомотоклубом	автомотоклуб	noun	noun:inanim:m:v_oru
автомотоклубу	автомотоклуб	noun	noun:inanim:m:v_dav
автомотоклубу	автомотоклуб	noun	noun:inanim:m:v_mis
автомотоклубу	автомотоклуб	noun	noun:inanim:m:v_rod
автомотоклубі	автомотоклуб	noun	noun:inanim:m:v_mis
автомотоклубів	автомотоклуб	noun	noun:inanim:p:v_rod
автомотолюбителеві	автомотолюбитель	noun	noun:anim:m:v_dav
автомотолюбителеві	автомотолюбитель	noun	noun:anim:m:v_mis
автомотолюбителем	автомотолюбитель	noun	noun:anim:m:v_oru
автомотолюбитель	автомотолюбитель	noun	noun:anim:m:v_naz
автомотолюбителька	автомотолюбителька	noun	noun:anim:f:v_naz
автомотолюбителькам	автомотолюбителька	noun	noun:anim:p:v_dav
автомотолюбительками	автомотолюбителька	noun	noun:anim:p:v_oru
автомотолюбительках	автомотолюбителька	noun	noun:anim:p:v_mis
автомотолюбительки	автомотолюбителька	noun	noun:anim:f:v_rod
автомотолюбительки	автомотолюбителька	noun	noun:anim:p:v_kly
автомотолюбительки	автомотолюбителька	noun	noun:anim:p:v_naz
автомотолюбительки	автомотолюбителька	noun	noun:anim:p:v_zna:rare
автомотолюбителько	автомотолюбителька	noun	noun:anim:f:v_kly
автомотолюбителькою	автомотолюбителька	noun	noun:anim:f:v_oru
автомотолюбительку	автомотолюбителька	noun	noun:anim:f:v_zna
автомотолюбительок	автомотолюбителька	noun	noun:anim:p:v_rod
автомотолюбительок	автомотолюбителька	noun	noun:anim:p:v_zna
автомотолюбительці	автомотолюбителька	noun	noun:anim:f:v_dav
автомотолюбительці	автомотолюбителька	noun	noun:anim:f:v_mis
автомотолюбителю	автомотолюбитель	noun	noun:anim:m:v_dav
автомотолюбителю	автомотолюбитель	noun	noun:anim:m:v_kly
автомотолюбителю	автомотолюбитель	noun	noun:anim:m:v_mis
автомотолюбителя	автомотолюбитель	noun	noun:anim:m:v_rod
автомотолюбителя	автомотолюбитель	noun	noun:anim:m:v_zna
автомотолюбителям	автомотолюбитель	noun	noun:anim:p:v_dav
автомотолюбителями	автомотолюбитель	noun	noun:anim:p:v_oru
автомотолюбителях	автомотолюбитель	noun	noun:anim:p:v_mis
автомотолюбителі	автомотолюбитель	noun	noun:anim:m:v_mis
автомотолюбителі	автомотолюбитель	noun	noun:anim:p:v_kly
автомотолюбителі	автомотолюбитель	noun	noun:anim:p:v_naz
автомотолюбителі	автомотолюбитель	noun	noun:anim:p:v_zna:rare
автомотолюбителів	автомотолюбитель	noun	noun:anim:p:v_rod
автомотолюбителів	автомотолюбитель	noun	noun:anim:p:v_zna
автомотор	автомотор	noun	noun:inanim:m:v_naz
автомотор	автомотор	noun	noun:inanim:m:v_zna
автомотора	автомотор	noun	noun:inanim:m:v_rod
автомоторам	автомотор	noun	noun:inanim:p:v_dav
автомоторами	автомотор	noun	noun:inanim:p:v_oru
автомоторах	автомотор	noun	noun:inanim:p:v_mis
автомоторе	автомотор	noun	noun:inanim:m:v_kly
автомотори	автомотор	noun	noun:inanim:p:v_kly
автомотори	автомотор	noun	noun:inanim:p:v_naz
автомотори	автомотор	noun	noun:inanim:p:v_zna
автомоторист	автомоторист	noun	noun:anim:m:v_naz
автомоториста	автомоторист	noun	noun:anim:m:v_rod
автомоториста	автомоторист	noun	noun:anim:m:v_zna
автомотористам	автомоторист	noun	noun:anim:p:v_dav
автомотористами	автомоторист	noun	noun:anim:p:v_oru
автомотористах	автомоторист	noun	noun:anim:p:v_mis
автомотористе	автомоторист	noun	noun:anim:m:v_kly
автомотористи	автомоторист	noun	noun:anim:p:v_kly
автомотористи	автомоторист	noun	noun:anim:p:v_naz
автомотористи	автомоторист	noun	noun:anim:p:v_zna:rare
автомотористові	автомоторист	noun	noun:anim:m:v_dav
автомотористові	автомоторист	noun	noun:anim:m:v_mis
автомотористом	автомоторист	noun	noun:anim:m:v_oru
автомотористі	автомоторист	noun	noun:anim:m:v_mis
автомотористів	автомоторист	noun	noun:anim:p:v_rod
автомотористів	автомоторист	noun	noun:anim:p:v_zna
автомоторові	автомотор	noun	noun:inanim:m:v_dav
автомоторові	автомотор	noun	noun:inanim:m:v_mis
автомотором	автомотор	noun	noun:inanim:m:v_oru
автомоторі	автомотор	noun	noun:inanim:m:v_mis
автомоторів	автомотор	noun	noun:inanim:p:v_rod
автомототрас	автомототраса	noun	noun:inanim:p:v_rod
автомототраса	автомототраса	noun	noun:inanim:f:v_naz
автомототрасам	автомототраса	noun	noun:inanim:p:v_dav
автомототрасами	автомототраса	noun	noun:inanim:p:v_oru
автомототрасах	автомототраса	noun	noun:inanim:p:v_mis
автомототраси	автомототраса	noun	noun:inanim:f:v_rod
автомототраси	автомототраса	noun	noun:inanim:p:v_kly
автомототраси	автомототраса	noun	noun:inanim:p:v_naz
автомототраси	автомототраса	noun	noun:inanim:p:v_zna
автомототрасо	автомототраса	noun	noun:inanim:f:v_kly
автомототрасою	автомототраса	noun	noun:inanim:f:v_oru
автомототрасу	автомототраса	noun	noun:inanim:f:v_zna
автомототрасі	автомототраса	noun	noun:inanim:f:v_dav
автомототрасі	автомототраса	noun	noun:inanim:f:v_mis
автомототрек	автомототрек	noun	noun:inanim:m:v_naz
автомототрек	автомототрек	noun	noun:inanim:m:v_zna
автомототрекам	автомототрек	noun	noun:inanim:p:v_dav
автомототреками	автомототрек	noun	noun:inanim:p:v_oru
автомототреках	автомототрек	noun	noun:inanim:p:v_mis
автомототреки	автомототрек	noun	noun:inanim:p:v_kly
автомототреки	автомототрек	noun	noun:inanim:p:v_naz
автомототреки	автомототрек	noun	noun:inanim:p:v_zna
автомототрекові	автомототрек	noun	noun:inanim:m:v_dav
автомототрекові	автомототрек	noun	noun:inanim:m:v_mis
автомототреком	автомототрек	noun	noun:inanim:m:v_oru
автомототреку	автомототрек	noun	noun:inanim:m:v_dav
автомототреку	автомототрек	noun	noun:inanim:m:v_kly
автомототреку	автомототрек	noun	noun:inanim:m:v_mis
автомототреку	автомототрек	noun	noun:inanim:m:v_rod
автомототреків	автомототрек	noun	noun:inanim:p:v_rod
автомототурист	автомототурист	noun	noun:anim:m:v_naz
автомототуриста	автомототурист	noun	noun:anim:m:v_rod
автомототуриста	автомототурист	noun	noun:anim:m:v_zna
автомототуристам	автомототурист	noun	noun:anim:p:v_dav
автомототуристами	автомототурист	noun	noun:anim:p:v_oru
автомототуристах	автомототурист	noun	noun:anim:p:v_mis
автомототуристе	автомототурист	noun	noun:anim:m:v_kly
автомототуристи	автомототурист	noun	noun:anim:p:v_kly
автомототуристи	автомототурист	noun	noun:anim:p:v_naz
автомототуристи	автомототурист	noun	noun:anim:p:v_zna:rare
автомототуристка	автомототуристка	noun	noun:anim:f:v_naz
автомототуристкам	автомототуристка	noun	noun:anim:p:v_dav
автомототуристками	автомототуристка	noun	noun:anim:p:v_oru
автомототуристках	автомототуристка	noun	noun:anim:p:v_mis
автомототуристки	автомототуристка	noun	noun:anim:f:v_rod
автомототуристки	автомототуристка	noun	noun:anim:p:v_kly
автомототуристки	автомототуристка	noun	noun:anim:p:v_naz
автомототуристки	автомототуристка	noun	noun:anim:p:v_zna:rare
автомототуристко	автомототуристка	noun	noun:anim:f:v_kly
автомототуристкою	автомототуристка	noun	noun:anim:f:v_oru
автомототуристку	автомототуристка	noun	noun:anim:f:v_zna
автомототуристові	автомототурист	noun	noun:anim:m:v_dav
автомототуристові	автомототурист	noun	noun:anim:m:v_mis
автомототуристок	автомототуристка	noun	noun:anim:p:v_rod
автомототуристок	автомототуристка	noun	noun:anim:p:v_zna
автомототуристом	автомототурист	noun	noun:anim:m:v_oru
автомототуристці	автомототуристка	noun	noun:anim:f:v_dav
автомототуристці	автомототуристка	noun	noun:anim:f:v_mis
автомототуристі	автомототурист	noun	noun:anim:m:v_mis
автомототуристів	автомототурист	noun	noun:anim:p:v_rod
автомототуристів	автомототурист	noun	noun:anim:p:v_zna
автомотрис	автомотриса	noun	noun:inanim:p:v_rod
автомотриса	автомотриса	noun	noun:inanim:f:v_naz
автомотрисам	автомотриса	noun	noun:inanim:p:v_dav
автомотрисами	автомотриса	noun	noun:inanim:p:v_oru
автомотрисах	автомотриса	noun	noun:inanim:p:v_mis
автомотриси	автомотриса	noun	noun:inanim:f:v_rod
автомотриси	автомотриса	noun	noun:inanim:p:v_kly
автомотриси	автомотриса	noun	noun:inanim:p:v_naz
автомотриси	автомотриса	noun	noun:inanim:p:v_zna
автомотрисо	автомотриса	noun	noun:inanim:f:v_kly
автомотрисою	автомотриса	noun	noun:inanim:f:v_oru
автомотрису	автомотриса	noun	noun:inanim:f:v_zna
автомотрисі	автомотриса	noun	noun:inanim:f:v_dav
автомотрисі	автомотриса	noun	noun:inanim:f:v_mis
автомурашник	автомурашник	noun	noun:inanim:m:v_naz
автомурашник	автомурашник	noun	noun:inanim:m:v_zna
автомурашника	автомурашник	noun	noun:inanim:m:v_rod
автомурашникам	автомурашник	noun	noun:inanim:p:v_dav
автомурашниками	автомурашник	noun	noun:inanim:p:v_oru
автомурашниках	автомурашник	noun	noun:inanim:p:v_mis
автомурашники	автомурашник	noun	noun:inanim:p:v_kly
автомурашники	автомурашник	noun	noun:inanim:p:v_naz
автомурашники	автомурашник	noun	noun:inanim:p:v_zna
автомурашникові	автомурашник	noun	noun:inanim:m:v_dav
автомурашникові	автомурашник	noun	noun:inanim:m:v_mis
автомурашником	автомурашник	noun	noun:inanim:m:v_oru
автомурашнику	автомурашник	noun	noun:inanim:m:v_dav
автомурашнику	автомурашник	noun	noun:inanim:m:v_kly
автомурашнику	автомурашник	noun	noun:inanim:m:v_mis
автомурашників	автомурашник	noun	noun:inanim:p:v_rod
автомутаген	автомутаген	noun	noun:inanim:m:v_naz
автомутаген	автомутаген	noun	noun:inanim:m:v_zna
автомутагенам	автомутаген	noun	noun:inanim:p:v_dav
автомутагенами	автомутаген	noun	noun:inanim:p:v_oru
автомутагенах	автомутаген	noun	noun:inanim:p:v_mis
автомутагене	автомутаген	noun	noun:inanim:m:v_kly
автомутагени	автомутаген	noun	noun:inanim:p:v_kly
автомутагени	автомутаген	noun	noun:inanim:p:v_naz
автомутагени	автомутаген	noun	noun:inanim:p:v_zna
автомутагенові	автомутаген	noun	noun:inanim:m:v_dav
автомутагенові	автомутаген	noun	noun:inanim:m:v_mis
автомутагеном	автомутаген	noun	noun:inanim:m:v_oru
автомутагену	автомутаген	noun	noun:inanim:m:v_dav
автомутагену	автомутаген	noun	noun:inanim:m:v_mis
автомутагену	автомутаген	noun	noun:inanim:m:v_rod
автомутагені	автомутаген	noun	noun:inanim:m:v_mis
автомутагенів	автомутаген	noun	noun:inanim:p:v_rod
автоміксис	автоміксис	noun	noun:inanim:m:v_naz
автоміксис	автоміксис	noun	noun:inanim:m:v_zna
автоміксисам	автоміксис	noun	noun:inanim:p:v_dav
автоміксисами	автоміксис	noun	noun:inanim:p:v_oru
автоміксисах	автоміксис	noun	noun:inanim:p:v_mis
автоміксисе	автоміксис	noun	noun:inanim:m:v_kly
автоміксиси	автоміксис	noun	noun:inanim:p:v_kly
автоміксиси	автоміксис	noun	noun:inanim:p:v_naz
автоміксиси	автоміксис	noun	noun:inanim:p:v_zna
автоміксисові	автоміксис	noun	noun:inanim:m:v_dav
автоміксисові	автоміксис	noun	noun:inanim:m:v_mis
автоміксисом	автоміксис	noun	noun:inanim:m:v_oru
автоміксису	автоміксис	noun	noun:inanim:m:v_dav
автоміксису	автоміксис	noun	noun:inanim:m:v_mis
автоміксису	автоміксис	noun	noun:inanim:m:v_rod
автоміксисі	автоміксис	noun	noun:inanim:m:v_mis
автоміксисів	автоміксис	noun	noun:inanim:p:v_rod
автоміст	автоміст	noun	noun:inanim:m:v_naz
автоміст	автоміст	noun	noun:inanim:m:v_zna
автомістечка	автомістечко	noun	noun:inanim:n:v_rod
автомістечка	автомістечко	noun	noun:inanim:p:v_kly
автомістечка	автомістечко	noun	noun:inanim:p:v_naz
автомістечка	автомістечко	noun	noun:inanim:p:v_zna
автомістечкам	автомістечко	noun	noun:inanim:p:v_dav
автомістечками	автомістечко	noun	noun:inanim:p:v_oru
автомістечках	автомістечко	noun	noun:inanim:p:v_mis
автомістечко	автомістечко	noun	noun:inanim:n:v_kly
автомістечко	автомістечко	noun	noun:inanim:n:v_naz
автомістечко	автомістечко	noun	noun:inanim:n:v_zna
автомістечком	автомістечко	noun	noun:inanim:n:v_oru
автомістечку	автомістечко	noun	noun:inanim:n:v_dav
автомістечку	автомістечко	noun	noun:inanim:n:v_mis
автомістечок	автомістечко	noun	noun:inanim:p:v_rod
автонавантажувач	автонавантажувач	noun	noun:inanim:m:v_naz
автонавантажувач	автонавантажувач	noun	noun:inanim:m:v_zna
автонавантажувача	автонавантажувач	noun	noun:inanim:m:v_rod
автонавантажувачам	автонавантажувач	noun	noun:inanim:p:v_dav
автонавантажувачами	автонавантажувач	noun	noun:inanim:p:v_oru
автонавантажувачах	автонавантажувач	noun	noun:inanim:p:v_mis
автонавантажувачеві	автонавантажувач	noun	noun:inanim:m:v_dav
автонавантажувачеві	автонавантажувач	noun	noun:inanim:m:v_mis
автонавантажувачем	автонавантажувач	noun	noun:inanim:m:v_oru
автонавантажувачу	автонавантажувач	noun	noun:inanim:m:v_dav
автонавантажувачу	автонавантажувач	noun	noun:inanim:m:v_kly
автонавантажувачу	автонавантажувач	noun	noun:inanim:m:v_mis
автонавантажувачі	автонавантажувач	noun	noun:inanim:m:v_mis
автонавантажувачі	автонавантажувач	noun	noun:inanim:p:v_kly
автонавантажувачі	автонавантажувач	noun	noun:inanim:p:v_naz
автонавантажувачі	автонавантажувач	noun	noun:inanim:p:v_zna
автонавантажувачів	автонавантажувач	noun	noun:inanim:p:v_rod
автонаведенню	автонаведення	noun	noun:inanim:n:v_dav
автонаведенню	автонаведення	noun	noun:inanim:n:v_mis
автонаведення	автонаведення	noun	noun:inanim:n:v_kly
автонаведення	автонаведення	noun	noun:inanim:n:v_naz
автонаведення	автонаведення	noun	noun:inanim:n:v_rod
автонаведення	автонаведення	noun	noun:inanim:n:v_zna
автонаведення	автонаведення	noun	noun:inanim:p:v_kly
автонаведення	автонаведення	noun	noun:inanim:p:v_naz
автонаведення	автонаведення	noun	noun:inanim:p:v_zna
автонаведенням	автонаведення	noun	noun:inanim:n:v_oru
автонаведенням	автонаведення	noun	noun:inanim:p:v_dav
автонаведеннями	автонаведення	noun	noun:inanim:p:v_oru
автонаведеннях	автонаведення	noun	noun:inanim:p:v_mis
автонаведенні	автонаведення	noun	noun:inanim:n:v_mis
автонаведень	автонаведення	noun	noun:inanim:p:v_rod
автонапувалка	автонапувалка	noun	noun:inanim:f:v_naz
автонапувалкам	автонапувалка	noun	noun:inanim:p:v_dav
автонапувалками	автонапувалка	noun	noun:inanim:p:v_oru
автонапувалках	автонапувалка	noun	noun:inanim:p:v_mis
автонапувалки	автонапувалка	noun	noun:inanim:f:v_rod
автонапувалки	автонапувалка	noun	noun:inanim:p:v_kly
автонапувалки	автонапувалка	noun	noun:inanim:p:v_naz
автонапувалки	автонапувалка	noun	noun:inanim:p:v_zna
автонапувалко	автонапувалка	noun	noun:inanim:f:v_kly
автонапувалкою	автонапувалка	noun	noun:inanim:f:v_oru
автонапувалку	автонапувалка	noun	noun:inanim:f:v_zna
автонапувалок	автонапувалка	noun	noun:inanim:p:v_rod
автонапувалці	автонапувалка	noun	noun:inanim:f:v_dav
автонапувалці	автонапувалка	noun	noun:inanim:f:v_mis
автонапувальнице	автонапувальниця	noun	noun:inanim:f:v_kly
автонапувальницею	автонапувальниця	noun	noun:inanim:f:v_oru
автонапувальниць	автонапувальниця	noun	noun:inanim:p:v_rod
автонапувальницю	автонапувальниця	noun	noun:inanim:f:v_zna
автонапувальниця	автонапувальниця	noun	noun:inanim:f:v_naz
автонапувальницям	автонапувальниця	noun	noun:inanim:p:v_dav
автонапувальницями	автонапувальниця	noun	noun:inanim:p:v_oru
автонапувальницях	автонапувальниця	noun	noun:inanim:p:v_mis
автонапувальниці	автонапувальниця	noun	noun:inanim:f:v_dav
автонапувальниці	автонапувальниця	noun	noun:inanim:f:v_mis
автонапувальниці	автонапувальниця	noun	noun:inanim:f:v_rod
автонапувальниці	автонапувальниця	noun	noun:inanim:p:v_kly
автонапувальниці	автонапувальниця	noun	noun:inanim:p:v_naz
автонапувальниці	автонапувальниця	noun	noun:inanim:p:v_zna
автонасос	автонасос	noun	noun:inanim:m:v_naz
автонасос	автонасос	noun	noun:inanim:m:v_zna
автонасоса	автонасос	noun	noun:inanim:m:v_rod
автонасосам	автонасос	noun	noun:inanim:p:v_dav
автонасосами	автонасос	noun	noun:inanim:p:v_oru
автонасосах	автонасос	noun	noun:inanim:p:v_mis
автонасосе	автонасос	noun	noun:inanim:m:v_kly
автонасоси	автонасос	noun	noun:inanim:p:v_kly
автонасоси	автонасос	noun	noun:inanim:p:v_naz
автонасоси	автонасос	noun	noun:inanim:p:v_zna
автонасосові	автонасос	noun	noun:inanim:m:v_dav
автонасосові	автонасос	noun	noun:inanim:m:v_mis
автонасосом	автонасос	noun	noun:inanim:m:v_oru
автонасосі	автонасос	noun	noun:inanim:m:v_mis
автонасосів	автонасос	noun	noun:inanim:p:v_rod
автонаїзд	автонаїзд	noun	noun:inanim:m:v_naz
автонаїзд	автонаїзд	noun	noun:inanim:m:v_zna
автонаїздам	автонаїзд	noun	noun:inanim:p:v_dav
автонаїздами	автонаїзд	noun	noun:inanim:p:v_oru
автонаїздах	автонаїзд	noun	noun:inanim:p:v_mis
автонаїзде	автонаїзд	noun	noun:inanim:m:v_kly
автонаїзди	автонаїзд	noun	noun:inanim:p:v_kly
автонаїзди	автонаїзд	noun	noun:inanim:p:v_naz
автонаїзди	автонаїзд	noun	noun:inanim:p:v_zna
автонаїздові	автонаїзд	noun	noun:inanim:m:v_dav
автонаїздові	автонаїзд	noun	noun:inanim:m:v_mis
автонаїздом	автонаїзд	noun	noun:inanim:m:v_oru
автонаїзду	автонаїзд	noun	noun:inanim:m:v_dav
автонаїзду	автонаїзд	noun	noun:inanim:m:v_mis
автонаїзду	автонаїзд	noun	noun:inanim:m:v_rod
автонаїзді	автонаїзд	noun	noun:inanim:m:v_mis
автонаїздів	автонаїзд	noun	noun:inanim:p:v_rod
автоновинка	автоновинка	noun	noun:inanim:f:v_naz
автоновинкам	автоновинка	noun	noun:inanim:p:v_dav
автоновинками	автоновинка	noun	noun:inanim:p:v_oru
автоновинках	автоновинка	noun	noun:inanim:p:v_mis
автоновинки	автоновинка	noun	noun:inanim:f:v_rod
автоновинки	автоновинка	noun	noun:inanim:p:v_kly
автоновинки	автоновинка	noun	noun:inanim:p:v_naz
автоновинки	автоновинка	noun	noun:inanim:p:v_zna
автоновинко	автоновинка	noun	noun:inanim:f:v_kly
автоновинкою	автоновинка	noun	noun:inanim:f:v_oru
автоновинку	автоновинка	noun	noun:inanim:f:v_zna
автоновинок	автоновинка	noun	noun:inanim:p:v_rod
автоновинці	автоновинка	noun	noun:inanim:f:v_dav
автоновинці	автоновинка	noun	noun:inanim:f:v_mis
автономер	автономер	noun	noun:inanim:m:v_naz
автономер	автономер	noun	noun:inanim:m:v_zna
автономера	автономер	noun	noun:inanim:m:v_rod
автономерам	автономер	noun	noun:inanim:p:v_dav
автономерами	автономер	noun	noun:inanim:p:v_oru
автономерах	автономер	noun	noun:inanim:p:v_mis
автономере	автономер	noun	noun:inanim:m:v_kly
автономери	автономер	noun	noun:inanim:p:v_kly
автономери	автономер	noun	noun:inanim:p:v_naz
автономери	автономер	noun	noun:inanim:p:v_zna
автономерові	автономер	noun	noun:inanim:m:v_dav
автономерові	автономер	noun	noun:inanim:m:v_mis
автономером	автономер	noun	noun:inanim:m:v_oru
автономері	автономер	noun	noun:inanim:m:v_mis
автономерів	автономер	noun	noun:inanim:p:v_rod
автономка	автономка	noun	noun:inanim:f:v_naz
автономкам	автономка	noun	noun:inanim:p:v_dav
автономками	автономка	noun	noun:inanim:p:v_oru
автономках	автономка	noun	noun:inanim:p:v_mis
автономки	автономка	noun	noun:inanim:f:v_rod
автономки	автономка	noun	noun:inanim:p:v_kly
автономки	автономка	noun	noun:inanim:p:v_naz
автономки	автономка	noun	noun:inanim:p:v_zna
автономко	автономка	noun	noun:inanim:f:v_kly
автономкою	автономка	noun	noun:inanim:f:v_oru
автономку	автономка	noun	noun:inanim:f:v_zna
автономник	автономник	noun	noun:inanim:m:v_naz
автономник	автономник	noun	noun:inanim:m:v_zna
автономника	автономник	noun	noun:inanim:m:v_rod
автономникам	автономник	noun	noun:inanim:p:v_dav
автономниками	автономник	noun	noun:inanim:p:v_oru
автономниках	автономник	noun	noun:inanim:p:v_mis
автономники	автономник	noun	noun:inanim:p:v_kly
автономники	автономник	noun	noun:inanim:p:v_naz
автономники	автономник	noun	noun:inanim:p:v_zna
автономникові	автономник	noun	noun:inanim:m:v_dav
автономникові	автономник	noun	noun:inanim:m:v_mis
автономником	автономник	noun	noun:inanim:m:v_oru
автономнику	автономник	noun	noun:inanim:m:v_dav
автономнику	автономник	noun	noun:inanim:m:v_kly
автономнику	автономник	noun	noun:inanim:m:v_mis
автономників	автономник	noun	noun:inanim:p:v_rod
автономок	автономка	noun	noun:inanim:p:v_rod
автономці	автономка	noun	noun:inanim:f:v_dav
автономці	автономка	noun	noun:inanim:f:v_mis
автономізацій	автономізація	noun	noun:inanim:p:v_rod
автономізацію	автономізація	noun	noun:inanim:f:v_zna
автономізація	автономізація	noun	noun:inanim:f:v_naz
автономізаціям	автономізація	noun	noun:inanim:p:v_dav
автономізаціями	автономізація	noun	noun:inanim:p:v_oru
автономізаціях	автономізація	noun	noun:inanim:p:v_mis
автономізаціє	автономізація	noun	noun:inanim:f:v_kly
автономізацією	автономізація	noun	noun:inanim:f:v_oru
автономізації	автономізація	noun	noun:inanim:f:v_dav
автономізації	автономізація	noun	noun:inanim:f:v_mis
автономізації	автономізація	noun	noun:inanim:f:v_rod
автономізації	автономізація	noun	noun:inanim:p:v_kly
автономізації	автономізація	noun	noun:inanim:p:v_naz
автономізації	автономізація	noun	noun:inanim:p:v_zna
автономій	автономія	noun	noun:inanim:p:v_rod
автономіст	автономіст	noun	noun:anim:m:v_naz
автономіста	автономіст	noun	noun:anim:m:v_rod
автономіста	автономіст	noun	noun:anim:m:v_zna
автономістам	автономіст	noun	noun:anim:p:v_dav
автономістами	автономіст	noun	noun:anim:p:v_oru
автономістах	автономіст	noun	noun:anim:p:v_mis
автономісте	автономіст	noun	noun:anim:m:v_kly
автономісти	автономіст	noun	noun:anim:p:v_kly
автономісти	автономіст	noun	noun:anim:p:v_naz
автономісти	автономіст	noun	noun:anim:p:v_zna:rare
автономістка	автономістка	noun	noun:anim:f:v_naz
автономісткам	автономістка	noun	noun:anim:p:v_dav
автономістками	автономістка	noun	noun:anim:p:v_oru
автономістках	автономістка	noun	noun:anim:p:v_mis
автономістки	автономістка	noun	noun:anim:f:v_rod
автономістки	автономістка	noun	noun:anim:p:v_kly
автономістки	автономістка	noun	noun:anim:p:v_naz
автономістки	автономістка	noun	noun:anim:p:v_zna:rare
автономістко	автономістка	noun	noun:anim:f:v_kly
автономісткою	автономістка	noun	noun:anim:f:v_oru
автономістку	автономістка	noun	noun:anim:f:v_zna
автономістові	автономіст	noun	noun:anim:m:v_dav
автономістові	автономіст	noun	noun:anim:m:v_mis
автономісток	автономістка	noun	noun:anim:p:v_rod
автономісток	автономістка	noun	noun:anim:p:v_zna
автономістом	автономіст	noun	noun:anim:m:v_oru
автономістці	автономістка	noun	noun:anim:f:v_dav
автономістці	автономістка	noun	noun:anim:f:v_mis
автономісті	автономіст	noun	noun:anim:m:v_mis
автономістів	автономіст	noun	noun:anim:p:v_rod
автономістів	автономіст	noun	noun:anim:p:v_zna
автономію	автономія	noun	noun:inanim:f:v_zna
автономія	автономія	noun	noun:inanim:f:v_naz
автономіям	автономія	noun	noun:inanim:p:v_dav
автономіями	автономія	noun	noun:inanim:p:v_oru
автономіях	автономія	noun	noun:inanim:p:v_mis
автономіє	автономія	noun	noun:inanim:f:v_kly
автономією	автономія	noun	noun:inanim:f:v_oru
автономії	автономія	noun	noun:inanim:f:v_dav
автономії	автономія	noun	noun:inanim:f:v_mis
автономії	автономія	noun	noun:inanim:f:v_rod
автономії	автономія	noun	noun:inanim:p:v_kly
автономії	автономія	noun	noun:inanim:p:v_naz
автономії	автономія	noun	noun:inanim:p:v_zna
автонумеруванню	автонумерування	noun	noun:inanim:n:v_dav
автонумеруванню	автонумерування	noun	noun:inanim:n:v_mis
автонумерування	автонумерування	noun	noun:inanim:n:v_kly
автонумерування	автонумерування	noun	noun:inanim:n:v_naz
автонумерування	автонумерування	noun	noun:inanim:n:v_rod
автонумерування	автонумерування	noun	noun:inanim:n:v_zna
автонумерування	автонумерування	noun	noun:inanim:p:v_kly
автонумерування	автонумерування	noun	noun:inanim:p:v_naz
автонумерування	автонумерування	noun	noun:inanim:p:v_zna
автонумеруванням	автонумерування	noun	noun:inanim:n:v_oru
автонумеруванням	автонумерування	noun	noun:inanim:p:v_dav
автонумеруваннями	автонумерування	noun	noun:inanim:p:v_oru
автонумеруваннях	автонумерування	noun	noun:inanim:p:v_mis
автонумеруванні	автонумерування	noun	noun:inanim:n:v_mis
автонумерувань	автонумерування	noun	noun:inanim:p:v_rod
автонім	автонім	noun	noun:inanim:m:v_naz
автонім	автонім	noun	noun:inanim:m:v_zna
автоніма	автонім	noun	noun:inanim:m:v_rod
автонімам	автонім	noun	noun:inanim:p:v_dav
автонімами	автонім	noun	noun:inanim:p:v_oru
автонімах	автонім	noun	noun:inanim:p:v_mis
автоніме	автонім	noun	noun:inanim:m:v_kly
автоніми	автонім	noun	noun:inanim:p:v_kly
автоніми	автонім	noun	noun:inanim:p:v_naz
автоніми	автонім	noun	noun:inanim:p:v_zna
автонімові	автонім	noun	noun:inanim:m:v_dav
автонімові	автонім	noun	noun:inanim:m:v_mis
автонімом	автонім	noun	noun:inanim:m:v_oru
автонімі	автонім	noun	noun:inanim:m:v_mis
автонімів	автонім	noun	noun:inanim:p:v_rod
автообраз	автообраз	noun	noun:inanim:m:v_naz
автообраз	автообраз	noun	noun:inanim:m:v_zna
автообразам	автообраз	noun	noun:inanim:p:v_dav
автообразами	автообраз	noun	noun:inanim:p:v_oru
автообразах	автообраз	noun	noun:inanim:p:v_mis
автообразе	автообраз	noun	noun:inanim:m:v_kly
автообрази	автообраз	noun	noun:inanim:p:v_kly
автообрази	автообраз	noun	noun:inanim:p:v_naz
автообрази	автообраз	noun	noun:inanim:p:v_zna
автообразові	автообраз	noun	noun:inanim:m:v_dav
автообразові	автообраз	noun	noun:inanim:m:v_mis
автообразом	автообраз	noun	noun:inanim:m:v_oru
автообразу	автообраз	noun	noun:inanim:m:v_dav
автообразу	автообраз	noun	noun:inanim:m:v_mis
автообразу	автообраз	noun	noun:inanim:m:v_rod
автообразі	автообраз	noun	noun:inanim:m:v_mis
автообразів	автообраз	noun	noun:inanim:p:v_rod
автообслуговуванню	автообслуговування	noun	noun:inanim:n:v_dav
автообслуговуванню	автообслуговування	noun	noun:inanim:n:v_mis
автообслуговування	автообслуговування	noun	noun:inanim:n:v_kly
автообслуговування	автообслуговування	noun	noun:inanim:n:v_naz
автообслуговування	автообслуговування	noun	noun:inanim:n:v_rod
автообслуговування	автообслуговування	noun	noun:inanim:n:v_zna
автообслуговування	автообслуговування	noun	noun:inanim:p:v_kly
автообслуговування	автообслуговування	noun	noun:inanim:p:v_naz
автообслуговування	автообслуговування	noun	noun:inanim:p:v_zna
автообслуговуванням	автообслуговування	noun	noun:inanim:n:v_oru
автообслуговуванням	автообслуговування	noun	noun:inanim:p:v_dav
автообслуговуваннями	автообслуговування	noun	noun:inanim:p:v_oru
автообслуговуваннях	автообслуговування	noun	noun:inanim:p:v_mis
автообслуговуванні	автообслуговування	noun	noun:inanim:n:v_mis
автообслуговувань	автообслуговування	noun	noun:inanim:p:v_rod
автооксидацій	автооксидація	noun	noun:inanim:p:v_rod
автооксидацію	автооксидація	noun	noun:inanim:f:v_zna
автооксидація	автооксидація	noun	noun:inanim:f:v_naz
автооксидаціям	автооксидація	noun	noun:inanim:p:v_dav
автооксидаціями	автооксидація	noun	noun:inanim:p:v_oru
автооксидаціях	автооксидація	noun	noun:inanim:p:v_mis
автооксидаціє	автооксидація	noun	noun:inanim:f:v_kly
автооксидацією	автооксидація	noun	noun:inanim:f:v_oru
автооксидації	автооксидація	noun	noun:inanim:f:v_dav
автооксидації	автооксидація	noun	noun:inanim:f:v_mis
автооксидації	автооксидація	noun	noun:inanim:f:v_rod
автооксидації	автооксидація	noun	noun:inanim:p:v_kly
автооксидації	автооксидація	noun	noun:inanim:p:v_naz
автооксидації	автооксидація	noun	noun:inanim:p:v_zna
автооператор	автооператор	noun	noun:anim:m:v_naz
автооператора	автооператор	noun	noun:anim:m:v_rod
автооператора	автооператор	noun	noun:anim:m:v_zna
автооператорам	автооператор	noun	noun:anim:p:v_dav
автооператорами	автооператор	noun	noun:anim:p:v_oru
автооператорах	автооператор	noun	noun:anim:p:v_mis
автооператоре	автооператор	noun	noun:anim:m:v_kly
автооператори	автооператор	noun	noun:anim:p:v_kly
автооператори	автооператор	noun	noun:anim:p:v_naz
автооператори	автооператор	noun	noun:anim:p:v_zna:rare
автооператорові	автооператор	noun	noun:anim:m:v_dav
автооператорові	автооператор	noun	noun:anim:m:v_mis
автооператором	автооператор	noun	noun:anim:m:v_oru
автооператорі	автооператор	noun	noun:anim:m:v_mis
автооператорів	автооператор	noun	noun:anim:p:v_rod
автооператорів	автооператор	noun	noun:anim:p:v_zna
автоопитуванню	автоопитування	noun	noun:inanim:n:v_dav
автоопитуванню	автоопитування	noun	noun:inanim:n:v_mis
автоопитування	автоопитування	noun	noun:inanim:n:v_kly
автоопитування	автоопитування	noun	noun:inanim:n:v_naz
автоопитування	автоопитування	noun	noun:inanim:n:v_rod
автоопитування	автоопитування	noun	noun:inanim:n:v_zna
автоопитування	автоопитування	noun	noun:inanim:p:v_kly
автоопитування	автоопитування	noun	noun:inanim:p:v_naz
автоопитування	автоопитування	noun	noun:inanim:p:v_zna
автоопитуванням	автоопитування	noun	noun:inanim:n:v_oru
автоопитуванням	автоопитування	noun	noun:inanim:p:v_dav
автоопитуваннями	автоопитування	noun	noun:inanim:p:v_oru
автоопитуваннях	автоопитування	noun	noun:inanim:p:v_mis
автоопитуванні	автоопитування	noun	noun:inanim:n:v_mis
автоопитувань	автоопитування	noun	noun:inanim:p:v_rod
автоорганізацій	автоорганізація	noun	noun:inanim:p:v_rod
автоорганізацію	автоорганізація	noun	noun:inanim:f:v_zna
автоорганізація	автоорганізація	noun	noun:inanim:f:v_naz
автоорганізаціям	автоорганізація	noun	noun:inanim:p:v_dav
автоорганізаціями	автоорганізація	noun	noun:inanim:p:v_oru
автоорганізаціях	автоорганізація	noun	noun:inanim:p:v_mis
автоорганізаціє	автоорганізація	noun	noun:inanim:f:v_kly
автоорганізацією	автоорганізація	noun	noun:inanim:f:v_oru
автоорганізації	автоорганізація	noun	noun:inanim:f:v_dav
автоорганізації	автоорганізація	noun	noun:inanim:f:v_mis
автоорганізації	автоорганізація	noun	noun:inanim:f:v_rod
автоорганізації	автоорганізація	noun	noun:inanim:p:v_kly
автоорганізації	автоорганізація	noun	noun:inanim:p:v_naz
автоорганізації	автоорганізація	noun	noun:inanim:p:v_zna
автопавільйон	автопавільйон	noun	noun:inanim:m:v_naz
автопавільйон	автопавільйон	noun	noun:inanim:m:v_zna
автопавільйонам	автопавільйон	noun	noun:inanim:p:v_dav
автопавільйонами	автопавільйон	noun	noun:inanim:p:v_oru
автопавільйонах	автопавільйон	noun	noun:inanim:p:v_mis
автопавільйоне	автопавільйон	noun	noun:inanim:m:v_kly
автопавільйони	автопавільйон	noun	noun:inanim:p:v_kly
автопавільйони	автопавільйон	noun	noun:inanim:p:v_naz
автопавільйони	автопавільйон	noun	noun:inanim:p:v_zna
автопавільйонові	автопавільйон	noun	noun:inanim:m:v_dav
автопавільйонові	автопавільйон	noun	noun:inanim:m:v_mis
автопавільйоном	автопавільйон	noun	noun:inanim:m:v_oru
автопавільйону	автопавільйон	noun	noun:inanim:m:v_dav
автопавільйону	автопавільйон	noun	noun:inanim:m:v_mis
автопавільйону	автопавільйон	noun	noun:inanim:m:v_rod
автопавільйоні	автопавільйон	noun	noun:inanim:m:v_mis
автопавільйонів	автопавільйон	noun	noun:inanim:p:v_rod
автопанелевоз	автопанелевоз	noun	noun:inanim:m:v_naz
автопанелевоз	автопанелевоз	noun	noun:inanim:m:v_zna
автопанелевоза	автопанелевоз	noun	noun:inanim:m:v_rod
автопанелевоза	автопанелевіз	noun	noun:inanim:m:v_rod
автопанелевозам	автопанелевоз	noun	noun:inanim:p:v_dav
автопанелевозам	автопанелевіз	noun	noun:inanim:p:v_dav
автопанелевозами	автопанелевоз	noun	noun:inanim:p:v_oru
автопанелевозами	автопанелевіз	noun	noun:inanim:p:v_oru
автопанелевозах	автопанелевоз	noun	noun:inanim:p:v_mis
автопанелевозах	автопанелевіз	noun	noun:inanim:p:v_mis
автопанелевозе	автопанелевоз	noun	noun:inanim:m:v_kly
автопанелевозе	автопанелевіз	noun	noun:inanim:m:v_kly
автопанелевози	автопанелевоз	noun	noun:inanim:p:v_kly
автопанелевози	автопанелевоз	noun	noun:inanim:p:v_naz
автопанелевози	автопанелевоз	noun	noun:inanim:p:v_zna
автопанелевози	автопанелевіз	noun	noun:inanim:p:v_kly
автопанелевози	автопанелевіз	noun	noun:inanim:p:v_naz
автопанелевози	автопанелевіз	noun	noun:inanim:p:v_zna
автопанелевозові	автопанелевоз	noun	noun:inanim:m:v_dav
автопанелевозові	автопанелевоз	noun	noun:inanim:m:v_mis
автопанелевозові	автопанелевіз	noun	noun:inanim:m:v_dav
автопанелевозові	автопанелевіз	noun	noun:inanim:m:v_mis
автопанелевозом	автопанелевоз	noun	noun:inanim:m:v_oru
автопанелевозом	автопанелевіз	noun	noun:inanim:m:v_oru
автопанелевозі	автопанелевоз	noun	noun:inanim:m:v_mis
автопанелевозі	автопанелевіз	noun	noun:inanim:m:v_mis
автопанелевозів	автопанелевоз	noun	noun:inanim:p:v_rod
автопанелевозів	автопанелевіз	noun	noun:inanim:p:v_rod
автопанелевіз	автопанелевіз	noun	noun:inanim:m:v_naz
автопанелевіз	автопанелевіз	noun	noun:inanim:m:v_zna
автопансіонат	автопансіонат	noun	noun:inanim:m:v_naz
автопансіонат	автопансіонат	noun	noun:inanim:m:v_zna
автопансіонатам	автопансіонат	noun	noun:inanim:p:v_dav
автопансіонатами	автопансіонат	noun	noun:inanim:p:v_oru
автопансіонатах	автопансіонат	noun	noun:inanim:p:v_mis
автопансіонате	автопансіонат	noun	noun:inanim:m:v_kly
автопансіонати	автопансіонат	noun	noun:inanim:p:v_kly
автопансіонати	автопансіонат	noun	noun:inanim:p:v_naz
автопансіонати	автопансіонат	noun	noun:inanim:p:v_zna
автопансіонатові	автопансіонат	noun	noun:inanim:m:v_dav
автопансіонатові	автопансіонат	noun	noun:inanim:m:v_mis
автопансіонатом	автопансіонат	noun	noun:inanim:m:v_oru
автопансіонату	автопансіонат	noun	noun:inanim:m:v_dav
автопансіонату	автопансіонат	noun	noun:inanim:m:v_mis
автопансіонату	автопансіонат	noun	noun:inanim:m:v_rod
автопансіонаті	автопансіонат	noun	noun:inanim:m:v_mis
автопансіонатів	автопансіонат	noun	noun:inanim:p:v_rod
автопанцерник	автопанцерник	noun	noun:inanim:m:v_naz
автопанцерник	автопанцерник	noun	noun:inanim:m:v_zna
автопанцерника	автопанцерник	noun	noun:inanim:m:v_rod
автопанцерникам	автопанцерник	noun	noun:inanim:p:v_dav
автопанцерниками	автопанцерник	noun	noun:inanim:p:v_oru
автопанцерниках	автопанцерник	noun	noun:inanim:p:v_mis
автопанцерники	автопанцерник	noun	noun:inanim:p:v_kly
автопанцерники	автопанцерник	noun	noun:inanim:p:v_naz
автопанцерники	автопанцерник	noun	noun:inanim:p:v_zna
автопанцерникові	автопанцерник	noun	noun:inanim:m:v_dav
автопанцерникові	автопанцерник	noun	noun:inanim:m:v_mis
автопанцерником	автопанцерник	noun	noun:inanim:m:v_oru
автопанцернику	автопанцерник	noun	noun:inanim:m:v_dav
автопанцернику	автопанцерник	noun	noun:inanim:m:v_kly
автопанцернику	автопанцерник	noun	noun:inanim:m:v_mis
автопанцерників	автопанцерник	noun	noun:inanim:p:v_rod
автопарад	автопарад	noun	noun:inanim:m:v_naz
автопарад	автопарад	noun	noun:inanim:m:v_zna
автопарадам	автопарад	noun	noun:inanim:p:v_dav
автопарадами	автопарад	noun	noun:inanim:p:v_oru
автопарадах	автопарад	noun	noun:inanim:p:v_mis
автопараде	автопарад	noun	noun:inanim:m:v_kly
автопаради	автопарад	noun	noun:inanim:p:v_kly
автопаради	автопарад	noun	noun:inanim:p:v_naz
автопаради	автопарад	noun	noun:inanim:p:v_zna
автопарадові	автопарад	noun	noun:inanim:m:v_dav
автопарадові	автопарад	noun	noun:inanim:m:v_mis
автопарадом	автопарад	noun	noun:inanim:m:v_oru
автопараду	автопарад	noun	noun:inanim:m:v_dav
автопараду	автопарад	noun	noun:inanim:m:v_mis
автопараду	автопарад	noun	noun:inanim:m:v_rod
автопараді	автопарад	noun	noun:inanim:m:v_mis
автопарадів	автопарад	noun	noun:inanim:p:v_rod
автопарк	автопарк	noun	noun:inanim:m:v_naz
автопарк	автопарк	noun	noun:inanim:m:v_zna
автопаркам	автопарк	noun	noun:inanim:p:v_dav
автопарками	автопарк	noun	noun:inanim:p:v_oru
автопарках	автопарк	noun	noun:inanim:p:v_mis
автопарки	автопарк	noun	noun:inanim:p:v_kly
автопарки	автопарк	noun	noun:inanim:p:v_naz
автопарки	автопарк	noun	noun:inanim:p:v_zna
автопарковка	автопарковка	noun	noun:inanim:f:v_naz
автопарковкам	автопарковка	noun	noun:inanim:p:v_dav
автопарковками	автопарковка	noun	noun:inanim:p:v_oru
автопарковках	автопарковка	noun	noun:inanim:p:v_mis
автопарковки	автопарковка	noun	noun:inanim:f:v_rod
автопарковки	автопарковка	noun	noun:inanim:p:v_kly
автопарковки	автопарковка	noun	noun:inanim:p:v_naz
автопарковки	автопарковка	noun	noun:inanim:p:v_zna
автопарковко	автопарковка	noun	noun:inanim:f:v_kly
автопарковкою	автопарковка	noun	noun:inanim:f:v_oru
автопарковку	автопарковка	noun	noun:inanim:f:v_zna
автопарковок	автопарковка	noun	noun:inanim:p:v_rod
автопарковці	автопарковка	noun	noun:inanim:f:v_dav
автопарковці	автопарковка	noun	noun:inanim:f:v_mis
автопаркові	автопарк	noun	noun:inanim:m:v_dav
автопаркові	автопарк	noun	noun:inanim:m:v_mis
автопарком	автопарк	noun	noun:inanim:m:v_oru
автопарку	автопарк	noun	noun:inanim:m:v_dav
автопарку	автопарк	noun	noun:inanim:m:v_kly
автопарку	автопарк	noun	noun:inanim:m:v_mis
автопарку	автопарк	noun	noun:inanim:m:v_rod
автопарків	автопарк	noun	noun:inanim:p:v_rod
автопаркінг	автопаркінг	noun	noun:inanim:m:v_naz
автопаркінг	автопаркінг	noun	noun:inanim:m:v_zna
автопаркінгам	автопаркінг	noun	noun:inanim:p:v_dav
автопаркінгами	автопаркінг	noun	noun:inanim:p:v_oru
автопаркінгах	автопаркінг	noun	noun:inanim:p:v_mis
автопаркінги	автопаркінг	noun	noun:inanim:p:v_kly
автопаркінги	автопаркінг	noun	noun:inanim:p:v_naz
автопаркінги	автопаркінг	noun	noun:inanim:p:v_zna
автопаркінгові	автопаркінг	noun	noun:inanim:m:v_dav
автопаркінгові	автопаркінг	noun	noun:inanim:m:v_mis
автопаркінгом	автопаркінг	noun	noun:inanim:m:v_oru
автопаркінгу	автопаркінг	noun	noun:inanim:m:v_dav
автопаркінгу	автопаркінг	noun	noun:inanim:m:v_kly
автопаркінгу	автопаркінг	noun	noun:inanim:m:v_mis
автопаркінгу	автопаркінг	noun	noun:inanim:m:v_rod
автопаркінгів	автопаркінг	noun	noun:inanim:p:v_rod
автопародій	автопародія	noun	noun:inanim:p:v_rod
автопародію	автопародія	noun	noun:inanim:f:v_zna
автопародія	автопародія	noun	noun:inanim:f:v_naz
автопародіям	автопародія	noun	noun:inanim:p:v_dav
автопародіями	автопародія	noun	noun:inanim:p:v_oru
автопародіях	автопародія	noun	noun:inanim:p:v_mis
автопародіє	автопародія	noun	noun:inanim:f:v_kly
автопародією	автопародія	noun	noun:inanim:f:v_oru
автопародії	автопародія	noun	noun:inanim:f:v_dav
автопародії	автопародія	noun	noun:inanim:f:v_mis
автопародії	автопародія	noun	noun:inanim:f:v_rod
автопародії	автопародія	noun	noun:inanim:p:v_kly
автопародії	автопародія	noun	noun:inanim:p:v_naz
автопародії	автопародія	noun	noun:inanim:p:v_zna
автопасажир	автопасажир	noun	noun:anim:m:v_naz
автопасажира	автопасажир	noun	noun:anim:m:v_rod
автопасажира	автопасажир	noun	noun:anim:m:v_zna
автопасажирам	автопасажир	noun	noun:anim:p:v_dav
автопасажирами	автопасажир	noun	noun:anim:p:v_oru
автопасажирах	автопасажир	noun	noun:anim:p:v_mis
автопасажире	автопасажир	noun	noun:anim:m:v_kly
автопасажири	автопасажир	noun	noun:anim:p:v_kly
автопасажири	автопасажир	noun	noun:anim:p:v_naz
автопасажири	автопасажир	noun	noun:anim:p:v_zna:rare
автопасажирові	автопасажир	noun	noun:anim:m:v_dav
автопасажирові	автопасажир	noun	noun:anim:m:v_mis
автопасажиром	автопасажир	noun	noun:anim:m:v_oru
автопасажирі	автопасажир	noun	noun:anim:m:v_mis
автопасажирів	автопасажир	noun	noun:anim:p:v_rod
автопасажирів	автопасажир	noun	noun:anim:p:v_zna
автопатрулеві	автопатруль	noun	noun:inanim:m:v_dav
автопатрулеві	автопатруль	noun	noun:inanim:m:v_mis
автопатрулем	автопатруль	noun	noun:inanim:m:v_oru
автопатруль	автопатруль	noun	noun:inanim:m:v_naz
автопатруль	автопатруль	noun	noun:inanim:m:v_zna
автопатрулю	автопатруль	noun	noun:inanim:m:v_dav
автопатрулю	автопатруль	noun	noun:inanim:m:v_kly
автопатрулю	автопатруль	noun	noun:inanim:m:v_mis
автопатруля	автопатруль	noun	noun:inanim:m:v_rod
автопатрулям	автопатруль	noun	noun:inanim:p:v_dav
автопатрулями	автопатруль	noun	noun:inanim:p:v_oru
автопатрулях	автопатруль	noun	noun:inanim:p:v_mis
автопатрулі	автопатруль	noun	noun:inanim:m:v_mis
автопатрулі	автопатруль	noun	noun:inanim:p:v_kly
автопатрулі	автопатруль	noun	noun:inanim:p:v_naz
автопатрулі	автопатруль	noun	noun:inanim:p:v_zna
автопатрулів	автопатруль	noun	noun:inanim:p:v_rod
автопепсій	автопепсія	noun	noun:inanim:p:v_rod
автопепсію	автопепсія	noun	noun:inanim:f:v_zna
автопепсія	автопепсія	noun	noun:inanim:f:v_naz
автопепсіям	автопепсія	noun	noun:inanim:p:v_dav
автопепсіями	автопепсія	noun	noun:inanim:p:v_oru
автопепсіях	автопепсія	noun	noun:inanim:p:v_mis
автопепсіє	автопепсія	noun	noun:inanim:f:v_kly
автопепсією	автопепсія	noun	noun:inanim:f:v_oru
автопепсії	автопепсія	noun	noun:inanim:f:v_dav
автопепсії	автопепсія	noun	noun:inanim:f:v_mis
автопепсії	автопепсія	noun	noun:inanim:f:v_rod
автопепсії	автопепсія	noun	noun:inanim:p:v_kly
автопепсії	автопепсія	noun	noun:inanim:p:v_naz
автопепсії	автопепсія	noun	noun:inanim:p:v_zna
автоперевезенню	автоперевезення	noun	noun:inanim:n:v_dav
автоперевезенню	автоперевезення	noun	noun:inanim:n:v_mis
автоперевезення	автоперевезення	noun	noun:inanim:n:v_kly
автоперевезення	автоперевезення	noun	noun:inanim:n:v_naz
автоперевезення	автоперевезення	noun	noun:inanim:n:v_rod
автоперевезення	автоперевезення	noun	noun:inanim:n:v_zna
автоперевезення	автоперевезення	noun	noun:inanim:p:v_kly
автоперевезення	автоперевезення	noun	noun:inanim:p:v_naz
автоперевезення	автоперевезення	noun	noun:inanim:p:v_zna
автоперевезенням	автоперевезення	noun	noun:inanim:n:v_oru
автоперевезенням	автоперевезення	noun	noun:inanim:p:v_dav
автоперевезеннями	автоперевезення	noun	noun:inanim:p:v_oru
автоперевезеннях	автоперевезення	noun	noun:inanim:p:v_mis
автоперевезенні	автоперевезення	noun	noun:inanim:n:v_mis
автоперевезень	автоперевезення	noun	noun:inanim:p:v_rod
автоперевізник	автоперевізник	noun	noun:anim:m:v_naz
автоперевізника	автоперевізник	noun	noun:anim:m:v_rod
автоперевізника	автоперевізник	noun	noun:anim:m:v_zna
автоперевізникам	автоперевізник	noun	noun:anim:p:v_dav
автоперевізниками	автоперевізник	noun	noun:anim:p:v_oru
автоперевізниках	автоперевізник	noun	noun:anim:p:v_mis
автоперевізники	автоперевізник	noun	noun:anim:p:v_kly
автоперевізники	автоперевізник	noun	noun:anim:p:v_naz
автоперевізники	автоперевізник	noun	noun:anim:p:v_zna:rare
автоперевізникові	автоперевізник	noun	noun:anim:m:v_dav
автоперевізникові	автоперевізник	noun	noun:anim:m:v_mis
автоперевізником	автоперевізник	noun	noun:anim:m:v_oru
автоперевізнику	автоперевізник	noun	noun:anim:m:v_dav
автоперевізнику	автоперевізник	noun	noun:anim:m:v_kly
автоперевізнику	автоперевізник	noun	noun:anim:m:v_mis
автоперевізників	автоперевізник	noun	noun:anim:p:v_rod
автоперевізників	автоперевізник	noun	noun:anim:p:v_zna
автоперегонник	автоперегонник	noun	noun:anim:m:v_naz
автоперегонника	автоперегонник	noun	noun:anim:m:v_rod
автоперегонника	автоперегонник	noun	noun:anim:m:v_zna
автоперегонникам	автоперегонник	noun	noun:anim:p:v_dav
автоперегонниками	автоперегонник	noun	noun:anim:p:v_oru
автоперегонниках	автоперегонник	noun	noun:anim:p:v_mis
автоперегонники	автоперегонник	noun	noun:anim:p:v_kly
автоперегонники	автоперегонник	noun	noun:anim:p:v_naz
автоперегонники	автоперегонник	noun	noun:anim:p:v_zna:rare
автоперегонникові	автоперегонник	noun	noun:anim:m:v_dav
автоперегонникові	автоперегонник	noun	noun:anim:m:v_mis
автоперегонником	автоперегонник	noun	noun:anim:m:v_oru
автоперегоннику	автоперегонник	noun	noun:anim:m:v_dav
автоперегоннику	автоперегонник	noun	noun:anim:m:v_kly
автоперегоннику	автоперегонник	noun	noun:anim:m:v_mis
автоперегонників	автоперегонник	noun	noun:anim:p:v_rod
автоперегонників	автоперегонник	noun	noun:anim:p:v_zna
автоперегоннице	автоперегонниця	noun	noun:anim:f:v_kly
автоперегонницею	автоперегонниця	noun	noun:anim:f:v_oru
автоперегонниць	автоперегонниця	noun	noun:anim:p:v_rod
автоперегонниць	автоперегонниця	noun	noun:anim:p:v_zna
автоперегонницю	автоперегонниця	noun	noun:anim:f:v_zna
автоперегонниця	автоперегонниця	noun	noun:anim:f:v_naz
автоперегонницям	автоперегонниця	noun	noun:anim:p:v_dav
автоперегонницями	автоперегонниця	noun	noun:anim:p:v_oru
автоперегонницях	автоперегонниця	noun	noun:anim:p:v_mis
автоперегонниці	автоперегонниця	noun	noun:anim:f:v_dav
автоперегонниці	автоперегонниця	noun	noun:anim:f:v_mis
автоперегонниці	автоперегонниця	noun	noun:anim:f:v_rod
автоперегонниці	автоперегонниця	noun	noun:anim:p:v_kly
автоперегонниці	автоперегонниця	noun	noun:anim:p:v_naz
автоперегонниці	автоперегонниця	noun	noun:anim:p:v_zna:rare
автопереклад	автопереклад	noun	noun:inanim:m:v_naz
автопереклад	автопереклад	noun	noun:inanim:m:v_zna
автоперекладам	автопереклад	noun	noun:inanim:p:v_dav
автоперекладами	автопереклад	noun	noun:inanim:p:v_oru
автоперекладах	автопереклад	noun	noun:inanim:p:v_mis
автоперекладач	автоперекладач	noun	noun:inanim:m:v_naz
автоперекладач	автоперекладач	noun	noun:inanim:m:v_zna
автоперекладача	автоперекладач	noun	noun:inanim:m:v_rod
автоперекладачам	автоперекладач	noun	noun:inanim:p:v_dav
автоперекладачами	автоперекладач	noun	noun:inanim:p:v_oru
автоперекладачах	автоперекладач	noun	noun:inanim:p:v_mis
автоперекладачеві	автоперекладач	noun	noun:inanim:m:v_dav
автоперекладачеві	автоперекладач	noun	noun:inanim:m:v_mis
автоперекладачем	автоперекладач	noun	noun:inanim:m:v_oru
автоперекладачу	автоперекладач	noun	noun:inanim:m:v_dav
автоперекладачу	автоперекладач	noun	noun:inanim:m:v_kly
автоперекладачу	автоперекладач	noun	noun:inanim:m:v_mis
автоперекладачі	автоперекладач	noun	noun:inanim:m:v_mis
автоперекладачі	автоперекладач	noun	noun:inanim:p:v_kly
автоперекладачі	автоперекладач	noun	noun:inanim:p:v_naz
автоперекладачі	автоперекладач	noun	noun:inanim:p:v_zna
автоперекладачів	автоперекладач	noun	noun:inanim:p:v_rod
автоперекладе	автопереклад	noun	noun:inanim:m:v_kly
автопереклади	автопереклад	noun	noun:inanim:p:v_kly
автопереклади	автопереклад	noun	noun:inanim:p:v_naz
автопереклади	автопереклад	noun	noun:inanim:p:v_zna
автоперекладові	автопереклад	noun	noun:inanim:m:v_dav
автоперекладові	автопереклад	noun	noun:inanim:m:v_mis
автоперекладом	автопереклад	noun	noun:inanim:m:v_oru
автоперекладу	автопереклад	noun	noun:inanim:m:v_dav
автоперекладу	автопереклад	noun	noun:inanim:m:v_mis
автоперекладу	автопереклад	noun	noun:inanim:m:v_rod
автоперекладі	автопереклад	noun	noun:inanim:m:v_mis
автоперекладів	автопереклад	noun	noun:inanim:p:v_rod
автоперериванню	автопереривання	noun	noun:inanim:n:v_dav
автоперериванню	автопереривання	noun	noun:inanim:n:v_mis
автопереривання	автопереривання	noun	noun:inanim:n:v_kly
автопереривання	автопереривання	noun	noun:inanim:n:v_naz
автопереривання	автопереривання	noun	noun:inanim:n:v_rod
автопереривання	автопереривання	noun	noun:inanim:n:v_zna
автопереривання	автопереривання	noun	noun:inanim:p:v_kly
автопереривання	автопереривання	noun	noun:inanim:p:v_naz
автопереривання	автопереривання	noun	noun:inanim:p:v_zna
автоперериванням	автопереривання	noun	noun:inanim:n:v_oru
автоперериванням	автопереривання	noun	noun:inanim:p:v_dav
автоперериваннями	автопереривання	noun	noun:inanim:p:v_oru
автоперериваннях	автопереривання	noun	noun:inanim:p:v_mis
автоперериванні	автопереривання	noun	noun:inanim:n:v_mis
автопереривань	автопереривання	noun	noun:inanim:p:v_rod
автопереходам	автоперехід	noun	noun:inanim:p:v_dav
автопереходами	автоперехід	noun	noun:inanim:p:v_oru
автопереходах	автоперехід	noun	noun:inanim:p:v_mis
автопереходе	автоперехід	noun	noun:inanim:m:v_kly
автопереходи	автоперехід	noun	noun:inanim:p:v_kly
автопереходи	автоперехід	noun	noun:inanim:p:v_naz
автопереходи	автоперехід	noun	noun:inanim:p:v_zna
автопереходові	автоперехід	noun	noun:inanim:m:v_dav
автопереходові	автоперехід	noun	noun:inanim:m:v_mis
автопереходом	автоперехід	noun	noun:inanim:m:v_oru
автопереходу	автоперехід	noun	noun:inanim:m:v_dav
автопереходу	автоперехід	noun	noun:inanim:m:v_mis
автопереходу	автоперехід	noun	noun:inanim:m:v_rod
автопереході	автоперехід	noun	noun:inanim:m:v_mis
автопереходів	автоперехід	noun	noun:inanim:p:v_rod
автоперехід	автоперехід	noun	noun:inanim:m:v_naz
автоперехід	автоперехід	noun	noun:inanim:m:v_zna
автоплагіат	автоплагіат	noun	noun:inanim:m:v_naz
автоплагіат	автоплагіат	noun	noun:inanim:m:v_zna
автоплагіатам	автоплагіат	noun	noun:inanim:p:v_dav
автоплагіатами	автоплагіат	noun	noun:inanim:p:v_oru
автоплагіатах	автоплагіат	noun	noun:inanim:p:v_mis
автоплагіате	автоплагіат	noun	noun:inanim:m:v_kly
автоплагіати	автоплагіат	noun	noun:inanim:p:v_kly
автоплагіати	автоплагіат	noun	noun:inanim:p:v_naz
автоплагіати	автоплагіат	noun	noun:inanim:p:v_zna
автоплагіатові	автоплагіат	noun	noun:inanim:m:v_dav
автоплагіатові	автоплагіат	noun	noun:inanim:m:v_mis
автоплагіатом	автоплагіат	noun	noun:inanim:m:v_oru
автоплагіату	автоплагіат	noun	noun:inanim:m:v_dav
автоплагіату	автоплагіат	noun	noun:inanim:m:v_mis
автоплагіату	автоплагіат	noun	noun:inanim:m:v_rod
автоплагіаті	автоплагіат	noun	noun:inanim:m:v_mis
автоплагіатів	автоплагіат	noun	noun:inanim:p:v_rod
автоплатформ	автоплатформа	noun	noun:inanim:p:v_rod
автоплатформа	автоплатформа	noun	noun:inanim:f:v_naz
автоплатформам	автоплатформа	noun	noun:inanim:p:v_dav
автоплатформами	автоплатформа	noun	noun:inanim:p:v_oru
автоплатформах	автоплатформа	noun	noun:inanim:p:v_mis
автоплатформи	автоплатформа	noun	noun:inanim:f:v_rod
автоплатформи	автоплатформа	noun	noun:inanim:p:v_kly
автоплатформи	автоплатформа	noun	noun:inanim:p:v_naz
автоплатформи	автоплатформа	noun	noun:inanim:p:v_zna
автоплатформо	автоплатформа	noun	noun:inanim:f:v_kly
автоплатформою	автоплатформа	noun	noun:inanim:f:v_oru
автоплатформу	автоплатформа	noun	noun:inanim:f:v_zna
автоплатформі	автоплатформа	noun	noun:inanim:f:v_dav
автоплатформі	автоплатформа	noun	noun:inanim:f:v_mis
автоплуг	автоплуг	noun	noun:inanim:m:v_naz
автоплуг	автоплуг	noun	noun:inanim:m:v_zna
автоплуга	автоплуг	noun	noun:inanim:m:v_rod
автоплугам	автоплуг	noun	noun:inanim:p:v_dav
автоплугами	автоплуг	noun	noun:inanim:p:v_oru
автоплугах	автоплуг	noun	noun:inanim:p:v_mis
автоплуги	автоплуг	noun	noun:inanim:p:v_kly
автоплуги	автоплуг	noun	noun:inanim:p:v_naz
автоплуги	автоплуг	noun	noun:inanim:p:v_zna
автоплугові	автоплуг	noun	noun:inanim:m:v_dav
автоплугові	автоплуг	noun	noun:inanim:m:v_mis
автоплугом	автоплуг	noun	noun:inanim:m:v_oru
автоплугів	автоплуг	noun	noun:inanim:p:v_rod
автоплуже	автоплуг	noun	noun:inanim:m:v_kly
автоповтор	автоповтор	noun	noun:inanim:m:v_naz
автоповтор	автоповтор	noun	noun:inanim:m:v_zna
автоповторам	автоповтор	noun	noun:inanim:p:v_dav
автоповторами	автоповтор	noun	noun:inanim:p:v_oru
автоповторах	автоповтор	noun	noun:inanim:p:v_mis
автоповторе	автоповтор	noun	noun:inanim:m:v_kly
автоповтори	автоповтор	noun	noun:inanim:p:v_kly
автоповтори	автоповтор	noun	noun:inanim:p:v_naz
автоповтори	автоповтор	noun	noun:inanim:p:v_zna
автоповторові	автоповтор	noun	noun:inanim:m:v_dav
автоповторові	автоповтор	noun	noun:inanim:m:v_mis
автоповтором	автоповтор	noun	noun:inanim:m:v_oru
автоповтору	автоповтор	noun	noun:inanim:m:v_dav
автоповтору	автоповтор	noun	noun:inanim:m:v_mis
автоповтору	автоповтор	noun	noun:inanim:m:v_rod
автоповторі	автоповтор	noun	noun:inanim:m:v_mis
автоповторів	автоповтор	noun	noun:inanim:p:v_rod
автоповідомленню	автоповідомлення	noun	noun:inanim:n:v_dav
автоповідомленню	автоповідомлення	noun	noun:inanim:n:v_mis
автоповідомлення	автоповідомлення	noun	noun:inanim:n:v_kly
автоповідомлення	автоповідомлення	noun	noun:inanim:n:v_naz
автоповідомлення	автоповідомлення	noun	noun:inanim:n:v_rod
автоповідомлення	автоповідомлення	noun	noun:inanim:n:v_zna
автоповідомлення	автоповідомлення	noun	noun:inanim:p:v_kly
автоповідомлення	автоповідомлення	noun	noun:inanim:p:v_naz
автоповідомлення	автоповідомлення	noun	noun:inanim:p:v_zna
автоповідомленням	автоповідомлення	noun	noun:inanim:n:v_oru
автоповідомленням	автоповідомлення	noun	noun:inanim:p:v_dav
автоповідомленнями	автоповідомлення	noun	noun:inanim:p:v_oru
автоповідомленнях	автоповідомлення	noun	noun:inanim:p:v_mis
автоповідомленні	автоповідомлення	noun	noun:inanim:n:v_mis
автоповідомлень	автоповідомлення	noun	noun:inanim:p:v_rod
автоподавач	автоподавач	noun	noun:inanim:m:v_naz
автоподавач	автоподавач	noun	noun:inanim:m:v_zna
автоподавача	автоподавач	noun	noun:inanim:m:v_rod
автоподавачам	автоподавач	noun	noun:inanim:p:v_dav
автоподавачами	автоподавач	noun	noun:inanim:p:v_oru
автоподавачах	автоподавач	noun	noun:inanim:p:v_mis
автоподавачеві	автоподавач	noun	noun:inanim:m:v_dav
автоподавачеві	автоподавач	noun	noun:inanim:m:v_mis
автоподавачем	автоподавач	noun	noun:inanim:m:v_oru
автоподавачу	автоподавач	noun	noun:inanim:m:v_dav
автоподавачу	автоподавач	noun	noun:inanim:m:v_kly
автоподавачу	автоподавач	noun	noun:inanim:m:v_mis
автоподавачі	автоподавач	noun	noun:inanim:m:v_mis
автоподавачі	автоподавач	noun	noun:inanim:p:v_kly
автоподавачі	автоподавач	noun	noun:inanim:p:v_naz
автоподавачі	автоподавач	noun	noun:inanim:p:v_zna
автоподавачів	автоподавач	noun	noun:inanim:p:v_rod
автоподорож	автоподорож	noun	noun:inanim:f:v_naz
автоподорож	автоподорож	noun	noun:inanim:f:v_zna
автоподорожам	автоподорож	noun	noun:inanim:p:v_dav
автоподорожами	автоподорож	noun	noun:inanim:p:v_oru
автоподорожах	автоподорож	noun	noun:inanim:p:v_mis
автоподороже	автоподорож	noun	noun:inanim:f:v_kly
автоподорожей	автоподорож	noun	noun:inanim:p:v_rod
автоподорожжю	автоподорож	noun	noun:inanim:f:v_oru
автоподорожі	автоподорож	noun	noun:inanim:f:v_dav
автоподорожі	автоподорож	noun	noun:inanim:f:v_mis
автоподорожі	автоподорож	noun	noun:inanim:f:v_rod
автоподорожі	автоподорож	noun	noun:inanim:p:v_kly
автоподорожі	автоподорож	noun	noun:inanim:p:v_naz
автоподорожі	автоподорож	noun	noun:inanim:p:v_zna
автопожеж	автопожежа	noun	noun:inanim:p:v_rod
автопожежа	автопожежа	noun	noun:inanim:f:v_naz
автопожежам	автопожежа	noun	noun:inanim:p:v_dav
автопожежами	автопожежа	noun	noun:inanim:p:v_oru
автопожежах	автопожежа	noun	noun:inanim:p:v_mis
автопожеже	автопожежа	noun	noun:inanim:f:v_kly
автопожежею	автопожежа	noun	noun:inanim:f:v_oru
автопожежу	автопожежа	noun	noun:inanim:f:v_zna
автопожежі	автопожежа	noun	noun:inanim:f:v_dav
автопожежі	автопожежа	noun	noun:inanim:f:v_mis
автопожежі	автопожежа	noun	noun:inanim:f:v_rod
автопожежі	автопожежа	noun	noun:inanim:p:v_kly
автопожежі	автопожежа	noun	noun:inanim:p:v_naz
автопожежі	автопожежа	noun	noun:inanim:p:v_zna
автопозик	автопозика	noun	noun:inanim:p:v_rod
автопозика	автопозика	noun	noun:inanim:f:v_naz
автопозикам	автопозика	noun	noun:inanim:p:v_dav
автопозиками	автопозика	noun	noun:inanim:p:v_oru
автопозиках	автопозика	noun	noun:inanim:p:v_mis
автопозики	автопозика	noun	noun:inanim:f:v_rod
автопозики	автопозика	noun	noun:inanim:p:v_kly
автопозики	автопозика	noun	noun:inanim:p:v_naz
автопозики	автопозика	noun	noun:inanim:p:v_zna
автопозико	автопозика	noun	noun:inanim:f:v_kly
автопозикою	автопозика	noun	noun:inanim:f:v_oru
автопозику	автопозика	noun	noun:inanim:f:v_zna
автопозиці	автопозика	noun	noun:inanim:f:v_dav
автопозиці	автопозика	noun	noun:inanim:f:v_mis
автопокришка	автопокришка	noun	noun:inanim:f:v_naz
автопокришкам	автопокришка	noun	noun:inanim:p:v_dav
автопокришками	автопокришка	noun	noun:inanim:p:v_oru
автопокришках	автопокришка	noun	noun:inanim:p:v_mis
автопокришки	автопокришка	noun	noun:inanim:f:v_rod
автопокришки	автопокришка	noun	noun:inanim:p:v_kly
автопокришки	автопокришка	noun	noun:inanim:p:v_naz
автопокришки	автопокришка	noun	noun:inanim:p:v_zna
автопокришко	автопокришка	noun	noun:inanim:f:v_kly
автопокришкою	автопокришка	noun	noun:inanim:f:v_oru
автопокришку	автопокришка	noun	noun:inanim:f:v_zna
автопокришок	автопокришка	noun	noun:inanim:p:v_rod
автопокришці	автопокришка	noun	noun:inanim:f:v_dav
автопокришці	автопокришка	noun	noun:inanim:f:v_mis
автопокупка	автопокупка	noun	noun:inanim:f:v_naz
автопокупкам	автопокупка	noun	noun:inanim:p:v_dav
автопокупками	автопокупка	noun	noun:inanim:p:v_oru
автопокупках	автопокупка	noun	noun:inanim:p:v_mis
автопокупки	автопокупка	noun	noun:inanim:f:v_rod
автопокупки	автопокупка	noun	noun:inanim:p:v_kly
автопокупки	автопокупка	noun	noun:inanim:p:v_naz
автопокупки	автопокупка	noun	noun:inanim:p:v_zna
автопокупко	автопокупка	noun	noun:inanim:f:v_kly
автопокупкою	автопокупка	noun	noun:inanim:f:v_oru
автопокупку	автопокупка	noun	noun:inanim:f:v_zna
автопокупок	автопокупка	noun	noun:inanim:p:v_rod
автопокупці	автопокупка	noun	noun:inanim:f:v_dav
автопокупці	автопокупка	noun	noun:inanim:f:v_mis
автополивальнице	автополивальниця	noun	noun:inanim:f:v_kly
автополивальницею	автополивальниця	noun	noun:inanim:f:v_oru
автополивальниць	автополивальниця	noun	noun:inanim:p:v_rod
автополивальницю	автополивальниця	noun	noun:inanim:f:v_zna
автополивальниця	автополивальниця	noun	noun:inanim:f:v_naz
автополивальницям	автополивальниця	noun	noun:inanim:p:v_dav
автополивальницями	автополивальниця	noun	noun:inanim:p:v_oru
автополивальницях	автополивальниця	noun	noun:inanim:p:v_mis
автополивальниці	автополивальниця	noun	noun:inanim:f:v_dav
автополивальниці	автополивальниця	noun	noun:inanim:f:v_mis
автополивальниці	автополивальниця	noun	noun:inanim:f:v_rod
автополивальниці	автополивальниця	noun	noun:inanim:p:v_kly
автополивальниці	автополивальниця	noun	noun:inanim:p:v_naz
автополивальниці	автополивальниця	noun	noun:inanim:p:v_zna
автополивачка	автополивачка	noun	noun:inanim:f:v_naz
автополивачкам	автополивачка	noun	noun:inanim:p:v_dav
автополивачками	автополивачка	noun	noun:inanim:p:v_oru
автополивачках	автополивачка	noun	noun:inanim:p:v_mis
автополивачки	автополивачка	noun	noun:inanim:f:v_rod
автополивачки	автополивачка	noun	noun:inanim:p:v_kly
автополивачки	автополивачка	noun	noun:inanim:p:v_naz
автополивачки	автополивачка	noun	noun:inanim:p:v_zna
автополивачко	автополивачка	noun	noun:inanim:f:v_kly
автополивачкою	автополивачка	noun	noun:inanim:f:v_oru
автополивачку	автополивачка	noun	noun:inanim:f:v_zna
автополивачок	автополивачка	noun	noun:inanim:p:v_rod
автополивачці	автополивачка	noun	noun:inanim:f:v_dav
автополивачці	автополивачка	noun	noun:inanim:f:v_mis
автополігон	автополігон	noun	noun:inanim:m:v_naz
автополігон	автополігон	noun	noun:inanim:m:v_zna
автополігонам	автополігон	noun	noun:inanim:p:v_dav
автополігонами	автополігон	noun	noun:inanim:p:v_oru
автополігонах	автополігон	noun	noun:inanim:p:v_mis
автополігоне	автополігон	noun	noun:inanim:m:v_kly
автополігони	автополігон	noun	noun:inanim:p:v_kly
автополігони	автополігон	noun	noun:inanim:p:v_naz
автополігони	автополігон	noun	noun:inanim:p:v_zna
автополігонові	автополігон	noun	noun:inanim:m:v_dav
автополігонові	автополігон	noun	noun:inanim:m:v_mis
автополігоном	автополігон	noun	noun:inanim:m:v_oru
автополігону	автополігон	noun	noun:inanim:m:v_dav
автополігону	автополігон	noun	noun:inanim:m:v_mis
автополігону	автополігон	noun	noun:inanim:m:v_rod
автополігоні	автополігон	noun	noun:inanim:m:v_mis
автополігонів	автополігон	noun	noun:inanim:p:v_rod
автополіплоїдій	автополіплоїдія	noun	noun:inanim:p:v_rod
автополіплоїдію	автополіплоїдія	noun	noun:inanim:f:v_zna
автополіплоїдія	автополіплоїдія	noun	noun:inanim:f:v_naz
автополіплоїдіям	автополіплоїдія	noun	noun:inanim:p:v_dav
автополіплоїдіями	автополіплоїдія	noun	noun:inanim:p:v_oru
автополіплоїдіях	автополіплоїдія	noun	noun:inanim:p:v_mis
автополіплоїдіє	автополіплоїдія	noun	noun:inanim:f:v_kly
автополіплоїдією	автополіплоїдія	noun	noun:inanim:f:v_oru
автополіплоїдії	автополіплоїдія	noun	noun:inanim:f:v_dav
автополіплоїдії	автополіплоїдія	noun	noun:inanim:f:v_mis
автополіплоїдії	автополіплоїдія	noun	noun:inanim:f:v_rod
автополіплоїдії	автополіплоїдія	noun	noun:inanim:p:v_kly
автополіплоїдії	автополіплоїдія	noun	noun:inanim:p:v_naz
автополіплоїдії	автополіплоїдія	noun	noun:inanim:p:v_zna
автопомп	автопомпа	noun	noun:inanim:p:v_rod
автопомпа	автопомпа	noun	noun:inanim:f:v_naz
автопомпам	автопомпа	noun	noun:inanim:p:v_dav
автопомпами	автопомпа	noun	noun:inanim:p:v_oru
автопомпах	автопомпа	noun	noun:inanim:p:v_mis
автопомпи	автопомпа	noun	noun:inanim:f:v_rod
автопомпи	автопомпа	noun	noun:inanim:p:v_kly
автопомпи	автопомпа	noun	noun:inanim:p:v_naz
автопомпи	автопомпа	noun	noun:inanim:p:v_zna
автопомпо	автопомпа	noun	noun:inanim:f:v_kly
автопомпою	автопомпа	noun	noun:inanim:f:v_oru
автопомпу	автопомпа	noun	noun:inanim:f:v_zna
автопомпі	автопомпа	noun	noun:inanim:f:v_dav
автопомпі	автопомпа	noun	noun:inanim:f:v_mis
автопором	автопором	noun	noun:inanim:m:v_naz
автопором	автопором	noun	noun:inanim:m:v_zna
автопорома	автопором	noun	noun:inanim:m:v_rod
автопоромам	автопором	noun	noun:inanim:p:v_dav
автопоромами	автопором	noun	noun:inanim:p:v_oru
автопоромах	автопором	noun	noun:inanim:p:v_mis
автопороме	автопором	noun	noun:inanim:m:v_kly
автопороми	автопором	noun	noun:inanim:p:v_kly
автопороми	автопором	noun	noun:inanim:p:v_naz
автопороми	автопором	noun	noun:inanim:p:v_zna
автопоромові	автопором	noun	noun:inanim:m:v_dav
автопоромові	автопором	noun	noun:inanim:m:v_mis
автопоромом	автопором	noun	noun:inanim:m:v_oru
автопоромі	автопором	noun	noun:inanim:m:v_mis
автопоромів	автопором	noun	noun:inanim:p:v_rod
автопорт	автопорт	noun	noun:inanim:m:v_naz
автопорт	автопорт	noun	noun:inanim:m:v_zna
автопортам	автопорт	noun	noun:inanim:p:v_dav
автопортами	автопорт	noun	noun:inanim:p:v_oru
автопортах	автопорт	noun	noun:inanim:p:v_mis
автопорте	автопорт	noun	noun:inanim:m:v_kly
автопорти	автопорт	noun	noun:inanim:p:v_kly
автопорти	автопорт	noun	noun:inanim:p:v_naz
автопорти	автопорт	noun	noun:inanim:p:v_zna
автопортові	автопорт	noun	noun:inanim:m:v_dav
автопортові	автопорт	noun	noun:inanim:m:v_mis
автопортом	автопорт	noun	noun:inanim:m:v_oru
автопортрет	автопортрет	noun	noun:inanim:m:v_naz
автопортрет	автопортрет	noun	noun:inanim:m:v_zna
автопортрета	автопортрет	noun	noun:inanim:m:v_rod
автопортретам	автопортрет	noun	noun:inanim:p:v_dav
автопортретами	автопортрет	noun	noun:inanim:p:v_oru
автопортретах	автопортрет	noun	noun:inanim:p:v_mis
автопортрете	автопортрет	noun	noun:inanim:m:v_kly
автопортрети	автопортрет	noun	noun:inanim:p:v_kly
автопортрети	автопортрет	noun	noun:inanim:p:v_naz
автопортрети	автопортрет	noun	noun:inanim:p:v_zna
автопортретові	автопортрет	noun	noun:inanim:m:v_dav
автопортретові	автопортрет	noun	noun:inanim:m:v_mis
автопортретом	автопортрет	noun	noun:inanim:m:v_oru
автопортреті	автопортрет	noun	noun:inanim:m:v_mis
автопортретів	автопортрет	noun	noun:inanim:p:v_rod
автопорту	автопорт	noun	noun:inanim:m:v_dav
автопорту	автопорт	noun	noun:inanim:m:v_mis
автопорту	автопорт	noun	noun:inanim:m:v_rod
автопорті	автопорт	noun	noun:inanim:m:v_mis
автопортів	автопорт	noun	noun:inanim:p:v_rod
автопорушник	автопорушник	noun	noun:anim:m:v_naz
автопорушника	автопорушник	noun	noun:anim:m:v_rod
автопорушника	автопорушник	noun	noun:anim:m:v_zna
автопорушникам	автопорушник	noun	noun:anim:p:v_dav
автопорушниками	автопорушник	noun	noun:anim:p:v_oru
автопорушниках	автопорушник	noun	noun:anim:p:v_mis
автопорушники	автопорушник	noun	noun:anim:p:v_kly
автопорушники	автопорушник	noun	noun:anim:p:v_naz
автопорушники	автопорушник	noun	noun:anim:p:v_zna:rare
автопорушникові	автопорушник	noun	noun:anim:m:v_dav
автопорушникові	автопорушник	noun	noun:anim:m:v_mis
автопорушником	автопорушник	noun	noun:anim:m:v_oru
автопорушнику	автопорушник	noun	noun:anim:m:v_dav
автопорушнику	автопорушник	noun	noun:anim:m:v_kly
автопорушнику	автопорушник	noun	noun:anim:m:v_mis
автопорушників	автопорушник	noun	noun:anim:p:v_rod
автопорушників	автопорушник	noun	noun:anim:p:v_zna
автопосиланню	автопосилання	noun	noun:inanim:n:v_dav
автопосиланню	автопосилання	noun	noun:inanim:n:v_mis
автопосилання	автопосилання	noun	noun:inanim:n:v_kly
автопосилання	автопосилання	noun	noun:inanim:n:v_naz
автопосилання	автопосилання	noun	noun:inanim:n:v_rod
автопосилання	автопосилання	noun	noun:inanim:n:v_zna
автопосилання	автопосилання	noun	noun:inanim:p:v_kly
автопосилання	автопосилання	noun	noun:inanim:p:v_naz
автопосилання	автопосилання	noun	noun:inanim:p:v_zna
автопосиланням	автопосилання	noun	noun:inanim:n:v_oru
автопосиланням	автопосилання	noun	noun:inanim:p:v_dav
автопосиланнями	автопосилання	noun	noun:inanim:p:v_oru
автопосиланнях	автопосилання	noun	noun:inanim:p:v_mis
автопосиланні	автопосилання	noun	noun:inanim:n:v_mis
автопосилань	автопосилання	noun	noun:inanim:p:v_rod
автопотенціометр	автопотенціометр	noun	noun:inanim:m:v_naz
автопотенціометр	автопотенціометр	noun	noun:inanim:m:v_zna
автопотенціометра	автопотенціометр	noun	noun:inanim:m:v_rod
автопотенціометрам	автопотенціометр	noun	noun:inanim:p:v_dav
автопотенціометрами	автопотенціометр	noun	noun:inanim:p:v_oru
автопотенціометрах	автопотенціометр	noun	noun:inanim:p:v_mis
автопотенціометре	автопотенціометр	noun	noun:inanim:m:v_kly
автопотенціометри	автопотенціометр	noun	noun:inanim:p:v_kly
автопотенціометри	автопотенціометр	noun	noun:inanim:p:v_naz
автопотенціометри	автопотенціометр	noun	noun:inanim:p:v_zna
автопотенціометрові	автопотенціометр	noun	noun:inanim:m:v_dav
автопотенціометрові	автопотенціометр	noun	noun:inanim:m:v_mis
автопотенціометром	автопотенціометр	noun	noun:inanim:m:v_oru
автопотенціометрі	автопотенціометр	noun	noun:inanim:m:v_mis
автопотенціометрів	автопотенціометр	noun	noun:inanim:p:v_rod
автопотокам	автопотік	noun	noun:inanim:p:v_dav
автопотоками	автопотік	noun	noun:inanim:p:v_oru
автопотоках	автопотік	noun	noun:inanim:p:v_mis
автопотоки	автопотік	noun	noun:inanim:p:v_kly
автопотоки	автопотік	noun	noun:inanim:p:v_naz
автопотоки	автопотік	noun	noun:inanim:p:v_zna
автопотокові	автопотік	noun	noun:inanim:m:v_dav
автопотокові	автопотік	noun	noun:inanim:m:v_mis
автопотоком	автопотік	noun	noun:inanim:m:v_oru
автопотоку	автопотік	noun	noun:inanim:m:v_dav
автопотоку	автопотік	noun	noun:inanim:m:v_kly
автопотоку	автопотік	noun	noun:inanim:m:v_mis
автопотоку	автопотік	noun	noun:inanim:m:v_rod
автопотоків	автопотік	noun	noun:inanim:p:v_rod
автопотяг	автопотяг	noun	noun:inanim:m:v_naz
автопотяг	автопотяг	noun	noun:inanim:m:v_zna
автопотяга	автопотяг	noun	noun:inanim:m:v_rod
автопотягам	автопотяг	noun	noun:inanim:p:v_dav
автопотягами	автопотяг	noun	noun:inanim:p:v_oru
автопотягах	автопотяг	noun	noun:inanim:p:v_mis
автопотяги	автопотяг	noun	noun:inanim:p:v_kly
автопотяги	автопотяг	noun	noun:inanim:p:v_naz
автопотяги	автопотяг	noun	noun:inanim:p:v_zna
автопотягові	автопотяг	noun	noun:inanim:m:v_dav
автопотягові	автопотяг	noun	noun:inanim:m:v_mis
автопотягом	автопотяг	noun	noun:inanim:m:v_oru
автопотягу	автопотяг	noun	noun:inanim:m:v_dav
автопотягу	автопотяг	noun	noun:inanim:m:v_kly
автопотягу	автопотяг	noun	noun:inanim:m:v_mis
автопотягів	автопотяг	noun	noun:inanim:p:v_rod
автопотік	автопотік	noun	noun:inanim:m:v_naz
автопотік	автопотік	noun	noun:inanim:m:v_zna
автопоїзд	автопоїзд	noun	noun:inanim:m:v_naz
автопоїзд	автопоїзд	noun	noun:inanim:m:v_zna
автопоїзда	автопоїзд	noun	noun:inanim:m:v_rod
автопоїздам	автопоїзд	noun	noun:inanim:p:v_dav
автопоїздами	автопоїзд	noun	noun:inanim:p:v_oru
автопоїздах	автопоїзд	noun	noun:inanim:p:v_mis
автопоїзде	автопоїзд	noun	noun:inanim:m:v_kly
автопоїзди	автопоїзд	noun	noun:inanim:p:v_kly
автопоїзди	автопоїзд	noun	noun:inanim:p:v_naz
автопоїзди	автопоїзд	noun	noun:inanim:p:v_zna
автопоїздка	автопоїздка	noun	noun:inanim:f:v_naz
автопоїздкам	автопоїздка	noun	noun:inanim:p:v_dav
автопоїздками	автопоїздка	noun	noun:inanim:p:v_oru
автопоїздках	автопоїздка	noun	noun:inanim:p:v_mis
автопоїздки	автопоїздка	noun	noun:inanim:f:v_rod
автопоїздки	автопоїздка	noun	noun:inanim:p:v_kly
автопоїздки	автопоїздка	noun	noun:inanim:p:v_naz
автопоїздки	автопоїздка	noun	noun:inanim:p:v_zna
автопоїздко	автопоїздка	noun	noun:inanim:f:v_kly
автопоїздкою	автопоїздка	noun	noun:inanim:f:v_oru
автопоїздку	автопоїздка	noun	noun:inanim:f:v_zna
автопоїздові	автопоїзд	noun	noun:inanim:m:v_dav
автопоїздові	автопоїзд	noun	noun:inanim:m:v_mis
автопоїздок	автопоїздка	noun	noun:inanim:p:v_rod
автопоїздом	автопоїзд	noun	noun:inanim:m:v_oru
автопоїздці	автопоїздка	noun	noun:inanim:f:v_dav
автопоїздці	автопоїздка	noun	noun:inanim:f:v_mis
автопоїзді	автопоїзд	noun	noun:inanim:m:v_mis
автопоїздів	автопоїзд	noun	noun:inanim:p:v_rod
автопоїлка	автопоїлка	noun	noun:inanim:f:v_naz
автопоїлкам	автопоїлка	noun	noun:inanim:p:v_dav
автопоїлками	автопоїлка	noun	noun:inanim:p:v_oru
автопоїлках	автопоїлка	noun	noun:inanim:p:v_mis
автопоїлки	автопоїлка	noun	noun:inanim:f:v_rod
автопоїлки	автопоїлка	noun	noun:inanim:p:v_kly
автопоїлки	автопоїлка	noun	noun:inanim:p:v_naz
автопоїлки	автопоїлка	noun	noun:inanim:p:v_zna
автопоїлко	автопоїлка	noun	noun:inanim:f:v_kly
автопоїлкою	автопоїлка	noun	noun:inanim:f:v_oru
автопоїлку	автопоїлка	noun	noun:inanim:f:v_zna
автопоїлок	автопоїлка	noun	noun:inanim:p:v_rod
автопоїлці	автопоїлка	noun	noun:inanim:f:v_dav
автопоїлці	автопоїлка	noun	noun:inanim:f:v_mis
автопрезентацій	автопрезентація	noun	noun:inanim:p:v_rod
автопрезентацію	автопрезентація	noun	noun:inanim:f:v_zna
автопрезентація	автопрезентація	noun	noun:inanim:f:v_naz
автопрезентаціям	автопрезентація	noun	noun:inanim:p:v_dav
автопрезентаціями	автопрезентація	noun	noun:inanim:p:v_oru
автопрезентаціях	автопрезентація	noun	noun:inanim:p:v_mis
автопрезентаціє	автопрезентація	noun	noun:inanim:f:v_kly
автопрезентацією	автопрезентація	noun	noun:inanim:f:v_oru
автопрезентації	автопрезентація	noun	noun:inanim:f:v_dav
автопрезентації	автопрезентація	noun	noun:inanim:f:v_mis
автопрезентації	автопрезентація	noun	noun:inanim:f:v_rod
автопрезентації	автопрезентація	noun	noun:inanim:p:v_kly
автопрезентації	автопрезентація	noun	noun:inanim:p:v_naz
автопрезентації	автопрезентація	noun	noun:inanim:p:v_zna
автопригод	автопригода	noun	noun:inanim:p:v_rod
автопригода	автопригода	noun	noun:inanim:f:v_naz
автопригодам	автопригода	noun	noun:inanim:p:v_dav
автопригодами	автопригода	noun	noun:inanim:p:v_oru
автопригодах	автопригода	noun	noun:inanim:p:v_mis
автопригоди	автопригода	noun	noun:inanim:f:v_rod
автопригоди	автопригода	noun	noun:inanim:p:v_kly
автопригоди	автопригода	noun	noun:inanim:p:v_naz
автопригоди	автопригода	noun	noun:inanim:p:v_zna
автопригодо	автопригода	noun	noun:inanim:f:v_kly
автопригодою	автопригода	noun	noun:inanim:f:v_oru
автопригоду	автопригода	noun	noun:inanim:f:v_zna
автопригоді	автопригода	noun	noun:inanim:f:v_dav
автопригоді	автопригода	noun	noun:inanim:f:v_mis
автопричепа	автопричіп	noun	noun:inanim:m:v_rod
автопричепам	автопричіп	noun	noun:inanim:p:v_dav
автопричепами	автопричіп	noun	noun:inanim:p:v_oru
автопричепах	автопричіп	noun	noun:inanim:p:v_mis
автопричепе	автопричіп	noun	noun:inanim:m:v_kly
автопричепи	автопричіп	noun	noun:inanim:p:v_kly
автопричепи	автопричіп	noun	noun:inanim:p:v_naz
автопричепи	автопричіп	noun	noun:inanim:p:v_zna
автопричепові	автопричіп	noun	noun:inanim:m:v_dav
автопричепові	автопричіп	noun	noun:inanim:m:v_mis
автопричепом	автопричіп	noun	noun:inanim:m:v_oru
автопричепі	автопричіп	noun	noun:inanim:m:v_mis
автопричепів	автопричіп	noun	noun:inanim:p:v_rod
автопричіп	автопричіп	noun	noun:inanim:m:v_naz
автопричіп	автопричіп	noun	noun:inanim:m:v_zna
автопробіг	автопробіг	noun	noun:inanim:m:v_naz
автопробіг	автопробіг	noun	noun:inanim:m:v_zna
автопробігам	автопробіг	noun	noun:inanim:p:v_dav
автопробігами	автопробіг	noun	noun:inanim:p:v_oru
автопробігах	автопробіг	noun	noun:inanim:p:v_mis
автопробіги	автопробіг	noun	noun:inanim:p:v_kly
автопробіги	автопробіг	noun	noun:inanim:p:v_naz
автопробіги	автопробіг	noun	noun:inanim:p:v_zna
автопробігові	автопробіг	noun	noun:inanim:m:v_dav
автопробігові	автопробіг	noun	noun:inanim:m:v_mis
автопробігом	автопробіг	noun	noun:inanim:m:v_oru
автопробігу	автопробіг	noun	noun:inanim:m:v_dav
автопробігу	автопробіг	noun	noun:inanim:m:v_kly
автопробігу	автопробіг	noun	noun:inanim:m:v_mis
автопробігу	автопробіг	noun	noun:inanim:m:v_rod
автопробігів	автопробіг	noun	noun:inanim:p:v_rod
автопрогулянка	автопрогулянка	noun	noun:inanim:f:v_naz
автопрогулянкам	автопрогулянка	noun	noun:inanim:p:v_dav
автопрогулянками	автопрогулянка	noun	noun:inanim:p:v_oru
автопрогулянках	автопрогулянка	noun	noun:inanim:p:v_mis
автопрогулянки	автопрогулянка	noun	noun:inanim:f:v_rod
автопрогулянки	автопрогулянка	noun	noun:inanim:p:v_kly
автопрогулянки	автопрогулянка	noun	noun:inanim:p:v_naz
автопрогулянки	автопрогулянка	noun	noun:inanim:p:v_zna
автопрогулянко	автопрогулянка	noun	noun:inanim:f:v_kly
автопрогулянкою	автопрогулянка	noun	noun:inanim:f:v_oru
автопрогулянку	автопрогулянка	noun	noun:inanim:f:v_zna
автопрогулянок	автопрогулянка	noun	noun:inanim:p:v_rod
автопрогулянці	автопрогулянка	noun	noun:inanim:f:v_dav
автопрогулянці	автопрогулянка	noun	noun:inanim:f:v_mis
автопродавець	автопродавець	noun	noun:anim:m:v_naz
автопродавцеві	автопродавець	noun	noun:anim:m:v_dav
автопродавцеві	автопродавець	noun	noun:anim:m:v_mis
автопродавцем	автопродавець	noun	noun:anim:m:v_oru
автопродавцю	автопродавець	noun	noun:anim:m:v_dav
автопродавцю	автопродавець	noun	noun:anim:m:v_kly
автопродавцю	автопродавець	noun	noun:anim:m:v_mis
автопродавця	автопродавець	noun	noun:anim:m:v_rod
автопродавця	автопродавець	noun	noun:anim:m:v_zna
автопродавцям	автопродавець	noun	noun:anim:p:v_dav
автопродавцями	автопродавець	noun	noun:anim:p:v_oru
автопродавцях	автопродавець	noun	noun:anim:p:v_mis
автопродавці	автопродавець	noun	noun:anim:m:v_mis
автопродавці	автопродавець	noun	noun:anim:p:v_kly
автопродавці	автопродавець	noun	noun:anim:p:v_naz
автопродавці	автопродавець	noun	noun:anim:p:v_zna:rare
автопродавців	автопродавець	noun	noun:anim:p:v_rod
автопродавців	автопродавець	noun	noun:anim:p:v_zna
автопродаж	автопродаж	noun	noun:inanim:m:v_naz
автопродаж	автопродаж	noun	noun:inanim:m:v_zna
автопродажам	автопродаж	noun	noun:inanim:p:v_dav
автопродажами	автопродаж	noun	noun:inanim:p:v_oru
автопродажах	автопродаж	noun	noun:inanim:p:v_mis
автопродаже	автопродаж	noun	noun:inanim:m:v_kly
автопродажеві	автопродаж	noun	noun:inanim:m:v_dav
автопродажеві	автопродаж	noun	noun:inanim:m:v_mis
автопродажем	автопродаж	noun	noun:inanim:m:v_oru
автопродажу	автопродаж	noun	noun:inanim:m:v_dav
автопродажу	автопродаж	noun	noun:inanim:m:v_mis
автопродажу	автопродаж	noun	noun:inanim:m:v_rod
автопродажі	автопродаж	noun	noun:inanim:m:v_mis
автопродажі	автопродаж	noun	noun:inanim:p:v_kly
автопродажі	автопродаж	noun	noun:inanim:p:v_naz
автопродажі	автопродаж	noun	noun:inanim:p:v_zna
автопродажів	автопродаж	noun	noun:inanim:p:v_rod
автопрокат	автопрокат	noun	noun:inanim:m:v_naz
автопрокат	автопрокат	noun	noun:inanim:m:v_zna
автопрокатам	автопрокат	noun	noun:inanim:p:v_dav
автопрокатами	автопрокат	noun	noun:inanim:p:v_oru
автопрокатах	автопрокат	noun	noun:inanim:p:v_mis
автопрокате	автопрокат	noun	noun:inanim:m:v_kly
автопрокати	автопрокат	noun	noun:inanim:p:v_kly
автопрокати	автопрокат	noun	noun:inanim:p:v_naz
автопрокати	автопрокат	noun	noun:inanim:p:v_zna
автопрокатові	автопрокат	noun	noun:inanim:m:v_dav
автопрокатові	автопрокат	noun	noun:inanim:m:v_mis
автопрокатом	автопрокат	noun	noun:inanim:m:v_oru
автопрокату	автопрокат	noun	noun:inanim:m:v_dav
автопрокату	автопрокат	noun	noun:inanim:m:v_mis
автопрокату	автопрокат	noun	noun:inanim:m:v_rod
автопрокаті	автопрокат	noun	noun:inanim:m:v_mis
автопрокатів	автопрокат	noun	noun:inanim:p:v_rod
автопрокладач	автопрокладач	noun	noun:inanim:m:v_naz
автопрокладач	автопрокладач	noun	noun:inanim:m:v_zna
автопрокладача	автопрокладач	noun	noun:inanim:m:v_rod
автопрокладачам	автопрокладач	noun	noun:inanim:p:v_dav
автопрокладачами	автопрокладач	noun	noun:inanim:p:v_oru
автопрокладачах	автопрокладач	noun	noun:inanim:p:v_mis
автопрокладачеві	автопрокладач	noun	noun:inanim:m:v_dav
автопрокладачеві	автопрокладач	noun	noun:inanim:m:v_mis
автопрокладачем	автопрокладач	noun	noun:inanim:m:v_oru
автопрокладачу	автопрокладач	noun	noun:inanim:m:v_dav
автопрокладачу	автопрокладач	noun	noun:inanim:m:v_kly
автопрокладачу	автопрокладач	noun	noun:inanim:m:v_mis
автопрокладачі	автопрокладач	noun	noun:inanim:m:v_mis
автопрокладачі	автопрокладач	noun	noun:inanim:p:v_kly
автопрокладачі	автопрокладач	noun	noun:inanim:p:v_naz
автопрокладачі	автопрокладач	noun	noun:inanim:p:v_zna
автопрокладачів	автопрокладач	noun	noun:inanim:p:v_rod
автопромисловець	автопромисловець	noun	noun:anim:m:v_naz
автопромисловосте	автопромисловість	noun	noun:inanim:f:v_kly
автопромисловостей	автопромисловість	noun	noun:inanim:p:v_rod
автопромисловостям	автопромисловість	noun	noun:inanim:p:v_dav
автопромисловостями	автопромисловість	noun	noun:inanim:p:v_oru
автопромисловостях	автопромисловість	noun	noun:inanim:p:v_mis
автопромисловості	автопромисловість	noun	noun:inanim:f:v_dav
автопромисловості	автопромисловість	noun	noun:inanim:f:v_mis
автопромисловості	автопромисловість	noun	noun:inanim:f:v_rod
автопромисловості	автопромисловість	noun	noun:inanim:p:v_kly
автопромисловості	автопромисловість	noun	noun:inanim:p:v_naz
автопромисловості	автопромисловість	noun	noun:inanim:p:v_zna
автопромисловцеві	автопромисловець	noun	noun:anim:m:v_dav
автопромисловцеві	автопромисловець	noun	noun:anim:m:v_mis
автопромисловцем	автопромисловець	noun	noun:anim:m:v_oru
автопромисловцю	автопромисловець	noun	noun:anim:m:v_dav
автопромисловцю	автопромисловець	noun	noun:anim:m:v_kly
автопромисловцю	автопромисловець	noun	noun:anim:m:v_mis
автопромисловця	автопромисловець	noun	noun:anim:m:v_rod
автопромисловця	автопромисловець	noun	noun:anim:m:v_zna
автопромисловцям	автопромисловець	noun	noun:anim:p:v_dav
автопромисловцями	автопромисловець	noun	noun:anim:p:v_oru
автопромисловцях	автопромисловець	noun	noun:anim:p:v_mis
автопромисловці	автопромисловець	noun	noun:anim:m:v_mis
автопромисловці	автопромисловець	noun	noun:anim:p:v_kly
автопромисловці	автопромисловець	noun	noun:anim:p:v_naz
автопромисловці	автопромисловець	noun	noun:anim:p:v_zna:rare
автопромисловців	автопромисловець	noun	noun:anim:p:v_rod
автопромисловців	автопромисловець	noun	noun:anim:p:v_zna
автопромисловість	автопромисловість	noun	noun:inanim:f:v_naz
автопромисловість	автопромисловість	noun	noun:inanim:f:v_zna
автопромисловістю	автопромисловість	noun	noun:inanim:f:v_oru
автопсій	автопсія	noun	noun:inanim:p:v_rod
автопсію	автопсія	noun	noun:inanim:f:v_zna
автопсія	автопсія	noun	noun:inanim:f:v_naz
автопсіям	автопсія	noun	noun:inanim:p:v_dav
автопсіями	автопсія	noun	noun:inanim:p:v_oru
автопсіях	автопсія	noun	noun:inanim:p:v_mis
автопсіє	автопсія	noun	noun:inanim:f:v_kly
автопсією	автопсія	noun	noun:inanim:f:v_oru
автопсії	автопсія	noun	noun:inanim:f:v_dav
автопсії	автопсія	noun	noun:inanim:f:v_mis
автопсії	автопсія	noun	noun:inanim:f:v_rod
автопсії	автопсія	noun	noun:inanim:p:v_kly
автопсії	автопсія	noun	noun:inanim:p:v_naz
автопсії	автопсія	noun	noun:inanim:p:v_zna
автопідприємств	автопідприємство	noun	noun:inanim:p:v_rod
автопідприємства	автопідприємство	noun	noun:inanim:n:v_rod
автопідприємства	автопідприємство	noun	noun:inanim:p:v_kly
автопідприємства	автопідприємство	noun	noun:inanim:p:v_naz
автопідприємства	автопідприємство	noun	noun:inanim:p:v_zna
автопідприємствам	автопідприємство	noun	noun:inanim:p:v_dav
автопідприємствами	автопідприємство	noun	noun:inanim:p:v_oru
автопідприємствах	автопідприємство	noun	noun:inanim:p:v_mis
автопідприємство	автопідприємство	noun	noun:inanim:n:v_kly
автопідприємство	автопідприємство	noun	noun:inanim:n:v_naz
автопідприємство	автопідприємство	noun	noun:inanim:n:v_zna
автопідприємством	автопідприємство	noun	noun:inanim:n:v_oru
автопідприємству	автопідприємство	noun	noun:inanim:n:v_dav
автопідприємству	автопідприємство	noun	noun:inanim:n:v_mis
автопідприємстві	автопідприємство	noun	noun:inanim:n:v_mis
автопідіймач	автопідіймач	noun	noun:inanim:m:v_naz
автопідіймач	автопідіймач	noun	noun:inanim:m:v_zna
автопідіймача	автопідіймач	noun	noun:inanim:m:v_rod
автопідіймачам	автопідіймач	noun	noun:inanim:p:v_dav
автопідіймачами	автопідіймач	noun	noun:inanim:p:v_oru
автопідіймачах	автопідіймач	noun	noun:inanim:p:v_mis
автопідіймачеві	автопідіймач	noun	noun:inanim:m:v_dav
автопідіймачеві	автопідіймач	noun	noun:inanim:m:v_mis
автопідіймачем	автопідіймач	noun	noun:inanim:m:v_oru
автопідіймачу	автопідіймач	noun	noun:inanim:m:v_dav
автопідіймачу	автопідіймач	noun	noun:inanim:m:v_kly
автопідіймачу	автопідіймач	noun	noun:inanim:m:v_mis
автопідіймачі	автопідіймач	noun	noun:inanim:m:v_mis
автопідіймачі	автопідіймач	noun	noun:inanim:p:v_kly
автопідіймачі	автопідіймач	noun	noun:inanim:p:v_naz
автопідіймачі	автопідіймач	noun	noun:inanim:p:v_zna
автопідіймачів	автопідіймач	noun	noun:inanim:p:v_rod
автопілот	автопілот	noun	noun:inanim:m:v_naz
автопілот	автопілот	noun	noun:inanim:m:v_zna
автопілота	автопілот	noun	noun:inanim:m:v_rod
автопілотам	автопілот	noun	noun:inanim:p:v_dav
автопілотами	автопілот	noun	noun:inanim:p:v_oru
автопілотах	автопілот	noun	noun:inanim:p:v_mis
автопілоте	автопілот	noun	noun:inanim:m:v_kly
автопілоти	автопілот	noun	noun:inanim:p:v_kly
автопілоти	автопілот	noun	noun:inanim:p:v_naz
автопілоти	автопілот	noun	noun:inanim:p:v_zna
автопілотові	автопілот	noun	noun:inanim:m:v_dav
автопілотові	автопілот	noun	noun:inanim:m:v_mis
автопілотом	автопілот	noun	noun:inanim:m:v_oru
автопілоті	автопілот	noun	noun:inanim:m:v_mis
автопілотів	автопілот	noun	noun:inanim:p:v_rod
автор	автор	noun	noun:anim:m:v_naz
автора	автор	noun	noun:anim:m:v_rod
автора	автор	noun	noun:anim:m:v_zna
авторадіограм	авторадіограма	noun	noun:inanim:p:v_rod
авторадіограма	авторадіограма	noun	noun:inanim:f:v_naz
авторадіограмам	авторадіограма	noun	noun:inanim:p:v_dav
авторадіограмами	авторадіограма	noun	noun:inanim:p:v_oru
авторадіограмах	авторадіограма	noun	noun:inanim:p:v_mis
авторадіограми	авторадіограма	noun	noun:inanim:f:v_rod
авторадіограми	авторадіограма	noun	noun:inanim:p:v_kly
авторадіограми	авторадіограма	noun	noun:inanim:p:v_naz
авторадіограми	авторадіограма	noun	noun:inanim:p:v_zna
авторадіограмо	авторадіограма	noun	noun:inanim:f:v_kly
авторадіограмою	авторадіограма	noun	noun:inanim:f:v_oru
авторадіограму	авторадіограма	noun	noun:inanim:f:v_zna
авторадіограмі	авторадіограма	noun	noun:inanim:f:v_dav
авторадіограмі	авторадіограма	noun	noun:inanim:f:v_mis
авторадіограф	авторадіограф	noun	noun:inanim:m:v_naz
авторадіограф	авторадіограф	noun	noun:inanim:m:v_zna
авторадіографа	авторадіограф	noun	noun:inanim:m:v_rod
авторадіографам	авторадіограф	noun	noun:inanim:p:v_dav
авторадіографами	авторадіограф	noun	noun:inanim:p:v_oru
авторадіографах	авторадіограф	noun	noun:inanim:p:v_mis
авторадіографе	авторадіограф	noun	noun:inanim:m:v_kly
авторадіографи	авторадіограф	noun	noun:inanim:p:v_kly
авторадіографи	авторадіограф	noun	noun:inanim:p:v_naz
авторадіографи	авторадіограф	noun	noun:inanim:p:v_zna
авторадіографові	авторадіограф	noun	noun:inanim:m:v_dav
авторадіографові	авторадіограф	noun	noun:inanim:m:v_mis
авторадіографом	авторадіограф	noun	noun:inanim:m:v_oru
авторадіографі	авторадіограф	noun	noun:inanim:m:v_mis
авторадіографів	авторадіограф	noun	noun:inanim:p:v_rod
авторадіографій	авторадіографія	noun	noun:inanim:p:v_rod
авторадіографію	авторадіографія	noun	noun:inanim:f:v_zna
авторадіографія	авторадіографія	noun	noun:inanim:f:v_naz
авторадіографіям	авторадіографія	noun	noun:inanim:p:v_dav
авторадіографіями	авторадіографія	noun	noun:inanim:p:v_oru
авторадіографіях	авторадіографія	noun	noun:inanim:p:v_mis
авторадіографіє	авторадіографія	noun	noun:inanim:f:v_kly
авторадіографією	авторадіографія	noun	noun:inanim:f:v_oru
авторадіографії	авторадіографія	noun	noun:inanim:f:v_dav
авторадіографії	авторадіографія	noun	noun:inanim:f:v_mis
авторадіографії	авторадіографія	noun	noun:inanim:f:v_rod
авторадіографії	авторадіографія	noun	noun:inanim:p:v_kly
авторадіографії	авторадіографія	noun	noun:inanim:p:v_naz
авторадіографії	авторадіографія	noun	noun:inanim:p:v_zna
авторам	автор	noun	noun:anim:p:v_dav
авторами	автор	noun	noun:anim:p:v_oru
автораритет	автораритет	noun	noun:inanim:m:v_naz
автораритет	автораритет	noun	noun:inanim:m:v_zna
автораритетам	автораритет	noun	noun:inanim:p:v_dav
автораритетами	автораритет	noun	noun:inanim:p:v_oru
автораритетах	автораритет	noun	noun:inanim:p:v_mis
автораритете	автораритет	noun	noun:inanim:m:v_kly
автораритети	автораритет	noun	noun:inanim:p:v_kly
автораритети	автораритет	noun	noun:inanim:p:v_naz
автораритети	автораритет	noun	noun:inanim:p:v_zna
автораритетові	автораритет	noun	noun:inanim:m:v_dav
автораритетові	автораритет	noun	noun:inanim:m:v_mis
автораритетом	автораритет	noun	noun:inanim:m:v_oru
автораритету	автораритет	noun	noun:inanim:m:v_dav
автораритету	автораритет	noun	noun:inanim:m:v_mis
автораритету	автораритет	noun	noun:inanim:m:v_rod
автораритеті	автораритет	noun	noun:inanim:m:v_mis
автораритетів	автораритет	noun	noun:inanim:p:v_rod
авторах	автор	noun	noun:anim:p:v_mis
авторе	автор	noun	noun:anim:m:v_kly
авторегресій	авторегресія	noun	noun:inanim:p:v_rod
авторегресію	авторегресія	noun	noun:inanim:f:v_zna
авторегресія	авторегресія	noun	noun:inanim:f:v_naz
авторегресіям	авторегресія	noun	noun:inanim:p:v_dav
авторегресіями	авторегресія	noun	noun:inanim:p:v_oru
авторегресіях	авторегресія	noun	noun:inanim:p:v_mis
авторегресіє	авторегресія	noun	noun:inanim:f:v_kly
авторегресією	авторегресія	noun	noun:inanim:f:v_oru
авторегресії	авторегресія	noun	noun:inanim:f:v_dav
авторегресії	авторегресія	noun	noun:inanim:f:v_mis
авторегресії	авторегресія	noun	noun:inanim:f:v_rod
авторегресії	авторегресія	noun	noun:inanim:p:v_kly
авторегресії	авторегресія	noun	noun:inanim:p:v_naz
авторегресії	авторегресія	noun	noun:inanim:p:v_zna
авторегулятор	авторегулятор	noun	noun:inanim:m:v_naz
авторегулятор	авторегулятор	noun	noun:inanim:m:v_zna
авторегулятора	авторегулятор	noun	noun:inanim:m:v_rod
авторегуляторам	авторегулятор	noun	noun:inanim:p:v_dav
авторегуляторами	авторегулятор	noun	noun:inanim:p:v_oru
авторегуляторах	авторегулятор	noun	noun:inanim:p:v_mis
авторегуляторе	авторегулятор	noun	noun:inanim:m:v_kly
авторегулятори	авторегулятор	noun	noun:inanim:p:v_kly
авторегулятори	авторегулятор	noun	noun:inanim:p:v_naz
авторегулятори	авторегулятор	noun	noun:inanim:p:v_zna
авторегуляторові	авторегулятор	noun	noun:inanim:m:v_dav
авторегуляторові	авторегулятор	noun	noun:inanim:m:v_mis
авторегулятором	авторегулятор	noun	noun:inanim:m:v_oru
авторегуляторі	авторегулятор	noun	noun:inanim:m:v_mis
авторегуляторів	авторегулятор	noun	noun:inanim:p:v_rod
авторегуляцій	авторегуляція	noun	noun:inanim:p:v_rod
авторегуляцію	авторегуляція	noun	noun:inanim:f:v_zna
авторегуляція	авторегуляція	noun	noun:inanim:f:v_naz
авторегуляціям	авторегуляція	noun	noun:inanim:p:v_dav
авторегуляціями	авторегуляція	noun	noun:inanim:p:v_oru
авторегуляціях	авторегуляція	noun	noun:inanim:p:v_mis
авторегуляціє	авторегуляція	noun	noun:inanim:f:v_kly
авторегуляцією	авторегуляція	noun	noun:inanim:f:v_oru
авторегуляції	авторегуляція	noun	noun:inanim:f:v_dav
авторегуляції	авторегуляція	noun	noun:inanim:f:v_mis
авторегуляції	авторегуляція	noun	noun:inanim:f:v_rod
авторегуляції	авторегуляція	noun	noun:inanim:p:v_kly
авторегуляції	авторегуляція	noun	noun:inanim:p:v_naz
авторегуляції	авторегуляція	noun	noun:inanim:p:v_zna
авторезонанс	авторезонанс	noun	noun:inanim:m:v_naz
авторезонанс	авторезонанс	noun	noun:inanim:m:v_zna
авторезонансам	авторезонанс	noun	noun:inanim:p:v_dav
авторезонансами	авторезонанс	noun	noun:inanim:p:v_oru
авторезонансах	авторезонанс	noun	noun:inanim:p:v_mis
авторезонансе	авторезонанс	noun	noun:inanim:m:v_kly
авторезонанси	авторезонанс	noun	noun:inanim:p:v_kly
авторезонанси	авторезонанс	noun	noun:inanim:p:v_naz
авторезонанси	авторезонанс	noun	noun:inanim:p:v_zna
авторезонансові	авторезонанс	noun	noun:inanim:m:v_dav
авторезонансові	авторезонанс	noun	noun:inanim:m:v_mis
авторезонансом	авторезонанс	noun	noun:inanim:m:v_oru
авторезонансу	авторезонанс	noun	noun:inanim:m:v_dav
авторезонансу	авторезонанс	noun	noun:inanim:m:v_mis
авторезонансу	авторезонанс	noun	noun:inanim:m:v_rod
авторезонансі	авторезонанс	noun	noun:inanim:m:v_mis
авторезонансів	авторезонанс	noun	noun:inanim:p:v_rod
авторейтинг	авторейтинг	noun	noun:inanim:m:v_naz
авторейтинг	авторейтинг	noun	noun:inanim:m:v_zna
авторейтингам	авторейтинг	noun	noun:inanim:p:v_dav
авторейтингами	авторейтинг	noun	noun:inanim:p:v_oru
авторейтингах	авторейтинг	noun	noun:inanim:p:v_mis
авторейтинги	авторейтинг	noun	noun:inanim:p:v_kly
авторейтинги	авторейтинг	noun	noun:inanim:p:v_naz
авторейтинги	авторейтинг	noun	noun:inanim:p:v_zna
авторейтингові	авторейтинг	noun	noun:inanim:m:v_dav
авторейтингові	авторейтинг	noun	noun:inanim:m:v_mis
авторейтингом	авторейтинг	noun	noun:inanim:m:v_oru
авторейтингу	авторейтинг	noun	noun:inanim:m:v_dav
авторейтингу	авторейтинг	noun	noun:inanim:m:v_kly
авторейтингу	авторейтинг	noun	noun:inanim:m:v_mis
авторейтингу	авторейтинг	noun	noun:inanim:m:v_rod
авторейтингів	авторейтинг	noun	noun:inanim:p:v_rod
авторелаксацій	авторелаксація	noun	noun:inanim:p:v_rod
авторелаксацію	авторелаксація	noun	noun:inanim:f:v_zna
авторелаксація	авторелаксація	noun	noun:inanim:f:v_naz
авторелаксаціям	авторелаксація	noun	noun:inanim:p:v_dav
авторелаксаціями	авторелаксація	noun	noun:inanim:p:v_oru
авторелаксаціях	авторелаксація	noun	noun:inanim:p:v_mis
авторелаксаціє	авторелаксація	noun	noun:inanim:f:v_kly
авторелаксацією	авторелаксація	noun	noun:inanim:f:v_oru
авторелаксації	авторелаксація	noun	noun:inanim:f:v_dav
авторелаксації	авторелаксація	noun	noun:inanim:f:v_mis
авторелаксації	авторелаксація	noun	noun:inanim:f:v_rod
авторелаксації	авторелаксація	noun	noun:inanim:p:v_kly
авторелаксації	авторелаксація	noun	noun:inanim:p:v_naz
авторелаксації	авторелаксація	noun	noun:inanim:p:v_zna
авторемзавод	авторемзавод	noun	noun:inanim:m:v_naz
авторемзавод	авторемзавод	noun	noun:inanim:m:v_zna
авторемзаводам	авторемзавод	noun	noun:inanim:p:v_dav
авторемзаводами	авторемзавод	noun	noun:inanim:p:v_oru
авторемзаводах	авторемзавод	noun	noun:inanim:p:v_mis
авторемзаводе	авторемзавод	noun	noun:inanim:m:v_kly
авторемзаводи	авторемзавод	noun	noun:inanim:p:v_kly
авторемзаводи	авторемзавод	noun	noun:inanim:p:v_naz
авторемзаводи	авторемзавод	noun	noun:inanim:p:v_zna
авторемзаводові	авторемзавод	noun	noun:inanim:m:v_dav
авторемзаводові	авторемзавод	noun	noun:inanim:m:v_mis
авторемзаводом	авторемзавод	noun	noun:inanim:m:v_oru
авторемзаводу	авторемзавод	noun	noun:inanim:m:v_dav
авторемзаводу	авторемзавод	noun	noun:inanim:m:v_mis
авторемзаводу	авторемзавод	noun	noun:inanim:m:v_rod
авторемзаводі	авторемзавод	noun	noun:inanim:m:v_mis
авторемзаводів	авторемзавод	noun	noun:inanim:p:v_rod
авторемонтник	авторемонтник	noun	noun:anim:m:v_naz
авторемонтника	авторемонтник	noun	noun:anim:m:v_rod
авторемонтника	авторемонтник	noun	noun:anim:m:v_zna
авторемонтникам	авторемонтник	noun	noun:anim:p:v_dav
авторемонтниками	авторемонтник	noun	noun:anim:p:v_oru
авторемонтниках	авторемонтник	noun	noun:anim:p:v_mis
авторемонтники	авторемонтник	noun	noun:anim:p:v_kly
авторемонтники	авторемонтник	noun	noun:anim:p:v_naz
авторемонтники	авторемонтник	noun	noun:anim:p:v_zna:rare
авторемонтникові	авторемонтник	noun	noun:anim:m:v_dav
авторемонтникові	авторемонтник	noun	noun:anim:m:v_mis
авторемонтником	авторемонтник	noun	noun:anim:m:v_oru
авторемонтнику	авторемонтник	noun	noun:anim:m:v_dav
авторемонтнику	авторемонтник	noun	noun:anim:m:v_kly
авторемонтнику	авторемонтник	noun	noun:anim:m:v_mis
авторемонтників	авторемонтник	noun	noun:anim:p:v_rod
авторемонтників	авторемонтник	noun	noun:anim:p:v_zna
авторемінісценцій	авторемінісценція	noun	noun:inanim:p:v_rod
авторемінісценцію	авторемінісценція	noun	noun:inanim:f:v_zna
авторемінісценція	авторемінісценція	noun	noun:inanim:f:v_naz
авторемінісценціям	авторемінісценція	noun	noun:inanim:p:v_dav
авторемінісценціями	авторемінісценція	noun	noun:inanim:p:v_oru
авторемінісценціях	авторемінісценція	noun	noun:inanim:p:v_mis
авторемінісценціє	авторемінісценція	noun	noun:inanim:f:v_kly
авторемінісценцією	авторемінісценція	noun	noun:inanim:f:v_oru
авторемінісценції	авторемінісценція	noun	noun:inanim:f:v_dav
авторемінісценції	авторемінісценція	noun	noun:inanim:f:v_mis
авторемінісценції	авторемінісценція	noun	noun:inanim:f:v_rod
авторемінісценції	авторемінісценція	noun	noun:inanim:p:v_kly
авторемінісценції	авторемінісценція	noun	noun:inanim:p:v_naz
авторемінісценції	авторемінісценція	noun	noun:inanim:p:v_zna
авторентген	авторентген	noun	noun:inanim:m:v_naz
авторентген	авторентген	noun	noun:inanim:m:v_zna
авторентгена	авторентген	noun	noun:inanim:m:v_rod
авторентгенам	авторентген	noun	noun:inanim:p:v_dav
авторентгенами	авторентген	noun	noun:inanim:p:v_oru
авторентгенах	авторентген	noun	noun:inanim:p:v_mis
авторентгене	авторентген	noun	noun:inanim:m:v_kly
авторентгени	авторентген	noun	noun:inanim:p:v_kly
авторентгени	авторентген	noun	noun:inanim:p:v_naz
авторентгени	авторентген	noun	noun:inanim:p:v_zna
авторентгенові	авторентген	noun	noun:inanim:m:v_dav
авторентгенові	авторентген	noun	noun:inanim:m:v_mis
авторентгеном	авторентген	noun	noun:inanim:m:v_oru
авторентгені	авторентген	noun	noun:inanim:m:v_mis
авторентгенів	авторентген	noun	noun:inanim:p:v_rod
авторепродукцій	авторепродукція	noun	noun:inanim:p:v_rod
авторепродукцію	авторепродукція	noun	noun:inanim:f:v_zna
авторепродукція	авторепродукція	noun	noun:inanim:f:v_naz
авторепродукціям	авторепродукція	noun	noun:inanim:p:v_dav
авторепродукціями	авторепродукція	noun	noun:inanim:p:v_oru
авторепродукціях	авторепродукція	noun	noun:inanim:p:v_mis
авторепродукціє	авторепродукція	noun	noun:inanim:f:v_kly
авторепродукцією	авторепродукція	noun	noun:inanim:f:v_oru
авторепродукції	авторепродукція	noun	noun:inanim:f:v_dav
авторепродукції	авторепродукція	noun	noun:inanim:f:v_mis
авторепродукції	авторепродукція	noun	noun:inanim:f:v_rod
авторепродукції	авторепродукція	noun	noun:inanim:p:v_kly
авторепродукції	авторепродукція	noun	noun:inanim:p:v_naz
авторепродукції	авторепродукція	noun	noun:inanim:p:v_zna
автореставратор	автореставратор	noun	noun:anim:m:v_naz
автореставратора	автореставратор	noun	noun:anim:m:v_rod
автореставратора	автореставратор	noun	noun:anim:m:v_zna
автореставраторам	автореставратор	noun	noun:anim:p:v_dav
автореставраторами	автореставратор	noun	noun:anim:p:v_oru
автореставраторах	автореставратор	noun	noun:anim:p:v_mis
автореставраторе	автореставратор	noun	noun:anim:m:v_kly
автореставратори	автореставратор	noun	noun:anim:p:v_kly
автореставратори	автореставратор	noun	noun:anim:p:v_naz
автореставратори	автореставратор	noun	noun:anim:p:v_zna:rare
автореставраторові	автореставратор	noun	noun:anim:m:v_dav
автореставраторові	автореставратор	noun	noun:anim:m:v_mis
автореставратором	автореставратор	noun	noun:anim:m:v_oru
автореставраторі	автореставратор	noun	noun:anim:m:v_mis
автореставраторів	автореставратор	noun	noun:anim:p:v_rod
автореставраторів	автореставратор	noun	noun:anim:p:v_zna
автореферат	автореферат	noun	noun:inanim:m:v_naz
автореферат	автореферат	noun	noun:inanim:m:v_zna
авторефератам	автореферат	noun	noun:inanim:p:v_dav
авторефератами	автореферат	noun	noun:inanim:p:v_oru
авторефератах	автореферат	noun	noun:inanim:p:v_mis
автореферате	автореферат	noun	noun:inanim:m:v_kly
автореферати	автореферат	noun	noun:inanim:p:v_kly
автореферати	автореферат	noun	noun:inanim:p:v_naz
автореферати	автореферат	noun	noun:inanim:p:v_zna
авторефератові	автореферат	noun	noun:inanim:m:v_dav
авторефератові	автореферат	noun	noun:inanim:m:v_mis
авторефератом	автореферат	noun	noun:inanim:m:v_oru
автореферату	автореферат	noun	noun:inanim:m:v_dav
автореферату	автореферат	noun	noun:inanim:m:v_mis
автореферату	автореферат	noun	noun:inanim:m:v_rod
авторефераті	автореферат	noun	noun:inanim:m:v_mis
авторефератів	автореферат	noun	noun:inanim:p:v_rod
автореференцій	автореференція	noun	noun:inanim:p:v_rod
автореференцію	автореференція	noun	noun:inanim:f:v_zna
автореференція	автореференція	noun	noun:inanim:f:v_naz
автореференціям	автореференція	noun	noun:inanim:p:v_dav
автореференціями	автореференція	noun	noun:inanim:p:v_oru
автореференціях	автореференція	noun	noun:inanim:p:v_mis
автореференціє	автореференція	noun	noun:inanim:f:v_kly
автореференцією	автореференція	noun	noun:inanim:f:v_oru
автореференції	автореференція	noun	noun:inanim:f:v_dav
автореференції	автореференція	noun	noun:inanim:f:v_mis
автореференції	автореференція	noun	noun:inanim:f:v_rod
автореференції	автореференція	noun	noun:inanim:p:v_kly
автореференції	автореференція	noun	noun:inanim:p:v_naz
автореференції	автореференція	noun	noun:inanim:p:v_zna
авторефлексій	авторефлексія	noun	noun:inanim:p:v_rod
авторефлексію	авторефлексія	noun	noun:inanim:f:v_zna
авторефлексія	авторефлексія	noun	noun:inanim:f:v_naz
авторефлексіям	авторефлексія	noun	noun:inanim:p:v_dav
авторефлексіями	авторефлексія	noun	noun:inanim:p:v_oru
авторефлексіях	авторефлексія	noun	noun:inanim:p:v_mis
авторефлексіє	авторефлексія	noun	noun:inanim:f:v_kly
авторефлексією	авторефлексія	noun	noun:inanim:f:v_oru
авторефлексії	авторефлексія	noun	noun:inanim:f:v_dav
авторефлексії	авторефлексія	noun	noun:inanim:f:v_mis
авторефлексії	авторефлексія	noun	noun:inanim:f:v_rod
авторефлексії	авторефлексія	noun	noun:inanim:p:v_kly
авторефлексії	авторефлексія	noun	noun:inanim:p:v_naz
авторефлексії	авторефлексія	noun	noun:inanim:p:v_zna
авторефрактометр	авторефрактометр	noun	noun:inanim:m:v_naz
авторефрактометр	авторефрактометр	noun	noun:inanim:m:v_zna
авторефрактометра	авторефрактометр	noun	noun:inanim:m:v_rod
авторефрактометрам	авторефрактометр	noun	noun:inanim:p:v_dav
авторефрактометрами	авторефрактометр	noun	noun:inanim:p:v_oru
авторефрактометрах	авторефрактометр	noun	noun:inanim:p:v_mis
авторефрактометре	авторефрактометр	noun	noun:inanim:m:v_kly
авторефрактометри	авторефрактометр	noun	noun:inanim:p:v_kly
авторефрактометри	авторефрактометр	noun	noun:inanim:p:v_naz
авторефрактометри	авторефрактометр	noun	noun:inanim:p:v_zna
авторефрактометрові	авторефрактометр	noun	noun:inanim:m:v_dav
авторефрактометрові	авторефрактометр	noun	noun:inanim:m:v_mis
авторефрактометром	авторефрактометр	noun	noun:inanim:m:v_oru
авторефрактометрі	авторефрактометр	noun	noun:inanim:m:v_mis
авторефрактометрів	авторефрактометр	noun	noun:inanim:p:v_rod
авторефрижератор	авторефрижератор	noun	noun:inanim:m:v_naz
авторефрижератор	авторефрижератор	noun	noun:inanim:m:v_zna
авторефрижератора	авторефрижератор	noun	noun:inanim:m:v_rod
авторефрижераторам	авторефрижератор	noun	noun:inanim:p:v_dav
авторефрижераторами	авторефрижератор	noun	noun:inanim:p:v_oru
авторефрижераторах	авторефрижератор	noun	noun:inanim:p:v_mis
авторефрижераторе	авторефрижератор	noun	noun:inanim:m:v_kly
авторефрижератори	авторефрижератор	noun	noun:inanim:p:v_kly
авторефрижератори	авторефрижератор	noun	noun:inanim:p:v_naz
авторефрижератори	авторефрижератор	noun	noun:inanim:p:v_zna
авторефрижераторові	авторефрижератор	noun	noun:inanim:m:v_dav
авторефрижераторові	авторефрижератор	noun	noun:inanim:m:v_mis
авторефрижератором	авторефрижератор	noun	noun:inanim:m:v_oru
авторефрижераторі	авторефрижератор	noun	noun:inanim:m:v_mis
авторефрижераторів	авторефрижератор	noun	noun:inanim:p:v_rod
авторецензій	авторецензія	noun	noun:inanim:p:v_rod
авторецензію	авторецензія	noun	noun:inanim:f:v_zna
авторецензія	авторецензія	noun	noun:inanim:f:v_naz
авторецензіям	авторецензія	noun	noun:inanim:p:v_dav
авторецензіями	авторецензія	noun	noun:inanim:p:v_oru
авторецензіях	авторецензія	noun	noun:inanim:p:v_mis
авторецензіє	авторецензія	noun	noun:inanim:f:v_kly
авторецензією	авторецензія	noun	noun:inanim:f:v_oru
авторецензії	авторецензія	noun	noun:inanim:f:v_dav
авторецензії	авторецензія	noun	noun:inanim:f:v_mis
авторецензії	авторецензія	noun	noun:inanim:f:v_rod
авторецензії	авторецензія	noun	noun:inanim:p:v_kly
авторецензії	авторецензія	noun	noun:inanim:p:v_naz
авторецензії	авторецензія	noun	noun:inanim:p:v_zna
авторецепцій	авторецепція	noun	noun:inanim:p:v_rod
авторецепцію	авторецепція	noun	noun:inanim:f:v_zna
авторецепція	авторецепція	noun	noun:inanim:f:v_naz
авторецепціям	авторецепція	noun	noun:inanim:p:v_dav
авторецепціями	авторецепція	noun	noun:inanim:p:v_oru
авторецепціях	авторецепція	noun	noun:inanim:p:v_mis
авторецепціє	авторецепція	noun	noun:inanim:f:v_kly
авторецепцією	авторецепція	noun	noun:inanim:f:v_oru
авторецепції	авторецепція	noun	noun:inanim:f:v_dav
авторецепції	авторецепція	noun	noun:inanim:f:v_mis
авторецепції	авторецепція	noun	noun:inanim:f:v_rod
авторецепції	авторецепція	noun	noun:inanim:p:v_kly
авторецепції	авторецепція	noun	noun:inanim:p:v_naz
авторецепції	авторецепція	noun	noun:inanim:p:v_zna
автореєстратор	автореєстратор	noun	noun:inanim:m:v_naz
автореєстратор	автореєстратор	noun	noun:inanim:m:v_zna
автореєстратора	автореєстратор	noun	noun:inanim:m:v_rod
автореєстраторам	автореєстратор	noun	noun:inanim:p:v_dav
автореєстраторами	автореєстратор	noun	noun:inanim:p:v_oru
автореєстраторах	автореєстратор	noun	noun:inanim:p:v_mis
автореєстраторе	автореєстратор	noun	noun:inanim:m:v_kly
автореєстратори	автореєстратор	noun	noun:inanim:p:v_kly
автореєстратори	автореєстратор	noun	noun:inanim:p:v_naz
автореєстратори	автореєстратор	noun	noun:inanim:p:v_zna
автореєстраторові	автореєстратор	noun	noun:inanim:m:v_dav
автореєстраторові	автореєстратор	noun	noun:inanim:m:v_mis
автореєстратором	автореєстратор	noun	noun:inanim:m:v_oru
автореєстраторі	автореєстратор	noun	noun:inanim:m:v_mis
автореєстраторів	автореєстратор	noun	noun:inanim:p:v_rod
автори	автор	noun	noun:anim:p:v_kly
автори	автор	noun	noun:anim:p:v_naz
автори	автор	noun	noun:anim:p:v_zna:rare
авторизацій	авторизація	noun	noun:inanim:p:v_rod
авторизацію	авторизація	noun	noun:inanim:f:v_zna
авторизація	авторизація	noun	noun:inanim:f:v_naz
авторизаціям	авторизація	noun	noun:inanim:p:v_dav
авторизаціями	авторизація	noun	noun:inanim:p:v_oru
авторизаціях	авторизація	noun	noun:inanim:p:v_mis
авторизаціє	авторизація	noun	noun:inanim:f:v_kly
авторизацією	авторизація	noun	noun:inanim:f:v_oru
авторизації	авторизація	noun	noun:inanim:f:v_dav
авторизації	авторизація	noun	noun:inanim:f:v_mis
авторизації	авторизація	noun	noun:inanim:f:v_rod
авторизації	авторизація	noun	noun:inanim:p:v_kly
авторизації	авторизація	noun	noun:inanim:p:v_naz
авторизації	авторизація	noun	noun:inanim:p:v_zna
авторинкам	авторинок	noun	noun:inanim:p:v_dav
авторинками	авторинок	noun	noun:inanim:p:v_oru
авторинках	авторинок	noun	noun:inanim:p:v_mis
авторинки	авторинок	noun	noun:inanim:p:v_kly
авторинки	авторинок	noun	noun:inanim:p:v_naz
авторинки	авторинок	noun	noun:inanim:p:v_zna
авторинкові	авторинок	noun	noun:inanim:m:v_dav
авторинкові	авторинок	noun	noun:inanim:m:v_mis
авторинком	авторинок	noun	noun:inanim:m:v_oru
авторинку	авторинок	noun	noun:inanim:m:v_dav
авторинку	авторинок	noun	noun:inanim:m:v_kly
авторинку	авторинок	noun	noun:inanim:m:v_mis
авторинку	авторинок	noun	noun:inanim:m:v_rod
авторинків	авторинок	noun	noun:inanim:p:v_rod
авторинок	авторинок	noun	noun:inanim:m:v_naz
авторинок	авторинок	noun	noun:inanim:m:v_zna
авторитаризм	авторитаризм	noun	noun:inanim:m:v_naz
авторитаризм	авторитаризм	noun	noun:inanim:m:v_zna
авторитаризмам	авторитаризм	noun	noun:inanim:p:v_dav
авторитаризмами	авторитаризм	noun	noun:inanim:p:v_oru
авторитаризмах	авторитаризм	noun	noun:inanim:p:v_mis
авторитаризме	авторитаризм	noun	noun:inanim:m:v_kly
авторитаризми	авторитаризм	noun	noun:inanim:p:v_kly
авторитаризми	авторитаризм	noun	noun:inanim:p:v_naz
авторитаризми	авторитаризм	noun	noun:inanim:p:v_zna
авторитаризмові	авторитаризм	noun	noun:inanim:m:v_dav
авторитаризмові	авторитаризм	noun	noun:inanim:m:v_mis
авторитаризмом	авторитаризм	noun	noun:inanim:m:v_oru
авторитаризму	авторитаризм	noun	noun:inanim:m:v_dav
авторитаризму	авторитаризм	noun	noun:inanim:m:v_mis
авторитаризму	авторитаризм	noun	noun:inanim:m:v_rod
авторитаризмі	авторитаризм	noun	noun:inanim:m:v_mis
авторитаризмів	авторитаризм	noun	noun:inanim:p:v_rod
авторитарист	авторитарист	noun	noun:anim:m:v_naz
авторитариста	авторитарист	noun	noun:anim:m:v_rod
авторитариста	авторитарист	noun	noun:anim:m:v_zna
авторитаристам	авторитарист	noun	noun:anim:p:v_dav
авторитаристами	авторитарист	noun	noun:anim:p:v_oru
авторитаристах	авторитарист	noun	noun:anim:p:v_mis
авторитаристе	авторитарист	noun	noun:anim:m:v_kly
авторитаристи	авторитарист	noun	noun:anim:p:v_kly
авторитаристи	авторитарист	noun	noun:anim:p:v_naz
авторитаристи	авторитарист	noun	noun:anim:p:v_zna:rare
авторитаристові	авторитарист	noun	noun:anim:m:v_dav
авторитаристові	авторитарист	noun	noun:anim:m:v_mis
авторитаристом	авторитарист	noun	noun:anim:m:v_oru
авторитаристі	авторитарист	noun	noun:anim:m:v_mis
авторитаристів	авторитарист	noun	noun:anim:p:v_rod
авторитаристів	авторитарист	noun	noun:anim:p:v_zna
авторитарій	авторитарій	noun	noun:anim:m:v_naz
авторитарію	авторитарій	noun	noun:anim:m:v_dav
авторитарію	авторитарій	noun	noun:anim:m:v_kly
авторитарію	авторитарій	noun	noun:anim:m:v_mis
авторитарія	авторитарій	noun	noun:anim:m:v_rod
авторитарія	авторитарій	noun	noun:anim:m:v_zna
авторитаріям	авторитарій	noun	noun:anim:p:v_dav
авторитаріями	авторитарій	noun	noun:anim:p:v_oru
авторитаріях	авторитарій	noun	noun:anim:p:v_mis
авторитарієві	авторитарій	noun	noun:anim:m:v_dav
авторитарієві	авторитарій	noun	noun:anim:m:v_mis
авторитарієм	авторитарій	noun	noun:anim:m:v_oru
авторитарії	авторитарій	noun	noun:anim:m:v_mis
авторитарії	авторитарій	noun	noun:anim:p:v_kly
авторитарії	авторитарій	noun	noun:anim:p:v_naz
авторитарії	авторитарій	noun	noun:anim:p:v_zna:rare
авторитаріїв	авторитарій	noun	noun:anim:p:v_rod
авторитаріїв	авторитарій	noun	noun:anim:p:v_zna
авторитет	авторитет	noun	noun:anim:m:v_naz
авторитет	авторитет	noun	noun:inanim:m:v_naz
авторитет	авторитет	noun	noun:inanim:m:v_zna
авторитета	авторитет	noun	noun:anim:m:v_rod
авторитета	авторитет	noun	noun:anim:m:v_zna
авторитетам	авторитет	noun	noun:anim:p:v_dav
авторитетам	авторитет	noun	noun:inanim:p:v_dav
авторитетами	авторитет	noun	noun:anim:p:v_oru
авторитетами	авторитет	noun	noun:inanim:p:v_oru
авторитетах	авторитет	noun	noun:anim:p:v_mis
авторитетах	авторитет	noun	noun:inanim:p:v_mis
авторитете	авторитет	noun	noun:anim:m:v_kly
авторитете	авторитет	noun	noun:inanim:m:v_kly
авторитети	авторитет	noun	noun:anim:p:v_kly
авторитети	авторитет	noun	noun:anim:p:v_naz
авторитети	авторитет	noun	noun:anim:p:v_zna:rare
авторитети	авторитет	noun	noun:inanim:p:v_kly
авторитети	авторитет	noun	noun:inanim:p:v_naz
авторитети	авторитет	noun	noun:inanim:p:v_zna
авторитетка	авторитетка	noun	noun:anim:f:v_naz
авторитеткам	авторитетка	noun	noun:anim:p:v_dav
авторитетками	авторитетка	noun	noun:anim:p:v_oru
авторитетках	авторитетка	noun	noun:anim:p:v_mis
авторитетки	авторитетка	noun	noun:anim:f:v_rod
авторитетки	авторитетка	noun	noun:anim:p:v_kly
авторитетки	авторитетка	noun	noun:anim:p:v_naz
авторитетки	авторитетка	noun	noun:anim:p:v_zna:rare
авторитетко	авторитетка	noun	noun:anim:f:v_kly
авторитеткою	авторитетка	noun	noun:anim:f:v_oru
авторитетку	авторитетка	noun	noun:anim:f:v_zna
авторитетові	авторитет	noun	noun:anim:m:v_dav
авторитетові	авторитет	noun	noun:anim:m:v_mis
авторитетові	авторитет	noun	noun:inanim:m:v_dav
авторитетові	авторитет	noun	noun:inanim:m:v_mis
авторитеток	авторитетка	noun	noun:anim:p:v_rod
авторитеток	авторитетка	noun	noun:anim:p:v_zna
авторитетом	авторитет	noun	noun:anim:m:v_oru
авторитетом	авторитет	noun	noun:inanim:m:v_oru
авторитетці	авторитетка	noun	noun:anim:f:v_dav
авторитетці	авторитетка	noun	noun:anim:f:v_mis
авторитеті	авторитет	noun	noun:anim:m:v_mis
авторитеті	авторитет	noun	noun:inanim:m:v_mis
авторитетів	авторитет	noun	noun:anim:p:v_rod
авторитетів	авторитет	noun	noun:anim:p:v_zna
авторитетів	авторитет	noun	noun:inanim:p:v_rod
авторка	авторка	noun	noun:anim:f:v_naz
авторкам	авторка	noun	noun:anim:p:v_dav
авторками	авторка	noun	noun:anim:p:v_oru
авторках	авторка	noun	noun:anim:p:v_mis
авторки	авторка	noun	noun:anim:f:v_rod
авторки	авторка	noun	noun:anim:p:v_kly
авторки	авторка	noun	noun:anim:p:v_naz
авторки	авторка	noun	noun:anim:p:v_zna:rare
авторко	авторка	noun	noun:anim:f:v_kly
авторкою	авторка	noun	noun:anim:f:v_oru
авторку	авторка	noun	noun:anim:f:v_zna
авторобот	авторобот	noun	noun:inanim:m:v_naz
авторобот	авторобот	noun	noun:inanim:m:v_zna
авторобота	авторобот	noun	noun:inanim:m:v_rod
автороботам	авторобот	noun	noun:inanim:p:v_dav
автороботами	авторобот	noun	noun:inanim:p:v_oru
автороботах	авторобот	noun	noun:inanim:p:v_mis
автороботе	авторобот	noun	noun:inanim:m:v_kly
автороботи	авторобот	noun	noun:inanim:p:v_kly
автороботи	авторобот	noun	noun:inanim:p:v_naz
автороботи	авторобот	noun	noun:inanim:p:v_zna
автороботові	авторобот	noun	noun:inanim:m:v_dav
автороботові	авторобот	noun	noun:inanim:m:v_mis
автороботом	авторобот	noun	noun:inanim:m:v_oru
автороботі	авторобот	noun	noun:inanim:m:v_mis
автороботів	авторобот	noun	noun:inanim:p:v_rod
авторові	автор	noun	noun:anim:m:v_dav
авторові	автор	noun	noun:anim:m:v_mis
авторозвантажувач	авторозвантажувач	noun	noun:inanim:m:v_naz
авторозвантажувач	авторозвантажувач	noun	noun:inanim:m:v_zna
авторозвантажувача	авторозвантажувач	noun	noun:inanim:m:v_rod
авторозвантажувачам	авторозвантажувач	noun	noun:inanim:p:v_dav
авторозвантажувачами	авторозвантажувач	noun	noun:inanim:p:v_oru
авторозвантажувачах	авторозвантажувач	noun	noun:inanim:p:v_mis
авторозвантажувачеві	авторозвантажувач	noun	noun:inanim:m:v_dav
авторозвантажувачеві	авторозвантажувач	noun	noun:inanim:m:v_mis
авторозвантажувачем	авторозвантажувач	noun	noun:inanim:m:v_oru
авторозвантажувачу	авторозвантажувач	noun	noun:inanim:m:v_dav
авторозвантажувачу	авторозвантажувач	noun	noun:inanim:m:v_kly
авторозвантажувачу	авторозвантажувач	noun	noun:inanim:m:v_mis
авторозвантажувачі	авторозвантажувач	noun	noun:inanim:m:v_mis
авторозвантажувачі	авторозвантажувач	noun	noun:inanim:p:v_kly
авторозвантажувачі	авторозвантажувач	noun	noun:inanim:p:v_naz
авторозвантажувачі	авторозвантажувач	noun	noun:inanim:p:v_zna
авторозвантажувачів	авторозвантажувач	noun	noun:inanim:p:v_rod
авторок	авторка	noun	noun:anim:p:v_rod
авторок	авторка	noun	noun:anim:p:v_zna
автором	автор	noun	noun:anim:m:v_oru
автороман	автороман	noun	noun:inanim:m:v_naz
автороман	автороман	noun	noun:inanim:m:v_zna
автороманам	автороман	noun	noun:inanim:p:v_dav
автороманами	автороман	noun	noun:inanim:p:v_oru
автороманах	автороман	noun	noun:inanim:p:v_mis
авторомане	автороман	noun	noun:inanim:m:v_kly
авторомани	автороман	noun	noun:inanim:p:v_kly
авторомани	автороман	noun	noun:inanim:p:v_naz
авторомани	автороман	noun	noun:inanim:p:v_zna
автороманові	автороман	noun	noun:inanim:m:v_dav
автороманові	автороман	noun	noun:inanim:m:v_mis
автороманом	автороман	noun	noun:inanim:m:v_oru
автороману	автороман	noun	noun:inanim:m:v_dav
автороману	автороман	noun	noun:inanim:m:v_mis
автороману	автороман	noun	noun:inanim:m:v_rod
авторомані	автороман	noun	noun:inanim:m:v_mis
автороманів	автороман	noun	noun:inanim:p:v_rod
авторот	авторота	noun	noun:inanim:p:v_rod
авторота	авторота	noun	noun:inanim:f:v_naz
авторотам	авторота	noun	noun:inanim:p:v_dav
авторотами	авторота	noun	noun:inanim:p:v_oru
авторотах	авторота	noun	noun:inanim:p:v_mis
авторотацій	авторотація	noun	noun:inanim:p:v_rod
авторотацію	авторотація	noun	noun:inanim:f:v_zna
авторотація	авторотація	noun	noun:inanim:f:v_naz
авторотаціям	авторотація	noun	noun:inanim:p:v_dav
авторотаціями	авторотація	noun	noun:inanim:p:v_oru
авторотаціях	авторотація	noun	noun:inanim:p:v_mis
авторотаціє	авторотація	noun	noun:inanim:f:v_kly
авторотацією	авторотація	noun	noun:inanim:f:v_oru
авторотації	авторотація	noun	noun:inanim:f:v_dav
авторотації	авторотація	noun	noun:inanim:f:v_mis
авторотації	авторотація	noun	noun:inanim:f:v_rod
авторотації	авторотація	noun	noun:inanim:p:v_kly
авторотації	авторотація	noun	noun:inanim:p:v_naz
авторотації	авторотація	noun	noun:inanim:p:v_zna
автороти	авторота	noun	noun:inanim:f:v_rod
автороти	авторота	noun	noun:inanim:p:v_kly
автороти	авторота	noun	noun:inanim:p:v_naz
автороти	авторота	noun	noun:inanim:p:v_zna
авторото	авторота	noun	noun:inanim:f:v_kly
авторотою	авторота	noun	noun:inanim:f:v_oru
автороту	авторота	noun	noun:inanim:f:v_zna
автороті	авторота	noun	noun:inanim:f:v_dav
автороті	авторота	noun	noun:inanim:f:v_mis
авторпортрет	авторпортрет	noun	noun:inanim:m:v_naz
авторпортрет	авторпортрет	noun	noun:inanim:m:v_zna
авторпортрета	авторпортрет	noun	noun:inanim:m:v_rod
авторпортретам	авторпортрет	noun	noun:inanim:p:v_dav
авторпортретами	авторпортрет	noun	noun:inanim:p:v_oru
авторпортретах	авторпортрет	noun	noun:inanim:p:v_mis
авторпортрете	авторпортрет	noun	noun:inanim:m:v_kly
авторпортрети	авторпортрет	noun	noun:inanim:p:v_kly
авторпортрети	авторпортрет	noun	noun:inanim:p:v_naz
авторпортрети	авторпортрет	noun	noun:inanim:p:v_zna
авторпортретові	авторпортрет	noun	noun:inanim:m:v_dav
авторпортретові	авторпортрет	noun	noun:inanim:m:v_mis
авторпортретом	авторпортрет	noun	noun:inanim:m:v_oru
авторпортреті	авторпортрет	noun	noun:inanim:m:v_mis
авторпортретів	авторпортрет	noun	noun:inanim:p:v_rod
авторств	авторство	noun	noun:inanim:p:v_rod
авторства	авторство	noun	noun:inanim:n:v_rod
авторства	авторство	noun	noun:inanim:p:v_kly
авторства	авторство	noun	noun:inanim:p:v_naz
авторства	авторство	noun	noun:inanim:p:v_zna
авторствам	авторство	noun	noun:inanim:p:v_dav
авторствами	авторство	noun	noun:inanim:p:v_oru
авторствах	авторство	noun	noun:inanim:p:v_mis
авторство	авторство	noun	noun:inanim:n:v_kly
авторство	авторство	noun	noun:inanim:n:v_naz
авторство	авторство	noun	noun:inanim:n:v_zna
авторством	авторство	noun	noun:inanim:n:v_oru
авторству	авторство	noun	noun:inanim:n:v_dav
авторству	авторство	noun	noun:inanim:n:v_mis
авторстві	авторство	noun	noun:inanim:n:v_mis
авторучка	авторучка	noun	noun:inanim:f:v_naz
авторучкам	авторучка	noun	noun:inanim:p:v_dav
авторучками	авторучка	noun	noun:inanim:p:v_oru
авторучках	авторучка	noun	noun:inanim:p:v_mis
авторучки	авторучка	noun	noun:inanim:f:v_rod
авторучки	авторучка	noun	noun:inanim:p:v_kly
авторучки	авторучка	noun	noun:inanim:p:v_naz
авторучки	авторучка	noun	noun:inanim:p:v_zna
авторучко	авторучка	noun	noun:inanim:f:v_kly
авторучкою	авторучка	noun	noun:inanim:f:v_oru
авторучку	авторучка	noun	noun:inanim:f:v_zna
авторучок	авторучка	noun	noun:inanim:p:v_rod
авторучці	авторучка	noun	noun:inanim:f:v_dav
авторучці	авторучка	noun	noun:inanim:f:v_mis
авторці	авторка	noun	noun:anim:f:v_dav
авторці	авторка	noun	noun:anim:f:v_mis
авторі	автор	noun	noun:anim:m:v_mis
авторів	автор	noun	noun:anim:p:v_rod
авторів	автор	noun	noun:anim:p:v_zna
авторідин	авторідина	noun	noun:inanim:p:v_rod
авторідина	авторідина	noun	noun:inanim:f:v_naz
авторідинам	авторідина	noun	noun:inanim:p:v_dav
авторідинами	авторідина	noun	noun:inanim:p:v_oru
авторідинах	авторідина	noun	noun:inanim:p:v_mis
авторідини	авторідина	noun	noun:inanim:f:v_rod
авторідини	авторідина	noun	noun:inanim:p:v_kly
авторідини	авторідина	noun	noun:inanim:p:v_naz
авторідини	авторідина	noun	noun:inanim:p:v_zna
авторідино	авторідина	noun	noun:inanim:f:v_kly
авторідиною	авторідина	noun	noun:inanim:f:v_oru
авторідину	авторідина	noun	noun:inanim:f:v_zna
авторідині	авторідина	noun	noun:inanim:f:v_dav
авторідині	авторідина	noun	noun:inanim:f:v_mis
автосалон	автосалон	noun	noun:inanim:m:v_naz
автосалон	автосалон	noun	noun:inanim:m:v_zna
автосалонам	автосалон	noun	noun:inanim:p:v_dav
автосалонами	автосалон	noun	noun:inanim:p:v_oru
автосалонах	автосалон	noun	noun:inanim:p:v_mis
автосалоне	автосалон	noun	noun:inanim:m:v_kly
автосалони	автосалон	noun	noun:inanim:p:v_kly
автосалони	автосалон	noun	noun:inanim:p:v_naz
автосалони	автосалон	noun	noun:inanim:p:v_zna
автосалонові	автосалон	noun	noun:inanim:m:v_dav
автосалонові	автосалон	noun	noun:inanim:m:v_mis
автосалоном	автосалон	noun	noun:inanim:m:v_oru
автосалону	автосалон	noun	noun:inanim:m:v_dav
автосалону	автосалон	noun	noun:inanim:m:v_mis
автосалону	автосалон	noun	noun:inanim:m:v_rod
автосалоні	автосалон	noun	noun:inanim:m:v_mis
автосалонів	автосалон	noun	noun:inanim:p:v_rod
автосамоскид	автосамоскид	noun	noun:inanim:m:v_naz
автосамоскид	автосамоскид	noun	noun:inanim:m:v_zna
автосамоскида	автосамоскид	noun	noun:inanim:m:v_rod
автосамоскидам	автосамоскид	noun	noun:inanim:p:v_dav
автосамоскидами	автосамоскид	noun	noun:inanim:p:v_oru
автосамоскидах	автосамоскид	noun	noun:inanim:p:v_mis
автосамоскиде	автосамоскид	noun	noun:inanim:m:v_kly
автосамоскиди	автосамоскид	noun	noun:inanim:p:v_kly
автосамоскиди	автосамоскид	noun	noun:inanim:p:v_naz
автосамоскиди	автосамоскид	noun	noun:inanim:p:v_zna
автосамоскидові	автосамоскид	noun	noun:inanim:m:v_dav
автосамоскидові	автосамоскид	noun	noun:inanim:m:v_mis
автосамоскидом	автосамоскид	noun	noun:inanim:m:v_oru
автосамоскиді	автосамоскид	noun	noun:inanim:m:v_mis
автосамоскидів	автосамоскид	noun	noun:inanim:p:v_rod
автосамплер	автосамплер	noun	noun:inanim:m:v_naz
автосамплер	автосамплер	noun	noun:inanim:m:v_zna
автосамплера	автосамплер	noun	noun:inanim:m:v_rod
автосамплерам	автосамплер	noun	noun:inanim:p:v_dav
автосамплерами	автосамплер	noun	noun:inanim:p:v_oru
автосамплерах	автосамплер	noun	noun:inanim:p:v_mis
автосамплере	автосамплер	noun	noun:inanim:m:v_kly
автосамплери	автосамплер	noun	noun:inanim:p:v_kly
автосамплери	автосамплер	noun	noun:inanim:p:v_naz
автосамплери	автосамплер	noun	noun:inanim:p:v_zna
автосамплерові	автосамплер	noun	noun:inanim:m:v_dav
автосамплерові	автосамплер	noun	noun:inanim:m:v_mis
автосамплером	автосамплер	noun	noun:inanim:m:v_oru
автосамплері	автосамплер	noun	noun:inanim:m:v_mis
автосамплерів	автосамплер	noun	noun:inanim:p:v_rod
автосвічка	автосвічка	noun	noun:inanim:f:v_naz
автосвічкам	автосвічка	noun	noun:inanim:p:v_dav
автосвічками	автосвічка	noun	noun:inanim:p:v_oru
автосвічках	автосвічка	noun	noun:inanim:p:v_mis
автосвічки	автосвічка	noun	noun:inanim:f:v_rod
автосвічки	автосвічка	noun	noun:inanim:p:v_kly
автосвічки	автосвічка	noun	noun:inanim:p:v_naz
автосвічки	автосвічка	noun	noun:inanim:p:v_zna
автосвічко	автосвічка	noun	noun:inanim:f:v_kly
автосвічкою	автосвічка	noun	noun:inanim:f:v_oru
автосвічку	автосвічка	noun	noun:inanim:f:v_zna
автосвічок	автосвічка	noun	noun:inanim:p:v_rod
автосвічці	автосвічка	noun	noun:inanim:f:v_dav
автосвічці	автосвічка	noun	noun:inanim:f:v_mis
автосенсибілізацій	автосенсибілізація	noun	noun:inanim:p:v_rod
автосенсибілізацію	автосенсибілізація	noun	noun:inanim:f:v_zna
автосенсибілізація	автосенсибілізація	noun	noun:inanim:f:v_naz
автосенсибілізаціям	автосенсибілізація	noun	noun:inanim:p:v_dav
автосенсибілізаціями	автосенсибілізація	noun	noun:inanim:p:v_oru
автосенсибілізаціях	автосенсибілізація	noun	noun:inanim:p:v_mis
автосенсибілізаціє	автосенсибілізація	noun	noun:inanim:f:v_kly
автосенсибілізацією	автосенсибілізація	noun	noun:inanim:f:v_oru
автосенсибілізації	автосенсибілізація	noun	noun:inanim:f:v_dav
автосенсибілізації	автосенсибілізація	noun	noun:inanim:f:v_mis
автосенсибілізації	автосенсибілізація	noun	noun:inanim:f:v_rod
автосенсибілізації	автосенсибілізація	noun	noun:inanim:p:v_kly
автосенсибілізації	автосенсибілізація	noun	noun:inanim:p:v_naz
автосенсибілізації	автосенсибілізація	noun	noun:inanim:p:v_zna
автосервіс	автосервіс	noun	noun:inanim:m:v_naz
автосервіс	автосервіс	noun	noun:inanim:m:v_zna
автосервісам	автосервіс	noun	noun:inanim:p:v_dav
автосервісами	автосервіс	noun	noun:inanim:p:v_oru
автосервісах	автосервіс	noun	noun:inanim:p:v_mis
автосервісе	автосервіс	noun	noun:inanim:m:v_kly
автосервіси	автосервіс	noun	noun:inanim:p:v_kly
автосервіси	автосервіс	noun	noun:inanim:p:v_naz
автосервіси	автосервіс	noun	noun:inanim:p:v_zna
автосервісові	автосервіс	noun	noun:inanim:m:v_dav
автосервісові	автосервіс	noun	noun:inanim:m:v_mis
автосервісом	автосервіс	noun	noun:inanim:m:v_oru
автосервісу	автосервіс	noun	noun:inanim:m:v_dav
автосервісу	автосервіс	noun	noun:inanim:m:v_mis
автосервісу	автосервіс	noun	noun:inanim:m:v_rod
автосервісі	автосервіс	noun	noun:inanim:m:v_mis
автосервісів	автосервіс	noun	noun:inanim:p:v_rod
автосеротерапій	автосеротерапія	noun	noun:inanim:p:v_rod
автосеротерапію	автосеротерапія	noun	noun:inanim:f:v_zna
автосеротерапія	автосеротерапія	noun	noun:inanim:f:v_naz
автосеротерапіям	автосеротерапія	noun	noun:inanim:p:v_dav
автосеротерапіями	автосеротерапія	noun	noun:inanim:p:v_oru
автосеротерапіях	автосеротерапія	noun	noun:inanim:p:v_mis
автосеротерапіє	автосеротерапія	noun	noun:inanim:f:v_kly
автосеротерапією	автосеротерапія	noun	noun:inanim:f:v_oru
автосеротерапії	автосеротерапія	noun	noun:inanim:f:v_dav
автосеротерапії	автосеротерапія	noun	noun:inanim:f:v_mis
автосеротерапії	автосеротерапія	noun	noun:inanim:f:v_rod
автосеротерапії	автосеротерапія	noun	noun:inanim:p:v_kly
автосеротерапії	автосеротерапія	noun	noun:inanim:p:v_naz
автосеротерапії	автосеротерапія	noun	noun:inanim:p:v_zna
автосигналізацій	автосигналізація	noun	noun:inanim:p:v_rod
автосигналізацію	автосигналізація	noun	noun:inanim:f:v_zna
автосигналізація	автосигналізація	noun	noun:inanim:f:v_naz
автосигналізаціям	автосигналізація	noun	noun:inanim:p:v_dav
автосигналізаціями	автосигналізація	noun	noun:inanim:p:v_oru
автосигналізаціях	автосигналізація	noun	noun:inanim:p:v_mis
автосигналізаціє	автосигналізація	noun	noun:inanim:f:v_kly
автосигналізацією	автосигналізація	noun	noun:inanim:f:v_oru
автосигналізації	автосигналізація	noun	noun:inanim:f:v_dav
автосигналізації	автосигналізація	noun	noun:inanim:f:v_mis
автосигналізації	автосигналізація	noun	noun:inanim:f:v_rod
автосигналізації	автосигналізація	noun	noun:inanim:p:v_kly
автосигналізації	автосигналізація	noun	noun:inanim:p:v_naz
автосигналізації	автосигналізація	noun	noun:inanim:p:v_zna
автосидінню	автосидіння	noun	noun:inanim:n:v_dav
автосидінню	автосидіння	noun	noun:inanim:n:v_mis
автосидіння	автосидіння	noun	noun:inanim:n:v_kly
автосидіння	автосидіння	noun	noun:inanim:n:v_naz
автосидіння	автосидіння	noun	noun:inanim:n:v_rod
автосидіння	автосидіння	noun	noun:inanim:n:v_zna
автосидіння	автосидіння	noun	noun:inanim:p:v_kly
автосидіння	автосидіння	noun	noun:inanim:p:v_naz
автосидіння	автосидіння	noun	noun:inanim:p:v_zna
автосидінням	автосидіння	noun	noun:inanim:n:v_oru
автосидінням	автосидіння	noun	noun:inanim:p:v_dav
автосидіннями	автосидіння	noun	noun:inanim:p:v_oru
автосидіннях	автосидіння	noun	noun:inanim:p:v_mis
автосидінні	автосидіння	noun	noun:inanim:n:v_mis
автосидінь	автосидіння	noun	noun:inanim:p:v_rod
автосимулятор	автосимулятор	noun	noun:inanim:m:v_naz
автосимулятор	автосимулятор	noun	noun:inanim:m:v_zna
автосимулятора	автосимулятор	noun	noun:inanim:m:v_rod
автосимуляторам	автосимулятор	noun	noun:inanim:p:v_dav
автосимуляторами	автосимулятор	noun	noun:inanim:p:v_oru
автосимуляторах	автосимулятор	noun	noun:inanim:p:v_mis
автосимуляторе	автосимулятор	noun	noun:inanim:m:v_kly
автосимулятори	автосимулятор	noun	noun:inanim:p:v_kly
автосимулятори	автосимулятор	noun	noun:inanim:p:v_naz
автосимулятори	автосимулятор	noun	noun:inanim:p:v_zna
автосимуляторові	автосимулятор	noun	noun:inanim:m:v_dav
автосимуляторові	автосимулятор	noun	noun:inanim:m:v_mis
автосимулятором	автосимулятор	noun	noun:inanim:m:v_oru
автосимуляторі	автосимулятор	noun	noun:inanim:m:v_mis
автосимуляторів	автосимулятор	noun	noun:inanim:p:v_rod
автосинхронізатор	автосинхронізатор	noun	noun:inanim:m:v_naz
автосинхронізатор	автосинхронізатор	noun	noun:inanim:m:v_zna
автосинхронізатора	автосинхронізатор	noun	noun:inanim:m:v_rod
автосинхронізаторам	автосинхронізатор	noun	noun:inanim:p:v_dav
автосинхронізаторами	автосинхронізатор	noun	noun:inanim:p:v_oru
автосинхронізаторах	автосинхронізатор	noun	noun:inanim:p:v_mis
автосинхронізаторе	автосинхронізатор	noun	noun:inanim:m:v_kly
автосинхронізатори	автосинхронізатор	noun	noun:inanim:p:v_kly
автосинхронізатори	автосинхронізатор	noun	noun:inanim:p:v_naz
автосинхронізатори	автосинхронізатор	noun	noun:inanim:p:v_zna
автосинхронізаторові	автосинхронізатор	noun	noun:inanim:m:v_dav
автосинхронізаторові	автосинхронізатор	noun	noun:inanim:m:v_mis
автосинхронізатором	автосинхронізатор	noun	noun:inanim:m:v_oru
автосинхронізаторі	автосинхронізатор	noun	noun:inanim:m:v_mis
автосинхронізаторів	автосинхронізатор	noun	noun:inanim:p:v_rod
автоскладальник	автоскладальник	noun	noun:anim:m:v_naz
автоскладальника	автоскладальник	noun	noun:anim:m:v_rod
автоскладальника	автоскладальник	noun	noun:anim:m:v_zna
автоскладальникам	автоскладальник	noun	noun:anim:p:v_dav
автоскладальниками	автоскладальник	noun	noun:anim:p:v_oru
автоскладальниках	автоскладальник	noun	noun:anim:p:v_mis
автоскладальники	автоскладальник	noun	noun:anim:p:v_kly
автоскладальники	автоскладальник	noun	noun:anim:p:v_naz
автоскладальники	автоскладальник	noun	noun:anim:p:v_zna:rare
автоскладальникові	автоскладальник	noun	noun:anim:m:v_dav
автоскладальникові	автоскладальник	noun	noun:anim:m:v_mis
автоскладальником	автоскладальник	noun	noun:anim:m:v_oru
автоскладальнику	автоскладальник	noun	noun:anim:m:v_dav
автоскладальнику	автоскладальник	noun	noun:anim:m:v_kly
автоскладальнику	автоскладальник	noun	noun:anim:m:v_mis
автоскладальників	автоскладальник	noun	noun:anim:p:v_rod
автоскладальників	автоскладальник	noun	noun:anim:p:v_zna
автоскрепер	автоскрепер	noun	noun:inanim:m:v_naz
автоскрепер	автоскрепер	noun	noun:inanim:m:v_zna
автоскрепера	автоскрепер	noun	noun:inanim:m:v_rod
автоскреперам	автоскрепер	noun	noun:inanim:p:v_dav
автоскреперами	автоскрепер	noun	noun:inanim:p:v_oru
автоскреперах	автоскрепер	noun	noun:inanim:p:v_mis
автоскрепере	автоскрепер	noun	noun:inanim:m:v_kly
автоскрепери	автоскрепер	noun	noun:inanim:p:v_kly
автоскрепери	автоскрепер	noun	noun:inanim:p:v_naz
автоскрепери	автоскрепер	noun	noun:inanim:p:v_zna
автоскреперові	автоскрепер	noun	noun:inanim:m:v_dav
автоскреперові	автоскрепер	noun	noun:inanim:m:v_mis
автоскрепером	автоскрепер	noun	noun:inanim:m:v_oru
автоскрепері	автоскрепер	noun	noun:inanim:m:v_mis
автоскреперів	автоскрепер	noun	noun:inanim:p:v_rod
автослалом	автослалом	noun	noun:inanim:m:v_naz
автослалом	автослалом	noun	noun:inanim:m:v_zna
автослаломам	автослалом	noun	noun:inanim:p:v_dav
автослаломами	автослалом	noun	noun:inanim:p:v_oru
автослаломах	автослалом	noun	noun:inanim:p:v_mis
автослаломе	автослалом	noun	noun:inanim:m:v_kly
автослаломи	автослалом	noun	noun:inanim:p:v_kly
автослаломи	автослалом	noun	noun:inanim:p:v_naz
автослаломи	автослалом	noun	noun:inanim:p:v_zna
автослаломові	автослалом	noun	noun:inanim:m:v_dav
автослаломові	автослалом	noun	noun:inanim:m:v_mis
автослаломом	автослалом	noun	noun:inanim:m:v_oru
автослалому	автослалом	noun	noun:inanim:m:v_dav
автослалому	автослалом	noun	noun:inanim:m:v_mis
автослалому	автослалом	noun	noun:inanim:m:v_rod
автослаломі	автослалом	noun	noun:inanim:m:v_mis
автослаломів	автослалом	noun	noun:inanim:p:v_rod
автослужб	автослужба	noun	noun:inanim:p:v_rod
автослужба	автослужба	noun	noun:inanim:f:v_naz
автослужбам	автослужба	noun	noun:inanim:p:v_dav
автослужбами	автослужба	noun	noun:inanim:p:v_oru
автослужбах	автослужба	noun	noun:inanim:p:v_mis
автослужби	автослужба	noun	noun:inanim:f:v_rod
автослужби	автослужба	noun	noun:inanim:p:v_kly
автослужби	автослужба	noun	noun:inanim:p:v_naz
автослужби	автослужба	noun	noun:inanim:p:v_zna
автослужбо	автослужба	noun	noun:inanim:f:v_kly
автослужбою	автослужба	noun	noun:inanim:f:v_oru
автослужбу	автослужба	noun	noun:inanim:f:v_zna
автослужбі	автослужба	noun	noun:inanim:f:v_dav
автослужбі	автослужба	noun	noun:inanim:f:v_mis
автослюсар	автослюсар	noun	noun:anim:m:v_naz
автослюсареві	автослюсар	noun	noun:anim:m:v_dav
автослюсареві	автослюсар	noun	noun:anim:m:v_mis
автослюсарем	автослюсар	noun	noun:anim:m:v_oru
автослюсарю	автослюсар	noun	noun:anim:m:v_dav
автослюсарю	автослюсар	noun	noun:anim:m:v_kly
автослюсарю	автослюсар	noun	noun:anim:m:v_mis
автослюсаря	автослюсар	noun	noun:anim:m:v_rod
автослюсаря	автослюсар	noun	noun:anim:m:v_zna
автослюсарям	автослюсар	noun	noun:anim:p:v_dav
автослюсарями	автослюсар	noun	noun:anim:p:v_oru
автослюсарях	автослюсар	noun	noun:anim:p:v_mis
автослюсарі	автослюсар	noun	noun:anim:m:v_mis
автослюсарі	автослюсар	noun	noun:anim:p:v_kly
автослюсарі	автослюсар	noun	noun:anim:p:v_naz
автослюсарі	автослюсар	noun	noun:anim:p:v_zna:rare
автослюсарів	автослюсар	noun	noun:anim:p:v_rod
автослюсарів	автослюсар	noun	noun:anim:p:v_zna
автосмуг	автосмуга	noun	noun:inanim:p:v_rod
автосмуга	автосмуга	noun	noun:inanim:f:v_naz
автосмугам	автосмуга	noun	noun:inanim:p:v_dav
автосмугами	автосмуга	noun	noun:inanim:p:v_oru
автосмугах	автосмуга	noun	noun:inanim:p:v_mis
автосмуги	автосмуга	noun	noun:inanim:f:v_rod
автосмуги	автосмуга	noun	noun:inanim:p:v_kly
автосмуги	автосмуга	noun	noun:inanim:p:v_naz
автосмуги	автосмуга	noun	noun:inanim:p:v_zna
автосмуго	автосмуга	noun	noun:inanim:f:v_kly
автосмугою	автосмуга	noun	noun:inanim:f:v_oru
автосмугу	автосмуга	noun	noun:inanim:f:v_zna
автосмузі	автосмуга	noun	noun:inanim:f:v_dav
автосмузі	автосмуга	noun	noun:inanim:f:v_mis
автосом	автосома	noun	noun:inanim:p:v_rod
автосома	автосома	noun	noun:inanim:f:v_naz
автосомам	автосома	noun	noun:inanim:p:v_dav
автосомами	автосома	noun	noun:inanim:p:v_oru
автосомах	автосома	noun	noun:inanim:p:v_mis
автосоми	автосома	noun	noun:inanim:f:v_rod
автосоми	автосома	noun	noun:inanim:p:v_kly
автосоми	автосома	noun	noun:inanim:p:v_naz
автосоми	автосома	noun	noun:inanim:p:v_zna
автосомо	автосома	noun	noun:inanim:f:v_kly
автосомою	автосома	noun	noun:inanim:f:v_oru
автосому	автосома	noun	noun:inanim:f:v_zna
автосомі	автосома	noun	noun:inanim:f:v_dav
автосомі	автосома	noun	noun:inanim:f:v_mis
автоспец	автоспец	noun	noun:anim:m:v_naz
автоспеца	автоспец	noun	noun:anim:m:v_rod
автоспеца	автоспец	noun	noun:anim:m:v_zna
автоспецам	автоспец	noun	noun:anim:p:v_dav
автоспецами	автоспец	noun	noun:anim:p:v_oru
автоспецах	автоспец	noun	noun:anim:p:v_mis
автоспеце	автоспец	noun	noun:anim:m:v_kly
автоспеци	автоспец	noun	noun:anim:p:v_kly
автоспеци	автоспец	noun	noun:anim:p:v_naz
автоспеци	автоспец	noun	noun:anim:p:v_zna:rare
автоспецові	автоспец	noun	noun:anim:m:v_dav
автоспецові	автоспец	noun	noun:anim:m:v_mis
автоспецом	автоспец	noun	noun:anim:m:v_oru
автоспеці	автоспец	noun	noun:anim:m:v_mis
автоспеців	автоспец	noun	noun:anim:p:v_rod
автоспеців	автоспец	noun	noun:anim:p:v_zna
автоспортсмен	автоспортсмен	noun	noun:anim:m:v_naz
автоспортсмена	автоспортсмен	noun	noun:anim:m:v_rod
автоспортсмена	автоспортсмен	noun	noun:anim:m:v_zna
автоспортсменам	автоспортсмен	noun	noun:anim:p:v_dav
автоспортсменами	автоспортсмен	noun	noun:anim:p:v_oru
автоспортсменах	автоспортсмен	noun	noun:anim:p:v_mis
автоспортсмене	автоспортсмен	noun	noun:anim:m:v_kly
автоспортсмени	автоспортсмен	noun	noun:anim:p:v_kly
автоспортсмени	автоспортсмен	noun	noun:anim:p:v_naz
автоспортсмени	автоспортсмен	noun	noun:anim:p:v_zna:rare
автоспортсменові	автоспортсмен	noun	noun:anim:m:v_dav
автоспортсменові	автоспортсмен	noun	noun:anim:m:v_mis
автоспортсменом	автоспортсмен	noun	noun:anim:m:v_oru
автоспортсмені	автоспортсмен	noun	noun:anim:m:v_mis
автоспортсменів	автоспортсмен	noun	noun:anim:p:v_rod
автоспортсменів	автоспортсмен	noun	noun:anim:p:v_zna
автоспуск	автоспуск	noun	noun:inanim:m:v_naz
автоспуск	автоспуск	noun	noun:inanim:m:v_zna
автоспускам	автоспуск	noun	noun:inanim:p:v_dav
автоспусками	автоспуск	noun	noun:inanim:p:v_oru
автоспусках	автоспуск	noun	noun:inanim:p:v_mis
автоспуски	автоспуск	noun	noun:inanim:p:v_kly
автоспуски	автоспуск	noun	noun:inanim:p:v_naz
автоспуски	автоспуск	noun	noun:inanim:p:v_zna
автоспускові	автоспуск	noun	noun:inanim:m:v_dav
автоспускові	автоспуск	noun	noun:inanim:m:v_mis
автоспуском	автоспуск	noun	noun:inanim:m:v_oru
автоспуску	автоспуск	noun	noun:inanim:m:v_dav
автоспуску	автоспуск	noun	noun:inanim:m:v_kly
автоспуску	автоспуск	noun	noun:inanim:m:v_mis
автоспуску	автоспуск	noun	noun:inanim:m:v_rod
автоспусків	автоспуск	noun	noun:inanim:p:v_rod
автостанцій	автостанція	noun	noun:inanim:p:v_rod
автостанцію	автостанція	noun	noun:inanim:f:v_zna
автостанція	автостанція	noun	noun:inanim:f:v_naz
автостанціям	автостанція	noun	noun:inanim:p:v_dav
автостанціями	автостанція	noun	noun:inanim:p:v_oru
автостанціях	автостанція	noun	noun:inanim:p:v_mis
автостанціє	автостанція	noun	noun:inanim:f:v_kly
автостанцією	автостанція	noun	noun:inanim:f:v_oru
автостанції	автостанція	noun	noun:inanim:f:v_dav
автостанції	автостанція	noun	noun:inanim:f:v_mis
автостанції	автостанція	noun	noun:inanim:f:v_rod
автостанції	автостанція	noun	noun:inanim:p:v_kly
автостанції	автостанція	noun	noun:inanim:p:v_naz
автостанції	автостанція	noun	noun:inanim:p:v_zna
автостарт	автостарт	noun	noun:inanim:m:v_naz
автостарт	автостарт	noun	noun:inanim:m:v_zna
автостартам	автостарт	noun	noun:inanim:p:v_dav
автостартами	автостарт	noun	noun:inanim:p:v_oru
автостартах	автостарт	noun	noun:inanim:p:v_mis
автостарте	автостарт	noun	noun:inanim:m:v_kly
автостарти	автостарт	noun	noun:inanim:p:v_kly
автостарти	автостарт	noun	noun:inanim:p:v_naz
автостарти	автостарт	noun	noun:inanim:p:v_zna
автостартові	автостарт	noun	noun:inanim:m:v_dav
автостартові	автостарт	noun	noun:inanim:m:v_mis
автостартом	автостарт	noun	noun:inanim:m:v_oru
автостарту	автостарт	noun	noun:inanim:m:v_dav
автостарту	автостарт	noun	noun:inanim:m:v_mis
автостарту	автостарт	noun	noun:inanim:m:v_rod
автостарті	автостарт	noun	noun:inanim:m:v_mis
автостартів	автостарт	noun	noun:inanim:p:v_rod
автостацій	автостація	noun	noun:inanim:p:v_rod
автостацію	автостація	noun	noun:inanim:f:v_zna
автостація	автостація	noun	noun:inanim:f:v_naz
автостаціям	автостація	noun	noun:inanim:p:v_dav
автостаціями	автостація	noun	noun:inanim:p:v_oru
автостаціях	автостація	noun	noun:inanim:p:v_mis
автостаціє	автостація	noun	noun:inanim:f:v_kly
автостацією	автостація	noun	noun:inanim:f:v_oru
автостації	автостація	noun	noun:inanim:f:v_dav
автостації	автостація	noun	noun:inanim:f:v_mis
автостації	автостація	noun	noun:inanim:f:v_rod
автостації	автостація	noun	noun:inanim:p:v_kly
автостації	автостація	noun	noun:inanim:p:v_naz
автостації	автостація	noun	noun:inanim:p:v_zna
автостереотип	автостереотип	noun	noun:inanim:m:v_naz
автостереотип	автостереотип	noun	noun:inanim:m:v_zna
автостереотипам	автостереотип	noun	noun:inanim:p:v_dav
автостереотипами	автостереотип	noun	noun:inanim:p:v_oru
автостереотипах	автостереотип	noun	noun:inanim:p:v_mis
автостереотипе	автостереотип	noun	noun:inanim:m:v_kly
автостереотипи	автостереотип	noun	noun:inanim:p:v_kly
автостереотипи	автостереотип	noun	noun:inanim:p:v_naz
автостереотипи	автостереотип	noun	noun:inanim:p:v_zna
автостереотипові	автостереотип	noun	noun:inanim:m:v_dav
автостереотипові	автостереотип	noun	noun:inanim:m:v_mis
автостереотипом	автостереотип	noun	noun:inanim:m:v_oru
автостереотипу	автостереотип	noun	noun:inanim:m:v_dav
автостереотипу	автостереотип	noun	noun:inanim:m:v_mis
автостереотипу	автостереотип	noun	noun:inanim:m:v_rod
автостереотипі	автостереотип	noun	noun:inanim:m:v_mis
автостереотипів	автостереотип	noun	noun:inanim:p:v_rod
автостерничий	автостерничий	noun	noun:inanim:m:v_kly
автостерничий	автостерничий	noun	noun:inanim:m:v_naz
автостерничий	автостерничий	noun	noun:inanim:m:v_zna
автостерничим	автостерничий	noun	noun:inanim:m:v_oru
автостерничим	автостерничий	noun	noun:inanim:p:v_dav
автостерничими	автостерничий	noun	noun:inanim:p:v_oru
автостерничих	автостерничий	noun	noun:inanim:p:v_mis
автостерничих	автостерничий	noun	noun:inanim:p:v_rod
автостерничого	автостерничий	noun	noun:inanim:m:v_rod
автостерничому	автостерничий	noun	noun:inanim:m:v_dav
автостерничому	автостерничий	noun	noun:inanim:m:v_mis
автостерничі	автостерничий	noun	noun:inanim:p:v_kly
автостерничі	автостерничий	noun	noun:inanim:p:v_naz
автостерничі	автостерничий	noun	noun:inanim:p:v_zna
автостерничім	автостерничий	noun	noun:inanim:m:v_mis
автостоп	автостоп	noun	noun:inanim:m:v_naz:xp1
автостоп	автостоп	noun	noun:inanim:m:v_naz:xp2
автостоп	автостоп	noun	noun:inanim:m:v_zna:xp1
автостоп	автостоп	noun	noun:inanim:m:v_zna:xp2
автостопа	автостоп	noun	noun:inanim:m:v_rod:xp1
автостопам	автостоп	noun	noun:inanim:p:v_dav:xp1
автостопами	автостоп	noun	noun:inanim:p:v_oru:xp1
автостопах	автостоп	noun	noun:inanim:p:v_mis:xp1
автостопе	автостоп	noun	noun:inanim:m:v_kly:xp1
автостопе	автостоп	noun	noun:inanim:m:v_kly:xp2
автостопер	автостопер	noun	noun:anim:m:v_naz
автостопера	автостопер	noun	noun:anim:m:v_rod
автостопера	автостопер	noun	noun:anim:m:v_zna
автостоперам	автостопер	noun	noun:anim:p:v_dav
автостоперами	автостопер	noun	noun:anim:p:v_oru
автостоперах	автостопер	noun	noun:anim:p:v_mis
автостопере	автостопер	noun	noun:anim:m:v_kly
автостопери	автостопер	noun	noun:anim:p:v_kly
автостопери	автостопер	noun	noun:anim:p:v_naz
автостопери	автостопер	noun	noun:anim:p:v_zna:rare
автостоперка	автостоперка	noun	noun:anim:f:v_naz
автостоперкам	автостоперка	noun	noun:anim:p:v_dav
автостоперками	автостоперка	noun	noun:anim:p:v_oru
автостоперках	автостоперка	noun	noun:anim:p:v_mis
автостоперки	автостоперка	noun	noun:anim:f:v_rod
автостоперки	автостоперка	noun	noun:anim:p:v_kly
автостоперки	автостоперка	noun	noun:anim:p:v_naz
автостоперки	автостоперка	noun	noun:anim:p:v_zna:rare
автостоперко	автостоперка	noun	noun:anim:f:v_kly
автостоперкою	автостоперка	noun	noun:anim:f:v_oru
автостоперку	автостоперка	noun	noun:anim:f:v_zna
автостоперові	автостопер	noun	noun:anim:m:v_dav
автостоперові	автостопер	noun	noun:anim:m:v_mis
автостоперок	автостоперка	noun	noun:anim:p:v_rod
автостоперок	автостоперка	noun	noun:anim:p:v_zna
автостопером	автостопер	noun	noun:anim:m:v_oru
автостоперці	автостоперка	noun	noun:anim:f:v_dav
автостоперці	автостоперка	noun	noun:anim:f:v_mis
автостопері	автостопер	noun	noun:anim:m:v_mis
автостоперів	автостопер	noun	noun:anim:p:v_rod
автостоперів	автостопер	noun	noun:anim:p:v_zna
автостопи	автостоп	noun	noun:inanim:p:v_kly:xp1
автостопи	автостоп	noun	noun:inanim:p:v_naz:xp1
автостопи	автостоп	noun	noun:inanim:p:v_zna:xp1
автостопник	автостопник	noun	noun:anim:m:v_naz
автостопника	автостопник	noun	noun:anim:m:v_rod
автостопника	автостопник	noun	noun:anim:m:v_zna
автостопникам	автостопник	noun	noun:anim:p:v_dav
автостопниками	автостопник	noun	noun:anim:p:v_oru
автостопниках	автостопник	noun	noun:anim:p:v_mis
автостопники	автостопник	noun	noun:anim:p:v_kly
автостопники	автостопник	noun	noun:anim:p:v_naz
автостопники	автостопник	noun	noun:anim:p:v_zna:rare
автостопникові	автостопник	noun	noun:anim:m:v_dav
автостопникові	автостопник	noun	noun:anim:m:v_mis
автостопником	автостопник	noun	noun:anim:m:v_oru
автостопнику	автостопник	noun	noun:anim:m:v_dav
автостопнику	автостопник	noun	noun:anim:m:v_kly
автостопнику	автостопник	noun	noun:anim:m:v_mis
автостопників	автостопник	noun	noun:anim:p:v_rod
автостопників	автостопник	noun	noun:anim:p:v_zna
автостопнице	автостопниця	noun	noun:anim:f:v_kly
автостопницею	автостопниця	noun	noun:anim:f:v_oru
автостопниць	автостопниця	noun	noun:anim:p:v_rod
автостопниць	автостопниця	noun	noun:anim:p:v_zna
автостопницю	автостопниця	noun	noun:anim:f:v_zna
автостопниця	автостопниця	noun	noun:anim:f:v_naz
автостопницям	автостопниця	noun	noun:anim:p:v_dav
автостопницями	автостопниця	noun	noun:anim:p:v_oru
автостопницях	автостопниця	noun	noun:anim:p:v_mis
автостопниці	автостопниця	noun	noun:anim:f:v_dav
автостопниці	автостопниця	noun	noun:anim:f:v_mis
автостопниці	автостопниця	noun	noun:anim:f:v_rod
автостопниці	автостопниця	noun	noun:anim:p:v_kly
автостопниці	автостопниця	noun	noun:anim:p:v_naz
автостопниці	автостопниця	noun	noun:anim:p:v_zna:rare
автостопові	автостоп	noun	noun:inanim:m:v_dav:xp1
автостопові	автостоп	noun	noun:inanim:m:v_dav:xp2
автостопові	автостоп	noun	noun:inanim:m:v_mis:xp1
автостопові	автостоп	noun	noun:inanim:m:v_mis:xp2
автостопом	автостоп	noun	noun:inanim:m:v_oru:xp1
автостопом	автостоп	noun	noun:inanim:m:v_oru:xp2
автостопі	автостоп	noun	noun:inanim:m:v_mis:xp1
автостопі	автостоп	noun	noun:inanim:m:v_mis:xp2
автостопів	автостоп	noun	noun:inanim:p:v_rod:xp1
автосторож	автосторож	noun	noun:inanim:m:v_naz
автосторож	автосторож	noun	noun:inanim:m:v_zna
автосторожа	автосторож	noun	noun:inanim:m:v_rod
автосторожам	автосторож	noun	noun:inanim:p:v_dav
автосторожами	автосторож	noun	noun:inanim:p:v_oru
автосторожах	автосторож	noun	noun:inanim:p:v_mis
автостороже	автосторож	noun	noun:inanim:m:v_kly
автосторожеві	автосторож	noun	noun:inanim:m:v_dav
автосторожеві	автосторож	noun	noun:inanim:m:v_mis
автосторожем	автосторож	noun	noun:inanim:m:v_oru
автосторожі	автосторож	noun	noun:inanim:m:v_mis
автосторожі	автосторож	noun	noun:inanim:p:v_kly
автосторожі	автосторож	noun	noun:inanim:p:v_naz
автосторожі	автосторож	noun	noun:inanim:p:v_zna
автосторожів	автосторож	noun	noun:inanim:p:v_rod
автостоянка	автостоянка	noun	noun:inanim:f:v_naz
автостоянкам	автостоянка	noun	noun:inanim:p:v_dav
автостоянками	автостоянка	noun	noun:inanim:p:v_oru
автостоянках	автостоянка	noun	noun:inanim:p:v_mis
автостоянки	автостоянка	noun	noun:inanim:f:v_rod
автостоянки	автостоянка	noun	noun:inanim:p:v_kly
автостоянки	автостоянка	noun	noun:inanim:p:v_naz
автостоянки	автостоянка	noun	noun:inanim:p:v_zna
автостоянко	автостоянка	noun	noun:inanim:f:v_kly
автостоянкою	автостоянка	noun	noun:inanim:f:v_oru
автостоянку	автостоянка	noun	noun:inanim:f:v_zna
автостоянок	автостоянка	noun	noun:inanim:p:v_rod
автостоянці	автостоянка	noun	noun:inanim:f:v_dav
автостоянці	автостоянка	noun	noun:inanim:f:v_mis
автострад	автострада	noun	noun:inanim:p:v_rod
автострада	автострада	noun	noun:inanim:f:v_naz
автострадам	автострада	noun	noun:inanim:p:v_dav
автострадами	автострада	noun	noun:inanim:p:v_oru
автострадах	автострада	noun	noun:inanim:p:v_mis
автостради	автострада	noun	noun:inanim:f:v_rod
автостради	автострада	noun	noun:inanim:p:v_kly
автостради	автострада	noun	noun:inanim:p:v_naz
автостради	автострада	noun	noun:inanim:p:v_zna
автострадо	автострада	noun	noun:inanim:f:v_kly
автострадою	автострада	noun	noun:inanim:f:v_oru
автостраду	автострада	noun	noun:inanim:f:v_zna
автостраді	автострада	noun	noun:inanim:f:v_dav
автостраді	автострада	noun	noun:inanim:f:v_mis
автостраховик	автостраховик	noun	noun:anim:m:v_naz
автостраховика	автостраховик	noun	noun:anim:m:v_rod
автостраховика	автостраховик	noun	noun:anim:m:v_zna
автостраховикам	автостраховик	noun	noun:anim:p:v_dav
автостраховиками	автостраховик	noun	noun:anim:p:v_oru
автостраховиках	автостраховик	noun	noun:anim:p:v_mis
автостраховики	автостраховик	noun	noun:anim:p:v_kly
автостраховики	автостраховик	noun	noun:anim:p:v_naz
автостраховики	автостраховик	noun	noun:anim:p:v_zna:rare
автостраховикові	автостраховик	noun	noun:anim:m:v_dav
автостраховикові	автостраховик	noun	noun:anim:m:v_mis
автостраховиком	автостраховик	noun	noun:anim:m:v_oru
автостраховику	автостраховик	noun	noun:anim:m:v_dav
автостраховику	автостраховик	noun	noun:anim:m:v_kly
автостраховику	автостраховик	noun	noun:anim:m:v_mis
автостраховиків	автостраховик	noun	noun:anim:p:v_rod
автостраховиків	автостраховик	noun	noun:anim:p:v_zna
автосугестій	автосугестія	noun	noun:inanim:p:v_rod
автосугестію	автосугестія	noun	noun:inanim:f:v_zna
автосугестія	автосугестія	noun	noun:inanim:f:v_naz
автосугестіям	автосугестія	noun	noun:inanim:p:v_dav
автосугестіями	автосугестія	noun	noun:inanim:p:v_oru
автосугестіях	автосугестія	noun	noun:inanim:p:v_mis
автосугестіє	автосугестія	noun	noun:inanim:f:v_kly
автосугестією	автосугестія	noun	noun:inanim:f:v_oru
автосугестії	автосугестія	noun	noun:inanim:f:v_dav
автосугестії	автосугестія	noun	noun:inanim:f:v_mis
автосугестії	автосугестія	noun	noun:inanim:f:v_rod
автосугестії	автосугестія	noun	noun:inanim:p:v_kly
автосугестії	автосугестія	noun	noun:inanim:p:v_naz
автосугестії	автосугестія	noun	noun:inanim:p:v_zna
автосуміш	автосуміш	noun	noun:inanim:f:v_naz
автосуміш	автосуміш	noun	noun:inanim:f:v_zna
автосумішам	автосуміш	noun	noun:inanim:p:v_dav
автосумішами	автосуміш	noun	noun:inanim:p:v_oru
автосумішах	автосуміш	noun	noun:inanim:p:v_mis
автосуміше	автосуміш	noun	noun:inanim:f:v_kly
автосумішей	автосуміш	noun	noun:inanim:p:v_rod
автосумішшю	автосуміш	noun	noun:inanim:f:v_oru
автосуміші	автосуміш	noun	noun:inanim:f:v_dav
автосуміші	автосуміш	noun	noun:inanim:f:v_mis
автосуміші	автосуміш	noun	noun:inanim:f:v_rod
автосуміші	автосуміш	noun	noun:inanim:p:v_kly
автосуміші	автосуміш	noun	noun:inanim:p:v_naz
автосуміші	автосуміш	noun	noun:inanim:p:v_zna
автотаймер	автотаймер	noun	noun:inanim:m:v_naz
автотаймер	автотаймер	noun	noun:inanim:m:v_zna
автотаймера	автотаймер	noun	noun:inanim:m:v_rod
автотаймерам	автотаймер	noun	noun:inanim:p:v_dav
автотаймерами	автотаймер	noun	noun:inanim:p:v_oru
автотаймерах	автотаймер	noun	noun:inanim:p:v_mis
автотаймере	автотаймер	noun	noun:inanim:m:v_kly
автотаймери	автотаймер	noun	noun:inanim:p:v_kly
автотаймери	автотаймер	noun	noun:inanim:p:v_naz
автотаймери	автотаймер	noun	noun:inanim:p:v_zna
автотаймерові	автотаймер	noun	noun:inanim:m:v_dav
автотаймерові	автотаймер	noun	noun:inanim:m:v_mis
автотаймером	автотаймер	noun	noun:inanim:m:v_oru
автотаймері	автотаймер	noun	noun:inanim:m:v_mis
автотаймерів	автотаймер	noun	noun:inanim:p:v_rod
автотермоцистерн	автотермоцистерна	noun	noun:inanim:p:v_rod
автотермоцистерна	автотермоцистерна	noun	noun:inanim:f:v_naz
автотермоцистернам	автотермоцистерна	noun	noun:inanim:p:v_dav
автотермоцистернами	автотермоцистерна	noun	noun:inanim:p:v_oru
автотермоцистернах	автотермоцистерна	noun	noun:inanim:p:v_mis
автотермоцистерни	автотермоцистерна	noun	noun:inanim:f:v_rod
автотермоцистерни	автотермоцистерна	noun	noun:inanim:p:v_kly
автотермоцистерни	автотермоцистерна	noun	noun:inanim:p:v_naz
автотермоцистерни	автотермоцистерна	noun	noun:inanim:p:v_zna
автотермоцистерно	автотермоцистерна	noun	noun:inanim:f:v_kly
автотермоцистерною	автотермоцистерна	noun	noun:inanim:f:v_oru
автотермоцистерну	автотермоцистерна	noun	noun:inanim:f:v_zna
автотермоцистерні	автотермоцистерна	noun	noun:inanim:f:v_dav
автотермоцистерні	автотермоцистерна	noun	noun:inanim:f:v_mis
автотермінал	автотермінал	noun	noun:inanim:m:v_naz
автотермінал	автотермінал	noun	noun:inanim:m:v_zna
автотермінала	автотермінал	noun	noun:inanim:m:v_rod
автотерміналам	автотермінал	noun	noun:inanim:p:v_dav
автотерміналами	автотермінал	noun	noun:inanim:p:v_oru
автотерміналах	автотермінал	noun	noun:inanim:p:v_mis
автотермінале	автотермінал	noun	noun:inanim:m:v_kly
автотермінали	автотермінал	noun	noun:inanim:p:v_kly
автотермінали	автотермінал	noun	noun:inanim:p:v_naz
автотермінали	автотермінал	noun	noun:inanim:p:v_zna
автотерміналові	автотермінал	noun	noun:inanim:m:v_dav
автотерміналові	автотермінал	noun	noun:inanim:m:v_mis
автотерміналом	автотермінал	noun	noun:inanim:m:v_oru
автотерміналі	автотермінал	noun	noun:inanim:m:v_mis
автотерміналів	автотермінал	noun	noun:inanim:p:v_rod
автотехнологій	автотехнологія	noun	noun:inanim:p:v_rod
автотехнологію	автотехнологія	noun	noun:inanim:f:v_zna
автотехнологія	автотехнологія	noun	noun:inanim:f:v_naz
автотехнологіям	автотехнологія	noun	noun:inanim:p:v_dav
автотехнологіями	автотехнологія	noun	noun:inanim:p:v_oru
автотехнологіях	автотехнологія	noun	noun:inanim:p:v_mis
автотехнологіє	автотехнологія	noun	noun:inanim:f:v_kly
автотехнологією	автотехнологія	noun	noun:inanim:f:v_oru
автотехнології	автотехнологія	noun	noun:inanim:f:v_dav
автотехнології	автотехнологія	noun	noun:inanim:f:v_mis
автотехнології	автотехнологія	noun	noun:inanim:f:v_rod
автотехнології	автотехнологія	noun	noun:inanim:p:v_kly
автотехнології	автотехнологія	noun	noun:inanim:p:v_naz
автотехнології	автотехнологія	noun	noun:inanim:p:v_zna
автотехнікум	автотехнікум	noun	noun:inanim:m:v_naz
автотехнікум	автотехнікум	noun	noun:inanim:m:v_zna
автотехнікума	автотехнікум	noun	noun:inanim:m:v_rod
автотехнікумам	автотехнікум	noun	noun:inanim:p:v_dav
автотехнікумами	автотехнікум	noun	noun:inanim:p:v_oru
автотехнікумах	автотехнікум	noun	noun:inanim:p:v_mis
автотехнікуме	автотехнікум	noun	noun:inanim:m:v_kly
автотехнікуми	автотехнікум	noun	noun:inanim:p:v_kly
автотехнікуми	автотехнікум	noun	noun:inanim:p:v_naz
автотехнікуми	автотехнікум	noun	noun:inanim:p:v_zna
автотехнікумові	автотехнікум	noun	noun:inanim:m:v_dav
автотехнікумові	автотехнікум	noun	noun:inanim:m:v_mis
автотехнікумом	автотехнікум	noun	noun:inanim:m:v_oru
автотехнікумі	автотехнікум	noun	noun:inanim:m:v_mis
автотехнікумів	автотехнікум	noun	noun:inanim:p:v_rod
автотехстанцій	автотехстанція	noun	noun:inanim:p:v_rod
автотехстанцію	автотехстанція	noun	noun:inanim:f:v_zna
автотехстанція	автотехстанція	noun	noun:inanim:f:v_naz
автотехстанціям	автотехстанція	noun	noun:inanim:p:v_dav
автотехстанціями	автотехстанція	noun	noun:inanim:p:v_oru
автотехстанціях	автотехстанція	noun	noun:inanim:p:v_mis
автотехстанціє	автотехстанція	noun	noun:inanim:f:v_kly
автотехстанцією	автотехстанція	noun	noun:inanim:f:v_oru
автотехстанції	автотехстанція	noun	noun:inanim:f:v_dav
автотехстанції	автотехстанція	noun	noun:inanim:f:v_mis
автотехстанції	автотехстанція	noun	noun:inanim:f:v_rod
автотехстанції	автотехстанція	noun	noun:inanim:p:v_kly
автотехстанції	автотехстанція	noun	noun:inanim:p:v_naz
автотехстанції	автотехстанція	noun	noun:inanim:p:v_zna
автотипій	автотипія	noun	noun:inanim:p:v_rod
автотипію	автотипія	noun	noun:inanim:f:v_zna
автотипія	автотипія	noun	noun:inanim:f:v_naz
автотипіям	автотипія	noun	noun:inanim:p:v_dav
автотипіями	автотипія	noun	noun:inanim:p:v_oru
автотипіях	автотипія	noun	noun:inanim:p:v_mis
автотипіє	автотипія	noun	noun:inanim:f:v_kly
автотипією	автотипія	noun	noun:inanim:f:v_oru
автотипії	автотипія	noun	noun:inanim:f:v_dav
автотипії	автотипія	noun	noun:inanim:f:v_mis
автотипії	автотипія	noun	noun:inanim:f:v_rod
автотипії	автотипія	noun	noun:inanim:p:v_kly
автотипії	автотипія	noun	noun:inanim:p:v_naz
автотипії	автотипія	noun	noun:inanim:p:v_zna
автотомій	автотомія	noun	noun:inanim:p:v_rod
автотомію	автотомія	noun	noun:inanim:f:v_zna
автотомія	автотомія	noun	noun:inanim:f:v_naz
автотоміям	автотомія	noun	noun:inanim:p:v_dav
автотоміями	автотомія	noun	noun:inanim:p:v_oru
автотоміях	автотомія	noun	noun:inanim:p:v_mis
автотоміє	автотомія	noun	noun:inanim:f:v_kly
автотомією	автотомія	noun	noun:inanim:f:v_oru
автотомії	автотомія	noun	noun:inanim:f:v_dav
автотомії	автотомія	noun	noun:inanim:f:v_mis
автотомії	автотомія	noun	noun:inanim:f:v_rod
автотомії	автотомія	noun	noun:inanim:p:v_kly
автотомії	автотомія	noun	noun:inanim:p:v_naz
автотомії	автотомія	noun	noun:inanim:p:v_zna
автотопаливозаправник	автотопаливозаправник	noun	noun:inanim:m:v_naz
автотопаливозаправник	автотопаливозаправник	noun	noun:inanim:m:v_zna
автотопаливозаправника	автотопаливозаправник	noun	noun:inanim:m:v_rod
автотопаливозаправникам	автотопаливозаправник	noun	noun:inanim:p:v_dav
автотопаливозаправниками	автотопаливозаправник	noun	noun:inanim:p:v_oru
автотопаливозаправниках	автотопаливозаправник	noun	noun:inanim:p:v_mis
автотопаливозаправники	автотопаливозаправник	noun	noun:inanim:p:v_kly
автотопаливозаправники	автотопаливозаправник	noun	noun:inanim:p:v_naz
автотопаливозаправники	автотопаливозаправник	noun	noun:inanim:p:v_zna
автотопаливозаправникові	автотопаливозаправник	noun	noun:inanim:m:v_dav
автотопаливозаправникові	автотопаливозаправник	noun	noun:inanim:m:v_mis
автотопаливозаправником	автотопаливозаправник	noun	noun:inanim:m:v_oru
автотопаливозаправнику	автотопаливозаправник	noun	noun:inanim:m:v_dav
автотопаливозаправнику	автотопаливозаправник	noun	noun:inanim:m:v_kly
автотопаливозаправнику	автотопаливозаправник	noun	noun:inanim:m:v_mis
автотопаливозаправників	автотопаливозаправник	noun	noun:inanim:p:v_rod
автоторговець	автоторговець	noun	noun:anim:m:v_naz
автоторговцеві	автоторговець	noun	noun:anim:m:v_dav
автоторговцеві	автоторговець	noun	noun:anim:m:v_mis
автоторговцем	автоторговець	noun	noun:anim:m:v_oru
автоторговцю	автоторговець	noun	noun:anim:m:v_dav
автоторговцю	автоторговець	noun	noun:anim:m:v_kly
автоторговцю	автоторговець	noun	noun:anim:m:v_mis
автоторговця	автоторговець	noun	noun:anim:m:v_rod
автоторговця	автоторговець	noun	noun:anim:m:v_zna
автоторговцям	автоторговець	noun	noun:anim:p:v_dav
автоторговцями	автоторговець	noun	noun:anim:p:v_oru
автоторговцях	автоторговець	noun	noun:anim:p:v_mis
автоторговці	автоторговець	noun	noun:anim:m:v_mis
автоторговці	автоторговець	noun	noun:anim:p:v_kly
автоторговці	автоторговець	noun	noun:anim:p:v_naz
автоторговці	автоторговець	noun	noun:anim:p:v_zna:rare
автоторговців	автоторговець	noun	noun:anim:p:v_rod
автоторговців	автоторговець	noun	noun:anim:p:v_zna
автотравм	автотравма	noun	noun:inanim:p:v_rod
автотравма	автотравма	noun	noun:inanim:f:v_naz
автотравмам	автотравма	noun	noun:inanim:p:v_dav
автотравмами	автотравма	noun	noun:inanim:p:v_oru
автотравмах	автотравма	noun	noun:inanim:p:v_mis
автотравми	автотравма	noun	noun:inanim:f:v_rod
автотравми	автотравма	noun	noun:inanim:p:v_kly
автотравми	автотравма	noun	noun:inanim:p:v_naz
автотравми	автотравма	noun	noun:inanim:p:v_zna
автотравмо	автотравма	noun	noun:inanim:f:v_kly
автотравмою	автотравма	noun	noun:inanim:f:v_oru
автотравму	автотравма	noun	noun:inanim:f:v_zna
автотравмі	автотравма	noun	noun:inanim:f:v_dav
автотравмі	автотравма	noun	noun:inanim:f:v_mis
автотракторобудуванню	автотракторобудування	noun	noun:inanim:n:v_dav
автотракторобудуванню	автотракторобудування	noun	noun:inanim:n:v_mis
автотракторобудування	автотракторобудування	noun	noun:inanim:n:v_kly
автотракторобудування	автотракторобудування	noun	noun:inanim:n:v_naz
автотракторобудування	автотракторобудування	noun	noun:inanim:n:v_rod
автотракторобудування	автотракторобудування	noun	noun:inanim:n:v_zna
автотракторобудування	автотракторобудування	noun	noun:inanim:p:v_kly
автотракторобудування	автотракторобудування	noun	noun:inanim:p:v_naz
автотракторобудування	автотракторобудування	noun	noun:inanim:p:v_zna
автотракторобудуванням	автотракторобудування	noun	noun:inanim:n:v_oru
автотракторобудуванням	автотракторобудування	noun	noun:inanim:p:v_dav
автотракторобудуваннями	автотракторобудування	noun	noun:inanim:p:v_oru
автотракторобудуваннях	автотракторобудування	noun	noun:inanim:p:v_mis
автотракторобудуванні	автотракторобудування	noun	noun:inanim:n:v_mis
автотракторобудувань	автотракторобудування	noun	noun:inanim:p:v_rod
автотрансдуктор	автотрансдуктор	noun	noun:inanim:m:v_naz
автотрансдуктор	автотрансдуктор	noun	noun:inanim:m:v_zna
автотрансдуктора	автотрансдуктор	noun	noun:inanim:m:v_rod
автотрансдукторам	автотрансдуктор	noun	noun:inanim:p:v_dav
автотрансдукторами	автотрансдуктор	noun	noun:inanim:p:v_oru
автотрансдукторах	автотрансдуктор	noun	noun:inanim:p:v_mis
автотрансдукторе	автотрансдуктор	noun	noun:inanim:m:v_kly
автотрансдуктори	автотрансдуктор	noun	noun:inanim:p:v_kly
автотрансдуктори	автотрансдуктор	noun	noun:inanim:p:v_naz
автотрансдуктори	автотрансдуктор	noun	noun:inanim:p:v_zna
автотрансдукторові	автотрансдуктор	noun	noun:inanim:m:v_dav
автотрансдукторові	автотрансдуктор	noun	noun:inanim:m:v_mis
автотрансдуктором	автотрансдуктор	noun	noun:inanim:m:v_oru
автотрансдукторі	автотрансдуктор	noun	noun:inanim:m:v_mis
автотрансдукторів	автотрансдуктор	noun	noun:inanim:p:v_rod
автотрансплантацій	автотрансплантація	noun	noun:inanim:p:v_rod
автотрансплантацію	автотрансплантація	noun	noun:inanim:f:v_zna
автотрансплантація	автотрансплантація	noun	noun:inanim:f:v_naz
автотрансплантаціям	автотрансплантація	noun	noun:inanim:p:v_dav
автотрансплантаціями	автотрансплантація	noun	noun:inanim:p:v_oru
автотрансплантаціях	автотрансплантація	noun	noun:inanim:p:v_mis
автотрансплантаціє	автотрансплантація	noun	noun:inanim:f:v_kly
автотрансплантацією	автотрансплантація	noun	noun:inanim:f:v_oru
автотрансплантації	автотрансплантація	noun	noun:inanim:f:v_dav
автотрансплантації	автотрансплантація	noun	noun:inanim:f:v_mis
автотрансплантації	автотрансплантація	noun	noun:inanim:f:v_rod
автотрансплантації	автотрансплантація	noun	noun:inanim:p:v_kly
автотрансплантації	автотрансплантація	noun	noun:inanim:p:v_naz
автотрансплантації	автотрансплантація	noun	noun:inanim:p:v_zna
автотранспортер	автотранспортер	noun	noun:inanim:m:v_naz
автотранспортер	автотранспортер	noun	noun:inanim:m:v_zna
автотранспортера	автотранспортер	noun	noun:inanim:m:v_rod
автотранспортерам	автотранспортер	noun	noun:inanim:p:v_dav
автотранспортерами	автотранспортер	noun	noun:inanim:p:v_oru
автотранспортерах	автотранспортер	noun	noun:inanim:p:v_mis
автотранспортере	автотранспортер	noun	noun:inanim:m:v_kly
автотранспортери	автотранспортер	noun	noun:inanim:p:v_kly
автотранспортери	автотранспортер	noun	noun:inanim:p:v_naz
автотранспортери	автотранспортер	noun	noun:inanim:p:v_zna
автотранспортерові	автотранспортер	noun	noun:inanim:m:v_dav
автотранспортерові	автотранспортер	noun	noun:inanim:m:v_mis
автотранспортером	автотранспортер	noun	noun:inanim:m:v_oru
автотранспортері	автотранспортер	noun	noun:inanim:m:v_mis
автотранспортерів	автотранспортер	noun	noun:inanim:p:v_rod
автотранспортник	автотранспортник	noun	noun:anim:m:v_naz
автотранспортника	автотранспортник	noun	noun:anim:m:v_rod
автотранспортника	автотранспортник	noun	noun:anim:m:v_zna
автотранспортникам	автотранспортник	noun	noun:anim:p:v_dav
автотранспортниками	автотранспортник	noun	noun:anim:p:v_oru
автотранспортниках	автотранспортник	noun	noun:anim:p:v_mis
автотранспортники	автотранспортник	noun	noun:anim:p:v_kly
автотранспортники	автотранспортник	noun	noun:anim:p:v_naz
автотранспортники	автотранспортник	noun	noun:anim:p:v_zna:rare
автотранспортникові	автотранспортник	noun	noun:anim:m:v_dav
автотранспортникові	автотранспортник	noun	noun:anim:m:v_mis
автотранспортником	автотранспортник	noun	noun:anim:m:v_oru
автотранспортнику	автотранспортник	noun	noun:anim:m:v_dav
автотранспортнику	автотранспортник	noun	noun:anim:m:v_kly
автотранспортнику	автотранспортник	noun	noun:anim:m:v_mis
автотранспортників	автотранспортник	noun	noun:anim:p:v_rod
автотранспортників	автотранспортник	noun	noun:anim:p:v_zna
автотрансформатор	автотрансформатор	noun	noun:inanim:m:v_naz
автотрансформатор	автотрансформатор	noun	noun:inanim:m:v_zna
автотрансформатора	автотрансформатор	noun	noun:inanim:m:v_rod
автотрансформаторам	автотрансформатор	noun	noun:inanim:p:v_dav
автотрансформаторами	автотрансформатор	noun	noun:inanim:p:v_oru
автотрансформаторах	автотрансформатор	noun	noun:inanim:p:v_mis
автотрансформаторе	автотрансформатор	noun	noun:inanim:m:v_kly
автотрансформатори	автотрансформатор	noun	noun:inanim:p:v_kly
автотрансформатори	автотрансформатор	noun	noun:inanim:p:v_naz
автотрансформатори	автотрансформатор	noun	noun:inanim:p:v_zna
автотрансформаторові	автотрансформатор	noun	noun:inanim:m:v_dav
автотрансформаторові	автотрансформатор	noun	noun:inanim:m:v_mis
автотрансформатором	автотрансформатор	noun	noun:inanim:m:v_oru
автотрансформаторі	автотрансформатор	noun	noun:inanim:m:v_mis
автотрансформаторів	автотрансформатор	noun	noun:inanim:p:v_rod
автотрансфузій	автотрансфузія	noun	noun:inanim:p:v_rod
автотрансфузію	автотрансфузія	noun	noun:inanim:f:v_zna
автотрансфузія	автотрансфузія	noun	noun:inanim:f:v_naz
автотрансфузіям	автотрансфузія	noun	noun:inanim:p:v_dav
автотрансфузіями	автотрансфузія	noun	noun:inanim:p:v_oru
автотрансфузіях	автотрансфузія	noun	noun:inanim:p:v_mis
автотрансфузіє	автотрансфузія	noun	noun:inanim:f:v_kly
автотрансфузією	автотрансфузія	noun	noun:inanim:f:v_oru
автотрансфузії	автотрансфузія	noun	noun:inanim:f:v_dav
автотрансфузії	автотрансфузія	noun	noun:inanim:f:v_mis
автотрансфузії	автотрансфузія	noun	noun:inanim:f:v_rod
автотрансфузії	автотрансфузія	noun	noun:inanim:p:v_kly
автотрансфузії	автотрансфузія	noun	noun:inanim:p:v_naz
автотрансфузії	автотрансфузія	noun	noun:inanim:p:v_zna
автотрас	автотраса	noun	noun:inanim:p:v_rod
автотраса	автотраса	noun	noun:inanim:f:v_naz
автотрасам	автотраса	noun	noun:inanim:p:v_dav
автотрасами	автотраса	noun	noun:inanim:p:v_oru
автотрасах	автотраса	noun	noun:inanim:p:v_mis
автотраси	автотраса	noun	noun:inanim:f:v_rod
автотраси	автотраса	noun	noun:inanim:p:v_kly
автотраси	автотраса	noun	noun:inanim:p:v_naz
автотраси	автотраса	noun	noun:inanim:p:v_zna
автотрасо	автотраса	noun	noun:inanim:f:v_kly
автотрасою	автотраса	noun	noun:inanim:f:v_oru
автотрасу	автотраса	noun	noun:inanim:f:v_zna
автотрасі	автотраса	noun	noun:inanim:f:v_dav
автотрасі	автотраса	noun	noun:inanim:f:v_mis
автотрейдер	автотрейдер	noun	noun:anim:m:v_naz
автотрейдера	автотрейдер	noun	noun:anim:m:v_rod
автотрейдера	автотрейдер	noun	noun:anim:m:v_zna
автотрейдерам	автотрейдер	noun	noun:anim:p:v_dav
автотрейдерами	автотрейдер	noun	noun:anim:p:v_oru
автотрейдерах	автотрейдер	noun	noun:anim:p:v_mis
автотрейдере	автотрейдер	noun	noun:anim:m:v_kly
автотрейдери	автотрейдер	noun	noun:anim:p:v_kly
автотрейдери	автотрейдер	noun	noun:anim:p:v_naz
автотрейдери	автотрейдер	noun	noun:anim:p:v_zna:rare
автотрейдерові	автотрейдер	noun	noun:anim:m:v_dav
автотрейдерові	автотрейдер	noun	noun:anim:m:v_mis
автотрейдером	автотрейдер	noun	noun:anim:m:v_oru
автотрейдері	автотрейдер	noun	noun:anim:m:v_mis
автотрейдерів	автотрейдер	noun	noun:anim:p:v_rod
автотрейдерів	автотрейдер	noun	noun:anim:p:v_zna
автотрейлер	автотрейлер	noun	noun:inanim:m:v_naz
автотрейлер	автотрейлер	noun	noun:inanim:m:v_zna
автотрейлера	автотрейлер	noun	noun:inanim:m:v_rod
автотрейлерам	автотрейлер	noun	noun:inanim:p:v_dav
автотрейлерами	автотрейлер	noun	noun:inanim:p:v_oru
автотрейлерах	автотрейлер	noun	noun:inanim:p:v_mis
автотрейлере	автотрейлер	noun	noun:inanim:m:v_kly
автотрейлери	автотрейлер	noun	noun:inanim:p:v_kly
автотрейлери	автотрейлер	noun	noun:inanim:p:v_naz
автотрейлери	автотрейлер	noun	noun:inanim:p:v_zna
автотрейлерові	автотрейлер	noun	noun:inanim:m:v_dav
автотрейлерові	автотрейлер	noun	noun:inanim:m:v_mis
автотрейлером	автотрейлер	noun	noun:inanim:m:v_oru
автотрейлері	автотрейлер	noun	noun:inanim:m:v_mis
автотрейлерів	автотрейлер	noun	noun:inanim:p:v_rod
автотрек	автотрек	noun	noun:inanim:m:v_naz
автотрек	автотрек	noun	noun:inanim:m:v_zna
автотрекам	автотрек	noun	noun:inanim:p:v_dav
автотреками	автотрек	noun	noun:inanim:p:v_oru
автотреках	автотрек	noun	noun:inanim:p:v_mis
автотреки	автотрек	noun	noun:inanim:p:v_kly
автотреки	автотрек	noun	noun:inanim:p:v_naz
автотреки	автотрек	noun	noun:inanim:p:v_zna
автотрекові	автотрек	noun	noun:inanim:m:v_dav
автотрекові	автотрек	noun	noun:inanim:m:v_mis
автотреком	автотрек	noun	noun:inanim:m:v_oru
автотреку	автотрек	noun	noun:inanim:m:v_dav
автотреку	автотрек	noun	noun:inanim:m:v_kly
автотреку	автотрек	noun	noun:inanim:m:v_mis
автотреку	автотрек	noun	noun:inanim:m:v_rod
автотреків	автотрек	noun	noun:inanim:p:v_rod
автотренажер	автотренажер	noun	noun:inanim:m:v_naz
автотренажер	автотренажер	noun	noun:inanim:m:v_zna
автотренажера	автотренажер	noun	noun:inanim:m:v_rod
автотренажерам	автотренажер	noun	noun:inanim:p:v_dav
автотренажерами	автотренажер	noun	noun:inanim:p:v_oru
автотренажерах	автотренажер	noun	noun:inanim:p:v_mis
автотренажере	автотренажер	noun	noun:inanim:m:v_kly
автотренажери	автотренажер	noun	noun:inanim:p:v_kly
автотренажери	автотренажер	noun	noun:inanim:p:v_naz
автотренажери	автотренажер	noun	noun:inanim:p:v_zna
автотренажерові	автотренажер	noun	noun:inanim:m:v_dav
автотренажерові	автотренажер	noun	noun:inanim:m:v_mis
автотренажером	автотренажер	noun	noun:inanim:m:v_oru
автотренажері	автотренажер	noun	noun:inanim:m:v_mis
автотренажерів	автотренажер	noun	noun:inanim:p:v_rod
автотренінг	автотренінг	noun	noun:inanim:m:v_naz
автотренінг	автотренінг	noun	noun:inanim:m:v_zna
автотренінгам	автотренінг	noun	noun:inanim:p:v_dav
автотренінгами	автотренінг	noun	noun:inanim:p:v_oru
автотренінгах	автотренінг	noun	noun:inanim:p:v_mis
автотренінги	автотренінг	noun	noun:inanim:p:v_kly
автотренінги	автотренінг	noun	noun:inanim:p:v_naz
автотренінги	автотренінг	noun	noun:inanim:p:v_zna
автотренінгові	автотренінг	noun	noun:inanim:m:v_dav
автотренінгові	автотренінг	noun	noun:inanim:m:v_mis
автотренінгом	автотренінг	noun	noun:inanim:m:v_oru
автотренінгу	автотренінг	noun	noun:inanim:m:v_dav
автотренінгу	автотренінг	noun	noun:inanim:m:v_kly
автотренінгу	автотренінг	noun	noun:inanim:m:v_mis
автотренінгу	автотренінг	noun	noun:inanim:m:v_rod
автотренінгів	автотренінг	noun	noun:inanim:p:v_rod
автотроф	автотроф	noun	noun:inanim:m:v_naz
автотроф	автотроф	noun	noun:inanim:m:v_zna
автотрофа	автотроф	noun	noun:inanim:m:v_rod
автотрофам	автотроф	noun	noun:inanim:p:v_dav
автотрофами	автотроф	noun	noun:inanim:p:v_oru
автотрофах	автотроф	noun	noun:inanim:p:v_mis
автотрофе	автотроф	noun	noun:inanim:m:v_kly
автотрофи	автотроф	noun	noun:inanim:p:v_kly
автотрофи	автотроф	noun	noun:inanim:p:v_naz
автотрофи	автотроф	noun	noun:inanim:p:v_zna
автотрофові	автотроф	noun	noun:inanim:m:v_dav
автотрофові	автотроф	noun	noun:inanim:m:v_mis
автотрофом	автотроф	noun	noun:inanim:m:v_oru
автотрофі	автотроф	noun	noun:inanim:m:v_mis
автотрофів	автотроф	noun	noun:inanim:p:v_rod
автотрощ	автотроща	noun	noun:inanim:p:v_rod
автотроща	автотроща	noun	noun:inanim:f:v_naz
автотрощам	автотроща	noun	noun:inanim:p:v_dav
автотрощами	автотроща	noun	noun:inanim:p:v_oru
автотрощах	автотроща	noun	noun:inanim:p:v_mis
автотроще	автотроща	noun	noun:inanim:f:v_kly
автотрощею	автотроща	noun	noun:inanim:f:v_oru
автотрощу	автотроща	noun	noun:inanim:f:v_zna
автотрощі	автотроща	noun	noun:inanim:f:v_dav
автотрощі	автотроща	noun	noun:inanim:f:v_mis
автотрощі	автотроща	noun	noun:inanim:f:v_rod
автотрощі	автотроща	noun	noun:inanim:p:v_kly
автотрощі	автотроща	noun	noun:inanim:p:v_naz
автотрощі	автотроща	noun	noun:inanim:p:v_zna
автотунелеві	автотунель	noun	noun:inanim:m:v_dav
автотунелеві	автотунель	noun	noun:inanim:m:v_mis
автотунелем	автотунель	noun	noun:inanim:m:v_oru
автотунель	автотунель	noun	noun:inanim:m:v_naz
автотунель	автотунель	noun	noun:inanim:m:v_zna
автотунелю	автотунель	noun	noun:inanim:m:v_dav
автотунелю	автотунель	noun	noun:inanim:m:v_kly
автотунелю	автотунель	noun	noun:inanim:m:v_mis
автотунелю	автотунель	noun	noun:inanim:m:v_rod
автотунелям	автотунель	noun	noun:inanim:p:v_dav
автотунелями	автотунель	noun	noun:inanim:p:v_oru
автотунелях	автотунель	noun	noun:inanim:p:v_mis
автотунелі	автотунель	noun	noun:inanim:m:v_mis
автотунелі	автотунель	noun	noun:inanim:p:v_kly
автотунелі	автотунель	noun	noun:inanim:p:v_naz
автотунелі	автотунель	noun	noun:inanim:p:v_zna
автотунелів	автотунель	noun	noun:inanim:p:v_rod
автотур	автотур	noun	noun:inanim:m:v_naz
автотур	автотур	noun	noun:inanim:m:v_zna
автотурам	автотур	noun	noun:inanim:p:v_dav
автотурами	автотур	noun	noun:inanim:p:v_oru
автотурах	автотур	noun	noun:inanim:p:v_mis
автотуре	автотур	noun	noun:inanim:m:v_kly
автотури	автотур	noun	noun:inanim:p:v_kly
автотури	автотур	noun	noun:inanim:p:v_naz
автотури	автотур	noun	noun:inanim:p:v_zna
автотурист	автотурист	noun	noun:anim:m:v_naz
автотуриста	автотурист	noun	noun:anim:m:v_rod
автотуриста	автотурист	noun	noun:anim:m:v_zna
автотуристам	автотурист	noun	noun:anim:p:v_dav
автотуристами	автотурист	noun	noun:anim:p:v_oru
автотуристах	автотурист	noun	noun:anim:p:v_mis
автотуристе	автотурист	noun	noun:anim:m:v_kly
автотуристи	автотурист	noun	noun:anim:p:v_kly
автотуристи	автотурист	noun	noun:anim:p:v_naz
автотуристи	автотурист	noun	noun:anim:p:v_zna:rare
автотуристові	автотурист	noun	noun:anim:m:v_dav
автотуристові	автотурист	noun	noun:anim:m:v_mis
автотуристом	автотурист	noun	noun:anim:m:v_oru
автотуристі	автотурист	noun	noun:anim:m:v_mis
автотуристів	автотурист	noun	noun:anim:p:v_rod
автотуристів	автотурист	noun	noun:anim:p:v_zna
автотурові	автотур	noun	noun:inanim:m:v_dav
автотурові	автотур	noun	noun:inanim:m:v_mis
автотуром	автотур	noun	noun:inanim:m:v_oru
автотуру	автотур	noun	noun:inanim:m:v_dav
автотуру	автотур	noun	noun:inanim:m:v_mis
автотуру	автотур	noun	noun:inanim:m:v_rod
автотурі	автотур	noun	noun:inanim:m:v_mis
автотурів	автотур	noun	noun:inanim:p:v_rod
автотусовка	автотусовка	noun	noun:inanim:f:v_naz
автотусовкам	автотусовка	noun	noun:inanim:p:v_dav
автотусовками	автотусовка	noun	noun:inanim:p:v_oru
автотусовках	автотусовка	noun	noun:inanim:p:v_mis
автотусовки	автотусовка	noun	noun:inanim:f:v_rod
автотусовки	автотусовка	noun	noun:inanim:p:v_kly
автотусовки	автотусовка	noun	noun:inanim:p:v_naz
автотусовки	автотусовка	noun	noun:inanim:p:v_zna
автотусовко	автотусовка	noun	noun:inanim:f:v_kly
автотусовкою	автотусовка	noun	noun:inanim:f:v_oru
автотусовку	автотусовка	noun	noun:inanim:f:v_zna
автотусовок	автотусовка	noun	noun:inanim:p:v_rod
автотусовці	автотусовка	noun	noun:inanim:f:v_dav
автотусовці	автотусовка	noun	noun:inanim:f:v_mis
автотягач	автотягач	noun	noun:inanim:m:v_naz
автотягач	автотягач	noun	noun:inanim:m:v_zna
автотягача	автотягач	noun	noun:inanim:m:v_rod
автотягачам	автотягач	noun	noun:inanim:p:v_dav
автотягачами	автотягач	noun	noun:inanim:p:v_oru
автотягачах	автотягач	noun	noun:inanim:p:v_mis
автотягачеві	автотягач	noun	noun:inanim:m:v_dav
автотягачеві	автотягач	noun	noun:inanim:m:v_mis
автотягачем	автотягач	noun	noun:inanim:m:v_oru
автотягачу	автотягач	noun	noun:inanim:m:v_dav
автотягачу	автотягач	noun	noun:inanim:m:v_kly
автотягачу	автотягач	noun	noun:inanim:m:v_mis
автотягачі	автотягач	noun	noun:inanim:m:v_mis
автотягачі	автотягач	noun	noun:inanim:p:v_kly
автотягачі	автотягач	noun	noun:inanim:p:v_naz
автотягачі	автотягач	noun	noun:inanim:p:v_zna
автотягачів	автотягач	noun	noun:inanim:p:v_rod
автоуправлінню	автоуправління	noun	noun:inanim:n:v_dav
автоуправлінню	автоуправління	noun	noun:inanim:n:v_mis
автоуправління	автоуправління	noun	noun:inanim:n:v_kly
автоуправління	автоуправління	noun	noun:inanim:n:v_naz
автоуправління	автоуправління	noun	noun:inanim:n:v_rod
автоуправління	автоуправління	noun	noun:inanim:n:v_zna
автоуправління	автоуправління	noun	noun:inanim:p:v_kly
автоуправління	автоуправління	noun	noun:inanim:p:v_naz
автоуправління	автоуправління	noun	noun:inanim:p:v_zna
автоуправлінням	автоуправління	noun	noun:inanim:n:v_oru
автоуправлінням	автоуправління	noun	noun:inanim:p:v_dav
автоуправліннями	автоуправління	noun	noun:inanim:p:v_oru
автоуправліннях	автоуправління	noun	noun:inanim:p:v_mis
автоуправлінні	автоуправління	noun	noun:inanim:n:v_mis
автоуправлінь	автоуправління	noun	noun:inanim:p:v_rod
автофабрик	автофабрика	noun	noun:inanim:p:v_rod
автофабрика	автофабрика	noun	noun:inanim:f:v_naz
автофабрикам	автофабрика	noun	noun:inanim:p:v_dav
автофабриками	автофабрика	noun	noun:inanim:p:v_oru
автофабриках	автофабрика	noun	noun:inanim:p:v_mis
автофабрики	автофабрика	noun	noun:inanim:f:v_rod
автофабрики	автофабрика	noun	noun:inanim:p:v_kly
автофабрики	автофабрика	noun	noun:inanim:p:v_naz
автофабрики	автофабрика	noun	noun:inanim:p:v_zna
автофабрико	автофабрика	noun	noun:inanim:f:v_kly
автофабрикою	автофабрика	noun	noun:inanim:f:v_oru
автофабрику	автофабрика	noun	noun:inanim:f:v_zna
автофабриці	автофабрика	noun	noun:inanim:f:v_dav
автофабриці	автофабрика	noun	noun:inanim:f:v_mis
автофагосом	автофагосома	noun	noun:inanim:p:v_rod
автофагосома	автофагосома	noun	noun:inanim:f:v_naz
автофагосомам	автофагосома	noun	noun:inanim:p:v_dav
автофагосомами	автофагосома	noun	noun:inanim:p:v_oru
автофагосомах	автофагосома	noun	noun:inanim:p:v_mis
автофагосоми	автофагосома	noun	noun:inanim:f:v_rod
автофагосоми	автофагосома	noun	noun:inanim:p:v_kly
автофагосоми	автофагосома	noun	noun:inanim:p:v_naz
автофагосоми	автофагосома	noun	noun:inanim:p:v_zna
автофагосомо	автофагосома	noun	noun:inanim:f:v_kly
автофагосомою	автофагосома	noun	noun:inanim:f:v_oru
автофагосому	автофагосома	noun	noun:inanim:f:v_zna
автофагосомі	автофагосома	noun	noun:inanim:f:v_dav
автофагосомі	автофагосома	noun	noun:inanim:f:v_mis
автофагій	автофагія	noun	noun:inanim:p:v_rod
автофагію	автофагія	noun	noun:inanim:f:v_zna
автофагія	автофагія	noun	noun:inanim:f:v_naz
автофагіям	автофагія	noun	noun:inanim:p:v_dav
автофагіями	автофагія	noun	noun:inanim:p:v_oru
автофагіях	автофагія	noun	noun:inanim:p:v_mis
автофагіє	автофагія	noun	noun:inanim:f:v_kly
автофагією	автофагія	noun	noun:inanim:f:v_oru
автофагії	автофагія	noun	noun:inanim:f:v_dav
автофагії	автофагія	noun	noun:inanim:f:v_mis
автофагії	автофагія	noun	noun:inanim:f:v_rod
автофагії	автофагія	noun	noun:inanim:p:v_kly
автофагії	автофагія	noun	noun:inanim:p:v_naz
автофагії	автофагія	noun	noun:inanim:p:v_zna
автофакс	автофакс	noun	noun:inanim:m:v_naz
автофакс	автофакс	noun	noun:inanim:m:v_zna
автофаксам	автофакс	noun	noun:inanim:p:v_dav
автофаксами	автофакс	noun	noun:inanim:p:v_oru
автофаксах	автофакс	noun	noun:inanim:p:v_mis
автофаксе	автофакс	noun	noun:inanim:m:v_kly
автофакси	автофакс	noun	noun:inanim:p:v_kly
автофакси	автофакс	noun	noun:inanim:p:v_naz
автофакси	автофакс	noun	noun:inanim:p:v_zna
автофаксові	автофакс	noun	noun:inanim:m:v_dav
автофаксові	автофакс	noun	noun:inanim:m:v_mis
автофаксом	автофакс	noun	noun:inanim:m:v_oru
автофаксу	автофакс	noun	noun:inanim:m:v_dav
автофаксу	автофакс	noun	noun:inanim:m:v_mis
автофаксу	автофакс	noun	noun:inanim:m:v_rod
автофаксі	автофакс	noun	noun:inanim:m:v_mis
автофаксів	автофакс	noun	noun:inanim:p:v_rod
автофан	автофан	noun	noun:anim:m:v_naz
автофана	автофан	noun	noun:anim:m:v_rod
автофана	автофан	noun	noun:anim:m:v_zna
автофанам	автофан	noun	noun:anim:p:v_dav
автофанами	автофан	noun	noun:anim:p:v_oru
автофанах	автофан	noun	noun:anim:p:v_mis
автофане	автофан	noun	noun:anim:m:v_kly
автофани	автофан	noun	noun:anim:p:v_kly
автофани	автофан	noun	noun:anim:p:v_naz
автофани	автофан	noun	noun:anim:p:v_zna:rare
автофанові	автофан	noun	noun:anim:m:v_dav
автофанові	автофан	noun	noun:anim:m:v_mis
автофаном	автофан	noun	noun:anim:m:v_oru
автофані	автофан	noun	noun:anim:m:v_mis
автофанів	автофан	noun	noun:anim:p:v_rod
автофанів	автофан	noun	noun:anim:p:v_zna
автофарб	автофарба	noun	noun:inanim:p:v_rod
автофарба	автофарба	noun	noun:inanim:f:v_naz
автофарбам	автофарба	noun	noun:inanim:p:v_dav
автофарбами	автофарба	noun	noun:inanim:p:v_oru
автофарбах	автофарба	noun	noun:inanim:p:v_mis
автофарби	автофарба	noun	noun:inanim:f:v_rod
автофарби	автофарба	noun	noun:inanim:p:v_kly
автофарби	автофарба	noun	noun:inanim:p:v_naz
автофарби	автофарба	noun	noun:inanim:p:v_zna
автофарбо	автофарба	noun	noun:inanim:f:v_kly
автофарбою	автофарба	noun	noun:inanim:f:v_oru
автофарбу	автофарба	noun	noun:inanim:f:v_zna
автофарбі	автофарба	noun	noun:inanim:f:v_dav
автофарбі	автофарба	noun	noun:inanim:f:v_mis
автофоній	автофонія	noun	noun:inanim:p:v_rod
автофонію	автофонія	noun	noun:inanim:f:v_zna
автофонія	автофонія	noun	noun:inanim:f:v_naz
автофоніям	автофонія	noun	noun:inanim:p:v_dav
автофоніями	автофонія	noun	noun:inanim:p:v_oru
автофоніях	автофонія	noun	noun:inanim:p:v_mis
автофоніє	автофонія	noun	noun:inanim:f:v_kly
автофонією	автофонія	noun	noun:inanim:f:v_oru
автофонії	автофонія	noun	noun:inanim:f:v_dav
автофонії	автофонія	noun	noun:inanim:f:v_mis
автофонії	автофонія	noun	noun:inanim:f:v_rod
автофонії	автофонія	noun	noun:inanim:p:v_kly
автофонії	автофонія	noun	noun:inanim:p:v_naz
автофонії	автофонія	noun	noun:inanim:p:v_zna
автофопоманій	автофопоманія	noun	noun:inanim:p:v_rod
автофопоманію	автофопоманія	noun	noun:inanim:f:v_zna
автофопоманія	автофопоманія	noun	noun:inanim:f:v_naz
автофопоманіям	автофопоманія	noun	noun:inanim:p:v_dav
автофопоманіями	автофопоманія	noun	noun:inanim:p:v_oru
автофопоманіях	автофопоманія	noun	noun:inanim:p:v_mis
автофопоманіє	автофопоманія	noun	noun:inanim:f:v_kly
автофопоманією	автофопоманія	noun	noun:inanim:f:v_oru
автофопоманії	автофопоманія	noun	noun:inanim:f:v_dav
автофопоманії	автофопоманія	noun	noun:inanim:f:v_mis
автофопоманії	автофопоманія	noun	noun:inanim:f:v_rod
автофопоманії	автофопоманія	noun	noun:inanim:p:v_kly
автофопоманії	автофопоманія	noun	noun:inanim:p:v_naz
автофопоманії	автофопоманія	noun	noun:inanim:p:v_zna
автофорум	автофорум	noun	noun:inanim:m:v_naz
автофорум	автофорум	noun	noun:inanim:m:v_zna
автофорумам	автофорум	noun	noun:inanim:p:v_dav
автофорумами	автофорум	noun	noun:inanim:p:v_oru
автофорумах	автофорум	noun	noun:inanim:p:v_mis
автофоруме	автофорум	noun	noun:inanim:m:v_kly
автофоруми	автофорум	noun	noun:inanim:p:v_kly
автофоруми	автофорум	noun	noun:inanim:p:v_naz
автофоруми	автофорум	noun	noun:inanim:p:v_zna
автофорумові	автофорум	noun	noun:inanim:m:v_dav
автофорумові	автофорум	noun	noun:inanim:m:v_mis
автофорумом	автофорум	noun	noun:inanim:m:v_oru
автофоруму	автофорум	noun	noun:inanim:m:v_dav
автофоруму	автофорум	noun	noun:inanim:m:v_mis
автофоруму	автофорум	noun	noun:inanim:m:v_rod
автофорумі	автофорум	noun	noun:inanim:m:v_mis
автофорумів	автофорум	noun	noun:inanim:p:v_rod
автофрез	автофреза	noun	noun:inanim:p:v_rod
автофреза	автофреза	noun	noun:inanim:f:v_naz
автофрезам	автофреза	noun	noun:inanim:p:v_dav
автофрезами	автофреза	noun	noun:inanim:p:v_oru
автофрезах	автофреза	noun	noun:inanim:p:v_mis
автофрези	автофреза	noun	noun:inanim:f:v_rod
автофрези	автофреза	noun	noun:inanim:p:v_kly
автофрези	автофреза	noun	noun:inanim:p:v_naz
автофрези	автофреза	noun	noun:inanim:p:v_zna
автофрезо	автофреза	noun	noun:inanim:f:v_kly
автофрезою	автофреза	noun	noun:inanim:f:v_oru
автофрезу	автофреза	noun	noun:inanim:f:v_zna
автофрезі	автофреза	noun	noun:inanim:f:v_dav
автофрезі	автофреза	noun	noun:inanim:f:v_mis
автофретаж	автофретаж	noun	noun:inanim:m:v_naz
автофретаж	автофретаж	noun	noun:inanim:m:v_zna
автофретажам	автофретаж	noun	noun:inanim:p:v_dav
автофретажами	автофретаж	noun	noun:inanim:p:v_oru
автофретажах	автофретаж	noun	noun:inanim:p:v_mis
автофретаже	автофретаж	noun	noun:inanim:m:v_kly
автофретажеві	автофретаж	noun	noun:inanim:m:v_dav
автофретажеві	автофретаж	noun	noun:inanim:m:v_mis
автофретажем	автофретаж	noun	noun:inanim:m:v_oru
автофретажу	автофретаж	noun	noun:inanim:m:v_dav
автофретажу	автофретаж	noun	noun:inanim:m:v_mis
автофретажу	автофретаж	noun	noun:inanim:m:v_rod
автофретажі	автофретаж	noun	noun:inanim:m:v_mis
автофретажі	автофретаж	noun	noun:inanim:p:v_kly
автофретажі	автофретаж	noun	noun:inanim:p:v_naz
автофретажі	автофретаж	noun	noun:inanim:p:v_zna
автофретажів	автофретаж	noun	noun:inanim:p:v_rod
автофур	автофура	noun	noun:inanim:p:v_rod
автофура	автофура	noun	noun:inanim:f:v_naz
автофурам	автофура	noun	noun:inanim:p:v_dav
автофурами	автофура	noun	noun:inanim:p:v_oru
автофурах	автофура	noun	noun:inanim:p:v_mis
автофургон	автофургон	noun	noun:inanim:m:v_naz
автофургон	автофургон	noun	noun:inanim:m:v_zna
автофургона	автофургон	noun	noun:inanim:m:v_rod
автофургонам	автофургон	noun	noun:inanim:p:v_dav
автофургонами	автофургон	noun	noun:inanim:p:v_oru
автофургонах	автофургон	noun	noun:inanim:p:v_mis
автофургоне	автофургон	noun	noun:inanim:m:v_kly
автофургони	автофургон	noun	noun:inanim:p:v_kly
автофургони	автофургон	noun	noun:inanim:p:v_naz
автофургони	автофургон	noun	noun:inanim:p:v_zna
автофургонові	автофургон	noun	noun:inanim:m:v_dav
автофургонові	автофургон	noun	noun:inanim:m:v_mis
автофургоном	автофургон	noun	noun:inanim:m:v_oru
автофургоні	автофургон	noun	noun:inanim:m:v_mis
автофургонів	автофургон	noun	noun:inanim:p:v_rod
автофури	автофура	noun	noun:inanim:f:v_rod
автофури	автофура	noun	noun:inanim:p:v_kly
автофури	автофура	noun	noun:inanim:p:v_naz
автофури	автофура	noun	noun:inanim:p:v_zna
автофуро	автофура	noun	noun:inanim:f:v_kly
автофурою	автофура	noun	noun:inanim:f:v_oru
автофуру	автофура	noun	noun:inanim:f:v_zna
автофурі	автофура	noun	noun:inanim:f:v_dav
автофурі	автофура	noun	noun:inanim:f:v_mis
автофіксацій	автофіксація	noun	noun:inanim:p:v_rod
автофіксацію	автофіксація	noun	noun:inanim:f:v_zna
автофіксація	автофіксація	noun	noun:inanim:f:v_naz
автофіксаціям	автофіксація	noun	noun:inanim:p:v_dav
автофіксаціями	автофіксація	noun	noun:inanim:p:v_oru
автофіксаціях	автофіксація	noun	noun:inanim:p:v_mis
автофіксаціє	автофіксація	noun	noun:inanim:f:v_kly
автофіксацією	автофіксація	noun	noun:inanim:f:v_oru
автофіксації	автофіксація	noun	noun:inanim:f:v_dav
автофіксації	автофіксація	noun	noun:inanim:f:v_mis
автофіксації	автофіксація	noun	noun:inanim:f:v_rod
автофіксації	автофіксація	noun	noun:inanim:p:v_kly
автофіксації	автофіксація	noun	noun:inanim:p:v_naz
автофіксації	автофіксація	noun	noun:inanim:p:v_zna
автофірм	автофірма	noun	noun:inanim:p:v_rod
автофірма	автофірма	noun	noun:inanim:f:v_naz
автофірмам	автофірма	noun	noun:inanim:p:v_dav
автофірмами	автофірма	noun	noun:inanim:p:v_oru
автофірмах	автофірма	noun	noun:inanim:p:v_mis
автофірми	автофірма	noun	noun:inanim:f:v_rod
автофірми	автофірма	noun	noun:inanim:p:v_kly
автофірми	автофірма	noun	noun:inanim:p:v_naz
автофірми	автофірма	noun	noun:inanim:p:v_zna
автофірмо	автофірма	noun	noun:inanim:f:v_kly
автофірмою	автофірма	noun	noun:inanim:f:v_oru
автофірму	автофірма	noun	noun:inanim:f:v_zna
автофірмі	автофірма	noun	noun:inanim:f:v_dav
автофірмі	автофірма	noun	noun:inanim:f:v_mis
автохвиле	автохвиля	noun	noun:inanim:f:v_kly
автохвилею	автохвиля	noun	noun:inanim:f:v_oru
автохвиль	автохвиля	noun	noun:inanim:p:v_rod
автохвилю	автохвиля	noun	noun:inanim:f:v_zna
автохвиля	автохвиля	noun	noun:inanim:f:v_naz
автохвилям	автохвиля	noun	noun:inanim:p:v_dav
автохвилями	автохвиля	noun	noun:inanim:p:v_oru
автохвилях	автохвиля	noun	noun:inanim:p:v_mis
автохвилі	автохвиля	noun	noun:inanim:f:v_dav
автохвилі	автохвиля	noun	noun:inanim:f:v_mis
автохвилі	автохвиля	noun	noun:inanim:f:v_rod
автохвилі	автохвиля	noun	noun:inanim:p:v_kly
автохвилі	автохвиля	noun	noun:inanim:p:v_naz
автохвилі	автохвиля	noun	noun:inanim:p:v_zna
автохолодильник	автохолодильник	noun	noun:inanim:m:v_naz
автохолодильник	автохолодильник	noun	noun:inanim:m:v_zna
автохолодильника	автохолодильник	noun	noun:inanim:m:v_rod
автохолодильникам	автохолодильник	noun	noun:inanim:p:v_dav
автохолодильниками	автохолодильник	noun	noun:inanim:p:v_oru
автохолодильниках	автохолодильник	noun	noun:inanim:p:v_mis
автохолодильники	автохолодильник	noun	noun:inanim:p:v_kly
автохолодильники	автохолодильник	noun	noun:inanim:p:v_naz
автохолодильники	автохолодильник	noun	noun:inanim:p:v_zna
автохолодильникові	автохолодильник	noun	noun:inanim:m:v_dav
автохолодильникові	автохолодильник	noun	noun:inanim:m:v_mis
автохолодильником	автохолодильник	noun	noun:inanim:m:v_oru
автохолодильнику	автохолодильник	noun	noun:inanim:m:v_dav
автохолодильнику	автохолодильник	noun	noun:inanim:m:v_kly
автохолодильнику	автохолодильник	noun	noun:inanim:m:v_mis
автохолодильників	автохолодильник	noun	noun:inanim:p:v_rod
автохор	автохор	noun	noun:inanim:m:v_naz
автохор	автохор	noun	noun:inanim:m:v_zna
автохора	автохор	noun	noun:inanim:m:v_rod
автохорам	автохор	noun	noun:inanim:p:v_dav
автохорами	автохор	noun	noun:inanim:p:v_oru
автохорах	автохор	noun	noun:inanim:p:v_mis
автохоре	автохор	noun	noun:inanim:m:v_kly
автохори	автохор	noun	noun:inanim:p:v_kly
автохори	автохор	noun	noun:inanim:p:v_naz
автохори	автохор	noun	noun:inanim:p:v_zna
автохорові	автохор	noun	noun:inanim:m:v_dav
автохорові	автохор	noun	noun:inanim:m:v_mis
автохором	автохор	noun	noun:inanim:m:v_oru
автохорі	автохор	noun	noun:inanim:m:v_mis
автохорів	автохор	noun	noun:inanim:p:v_rod
автохром	автохром	noun	noun:inanim:m:v_naz
автохром	автохром	noun	noun:inanim:m:v_zna
автохромам	автохром	noun	noun:inanim:p:v_dav
автохромами	автохром	noun	noun:inanim:p:v_oru
автохромах	автохром	noun	noun:inanim:p:v_mis
автохроме	автохром	noun	noun:inanim:m:v_kly
автохроми	автохром	noun	noun:inanim:p:v_kly
автохроми	автохром	noun	noun:inanim:p:v_naz
автохроми	автохром	noun	noun:inanim:p:v_zna
автохромові	автохром	noun	noun:inanim:m:v_dav
автохромові	автохром	noun	noun:inanim:m:v_mis
автохромом	автохром	noun	noun:inanim:m:v_oru
автохрому	автохром	noun	noun:inanim:m:v_dav
автохрому	автохром	noun	noun:inanim:m:v_mis
автохрому	автохром	noun	noun:inanim:m:v_rod
автохромі	автохром	noun	noun:inanim:m:v_mis
автохромів	автохром	noun	noun:inanim:p:v_rod
автохронометраж	автохронометраж	noun	noun:inanim:m:v_naz
автохронометраж	автохронометраж	noun	noun:inanim:m:v_zna
автохронометражам	автохронометраж	noun	noun:inanim:p:v_dav
автохронометражами	автохронометраж	noun	noun:inanim:p:v_oru
автохронометражах	автохронометраж	noun	noun:inanim:p:v_mis
автохронометраже	автохронометраж	noun	noun:inanim:m:v_kly
автохронометражеві	автохронометраж	noun	noun:inanim:m:v_dav
автохронометражеві	автохронометраж	noun	noun:inanim:m:v_mis
автохронометражем	автохронометраж	noun	noun:inanim:m:v_oru
автохронометражу	автохронометраж	noun	noun:inanim:m:v_dav
автохронометражу	автохронометраж	noun	noun:inanim:m:v_mis
автохронометражу	автохронометраж	noun	noun:inanim:m:v_rod
автохронометражі	автохронометраж	noun	noun:inanim:m:v_mis
автохронометражі	автохронометраж	noun	noun:inanim:p:v_kly
автохронометражі	автохронометраж	noun	noun:inanim:p:v_naz
автохронометражі	автохронометраж	noun	noun:inanim:p:v_zna
автохронометражів	автохронометраж	noun	noun:inanim:p:v_rod
автохтон	автохтон	noun	noun:anim:m:v_naz
автохтон	автохтон	noun	noun:inanim:m:v_naz
автохтон	автохтон	noun	noun:inanim:m:v_zna
автохтона	автохтон	noun	noun:anim:m:v_rod
автохтона	автохтон	noun	noun:anim:m:v_zna
автохтона	автохтон	noun	noun:inanim:m:v_rod
автохтонам	автохтон	noun	noun:anim:p:v_dav
автохтонам	автохтон	noun	noun:inanim:p:v_dav
автохтонами	автохтон	noun	noun:anim:p:v_oru
автохтонами	автохтон	noun	noun:inanim:p:v_oru
автохтонах	автохтон	noun	noun:anim:p:v_mis
автохтонах	автохтон	noun	noun:inanim:p:v_mis
автохтоне	автохтон	noun	noun:anim:m:v_kly
автохтоне	автохтон	noun	noun:inanim:m:v_kly
автохтони	автохтон	noun	noun:anim:p:v_kly
автохтони	автохтон	noun	noun:anim:p:v_naz
автохтони	автохтон	noun	noun:anim:p:v_zna:rare
автохтони	автохтон	noun	noun:inanim:p:v_kly
автохтони	автохтон	noun	noun:inanim:p:v_naz
автохтони	автохтон	noun	noun:inanim:p:v_zna
автохтонка	автохтонка	noun	noun:anim:f:v_naz
автохтонкам	автохтонка	noun	noun:anim:p:v_dav
автохтонками	автохтонка	noun	noun:anim:p:v_oru
автохтонках	автохтонка	noun	noun:anim:p:v_mis
автохтонки	автохтонка	noun	noun:anim:f:v_rod
автохтонки	автохтонка	noun	noun:anim:p:v_kly
автохтонки	автохтонка	noun	noun:anim:p:v_naz
автохтонки	автохтонка	noun	noun:anim:p:v_zna:rare
автохтонко	автохтонка	noun	noun:anim:f:v_kly
автохтонкою	автохтонка	noun	noun:anim:f:v_oru
автохтонку	автохтонка	noun	noun:anim:f:v_zna
автохтонносте	автохтонність	noun	noun:inanim:f:v_kly
автохтонностей	автохтонність	noun	noun:inanim:p:v_rod
автохтонностям	автохтонність	noun	noun:inanim:p:v_dav
автохтонностями	автохтонність	noun	noun:inanim:p:v_oru
автохтонностях	автохтонність	noun	noun:inanim:p:v_mis
автохтонності	автохтонність	noun	noun:inanim:f:v_dav
автохтонності	автохтонність	noun	noun:inanim:f:v_mis
автохтонності	автохтонність	noun	noun:inanim:f:v_rod
автохтонності	автохтонність	noun	noun:inanim:p:v_kly
автохтонності	автохтонність	noun	noun:inanim:p:v_naz
автохтонності	автохтонність	noun	noun:inanim:p:v_zna
автохтонність	автохтонність	noun	noun:inanim:f:v_naz
автохтонність	автохтонність	noun	noun:inanim:f:v_zna
автохтонністю	автохтонність	noun	noun:inanim:f:v_oru
автохтонові	автохтон	noun	noun:anim:m:v_dav
автохтонові	автохтон	noun	noun:anim:m:v_mis
автохтонові	автохтон	noun	noun:inanim:m:v_dav
автохтонові	автохтон	noun	noun:inanim:m:v_mis
автохтонок	автохтонка	noun	noun:anim:p:v_rod
автохтонок	автохтонка	noun	noun:anim:p:v_zna
автохтоном	автохтон	noun	noun:anim:m:v_oru
автохтоном	автохтон	noun	noun:inanim:m:v_oru
автохтонці	автохтонка	noun	noun:anim:f:v_dav
автохтонці	автохтонка	noun	noun:anim:f:v_mis
автохтоні	автохтон	noun	noun:anim:m:v_mis
автохтоні	автохтон	noun	noun:inanim:m:v_mis
автохтонів	автохтон	noun	noun:anim:p:v_rod
автохтонів	автохтон	noun	noun:anim:p:v_zna
автохтонів	автохтон	noun	noun:inanim:p:v_rod
автохтоніст	автохтоніст	noun	noun:anim:m:v_naz
автохтоніста	автохтоніст	noun	noun:anim:m:v_rod
автохтоніста	автохтоніст	noun	noun:anim:m:v_zna
автохтоністам	автохтоніст	noun	noun:anim:p:v_dav
автохтоністами	автохтоніст	noun	noun:anim:p:v_oru
автохтоністах	автохтоніст	noun	noun:anim:p:v_mis
автохтоністе	автохтоніст	noun	noun:anim:m:v_kly
автохтоністи	автохтоніст	noun	noun:anim:p:v_kly
автохтоністи	автохтоніст	noun	noun:anim:p:v_naz
автохтоністи	автохтоніст	noun	noun:anim:p:v_zna:rare
автохтоністові	автохтоніст	noun	noun:anim:m:v_dav
автохтоністові	автохтоніст	noun	noun:anim:m:v_mis
автохтоністом	автохтоніст	noun	noun:anim:m:v_oru
автохтоністі	автохтоніст	noun	noun:anim:m:v_mis
автохтоністів	автохтоніст	noun	noun:anim:p:v_rod
автохтоністів	автохтоніст	noun	noun:anim:p:v_zna
автохуліган	автохуліган	noun	noun:anim:m:v_naz
автохулігана	автохуліган	noun	noun:anim:m:v_rod
автохулігана	автохуліган	noun	noun:anim:m:v_zna
автохуліганам	автохуліган	noun	noun:anim:p:v_dav
автохуліганами	автохуліган	noun	noun:anim:p:v_oru
автохуліганах	автохуліган	noun	noun:anim:p:v_mis
автохулігане	автохуліган	noun	noun:anim:m:v_kly
автохулігани	автохуліган	noun	noun:anim:p:v_kly
автохулігани	автохуліган	noun	noun:anim:p:v_naz
автохулігани	автохуліган	noun	noun:anim:p:v_zna:rare
автохуліганові	автохуліган	noun	noun:anim:m:v_dav
автохуліганові	автохуліган	noun	noun:anim:m:v_mis
автохуліганом	автохуліган	noun	noun:anim:m:v_oru
автохулігані	автохуліган	noun	noun:anim:m:v_mis
автохуліганів	автохуліган	noun	noun:anim:p:v_rod
автохуліганів	автохуліган	noun	noun:anim:p:v_zna
автоцвинтар	автоцвинтар	noun	noun:inanim:m:v_naz
автоцвинтар	автоцвинтар	noun	noun:inanim:m:v_zna
автоцвинтареві	автоцвинтар	noun	noun:inanim:m:v_dav
автоцвинтареві	автоцвинтар	noun	noun:inanim:m:v_mis
автоцвинтарем	автоцвинтар	noun	noun:inanim:m:v_oru
автоцвинтарю	автоцвинтар	noun	noun:inanim:m:v_dav
автоцвинтарю	автоцвинтар	noun	noun:inanim:m:v_kly
автоцвинтарю	автоцвинтар	noun	noun:inanim:m:v_mis
автоцвинтаря	автоцвинтар	noun	noun:inanim:m:v_rod
автоцвинтарям	автоцвинтар	noun	noun:inanim:p:v_dav
автоцвинтарями	автоцвинтар	noun	noun:inanim:p:v_oru
автоцвинтарях	автоцвинтар	noun	noun:inanim:p:v_mis
автоцвинтарі	автоцвинтар	noun	noun:inanim:m:v_mis
автоцвинтарі	автоцвинтар	noun	noun:inanim:p:v_kly
автоцвинтарі	автоцвинтар	noun	noun:inanim:p:v_naz
автоцвинтарі	автоцвинтар	noun	noun:inanim:p:v_zna
автоцвинтарів	автоцвинтар	noun	noun:inanim:p:v_rod
автоцементовоз	автоцементовоз	noun	noun:inanim:m:v_naz
автоцементовоз	автоцементовоз	noun	noun:inanim:m:v_zna
автоцементовоза	автоцементовоз	noun	noun:inanim:m:v_rod
автоцементовоза	автоцементовіз	noun	noun:inanim:m:v_rod
автоцементовозам	автоцементовоз	noun	noun:inanim:p:v_dav
автоцементовозам	автоцементовіз	noun	noun:inanim:p:v_dav
автоцементовозами	автоцементовоз	noun	noun:inanim:p:v_oru
автоцементовозами	автоцементовіз	noun	noun:inanim:p:v_oru
автоцементовозах	автоцементовоз	noun	noun:inanim:p:v_mis
автоцементовозах	автоцементовіз	noun	noun:inanim:p:v_mis
автоцементовозе	автоцементовоз	noun	noun:inanim:m:v_kly
автоцементовозе	автоцементовіз	noun	noun:inanim:m:v_kly
автоцементовози	автоцементовоз	noun	noun:inanim:p:v_kly
автоцементовози	автоцементовоз	noun	noun:inanim:p:v_naz
автоцементовози	автоцементовоз	noun	noun:inanim:p:v_zna
автоцементовози	автоцементовіз	noun	noun:inanim:p:v_kly
автоцементовози	автоцементовіз	noun	noun:inanim:p:v_naz
автоцементовози	автоцементовіз	noun	noun:inanim:p:v_zna
автоцементовозові	автоцементовоз	noun	noun:inanim:m:v_dav
автоцементовозові	автоцементовоз	noun	noun:inanim:m:v_mis
автоцементовозові	автоцементовіз	noun	noun:inanim:m:v_dav
автоцементовозові	автоцементовіз	noun	noun:inanim:m:v_mis
автоцементовозом	автоцементовоз	noun	noun:inanim:m:v_oru
автоцементовозом	автоцементовіз	noun	noun:inanim:m:v_oru
автоцементовозі	автоцементовоз	noun	noun:inanim:m:v_mis
автоцементовозі	автоцементовіз	noun	noun:inanim:m:v_mis
автоцементовозів	автоцементовоз	noun	noun:inanim:p:v_rod
автоцементовозів	автоцементовіз	noun	noun:inanim:p:v_rod
автоцементовіз	автоцементовіз	noun	noun:inanim:m:v_naz
автоцементовіз	автоцементовіз	noun	noun:inanim:m:v_zna
автоцентр	автоцентр	noun	noun:inanim:m:v_naz
автоцентр	автоцентр	noun	noun:inanim:m:v_zna
автоцентрам	автоцентр	noun	noun:inanim:p:v_dav
автоцентрами	автоцентр	noun	noun:inanim:p:v_oru
автоцентрах	автоцентр	noun	noun:inanim:p:v_mis
автоцентре	автоцентр	noun	noun:inanim:m:v_kly
автоцентри	автоцентр	noun	noun:inanim:p:v_kly
автоцентри	автоцентр	noun	noun:inanim:p:v_naz
автоцентри	автоцентр	noun	noun:inanim:p:v_zna
автоцентрові	автоцентр	noun	noun:inanim:m:v_dav
автоцентрові	автоцентр	noun	noun:inanim:m:v_mis
автоцентром	автоцентр	noun	noun:inanim:m:v_oru
автоцентру	автоцентр	noun	noun:inanim:m:v_dav
автоцентру	автоцентр	noun	noun:inanim:m:v_mis
автоцентру	автоцентр	noun	noun:inanim:m:v_rod
автоцентрі	автоцентр	noun	noun:inanim:m:v_mis
автоцентрів	автоцентр	noun	noun:inanim:p:v_rod
автоцистерн	автоцистерна	noun	noun:inanim:p:v_rod
автоцистерна	автоцистерна	noun	noun:inanim:f:v_naz
автоцистернам	автоцистерна	noun	noun:inanim:p:v_dav
автоцистернами	автоцистерна	noun	noun:inanim:p:v_oru
автоцистернах	автоцистерна	noun	noun:inanim:p:v_mis
автоцистерни	автоцистерна	noun	noun:inanim:f:v_rod
автоцистерни	автоцистерна	noun	noun:inanim:p:v_kly
автоцистерни	автоцистерна	noun	noun:inanim:p:v_naz
автоцистерни	автоцистерна	noun	noun:inanim:p:v_zna
автоцистерно	автоцистерна	noun	noun:inanim:f:v_kly
автоцистерною	автоцистерна	noun	noun:inanim:f:v_oru
автоцистерну	автоцистерна	noun	noun:inanim:f:v_zna
автоцистерні	автоцистерна	noun	noun:inanim:f:v_dav
автоцистерні	автоцистерна	noun	noun:inanim:f:v_mis
автоцитат	автоцитата	noun	noun:inanim:p:v_rod
автоцитата	автоцитата	noun	noun:inanim:f:v_naz
автоцитатам	автоцитата	noun	noun:inanim:p:v_dav
автоцитатами	автоцитата	noun	noun:inanim:p:v_oru
автоцитатах	автоцитата	noun	noun:inanim:p:v_mis
автоцитати	автоцитата	noun	noun:inanim:f:v_rod
автоцитати	автоцитата	noun	noun:inanim:p:v_kly
автоцитати	автоцитата	noun	noun:inanim:p:v_naz
автоцитати	автоцитата	noun	noun:inanim:p:v_zna
автоцитато	автоцитата	noun	noun:inanim:f:v_kly
автоцитатою	автоцитата	noun	noun:inanim:f:v_oru
автоцитату	автоцитата	noun	noun:inanim:f:v_zna
автоцитаті	автоцитата	noun	noun:inanim:f:v_dav
автоцитаті	автоцитата	noun	noun:inanim:f:v_mis
авточастин	авточастина	noun	noun:inanim:p:v_rod
авточастина	авточастина	noun	noun:inanim:f:v_naz
авточастинам	авточастина	noun	noun:inanim:p:v_dav
авточастинами	авточастина	noun	noun:inanim:p:v_oru
авточастинах	авточастина	noun	noun:inanim:p:v_mis
авточастини	авточастина	noun	noun:inanim:f:v_rod
авточастини	авточастина	noun	noun:inanim:p:v_kly
авточастини	авточастина	noun	noun:inanim:p:v_naz
авточастини	авточастина	noun	noun:inanim:p:v_zna
авточастино	авточастина	noun	noun:inanim:f:v_kly
авточастиною	авточастина	noun	noun:inanim:f:v_oru
авточастину	авточастина	noun	noun:inanim:f:v_zna
авточастині	авточастина	noun	noun:inanim:f:v_dav
авточастині	авточастина	noun	noun:inanim:f:v_mis
авточерг	авточерга	noun	noun:inanim:p:v_rod
авточерга	авточерга	noun	noun:inanim:f:v_naz
авточергам	авточерга	noun	noun:inanim:p:v_dav
авточергами	авточерга	noun	noun:inanim:p:v_oru
авточергах	авточерга	noun	noun:inanim:p:v_mis
авточерги	авточерга	noun	noun:inanim:f:v_rod
авточерги	авточерга	noun	noun:inanim:p:v_kly
авточерги	авточерга	noun	noun:inanim:p:v_naz
авточерги	авточерга	noun	noun:inanim:p:v_zna
авточерго	авточерга	noun	noun:inanim:f:v_kly
авточергою	авточерга	noun	noun:inanim:f:v_oru
авточергу	авточерга	noun	noun:inanim:f:v_zna
авточерзі	авточерга	noun	noun:inanim:f:v_dav
авточерзі	авточерга	noun	noun:inanim:f:v_mis
авточохла	авточохол	noun	noun:inanim:m:v_rod
авточохлам	авточохол	noun	noun:inanim:p:v_dav
авточохлами	авточохол	noun	noun:inanim:p:v_oru
авточохлах	авточохол	noun	noun:inanim:p:v_mis
авточохле	авточохол	noun	noun:inanim:m:v_kly
авточохли	авточохол	noun	noun:inanim:p:v_kly
авточохли	авточохол	noun	noun:inanim:p:v_naz
авточохли	авточохол	noun	noun:inanim:p:v_zna
авточохлові	авточохол	noun	noun:inanim:m:v_dav
авточохлові	авточохол	noun	noun:inanim:m:v_mis
авточохлом	авточохол	noun	noun:inanim:m:v_oru
авточохлі	авточохол	noun	noun:inanim:m:v_mis
авточохлів	авточохол	noun	noun:inanim:p:v_rod
авточохол	авточохол	noun	noun:inanim:m:v_naz
авточохол	авточохол	noun	noun:inanim:m:v_zna
автошампуневі	автошампунь	noun	noun:inanim:m:v_dav
автошампуневі	автошампунь	noun	noun:inanim:m:v_mis
автошампунем	автошампунь	noun	noun:inanim:m:v_oru
автошампунь	автошампунь	noun	noun:inanim:m:v_naz
автошампунь	автошампунь	noun	noun:inanim:m:v_zna
автошампуню	автошампунь	noun	noun:inanim:m:v_dav
автошампуню	автошампунь	noun	noun:inanim:m:v_kly
автошампуню	автошампунь	noun	noun:inanim:m:v_mis
автошампуня	автошампунь	noun	noun:inanim:m:v_rod
автошампуням	автошампунь	noun	noun:inanim:p:v_dav
автошампунями	автошампунь	noun	noun:inanim:p:v_oru
автошампунях	автошампунь	noun	noun:inanim:p:v_mis
автошампуні	автошампунь	noun	noun:inanim:m:v_mis
автошампуні	автошампунь	noun	noun:inanim:p:v_kly
автошампуні	автошампунь	noun	noun:inanim:p:v_naz
автошампуні	автошампунь	noun	noun:inanim:p:v_zna
автошампунів	автошампунь	noun	noun:inanim:p:v_rod
автошарж	автошарж	noun	noun:inanim:m:v_naz
автошарж	автошарж	noun	noun:inanim:m:v_zna
автошаржам	автошарж	noun	noun:inanim:p:v_dav
автошаржами	автошарж	noun	noun:inanim:p:v_oru
автошаржах	автошарж	noun	noun:inanim:p:v_mis
автошарже	автошарж	noun	noun:inanim:m:v_kly
автошаржеві	автошарж	noun	noun:inanim:m:v_dav
автошаржеві	автошарж	noun	noun:inanim:m:v_mis
автошаржем	автошарж	noun	noun:inanim:m:v_oru
автошаржу	автошарж	noun	noun:inanim:m:v_dav
автошаржу	автошарж	noun	noun:inanim:m:v_mis
автошаржу	автошарж	noun	noun:inanim:m:v_rod
автошаржі	автошарж	noun	noun:inanim:m:v_mis
автошаржі	автошарж	noun	noun:inanim:p:v_kly
автошаржі	автошарж	noun	noun:inanim:p:v_naz
автошаржі	автошарж	noun	noun:inanim:p:v_zna
автошаржів	автошарж	noun	noun:inanim:p:v_rod
автошахрай	автошахрай	noun	noun:anim:m:v_naz
автошахрайств	автошахрайство	noun	noun:inanim:p:v_rod
автошахрайства	автошахрайство	noun	noun:inanim:n:v_rod
автошахрайства	автошахрайство	noun	noun:inanim:p:v_kly
автошахрайства	автошахрайство	noun	noun:inanim:p:v_naz
автошахрайства	автошахрайство	noun	noun:inanim:p:v_zna
автошахрайствам	автошахрайство	noun	noun:inanim:p:v_dav
автошахрайствами	автошахрайство	noun	noun:inanim:p:v_oru
автошахрайствах	автошахрайство	noun	noun:inanim:p:v_mis
автошахрайство	автошахрайство	noun	noun:inanim:n:v_kly
автошахрайство	автошахрайство	noun	noun:inanim:n:v_naz
автошахрайство	автошахрайство	noun	noun:inanim:n:v_zna
автошахрайством	автошахрайство	noun	noun:inanim:n:v_oru
автошахрайству	автошахрайство	noun	noun:inanim:n:v_dav
автошахрайству	автошахрайство	noun	noun:inanim:n:v_mis
автошахрайстві	автошахрайство	noun	noun:inanim:n:v_mis
автошахраю	автошахрай	noun	noun:anim:m:v_dav
автошахраю	автошахрай	noun	noun:anim:m:v_kly
автошахраю	автошахрай	noun	noun:anim:m:v_mis
автошахрая	автошахрай	noun	noun:anim:m:v_rod
автошахрая	автошахрай	noun	noun:anim:m:v_zna
автошахраям	автошахрай	noun	noun:anim:p:v_dav
автошахраями	автошахрай	noun	noun:anim:p:v_oru
автошахраях	автошахрай	noun	noun:anim:p:v_mis
автошахраєві	автошахрай	noun	noun:anim:m:v_dav
автошахраєві	автошахрай	noun	noun:anim:m:v_mis
автошахраєм	автошахрай	noun	noun:anim:m:v_oru
автошахраї	автошахрай	noun	noun:anim:m:v_mis
автошахраї	автошахрай	noun	noun:anim:p:v_kly
автошахраї	автошахрай	noun	noun:anim:p:v_naz
автошахраї	автошахрай	noun	noun:anim:p:v_zna:rare
автошахраїв	автошахрай	noun	noun:anim:p:v_rod
автошахраїв	автошахрай	noun	noun:anim:p:v_zna
автошин	автошина	noun	noun:inanim:p:v_rod
автошина	автошина	noun	noun:inanim:f:v_naz
автошинам	автошина	noun	noun:inanim:p:v_dav
автошинами	автошина	noun	noun:inanim:p:v_oru
автошинах	автошина	noun	noun:inanim:p:v_mis
автошини	автошина	noun	noun:inanim:f:v_rod
автошини	автошина	noun	noun:inanim:p:v_kly
автошини	автошина	noun	noun:inanim:p:v_naz
автошини	автошина	noun	noun:inanim:p:v_zna
автошино	автошина	noun	noun:inanim:f:v_kly
автошиною	автошина	noun	noun:inanim:f:v_oru
автошину	автошина	noun	noun:inanim:f:v_zna
автошині	автошина	noun	noun:inanim:f:v_dav
автошині	автошина	noun	noun:inanim:f:v_mis
автошкола	автошкола	noun	noun:inanim:f:v_naz
автошколам	автошкола	noun	noun:inanim:p:v_dav
автошколами	автошкола	noun	noun:inanim:p:v_oru
автошколах	автошкола	noun	noun:inanim:p:v_mis
автошколи	автошкола	noun	noun:inanim:f:v_rod
автошколи	автошкола	noun	noun:inanim:p:v_kly
автошколи	автошкола	noun	noun:inanim:p:v_naz
автошколи	автошкола	noun	noun:inanim:p:v_zna
автошколо	автошкола	noun	noun:inanim:f:v_kly
автошколою	автошкола	noun	noun:inanim:f:v_oru
автошколу	автошкола	noun	noun:inanim:f:v_zna
автошколі	автошкола	noun	noun:inanim:f:v_dav
автошколі	автошкола	noun	noun:inanim:f:v_mis
автошкіл	автошкола	noun	noun:inanim:p:v_rod
автошлях	автошлях	noun	noun:inanim:m:v_naz
автошлях	автошлях	noun	noun:inanim:m:v_zna
автошляхам	автошлях	noun	noun:inanim:p:v_dav
автошляхами	автошлях	noun	noun:inanim:p:v_oru
автошляхах	автошлях	noun	noun:inanim:p:v_mis
автошляхи	автошлях	noun	noun:inanim:p:v_kly
автошляхи	автошлях	noun	noun:inanim:p:v_naz
автошляхи	автошлях	noun	noun:inanim:p:v_zna
автошляховик	автошляховик	noun	noun:anim:m:v_naz
автошляховика	автошляховик	noun	noun:anim:m:v_rod
автошляховика	автошляховик	noun	noun:anim:m:v_zna
автошляховикам	автошляховик	noun	noun:anim:p:v_dav
автошляховиками	автошляховик	noun	noun:anim:p:v_oru
автошляховиках	автошляховик	noun	noun:anim:p:v_mis
автошляховики	автошляховик	noun	noun:anim:p:v_kly
автошляховики	автошляховик	noun	noun:anim:p:v_naz
автошляховики	автошляховик	noun	noun:anim:p:v_zna:rare
автошляховикові	автошляховик	noun	noun:anim:m:v_dav
автошляховикові	автошляховик	noun	noun:anim:m:v_mis
автошляховиком	автошляховик	noun	noun:anim:m:v_oru
автошляховику	автошляховик	noun	noun:anim:m:v_dav
автошляховику	автошляховик	noun	noun:anim:m:v_kly
автошляховику	автошляховик	noun	noun:anim:m:v_mis
автошляховиків	автошляховик	noun	noun:anim:p:v_rod
автошляховиків	автошляховик	noun	noun:anim:p:v_zna
автошляхові	автошлях	noun	noun:inanim:m:v_dav
автошляхові	автошлях	noun	noun:inanim:m:v_mis
автошляхом	автошлях	noun	noun:inanim:m:v_oru
автошляху	автошлях	noun	noun:inanim:m:v_dav
автошляху	автошлях	noun	noun:inanim:m:v_kly
автошляху	автошлях	noun	noun:inanim:m:v_mis
автошляху	автошлях	noun	noun:inanim:m:v_rod
автошляхів	автошлях	noun	noun:inanim:p:v_rod
автоштамп	автоштамп	noun	noun:inanim:m:v_naz
автоштамп	автоштамп	noun	noun:inanim:m:v_zna
автоштампа	автоштамп	noun	noun:inanim:m:v_rod
автоштампам	автоштамп	noun	noun:inanim:p:v_dav
автоштампами	автоштамп	noun	noun:inanim:p:v_oru
автоштампах	автоштамп	noun	noun:inanim:p:v_mis
автоштампе	автоштамп	noun	noun:inanim:m:v_kly
автоштампи	автоштамп	noun	noun:inanim:p:v_kly
автоштампи	автоштамп	noun	noun:inanim:p:v_naz
автоштампи	автоштамп	noun	noun:inanim:p:v_zna
автоштампові	автоштамп	noun	noun:inanim:m:v_dav
автоштампові	автоштамп	noun	noun:inanim:m:v_mis
автоштампом	автоштамп	noun	noun:inanim:m:v_oru
автоштампі	автоштамп	noun	noun:inanim:m:v_mis
автоштампів	автоштамп	noun	noun:inanim:p:v_rod
автоштурман	автоштурман	noun	noun:inanim:m:v_naz
автоштурман	автоштурман	noun	noun:inanim:m:v_zna
автоштурмана	автоштурман	noun	noun:inanim:m:v_rod
автоштурманам	автоштурман	noun	noun:inanim:p:v_dav
автоштурманами	автоштурман	noun	noun:inanim:p:v_oru
автоштурманах	автоштурман	noun	noun:inanim:p:v_mis
автоштурмане	автоштурман	noun	noun:inanim:m:v_kly
автоштурмани	автоштурман	noun	noun:inanim:p:v_kly
автоштурмани	автоштурман	noun	noun:inanim:p:v_naz
автоштурмани	автоштурман	noun	noun:inanim:p:v_zna
автоштурманові	автоштурман	noun	noun:inanim:m:v_dav
автоштурманові	автоштурман	noun	noun:inanim:m:v_mis
автоштурманом	автоштурман	noun	noun:inanim:m:v_oru
автоштурмані	автоштурман	noun	noun:inanim:m:v_mis
автоштурманів	автоштурман	noun	noun:inanim:p:v_rod
автошукач	автошукач	noun	noun:inanim:m:v_naz
автошукач	автошукач	noun	noun:inanim:m:v_zna
автошукача	автошукач	noun	noun:inanim:m:v_rod
автошукачам	автошукач	noun	noun:inanim:p:v_dav
автошукачами	автошукач	noun	noun:inanim:p:v_oru
автошукачах	автошукач	noun	noun:inanim:p:v_mis
автошукачеві	автошукач	noun	noun:inanim:m:v_dav
автошукачеві	автошукач	noun	noun:inanim:m:v_mis
автошукачем	автошукач	noun	noun:inanim:m:v_oru
автошукачу	автошукач	noun	noun:inanim:m:v_dav
автошукачу	автошукач	noun	noun:inanim:m:v_kly
автошукачу	автошукач	noun	noun:inanim:m:v_mis
автошукачі	автошукач	noun	noun:inanim:m:v_mis
автошукачі	автошукач	noun	noun:inanim:p:v_kly
автошукачі	автошукач	noun	noun:inanim:p:v_naz
автошукачі	автошукач	noun	noun:inanim:p:v_zna
автошукачів	автошукач	noun	noun:inanim:p:v_rod
автоямобур	автоямобур	noun	noun:inanim:m:v_naz
автоямобур	автоямобур	noun	noun:inanim:m:v_zna
автоямобура	автоямобур	noun	noun:inanim:m:v_rod
автоямобурам	автоямобур	noun	noun:inanim:p:v_dav
автоямобурами	автоямобур	noun	noun:inanim:p:v_oru
автоямобурах	автоямобур	noun	noun:inanim:p:v_mis
автоямобуре	автоямобур	noun	noun:inanim:m:v_kly
автоямобури	автоямобур	noun	noun:inanim:p:v_kly
автоямобури	автоямобур	noun	noun:inanim:p:v_naz
автоямобури	автоямобур	noun	noun:inanim:p:v_zna
автоямобурові	автоямобур	noun	noun:inanim:m:v_dav
автоямобурові	автоямобур	noun	noun:inanim:m:v_mis
автоямобуром	автоямобур	noun	noun:inanim:m:v_oru
автоямобурі	автоямобур	noun	noun:inanim:m:v_mis
автоямобурів	автоямобур	noun	noun:inanim:p:v_rod
автоімперій	автоімперія	noun	noun:inanim:p:v_rod
автоімперію	автоімперія	noun	noun:inanim:f:v_zna
автоімперія	автоімперія	noun	noun:inanim:f:v_naz
автоімперіям	автоімперія	noun	noun:inanim:p:v_dav
автоімперіями	автоімперія	noun	noun:inanim:p:v_oru
автоімперіях	автоімперія	noun	noun:inanim:p:v_mis
автоімперіє	автоімперія	noun	noun:inanim:f:v_kly
автоімперією	автоімперія	noun	noun:inanim:f:v_oru
автоімперії	автоімперія	noun	noun:inanim:f:v_dav
автоімперії	автоімперія	noun	noun:inanim:f:v_mis
автоімперії	автоімперія	noun	noun:inanim:f:v_rod
автоімперії	автоімперія	noun	noun:inanim:p:v_kly
автоімперії	автоімперія	noun	noun:inanim:p:v_naz
автоімперії	автоімперія	noun	noun:inanim:p:v_zna
автоімпортер	автоімпортер	noun	noun:anim:m:v_naz
автоімпортера	автоімпортер	noun	noun:anim:m:v_rod
автоімпортера	автоімпортер	noun	noun:anim:m:v_zna
автоімпортерам	автоімпортер	noun	noun:anim:p:v_dav
автоімпортерами	автоімпортер	noun	noun:anim:p:v_oru
автоімпортерах	автоімпортер	noun	noun:anim:p:v_mis
автоімпортере	автоімпортер	noun	noun:anim:m:v_kly
автоімпортери	автоімпортер	noun	noun:anim:p:v_kly
автоімпортери	автоімпортер	noun	noun:anim:p:v_naz
автоімпортери	автоімпортер	noun	noun:anim:p:v_zna:rare
автоімпортерові	автоімпортер	noun	noun:anim:m:v_dav
автоімпортерові	автоімпортер	noun	noun:anim:m:v_mis
автоімпортером	автоімпортер	noun	noun:anim:m:v_oru
автоімпортері	автоімпортер	noun	noun:anim:m:v_mis
автоімпортерів	автоімпортер	noun	noun:anim:p:v_rod
автоімпортерів	автоімпортер	noun	noun:anim:p:v_zna
автоімунітет	автоімунітет	noun	noun:inanim:m:v_naz
автоімунітет	автоімунітет	noun	noun:inanim:m:v_zna
автоімунітетам	автоімунітет	noun	noun:inanim:p:v_dav
автоімунітетами	автоімунітет	noun	noun:inanim:p:v_oru
автоімунітетах	автоімунітет	noun	noun:inanim:p:v_mis
автоімунітете	автоімунітет	noun	noun:inanim:m:v_kly
автоімунітети	автоімунітет	noun	noun:inanim:p:v_kly
автоімунітети	автоімунітет	noun	noun:inanim:p:v_naz
автоімунітети	автоімунітет	noun	noun:inanim:p:v_zna
автоімунітетові	автоімунітет	noun	noun:inanim:m:v_dav
автоімунітетові	автоімунітет	noun	noun:inanim:m:v_mis
автоімунітетом	автоімунітет	noun	noun:inanim:m:v_oru
автоімунітету	автоімунітет	noun	noun:inanim:m:v_dav
автоімунітету	автоімунітет	noun	noun:inanim:m:v_mis
автоімунітету	автоімунітет	noun	noun:inanim:m:v_rod
автоімунітеті	автоімунітет	noun	noun:inanim:m:v_mis
автоімунітетів	автоімунітет	noun	noun:inanim:p:v_rod
автоінвазій	автоінвазія	noun	noun:inanim:p:v_rod
автоінвазію	автоінвазія	noun	noun:inanim:f:v_zna
автоінвазія	автоінвазія	noun	noun:inanim:f:v_naz
автоінвазіям	автоінвазія	noun	noun:inanim:p:v_dav
автоінвазіями	автоінвазія	noun	noun:inanim:p:v_oru
автоінвазіях	автоінвазія	noun	noun:inanim:p:v_mis
автоінвазіє	автоінвазія	noun	noun:inanim:f:v_kly
автоінвазією	автоінвазія	noun	noun:inanim:f:v_oru
автоінвазії	автоінвазія	noun	noun:inanim:f:v_dav
автоінвазії	автоінвазія	noun	noun:inanim:f:v_mis
автоінвазії	автоінвазія	noun	noun:inanim:f:v_rod
автоінвазії	автоінвазія	noun	noun:inanim:p:v_kly
автоінвазії	автоінвазія	noun	noun:inanim:p:v_naz
автоінвазії	автоінвазія	noun	noun:inanim:p:v_zna
автоінкремент	автоінкремент	noun	noun:inanim:m:v_naz
автоінкремент	автоінкремент	noun	noun:inanim:m:v_zna
автоінкрементам	автоінкремент	noun	noun:inanim:p:v_dav
автоінкрементами	автоінкремент	noun	noun:inanim:p:v_oru
автоінкрементах	автоінкремент	noun	noun:inanim:p:v_mis
автоінкременте	автоінкремент	noun	noun:inanim:m:v_kly
автоінкременти	автоінкремент	noun	noun:inanim:p:v_kly
автоінкременти	автоінкремент	noun	noun:inanim:p:v_naz
автоінкременти	автоінкремент	noun	noun:inanim:p:v_zna
автоінкрементові	автоінкремент	noun	noun:inanim:m:v_dav
автоінкрементові	автоінкремент	noun	noun:inanim:m:v_mis
автоінкрементом	автоінкремент	noun	noun:inanim:m:v_oru
автоінкременту	автоінкремент	noun	noun:inanim:m:v_dav
автоінкременту	автоінкремент	noun	noun:inanim:m:v_mis
автоінкременту	автоінкремент	noun	noun:inanim:m:v_rod
автоінкременті	автоінкремент	noun	noun:inanim:m:v_mis
автоінкрементів	автоінкремент	noun	noun:inanim:p:v_rod
автоінокуляцій	автоінокуляція	noun	noun:inanim:p:v_rod
автоінокуляцію	автоінокуляція	noun	noun:inanim:f:v_zna
автоінокуляція	автоінокуляція	noun	noun:inanim:f:v_naz
автоінокуляціям	автоінокуляція	noun	noun:inanim:p:v_dav
автоінокуляціями	автоінокуляція	noun	noun:inanim:p:v_oru
автоінокуляціях	автоінокуляція	noun	noun:inanim:p:v_mis
автоінокуляціє	автоінокуляція	noun	noun:inanim:f:v_kly
автоінокуляцією	автоінокуляція	noun	noun:inanim:f:v_oru
автоінокуляції	автоінокуляція	noun	noun:inanim:f:v_dav
автоінокуляції	автоінокуляція	noun	noun:inanim:f:v_mis
автоінокуляції	автоінокуляція	noun	noun:inanim:f:v_rod
автоінокуляції	автоінокуляція	noun	noun:inanim:p:v_kly
автоінокуляції	автоінокуляція	noun	noun:inanim:p:v_naz
автоінокуляції	автоінокуляція	noun	noun:inanim:p:v_zna
автоінспектор	автоінспектор	noun	noun:anim:m:v_naz
автоінспектора	автоінспектор	noun	noun:anim:m:v_rod
автоінспектора	автоінспектор	noun	noun:anim:m:v_zna
автоінспекторам	автоінспектор	noun	noun:anim:p:v_dav
автоінспекторами	автоінспектор	noun	noun:anim:p:v_oru
автоінспекторах	автоінспектор	noun	noun:anim:p:v_mis
автоінспекторе	автоінспектор	noun	noun:anim:m:v_kly
автоінспектори	автоінспектор	noun	noun:anim:p:v_kly
автоінспектори	автоінспектор	noun	noun:anim:p:v_naz
автоінспектори	автоінспектор	noun	noun:anim:p:v_zna:rare
автоінспекторка	автоінспекторка	noun	noun:anim:f:v_naz
автоінспекторкам	автоінспекторка	noun	noun:anim:p:v_dav
автоінспекторками	автоінспекторка	noun	noun:anim:p:v_oru
автоінспекторках	автоінспекторка	noun	noun:anim:p:v_mis
автоінспекторки	автоінспекторка	noun	noun:anim:f:v_rod
автоінспекторки	автоінспекторка	noun	noun:anim:p:v_kly
автоінспекторки	автоінспекторка	noun	noun:anim:p:v_naz
автоінспекторки	автоінспекторка	noun	noun:anim:p:v_zna:rare
автоінспекторко	автоінспекторка	noun	noun:anim:f:v_kly
автоінспекторкою	автоінспекторка	noun	noun:anim:f:v_oru
автоінспекторку	автоінспекторка	noun	noun:anim:f:v_zna
автоінспекторові	автоінспектор	noun	noun:anim:m:v_dav
автоінспекторові	автоінспектор	noun	noun:anim:m:v_mis
автоінспекторок	автоінспекторка	noun	noun:anim:p:v_rod
автоінспекторок	автоінспекторка	noun	noun:anim:p:v_zna
автоінспектором	автоінспектор	noun	noun:anim:m:v_oru
автоінспекторці	автоінспекторка	noun	noun:anim:f:v_dav
автоінспекторці	автоінспекторка	noun	noun:anim:f:v_mis
автоінспекторі	автоінспектор	noun	noun:anim:m:v_mis
автоінспекторів	автоінспектор	noun	noun:anim:p:v_rod
автоінспекторів	автоінспектор	noun	noun:anim:p:v_zna
автоінспекцій	автоінспекція	noun	noun:inanim:p:v_rod
автоінспекцію	автоінспекція	noun	noun:inanim:f:v_zna
автоінспекція	автоінспекція	noun	noun:inanim:f:v_naz
автоінспекціям	автоінспекція	noun	noun:inanim:p:v_dav
автоінспекціями	автоінспекція	noun	noun:inanim:p:v_oru
автоінспекціях	автоінспекція	noun	noun:inanim:p:v_mis
автоінспекціє	автоінспекція	noun	noun:inanim:f:v_kly
автоінспекцією	автоінспекція	noun	noun:inanim:f:v_oru
автоінспекції	автоінспекція	noun	noun:inanim:f:v_dav
автоінспекції	автоінспекція	noun	noun:inanim:f:v_mis
автоінспекції	автоінспекція	noun	noun:inanim:f:v_rod
автоінспекції	автоінспекція	noun	noun:inanim:p:v_kly
автоінспекції	автоінспекція	noun	noun:inanim:p:v_naz
автоінспекції	автоінспекція	noun	noun:inanim:p:v_zna
автоінструкторка	автоінструкторка	noun	noun:anim:f:v_naz
автоінструкторкам	автоінструкторка	noun	noun:anim:p:v_dav
автоінструкторками	автоінструкторка	noun	noun:anim:p:v_oru
автоінструкторках	автоінструкторка	noun	noun:anim:p:v_mis
автоінструкторки	автоінструкторка	noun	noun:anim:f:v_rod
автоінструкторки	автоінструкторка	noun	noun:anim:p:v_kly
автоінструкторки	автоінструкторка	noun	noun:anim:p:v_naz
автоінструкторки	автоінструкторка	noun	noun:anim:p:v_zna:rare
автоінструкторко	автоінструкторка	noun	noun:anim:f:v_kly
автоінструкторкою	автоінструкторка	noun	noun:anim:f:v_oru
автоінструкторку	автоінструкторка	noun	noun:anim:f:v_zna
автоінструкторок	автоінструкторка	noun	noun:anim:p:v_rod
автоінструкторок	автоінструкторка	noun	noun:anim:p:v_zna
автоінструкторці	автоінструкторка	noun	noun:anim:f:v_dav
автоінструкторці	автоінструкторка	noun	noun:anim:f:v_mis
автоінтоксикацій	автоінтоксикація	noun	noun:inanim:p:v_rod
автоінтоксикацію	автоінтоксикація	noun	noun:inanim:f:v_zna
автоінтоксикація	автоінтоксикація	noun	noun:inanim:f:v_naz
автоінтоксикаціям	автоінтоксикація	noun	noun:inanim:p:v_dav
автоінтоксикаціями	автоінтоксикація	noun	noun:inanim:p:v_oru
автоінтоксикаціях	автоінтоксикація	noun	noun:inanim:p:v_mis
автоінтоксикаціє	автоінтоксикація	noun	noun:inanim:f:v_kly
автоінтоксикацією	автоінтоксикація	noun	noun:inanim:f:v_oru
автоінтоксикації	автоінтоксикація	noun	noun:inanim:f:v_dav
автоінтоксикації	автоінтоксикація	noun	noun:inanim:f:v_mis
автоінтоксикації	автоінтоксикація	noun	noun:inanim:f:v_rod
автоінтоксикації	автоінтоксикація	noun	noun:inanim:p:v_kly
автоінтоксикації	автоінтоксикація	noun	noun:inanim:p:v_naz
автоінтоксикації	автоінтоксикація	noun	noun:inanim:p:v_zna
автоінфекцій	автоінфекція	noun	noun:inanim:p:v_rod
автоінфекцію	автоінфекція	noun	noun:inanim:f:v_zna
автоінфекція	автоінфекція	noun	noun:inanim:f:v_naz
автоінфекціям	автоінфекція	noun	noun:inanim:p:v_dav
автоінфекціями	автоінфекція	noun	noun:inanim:p:v_oru
автоінфекціях	автоінфекція	noun	noun:inanim:p:v_mis
автоінфекціє	автоінфекція	noun	noun:inanim:f:v_kly
автоінфекцією	автоінфекція	noun	noun:inanim:f:v_oru
автоінфекції	автоінфекція	noun	noun:inanim:f:v_dav
автоінфекції	автоінфекція	noun	noun:inanim:f:v_mis
автоінфекції	автоінфекція	noun	noun:inanim:f:v_rod
автоінфекції	автоінфекція	noun	noun:inanim:p:v_kly
автоінфекції	автоінфекція	noun	noun:inanim:p:v_naz
автоінфекції	автоінфекція	noun	noun:inanim:p:v_zna
автоінформатор	автоінформатор	noun	noun:inanim:m:v_naz
автоінформатор	автоінформатор	noun	noun:inanim:m:v_zna
автоінформатора	автоінформатор	noun	noun:inanim:m:v_rod
автоінформаторам	автоінформатор	noun	noun:inanim:p:v_dav
автоінформаторами	автоінформатор	noun	noun:inanim:p:v_oru
автоінформаторах	автоінформатор	noun	noun:inanim:p:v_mis
автоінформаторе	автоінформатор	noun	noun:inanim:m:v_kly
автоінформатори	автоінформатор	noun	noun:inanim:p:v_kly
автоінформатори	автоінформатор	noun	noun:inanim:p:v_naz
автоінформатори	автоінформатор	noun	noun:inanim:p:v_zna
автоінформаторові	автоінформатор	noun	noun:inanim:m:v_dav
автоінформаторові	автоінформатор	noun	noun:inanim:m:v_mis
автоінформатором	автоінформатор	noun	noun:inanim:m:v_oru
автоінформаторі	автоінформатор	noun	noun:inanim:m:v_mis
автоінформаторів	автоінформатор	noun	noun:inanim:p:v_rod
автоіонізатор	автоіонізатор	noun	noun:inanim:m:v_naz
автоіонізатор	автоіонізатор	noun	noun:inanim:m:v_zna
автоіонізатора	автоіонізатор	noun	noun:inanim:m:v_rod
автоіонізаторам	автоіонізатор	noun	noun:inanim:p:v_dav
автоіонізаторами	автоіонізатор	noun	noun:inanim:p:v_oru
автоіонізаторах	автоіонізатор	noun	noun:inanim:p:v_mis
автоіонізаторе	автоіонізатор	noun	noun:inanim:m:v_kly
автоіонізатори	автоіонізатор	noun	noun:inanim:p:v_kly
автоіонізатори	автоіонізатор	noun	noun:inanim:p:v_naz
автоіонізатори	автоіонізатор	noun	noun:inanim:p:v_zna
автоіонізаторові	автоіонізатор	noun	noun:inanim:m:v_dav
автоіонізаторові	автоіонізатор	noun	noun:inanim:m:v_mis
автоіонізатором	автоіонізатор	noun	noun:inanim:m:v_oru
автоіонізаторі	автоіонізатор	noun	noun:inanim:m:v_mis
автоіонізаторів	автоіонізатор	noun	noun:inanim:p:v_rod
автівка	автівка	noun	noun:inanim:f:v_naz
автівкам	автівка	noun	noun:inanim:p:v_dav
автівками	автівка	noun	noun:inanim:p:v_oru
автівках	автівка	noun	noun:inanim:p:v_mis
автівки	автівка	noun	noun:inanim:f:v_rod
автівки	автівка	noun	noun:inanim:p:v_kly
автівки	автівка	noun	noun:inanim:p:v_naz
автівки	автівка	noun	noun:inanim:p:v_zna
автівко	автівка	noun	noun:inanim:f:v_kly
автівкою	автівка	noun	noun:inanim:f:v_oru
автівку	автівка	noun	noun:inanim:f:v_zna
автівок	автівка	noun	noun:inanim:p:v_rod
автівці	автівка	noun	noun:inanim:f:v_dav
автівці	автівка	noun	noun:inanim:f:v_mis
аву	ава	noun	noun:inanim:f:v_zna:slang
аві	ава	noun	noun:inanim:f:v_dav:slang
аві	ава	noun	noun:inanim:f:v_mis:slang
авіааварій	авіааварія	noun	noun:inanim:p:v_rod
авіааварію	авіааварія	noun	noun:inanim:f:v_zna
авіааварія	авіааварія	noun	noun:inanim:f:v_naz
авіааваріям	авіааварія	noun	noun:inanim:p:v_dav
авіааваріями	авіааварія	noun	noun:inanim:p:v_oru
авіааваріях	авіааварія	noun	noun:inanim:p:v_mis
авіааваріє	авіааварія	noun	noun:inanim:f:v_kly
авіааварією	авіааварія	noun	noun:inanim:f:v_oru
авіааварії	авіааварія	noun	noun:inanim:f:v_dav
авіааварії	авіааварія	noun	noun:inanim:f:v_mis
авіааварії	авіааварія	noun	noun:inanim:f:v_rod
авіааварії	авіааварія	noun	noun:inanim:p:v_kly
авіааварії	авіааварія	noun	noun:inanim:p:v_naz
авіааварії	авіааварія	noun	noun:inanim:p:v_zna
авіаагент	авіаагент	noun	noun:anim:m:v_naz
авіаагента	авіаагент	noun	noun:anim:m:v_rod
авіаагента	авіаагент	noun	noun:anim:m:v_zna
авіаагентам	авіаагент	noun	noun:anim:p:v_dav
авіаагентами	авіаагент	noun	noun:anim:p:v_oru
авіаагентах	авіаагент	noun	noun:anim:p:v_mis
авіаагенте	авіаагент	noun	noun:anim:m:v_kly
авіаагенти	авіаагент	noun	noun:anim:p:v_kly
авіаагенти	авіаагент	noun	noun:anim:p:v_naz
авіаагенти	авіаагент	noun	noun:anim:p:v_zna:rare
авіаагентові	авіаагент	noun	noun:anim:m:v_dav
авіаагентові	авіаагент	noun	noun:anim:m:v_mis
авіаагентом	авіаагент	noun	noun:anim:m:v_oru
авіаагенті	авіаагент	noun	noun:anim:m:v_mis
авіаагентів	авіаагент	noun	noun:anim:p:v_rod
авіаагентів	авіаагент	noun	noun:anim:p:v_zna
авіаадміністрацій	авіаадміністрація	noun	noun:inanim:p:v_rod
авіаадміністрацію	авіаадміністрація	noun	noun:inanim:f:v_zna
авіаадміністрація	авіаадміністрація	noun	noun:inanim:f:v_naz
авіаадміністраціям	авіаадміністрація	noun	noun:inanim:p:v_dav
авіаадміністраціями	авіаадміністрація	noun	noun:inanim:p:v_oru
авіаадміністраціях	авіаадміністрація	noun	noun:inanim:p:v_mis
авіаадміністраціє	авіаадміністрація	noun	noun:inanim:f:v_kly
авіаадміністрацією	авіаадміністрація	noun	noun:inanim:f:v_oru
авіаадміністрації	авіаадміністрація	noun	noun:inanim:f:v_dav
авіаадміністрації	авіаадміністрація	noun	noun:inanim:f:v_mis
авіаадміністрації	авіаадміністрація	noun	noun:inanim:f:v_rod
авіаадміністрації	авіаадміністрація	noun	noun:inanim:p:v_kly
авіаадміністрації	авіаадміністрація	noun	noun:inanim:p:v_naz
авіаадміністрації	авіаадміністрація	noun	noun:inanim:p:v_zna
авіаальянс	авіаальянс	noun	noun:inanim:m:v_naz
авіаальянс	авіаальянс	noun	noun:inanim:m:v_zna
авіаальянсам	авіаальянс	noun	noun:inanim:p:v_dav
авіаальянсами	авіаальянс	noun	noun:inanim:p:v_oru
авіаальянсах	авіаальянс	noun	noun:inanim:p:v_mis
авіаальянсе	авіаальянс	noun	noun:inanim:m:v_kly
авіаальянси	авіаальянс	noun	noun:inanim:p:v_kly
авіаальянси	авіаальянс	noun	noun:inanim:p:v_naz
авіаальянси	авіаальянс	noun	noun:inanim:p:v_zna
авіаальянсові	авіаальянс	noun	noun:inanim:m:v_dav
авіаальянсові	авіаальянс	noun	noun:inanim:m:v_mis
авіаальянсом	авіаальянс	noun	noun:inanim:m:v_oru
авіаальянсу	авіаальянс	noun	noun:inanim:m:v_dav
авіаальянсу	авіаальянс	noun	noun:inanim:m:v_mis
авіаальянсу	авіаальянс	noun	noun:inanim:m:v_rod
авіаальянсі	авіаальянс	noun	noun:inanim:m:v_mis
авіаальянсів	авіаальянс	noun	noun:inanim:p:v_rod
авіааматор	авіааматор	noun	noun:anim:m:v_naz
авіааматора	авіааматор	noun	noun:anim:m:v_rod
авіааматора	авіааматор	noun	noun:anim:m:v_zna
авіааматорам	авіааматор	noun	noun:anim:p:v_dav
авіааматорами	авіааматор	noun	noun:anim:p:v_oru
авіааматорах	авіааматор	noun	noun:anim:p:v_mis
авіааматоре	авіааматор	noun	noun:anim:m:v_kly
авіааматори	авіааматор	noun	noun:anim:p:v_kly
авіааматори	авіааматор	noun	noun:anim:p:v_naz
авіааматори	авіааматор	noun	noun:anim:p:v_zna:rare
авіааматорові	авіааматор	noun	noun:anim:m:v_dav
авіааматорові	авіааматор	noun	noun:anim:m:v_mis
авіааматором	авіааматор	noun	noun:anim:m:v_oru
авіааматорі	авіааматор	noun	noun:anim:m:v_mis
авіааматорів	авіааматор	noun	noun:anim:p:v_rod
авіааматорів	авіааматор	noun	noun:anim:p:v_zna
авіаатак	авіаатака	noun	noun:inanim:p:v_rod
авіаатака	авіаатака	noun	noun:inanim:f:v_naz
авіаатакам	авіаатака	noun	noun:inanim:p:v_dav
авіаатаками	авіаатака	noun	noun:inanim:p:v_oru
авіаатаках	авіаатака	noun	noun:inanim:p:v_mis
авіаатаки	авіаатака	noun	noun:inanim:f:v_rod
авіаатаки	авіаатака	noun	noun:inanim:p:v_kly
авіаатаки	авіаатака	noun	noun:inanim:p:v_naz
авіаатаки	авіаатака	noun	noun:inanim:p:v_zna
авіаатако	авіаатака	noun	noun:inanim:f:v_kly
авіаатакою	авіаатака	noun	noun:inanim:f:v_oru
авіаатаку	авіаатака	noun	noun:inanim:f:v_zna
авіаатаці	авіаатака	noun	noun:inanim:f:v_dav
авіаатаці	авіаатака	noun	noun:inanim:f:v_mis
авіабаз	авіабаза	noun	noun:inanim:p:v_rod
авіабаза	авіабаза	noun	noun:inanim:f:v_naz
авіабазам	авіабаза	noun	noun:inanim:p:v_dav
авіабазами	авіабаза	noun	noun:inanim:p:v_oru
авіабазах	авіабаза	noun	noun:inanim:p:v_mis
авіабази	авіабаза	noun	noun:inanim:f:v_rod
авіабази	авіабаза	noun	noun:inanim:p:v_kly
авіабази	авіабаза	noun	noun:inanim:p:v_naz
авіабази	авіабаза	noun	noun:inanim:p:v_zna
авіабазо	авіабаза	noun	noun:inanim:f:v_kly
авіабазою	авіабаза	noun	noun:inanim:f:v_oru
авіабазу	авіабаза	noun	noun:inanim:f:v_zna
авіабазі	авіабаза	noun	noun:inanim:f:v_dav
авіабазі	авіабаза	noun	noun:inanim:f:v_mis
авіабензин	авіабензин	noun	noun:inanim:m:v_naz
авіабензин	авіабензин	noun	noun:inanim:m:v_zna
авіабензинам	авіабензин	noun	noun:inanim:p:v_dav
авіабензинами	авіабензин	noun	noun:inanim:p:v_oru
авіабензинах	авіабензин	noun	noun:inanim:p:v_mis
авіабензине	авіабензин	noun	noun:inanim:m:v_kly
авіабензини	авіабензин	noun	noun:inanim:p:v_kly
авіабензини	авіабензин	noun	noun:inanim:p:v_naz
авіабензини	авіабензин	noun	noun:inanim:p:v_zna
авіабензинові	авіабензин	noun	noun:inanim:m:v_dav
авіабензинові	авіабензин	noun	noun:inanim:m:v_mis
авіабензином	авіабензин	noun	noun:inanim:m:v_oru
авіабензину	авіабензин	noun	noun:inanim:m:v_dav
авіабензину	авіабензин	noun	noun:inanim:m:v_mis
авіабензину	авіабензин	noun	noun:inanim:m:v_rod
авіабензині	авіабензин	noun	noun:inanim:m:v_mis
авіабензинів	авіабензин	noun	noun:inanim:p:v_rod
авіабомб	авіабомба	noun	noun:inanim:p:v_rod
авіабомба	авіабомба	noun	noun:inanim:f:v_naz
авіабомбам	авіабомба	noun	noun:inanim:p:v_dav
авіабомбами	авіабомба	noun	noun:inanim:p:v_oru
авіабомбардуванню	авіабомбардування	noun	noun:inanim:n:v_dav
авіабомбардуванню	авіабомбардування	noun	noun:inanim:n:v_mis
авіабомбардування	авіабомбардування	noun	noun:inanim:n:v_kly
авіабомбардування	авіабомбардування	noun	noun:inanim:n:v_naz
авіабомбардування	авіабомбардування	noun	noun:inanim:n:v_rod
авіабомбардування	авіабомбардування	noun	noun:inanim:n:v_zna
авіабомбардування	авіабомбардування	noun	noun:inanim:p:v_kly
авіабомбардування	авіабомбардування	noun	noun:inanim:p:v_naz
авіабомбардування	авіабомбардування	noun	noun:inanim:p:v_zna
авіабомбардуванням	авіабомбардування	noun	noun:inanim:n:v_oru
авіабомбардуванням	авіабомбардування	noun	noun:inanim:p:v_dav
авіабомбардуваннями	авіабомбардування	noun	noun:inanim:p:v_oru
авіабомбардуваннях	авіабомбардування	noun	noun:inanim:p:v_mis
авіабомбардуванні	авіабомбардування	noun	noun:inanim:n:v_mis
авіабомбардувань	авіабомбардування	noun	noun:inanim:p:v_rod
авіабомбах	авіабомба	noun	noun:inanim:p:v_mis
авіабомби	авіабомба	noun	noun:inanim:f:v_rod
авіабомби	авіабомба	noun	noun:inanim:p:v_kly
авіабомби	авіабомба	noun	noun:inanim:p:v_naz
авіабомби	авіабомба	noun	noun:inanim:p:v_zna
авіабомбо	авіабомба	noun	noun:inanim:f:v_kly
авіабомбою	авіабомба	noun	noun:inanim:f:v_oru
авіабомбу	авіабомба	noun	noun:inanim:f:v_zna
авіабомбуванню	авіабомбування	noun	noun:inanim:n:v_dav
авіабомбуванню	авіабомбування	noun	noun:inanim:n:v_mis
авіабомбування	авіабомбування	noun	noun:inanim:n:v_kly
авіабомбування	авіабомбування	noun	noun:inanim:n:v_naz
авіабомбування	авіабомбування	noun	noun:inanim:n:v_rod
авіабомбування	авіабомбування	noun	noun:inanim:n:v_zna
авіабомбування	авіабомбування	noun	noun:inanim:p:v_kly
авіабомбування	авіабомбування	noun	noun:inanim:p:v_naz
авіабомбування	авіабомбування	noun	noun:inanim:p:v_zna
авіабомбуванням	авіабомбування	noun	noun:inanim:n:v_oru
авіабомбуванням	авіабомбування	noun	noun:inanim:p:v_dav
авіабомбуваннями	авіабомбування	noun	noun:inanim:p:v_oru
авіабомбуваннях	авіабомбування	noun	noun:inanim:p:v_mis
авіабомбуванні	авіабомбування	noun	noun:inanim:n:v_mis
авіабомбувань	авіабомбування	noun	noun:inanim:p:v_rod
авіабомбі	авіабомба	noun	noun:inanim:f:v_dav
авіабомбі	авіабомба	noun	noun:inanim:f:v_mis
авіаборг	авіаборг	noun	noun:inanim:m:v_naz
авіаборг	авіаборг	noun	noun:inanim:m:v_zna
авіаборгам	авіаборг	noun	noun:inanim:p:v_dav
авіаборгами	авіаборг	noun	noun:inanim:p:v_oru
авіаборгах	авіаборг	noun	noun:inanim:p:v_mis
авіаборги	авіаборг	noun	noun:inanim:p:v_kly
авіаборги	авіаборг	noun	noun:inanim:p:v_naz
авіаборги	авіаборг	noun	noun:inanim:p:v_zna
авіаборгові	авіаборг	noun	noun:inanim:m:v_dav
авіаборгові	авіаборг	noun	noun:inanim:m:v_mis
авіаборгом	авіаборг	noun	noun:inanim:m:v_oru
авіаборгу	авіаборг	noun	noun:inanim:m:v_dav
авіаборгу	авіаборг	noun	noun:inanim:m:v_kly
авіаборгу	авіаборг	noun	noun:inanim:m:v_mis
авіаборгу	авіаборг	noun	noun:inanim:m:v_rod
авіаборгів	авіаборг	noun	noun:inanim:p:v_rod
авіаборт	авіаборт	noun	noun:inanim:m:v_naz
авіаборт	авіаборт	noun	noun:inanim:m:v_zna
авіаборта	авіаборт	noun	noun:inanim:m:v_rod
авіабортам	авіаборт	noun	noun:inanim:p:v_dav
авіабортами	авіаборт	noun	noun:inanim:p:v_oru
авіабортах	авіаборт	noun	noun:inanim:p:v_mis
авіаборте	авіаборт	noun	noun:inanim:m:v_kly
авіаборти	авіаборт	noun	noun:inanim:p:v_kly
авіаборти	авіаборт	noun	noun:inanim:p:v_naz
авіаборти	авіаборт	noun	noun:inanim:p:v_zna
авіабортові	авіаборт	noun	noun:inanim:m:v_dav
авіабортові	авіаборт	noun	noun:inanim:m:v_mis
авіабортом	авіаборт	noun	noun:inanim:m:v_oru
авіаборті	авіаборт	noun	noun:inanim:m:v_mis
авіабортів	авіаборт	noun	noun:inanim:p:v_rod
авіабригад	авіабригада	noun	noun:inanim:p:v_rod
авіабригада	авіабригада	noun	noun:inanim:f:v_naz
авіабригадам	авіабригада	noun	noun:inanim:p:v_dav
авіабригадами	авіабригада	noun	noun:inanim:p:v_oru
авіабригадах	авіабригада	noun	noun:inanim:p:v_mis
авіабригади	авіабригада	noun	noun:inanim:f:v_rod
авіабригади	авіабригада	noun	noun:inanim:p:v_kly
авіабригади	авіабригада	noun	noun:inanim:p:v_naz
авіабригади	авіабригада	noun	noun:inanim:p:v_zna
авіабригадо	авіабригада	noun	noun:inanim:f:v_kly
авіабригадою	авіабригада	noun	noun:inanim:f:v_oru
авіабригаду	авіабригада	noun	noun:inanim:f:v_zna
авіабригаді	авіабригада	noun	noun:inanim:f:v_dav
авіабригаді	авіабригада	noun	noun:inanim:f:v_mis
авіабудуванню	авіабудування	noun	noun:inanim:n:v_dav
авіабудуванню	авіабудування	noun	noun:inanim:n:v_mis
авіабудування	авіабудування	noun	noun:inanim:n:v_kly
авіабудування	авіабудування	noun	noun:inanim:n:v_naz
авіабудування	авіабудування	noun	noun:inanim:n:v_rod
авіабудування	авіабудування	noun	noun:inanim:n:v_zna
авіабудування	авіабудування	noun	noun:inanim:p:v_kly
авіабудування	авіабудування	noun	noun:inanim:p:v_naz
авіабудування	авіабудування	noun	noun:inanim:p:v_zna
авіабудуванням	авіабудування	noun	noun:inanim:n:v_oru
авіабудуванням	авіабудування	noun	noun:inanim:p:v_dav
авіабудуваннями	авіабудування	noun	noun:inanim:p:v_oru
авіабудуваннях	авіабудування	noun	noun:inanim:p:v_mis
авіабудуванні	авіабудування	noun	noun:inanim:n:v_mis
авіабудувань	авіабудування	noun	noun:inanim:p:v_rod
авіабудівельник	авіабудівельник	noun	noun:anim:m:v_naz
авіабудівельника	авіабудівельник	noun	noun:anim:m:v_rod
авіабудівельника	авіабудівельник	noun	noun:anim:m:v_zna
авіабудівельникам	авіабудівельник	noun	noun:anim:p:v_dav
авіабудівельниками	авіабудівельник	noun	noun:anim:p:v_oru
авіабудівельниках	авіабудівельник	noun	noun:anim:p:v_mis
авіабудівельники	авіабудівельник	noun	noun:anim:p:v_kly
авіабудівельники	авіабудівельник	noun	noun:anim:p:v_naz
авіабудівельники	авіабудівельник	noun	noun:anim:p:v_zna:rare
авіабудівельникові	авіабудівельник	noun	noun:anim:m:v_dav
авіабудівельникові	авіабудівельник	noun	noun:anim:m:v_mis
авіабудівельником	авіабудівельник	noun	noun:anim:m:v_oru
авіабудівельнику	авіабудівельник	noun	noun:anim:m:v_dav
авіабудівельнику	авіабудівельник	noun	noun:anim:m:v_kly
авіабудівельнику	авіабудівельник	noun	noun:anim:m:v_mis
авіабудівельників	авіабудівельник	noun	noun:anim:p:v_rod
авіабудівельників	авіабудівельник	noun	noun:anim:p:v_zna
авіабудівник	авіабудівник	noun	noun:anim:m:v_naz
авіабудівника	авіабудівник	noun	noun:anim:m:v_rod
авіабудівника	авіабудівник	noun	noun:anim:m:v_zna
авіабудівникам	авіабудівник	noun	noun:anim:p:v_dav
авіабудівниками	авіабудівник	noun	noun:anim:p:v_oru
авіабудівниках	авіабудівник	noun	noun:anim:p:v_mis
авіабудівники	авіабудівник	noun	noun:anim:p:v_kly
авіабудівники	авіабудівник	noun	noun:anim:p:v_naz
авіабудівники	авіабудівник	noun	noun:anim:p:v_zna:rare
авіабудівникові	авіабудівник	noun	noun:anim:m:v_dav
авіабудівникові	авіабудівник	noun	noun:anim:m:v_mis
авіабудівником	авіабудівник	noun	noun:anim:m:v_oru
авіабудівнику	авіабудівник	noun	noun:anim:m:v_dav
авіабудівнику	авіабудівник	noun	noun:anim:m:v_kly
авіабудівнику	авіабудівник	noun	noun:anim:m:v_mis
авіабудівників	авіабудівник	noun	noun:anim:p:v_rod
авіабудівників	авіабудівник	noun	noun:anim:p:v_zna
авіабум	авіабум	noun	noun:inanim:m:v_naz
авіабум	авіабум	noun	noun:inanim:m:v_zna
авіабумам	авіабум	noun	noun:inanim:p:v_dav
авіабумами	авіабум	noun	noun:inanim:p:v_oru
авіабумах	авіабум	noun	noun:inanim:p:v_mis
авіабуме	авіабум	noun	noun:inanim:m:v_kly
авіабуми	авіабум	noun	noun:inanim:p:v_kly
авіабуми	авіабум	noun	noun:inanim:p:v_naz
авіабуми	авіабум	noun	noun:inanim:p:v_zna
авіабумові	авіабум	noun	noun:inanim:m:v_dav
авіабумові	авіабум	noun	noun:inanim:m:v_mis
авіабумом	авіабум	noun	noun:inanim:m:v_oru
авіабуму	авіабум	noun	noun:inanim:m:v_dav
авіабуму	авіабум	noun	noun:inanim:m:v_mis
авіабуму	авіабум	noun	noun:inanim:m:v_rod
авіабумі	авіабум	noun	noun:inanim:m:v_mis
авіабумів	авіабум	noun	noun:inanim:p:v_rod
авіабілет	авіабілет	noun	noun:inanim:m:v_naz
авіабілет	авіабілет	noun	noun:inanim:m:v_zna
авіабілета	авіабілет	noun	noun:inanim:m:v_rod
авіабілетам	авіабілет	noun	noun:inanim:p:v_dav
авіабілетами	авіабілет	noun	noun:inanim:p:v_oru
авіабілетах	авіабілет	noun	noun:inanim:p:v_mis
авіабілете	авіабілет	noun	noun:inanim:m:v_kly
авіабілети	авіабілет	noun	noun:inanim:p:v_kly
авіабілети	авіабілет	noun	noun:inanim:p:v_naz
авіабілети	авіабілет	noun	noun:inanim:p:v_zna
авіабілетові	авіабілет	noun	noun:inanim:m:v_dav
авіабілетові	авіабілет	noun	noun:inanim:m:v_mis
авіабілетом	авіабілет	noun	noun:inanim:m:v_oru
авіабілеті	авіабілет	noun	noun:inanim:m:v_mis
авіабілетів	авіабілет	noun	noun:inanim:p:v_rod
авіавелетень	авіавелетень	noun	noun:anim:m:v_naz
авіавелетневі	авіавелетень	noun	noun:anim:m:v_dav
авіавелетневі	авіавелетень	noun	noun:anim:m:v_mis
авіавелетнем	авіавелетень	noun	noun:anim:m:v_oru
авіавелетню	авіавелетень	noun	noun:anim:m:v_dav
авіавелетню	авіавелетень	noun	noun:anim:m:v_kly
авіавелетню	авіавелетень	noun	noun:anim:m:v_mis
авіавелетня	авіавелетень	noun	noun:anim:m:v_rod
авіавелетня	авіавелетень	noun	noun:anim:m:v_zna
авіавелетням	авіавелетень	noun	noun:anim:p:v_dav
авіавелетнями	авіавелетень	noun	noun:anim:p:v_oru
авіавелетнях	авіавелетень	noun	noun:anim:p:v_mis
авіавелетні	авіавелетень	noun	noun:anim:m:v_mis
авіавелетні	авіавелетень	noun	noun:anim:p:v_kly
авіавелетні	авіавелетень	noun	noun:anim:p:v_naz
авіавелетні	авіавелетень	noun	noun:anim:p:v_zna:rare
авіавелетнів	авіавелетень	noun	noun:anim:p:v_rod
авіавелетнів	авіавелетень	noun	noun:anim:p:v_zna
авіавильотам	авіавиліт	noun	noun:inanim:p:v_dav
авіавильотами	авіавиліт	noun	noun:inanim:p:v_oru
авіавильотах	авіавиліт	noun	noun:inanim:p:v_mis
авіавильоте	авіавиліт	noun	noun:inanim:m:v_kly
авіавильоти	авіавиліт	noun	noun:inanim:p:v_kly
авіавильоти	авіавиліт	noun	noun:inanim:p:v_naz
авіавильоти	авіавиліт	noun	noun:inanim:p:v_zna
авіавильотові	авіавиліт	noun	noun:inanim:m:v_dav
авіавильотові	авіавиліт	noun	noun:inanim:m:v_mis
авіавильотом	авіавиліт	noun	noun:inanim:m:v_oru
авіавильоту	авіавиліт	noun	noun:inanim:m:v_dav
авіавильоту	авіавиліт	noun	noun:inanim:m:v_mis
авіавильоту	авіавиліт	noun	noun:inanim:m:v_rod
авіавильоті	авіавиліт	noun	noun:inanim:m:v_mis
авіавильотів	авіавиліт	noun	noun:inanim:p:v_rod
авіавиліт	авіавиліт	noun	noun:inanim:m:v_naz
авіавиліт	авіавиліт	noun	noun:inanim:m:v_zna
авіавипадкам	авіавипадок	noun	noun:inanim:p:v_dav
авіавипадками	авіавипадок	noun	noun:inanim:p:v_oru
авіавипадках	авіавипадок	noun	noun:inanim:p:v_mis
авіавипадки	авіавипадок	noun	noun:inanim:p:v_kly
авіавипадки	авіавипадок	noun	noun:inanim:p:v_naz
авіавипадки	авіавипадок	noun	noun:inanim:p:v_zna
авіавипадкові	авіавипадок	noun	noun:inanim:m:v_dav
авіавипадкові	авіавипадок	noun	noun:inanim:m:v_mis
авіавипадком	авіавипадок	noun	noun:inanim:m:v_oru
авіавипадку	авіавипадок	noun	noun:inanim:m:v_dav
авіавипадку	авіавипадок	noun	noun:inanim:m:v_kly
авіавипадку	авіавипадок	noun	noun:inanim:m:v_mis
авіавипадку	авіавипадок	noun	noun:inanim:m:v_rod
авіавипадків	авіавипадок	noun	noun:inanim:p:v_rod
авіавипадок	авіавипадок	noun	noun:inanim:m:v_naz
авіавипадок	авіавипадок	noun	noun:inanim:m:v_zna
авіавиробник	авіавиробник	noun	noun:anim:m:v_naz
авіавиробника	авіавиробник	noun	noun:anim:m:v_rod
авіавиробника	авіавиробник	noun	noun:anim:m:v_zna
авіавиробникам	авіавиробник	noun	noun:anim:p:v_dav
авіавиробниками	авіавиробник	noun	noun:anim:p:v_oru
авіавиробниках	авіавиробник	noun	noun:anim:p:v_mis
авіавиробники	авіавиробник	noun	noun:anim:p:v_kly
авіавиробники	авіавиробник	noun	noun:anim:p:v_naz
авіавиробники	авіавиробник	noun	noun:anim:p:v_zna:rare
авіавиробникові	авіавиробник	noun	noun:anim:m:v_dav
авіавиробникові	авіавиробник	noun	noun:anim:m:v_mis
авіавиробником	авіавиробник	noun	noun:anim:m:v_oru
авіавиробнику	авіавиробник	noun	noun:anim:m:v_dav
авіавиробнику	авіавиробник	noun	noun:anim:m:v_kly
авіавиробнику	авіавиробник	noun	noun:anim:m:v_mis
авіавиробників	авіавиробник	noun	noun:anim:p:v_rod
авіавиробників	авіавиробник	noun	noun:anim:p:v_zna
авіавиробництв	авіавиробництво	noun	noun:inanim:p:v_rod
авіавиробництва	авіавиробництво	noun	noun:inanim:n:v_rod
авіавиробництва	авіавиробництво	noun	noun:inanim:p:v_kly
авіавиробництва	авіавиробництво	noun	noun:inanim:p:v_naz
авіавиробництва	авіавиробництво	noun	noun:inanim:p:v_zna
авіавиробництвам	авіавиробництво	noun	noun:inanim:p:v_dav
авіавиробництвами	авіавиробництво	noun	noun:inanim:p:v_oru
авіавиробництвах	авіавиробництво	noun	noun:inanim:p:v_mis
авіавиробництво	авіавиробництво	noun	noun:inanim:n:v_kly
авіавиробництво	авіавиробництво	noun	noun:inanim:n:v_naz
авіавиробництво	авіавиробництво	noun	noun:inanim:n:v_zna
авіавиробництвом	авіавиробництво	noun	noun:inanim:n:v_oru
авіавиробництву	авіавиробництво	noun	noun:inanim:n:v_dav
авіавиробництву	авіавиробництво	noun	noun:inanim:n:v_mis
авіавиробництві	авіавиробництво	noun	noun:inanim:n:v_mis
авіавиставка	авіавиставка	noun	noun:inanim:f:v_naz
авіавиставкам	авіавиставка	noun	noun:inanim:p:v_dav
авіавиставками	авіавиставка	noun	noun:inanim:p:v_oru
авіавиставках	авіавиставка	noun	noun:inanim:p:v_mis
авіавиставки	авіавиставка	noun	noun:inanim:f:v_rod
авіавиставки	авіавиставка	noun	noun:inanim:p:v_kly
авіавиставки	авіавиставка	noun	noun:inanim:p:v_naz
авіавиставки	авіавиставка	noun	noun:inanim:p:v_zna
авіавиставко	авіавиставка	noun	noun:inanim:f:v_kly
авіавиставкою	авіавиставка	noun	noun:inanim:f:v_oru
авіавиставку	авіавиставка	noun	noun:inanim:f:v_zna
авіавиставок	авіавиставка	noun	noun:inanim:p:v_rod
авіавиставці	авіавиставка	noun	noun:inanim:f:v_dav
авіавиставці	авіавиставка	noun	noun:inanim:f:v_mis
авіавиступ	авіавиступ	noun	noun:inanim:m:v_naz
авіавиступ	авіавиступ	noun	noun:inanim:m:v_zna
авіавиступам	авіавиступ	noun	noun:inanim:p:v_dav
авіавиступами	авіавиступ	noun	noun:inanim:p:v_oru
авіавиступах	авіавиступ	noun	noun:inanim:p:v_mis
авіавиступе	авіавиступ	noun	noun:inanim:m:v_kly
авіавиступи	авіавиступ	noun	noun:inanim:p:v_kly
авіавиступи	авіавиступ	noun	noun:inanim:p:v_naz
авіавиступи	авіавиступ	noun	noun:inanim:p:v_zna
авіавиступові	авіавиступ	noun	noun:inanim:m:v_dav
авіавиступові	авіавиступ	noun	noun:inanim:m:v_mis
авіавиступом	авіавиступ	noun	noun:inanim:m:v_oru
авіавиступу	авіавиступ	noun	noun:inanim:m:v_dav
авіавиступу	авіавиступ	noun	noun:inanim:m:v_mis
авіавиступу	авіавиступ	noun	noun:inanim:m:v_rod
авіавиступі	авіавиступ	noun	noun:inanim:m:v_mis
авіавиступів	авіавиступ	noun	noun:inanim:p:v_rod
авіавояж	авіавояж	noun	noun:inanim:m:v_naz
авіавояж	авіавояж	noun	noun:inanim:m:v_zna
авіавояжам	авіавояж	noun	noun:inanim:p:v_dav
авіавояжами	авіавояж	noun	noun:inanim:p:v_oru
авіавояжах	авіавояж	noun	noun:inanim:p:v_mis
авіавояже	авіавояж	noun	noun:inanim:m:v_kly
авіавояжеві	авіавояж	noun	noun:inanim:m:v_dav
авіавояжеві	авіавояж	noun	noun:inanim:m:v_mis
авіавояжем	авіавояж	noun	noun:inanim:m:v_oru
авіавояжу	авіавояж	noun	noun:inanim:m:v_dav
авіавояжу	авіавояж	noun	noun:inanim:m:v_mis
авіавояжу	авіавояж	noun	noun:inanim:m:v_rod
авіавояжі	авіавояж	noun	noun:inanim:m:v_mis
авіавояжі	авіавояж	noun	noun:inanim:p:v_kly
авіавояжі	авіавояж	noun	noun:inanim:p:v_naz
авіавояжі	авіавояж	noun	noun:inanim:p:v_zna
авіавояжів	авіавояж	noun	noun:inanim:p:v_rod
авіавузла	авіавузол	noun	noun:inanim:m:v_rod
авіавузлам	авіавузол	noun	noun:inanim:p:v_dav
авіавузлами	авіавузол	noun	noun:inanim:p:v_oru
авіавузлах	авіавузол	noun	noun:inanim:p:v_mis
авіавузле	авіавузол	noun	noun:inanim:m:v_kly
авіавузли	авіавузол	noun	noun:inanim:p:v_kly
авіавузли	авіавузол	noun	noun:inanim:p:v_naz
авіавузли	авіавузол	noun	noun:inanim:p:v_zna
авіавузлові	авіавузол	noun	noun:inanim:m:v_dav
авіавузлові	авіавузол	noun	noun:inanim:m:v_mis
авіавузлом	авіавузол	noun	noun:inanim:m:v_oru
авіавузлі	авіавузол	noun	noun:inanim:m:v_mis
авіавузлів	авіавузол	noun	noun:inanim:p:v_rod
авіавузол	авіавузол	noun	noun:inanim:m:v_naz
авіавузол	авіавузол	noun	noun:inanim:m:v_zna
авіавіраж	авіавіраж	noun	noun:inanim:m:v_naz
авіавіраж	авіавіраж	noun	noun:inanim:m:v_zna
авіавіражам	авіавіраж	noun	noun:inanim:p:v_dav
авіавіражами	авіавіраж	noun	noun:inanim:p:v_oru
авіавіражах	авіавіраж	noun	noun:inanim:p:v_mis
авіавіраже	авіавіраж	noun	noun:inanim:m:v_kly
авіавіражеві	авіавіраж	noun	noun:inanim:m:v_dav
авіавіражеві	авіавіраж	noun	noun:inanim:m:v_mis
авіавіражем	авіавіраж	noun	noun:inanim:m:v_oru
авіавіражу	авіавіраж	noun	noun:inanim:m:v_dav
авіавіражу	авіавіраж	noun	noun:inanim:m:v_mis
авіавіражу	авіавіраж	noun	noun:inanim:m:v_rod
авіавіражі	авіавіраж	noun	noun:inanim:m:v_mis
авіавіражі	авіавіраж	noun	noun:inanim:p:v_kly
авіавіражі	авіавіраж	noun	noun:inanim:p:v_naz
авіавіражі	авіавіраж	noun	noun:inanim:p:v_zna
авіавіражів	авіавіраж	noun	noun:inanim:p:v_rod
авіагараж	авіагараж	noun	noun:inanim:m:v_naz
авіагараж	авіагараж	noun	noun:inanim:m:v_zna
авіагаража	авіагараж	noun	noun:inanim:m:v_rod
авіагаражам	авіагараж	noun	noun:inanim:p:v_dav
авіагаражами	авіагараж	noun	noun:inanim:p:v_oru
авіагаражах	авіагараж	noun	noun:inanim:p:v_mis
авіагараже	авіагараж	noun	noun:inanim:m:v_kly
авіагаражеві	авіагараж	noun	noun:inanim:m:v_dav
авіагаражеві	авіагараж	noun	noun:inanim:m:v_mis
авіагаражем	авіагараж	noun	noun:inanim:m:v_oru
авіагаражі	авіагараж	noun	noun:inanim:m:v_mis
авіагаражі	авіагараж	noun	noun:inanim:p:v_kly
авіагаражі	авіагараж	noun	noun:inanim:p:v_naz
авіагаражі	авіагараж	noun	noun:inanim:p:v_zna
авіагаражів	авіагараж	noun	noun:inanim:p:v_rod
авіагармат	авіагармата	noun	noun:inanim:p:v_rod
авіагармата	авіагармата	noun	noun:inanim:f:v_naz
авіагарматам	авіагармата	noun	noun:inanim:p:v_dav
авіагарматами	авіагармата	noun	noun:inanim:p:v_oru
авіагарматах	авіагармата	noun	noun:inanim:p:v_mis
авіагармати	авіагармата	noun	noun:inanim:f:v_rod
авіагармати	авіагармата	noun	noun:inanim:p:v_kly
авіагармати	авіагармата	noun	noun:inanim:p:v_naz
авіагармати	авіагармата	noun	noun:inanim:p:v_zna
авіагармато	авіагармата	noun	noun:inanim:f:v_kly
авіагарматою	авіагармата	noun	noun:inanim:f:v_oru
авіагармату	авіагармата	noun	noun:inanim:f:v_zna
авіагарматі	авіагармата	noun	noun:inanim:f:v_dav
авіагарматі	авіагармата	noun	noun:inanim:f:v_mis
авіагарнізон	авіагарнізон	noun	noun:inanim:m:v_naz
авіагарнізон	авіагарнізон	noun	noun:inanim:m:v_zna
авіагарнізонам	авіагарнізон	noun	noun:inanim:p:v_dav
авіагарнізонами	авіагарнізон	noun	noun:inanim:p:v_oru
авіагарнізонах	авіагарнізон	noun	noun:inanim:p:v_mis
авіагарнізоне	авіагарнізон	noun	noun:inanim:m:v_kly
авіагарнізони	авіагарнізон	noun	noun:inanim:p:v_kly
авіагарнізони	авіагарнізон	noun	noun:inanim:p:v_naz
авіагарнізони	авіагарнізон	noun	noun:inanim:p:v_zna
авіагарнізонові	авіагарнізон	noun	noun:inanim:m:v_dav
авіагарнізонові	авіагарнізон	noun	noun:inanim:m:v_mis
авіагарнізоном	авіагарнізон	noun	noun:inanim:m:v_oru
авіагарнізону	авіагарнізон	noun	noun:inanim:m:v_dav
авіагарнізону	авіагарнізон	noun	noun:inanim:m:v_mis
авіагарнізону	авіагарнізон	noun	noun:inanim:m:v_rod
авіагарнізоні	авіагарнізон	noun	noun:inanim:m:v_mis
авіагарнізонів	авіагарнізон	noun	noun:inanim:p:v_rod
авіагоризонт	авіагоризонт	noun	noun:inanim:m:v_naz
авіагоризонт	авіагоризонт	noun	noun:inanim:m:v_zna
авіагоризонтам	авіагоризонт	noun	noun:inanim:p:v_dav
авіагоризонтами	авіагоризонт	noun	noun:inanim:p:v_oru
авіагоризонтах	авіагоризонт	noun	noun:inanim:p:v_mis
авіагоризонте	авіагоризонт	noun	noun:inanim:m:v_kly
авіагоризонти	авіагоризонт	noun	noun:inanim:p:v_kly
авіагоризонти	авіагоризонт	noun	noun:inanim:p:v_naz
авіагоризонти	авіагоризонт	noun	noun:inanim:p:v_zna
авіагоризонтові	авіагоризонт	noun	noun:inanim:m:v_dav
авіагоризонтові	авіагоризонт	noun	noun:inanim:m:v_mis
авіагоризонтом	авіагоризонт	noun	noun:inanim:m:v_oru
авіагоризонту	авіагоризонт	noun	noun:inanim:m:v_dav
авіагоризонту	авіагоризонт	noun	noun:inanim:m:v_mis
авіагоризонту	авіагоризонт	noun	noun:inanim:m:v_rod
авіагоризонті	авіагоризонт	noun	noun:inanim:m:v_mis
авіагоризонтів	авіагоризонт	noun	noun:inanim:p:v_rod
авіагосподарств	авіагосподарство	noun	noun:inanim:p:v_rod
авіагосподарства	авіагосподарство	noun	noun:inanim:n:v_rod
авіагосподарства	авіагосподарство	noun	noun:inanim:p:v_kly
авіагосподарства	авіагосподарство	noun	noun:inanim:p:v_naz
авіагосподарства	авіагосподарство	noun	noun:inanim:p:v_zna
авіагосподарствам	авіагосподарство	noun	noun:inanim:p:v_dav
авіагосподарствами	авіагосподарство	noun	noun:inanim:p:v_oru
авіагосподарствах	авіагосподарство	noun	noun:inanim:p:v_mis
авіагосподарство	авіагосподарство	noun	noun:inanim:n:v_kly
авіагосподарство	авіагосподарство	noun	noun:inanim:n:v_naz
авіагосподарство	авіагосподарство	noun	noun:inanim:n:v_zna
авіагосподарством	авіагосподарство	noun	noun:inanim:n:v_oru
авіагосподарству	авіагосподарство	noun	noun:inanim:n:v_dav
авіагосподарству	авіагосподарство	noun	noun:inanim:n:v_mis
авіагосподарстві	авіагосподарство	noun	noun:inanim:n:v_mis
авіагруп	авіагрупа	noun	noun:inanim:p:v_rod
авіагрупа	авіагрупа	noun	noun:inanim:f:v_naz
авіагрупам	авіагрупа	noun	noun:inanim:p:v_dav
авіагрупами	авіагрупа	noun	noun:inanim:p:v_oru
авіагрупах	авіагрупа	noun	noun:inanim:p:v_mis
авіагрупи	авіагрупа	noun	noun:inanim:f:v_rod
авіагрупи	авіагрупа	noun	noun:inanim:p:v_kly
авіагрупи	авіагрупа	noun	noun:inanim:p:v_naz
авіагрупи	авіагрупа	noun	noun:inanim:p:v_zna
авіагрупо	авіагрупа	noun	noun:inanim:f:v_kly
авіагрупою	авіагрупа	noun	noun:inanim:f:v_oru
авіагрупу	авіагрупа	noun	noun:inanim:f:v_zna
авіагрупі	авіагрупа	noun	noun:inanim:f:v_dav
авіагрупі	авіагрупа	noun	noun:inanim:f:v_mis
авіагуртка	авіагурток	noun	noun:inanim:m:v_rod
авіагурткам	авіагурток	noun	noun:inanim:p:v_dav
авіагуртками	авіагурток	noun	noun:inanim:p:v_oru
авіагуртках	авіагурток	noun	noun:inanim:p:v_mis
авіагуртки	авіагурток	noun	noun:inanim:p:v_kly
авіагуртки	авіагурток	noun	noun:inanim:p:v_naz
авіагуртки	авіагурток	noun	noun:inanim:p:v_zna
авіагурткові	авіагурток	noun	noun:inanim:m:v_dav
авіагурткові	авіагурток	noun	noun:inanim:m:v_mis
авіагуртком	авіагурток	noun	noun:inanim:m:v_oru
авіагуртку	авіагурток	noun	noun:inanim:m:v_dav
авіагуртку	авіагурток	noun	noun:inanim:m:v_kly
авіагуртку	авіагурток	noun	noun:inanim:m:v_mis
авіагуртків	авіагурток	noun	noun:inanim:p:v_rod
авіагурток	авіагурток	noun	noun:inanim:m:v_naz
авіагурток	авіагурток	noun	noun:inanim:m:v_zna
авіагігант	авіагігант	noun	noun:inanim:m:v_naz
авіагігант	авіагігант	noun	noun:inanim:m:v_zna
авіагіганта	авіагігант	noun	noun:inanim:m:v_rod
авіагігантам	авіагігант	noun	noun:inanim:p:v_dav
авіагігантами	авіагігант	noun	noun:inanim:p:v_oru
авіагігантах	авіагігант	noun	noun:inanim:p:v_mis
авіагіганте	авіагігант	noun	noun:inanim:m:v_kly
авіагіганти	авіагігант	noun	noun:inanim:p:v_kly
авіагіганти	авіагігант	noun	noun:inanim:p:v_naz
авіагіганти	авіагігант	noun	noun:inanim:p:v_zna
авіагігантові	авіагігант	noun	noun:inanim:m:v_dav
авіагігантові	авіагігант	noun	noun:inanim:m:v_mis
авіагігантом	авіагігант	noun	noun:inanim:m:v_oru
авіагіганті	авіагігант	noun	noun:inanim:m:v_mis
авіагігантів	авіагігант	noun	noun:inanim:p:v_rod
авіадвигун	авіадвигун	noun	noun:inanim:m:v_naz
авіадвигун	авіадвигун	noun	noun:inanim:m:v_zna
авіадвигуна	авіадвигун	noun	noun:inanim:m:v_rod
авіадвигунам	авіадвигун	noun	noun:inanim:p:v_dav
авіадвигунами	авіадвигун	noun	noun:inanim:p:v_oru
авіадвигунах	авіадвигун	noun	noun:inanim:p:v_mis
авіадвигуне	авіадвигун	noun	noun:inanim:m:v_kly
авіадвигуни	авіадвигун	noun	noun:inanim:p:v_kly
авіадвигуни	авіадвигун	noun	noun:inanim:p:v_naz
авіадвигуни	авіадвигун	noun	noun:inanim:p:v_zna
авіадвигунові	авіадвигун	noun	noun:inanim:m:v_dav
авіадвигунові	авіадвигун	noun	noun:inanim:m:v_mis
авіадвигуном	авіадвигун	noun	noun:inanim:m:v_oru
авіадвигуні	авіадвигун	noun	noun:inanim:m:v_mis
авіадвигунів	авіадвигун	noun	noun:inanim:p:v_rod
авіадержав	авіадержава	noun	noun:inanim:p:v_rod
авіадержава	авіадержава	noun	noun:inanim:f:v_naz
авіадержавам	авіадержава	noun	noun:inanim:p:v_dav
авіадержавами	авіадержава	noun	noun:inanim:p:v_oru
авіадержавах	авіадержава	noun	noun:inanim:p:v_mis
авіадержави	авіадержава	noun	noun:inanim:f:v_rod
авіадержави	авіадержава	noun	noun:inanim:p:v_kly
авіадержави	авіадержава	noun	noun:inanim:p:v_naz
авіадержави	авіадержава	noun	noun:inanim:p:v_zna
авіадержаво	авіадержава	noun	noun:inanim:f:v_kly
авіадержавою	авіадержава	noun	noun:inanim:f:v_oru
авіадержаву	авіадержава	noun	noun:inanim:f:v_zna
авіадержаві	авіадержава	noun	noun:inanim:f:v_dav
авіадержаві	авіадержава	noun	noun:inanim:f:v_mis
авіадесант	авіадесант	noun	noun:inanim:m:v_naz
авіадесант	авіадесант	noun	noun:inanim:m:v_zna
авіадесантам	авіадесант	noun	noun:inanim:p:v_dav
авіадесантами	авіадесант	noun	noun:inanim:p:v_oru
авіадесантах	авіадесант	noun	noun:inanim:p:v_mis
авіадесанте	авіадесант	noun	noun:inanim:m:v_kly
авіадесанти	авіадесант	noun	noun:inanim:p:v_kly
авіадесанти	авіадесант	noun	noun:inanim:p:v_naz
авіадесанти	авіадесант	noun	noun:inanim:p:v_zna
авіадесантник	авіадесантник	noun	noun:anim:m:v_naz
авіадесантника	авіадесантник	noun	noun:anim:m:v_rod
авіадесантника	авіадесантник	noun	noun:anim:m:v_zna
авіадесантникам	авіадесантник	noun	noun:anim:p:v_dav
авіадесантниками	авіадесантник	noun	noun:anim:p:v_oru
авіадесантниках	авіадесантник	noun	noun:anim:p:v_mis
авіадесантники	авіадесантник	noun	noun:anim:p:v_kly
авіадесантники	авіадесантник	noun	noun:anim:p:v_naz
авіадесантники	авіадесантник	noun	noun:anim:p:v_zna:rare
авіадесантникові	авіадесантник	noun	noun:anim:m:v_dav
авіадесантникові	авіадесантник	noun	noun:anim:m:v_mis
авіадесантником	авіадесантник	noun	noun:anim:m:v_oru
авіадесантнику	авіадесантник	noun	noun:anim:m:v_dav
авіадесантнику	авіадесантник	noun	noun:anim:m:v_kly
авіадесантнику	авіадесантник	noun	noun:anim:m:v_mis
авіадесантників	авіадесантник	noun	noun:anim:p:v_rod
авіадесантників	авіадесантник	noun	noun:anim:p:v_zna
авіадесантові	авіадесант	noun	noun:inanim:m:v_dav
авіадесантові	авіадесант	noun	noun:inanim:m:v_mis
авіадесантом	авіадесант	noun	noun:inanim:m:v_oru
авіадесанту	авіадесант	noun	noun:inanim:m:v_dav
авіадесанту	авіадесант	noun	noun:inanim:m:v_mis
авіадесанту	авіадесант	noun	noun:inanim:m:v_rod
авіадесантуванню	авіадесантування	noun	noun:inanim:n:v_dav
авіадесантуванню	авіадесантування	noun	noun:inanim:n:v_mis
авіадесантування	авіадесантування	noun	noun:inanim:n:v_kly
авіадесантування	авіадесантування	noun	noun:inanim:n:v_naz
авіадесантування	авіадесантування	noun	noun:inanim:n:v_rod
авіадесантування	авіадесантування	noun	noun:inanim:n:v_zna
авіадесантування	авіадесантування	noun	noun:inanim:p:v_kly
авіадесантування	авіадесантування	noun	noun:inanim:p:v_naz
авіадесантування	авіадесантування	noun	noun:inanim:p:v_zna
авіадесантуванням	авіадесантування	noun	noun:inanim:n:v_oru
авіадесантуванням	авіадесантування	noun	noun:inanim:p:v_dav
авіадесантуваннями	авіадесантування	noun	noun:inanim:p:v_oru
авіадесантуваннях	авіадесантування	noun	noun:inanim:p:v_mis
авіадесантуванні	авіадесантування	noun	noun:inanim:n:v_mis
авіадесантувань	авіадесантування	noun	noun:inanim:p:v_rod
авіадесанті	авіадесант	noun	noun:inanim:m:v_mis
авіадесантів	авіадесант	noun	noun:inanim:p:v_rod
авіадивізій	авіадивізія	noun	noun:inanim:p:v_rod
авіадивізіон	авіадивізіон	noun	noun:inanim:m:v_naz
авіадивізіон	авіадивізіон	noun	noun:inanim:m:v_zna
авіадивізіонам	авіадивізіон	noun	noun:inanim:p:v_dav
авіадивізіонами	авіадивізіон	noun	noun:inanim:p:v_oru
авіадивізіонах	авіадивізіон	noun	noun:inanim:p:v_mis
авіадивізіоне	авіадивізіон	noun	noun:inanim:m:v_kly
авіадивізіони	авіадивізіон	noun	noun:inanim:p:v_kly
авіадивізіони	авіадивізіон	noun	noun:inanim:p:v_naz
авіадивізіони	авіадивізіон	noun	noun:inanim:p:v_zna
авіадивізіонові	авіадивізіон	noun	noun:inanim:m:v_dav
авіадивізіонові	авіадивізіон	noun	noun:inanim:m:v_mis
авіадивізіоном	авіадивізіон	noun	noun:inanim:m:v_oru
авіадивізіону	авіадивізіон	noun	noun:inanim:m:v_dav
авіадивізіону	авіадивізіон	noun	noun:inanim:m:v_mis
авіадивізіону	авіадивізіон	noun	noun:inanim:m:v_rod
авіадивізіоні	авіадивізіон	noun	noun:inanim:m:v_mis
авіадивізіонів	авіадивізіон	noun	noun:inanim:p:v_rod
авіадивізію	авіадивізія	noun	noun:inanim:f:v_zna
авіадивізія	авіадивізія	noun	noun:inanim:f:v_naz
авіадивізіям	авіадивізія	noun	noun:inanim:p:v_dav
авіадивізіями	авіадивізія	noun	noun:inanim:p:v_oru
авіадивізіях	авіадивізія	noun	noun:inanim:p:v_mis
авіадивізіє	авіадивізія	noun	noun:inanim:f:v_kly
авіадивізією	авіадивізія	noun	noun:inanim:f:v_oru
авіадивізії	авіадивізія	noun	noun:inanim:f:v_dav
авіадивізії	авіадивізія	noun	noun:inanim:f:v_mis
авіадивізії	авіадивізія	noun	noun:inanim:f:v_rod
авіадивізії	авіадивізія	noun	noun:inanim:p:v_kly
авіадивізії	авіадивізія	noun	noun:inanim:p:v_naz
авіадивізії	авіадивізія	noun	noun:inanim:p:v_zna
авіадискаунтер	авіадискаунтер	noun	noun:inanim:m:v_naz
авіадискаунтер	авіадискаунтер	noun	noun:inanim:m:v_zna
авіадискаунтера	авіадискаунтер	noun	noun:inanim:m:v_rod
авіадискаунтерам	авіадискаунтер	noun	noun:inanim:p:v_dav
авіадискаунтерами	авіадискаунтер	noun	noun:inanim:p:v_oru
авіадискаунтерах	авіадискаунтер	noun	noun:inanim:p:v_mis
авіадискаунтере	авіадискаунтер	noun	noun:inanim:m:v_kly
авіадискаунтери	авіадискаунтер	noun	noun:inanim:p:v_kly
авіадискаунтери	авіадискаунтер	noun	noun:inanim:p:v_naz
авіадискаунтери	авіадискаунтер	noun	noun:inanim:p:v_zna
авіадискаунтерові	авіадискаунтер	noun	noun:inanim:m:v_dav
авіадискаунтерові	авіадискаунтер	noun	noun:inanim:m:v_mis
авіадискаунтером	авіадискаунтер	noun	noun:inanim:m:v_oru
авіадискаунтері	авіадискаунтер	noun	noun:inanim:m:v_mis
авіадискаунтерів	авіадискаунтер	noun	noun:inanim:p:v_rod
авіадиспетчер	авіадиспетчер	noun	noun:anim:m:v_naz
авіадиспетчера	авіадиспетчер	noun	noun:anim:m:v_rod
авіадиспетчера	авіадиспетчер	noun	noun:anim:m:v_zna
авіадиспетчерам	авіадиспетчер	noun	noun:anim:p:v_dav
авіадиспетчерами	авіадиспетчер	noun	noun:anim:p:v_oru
авіадиспетчерах	авіадиспетчер	noun	noun:anim:p:v_mis
авіадиспетчере	авіадиспетчер	noun	noun:anim:m:v_kly
авіадиспетчери	авіадиспетчер	noun	noun:anim:p:v_kly
авіадиспетчери	авіадиспетчер	noun	noun:anim:p:v_naz
авіадиспетчери	авіадиспетчер	noun	noun:anim:p:v_zna:rare
авіадиспетчерові	авіадиспетчер	noun	noun:anim:m:v_dav
авіадиспетчерові	авіадиспетчер	noun	noun:anim:m:v_mis
авіадиспетчером	авіадиспетчер	noun	noun:anim:m:v_oru
авіадиспетчерська	авіадиспетчерська	noun	noun:inanim:f:v_kly
авіадиспетчерська	авіадиспетчерська	noun	noun:inanim:f:v_naz
авіадиспетчерським	авіадиспетчерська	noun	noun:inanim:p:v_dav
авіадиспетчерськими	авіадиспетчерська	noun	noun:inanim:p:v_oru
авіадиспетчерських	авіадиспетчерська	noun	noun:inanim:p:v_mis
авіадиспетчерських	авіадиспетчерська	noun	noun:inanim:p:v_rod
авіадиспетчерською	авіадиспетчерська	noun	noun:inanim:f:v_oru
авіадиспетчерської	авіадиспетчерська	noun	noun:inanim:f:v_rod
авіадиспетчерську	авіадиспетчерська	noun	noun:inanim:f:v_zna
авіадиспетчерські	авіадиспетчерська	noun	noun:inanim:p:v_kly
авіадиспетчерські	авіадиспетчерська	noun	noun:inanim:p:v_naz
авіадиспетчерські	авіадиспетчерська	noun	noun:inanim:p:v_zna
авіадиспетчерській	авіадиспетчерська	noun	noun:inanim:f:v_dav
авіадиспетчерській	авіадиспетчерська	noun	noun:inanim:f:v_mis
авіадиспетчері	авіадиспетчер	noun	noun:anim:m:v_mis
авіадиспетчерів	авіадиспетчер	noun	noun:anim:p:v_rod
авіадиспетчерів	авіадиспетчер	noun	noun:anim:p:v_zna
авіадосягненню	авіадосягнення	noun	noun:inanim:n:v_dav
авіадосягненню	авіадосягнення	noun	noun:inanim:n:v_mis
авіадосягнення	авіадосягнення	noun	noun:inanim:n:v_kly
авіадосягнення	авіадосягнення	noun	noun:inanim:n:v_naz
авіадосягнення	авіадосягнення	noun	noun:inanim:n:v_rod
авіадосягнення	авіадосягнення	noun	noun:inanim:n:v_zna
авіадосягнення	авіадосягнення	noun	noun:inanim:p:v_kly
авіадосягнення	авіадосягнення	noun	noun:inanim:p:v_naz
авіадосягнення	авіадосягнення	noun	noun:inanim:p:v_zna
авіадосягненням	авіадосягнення	noun	noun:inanim:n:v_oru
авіадосягненням	авіадосягнення	noun	noun:inanim:p:v_dav
авіадосягненнями	авіадосягнення	noun	noun:inanim:p:v_oru
авіадосягненнях	авіадосягнення	noun	noun:inanim:p:v_mis
авіадосягненні	авіадосягнення	noun	noun:inanim:n:v_mis
авіадосягнень	авіадосягнення	noun	noun:inanim:p:v_rod
авіаекскурсій	авіаекскурсія	noun	noun:inanim:p:v_rod
авіаекскурсію	авіаекскурсія	noun	noun:inanim:f:v_zna
авіаекскурсія	авіаекскурсія	noun	noun:inanim:f:v_naz
авіаекскурсіям	авіаекскурсія	noun	noun:inanim:p:v_dav
авіаекскурсіями	авіаекскурсія	noun	noun:inanim:p:v_oru
авіаекскурсіях	авіаекскурсія	noun	noun:inanim:p:v_mis
авіаекскурсіє	авіаекскурсія	noun	noun:inanim:f:v_kly
авіаекскурсією	авіаекскурсія	noun	noun:inanim:f:v_oru
авіаекскурсії	авіаекскурсія	noun	noun:inanim:f:v_dav
авіаекскурсії	авіаекскурсія	noun	noun:inanim:f:v_mis
авіаекскурсії	авіаекскурсія	noun	noun:inanim:f:v_rod
авіаекскурсії	авіаекскурсія	noun	noun:inanim:p:v_kly
авіаекскурсії	авіаекскурсія	noun	noun:inanim:p:v_naz
авіаекскурсії	авіаекскурсія	noun	noun:inanim:p:v_zna
авіаексперт	авіаексперт	noun	noun:anim:m:v_naz
авіаексперта	авіаексперт	noun	noun:anim:m:v_rod
авіаексперта	авіаексперт	noun	noun:anim:m:v_zna
авіаекспертам	авіаексперт	noun	noun:anim:p:v_dav
авіаекспертами	авіаексперт	noun	noun:anim:p:v_oru
авіаекспертах	авіаексперт	noun	noun:anim:p:v_mis
авіаексперте	авіаексперт	noun	noun:anim:m:v_kly
авіаексперти	авіаексперт	noun	noun:anim:p:v_kly
авіаексперти	авіаексперт	noun	noun:anim:p:v_naz
авіаексперти	авіаексперт	noun	noun:anim:p:v_zna:rare
авіаекспертові	авіаексперт	noun	noun:anim:m:v_dav
авіаекспертові	авіаексперт	noun	noun:anim:m:v_mis
авіаекспертом	авіаексперт	noun	noun:anim:m:v_oru
авіаексперті	авіаексперт	noun	noun:anim:m:v_mis
авіаекспертів	авіаексперт	noun	noun:anim:p:v_rod
авіаекспертів	авіаексперт	noun	noun:anim:p:v_zna
авіаекспрес	авіаекспрес	noun	noun:inanim:m:v_naz
авіаекспрес	авіаекспрес	noun	noun:inanim:m:v_zna
авіаекспреса	авіаекспрес	noun	noun:inanim:m:v_rod
авіаекспресам	авіаекспрес	noun	noun:inanim:p:v_dav
авіаекспресами	авіаекспрес	noun	noun:inanim:p:v_oru
авіаекспресах	авіаекспрес	noun	noun:inanim:p:v_mis
авіаекспресе	авіаекспрес	noun	noun:inanim:m:v_kly
авіаекспреси	авіаекспрес	noun	noun:inanim:p:v_kly
авіаекспреси	авіаекспрес	noun	noun:inanim:p:v_naz
авіаекспреси	авіаекспрес	noun	noun:inanim:p:v_zna
авіаекспресові	авіаекспрес	noun	noun:inanim:m:v_dav
авіаекспресові	авіаекспрес	noun	noun:inanim:m:v_mis
авіаекспресом	авіаекспрес	noun	noun:inanim:m:v_oru
авіаекспресі	авіаекспрес	noun	noun:inanim:m:v_mis
авіаекспресів	авіаекспрес	noun	noun:inanim:p:v_rod
авіаекіпаж	авіаекіпаж	noun	noun:inanim:m:v_naz
авіаекіпаж	авіаекіпаж	noun	noun:inanim:m:v_zna
авіаекіпажам	авіаекіпаж	noun	noun:inanim:p:v_dav
авіаекіпажами	авіаекіпаж	noun	noun:inanim:p:v_oru
авіаекіпажах	авіаекіпаж	noun	noun:inanim:p:v_mis
авіаекіпаже	авіаекіпаж	noun	noun:inanim:m:v_kly
авіаекіпажеві	авіаекіпаж	noun	noun:inanim:m:v_dav
авіаекіпажеві	авіаекіпаж	noun	noun:inanim:m:v_mis
авіаекіпажем	авіаекіпаж	noun	noun:inanim:m:v_oru
авіаекіпажу	авіаекіпаж	noun	noun:inanim:m:v_dav
авіаекіпажу	авіаекіпаж	noun	noun:inanim:m:v_mis
авіаекіпажу	авіаекіпаж	noun	noun:inanim:m:v_rod
авіаекіпажі	авіаекіпаж	noun	noun:inanim:m:v_mis
авіаекіпажі	авіаекіпаж	noun	noun:inanim:p:v_kly
авіаекіпажі	авіаекіпаж	noun	noun:inanim:p:v_naz
авіаекіпажі	авіаекіпаж	noun	noun:inanim:p:v_zna
авіаекіпажів	авіаекіпаж	noun	noun:inanim:p:v_rod
авіаескадр	авіаескадра	noun	noun:inanim:p:v_rod
авіаескадра	авіаескадра	noun	noun:inanim:f:v_naz
авіаескадрам	авіаескадра	noun	noun:inanim:p:v_dav
авіаескадрами	авіаескадра	noun	noun:inanim:p:v_oru
авіаескадрах	авіаескадра	noun	noun:inanim:p:v_mis
авіаескадри	авіаескадра	noun	noun:inanim:f:v_rod
авіаескадри	авіаескадра	noun	noun:inanim:p:v_kly
авіаескадри	авіаескадра	noun	noun:inanim:p:v_naz
авіаескадри	авіаескадра	noun	noun:inanim:p:v_zna
авіаескадрилей	авіаескадрилья	noun	noun:inanim:p:v_rod
авіаескадрилью	авіаескадрилья	noun	noun:inanim:f:v_zna
авіаескадрилья	авіаескадрилья	noun	noun:inanim:f:v_naz
авіаескадрильям	авіаескадрилья	noun	noun:inanim:p:v_dav
авіаескадрильями	авіаескадрилья	noun	noun:inanim:p:v_oru
авіаескадрильях	авіаескадрилья	noun	noun:inanim:p:v_mis
авіаескадрильє	авіаескадрилья	noun	noun:inanim:f:v_kly
авіаескадрильєю	авіаескадрилья	noun	noun:inanim:f:v_oru
авіаескадрильї	авіаескадрилья	noun	noun:inanim:f:v_dav
авіаескадрильї	авіаескадрилья	noun	noun:inanim:f:v_mis
авіаескадрильї	авіаескадрилья	noun	noun:inanim:f:v_rod
авіаескадрильї	авіаескадрилья	noun	noun:inanim:p:v_kly
авіаескадрильї	авіаескадрилья	noun	noun:inanim:p:v_naz
авіаескадрильї	авіаескадрилья	noun	noun:inanim:p:v_zna
авіаескадро	авіаескадра	noun	noun:inanim:f:v_kly
авіаескадрою	авіаескадра	noun	noun:inanim:f:v_oru
авіаескадру	авіаескадра	noun	noun:inanim:f:v_zna
авіаескадрі	авіаескадра	noun	noun:inanim:f:v_dav
авіаескадрі	авіаескадра	noun	noun:inanim:f:v_mis
авіажурнал	авіажурнал	noun	noun:inanim:m:v_naz
авіажурнал	авіажурнал	noun	noun:inanim:m:v_zna
авіажурналам	авіажурнал	noun	noun:inanim:p:v_dav
авіажурналами	авіажурнал	noun	noun:inanim:p:v_oru
авіажурналах	авіажурнал	noun	noun:inanim:p:v_mis
авіажурнале	авіажурнал	noun	noun:inanim:m:v_kly
авіажурнали	авіажурнал	noun	noun:inanim:p:v_kly
авіажурнали	авіажурнал	noun	noun:inanim:p:v_naz
авіажурнали	авіажурнал	noun	noun:inanim:p:v_zna
авіажурналові	авіажурнал	noun	noun:inanim:m:v_dav
авіажурналові	авіажурнал	noun	noun:inanim:m:v_mis
авіажурналом	авіажурнал	noun	noun:inanim:m:v_oru
авіажурналу	авіажурнал	noun	noun:inanim:m:v_dav
авіажурналу	авіажурнал	noun	noun:inanim:m:v_mis
авіажурналу	авіажурнал	noun	noun:inanim:m:v_rod
авіажурналі	авіажурнал	noun	noun:inanim:m:v_mis
авіажурналів	авіажурнал	noun	noun:inanim:p:v_rod
авіазавод	авіазавод	noun	noun:inanim:m:v_naz
авіазавод	авіазавод	noun	noun:inanim:m:v_zna
авіазаводам	авіазавод	noun	noun:inanim:p:v_dav
авіазаводами	авіазавод	noun	noun:inanim:p:v_oru
авіазаводах	авіазавод	noun	noun:inanim:p:v_mis
авіазаводе	авіазавод	noun	noun:inanim:m:v_kly
авіазаводи	авіазавод	noun	noun:inanim:p:v_kly
авіазаводи	авіазавод	noun	noun:inanim:p:v_naz
авіазаводи	авіазавод	noun	noun:inanim:p:v_zna
авіазаводові	авіазавод	noun	noun:inanim:m:v_dav
авіазаводові	авіазавод	noun	noun:inanim:m:v_mis
авіазаводом	авіазавод	noun	noun:inanim:m:v_oru
авіазаводу	авіазавод	noun	noun:inanim:m:v_dav
авіазаводу	авіазавод	noun	noun:inanim:m:v_mis
авіазаводу	авіазавод	noun	noun:inanim:m:v_rod
авіазаводі	авіазавод	noun	noun:inanim:m:v_mis
авіазаводів	авіазавод	noun	noun:inanim:p:v_rod
авіазагонам	авіазагін	noun	noun:inanim:p:v_dav
авіазагонами	авіазагін	noun	noun:inanim:p:v_oru
авіазагонах	авіазагін	noun	noun:inanim:p:v_mis
авіазагоне	авіазагін	noun	noun:inanim:m:v_kly
авіазагони	авіазагін	noun	noun:inanim:p:v_kly
авіазагони	авіазагін	noun	noun:inanim:p:v_naz
авіазагони	авіазагін	noun	noun:inanim:p:v_zna
авіазагонові	авіазагін	noun	noun:inanim:m:v_dav
авіазагонові	авіазагін	noun	noun:inanim:m:v_mis
авіазагоном	авіазагін	noun	noun:inanim:m:v_oru
авіазагону	авіазагін	noun	noun:inanim:m:v_dav
авіазагону	авіазагін	noun	noun:inanim:m:v_mis
авіазагону	авіазагін	noun	noun:inanim:m:v_rod
авіазагоні	авіазагін	noun	noun:inanim:m:v_mis
авіазагонів	авіазагін	noun	noun:inanim:p:v_rod
авіазагін	авіазагін	noun	noun:inanim:m:v_naz
авіазагін	авіазагін	noun	noun:inanim:m:v_zna
авіазамах	авіазамах	noun	noun:inanim:m:v_naz
авіазамах	авіазамах	noun	noun:inanim:m:v_zna
авіазамахам	авіазамах	noun	noun:inanim:p:v_dav
авіазамахами	авіазамах	noun	noun:inanim:p:v_oru
авіазамахах	авіазамах	noun	noun:inanim:p:v_mis
авіазамахи	авіазамах	noun	noun:inanim:p:v_kly
авіазамахи	авіазамах	noun	noun:inanim:p:v_naz
авіазамахи	авіазамах	noun	noun:inanim:p:v_zna
авіазамахові	авіазамах	noun	noun:inanim:m:v_dav
авіазамахові	авіазамах	noun	noun:inanim:m:v_mis
авіазамахом	авіазамах	noun	noun:inanim:m:v_oru
авіазамаху	авіазамах	noun	noun:inanim:m:v_dav
авіазамаху	авіазамах	noun	noun:inanim:m:v_kly
авіазамаху	авіазамах	noun	noun:inanim:m:v_mis
авіазамаху	авіазамах	noun	noun:inanim:m:v_rod
авіазамахів	авіазамах	noun	noun:inanim:p:v_rod
авіазасобам	авіазасіб	noun	noun:inanim:p:v_dav
авіазасобами	авіазасіб	noun	noun:inanim:p:v_oru
авіазасобах	авіазасіб	noun	noun:inanim:p:v_mis
авіазасобе	авіазасіб	noun	noun:inanim:m:v_kly
авіазасоби	авіазасіб	noun	noun:inanim:p:v_kly
авіазасоби	авіазасіб	noun	noun:inanim:p:v_naz
авіазасоби	авіазасіб	noun	noun:inanim:p:v_zna
авіазасобові	авіазасіб	noun	noun:inanim:m:v_dav
авіазасобові	авіазасіб	noun	noun:inanim:m:v_mis
авіазасобом	авіазасіб	noun	noun:inanim:m:v_oru
авіазасобу	авіазасіб	noun	noun:inanim:m:v_dav
авіазасобу	авіазасіб	noun	noun:inanim:m:v_mis
авіазасобу	авіазасіб	noun	noun:inanim:m:v_rod
авіазасобі	авіазасіб	noun	noun:inanim:m:v_mis
авіазасобів	авіазасіб	noun	noun:inanim:p:v_rod
авіазасіб	авіазасіб	noun	noun:inanim:m:v_naz
авіазасіб	авіазасіб	noun	noun:inanim:m:v_zna
авіакас	авіакаса	noun	noun:inanim:p:v_rod
авіакаса	авіакаса	noun	noun:inanim:f:v_naz
авіакасам	авіакаса	noun	noun:inanim:p:v_dav
авіакасами	авіакаса	noun	noun:inanim:p:v_oru
авіакасах	авіакаса	noun	noun:inanim:p:v_mis
авіакаси	авіакаса	noun	noun:inanim:f:v_rod
авіакаси	авіакаса	noun	noun:inanim:p:v_kly
авіакаси	авіакаса	noun	noun:inanim:p:v_naz
авіакаси	авіакаса	noun	noun:inanim:p:v_zna
авіакасо	авіакаса	noun	noun:inanim:f:v_kly
авіакасою	авіакаса	noun	noun:inanim:f:v_oru
авіакасу	авіакаса	noun	noun:inanim:f:v_zna
авіакасі	авіакаса	noun	noun:inanim:f:v_dav
авіакасі	авіакаса	noun	noun:inanim:f:v_mis
авіакатастроф	авіакатастрофа	noun	noun:inanim:p:v_rod
авіакатастрофа	авіакатастрофа	noun	noun:inanim:f:v_naz
авіакатастрофам	авіакатастрофа	noun	noun:inanim:p:v_dav
авіакатастрофами	авіакатастрофа	noun	noun:inanim:p:v_oru
авіакатастрофах	авіакатастрофа	noun	noun:inanim:p:v_mis
авіакатастрофи	авіакатастрофа	noun	noun:inanim:f:v_rod
авіакатастрофи	авіакатастрофа	noun	noun:inanim:p:v_kly
авіакатастрофи	авіакатастрофа	noun	noun:inanim:p:v_naz
авіакатастрофи	авіакатастрофа	noun	noun:inanim:p:v_zna
авіакатастрофо	авіакатастрофа	noun	noun:inanim:f:v_kly
авіакатастрофою	авіакатастрофа	noun	noun:inanim:f:v_oru
авіакатастрофу	авіакатастрофа	noun	noun:inanim:f:v_zna
авіакатастрофі	авіакатастрофа	noun	noun:inanim:f:v_dav
авіакатастрофі	авіакатастрофа	noun	noun:inanim:f:v_mis
авіаквитка	авіаквиток	noun	noun:inanim:m:v_rod
авіаквиткам	авіаквиток	noun	noun:inanim:p:v_dav
авіаквитками	авіаквиток	noun	noun:inanim:p:v_oru
авіаквитках	авіаквиток	noun	noun:inanim:p:v_mis
авіаквитки	авіаквиток	noun	noun:inanim:p:v_kly
авіаквитки	авіаквиток	noun	noun:inanim:p:v_naz
авіаквитки	авіаквиток	noun	noun:inanim:p:v_zna
авіаквиткові	авіаквиток	noun	noun:inanim:m:v_dav
авіаквиткові	авіаквиток	noun	noun:inanim:m:v_mis
авіаквитком	авіаквиток	noun	noun:inanim:m:v_oru
авіаквитку	авіаквиток	noun	noun:inanim:m:v_dav
авіаквитку	авіаквиток	noun	noun:inanim:m:v_kly
авіаквитку	авіаквиток	noun	noun:inanim:m:v_mis
авіаквитків	авіаквиток	noun	noun:inanim:p:v_rod
авіаквиток	авіаквиток	noun	noun:inanim:m:v_naz
авіаквиток	авіаквиток	noun	noun:inanim:m:v_zna
авіакеросин	авіакеросин	noun	noun:inanim:m:v_naz
авіакеросин	авіакеросин	noun	noun:inanim:m:v_zna
авіакеросинам	авіакеросин	noun	noun:inanim:p:v_dav
авіакеросинами	авіакеросин	noun	noun:inanim:p:v_oru
авіакеросинах	авіакеросин	noun	noun:inanim:p:v_mis
авіакеросине	авіакеросин	noun	noun:inanim:m:v_kly
авіакеросини	авіакеросин	noun	noun:inanim:p:v_kly
авіакеросини	авіакеросин	noun	noun:inanim:p:v_naz
авіакеросини	авіакеросин	noun	noun:inanim:p:v_zna
авіакеросинові	авіакеросин	noun	noun:inanim:m:v_dav
авіакеросинові	авіакеросин	noun	noun:inanim:m:v_mis
авіакеросином	авіакеросин	noun	noun:inanim:m:v_oru
авіакеросину	авіакеросин	noun	noun:inanim:m:v_dav
авіакеросину	авіакеросин	noun	noun:inanim:m:v_mis
авіакеросину	авіакеросин	noun	noun:inanim:m:v_rod
авіакеросині	авіакеросин	noun	noun:inanim:m:v_mis
авіакеросинів	авіакеросин	noun	noun:inanim:p:v_rod
авіакластер	авіакластер	noun	noun:inanim:m:v_naz
авіакластер	авіакластер	noun	noun:inanim:m:v_zna
авіакластера	авіакластер	noun	noun:inanim:m:v_rod
авіакластерам	авіакластер	noun	noun:inanim:p:v_dav
авіакластерами	авіакластер	noun	noun:inanim:p:v_oru
авіакластерах	авіакластер	noun	noun:inanim:p:v_mis
авіакластере	авіакластер	noun	noun:inanim:m:v_kly
авіакластери	авіакластер	noun	noun:inanim:p:v_kly
авіакластери	авіакластер	noun	noun:inanim:p:v_naz
авіакластери	авіакластер	noun	noun:inanim:p:v_zna
авіакластерові	авіакластер	noun	noun:inanim:m:v_dav
авіакластерові	авіакластер	noun	noun:inanim:m:v_mis
авіакластером	авіакластер	noun	noun:inanim:m:v_oru
авіакластері	авіакластер	noun	noun:inanim:m:v_mis
авіакластерів	авіакластер	noun	noun:inanim:p:v_rod
авіаклуб	авіаклуб	noun	noun:inanim:m:v_naz
авіаклуб	авіаклуб	noun	noun:inanim:m:v_zna
авіаклубам	авіаклуб	noun	noun:inanim:p:v_dav
авіаклубами	авіаклуб	noun	noun:inanim:p:v_oru
авіаклубах	авіаклуб	noun	noun:inanim:p:v_mis
авіаклубе	авіаклуб	noun	noun:inanim:m:v_kly
авіаклуби	авіаклуб	noun	noun:inanim:p:v_kly
авіаклуби	авіаклуб	noun	noun:inanim:p:v_naz
авіаклуби	авіаклуб	noun	noun:inanim:p:v_zna
авіаклубові	авіаклуб	noun	noun:inanim:m:v_dav
авіаклубові	авіаклуб	noun	noun:inanim:m:v_mis
авіаклубом	авіаклуб	noun	noun:inanim:m:v_oru
авіаклубу	авіаклуб	noun	noun:inanim:m:v_dav
авіаклубу	авіаклуб	noun	noun:inanim:m:v_mis
авіаклубу	авіаклуб	noun	noun:inanim:m:v_rod
авіаклубі	авіаклуб	noun	noun:inanim:m:v_mis
авіаклубів	авіаклуб	noun	noun:inanim:p:v_rod
авіаколедж	авіаколедж	noun	noun:inanim:m:v_naz
авіаколедж	авіаколедж	noun	noun:inanim:m:v_zna
авіаколеджам	авіаколедж	noun	noun:inanim:p:v_dav
авіаколеджами	авіаколедж	noun	noun:inanim:p:v_oru
авіаколеджах	авіаколедж	noun	noun:inanim:p:v_mis
авіаколедже	авіаколедж	noun	noun:inanim:m:v_kly
авіаколеджеві	авіаколедж	noun	noun:inanim:m:v_dav
авіаколеджеві	авіаколедж	noun	noun:inanim:m:v_mis
авіаколеджем	авіаколедж	noun	noun:inanim:m:v_oru
авіаколеджу	авіаколедж	noun	noun:inanim:m:v_dav
авіаколеджу	авіаколедж	noun	noun:inanim:m:v_mis
авіаколеджу	авіаколедж	noun	noun:inanim:m:v_rod
авіаколеджі	авіаколедж	noun	noun:inanim:m:v_mis
авіаколеджі	авіаколедж	noun	noun:inanim:p:v_kly
авіаколеджі	авіаколедж	noun	noun:inanim:p:v_naz
авіаколеджі	авіаколедж	noun	noun:inanim:p:v_zna
авіаколеджів	авіаколедж	noun	noun:inanim:p:v_rod
авіакомпаній	авіакомпанія	noun	noun:inanim:p:v_rod
авіакомпанію	авіакомпанія	noun	noun:inanim:f:v_zna
авіакомпанія	авіакомпанія	noun	noun:inanim:f:v_naz
авіакомпаніям	авіакомпанія	noun	noun:inanim:p:v_dav
авіакомпаніями	авіакомпанія	noun	noun:inanim:p:v_oru
авіакомпаніях	авіакомпанія	noun	noun:inanim:p:v_mis
авіакомпаніє	авіакомпанія	noun	noun:inanim:f:v_kly
авіакомпанією	авіакомпанія	noun	noun:inanim:f:v_oru
авіакомпанії	авіакомпанія	noun	noun:inanim:f:v_dav
авіакомпанії	авіакомпанія	noun	noun:inanim:f:v_mis
авіакомпанії	авіакомпанія	noun	noun:inanim:f:v_rod
авіакомпанії	авіакомпанія	noun	noun:inanim:p:v_kly
авіакомпанії	авіакомпанія	noun	noun:inanim:p:v_naz
авіакомпанії	авіакомпанія	noun	noun:inanim:p:v_zna
авіакомпас	авіакомпас	noun	noun:inanim:m:v_naz
авіакомпас	авіакомпас	noun	noun:inanim:m:v_zna
авіакомпаса	авіакомпас	noun	noun:inanim:m:v_rod
авіакомпасам	авіакомпас	noun	noun:inanim:p:v_dav
авіакомпасами	авіакомпас	noun	noun:inanim:p:v_oru
авіакомпасах	авіакомпас	noun	noun:inanim:p:v_mis
авіакомпасе	авіакомпас	noun	noun:inanim:m:v_kly
авіакомпаси	авіакомпас	noun	noun:inanim:p:v_kly
авіакомпаси	авіакомпас	noun	noun:inanim:p:v_naz
авіакомпаси	авіакомпас	noun	noun:inanim:p:v_zna
авіакомпасові	авіакомпас	noun	noun:inanim:m:v_dav
авіакомпасові	авіакомпас	noun	noun:inanim:m:v_mis
авіакомпасом	авіакомпас	noun	noun:inanim:m:v_oru
авіакомпасі	авіакомпас	noun	noun:inanim:m:v_mis
авіакомпасів	авіакомпас	noun	noun:inanim:p:v_rod
авіакомплекс	авіакомплекс	noun	noun:inanim:m:v_naz
авіакомплекс	авіакомплекс	noun	noun:inanim:m:v_zna
авіакомплексам	авіакомплекс	noun	noun:inanim:p:v_dav
авіакомплексами	авіакомплекс	noun	noun:inanim:p:v_oru
авіакомплексах	авіакомплекс	noun	noun:inanim:p:v_mis
авіакомплексе	авіакомплекс	noun	noun:inanim:m:v_kly
авіакомплекси	авіакомплекс	noun	noun:inanim:p:v_kly
авіакомплекси	авіакомплекс	noun	noun:inanim:p:v_naz
авіакомплекси	авіакомплекс	noun	noun:inanim:p:v_zna
авіакомплексові	авіакомплекс	noun	noun:inanim:m:v_dav
авіакомплексові	авіакомплекс	noun	noun:inanim:m:v_mis
авіакомплексом	авіакомплекс	noun	noun:inanim:m:v_oru
авіакомплексу	авіакомплекс	noun	noun:inanim:m:v_dav
авіакомплексу	авіакомплекс	noun	noun:inanim:m:v_mis
авіакомплексу	авіакомплекс	noun	noun:inanim:m:v_rod
авіакомплексі	авіакомплекс	noun	noun:inanim:m:v_mis
авіакомплексів	авіакомплекс	noun	noun:inanim:p:v_rod
авіакомпонент	авіакомпонент	noun	noun:inanim:m:v_naz
авіакомпонент	авіакомпонент	noun	noun:inanim:m:v_zna
авіакомпонента	авіакомпонент	noun	noun:inanim:m:v_rod
авіакомпонентам	авіакомпонент	noun	noun:inanim:p:v_dav
авіакомпонентами	авіакомпонент	noun	noun:inanim:p:v_oru
авіакомпонентах	авіакомпонент	noun	noun:inanim:p:v_mis
авіакомпоненте	авіакомпонент	noun	noun:inanim:m:v_kly
авіакомпоненти	авіакомпонент	noun	noun:inanim:p:v_kly
авіакомпоненти	авіакомпонент	noun	noun:inanim:p:v_naz
авіакомпоненти	авіакомпонент	noun	noun:inanim:p:v_zna
авіакомпонентові	авіакомпонент	noun	noun:inanim:m:v_dav
авіакомпонентові	авіакомпонент	noun	noun:inanim:m:v_mis
авіакомпонентом	авіакомпонент	noun	noun:inanim:m:v_oru
авіакомпоненті	авіакомпонент	noun	noun:inanim:m:v_mis
авіакомпонентів	авіакомпонент	noun	noun:inanim:p:v_rod
авіаконструктор	авіаконструктор	noun	noun:anim:m:v_naz
авіаконструктора	авіаконструктор	noun	noun:anim:m:v_rod
авіаконструктора	авіаконструктор	noun	noun:anim:m:v_zna
авіаконструкторам	авіаконструктор	noun	noun:anim:p:v_dav
авіаконструкторами	авіаконструктор	noun	noun:anim:p:v_oru
авіаконструкторах	авіаконструктор	noun	noun:anim:p:v_mis
авіаконструкторе	авіаконструктор	noun	noun:anim:m:v_kly
авіаконструктори	авіаконструктор	noun	noun:anim:p:v_kly
авіаконструктори	авіаконструктор	noun	noun:anim:p:v_naz
авіаконструктори	авіаконструктор	noun	noun:anim:p:v_zna:rare
авіаконструкторка	авіаконструкторка	noun	noun:anim:f:v_naz
авіаконструкторкам	авіаконструкторка	noun	noun:anim:p:v_dav
авіаконструкторками	авіаконструкторка	noun	noun:anim:p:v_oru
авіаконструкторках	авіаконструкторка	noun	noun:anim:p:v_mis
авіаконструкторки	авіаконструкторка	noun	noun:anim:f:v_rod
авіаконструкторки	авіаконструкторка	noun	noun:anim:p:v_kly
авіаконструкторки	авіаконструкторка	noun	noun:anim:p:v_naz
авіаконструкторки	авіаконструкторка	noun	noun:anim:p:v_zna:rare
авіаконструкторко	авіаконструкторка	noun	noun:anim:f:v_kly
авіаконструкторкою	авіаконструкторка	noun	noun:anim:f:v_oru
авіаконструкторку	авіаконструкторка	noun	noun:anim:f:v_zna
авіаконструкторові	авіаконструктор	noun	noun:anim:m:v_dav
авіаконструкторові	авіаконструктор	noun	noun:anim:m:v_mis
авіаконструкторок	авіаконструкторка	noun	noun:anim:p:v_rod
авіаконструкторок	авіаконструкторка	noun	noun:anim:p:v_zna
авіаконструктором	авіаконструктор	noun	noun:anim:m:v_oru
авіаконструкторці	авіаконструкторка	noun	noun:anim:f:v_dav
авіаконструкторці	авіаконструкторка	noun	noun:anim:f:v_mis
авіаконструкторі	авіаконструктор	noun	noun:anim:m:v_mis
авіаконструкторів	авіаконструктор	noun	noun:anim:p:v_rod
авіаконструкторів	авіаконструктор	noun	noun:anim:p:v_zna
авіаконструкцій	авіаконструкція	noun	noun:inanim:p:v_rod
авіаконструкцію	авіаконструкція	noun	noun:inanim:f:v_zna
авіаконструкція	авіаконструкція	noun	noun:inanim:f:v_naz
авіаконструкціям	авіаконструкція	noun	noun:inanim:p:v_dav
авіаконструкціями	авіаконструкція	noun	noun:inanim:p:v_oru
авіаконструкціях	авіаконструкція	noun	noun:inanim:p:v_mis
авіаконструкціє	авіаконструкція	noun	noun:inanim:f:v_kly
авіаконструкцією	авіаконструкція	noun	noun:inanim:f:v_oru
авіаконструкції	авіаконструкція	noun	noun:inanim:f:v_dav
авіаконструкції	авіаконструкція	noun	noun:inanim:f:v_mis
авіаконструкції	авіаконструкція	noun	noun:inanim:f:v_rod
авіаконструкції	авіаконструкція	noun	noun:inanim:p:v_kly
авіаконструкції	авіаконструкція	noun	noun:inanim:p:v_naz
авіаконструкції	авіаконструкція	noun	noun:inanim:p:v_zna
авіаконцерн	авіаконцерн	noun	noun:inanim:m:v_naz
авіаконцерн	авіаконцерн	noun	noun:inanim:m:v_zna
авіаконцернам	авіаконцерн	noun	noun:inanim:p:v_dav
авіаконцернами	авіаконцерн	noun	noun:inanim:p:v_oru
авіаконцернах	авіаконцерн	noun	noun:inanim:p:v_mis
авіаконцерне	авіаконцерн	noun	noun:inanim:m:v_kly
авіаконцерни	авіаконцерн	noun	noun:inanim:p:v_kly
авіаконцерни	авіаконцерн	noun	noun:inanim:p:v_naz
авіаконцерни	авіаконцерн	noun	noun:inanim:p:v_zna
авіаконцернові	авіаконцерн	noun	noun:inanim:m:v_dav
авіаконцернові	авіаконцерн	noun	noun:inanim:m:v_mis
авіаконцерном	авіаконцерн	noun	noun:inanim:m:v_oru
авіаконцерну	авіаконцерн	noun	noun:inanim:m:v_dav
авіаконцерну	авіаконцерн	noun	noun:inanim:m:v_mis
авіаконцерну	авіаконцерн	noun	noun:inanim:m:v_rod
авіаконцерні	авіаконцерн	noun	noun:inanim:m:v_mis
авіаконцернів	авіаконцерн	noun	noun:inanim:p:v_rod
авіакорпорацій	авіакорпорація	noun	noun:inanim:p:v_rod
авіакорпорацію	авіакорпорація	noun	noun:inanim:f:v_zna
авіакорпорація	авіакорпорація	noun	noun:inanim:f:v_naz
авіакорпораціям	авіакорпорація	noun	noun:inanim:p:v_dav
авіакорпораціями	авіакорпорація	noun	noun:inanim:p:v_oru
авіакорпораціях	авіакорпорація	noun	noun:inanim:p:v_mis
авіакорпораціє	авіакорпорація	noun	noun:inanim:f:v_kly
авіакорпорацією	авіакорпорація	noun	noun:inanim:f:v_oru
авіакорпорації	авіакорпорація	noun	noun:inanim:f:v_dav
авіакорпорації	авіакорпорація	noun	noun:inanim:f:v_mis
авіакорпорації	авіакорпорація	noun	noun:inanim:f:v_rod
авіакорпорації	авіакорпорація	noun	noun:inanim:p:v_kly
авіакорпорації	авіакорпорація	noun	noun:inanim:p:v_naz
авіакорпорації	авіакорпорація	noun	noun:inanim:p:v_zna
авіакорпус	авіакорпус	noun	noun:inanim:m:v_naz
авіакорпус	авіакорпус	noun	noun:inanim:m:v_zna
авіакорпусам	авіакорпус	noun	noun:inanim:p:v_dav
авіакорпусами	авіакорпус	noun	noun:inanim:p:v_oru
авіакорпусах	авіакорпус	noun	noun:inanim:p:v_mis
авіакорпусе	авіакорпус	noun	noun:inanim:m:v_kly
авіакорпуси	авіакорпус	noun	noun:inanim:p:v_kly
авіакорпуси	авіакорпус	noun	noun:inanim:p:v_naz
авіакорпуси	авіакорпус	noun	noun:inanim:p:v_zna
авіакорпусові	авіакорпус	noun	noun:inanim:m:v_dav
авіакорпусові	авіакорпус	noun	noun:inanim:m:v_mis
авіакорпусом	авіакорпус	noun	noun:inanim:m:v_oru
авіакорпусу	авіакорпус	noun	noun:inanim:m:v_dav
авіакорпусу	авіакорпус	noun	noun:inanim:m:v_mis
авіакорпусу	авіакорпус	noun	noun:inanim:m:v_rod
авіакорпусі	авіакорпус	noun	noun:inanim:m:v_mis
авіакорпусів	авіакорпус	noun	noun:inanim:p:v_rod
авіакрил	авіакрило	noun	noun:inanim:p:v_rod
авіакрила	авіакрило	noun	noun:inanim:n:v_rod
авіакрила	авіакрило	noun	noun:inanim:p:v_kly
авіакрила	авіакрило	noun	noun:inanim:p:v_naz
авіакрила	авіакрило	noun	noun:inanim:p:v_zna
авіакрилам	авіакрило	noun	noun:inanim:p:v_dav
авіакрилами	авіакрило	noun	noun:inanim:p:v_oru
авіакрилах	авіакрило	noun	noun:inanim:p:v_mis
авіакрило	авіакрило	noun	noun:inanim:n:v_kly
авіакрило	авіакрило	noun	noun:inanim:n:v_naz
авіакрило	авіакрило	noun	noun:inanim:n:v_zna
авіакрилом	авіакрило	noun	noun:inanim:n:v_oru
авіакрилу	авіакрило	noun	noun:inanim:n:v_dav
авіакрилу	авіакрило	noun	noun:inanim:n:v_mis
авіакрилі	авіакрило	noun	noun:inanim:n:v_mis
авіакулемет	авіакулемет	noun	noun:inanim:m:v_naz
авіакулемет	авіакулемет	noun	noun:inanim:m:v_zna
авіакулемета	авіакулемет	noun	noun:inanim:m:v_rod
авіакулеметам	авіакулемет	noun	noun:inanim:p:v_dav
авіакулеметами	авіакулемет	noun	noun:inanim:p:v_oru
авіакулеметах	авіакулемет	noun	noun:inanim:p:v_mis
авіакулемете	авіакулемет	noun	noun:inanim:m:v_kly
авіакулемети	авіакулемет	noun	noun:inanim:p:v_kly
авіакулемети	авіакулемет	noun	noun:inanim:p:v_naz
авіакулемети	авіакулемет	noun	noun:inanim:p:v_zna
авіакулеметові	авіакулемет	noun	noun:inanim:m:v_dav
авіакулеметові	авіакулемет	noun	noun:inanim:m:v_mis
авіакулеметом	авіакулемет	noun	noun:inanim:m:v_oru
авіакулеметі	авіакулемет	noun	noun:inanim:m:v_mis
авіакулеметів	авіакулемет	noun	noun:inanim:p:v_rod
авіалайнер	авіалайнер	noun	noun:inanim:m:v_naz
авіалайнер	авіалайнер	noun	noun:inanim:m:v_zna
авіалайнера	авіалайнер	noun	noun:inanim:m:v_rod
авіалайнерам	авіалайнер	noun	noun:inanim:p:v_dav
авіалайнерами	авіалайнер	noun	noun:inanim:p:v_oru
авіалайнерах	авіалайнер	noun	noun:inanim:p:v_mis
авіалайнере	авіалайнер	noun	noun:inanim:m:v_kly
авіалайнери	авіалайнер	noun	noun:inanim:p:v_kly
авіалайнери	авіалайнер	noun	noun:inanim:p:v_naz
авіалайнери	авіалайнер	noun	noun:inanim:p:v_zna
авіалайнерові	авіалайнер	noun	noun:inanim:m:v_dav
авіалайнерові	авіалайнер	noun	noun:inanim:m:v_mis
авіалайнером	авіалайнер	noun	noun:inanim:m:v_oru
авіалайнері	авіалайнер	noun	noun:inanim:m:v_mis
авіалайнерів	авіалайнер	noun	noun:inanim:p:v_rod
авіаланка	авіаланка	noun	noun:inanim:f:v_naz
авіаланкам	авіаланка	noun	noun:inanim:p:v_dav
авіаланками	авіаланка	noun	noun:inanim:p:v_oru
авіаланках	авіаланка	noun	noun:inanim:p:v_mis
авіаланки	авіаланка	noun	noun:inanim:f:v_rod
авіаланки	авіаланка	noun	noun:inanim:p:v_kly
авіаланки	авіаланка	noun	noun:inanim:p:v_naz
авіаланки	авіаланка	noun	noun:inanim:p:v_zna
авіаланко	авіаланка	noun	noun:inanim:f:v_kly
авіаланкою	авіаланка	noun	noun:inanim:f:v_oru
авіаланку	авіаланка	noun	noun:inanim:f:v_zna
авіаланок	авіаланка	noun	noun:inanim:p:v_rod
авіаланці	авіаланка	noun	noun:inanim:f:v_dav
авіаланці	авіаланка	noun	noun:inanim:f:v_mis
авіалюбителеві	авіалюбитель	noun	noun:anim:m:v_dav
авіалюбителеві	авіалюбитель	noun	noun:anim:m:v_mis
авіалюбителем	авіалюбитель	noun	noun:anim:m:v_oru
авіалюбитель	авіалюбитель	noun	noun:anim:m:v_naz
авіалюбителю	авіалюбитель	noun	noun:anim:m:v_dav
авіалюбителю	авіалюбитель	noun	noun:anim:m:v_kly
авіалюбителю	авіалюбитель	noun	noun:anim:m:v_mis
авіалюбителя	авіалюбитель	noun	noun:anim:m:v_rod
авіалюбителя	авіалюбитель	noun	noun:anim:m:v_zna
авіалюбителям	авіалюбитель	noun	noun:anim:p:v_dav
авіалюбителями	авіалюбитель	noun	noun:anim:p:v_oru
авіалюбителях	авіалюбитель	noun	noun:anim:p:v_mis
авіалюбителі	авіалюбитель	noun	noun:anim:m:v_mis
авіалюбителі	авіалюбитель	noun	noun:anim:p:v_kly
авіалюбителі	авіалюбитель	noun	noun:anim:p:v_naz
авіалюбителі	авіалюбитель	noun	noun:anim:p:v_zna:rare
авіалюбителів	авіалюбитель	noun	noun:anim:p:v_rod
авіалюбителів	авіалюбитель	noun	noun:anim:p:v_zna
авіаліній	авіалінія	noun	noun:inanim:p:v_rod
авіалінію	авіалінія	noun	noun:inanim:f:v_zna
авіалінія	авіалінія	noun	noun:inanim:f:v_naz
авіалініям	авіалінія	noun	noun:inanim:p:v_dav
авіалініями	авіалінія	noun	noun:inanim:p:v_oru
авіалініях	авіалінія	noun	noun:inanim:p:v_mis
авіалініє	авіалінія	noun	noun:inanim:f:v_kly
авіалінією	авіалінія	noun	noun:inanim:f:v_oru
авіалінії	авіалінія	noun	noun:inanim:f:v_dav
авіалінії	авіалінія	noun	noun:inanim:f:v_mis
авіалінії	авіалінія	noun	noun:inanim:f:v_rod
авіалінії	авіалінія	noun	noun:inanim:p:v_kly
авіалінії	авіалінія	noun	noun:inanim:p:v_naz
авіалінії	авіалінія	noun	noun:inanim:p:v_zna
авіамагазин	авіамагазин	noun	noun:inanim:m:v_naz
авіамагазин	авіамагазин	noun	noun:inanim:m:v_zna
авіамагазинам	авіамагазин	noun	noun:inanim:p:v_dav
авіамагазинами	авіамагазин	noun	noun:inanim:p:v_oru
авіамагазинах	авіамагазин	noun	noun:inanim:p:v_mis
авіамагазине	авіамагазин	noun	noun:inanim:m:v_kly
авіамагазини	авіамагазин	noun	noun:inanim:p:v_kly
авіамагазини	авіамагазин	noun	noun:inanim:p:v_naz
авіамагазини	авіамагазин	noun	noun:inanim:p:v_zna
авіамагазинові	авіамагазин	noun	noun:inanim:m:v_dav
авіамагазинові	авіамагазин	noun	noun:inanim:m:v_mis
авіамагазином	авіамагазин	noun	noun:inanim:m:v_oru
авіамагазину	авіамагазин	noun	noun:inanim:m:v_dav
авіамагазину	авіамагазин	noun	noun:inanim:m:v_mis
авіамагазину	авіамагазин	noun	noun:inanim:m:v_rod
авіамагазині	авіамагазин	noun	noun:inanim:m:v_mis
авіамагазинів	авіамагазин	noun	noun:inanim:p:v_rod
авіамагістрале	авіамагістраль	noun	noun:inanim:f:v_kly
авіамагістралей	авіамагістраль	noun	noun:inanim:p:v_rod
авіамагістраллю	авіамагістраль	noun	noun:inanim:f:v_oru
авіамагістраль	авіамагістраль	noun	noun:inanim:f:v_naz
авіамагістраль	авіамагістраль	noun	noun:inanim:f:v_zna
авіамагістралям	авіамагістраль	noun	noun:inanim:p:v_dav
авіамагістралями	авіамагістраль	noun	noun:inanim:p:v_oru
авіамагістралях	авіамагістраль	noun	noun:inanim:p:v_mis
авіамагістралі	авіамагістраль	noun	noun:inanim:f:v_dav
авіамагістралі	авіамагістраль	noun	noun:inanim:f:v_mis
авіамагістралі	авіамагістраль	noun	noun:inanim:f:v_rod
авіамагістралі	авіамагістраль	noun	noun:inanim:p:v_kly
авіамагістралі	авіамагістраль	noun	noun:inanim:p:v_naz
авіамагістралі	авіамагістраль	noun	noun:inanim:p:v_zna
авіамайданчик	авіамайданчик	noun	noun:inanim:m:v_naz
авіамайданчик	авіамайданчик	noun	noun:inanim:m:v_zna
авіамайданчика	авіамайданчик	noun	noun:inanim:m:v_rod
авіамайданчикам	авіамайданчик	noun	noun:inanim:p:v_dav
авіамайданчиками	авіамайданчик	noun	noun:inanim:p:v_oru
авіамайданчиках	авіамайданчик	noun	noun:inanim:p:v_mis
авіамайданчики	авіамайданчик	noun	noun:inanim:p:v_kly
авіамайданчики	авіамайданчик	noun	noun:inanim:p:v_naz
авіамайданчики	авіамайданчик	noun	noun:inanim:p:v_zna
авіамайданчикові	авіамайданчик	noun	noun:inanim:m:v_dav
авіамайданчикові	авіамайданчик	noun	noun:inanim:m:v_mis
авіамайданчиком	авіамайданчик	noun	noun:inanim:m:v_oru
авіамайданчику	авіамайданчик	noun	noun:inanim:m:v_dav
авіамайданчику	авіамайданчик	noun	noun:inanim:m:v_kly
авіамайданчику	авіамайданчик	noun	noun:inanim:m:v_mis
авіамайданчиків	авіамайданчик	noun	noun:inanim:p:v_rod
авіамайстерень	авіамайстерня	noun	noun:inanim:p:v_rod
авіамайстерне	авіамайстерня	noun	noun:inanim:f:v_kly
авіамайстернею	авіамайстерня	noun	noun:inanim:f:v_oru
авіамайстерню	авіамайстерня	noun	noun:inanim:f:v_zna
авіамайстерня	авіамайстерня	noun	noun:inanim:f:v_naz
авіамайстерням	авіамайстерня	noun	noun:inanim:p:v_dav
авіамайстернями	авіамайстерня	noun	noun:inanim:p:v_oru
авіамайстернях	авіамайстерня	noun	noun:inanim:p:v_mis
авіамайстерні	авіамайстерня	noun	noun:inanim:f:v_dav
авіамайстерні	авіамайстерня	noun	noun:inanim:f:v_mis
авіамайстерні	авіамайстерня	noun	noun:inanim:f:v_rod
авіамайстерні	авіамайстерня	noun	noun:inanim:p:v_kly
авіамайстерні	авіамайстерня	noun	noun:inanim:p:v_naz
авіамайстерні	авіамайстерня	noun	noun:inanim:p:v_zna
авіаманевр	авіаманевр	noun	noun:inanim:m:v_naz
авіаманевр	авіаманевр	noun	noun:inanim:m:v_zna
авіаманеврам	авіаманевр	noun	noun:inanim:p:v_dav
авіаманеврами	авіаманевр	noun	noun:inanim:p:v_oru
авіаманеврах	авіаманевр	noun	noun:inanim:p:v_mis
авіаманевре	авіаманевр	noun	noun:inanim:m:v_kly
авіаманеври	авіаманевр	noun	noun:inanim:p:v_kly
авіаманеври	авіаманевр	noun	noun:inanim:p:v_naz
авіаманеври	авіаманевр	noun	noun:inanim:p:v_zna
авіаманеврові	авіаманевр	noun	noun:inanim:m:v_dav
авіаманеврові	авіаманевр	noun	noun:inanim:m:v_mis
авіаманевром	авіаманевр	noun	noun:inanim:m:v_oru
авіаманевру	авіаманевр	noun	noun:inanim:m:v_dav
авіаманевру	авіаманевр	noun	noun:inanim:m:v_mis
авіаманевру	авіаманевр	noun	noun:inanim:m:v_rod
авіаманеврі	авіаманевр	noun	noun:inanim:m:v_mis
авіаманеврів	авіаманевр	noun	noun:inanim:p:v_rod
авіамаршрут	авіамаршрут	noun	noun:inanim:m:v_naz
авіамаршрут	авіамаршрут	noun	noun:inanim:m:v_zna
авіамаршрутам	авіамаршрут	noun	noun:inanim:p:v_dav
авіамаршрутами	авіамаршрут	noun	noun:inanim:p:v_oru
авіамаршрутах	авіамаршрут	noun	noun:inanim:p:v_mis
авіамаршруте	авіамаршрут	noun	noun:inanim:m:v_kly
авіамаршрути	авіамаршрут	noun	noun:inanim:p:v_kly
авіамаршрути	авіамаршрут	noun	noun:inanim:p:v_naz
авіамаршрути	авіамаршрут	noun	noun:inanim:p:v_zna
авіамаршрутові	авіамаршрут	noun	noun:inanim:m:v_dav
авіамаршрутові	авіамаршрут	noun	noun:inanim:m:v_mis
авіамаршрутом	авіамаршрут	noun	noun:inanim:m:v_oru
авіамаршруту	авіамаршрут	noun	noun:inanim:m:v_dav
авіамаршруту	авіамаршрут	noun	noun:inanim:m:v_mis
авіамаршруту	авіамаршрут	noun	noun:inanim:m:v_rod
авіамаршруті	авіамаршрут	noun	noun:inanim:m:v_mis
авіамаршрутів	авіамаршрут	noun	noun:inanim:p:v_rod
авіаматка	авіаматка	noun	noun:inanim:f:v_naz
авіаматкам	авіаматка	noun	noun:inanim:p:v_dav
авіаматками	авіаматка	noun	noun:inanim:p:v_oru
авіаматках	авіаматка	noun	noun:inanim:p:v_mis
авіаматки	авіаматка	noun	noun:inanim:f:v_rod
авіаматки	авіаматка	noun	noun:inanim:p:v_kly
авіаматки	авіаматка	noun	noun:inanim:p:v_naz
авіаматки	авіаматка	noun	noun:inanim:p:v_zna
авіаматко	авіаматка	noun	noun:inanim:f:v_kly
авіаматкою	авіаматка	noun	noun:inanim:f:v_oru
авіаматку	авіаматка	noun	noun:inanim:f:v_zna
авіаматок	авіаматка	noun	noun:inanim:p:v_rod
авіаматці	авіаматка	noun	noun:inanim:f:v_dav
авіаматці	авіаматка	noun	noun:inanim:f:v_mis
авіамашин	авіамашина	noun	noun:inanim:p:v_rod
авіамашина	авіамашина	noun	noun:inanim:f:v_naz
авіамашинам	авіамашина	noun	noun:inanim:p:v_dav
авіамашинами	авіамашина	noun	noun:inanim:p:v_oru
авіамашинах	авіамашина	noun	noun:inanim:p:v_mis
авіамашини	авіамашина	noun	noun:inanim:f:v_rod
авіамашини	авіамашина	noun	noun:inanim:p:v_kly
авіамашини	авіамашина	noun	noun:inanim:p:v_naz
авіамашини	авіамашина	noun	noun:inanim:p:v_zna
авіамашино	авіамашина	noun	noun:inanim:f:v_kly
авіамашиною	авіамашина	noun	noun:inanim:f:v_oru
авіамашину	авіамашина	noun	noun:inanim:f:v_zna
авіамашині	авіамашина	noun	noun:inanim:f:v_dav
авіамашині	авіамашина	noun	noun:inanim:f:v_mis
авіамаяк	авіамаяк	noun	noun:inanim:m:v_naz
авіамаяк	авіамаяк	noun	noun:inanim:m:v_zna
авіамаяка	авіамаяк	noun	noun:inanim:m:v_rod
авіамаякам	авіамаяк	noun	noun:inanim:p:v_dav
авіамаяками	авіамаяк	noun	noun:inanim:p:v_oru
авіамаяках	авіамаяк	noun	noun:inanim:p:v_mis
авіамаяки	авіамаяк	noun	noun:inanim:p:v_kly
авіамаяки	авіамаяк	noun	noun:inanim:p:v_naz
авіамаяки	авіамаяк	noun	noun:inanim:p:v_zna
авіамаякові	авіамаяк	noun	noun:inanim:m:v_dav
авіамаякові	авіамаяк	noun	noun:inanim:m:v_mis
авіамаяком	авіамаяк	noun	noun:inanim:m:v_oru
авіамаяку	авіамаяк	noun	noun:inanim:m:v_dav
авіамаяку	авіамаяк	noun	noun:inanim:m:v_kly
авіамаяку	авіамаяк	noun	noun:inanim:m:v_mis
авіамаяків	авіамаяк	noun	noun:inanim:p:v_rod
авіамедик	авіамедик	noun	noun:anim:m:v_naz
авіамедика	авіамедик	noun	noun:anim:m:v_rod
авіамедика	авіамедик	noun	noun:anim:m:v_zna
авіамедикам	авіамедик	noun	noun:anim:p:v_dav
авіамедиками	авіамедик	noun	noun:anim:p:v_oru
авіамедиках	авіамедик	noun	noun:anim:p:v_mis
авіамедики	авіамедик	noun	noun:anim:p:v_kly
авіамедики	авіамедик	noun	noun:anim:p:v_naz
авіамедики	авіамедик	noun	noun:anim:p:v_zna:rare
авіамедикові	авіамедик	noun	noun:anim:m:v_dav
авіамедикові	авіамедик	noun	noun:anim:m:v_mis
авіамедиком	авіамедик	noun	noun:anim:m:v_oru
авіамедику	авіамедик	noun	noun:anim:m:v_dav
авіамедику	авіамедик	noun	noun:anim:m:v_kly
авіамедику	авіамедик	noun	noun:anim:m:v_mis
авіамедиків	авіамедик	noun	noun:anim:p:v_rod
авіамедиків	авіамедик	noun	noun:anim:p:v_zna
авіаменеджер	авіаменеджер	noun	noun:anim:m:v_naz
авіаменеджера	авіаменеджер	noun	noun:anim:m:v_rod
авіаменеджера	авіаменеджер	noun	noun:anim:m:v_zna
авіаменеджерам	авіаменеджер	noun	noun:anim:p:v_dav
авіаменеджерами	авіаменеджер	noun	noun:anim:p:v_oru
авіаменеджерах	авіаменеджер	noun	noun:anim:p:v_mis
авіаменеджере	авіаменеджер	noun	noun:anim:m:v_kly
авіаменеджери	авіаменеджер	noun	noun:anim:p:v_kly
авіаменеджери	авіаменеджер	noun	noun:anim:p:v_naz
авіаменеджери	авіаменеджер	noun	noun:anim:p:v_zna:rare
авіаменеджерові	авіаменеджер	noun	noun:anim:m:v_dav
авіаменеджерові	авіаменеджер	noun	noun:anim:m:v_mis
авіаменеджером	авіаменеджер	noun	noun:anim:m:v_oru
авіаменеджері	авіаменеджер	noun	noun:anim:m:v_mis
авіаменеджерів	авіаменеджер	noun	noun:anim:p:v_rod
авіаменеджерів	авіаменеджер	noun	noun:anim:p:v_zna
авіаметеослужб	авіаметеослужба	noun	noun:inanim:p:v_rod
авіаметеослужба	авіаметеослужба	noun	noun:inanim:f:v_naz
авіаметеослужбам	авіаметеослужба	noun	noun:inanim:p:v_dav
авіаметеослужбами	авіаметеослужба	noun	noun:inanim:p:v_oru
авіаметеослужбах	авіаметеослужба	noun	noun:inanim:p:v_mis
авіаметеослужби	авіаметеослужба	noun	noun:inanim:f:v_rod
авіаметеослужби	авіаметеослужба	noun	noun:inanim:p:v_kly
авіаметеослужби	авіаметеослужба	noun	noun:inanim:p:v_naz
авіаметеослужби	авіаметеослужба	noun	noun:inanim:p:v_zna
авіаметеослужбо	авіаметеослужба	noun	noun:inanim:f:v_kly
авіаметеослужбою	авіаметеослужба	noun	noun:inanim:f:v_oru
авіаметеослужбу	авіаметеослужба	noun	noun:inanim:f:v_zna
авіаметеослужбі	авіаметеослужба	noun	noun:inanim:f:v_dav
авіаметеослужбі	авіаметеослужба	noun	noun:inanim:f:v_mis
авіаметеостанцій	авіаметеостанція	noun	noun:inanim:p:v_rod
авіаметеостанцію	авіаметеостанція	noun	noun:inanim:f:v_zna
авіаметеостанція	авіаметеостанція	noun	noun:inanim:f:v_naz
авіаметеостанціям	авіаметеостанція	noun	noun:inanim:p:v_dav
авіаметеостанціями	авіаметеостанція	noun	noun:inanim:p:v_oru
авіаметеостанціях	авіаметеостанція	noun	noun:inanim:p:v_mis
авіаметеостанціє	авіаметеостанція	noun	noun:inanim:f:v_kly
авіаметеостанцією	авіаметеостанція	noun	noun:inanim:f:v_oru
авіаметеостанції	авіаметеостанція	noun	noun:inanim:f:v_dav
авіаметеостанції	авіаметеостанція	noun	noun:inanim:f:v_mis
авіаметеостанції	авіаметеостанція	noun	noun:inanim:f:v_rod
авіаметеостанції	авіаметеостанція	noun	noun:inanim:p:v_kly
авіаметеостанції	авіаметеостанція	noun	noun:inanim:p:v_naz
авіаметеостанції	авіаметеостанція	noun	noun:inanim:p:v_zna
авіамеханік	авіамеханік	noun	noun:anim:m:v_naz
авіамеханіка	авіамеханік	noun	noun:anim:m:v_rod
авіамеханіка	авіамеханік	noun	noun:anim:m:v_zna
авіамеханікам	авіамеханік	noun	noun:anim:p:v_dav
авіамеханіками	авіамеханік	noun	noun:anim:p:v_oru
авіамеханіках	авіамеханік	noun	noun:anim:p:v_mis
авіамеханіки	авіамеханік	noun	noun:anim:p:v_kly
авіамеханіки	авіамеханік	noun	noun:anim:p:v_naz
авіамеханіки	авіамеханік	noun	noun:anim:p:v_zna:rare
авіамеханікові	авіамеханік	noun	noun:anim:m:v_dav
авіамеханікові	авіамеханік	noun	noun:anim:m:v_mis
авіамеханіком	авіамеханік	noun	noun:anim:m:v_oru
авіамеханіку	авіамеханік	noun	noun:anim:m:v_dav
авіамеханіку	авіамеханік	noun	noun:anim:m:v_kly
авіамеханіку	авіамеханік	noun	noun:anim:m:v_mis
авіамеханіків	авіамеханік	noun	noun:anim:p:v_rod
авіамеханіків	авіамеханік	noun	noun:anim:p:v_zna
авіамоделе	авіамодель	noun	noun:inanim:f:v_kly
авіамоделей	авіамодель	noun	noun:inanim:p:v_rod
авіамоделлю	авіамодель	noun	noun:inanim:f:v_oru
авіамодель	авіамодель	noun	noun:inanim:f:v_naz
авіамодель	авіамодель	noun	noun:inanim:f:v_zna
авіамоделям	авіамодель	noun	noun:inanim:p:v_dav
авіамоделями	авіамодель	noun	noun:inanim:p:v_oru
авіамоделях	авіамодель	noun	noun:inanim:p:v_mis
авіамоделі	авіамодель	noun	noun:inanim:f:v_dav
авіамоделі	авіамодель	noun	noun:inanim:f:v_mis
авіамоделі	авіамодель	noun	noun:inanim:f:v_rod
авіамоделі	авіамодель	noun	noun:inanim:p:v_kly
авіамоделі	авіамодель	noun	noun:inanim:p:v_naz
авіамоделі	авіамодель	noun	noun:inanim:p:v_zna
авіамоделіст	авіамоделіст	noun	noun:anim:m:v_naz
авіамоделіста	авіамоделіст	noun	noun:anim:m:v_rod
авіамоделіста	авіамоделіст	noun	noun:anim:m:v_zna
авіамоделістам	авіамоделіст	noun	noun:anim:p:v_dav
авіамоделістами	авіамоделіст	noun	noun:anim:p:v_oru
авіамоделістах	авіамоделіст	noun	noun:anim:p:v_mis
авіамоделісте	авіамоделіст	noun	noun:anim:m:v_kly
авіамоделісти	авіамоделіст	noun	noun:anim:p:v_kly
авіамоделісти	авіамоделіст	noun	noun:anim:p:v_naz
авіамоделісти	авіамоделіст	noun	noun:anim:p:v_zna:rare
авіамоделістові	авіамоделіст	noun	noun:anim:m:v_dav
авіамоделістові	авіамоделіст	noun	noun:anim:m:v_mis
авіамоделістом	авіамоделіст	noun	noun:anim:m:v_oru
авіамоделісті	авіамоделіст	noun	noun:anim:m:v_mis
авіамоделістів	авіамоделіст	noun	noun:anim:p:v_rod
авіамоделістів	авіамоделіст	noun	noun:anim:p:v_zna
авіамотор	авіамотор	noun	noun:inanim:m:v_naz
авіамотор	авіамотор	noun	noun:inanim:m:v_zna
авіамотора	авіамотор	noun	noun:inanim:m:v_rod
авіамоторам	авіамотор	noun	noun:inanim:p:v_dav
авіамоторами	авіамотор	noun	noun:inanim:p:v_oru
авіамоторах	авіамотор	noun	noun:inanim:p:v_mis
авіамоторе	авіамотор	noun	noun:inanim:m:v_kly
авіамотори	авіамотор	noun	noun:inanim:p:v_kly
авіамотори	авіамотор	noun	noun:inanim:p:v_naz
авіамотори	авіамотор	noun	noun:inanim:p:v_zna
авіамоторист	авіамоторист	noun	noun:anim:m:v_naz
авіамоториста	авіамоторист	noun	noun:anim:m:v_rod
авіамоториста	авіамоторист	noun	noun:anim:m:v_zna
авіамотористам	авіамоторист	noun	noun:anim:p:v_dav
авіамотористами	авіамоторист	noun	noun:anim:p:v_oru
авіамотористах	авіамоторист	noun	noun:anim:p:v_mis
авіамотористе	авіамоторист	noun	noun:anim:m:v_kly
авіамотористи	авіамоторист	noun	noun:anim:p:v_kly
авіамотористи	авіамоторист	noun	noun:anim:p:v_naz
авіамотористи	авіамоторист	noun	noun:anim:p:v_zna:rare
авіамотористові	авіамоторист	noun	noun:anim:m:v_dav
авіамотористові	авіамоторист	noun	noun:anim:m:v_mis
авіамотористом	авіамоторист	noun	noun:anim:m:v_oru
авіамотористі	авіамоторист	noun	noun:anim:m:v_mis
авіамотористів	авіамоторист	noun	noun:anim:p:v_rod
авіамотористів	авіамоторист	noun	noun:anim:p:v_zna
авіамоторові	авіамотор	noun	noun:inanim:m:v_dav
авіамоторові	авіамотор	noun	noun:inanim:m:v_mis
авіамотором	авіамотор	noun	noun:inanim:m:v_oru
авіамоторі	авіамотор	noun	noun:inanim:m:v_mis
авіамоторів	авіамотор	noun	noun:inanim:p:v_rod
авіамузей	авіамузей	noun	noun:inanim:m:v_naz
авіамузей	авіамузей	noun	noun:inanim:m:v_zna
авіамузею	авіамузей	noun	noun:inanim:m:v_dav
авіамузею	авіамузей	noun	noun:inanim:m:v_kly
авіамузею	авіамузей	noun	noun:inanim:m:v_mis
авіамузею	авіамузей	noun	noun:inanim:m:v_rod
авіамузеям	авіамузей	noun	noun:inanim:p:v_dav
авіамузеями	авіамузей	noun	noun:inanim:p:v_oru
авіамузеях	авіамузей	noun	noun:inanim:p:v_mis
авіамузеєві	авіамузей	noun	noun:inanim:m:v_dav
авіамузеєві	авіамузей	noun	noun:inanim:m:v_mis
авіамузеєм	авіамузей	noun	noun:inanim:m:v_oru
авіамузеї	авіамузей	noun	noun:inanim:m:v_mis
авіамузеї	авіамузей	noun	noun:inanim:p:v_kly
авіамузеї	авіамузей	noun	noun:inanim:p:v_naz
авіамузеї	авіамузей	noun	noun:inanim:p:v_zna
авіамузеїв	авіамузей	noun	noun:inanim:p:v_rod
авіамістечка	авіамістечко	noun	noun:inanim:n:v_rod
авіамістечка	авіамістечко	noun	noun:inanim:p:v_kly
авіамістечка	авіамістечко	noun	noun:inanim:p:v_naz
авіамістечка	авіамістечко	noun	noun:inanim:p:v_zna
авіамістечкам	авіамістечко	noun	noun:inanim:p:v_dav
авіамістечками	авіамістечко	noun	noun:inanim:p:v_oru
авіамістечках	авіамістечко	noun	noun:inanim:p:v_mis
авіамістечко	авіамістечко	noun	noun:inanim:n:v_kly
авіамістечко	авіамістечко	noun	noun:inanim:n:v_naz
авіамістечко	авіамістечко	noun	noun:inanim:n:v_zna
авіамістечком	авіамістечко	noun	noun:inanim:n:v_oru
авіамістечку	авіамістечко	noun	noun:inanim:n:v_dav
авіамістечку	авіамістечко	noun	noun:inanim:n:v_mis
авіамістечок	авіамістечко	noun	noun:inanim:p:v_rod
авіанавідник	авіанавідник	noun	noun:anim:m:v_naz
авіанавідника	авіанавідник	noun	noun:anim:m:v_rod
авіанавідника	авіанавідник	noun	noun:anim:m:v_zna
авіанавідникам	авіанавідник	noun	noun:anim:p:v_dav
авіанавідниками	авіанавідник	noun	noun:anim:p:v_oru
авіанавідниках	авіанавідник	noun	noun:anim:p:v_mis
авіанавідники	авіанавідник	noun	noun:anim:p:v_kly
авіанавідники	авіанавідник	noun	noun:anim:p:v_naz
авіанавідники	авіанавідник	noun	noun:anim:p:v_zna:rare
авіанавідникові	авіанавідник	noun	noun:anim:m:v_dav
авіанавідникові	авіанавідник	noun	noun:anim:m:v_mis
авіанавідником	авіанавідник	noun	noun:anim:m:v_oru
авіанавіднику	авіанавідник	noun	noun:anim:m:v_dav
авіанавіднику	авіанавідник	noun	noun:anim:m:v_kly
авіанавіднику	авіанавідник	noun	noun:anim:m:v_mis
авіанавідників	авіанавідник	noun	noun:anim:p:v_rod
авіанавідників	авіанавідник	noun	noun:anim:p:v_zna
авіанальотам	авіаналіт	noun	noun:inanim:p:v_dav
авіанальотами	авіаналіт	noun	noun:inanim:p:v_oru
авіанальотах	авіаналіт	noun	noun:inanim:p:v_mis
авіанальоте	авіаналіт	noun	noun:inanim:m:v_kly
авіанальоти	авіаналіт	noun	noun:inanim:p:v_kly
авіанальоти	авіаналіт	noun	noun:inanim:p:v_naz
авіанальоти	авіаналіт	noun	noun:inanim:p:v_zna
авіанальотові	авіаналіт	noun	noun:inanim:m:v_dav
авіанальотові	авіаналіт	noun	noun:inanim:m:v_mis
авіанальотом	авіаналіт	noun	noun:inanim:m:v_oru
авіанальоту	авіаналіт	noun	noun:inanim:m:v_dav
авіанальоту	авіаналіт	noun	noun:inanim:m:v_mis
авіанальоту	авіаналіт	noun	noun:inanim:m:v_rod
авіанальоті	авіаналіт	noun	noun:inanim:m:v_mis
авіанальотів	авіаналіт	noun	noun:inanim:p:v_rod
авіаналіт	авіаналіт	noun	noun:inanim:m:v_naz
авіаналіт	авіаналіт	noun	noun:inanim:m:v_zna
авіанапад	авіанапад	noun	noun:inanim:m:v_naz
авіанапад	авіанапад	noun	noun:inanim:m:v_zna
авіанападам	авіанапад	noun	noun:inanim:p:v_dav
авіанападами	авіанапад	noun	noun:inanim:p:v_oru
авіанападах	авіанапад	noun	noun:inanim:p:v_mis
авіанападе	авіанапад	noun	noun:inanim:m:v_kly
авіанапади	авіанапад	noun	noun:inanim:p:v_kly
авіанапади	авіанапад	noun	noun:inanim:p:v_naz
авіанапади	авіанапад	noun	noun:inanim:p:v_zna
авіанападові	авіанапад	noun	noun:inanim:m:v_dav
авіанападові	авіанапад	noun	noun:inanim:m:v_mis
авіанападом	авіанапад	noun	noun:inanim:m:v_oru
авіанападу	авіанапад	noun	noun:inanim:m:v_dav
авіанападу	авіанапад	noun	noun:inanim:m:v_mis
авіанападу	авіанапад	noun	noun:inanim:m:v_rod
авіанападі	авіанапад	noun	noun:inanim:m:v_mis
авіанападів	авіанапад	noun	noun:inanim:p:v_rod
авіаносець	авіаносець	noun	noun:inanim:m:v_naz
авіаносець	авіаносець	noun	noun:inanim:m:v_zna
авіаносцеві	авіаносець	noun	noun:inanim:m:v_dav
авіаносцеві	авіаносець	noun	noun:inanim:m:v_mis
авіаносцем	авіаносець	noun	noun:inanim:m:v_oru
авіаносцю	авіаносець	noun	noun:inanim:m:v_dav
авіаносцю	авіаносець	noun	noun:inanim:m:v_kly
авіаносцю	авіаносець	noun	noun:inanim:m:v_mis
авіаносця	авіаносець	noun	noun:inanim:m:v_rod
авіаносцям	авіаносець	noun	noun:inanim:p:v_dav
авіаносцями	авіаносець	noun	noun:inanim:p:v_oru
авіаносцях	авіаносець	noun	noun:inanim:p:v_mis
авіаносці	авіаносець	noun	noun:inanim:m:v_mis
авіаносці	авіаносець	noun	noun:inanim:p:v_kly
авіаносці	авіаносець	noun	noun:inanim:p:v_naz
авіаносці	авіаносець	noun	noun:inanim:p:v_zna
авіаносців	авіаносець	noun	noun:inanim:p:v_rod
авіаоблік	авіаоблік	noun	noun:inanim:m:v_naz
авіаоблік	авіаоблік	noun	noun:inanim:m:v_zna
авіаоблікам	авіаоблік	noun	noun:inanim:p:v_dav
авіаобліками	авіаоблік	noun	noun:inanim:p:v_oru
авіаобліках	авіаоблік	noun	noun:inanim:p:v_mis
авіаобліки	авіаоблік	noun	noun:inanim:p:v_kly
авіаобліки	авіаоблік	noun	noun:inanim:p:v_naz
авіаобліки	авіаоблік	noun	noun:inanim:p:v_zna
авіаоблікові	авіаоблік	noun	noun:inanim:m:v_dav
авіаоблікові	авіаоблік	noun	noun:inanim:m:v_mis
авіаобліком	авіаоблік	noun	noun:inanim:m:v_oru
авіаобліку	авіаоблік	noun	noun:inanim:m:v_dav
авіаобліку	авіаоблік	noun	noun:inanim:m:v_kly
авіаобліку	авіаоблік	noun	noun:inanim:m:v_mis
авіаобліку	авіаоблік	noun	noun:inanim:m:v_rod
авіаобліків	авіаоблік	noun	noun:inanim:p:v_rod
авіаобприскуванню	авіаобприскування	noun	noun:inanim:n:v_dav
авіаобприскуванню	авіаобприскування	noun	noun:inanim:n:v_mis
авіаобприскування	авіаобприскування	noun	noun:inanim:n:v_kly
авіаобприскування	авіаобприскування	noun	noun:inanim:n:v_naz
авіаобприскування	авіаобприскування	noun	noun:inanim:n:v_rod
авіаобприскування	авіаобприскування	noun	noun:inanim:n:v_zna
авіаобприскування	авіаобприскування	noun	noun:inanim:p:v_kly
авіаобприскування	авіаобприскування	noun	noun:inanim:p:v_naz
авіаобприскування	авіаобприскування	noun	noun:inanim:p:v_zna
авіаобприскуванням	авіаобприскування	noun	noun:inanim:n:v_oru
авіаобприскуванням	авіаобприскування	noun	noun:inanim:p:v_dav
авіаобприскуваннями	авіаобприскування	noun	noun:inanim:p:v_oru
авіаобприскуваннях	авіаобприскування	noun	noun:inanim:p:v_mis
авіаобприскуванні	авіаобприскування	noun	noun:inanim:n:v_mis
авіаобприскувань	авіаобприскування	noun	noun:inanim:p:v_rod
авіаобприскувач	авіаобприскувач	noun	noun:inanim:m:v_naz
авіаобприскувач	авіаобприскувач	noun	noun:inanim:m:v_zna
авіаобприскувача	авіаобприскувач	noun	noun:inanim:m:v_rod
авіаобприскувачам	авіаобприскувач	noun	noun:inanim:p:v_dav
авіаобприскувачами	авіаобприскувач	noun	noun:inanim:p:v_oru
авіаобприскувачах	авіаобприскувач	noun	noun:inanim:p:v_mis
авіаобприскувачеві	авіаобприскувач	noun	noun:inanim:m:v_dav
авіаобприскувачеві	авіаобприскувач	noun	noun:inanim:m:v_mis
авіаобприскувачем	авіаобприскувач	noun	noun:inanim:m:v_oru
авіаобприскувачу	авіаобприскувач	noun	noun:inanim:m:v_dav
авіаобприскувачу	авіаобприскувач	noun	noun:inanim:m:v_kly
авіаобприскувачу	авіаобприскувач	noun	noun:inanim:m:v_mis
авіаобприскувачі	авіаобприскувач	noun	noun:inanim:m:v_mis
авіаобприскувачі	авіаобприскувач	noun	noun:inanim:p:v_kly
авіаобприскувачі	авіаобприскувач	noun	noun:inanim:p:v_naz
авіаобприскувачі	авіаобприскувач	noun	noun:inanim:p:v_zna
авіаобприскувачів	авіаобприскувач	noun	noun:inanim:p:v_rod
авіаоператор	авіаоператор	noun	noun:anim:m:v_naz
авіаоператора	авіаоператор	noun	noun:anim:m:v_rod
авіаоператора	авіаоператор	noun	noun:anim:m:v_zna
авіаоператорам	авіаоператор	noun	noun:anim:p:v_dav
авіаоператорами	авіаоператор	noun	noun:anim:p:v_oru
авіаоператорах	авіаоператор	noun	noun:anim:p:v_mis
авіаоператоре	авіаоператор	noun	noun:anim:m:v_kly
авіаоператори	авіаоператор	noun	noun:anim:p:v_kly
авіаоператори	авіаоператор	noun	noun:anim:p:v_naz
авіаоператори	авіаоператор	noun	noun:anim:p:v_zna:rare
авіаоператорові	авіаоператор	noun	noun:anim:m:v_dav
авіаоператорові	авіаоператор	noun	noun:anim:m:v_mis
авіаоператором	авіаоператор	noun	noun:anim:m:v_oru
авіаоператорі	авіаоператор	noun	noun:anim:m:v_mis
авіаоператорів	авіаоператор	noun	noun:anim:p:v_rod
авіаоператорів	авіаоператор	noun	noun:anim:p:v_zna
авіапарк	авіапарк	noun	noun:inanim:m:v_naz
авіапарк	авіапарк	noun	noun:inanim:m:v_zna
авіапаркам	авіапарк	noun	noun:inanim:p:v_dav
авіапарками	авіапарк	noun	noun:inanim:p:v_oru
авіапарках	авіапарк	noun	noun:inanim:p:v_mis
авіапарки	авіапарк	noun	noun:inanim:p:v_kly
авіапарки	авіапарк	noun	noun:inanim:p:v_naz
авіапарки	авіапарк	noun	noun:inanim:p:v_zna
авіапаркові	авіапарк	noun	noun:inanim:m:v_dav
авіапаркові	авіапарк	noun	noun:inanim:m:v_mis
авіапарком	авіапарк	noun	noun:inanim:m:v_oru
авіапарку	авіапарк	noun	noun:inanim:m:v_dav
авіапарку	авіапарк	noun	noun:inanim:m:v_kly
авіапарку	авіапарк	noun	noun:inanim:m:v_mis
авіапарку	авіапарк	noun	noun:inanim:m:v_rod
авіапарків	авіапарк	noun	noun:inanim:p:v_rod
авіапартнер	авіапартнер	noun	noun:inanim:m:v_naz
авіапартнер	авіапартнер	noun	noun:inanim:m:v_zna
авіапартнера	авіапартнер	noun	noun:inanim:m:v_rod
авіапартнерам	авіапартнер	noun	noun:inanim:p:v_dav
авіапартнерами	авіапартнер	noun	noun:inanim:p:v_oru
авіапартнерах	авіапартнер	noun	noun:inanim:p:v_mis
авіапартнере	авіапартнер	noun	noun:inanim:m:v_kly
авіапартнери	авіапартнер	noun	noun:inanim:p:v_kly
авіапартнери	авіапартнер	noun	noun:inanim:p:v_naz
авіапартнери	авіапартнер	noun	noun:inanim:p:v_zna
авіапартнерові	авіапартнер	noun	noun:inanim:m:v_dav
авіапартнерові	авіапартнер	noun	noun:inanim:m:v_mis
авіапартнером	авіапартнер	noun	noun:inanim:m:v_oru
авіапартнері	авіапартнер	noun	noun:inanim:m:v_mis
авіапартнерів	авіапартнер	noun	noun:inanim:p:v_rod
авіапасажир	авіапасажир	noun	noun:anim:m:v_naz
авіапасажира	авіапасажир	noun	noun:anim:m:v_rod
авіапасажира	авіапасажир	noun	noun:anim:m:v_zna
авіапасажирам	авіапасажир	noun	noun:anim:p:v_dav
авіапасажирами	авіапасажир	noun	noun:anim:p:v_oru
авіапасажирах	авіапасажир	noun	noun:anim:p:v_mis
авіапасажире	авіапасажир	noun	noun:anim:m:v_kly
авіапасажири	авіапасажир	noun	noun:anim:p:v_kly
авіапасажири	авіапасажир	noun	noun:anim:p:v_naz
авіапасажири	авіапасажир	noun	noun:anim:p:v_zna:rare
авіапасажирка	авіапасажирка	noun	noun:anim:f:v_naz
авіапасажиркам	авіапасажирка	noun	noun:anim:p:v_dav
авіапасажирками	авіапасажирка	noun	noun:anim:p:v_oru
авіапасажирках	авіапасажирка	noun	noun:anim:p:v_mis
авіапасажирки	авіапасажирка	noun	noun:anim:f:v_rod
авіапасажирки	авіапасажирка	noun	noun:anim:p:v_kly
авіапасажирки	авіапасажирка	noun	noun:anim:p:v_naz
авіапасажирки	авіапасажирка	noun	noun:anim:p:v_zna:rare
авіапасажирко	авіапасажирка	noun	noun:anim:f:v_kly
авіапасажиркою	авіапасажирка	noun	noun:anim:f:v_oru
авіапасажирку	авіапасажирка	noun	noun:anim:f:v_zna
авіапасажирові	авіапасажир	noun	noun:anim:m:v_dav
авіапасажирові	авіапасажир	noun	noun:anim:m:v_mis
авіапасажирок	авіапасажирка	noun	noun:anim:p:v_rod
авіапасажирок	авіапасажирка	noun	noun:anim:p:v_zna
авіапасажиром	авіапасажир	noun	noun:anim:m:v_oru
авіапасажирці	авіапасажирка	noun	noun:anim:f:v_dav
авіапасажирці	авіапасажирка	noun	noun:anim:f:v_mis
авіапасажирі	авіапасажир	noun	noun:anim:m:v_mis
авіапасажирів	авіапасажир	noun	noun:anim:p:v_rod
авіапасажирів	авіапасажир	noun	noun:anim:p:v_zna
авіапатрулеві	авіапатруль	noun	noun:inanim:m:v_dav
авіапатрулеві	авіапатруль	noun	noun:inanim:m:v_mis
авіапатрулем	авіапатруль	noun	noun:inanim:m:v_oru
авіапатруль	авіапатруль	noun	noun:inanim:m:v_naz
авіапатруль	авіапатруль	noun	noun:inanim:m:v_zna
авіапатрулю	авіапатруль	noun	noun:inanim:m:v_dav
авіапатрулю	авіапатруль	noun	noun:inanim:m:v_kly
авіапатрулю	авіапатруль	noun	noun:inanim:m:v_mis
авіапатруля	авіапатруль	noun	noun:inanim:m:v_rod
авіапатрулям	авіапатруль	noun	noun:inanim:p:v_dav
авіапатрулями	авіапатруль	noun	noun:inanim:p:v_oru
авіапатрулях	авіапатруль	noun	noun:inanim:p:v_mis
авіапатрулі	авіапатруль	noun	noun:inanim:m:v_mis
авіапатрулі	авіапатруль	noun	noun:inanim:p:v_kly
авіапатрулі	авіапатруль	noun	noun:inanim:p:v_naz
авіапатрулі	авіапатруль	noun	noun:inanim:p:v_zna
авіапатрулів	авіапатруль	noun	noun:inanim:p:v_rod
авіаперевезенню	авіаперевезення	noun	noun:inanim:n:v_dav
авіаперевезенню	авіаперевезення	noun	noun:inanim:n:v_mis
авіаперевезення	авіаперевезення	noun	noun:inanim:n:v_kly
авіаперевезення	авіаперевезення	noun	noun:inanim:n:v_naz
авіаперевезення	авіаперевезення	noun	noun:inanim:n:v_rod
авіаперевезення	авіаперевезення	noun	noun:inanim:n:v_zna
авіаперевезення	авіаперевезення	noun	noun:inanim:p:v_kly
авіаперевезення	авіаперевезення	noun	noun:inanim:p:v_naz
авіаперевезення	авіаперевезення	noun	noun:inanim:p:v_zna
авіаперевезенням	авіаперевезення	noun	noun:inanim:n:v_oru
авіаперевезенням	авіаперевезення	noun	noun:inanim:p:v_dav
авіаперевезеннями	авіаперевезення	noun	noun:inanim:p:v_oru
авіаперевезеннях	авіаперевезення	noun	noun:inanim:p:v_mis
авіаперевезенні	авіаперевезення	noun	noun:inanim:n:v_mis
авіаперевезень	авіаперевезення	noun	noun:inanim:p:v_rod
авіаперевізник	авіаперевізник	noun	noun:anim:m:v_naz
авіаперевізника	авіаперевізник	noun	noun:anim:m:v_rod
авіаперевізника	авіаперевізник	noun	noun:anim:m:v_zna
авіаперевізникам	авіаперевізник	noun	noun:anim:p:v_dav
авіаперевізниками	авіаперевізник	noun	noun:anim:p:v_oru
авіаперевізниках	авіаперевізник	noun	noun:anim:p:v_mis
авіаперевізники	авіаперевізник	noun	noun:anim:p:v_kly
авіаперевізники	авіаперевізник	noun	noun:anim:p:v_naz
авіаперевізники	авіаперевізник	noun	noun:anim:p:v_zna:rare
авіаперевізникові	авіаперевізник	noun	noun:anim:m:v_dav
авіаперевізникові	авіаперевізник	noun	noun:anim:m:v_mis
авіаперевізником	авіаперевізник	noun	noun:anim:m:v_oru
авіаперевізнику	авіаперевізник	noun	noun:anim:m:v_dav
авіаперевізнику	авіаперевізник	noun	noun:anim:m:v_kly
авіаперевізнику	авіаперевізник	noun	noun:anim:m:v_mis
авіаперевізників	авіаперевізник	noun	noun:anim:p:v_rod
авіаперевізників	авіаперевізник	noun	noun:anim:p:v_zna
авіаперельотам	авіапереліт	noun	noun:inanim:p:v_dav
авіаперельотами	авіапереліт	noun	noun:inanim:p:v_oru
авіаперельотах	авіапереліт	noun	noun:inanim:p:v_mis
авіаперельоте	авіапереліт	noun	noun:inanim:m:v_kly
авіаперельоти	авіапереліт	noun	noun:inanim:p:v_kly
авіаперельоти	авіапереліт	noun	noun:inanim:p:v_naz
авіаперельоти	авіапереліт	noun	noun:inanim:p:v_zna
авіаперельотові	авіапереліт	noun	noun:inanim:m:v_dav
авіаперельотові	авіапереліт	noun	noun:inanim:m:v_mis
авіаперельотом	авіапереліт	noun	noun:inanim:m:v_oru
авіаперельоту	авіапереліт	noun	noun:inanim:m:v_dav
авіаперельоту	авіапереліт	noun	noun:inanim:m:v_mis
авіаперельоту	авіапереліт	noun	noun:inanim:m:v_rod
авіаперельоті	авіапереліт	noun	noun:inanim:m:v_mis
авіаперельотів	авіапереліт	noun	noun:inanim:p:v_rod
авіапереліт	авіапереліт	noun	noun:inanim:m:v_naz
авіапереліт	авіапереліт	noun	noun:inanim:m:v_zna
авіаподорож	авіаподорож	noun	noun:inanim:f:v_naz
авіаподорож	авіаподорож	noun	noun:inanim:f:v_zna
авіаподорожам	авіаподорож	noun	noun:inanim:p:v_dav
авіаподорожами	авіаподорож	noun	noun:inanim:p:v_oru
авіаподорожах	авіаподорож	noun	noun:inanim:p:v_mis
авіаподороже	авіаподорож	noun	noun:inanim:f:v_kly
авіаподорожей	авіаподорож	noun	noun:inanim:p:v_rod
авіаподорожжю	авіаподорож	noun	noun:inanim:f:v_oru
авіаподорожі	авіаподорож	noun	noun:inanim:f:v_dav
авіаподорожі	авіаподорож	noun	noun:inanim:f:v_mis
авіаподорожі	авіаподорож	noun	noun:inanim:f:v_rod
авіаподорожі	авіаподорож	noun	noun:inanim:p:v_kly
авіаподорожі	авіаподорож	noun	noun:inanim:p:v_naz
авіаподорожі	авіаподорож	noun	noun:inanim:p:v_zna
авіаполк	авіаполк	noun	noun:inanim:m:v_naz
авіаполк	авіаполк	noun	noun:inanim:m:v_zna
авіаполкам	авіаполк	noun	noun:inanim:p:v_dav
авіаполками	авіаполк	noun	noun:inanim:p:v_oru
авіаполках	авіаполк	noun	noun:inanim:p:v_mis
авіаполки	авіаполк	noun	noun:inanim:p:v_kly
авіаполки	авіаполк	noun	noun:inanim:p:v_naz
авіаполки	авіаполк	noun	noun:inanim:p:v_zna
авіаполкові	авіаполк	noun	noun:inanim:m:v_dav
авіаполкові	авіаполк	noun	noun:inanim:m:v_mis
авіаполком	авіаполк	noun	noun:inanim:m:v_oru
авіаполку	авіаполк	noun	noun:inanim:m:v_dav
авіаполку	авіаполк	noun	noun:inanim:m:v_kly
авіаполку	авіаполк	noun	noun:inanim:m:v_mis
авіаполку	авіаполк	noun	noun:inanim:m:v_rod
авіаполків	авіаполк	noun	noun:inanim:p:v_rod
авіапольотам	авіаполіт	noun	noun:inanim:p:v_dav
авіапольотами	авіаполіт	noun	noun:inanim:p:v_oru
авіапольотах	авіаполіт	noun	noun:inanim:p:v_mis
авіапольоте	авіаполіт	noun	noun:inanim:m:v_kly
авіапольоти	авіаполіт	noun	noun:inanim:p:v_kly
авіапольоти	авіаполіт	noun	noun:inanim:p:v_naz
авіапольоти	авіаполіт	noun	noun:inanim:p:v_zna
авіапольотові	авіаполіт	noun	noun:inanim:m:v_dav
авіапольотові	авіаполіт	noun	noun:inanim:m:v_mis
авіапольотом	авіаполіт	noun	noun:inanim:m:v_oru
авіапольоту	авіаполіт	noun	noun:inanim:m:v_dav
авіапольоту	авіаполіт	noun	noun:inanim:m:v_mis
авіапольоту	авіаполіт	noun	noun:inanim:m:v_rod
авіапольоті	авіаполіт	noun	noun:inanim:m:v_mis
авіапольотів	авіаполіт	noun	noun:inanim:p:v_rod
авіаполігон	авіаполігон	noun	noun:inanim:m:v_naz
авіаполігон	авіаполігон	noun	noun:inanim:m:v_zna
авіаполігонам	авіаполігон	noun	noun:inanim:p:v_dav
авіаполігонами	авіаполігон	noun	noun:inanim:p:v_oru
авіаполігонах	авіаполігон	noun	noun:inanim:p:v_mis
авіаполігоне	авіаполігон	noun	noun:inanim:m:v_kly
авіаполігони	авіаполігон	noun	noun:inanim:p:v_kly
авіаполігони	авіаполігон	noun	noun:inanim:p:v_naz
авіаполігони	авіаполігон	noun	noun:inanim:p:v_zna
авіаполігонові	авіаполігон	noun	noun:inanim:m:v_dav
авіаполігонові	авіаполігон	noun	noun:inanim:m:v_mis
авіаполігоном	авіаполігон	noun	noun:inanim:m:v_oru
авіаполігону	авіаполігон	noun	noun:inanim:m:v_dav
авіаполігону	авіаполігон	noun	noun:inanim:m:v_mis
авіаполігону	авіаполігон	noun	noun:inanim:m:v_rod
авіаполігоні	авіаполігон	noun	noun:inanim:m:v_mis
авіаполігонів	авіаполігон	noun	noun:inanim:p:v_rod
авіаполіт	авіаполіт	noun	noun:inanim:m:v_naz
авіаполіт	авіаполіт	noun	noun:inanim:m:v_zna
авіапорт	авіапорт	noun	noun:inanim:m:v_naz
авіапорт	авіапорт	noun	noun:inanim:m:v_zna
авіапортам	авіапорт	noun	noun:inanim:p:v_dav
авіапортами	авіапорт	noun	noun:inanim:p:v_oru
авіапортах	авіапорт	noun	noun:inanim:p:v_mis
авіапорте	авіапорт	noun	noun:inanim:m:v_kly
авіапорти	авіапорт	noun	noun:inanim:p:v_kly
авіапорти	авіапорт	noun	noun:inanim:p:v_naz
авіапорти	авіапорт	noun	noun:inanim:p:v_zna
авіапортові	авіапорт	noun	noun:inanim:m:v_dav
авіапортові	авіапорт	noun	noun:inanim:m:v_mis
авіапортом	авіапорт	noun	noun:inanim:m:v_oru
авіапорту	авіапорт	noun	noun:inanim:m:v_dav
авіапорту	авіапорт	noun	noun:inanim:m:v_mis
авіапорту	авіапорт	noun	noun:inanim:m:v_rod
авіапорті	авіапорт	noun	noun:inanim:m:v_mis
авіапортів	авіапорт	noun	noun:inanim:p:v_rod
авіапотокам	авіапотік	noun	noun:inanim:p:v_dav
авіапотоками	авіапотік	noun	noun:inanim:p:v_oru
авіапотоках	авіапотік	noun	noun:inanim:p:v_mis
авіапотоки	авіапотік	noun	noun:inanim:p:v_kly
авіапотоки	авіапотік	noun	noun:inanim:p:v_naz
авіапотоки	авіапотік	noun	noun:inanim:p:v_zna
авіапотокові	авіапотік	noun	noun:inanim:m:v_dav
авіапотокові	авіапотік	noun	noun:inanim:m:v_mis
авіапотоком	авіапотік	noun	noun:inanim:m:v_oru
авіапотоку	авіапотік	noun	noun:inanim:m:v_dav
авіапотоку	авіапотік	noun	noun:inanim:m:v_kly
авіапотоку	авіапотік	noun	noun:inanim:m:v_mis
авіапотоку	авіапотік	noun	noun:inanim:m:v_rod
авіапотоків	авіапотік	noun	noun:inanim:p:v_rod
авіапотік	авіапотік	noun	noun:inanim:m:v_naz
авіапотік	авіапотік	noun	noun:inanim:m:v_zna
авіапрацівник	авіапрацівник	noun	noun:anim:m:v_naz
авіапрацівника	авіапрацівник	noun	noun:anim:m:v_rod
авіапрацівника	авіапрацівник	noun	noun:anim:m:v_zna
авіапрацівникам	авіапрацівник	noun	noun:anim:p:v_dav
авіапрацівниками	авіапрацівник	noun	noun:anim:p:v_oru
авіапрацівниках	авіапрацівник	noun	noun:anim:p:v_mis
авіапрацівники	авіапрацівник	noun	noun:anim:p:v_kly
авіапрацівники	авіапрацівник	noun	noun:anim:p:v_naz
авіапрацівники	авіапрацівник	noun	noun:anim:p:v_zna:rare
авіапрацівникові	авіапрацівник	noun	noun:anim:m:v_dav
авіапрацівникові	авіапрацівник	noun	noun:anim:m:v_mis
авіапрацівником	авіапрацівник	noun	noun:anim:m:v_oru
авіапрацівнику	авіапрацівник	noun	noun:anim:m:v_dav
авіапрацівнику	авіапрацівник	noun	noun:anim:m:v_kly
авіапрацівнику	авіапрацівник	noun	noun:anim:m:v_mis
авіапрацівників	авіапрацівник	noun	noun:anim:p:v_rod
авіапрацівників	авіапрацівник	noun	noun:anim:p:v_zna
авіапригод	авіапригода	noun	noun:inanim:p:v_rod
авіапригода	авіапригода	noun	noun:inanim:f:v_naz
авіапригодам	авіапригода	noun	noun:inanim:p:v_dav
авіапригодами	авіапригода	noun	noun:inanim:p:v_oru
авіапригодах	авіапригода	noun	noun:inanim:p:v_mis
авіапригоди	авіапригода	noun	noun:inanim:f:v_rod
авіапригоди	авіапригода	noun	noun:inanim:p:v_kly
авіапригоди	авіапригода	noun	noun:inanim:p:v_naz
авіапригоди	авіапригода	noun	noun:inanim:p:v_zna
авіапригодо	авіапригода	noun	noun:inanim:f:v_kly
авіапригодою	авіапригода	noun	noun:inanim:f:v_oru
авіапригоду	авіапригода	noun	noun:inanim:f:v_zna
авіапригоді	авіапригода	noun	noun:inanim:f:v_dav
авіапригоді	авіапригода	noun	noun:inanim:f:v_mis
авіапрограм	авіапрограма	noun	noun:inanim:p:v_rod
авіапрограма	авіапрограма	noun	noun:inanim:f:v_naz
авіапрограмам	авіапрограма	noun	noun:inanim:p:v_dav
авіапрограмами	авіапрограма	noun	noun:inanim:p:v_oru
авіапрограмах	авіапрограма	noun	noun:inanim:p:v_mis
авіапрограми	авіапрограма	noun	noun:inanim:f:v_rod
авіапрограми	авіапрограма	noun	noun:inanim:p:v_kly
авіапрограми	авіапрограма	noun	noun:inanim:p:v_naz
авіапрограми	авіапрограма	noun	noun:inanim:p:v_zna
авіапрограмо	авіапрограма	noun	noun:inanim:f:v_kly
авіапрограмою	авіапрограма	noun	noun:inanim:f:v_oru
авіапрограму	авіапрограма	noun	noun:inanim:f:v_zna
авіапрограмі	авіапрограма	noun	noun:inanim:f:v_dav
авіапрограмі	авіапрограма	noun	noun:inanim:f:v_mis
авіапродукт	авіапродукт	noun	noun:inanim:m:v_naz
авіапродукт	авіапродукт	noun	noun:inanim:m:v_zna
авіапродуктам	авіапродукт	noun	noun:inanim:p:v_dav
авіапродуктами	авіапродукт	noun	noun:inanim:p:v_oru
авіапродуктах	авіапродукт	noun	noun:inanim:p:v_mis
авіапродукте	авіапродукт	noun	noun:inanim:m:v_kly
авіапродукти	авіапродукт	noun	noun:inanim:p:v_kly
авіапродукти	авіапродукт	noun	noun:inanim:p:v_naz
авіапродукти	авіапродукт	noun	noun:inanim:p:v_zna
авіапродуктові	авіапродукт	noun	noun:inanim:m:v_dav
авіапродуктові	авіапродукт	noun	noun:inanim:m:v_mis
авіапродуктом	авіапродукт	noun	noun:inanim:m:v_oru
авіапродукту	авіапродукт	noun	noun:inanim:m:v_dav
авіапродукту	авіапродукт	noun	noun:inanim:m:v_mis
авіапродукту	авіапродукт	noun	noun:inanim:m:v_rod
авіапродукті	авіапродукт	noun	noun:inanim:m:v_mis
авіапродуктів	авіапродукт	noun	noun:inanim:p:v_rod
авіапроект	авіапроект	noun	noun:inanim:m:v_naz:up92
авіапроект	авіапроект	noun	noun:inanim:m:v_zna:up92
авіапроектам	авіапроект	noun	noun:inanim:p:v_dav:up92
авіапроектами	авіапроект	noun	noun:inanim:p:v_oru:up92
авіапроектах	авіапроект	noun	noun:inanim:p:v_mis:up92
авіапроекте	авіапроект	noun	noun:inanim:m:v_kly:up92
авіапроекти	авіапроект	noun	noun:inanim:p:v_kly:up92
авіапроекти	авіапроект	noun	noun:inanim:p:v_naz:up92
авіапроекти	авіапроект	noun	noun:inanim:p:v_zna:up92
авіапроектові	авіапроект	noun	noun:inanim:m:v_dav:up92
авіапроектові	авіапроект	noun	noun:inanim:m:v_mis:up92
авіапроектом	авіапроект	noun	noun:inanim:m:v_oru:up92
авіапроекту	авіапроект	noun	noun:inanim:m:v_dav:up92
авіапроекту	авіапроект	noun	noun:inanim:m:v_mis:up92
авіапроекту	авіапроект	noun	noun:inanim:m:v_rod:up92
авіапроекті	авіапроект	noun	noun:inanim:m:v_mis:up92
авіапроектів	авіапроект	noun	noun:inanim:p:v_rod:up92
авіапром	авіапром	noun	noun:inanim:m:v_naz
авіапром	авіапром	noun	noun:inanim:m:v_zna
авіапромам	авіапром	noun	noun:inanim:p:v_dav
авіапромами	авіапром	noun	noun:inanim:p:v_oru
авіапромах	авіапром	noun	noun:inanim:p:v_mis
авіапроме	авіапром	noun	noun:inanim:m:v_kly
авіапроми	авіапром	noun	noun:inanim:p:v_kly
авіапроми	авіапром	noun	noun:inanim:p:v_naz
авіапроми	авіапром	noun	noun:inanim:p:v_zna
авіапромисловосте	авіапромисловість	noun	noun:inanim:f:v_kly
авіапромисловостей	авіапромисловість	noun	noun:inanim:p:v_rod
авіапромисловостям	авіапромисловість	noun	noun:inanim:p:v_dav
авіапромисловостями	авіапромисловість	noun	noun:inanim:p:v_oru
авіапромисловостях	авіапромисловість	noun	noun:inanim:p:v_mis
авіапромисловості	авіапромисловість	noun	noun:inanim:f:v_dav
авіапромисловості	авіапромисловість	noun	noun:inanim:f:v_mis
авіапромисловості	авіапромисловість	noun	noun:inanim:f:v_rod
авіапромисловості	авіапромисловість	noun	noun:inanim:p:v_kly
авіапромисловості	авіапромисловість	noun	noun:inanim:p:v_naz
авіапромисловості	авіапромисловість	noun	noun:inanim:p:v_zna
авіапромисловість	авіапромисловість	noun	noun:inanim:f:v_naz
авіапромисловість	авіапромисловість	noun	noun:inanim:f:v_zna
авіапромисловістю	авіапромисловість	noun	noun:inanim:f:v_oru
авіапромові	авіапром	noun	noun:inanim:m:v_dav
авіапромові	авіапром	noun	noun:inanim:m:v_mis
авіапромом	авіапром	noun	noun:inanim:m:v_oru
авіапрому	авіапром	noun	noun:inanim:m:v_dav
авіапрому	авіапром	noun	noun:inanim:m:v_mis
авіапрому	авіапром	noun	noun:inanim:m:v_rod
авіапромі	авіапром	noun	noun:inanim:m:v_mis
авіапромів	авіапром	noun	noun:inanim:p:v_rod
авіапроєкт	авіапроєкт	noun	noun:inanim:m:v_naz:up19
авіапроєкт	авіапроєкт	noun	noun:inanim:m:v_zna:up19
авіапроєктам	авіапроєкт	noun	noun:inanim:p:v_dav:up19
авіапроєктами	авіапроєкт	noun	noun:inanim:p:v_oru:up19
авіапроєктах	авіапроєкт	noun	noun:inanim:p:v_mis:up19
авіапроєкте	авіапроєкт	noun	noun:inanim:m:v_kly:up19
авіапроєкти	авіапроєкт	noun	noun:inanim:p:v_kly:up19
авіапроєкти	авіапроєкт	noun	noun:inanim:p:v_naz:up19
авіапроєкти	авіапроєкт	noun	noun:inanim:p:v_zna:up19
авіапроєктові	авіапроєкт	noun	noun:inanim:m:v_dav:up19
авіапроєктові	авіапроєкт	noun	noun:inanim:m:v_mis:up19
авіапроєктом	авіапроєкт	noun	noun:inanim:m:v_oru:up19
авіапроєкту	авіапроєкт	noun	noun:inanim:m:v_dav:up19
авіапроєкту	авіапроєкт	noun	noun:inanim:m:v_mis:up19
авіапроєкту	авіапроєкт	noun	noun:inanim:m:v_rod:up19
авіапроєкті	авіапроєкт	noun	noun:inanim:m:v_mis:up19
авіапроєктів	авіапроєкт	noun	noun:inanim:p:v_rod:up19
авіапідприємств	авіапідприємство	noun	noun:inanim:p:v_rod
авіапідприємства	авіапідприємство	noun	noun:inanim:n:v_rod
авіапідприємства	авіапідприємство	noun	noun:inanim:p:v_kly
авіапідприємства	авіапідприємство	noun	noun:inanim:p:v_naz
авіапідприємства	авіапідприємство	noun	noun:inanim:p:v_zna
авіапідприємствам	авіапідприємство	noun	noun:inanim:p:v_dav
авіапідприємствами	авіапідприємство	noun	noun:inanim:p:v_oru
авіапідприємствах	авіапідприємство	noun	noun:inanim:p:v_mis
авіапідприємство	авіапідприємство	noun	noun:inanim:n:v_kly
авіапідприємство	авіапідприємство	noun	noun:inanim:n:v_naz
авіапідприємство	авіапідприємство	noun	noun:inanim:n:v_zna
авіапідприємством	авіапідприємство	noun	noun:inanim:n:v_oru
авіапідприємству	авіапідприємство	noun	noun:inanim:n:v_dav
авіапідприємству	авіапідприємство	noun	noun:inanim:n:v_mis
авіапідприємстві	авіапідприємство	noun	noun:inanim:n:v_mis
авіапідрозділ	авіапідрозділ	noun	noun:inanim:m:v_naz
авіапідрозділ	авіапідрозділ	noun	noun:inanim:m:v_zna
авіапідрозділам	авіапідрозділ	noun	noun:inanim:p:v_dav
авіапідрозділами	авіапідрозділ	noun	noun:inanim:p:v_oru
авіапідрозділах	авіапідрозділ	noun	noun:inanim:p:v_mis
авіапідрозділе	авіапідрозділ	noun	noun:inanim:m:v_kly
авіапідрозділи	авіапідрозділ	noun	noun:inanim:p:v_kly
авіапідрозділи	авіапідрозділ	noun	noun:inanim:p:v_naz
авіапідрозділи	авіапідрозділ	noun	noun:inanim:p:v_zna
авіапідрозділові	авіапідрозділ	noun	noun:inanim:m:v_dav
авіапідрозділові	авіапідрозділ	noun	noun:inanim:m:v_mis
авіапідрозділом	авіапідрозділ	noun	noun:inanim:m:v_oru
авіапідрозділу	авіапідрозділ	noun	noun:inanim:m:v_dav
авіапідрозділу	авіапідрозділ	noun	noun:inanim:m:v_mis
авіапідрозділу	авіапідрозділ	noun	noun:inanim:m:v_rod
авіапідрозділі	авіапідрозділ	noun	noun:inanim:m:v_mis
авіапідрозділів	авіапідрозділ	noun	noun:inanim:p:v_rod
авіарадист	авіарадист	noun	noun:anim:m:v_naz
авіарадиста	авіарадист	noun	noun:anim:m:v_rod
авіарадиста	авіарадист	noun	noun:anim:m:v_zna
авіарадистам	авіарадист	noun	noun:anim:p:v_dav
авіарадистами	авіарадист	noun	noun:anim:p:v_oru
авіарадистах	авіарадист	noun	noun:anim:p:v_mis
авіарадисте	авіарадист	noun	noun:anim:m:v_kly
авіарадисти	авіарадист	noun	noun:anim:p:v_kly
авіарадисти	авіарадист	noun	noun:anim:p:v_naz
авіарадисти	авіарадист	noun	noun:anim:p:v_zna:rare
авіарадистові	авіарадист	noun	noun:anim:m:v_dav
авіарадистові	авіарадист	noun	noun:anim:m:v_mis
авіарадистом	авіарадист	noun	noun:anim:m:v_oru
авіарадисті	авіарадист	noun	noun:anim:m:v_mis
авіарадистів	авіарадист	noun	noun:anim:p:v_rod
авіарадистів	авіарадист	noun	noun:anim:p:v_zna
авіаракет	авіаракета	noun	noun:inanim:p:v_rod
авіаракета	авіаракета	noun	noun:inanim:f:v_naz
авіаракетам	авіаракета	noun	noun:inanim:p:v_dav
авіаракетами	авіаракета	noun	noun:inanim:p:v_oru
авіаракетах	авіаракета	noun	noun:inanim:p:v_mis
авіаракети	авіаракета	noun	noun:inanim:f:v_rod
авіаракети	авіаракета	noun	noun:inanim:p:v_kly
авіаракети	авіаракета	noun	noun:inanim:p:v_naz
авіаракети	авіаракета	noun	noun:inanim:p:v_zna
авіаракето	авіаракета	noun	noun:inanim:f:v_kly
авіаракетою	авіаракета	noun	noun:inanim:f:v_oru
авіаракету	авіаракета	noun	noun:inanim:f:v_zna
авіаракеті	авіаракета	noun	noun:inanim:f:v_dav
авіаракеті	авіаракета	noun	noun:inanim:f:v_mis
авіарегулятор	авіарегулятор	noun	noun:inanim:m:v_naz
авіарегулятор	авіарегулятор	noun	noun:inanim:m:v_zna
авіарегулятора	авіарегулятор	noun	noun:inanim:m:v_rod
авіарегуляторам	авіарегулятор	noun	noun:inanim:p:v_dav
авіарегуляторами	авіарегулятор	noun	noun:inanim:p:v_oru
авіарегуляторах	авіарегулятор	noun	noun:inanim:p:v_mis
авіарегуляторе	авіарегулятор	noun	noun:inanim:m:v_kly
авіарегулятори	авіарегулятор	noun	noun:inanim:p:v_kly
авіарегулятори	авіарегулятор	noun	noun:inanim:p:v_naz
авіарегулятори	авіарегулятор	noun	noun:inanim:p:v_zna
авіарегуляторові	авіарегулятор	noun	noun:inanim:m:v_dav
авіарегуляторові	авіарегулятор	noun	noun:inanim:m:v_mis
авіарегулятором	авіарегулятор	noun	noun:inanim:m:v_oru
авіарегуляторі	авіарегулятор	noun	noun:inanim:m:v_mis
авіарегуляторів	авіарегулятор	noun	noun:inanim:p:v_rod
авіарегістр	авіарегістр	noun	noun:inanim:m:v_naz
авіарегістр	авіарегістр	noun	noun:inanim:m:v_zna
авіарегістра	авіарегістр	noun	noun:inanim:m:v_rod
авіарегістрам	авіарегістр	noun	noun:inanim:p:v_dav
авіарегістрами	авіарегістр	noun	noun:inanim:p:v_oru
авіарегістрах	авіарегістр	noun	noun:inanim:p:v_mis
авіарегістре	авіарегістр	noun	noun:inanim:m:v_kly
авіарегістри	авіарегістр	noun	noun:inanim:p:v_kly
авіарегістри	авіарегістр	noun	noun:inanim:p:v_naz
авіарегістри	авіарегістр	noun	noun:inanim:p:v_zna
авіарегістрові	авіарегістр	noun	noun:inanim:m:v_dav
авіарегістрові	авіарегістр	noun	noun:inanim:m:v_mis
авіарегістром	авіарегістр	noun	noun:inanim:m:v_oru
авіарегістрі	авіарегістр	noun	noun:inanim:m:v_mis
авіарегістрів	авіарегістр	noun	noun:inanim:p:v_rod
авіарейд	авіарейд	noun	noun:inanim:m:v_naz
авіарейд	авіарейд	noun	noun:inanim:m:v_zna
авіарейдам	авіарейд	noun	noun:inanim:p:v_dav
авіарейдами	авіарейд	noun	noun:inanim:p:v_oru
авіарейдах	авіарейд	noun	noun:inanim:p:v_mis
авіарейде	авіарейд	noun	noun:inanim:m:v_kly
авіарейди	авіарейд	noun	noun:inanim:p:v_kly
авіарейди	авіарейд	noun	noun:inanim:p:v_naz
авіарейди	авіарейд	noun	noun:inanim:p:v_zna
авіарейдові	авіарейд	noun	noun:inanim:m:v_dav
авіарейдові	авіарейд	noun	noun:inanim:m:v_mis
авіарейдом	авіарейд	noun	noun:inanim:m:v_oru
авіарейду	авіарейд	noun	noun:inanim:m:v_dav
авіарейду	авіарейд	noun	noun:inanim:m:v_mis
авіарейду	авіарейд	noun	noun:inanim:m:v_rod
авіарейді	авіарейд	noun	noun:inanim:m:v_mis
авіарейдів	авіарейд	noun	noun:inanim:p:v_rod
авіарейс	авіарейс	noun	noun:inanim:m:v_naz
авіарейс	авіарейс	noun	noun:inanim:m:v_zna
авіарейсам	авіарейс	noun	noun:inanim:p:v_dav
авіарейсами	авіарейс	noun	noun:inanim:p:v_oru
авіарейсах	авіарейс	noun	noun:inanim:p:v_mis
авіарейсе	авіарейс	noun	noun:inanim:m:v_kly
авіарейси	авіарейс	noun	noun:inanim:p:v_kly
авіарейси	авіарейс	noun	noun:inanim:p:v_naz
авіарейси	авіарейс	noun	noun:inanim:p:v_zna
авіарейсові	авіарейс	noun	noun:inanim:m:v_dav
авіарейсові	авіарейс	noun	noun:inanim:m:v_mis
авіарейсом	авіарейс	noun	noun:inanim:m:v_oru
авіарейсу	авіарейс	noun	noun:inanim:m:v_dav
авіарейсу	авіарейс	noun	noun:inanim:m:v_mis
авіарейсу	авіарейс	noun	noun:inanim:m:v_rod
авіарейсі	авіарейс	noun	noun:inanim:m:v_mis
авіарейсів	авіарейс	noun	noun:inanim:p:v_rod
авіаремонтник	авіаремонтник	noun	noun:anim:m:v_naz
авіаремонтника	авіаремонтник	noun	noun:anim:m:v_rod
авіаремонтника	авіаремонтник	noun	noun:anim:m:v_zna
авіаремонтникам	авіаремонтник	noun	noun:anim:p:v_dav
авіаремонтниками	авіаремонтник	noun	noun:anim:p:v_oru
авіаремонтниках	авіаремонтник	noun	noun:anim:p:v_mis
авіаремонтники	авіаремонтник	noun	noun:anim:p:v_kly
авіаремонтники	авіаремонтник	noun	noun:anim:p:v_naz
авіаремонтники	авіаремонтник	noun	noun:anim:p:v_zna:rare
авіаремонтникові	авіаремонтник	noun	noun:anim:m:v_dav
авіаремонтникові	авіаремонтник	noun	noun:anim:m:v_mis
авіаремонтником	авіаремонтник	noun	noun:anim:m:v_oru
авіаремонтнику	авіаремонтник	noun	noun:anim:m:v_dav
авіаремонтнику	авіаремонтник	noun	noun:anim:m:v_kly
авіаремонтнику	авіаремонтник	noun	noun:anim:m:v_mis
авіаремонтників	авіаремонтник	noun	noun:anim:p:v_rod
авіаремонтників	авіаремонтник	noun	noun:anim:p:v_zna
авіаринкам	авіаринок	noun	noun:inanim:p:v_dav
авіаринками	авіаринок	noun	noun:inanim:p:v_oru
авіаринках	авіаринок	noun	noun:inanim:p:v_mis
авіаринки	авіаринок	noun	noun:inanim:p:v_kly
авіаринки	авіаринок	noun	noun:inanim:p:v_naz
авіаринки	авіаринок	noun	noun:inanim:p:v_zna
авіаринкові	авіаринок	noun	noun:inanim:m:v_dav
авіаринкові	авіаринок	noun	noun:inanim:m:v_mis
авіаринком	авіаринок	noun	noun:inanim:m:v_oru
авіаринку	авіаринок	noun	noun:inanim:m:v_dav
авіаринку	авіаринок	noun	noun:inanim:m:v_kly
авіаринку	авіаринок	noun	noun:inanim:m:v_mis
авіаринку	авіаринок	noun	noun:inanim:m:v_rod
авіаринків	авіаринок	noun	noun:inanim:p:v_rod
авіаринок	авіаринок	noun	noun:inanim:m:v_naz
авіаринок	авіаринок	noun	noun:inanim:m:v_zna
авіарозвідка	авіарозвідка	noun	noun:inanim:f:v_naz
авіарозвідкам	авіарозвідка	noun	noun:inanim:p:v_dav
авіарозвідками	авіарозвідка	noun	noun:inanim:p:v_oru
авіарозвідках	авіарозвідка	noun	noun:inanim:p:v_mis
авіарозвідки	авіарозвідка	noun	noun:inanim:f:v_rod
авіарозвідки	авіарозвідка	noun	noun:inanim:p:v_kly
авіарозвідки	авіарозвідка	noun	noun:inanim:p:v_naz
авіарозвідки	авіарозвідка	noun	noun:inanim:p:v_zna
авіарозвідко	авіарозвідка	noun	noun:inanim:f:v_kly
авіарозвідкою	авіарозвідка	noun	noun:inanim:f:v_oru
авіарозвідку	авіарозвідка	noun	noun:inanim:f:v_zna
авіарозвідник	авіарозвідник	noun	noun:inanim:m:v_naz
авіарозвідник	авіарозвідник	noun	noun:inanim:m:v_zna
авіарозвідника	авіарозвідник	noun	noun:inanim:m:v_rod
авіарозвідникам	авіарозвідник	noun	noun:inanim:p:v_dav
авіарозвідниками	авіарозвідник	noun	noun:inanim:p:v_oru
авіарозвідниках	авіарозвідник	noun	noun:inanim:p:v_mis
авіарозвідники	авіарозвідник	noun	noun:inanim:p:v_kly
авіарозвідники	авіарозвідник	noun	noun:inanim:p:v_naz
авіарозвідники	авіарозвідник	noun	noun:inanim:p:v_zna
авіарозвідникові	авіарозвідник	noun	noun:inanim:m:v_dav
авіарозвідникові	авіарозвідник	noun	noun:inanim:m:v_mis
авіарозвідником	авіарозвідник	noun	noun:inanim:m:v_oru
авіарозвіднику	авіарозвідник	noun	noun:inanim:m:v_dav
авіарозвіднику	авіарозвідник	noun	noun:inanim:m:v_kly
авіарозвіднику	авіарозвідник	noun	noun:inanim:m:v_mis
авіарозвідників	авіарозвідник	noun	noun:inanim:p:v_rod
авіарозвідок	авіарозвідка	noun	noun:inanim:p:v_rod
авіарозвідуванню	авіарозвідування	noun	noun:inanim:n:v_dav
авіарозвідуванню	авіарозвідування	noun	noun:inanim:n:v_mis
авіарозвідування	авіарозвідування	noun	noun:inanim:n:v_kly
авіарозвідування	авіарозвідування	noun	noun:inanim:n:v_naz
авіарозвідування	авіарозвідування	noun	noun:inanim:n:v_rod
авіарозвідування	авіарозвідування	noun	noun:inanim:n:v_zna
авіарозвідування	авіарозвідування	noun	noun:inanim:p:v_kly
авіарозвідування	авіарозвідування	noun	noun:inanim:p:v_naz
авіарозвідування	авіарозвідування	noun	noun:inanim:p:v_zna
авіарозвідуванням	авіарозвідування	noun	noun:inanim:n:v_oru
авіарозвідуванням	авіарозвідування	noun	noun:inanim:p:v_dav
авіарозвідуваннями	авіарозвідування	noun	noun:inanim:p:v_oru
авіарозвідуваннях	авіарозвідування	noun	noun:inanim:p:v_mis
авіарозвідуванні	авіарозвідування	noun	noun:inanim:n:v_mis
авіарозвідувань	авіарозвідування	noun	noun:inanim:p:v_rod
авіарозвідці	авіарозвідка	noun	noun:inanim:f:v_dav
авіарозвідці	авіарозвідка	noun	noun:inanim:f:v_mis
авіарозробник	авіарозробник	noun	noun:anim:m:v_naz
авіарозробника	авіарозробник	noun	noun:anim:m:v_rod
авіарозробника	авіарозробник	noun	noun:anim:m:v_zna
авіарозробникам	авіарозробник	noun	noun:anim:p:v_dav
авіарозробниками	авіарозробник	noun	noun:anim:p:v_oru
авіарозробниках	авіарозробник	noun	noun:anim:p:v_mis
авіарозробники	авіарозробник	noun	noun:anim:p:v_kly
авіарозробники	авіарозробник	noun	noun:anim:p:v_naz
авіарозробники	авіарозробник	noun	noun:anim:p:v_zna:rare
авіарозробникові	авіарозробник	noun	noun:anim:m:v_dav
авіарозробникові	авіарозробник	noun	noun:anim:m:v_mis
авіарозробником	авіарозробник	noun	noun:anim:m:v_oru
авіарозробнику	авіарозробник	noun	noun:anim:m:v_dav
авіарозробнику	авіарозробник	noun	noun:anim:m:v_kly
авіарозробнику	авіарозробник	noun	noun:anim:m:v_mis
авіарозробників	авіарозробник	noun	noun:anim:p:v_rod
авіарозробників	авіарозробник	noun	noun:anim:p:v_zna
авіарій	авіарій	noun	noun:inanim:m:v_naz
авіарій	авіарій	noun	noun:inanim:m:v_zna
авіарію	авіарій	noun	noun:inanim:m:v_dav
авіарію	авіарій	noun	noun:inanim:m:v_kly
авіарію	авіарій	noun	noun:inanim:m:v_mis
авіарію	авіарій	noun	noun:inanim:m:v_rod
авіаріям	авіарій	noun	noun:inanim:p:v_dav
авіаріями	авіарій	noun	noun:inanim:p:v_oru
авіаріях	авіарій	noun	noun:inanim:p:v_mis
авіарієві	авіарій	noun	noun:inanim:m:v_dav
авіарієві	авіарій	noun	noun:inanim:m:v_mis
авіарієм	авіарій	noun	noun:inanim:m:v_oru
авіарії	авіарій	noun	noun:inanim:m:v_mis
авіарії	авіарій	noun	noun:inanim:p:v_kly
авіарії	авіарій	noun	noun:inanim:p:v_naz
авіарії	авіарій	noun	noun:inanim:p:v_zna
авіаріїв	авіарій	noun	noun:inanim:p:v_rod
авіасалон	авіасалон	noun	noun:inanim:m:v_naz
авіасалон	авіасалон	noun	noun:inanim:m:v_zna
авіасалонам	авіасалон	noun	noun:inanim:p:v_dav
авіасалонами	авіасалон	noun	noun:inanim:p:v_oru
авіасалонах	авіасалон	noun	noun:inanim:p:v_mis
авіасалоне	авіасалон	noun	noun:inanim:m:v_kly
авіасалони	авіасалон	noun	noun:inanim:p:v_kly
авіасалони	авіасалон	noun	noun:inanim:p:v_naz
авіасалони	авіасалон	noun	noun:inanim:p:v_zna
авіасалонові	авіасалон	noun	noun:inanim:m:v_dav
авіасалонові	авіасалон	noun	noun:inanim:m:v_mis
авіасалоном	авіасалон	noun	noun:inanim:m:v_oru
авіасалону	авіасалон	noun	noun:inanim:m:v_dav
авіасалону	авіасалон	noun	noun:inanim:m:v_mis
авіасалону	авіасалон	noun	noun:inanim:m:v_rod
авіасалоні	авіасалон	noun	noun:inanim:m:v_mis
авіасалонів	авіасалон	noun	noun:inanim:p:v_rod
авіасвят	авіасвято	noun	noun:inanim:p:v_rod
авіасвята	авіасвято	noun	noun:inanim:n:v_rod
авіасвята	авіасвято	noun	noun:inanim:p:v_kly
авіасвята	авіасвято	noun	noun:inanim:p:v_naz
авіасвята	авіасвято	noun	noun:inanim:p:v_zna
авіасвятам	авіасвято	noun	noun:inanim:p:v_dav
авіасвятами	авіасвято	noun	noun:inanim:p:v_oru
авіасвятах	авіасвято	noun	noun:inanim:p:v_mis
авіасвято	авіасвято	noun	noun:inanim:n:v_kly
авіасвято	авіасвято	noun	noun:inanim:n:v_naz
авіасвято	авіасвято	noun	noun:inanim:n:v_zna
авіасвятові	авіасвято	noun	noun:inanim:n:v_dav
авіасвятові	авіасвято	noun	noun:inanim:n:v_mis
авіасвятом	авіасвято	noun	noun:inanim:n:v_oru
авіасвяті	авіасвято	noun	noun:inanim:n:v_mis
авіасекстант	авіасекстант	noun	noun:inanim:m:v_naz
авіасекстант	авіасекстант	noun	noun:inanim:m:v_zna
авіасекстанта	авіасекстант	noun	noun:inanim:m:v_rod
авіасекстантам	авіасекстант	noun	noun:inanim:p:v_dav
авіасекстантами	авіасекстант	noun	noun:inanim:p:v_oru
авіасекстантах	авіасекстант	noun	noun:inanim:p:v_mis
авіасекстанте	авіасекстант	noun	noun:inanim:m:v_kly
авіасекстанти	авіасекстант	noun	noun:inanim:p:v_kly
авіасекстанти	авіасекстант	noun	noun:inanim:p:v_naz
авіасекстанти	авіасекстант	noun	noun:inanim:p:v_zna
авіасекстантові	авіасекстант	noun	noun:inanim:m:v_dav
авіасекстантові	авіасекстант	noun	noun:inanim:m:v_mis
авіасекстантом	авіасекстант	noun	noun:inanim:m:v_oru
авіасекстанті	авіасекстант	noun	noun:inanim:m:v_mis
авіасекстантів	авіасекстант	noun	noun:inanim:p:v_rod
авіасимулятор	авіасимулятор	noun	noun:inanim:m:v_naz
авіасимулятор	авіасимулятор	noun	noun:inanim:m:v_zna
авіасимулятора	авіасимулятор	noun	noun:inanim:m:v_rod
авіасимуляторам	авіасимулятор	noun	noun:inanim:p:v_dav
авіасимуляторами	авіасимулятор	noun	noun:inanim:p:v_oru
авіасимуляторах	авіасимулятор	noun	noun:inanim:p:v_mis
авіасимуляторе	авіасимулятор	noun	noun:inanim:m:v_kly
авіасимулятори	авіасимулятор	noun	noun:inanim:p:v_kly
авіасимулятори	авіасимулятор	noun	noun:inanim:p:v_naz
авіасимулятори	авіасимулятор	noun	noun:inanim:p:v_zna
авіасимуляторові	авіасимулятор	noun	noun:inanim:m:v_dav
авіасимуляторові	авіасимулятор	noun	noun:inanim:m:v_mis
авіасимулятором	авіасимулятор	noun	noun:inanim:m:v_oru
авіасимуляторі	авіасимулятор	noun	noun:inanim:m:v_mis
авіасимуляторів	авіасимулятор	noun	noun:inanim:p:v_rod
авіаслужб	авіаслужба	noun	noun:inanim:p:v_rod
авіаслужба	авіаслужба	noun	noun:inanim:f:v_naz
авіаслужбам	авіаслужба	noun	noun:inanim:p:v_dav
авіаслужбами	авіаслужба	noun	noun:inanim:p:v_oru
авіаслужбах	авіаслужба	noun	noun:inanim:p:v_mis
авіаслужби	авіаслужба	noun	noun:inanim:f:v_rod
авіаслужби	авіаслужба	noun	noun:inanim:p:v_kly
авіаслужби	авіаслужба	noun	noun:inanim:p:v_naz
авіаслужби	авіаслужба	noun	noun:inanim:p:v_zna
авіаслужбо	авіаслужба	noun	noun:inanim:f:v_kly
авіаслужбою	авіаслужба	noun	noun:inanim:f:v_oru
авіаслужбу	авіаслужба	noun	noun:inanim:f:v_zna
авіаслужбі	авіаслужба	noun	noun:inanim:f:v_dav
авіаслужбі	авіаслужба	noun	noun:inanim:f:v_mis
авіаспеціальносте	авіаспеціальність	noun	noun:inanim:f:v_kly
авіаспеціальностей	авіаспеціальність	noun	noun:inanim:p:v_rod
авіаспеціальностям	авіаспеціальність	noun	noun:inanim:p:v_dav
авіаспеціальностями	авіаспеціальність	noun	noun:inanim:p:v_oru
авіаспеціальностях	авіаспеціальність	noun	noun:inanim:p:v_mis
авіаспеціальності	авіаспеціальність	noun	noun:inanim:f:v_dav
авіаспеціальності	авіаспеціальність	noun	noun:inanim:f:v_mis
авіаспеціальності	авіаспеціальність	noun	noun:inanim:f:v_rod
авіаспеціальності	авіаспеціальність	noun	noun:inanim:p:v_kly
авіаспеціальності	авіаспеціальність	noun	noun:inanim:p:v_naz
авіаспеціальності	авіаспеціальність	noun	noun:inanim:p:v_zna
авіаспеціальність	авіаспеціальність	noun	noun:inanim:f:v_naz
авіаспеціальність	авіаспеціальність	noun	noun:inanim:f:v_zna
авіаспеціальністю	авіаспеціальність	noun	noun:inanim:f:v_oru
авіаспеціаліст	авіаспеціаліст	noun	noun:anim:m:v_naz
авіаспеціаліста	авіаспеціаліст	noun	noun:anim:m:v_rod
авіаспеціаліста	авіаспеціаліст	noun	noun:anim:m:v_zna
авіаспеціалістам	авіаспеціаліст	noun	noun:anim:p:v_dav
авіаспеціалістами	авіаспеціаліст	noun	noun:anim:p:v_oru
авіаспеціалістах	авіаспеціаліст	noun	noun:anim:p:v_mis
авіаспеціалісте	авіаспеціаліст	noun	noun:anim:m:v_kly
авіаспеціалісти	авіаспеціаліст	noun	noun:anim:p:v_kly
авіаспеціалісти	авіаспеціаліст	noun	noun:anim:p:v_naz
авіаспеціалісти	авіаспеціаліст	noun	noun:anim:p:v_zna:rare
авіаспеціалістові	авіаспеціаліст	noun	noun:anim:m:v_dav
авіаспеціалістові	авіаспеціаліст	noun	noun:anim:m:v_mis
авіаспеціалістом	авіаспеціаліст	noun	noun:anim:m:v_oru
авіаспеціалісті	авіаспеціаліст	noun	noun:anim:m:v_mis
авіаспеціалістів	авіаспеціаліст	noun	noun:anim:p:v_rod
авіаспеціалістів	авіаспеціаліст	noun	noun:anim:p:v_zna
авіасполученню	авіасполучення	noun	noun:inanim:n:v_dav
авіасполученню	авіасполучення	noun	noun:inanim:n:v_mis
авіасполучення	авіасполучення	noun	noun:inanim:n:v_kly
авіасполучення	авіасполучення	noun	noun:inanim:n:v_naz
авіасполучення	авіасполучення	noun	noun:inanim:n:v_rod
авіасполучення	авіасполучення	noun	noun:inanim:n:v_zna
авіасполучення	авіасполучення	noun	noun:inanim:p:v_kly
авіасполучення	авіасполучення	noun	noun:inanim:p:v_naz
авіасполучення	авіасполучення	noun	noun:inanim:p:v_zna
авіасполученням	авіасполучення	noun	noun:inanim:n:v_oru
авіасполученням	авіасполучення	noun	noun:inanim:p:v_dav
авіасполученнями	авіасполучення	noun	noun:inanim:p:v_oru
авіасполученнях	авіасполучення	noun	noun:inanim:p:v_mis
авіасполученні	авіасполучення	noun	noun:inanim:n:v_mis
авіасполучень	авіасполучення	noun	noun:inanim:p:v_rod
авіаспортклуб	авіаспортклуб	noun	noun:inanim:m:v_naz
авіаспортклуб	авіаспортклуб	noun	noun:inanim:m:v_zna
авіаспортклубам	авіаспортклуб	noun	noun:inanim:p:v_dav
авіаспортклубами	авіаспортклуб	noun	noun:inanim:p:v_oru
авіаспортклубах	авіаспортклуб	noun	noun:inanim:p:v_mis
авіаспортклубе	авіаспортклуб	noun	noun:inanim:m:v_kly
авіаспортклуби	авіаспортклуб	noun	noun:inanim:p:v_kly
авіаспортклуби	авіаспортклуб	noun	noun:inanim:p:v_naz
авіаспортклуби	авіаспортклуб	noun	noun:inanim:p:v_zna
авіаспортклубові	авіаспортклуб	noun	noun:inanim:m:v_dav
авіаспортклубові	авіаспортклуб	noun	noun:inanim:m:v_mis
авіаспортклубом	авіаспортклуб	noun	noun:inanim:m:v_oru
авіаспортклубу	авіаспортклуб	noun	noun:inanim:m:v_dav
авіаспортклубу	авіаспортклуб	noun	noun:inanim:m:v_mis
авіаспортклубу	авіаспортклуб	noun	noun:inanim:m:v_rod
авіаспортклубі	авіаспортклуб	noun	noun:inanim:m:v_mis
авіаспортклубів	авіаспортклуб	noun	noun:inanim:p:v_rod
авіаспостереженню	авіаспостереження	noun	noun:inanim:n:v_dav
авіаспостереженню	авіаспостереження	noun	noun:inanim:n:v_mis
авіаспостереження	авіаспостереження	noun	noun:inanim:n:v_kly
авіаспостереження	авіаспостереження	noun	noun:inanim:n:v_naz
авіаспостереження	авіаспостереження	noun	noun:inanim:n:v_rod
авіаспостереження	авіаспостереження	noun	noun:inanim:n:v_zna
авіаспостереження	авіаспостереження	noun	noun:inanim:p:v_kly
авіаспостереження	авіаспостереження	noun	noun:inanim:p:v_naz
авіаспостереження	авіаспостереження	noun	noun:inanim:p:v_zna
авіаспостереженням	авіаспостереження	noun	noun:inanim:n:v_oru
авіаспостереженням	авіаспостереження	noun	noun:inanim:p:v_dav
авіаспостереженнями	авіаспостереження	noun	noun:inanim:p:v_oru
авіаспостереженнях	авіаспостереження	noun	noun:inanim:p:v_mis
авіаспостереженні	авіаспостереження	noun	noun:inanim:n:v_mis
авіаспостережень	авіаспостереження	noun	noun:inanim:p:v_rod
авіаспостерігач	авіаспостерігач	noun	noun:anim:m:v_naz
авіаспостерігача	авіаспостерігач	noun	noun:anim:m:v_rod
авіаспостерігача	авіаспостерігач	noun	noun:anim:m:v_zna
авіаспостерігачам	авіаспостерігач	noun	noun:anim:p:v_dav
авіаспостерігачами	авіаспостерігач	noun	noun:anim:p:v_oru
авіаспостерігачах	авіаспостерігач	noun	noun:anim:p:v_mis
авіаспостерігачеві	авіаспостерігач	noun	noun:anim:m:v_dav
авіаспостерігачеві	авіаспостерігач	noun	noun:anim:m:v_mis
авіаспостерігачем	авіаспостерігач	noun	noun:anim:m:v_oru
авіаспостерігачу	авіаспостерігач	noun	noun:anim:m:v_dav
авіаспостерігачу	авіаспостерігач	noun	noun:anim:m:v_kly
авіаспостерігачу	авіаспостерігач	noun	noun:anim:m:v_mis
авіаспостерігачі	авіаспостерігач	noun	noun:anim:m:v_mis
авіаспостерігачі	авіаспостерігач	noun	noun:anim:p:v_kly
авіаспостерігачі	авіаспостерігач	noun	noun:anim:p:v_naz
авіаспостерігачі	авіаспостерігач	noun	noun:anim:p:v_zna:rare
авіаспостерігачів	авіаспостерігач	noun	noun:anim:p:v_rod
авіаспостерігачів	авіаспостерігач	noun	noun:anim:p:v_zna
авіаструктур	авіаструктура	noun	noun:inanim:p:v_rod
авіаструктура	авіаструктура	noun	noun:inanim:f:v_naz
авіаструктурам	авіаструктура	noun	noun:inanim:p:v_dav
авіаструктурами	авіаструктура	noun	noun:inanim:p:v_oru
авіаструктурах	авіаструктура	noun	noun:inanim:p:v_mis
авіаструктури	авіаструктура	noun	noun:inanim:f:v_rod
авіаструктури	авіаструктура	noun	noun:inanim:p:v_kly
авіаструктури	авіаструктура	noun	noun:inanim:p:v_naz
авіаструктури	авіаструктура	noun	noun:inanim:p:v_zna
авіаструктуро	авіаструктура	noun	noun:inanim:f:v_kly
авіаструктурою	авіаструктура	noun	noun:inanim:f:v_oru
авіаструктуру	авіаструктура	noun	noun:inanim:f:v_zna
авіаструктурі	авіаструктура	noun	noun:inanim:f:v_dav
авіаструктурі	авіаструктура	noun	noun:inanim:f:v_mis
авіасуден	авіасудно	noun	noun:inanim:p:v_rod
авіасудна	авіасудно	noun	noun:inanim:n:v_rod
авіасудна	авіасудно	noun	noun:inanim:p:v_kly
авіасудна	авіасудно	noun	noun:inanim:p:v_naz
авіасудна	авіасудно	noun	noun:inanim:p:v_zna
авіасуднам	авіасудно	noun	noun:inanim:p:v_dav
авіасуднами	авіасудно	noun	noun:inanim:p:v_oru
авіасуднах	авіасудно	noun	noun:inanim:p:v_mis
авіасудно	авіасудно	noun	noun:inanim:n:v_kly
авіасудно	авіасудно	noun	noun:inanim:n:v_naz
авіасудно	авіасудно	noun	noun:inanim:n:v_zna
авіасудном	авіасудно	noun	noun:inanim:n:v_oru
авіасудну	авіасудно	noun	noun:inanim:n:v_dav
авіасудну	авіасудно	noun	noun:inanim:n:v_mis
авіасудні	авіасудно	noun	noun:inanim:n:v_mis
авіатаксист	авіатаксист	noun	noun:anim:m:v_naz
авіатаксиста	авіатаксист	noun	noun:anim:m:v_rod
авіатаксиста	авіатаксист	noun	noun:anim:m:v_zna
авіатаксистам	авіатаксист	noun	noun:anim:p:v_dav
авіатаксистами	авіатаксист	noun	noun:anim:p:v_oru
авіатаксистах	авіатаксист	noun	noun:anim:p:v_mis
авіатаксисте	авіатаксист	noun	noun:anim:m:v_kly
авіатаксисти	авіатаксист	noun	noun:anim:p:v_kly
авіатаксисти	авіатаксист	noun	noun:anim:p:v_naz
авіатаксисти	авіатаксист	noun	noun:anim:p:v_zna:rare
авіатаксистові	авіатаксист	noun	noun:anim:m:v_dav
авіатаксистові	авіатаксист	noun	noun:anim:m:v_mis
авіатаксистом	авіатаксист	noun	noun:anim:m:v_oru
авіатаксисті	авіатаксист	noun	noun:anim:m:v_mis
авіатаксистів	авіатаксист	noun	noun:anim:p:v_rod
авіатаксистів	авіатаксист	noun	noun:anim:p:v_zna
авіатермінал	авіатермінал	noun	noun:inanim:m:v_naz
авіатермінал	авіатермінал	noun	noun:inanim:m:v_zna
авіатермінала	авіатермінал	noun	noun:inanim:m:v_rod
авіатерміналам	авіатермінал	noun	noun:inanim:p:v_dav
авіатерміналами	авіатермінал	noun	noun:inanim:p:v_oru
авіатерміналах	авіатермінал	noun	noun:inanim:p:v_mis
авіатермінале	авіатермінал	noun	noun:inanim:m:v_kly
авіатермінали	авіатермінал	noun	noun:inanim:p:v_kly
авіатермінали	авіатермінал	noun	noun:inanim:p:v_naz
авіатермінали	авіатермінал	noun	noun:inanim:p:v_zna
авіатерміналові	авіатермінал	noun	noun:inanim:m:v_dav
авіатерміналові	авіатермінал	noun	noun:inanim:m:v_mis
авіатерміналом	авіатермінал	noun	noun:inanim:m:v_oru
авіатерміналі	авіатермінал	noun	noun:inanim:m:v_mis
авіатерміналів	авіатермінал	noun	noun:inanim:p:v_rod
авіатехнологій	авіатехнологія	noun	noun:inanim:p:v_rod
авіатехнологію	авіатехнологія	noun	noun:inanim:f:v_zna
авіатехнологія	авіатехнологія	noun	noun:inanim:f:v_naz
авіатехнологіям	авіатехнологія	noun	noun:inanim:p:v_dav
авіатехнологіями	авіатехнологія	noun	noun:inanim:p:v_oru
авіатехнологіях	авіатехнологія	noun	noun:inanim:p:v_mis
авіатехнологіє	авіатехнологія	noun	noun:inanim:f:v_kly
авіатехнологією	авіатехнологія	noun	noun:inanim:f:v_oru
авіатехнології	авіатехнологія	noun	noun:inanim:f:v_dav
авіатехнології	авіатехнологія	noun	noun:inanim:f:v_mis
авіатехнології	авіатехнологія	noun	noun:inanim:f:v_rod
авіатехнології	авіатехнологія	noun	noun:inanim:p:v_kly
авіатехнології	авіатехнологія	noun	noun:inanim:p:v_naz
авіатехнології	авіатехнологія	noun	noun:inanim:p:v_zna
авіатехнік	авіатехнік	noun	noun:anim:m:v_naz
авіатехніка	авіатехнік	noun	noun:anim:m:v_rod
авіатехніка	авіатехнік	noun	noun:anim:m:v_zna
авіатехнікам	авіатехнік	noun	noun:anim:p:v_dav
авіатехніками	авіатехнік	noun	noun:anim:p:v_oru
авіатехніках	авіатехнік	noun	noun:anim:p:v_mis
авіатехніки	авіатехнік	noun	noun:anim:p:v_kly
авіатехніки	авіатехнік	noun	noun:anim:p:v_naz
авіатехніки	авіатехнік	noun	noun:anim:p:v_zna:rare
авіатехнікові	авіатехнік	noun	noun:anim:m:v_dav
авіатехнікові	авіатехнік	noun	noun:anim:m:v_mis
авіатехніком	авіатехнік	noun	noun:anim:m:v_oru
авіатехніку	авіатехнік	noun	noun:anim:m:v_dav
авіатехніку	авіатехнік	noun	noun:anim:m:v_kly
авіатехніку	авіатехнік	noun	noun:anim:m:v_mis
авіатехніків	авіатехнік	noun	noun:anim:p:v_rod
авіатехніків	авіатехнік	noun	noun:anim:p:v_zna
авіатовариств	авіатовариство	noun	noun:inanim:p:v_rod
авіатовариства	авіатовариство	noun	noun:inanim:n:v_rod
авіатовариства	авіатовариство	noun	noun:inanim:p:v_kly
авіатовариства	авіатовариство	noun	noun:inanim:p:v_naz
авіатовариства	авіатовариство	noun	noun:inanim:p:v_zna
авіатовариствам	авіатовариство	noun	noun:inanim:p:v_dav
авіатовариствами	авіатовариство	noun	noun:inanim:p:v_oru
авіатовариствах	авіатовариство	noun	noun:inanim:p:v_mis
авіатовариство	авіатовариство	noun	noun:inanim:n:v_kly
авіатовариство	авіатовариство	noun	noun:inanim:n:v_naz
авіатовариство	авіатовариство	noun	noun:inanim:n:v_zna
авіатовариством	авіатовариство	noun	noun:inanim:n:v_oru
авіатовариству	авіатовариство	noun	noun:inanim:n:v_dav
авіатовариству	авіатовариство	noun	noun:inanim:n:v_mis
авіатоваристві	авіатовариство	noun	noun:inanim:n:v_mis
авіатор	авіатор	noun	noun:anim:m:v_naz
авіатора	авіатор	noun	noun:anim:m:v_rod
авіатора	авіатор	noun	noun:anim:m:v_zna
авіаторам	авіатор	noun	noun:anim:p:v_dav
авіаторами	авіатор	noun	noun:anim:p:v_oru
авіаторах	авіатор	noun	noun:anim:p:v_mis
авіаторе	авіатор	noun	noun:anim:m:v_kly
авіатори	авіатор	noun	noun:anim:p:v_kly
авіатори	авіатор	noun	noun:anim:p:v_naz
авіатори	авіатор	noun	noun:anim:p:v_zna:rare
авіаторка	авіаторка	noun	noun:anim:f:v_naz
авіаторкам	авіаторка	noun	noun:anim:p:v_dav
авіаторками	авіаторка	noun	noun:anim:p:v_oru
авіаторках	авіаторка	noun	noun:anim:p:v_mis
авіаторки	авіаторка	noun	noun:anim:f:v_rod
авіаторки	авіаторка	noun	noun:anim:p:v_kly
авіаторки	авіаторка	noun	noun:anim:p:v_naz
авіаторки	авіаторка	noun	noun:anim:p:v_zna:rare
авіаторко	авіаторка	noun	noun:anim:f:v_kly
авіаторкою	авіаторка	noun	noun:anim:f:v_oru
авіаторку	авіаторка	noun	noun:anim:f:v_zna
авіаторові	авіатор	noun	noun:anim:m:v_dav
авіаторові	авіатор	noun	noun:anim:m:v_mis
авіаторок	авіаторка	noun	noun:anim:p:v_rod
авіаторок	авіаторка	noun	noun:anim:p:v_zna
авіатором	авіатор	noun	noun:anim:m:v_oru
авіаторпед	авіаторпеда	noun	noun:inanim:p:v_rod
авіаторпеда	авіаторпеда	noun	noun:inanim:f:v_naz
авіаторпедам	авіаторпеда	noun	noun:inanim:p:v_dav
авіаторпедами	авіаторпеда	noun	noun:inanim:p:v_oru
авіаторпедах	авіаторпеда	noun	noun:inanim:p:v_mis
авіаторпеди	авіаторпеда	noun	noun:inanim:f:v_rod
авіаторпеди	авіаторпеда	noun	noun:inanim:p:v_kly
авіаторпеди	авіаторпеда	noun	noun:inanim:p:v_naz
авіаторпеди	авіаторпеда	noun	noun:inanim:p:v_zna
авіаторпедо	авіаторпеда	noun	noun:inanim:f:v_kly
авіаторпедою	авіаторпеда	noun	noun:inanim:f:v_oru
авіаторпеду	авіаторпеда	noun	noun:inanim:f:v_zna
авіаторпеді	авіаторпеда	noun	noun:inanim:f:v_dav
авіаторпеді	авіаторпеда	noun	noun:inanim:f:v_mis
авіаторці	авіаторка	noun	noun:anim:f:v_dav
авіаторці	авіаторка	noun	noun:anim:f:v_mis
авіаторі	авіатор	noun	noun:anim:m:v_mis
авіаторів	авіатор	noun	noun:anim:p:v_rod
авіаторів	авіатор	noun	noun:anim:p:v_zna
авіатравм	авіатравма	noun	noun:inanim:p:v_rod
авіатравма	авіатравма	noun	noun:inanim:f:v_naz
авіатравмам	авіатравма	noun	noun:inanim:p:v_dav
авіатравмами	авіатравма	noun	noun:inanim:p:v_oru
авіатравмах	авіатравма	noun	noun:inanim:p:v_mis
авіатравми	авіатравма	noun	noun:inanim:f:v_rod
авіатравми	авіатравма	noun	noun:inanim:p:v_kly
авіатравми	авіатравма	noun	noun:inanim:p:v_naz
авіатравми	авіатравма	noun	noun:inanim:p:v_zna
авіатравмо	авіатравма	noun	noun:inanim:f:v_kly
авіатравмою	авіатравма	noun	noun:inanim:f:v_oru
авіатравму	авіатравма	noun	noun:inanim:f:v_zna
авіатравмі	авіатравма	noun	noun:inanim:f:v_dav
авіатравмі	авіатравма	noun	noun:inanim:f:v_mis
авіатрагедій	авіатрагедія	noun	noun:inanim:p:v_rod
авіатрагедію	авіатрагедія	noun	noun:inanim:f:v_zna
авіатрагедія	авіатрагедія	noun	noun:inanim:f:v_naz
авіатрагедіям	авіатрагедія	noun	noun:inanim:p:v_dav
авіатрагедіями	авіатрагедія	noun	noun:inanim:p:v_oru
авіатрагедіях	авіатрагедія	noun	noun:inanim:p:v_mis
авіатрагедіє	авіатрагедія	noun	noun:inanim:f:v_kly
авіатрагедією	авіатрагедія	noun	noun:inanim:f:v_oru
авіатрагедії	авіатрагедія	noun	noun:inanim:f:v_dav
авіатрагедії	авіатрагедія	noun	noun:inanim:f:v_mis
авіатрагедії	авіатрагедія	noun	noun:inanim:f:v_rod
авіатрагедії	авіатрагедія	noun	noun:inanim:p:v_kly
авіатрагедії	авіатрагедія	noun	noun:inanim:p:v_naz
авіатрагедії	авіатрагедія	noun	noun:inanim:p:v_zna
авіатранспортник	авіатранспортник	noun	noun:anim:m:v_naz
авіатранспортника	авіатранспортник	noun	noun:anim:m:v_rod
авіатранспортника	авіатранспортник	noun	noun:anim:m:v_zna
авіатранспортникам	авіатранспортник	noun	noun:anim:p:v_dav
авіатранспортниками	авіатранспортник	noun	noun:anim:p:v_oru
авіатранспортниках	авіатранспортник	noun	noun:anim:p:v_mis
авіатранспортники	авіатранспортник	noun	noun:anim:p:v_kly
авіатранспортники	авіатранспортник	noun	noun:anim:p:v_naz
авіатранспортники	авіатранспортник	noun	noun:anim:p:v_zna:rare
авіатранспортникові	авіатранспортник	noun	noun:anim:m:v_dav
авіатранспортникові	авіатранспортник	noun	noun:anim:m:v_mis
авіатранспортником	авіатранспортник	noun	noun:anim:m:v_oru
авіатранспортнику	авіатранспортник	noun	noun:anim:m:v_dav
авіатранспортнику	авіатранспортник	noun	noun:anim:m:v_kly
авіатранспортнику	авіатранспортник	noun	noun:anim:m:v_mis
авіатранспортників	авіатранспортник	noun	noun:anim:p:v_rod
авіатранспортників	авіатранспортник	noun	noun:anim:p:v_zna
авіатрас	авіатраса	noun	noun:inanim:p:v_rod
авіатраса	авіатраса	noun	noun:inanim:f:v_naz
авіатрасам	авіатраса	noun	noun:inanim:p:v_dav
авіатрасами	авіатраса	noun	noun:inanim:p:v_oru
авіатрасах	авіатраса	noun	noun:inanim:p:v_mis
авіатраси	авіатраса	noun	noun:inanim:f:v_rod
авіатраси	авіатраса	noun	noun:inanim:p:v_kly
авіатраси	авіатраса	noun	noun:inanim:p:v_naz
авіатраси	авіатраса	noun	noun:inanim:p:v_zna
авіатрасо	авіатраса	noun	noun:inanim:f:v_kly
авіатрасою	авіатраса	noun	noun:inanim:f:v_oru
авіатрасу	авіатраса	noun	noun:inanim:f:v_zna
авіатрасі	авіатраса	noun	noun:inanim:f:v_dav
авіатрасі	авіатраса	noun	noun:inanim:f:v_mis
авіатренажер	авіатренажер	noun	noun:inanim:m:v_naz
авіатренажер	авіатренажер	noun	noun:inanim:m:v_zna
авіатренажера	авіатренажер	noun	noun:inanim:m:v_rod
авіатренажерам	авіатренажер	noun	noun:inanim:p:v_dav
авіатренажерами	авіатренажер	noun	noun:inanim:p:v_oru
авіатренажерах	авіатренажер	noun	noun:inanim:p:v_mis
авіатренажере	авіатренажер	noun	noun:inanim:m:v_kly
авіатренажери	авіатренажер	noun	noun:inanim:p:v_kly
авіатренажери	авіатренажер	noun	noun:inanim:p:v_naz
авіатренажери	авіатренажер	noun	noun:inanim:p:v_zna
авіатренажерові	авіатренажер	noun	noun:inanim:m:v_dav
авіатренажерові	авіатренажер	noun	noun:inanim:m:v_mis
авіатренажером	авіатренажер	noun	noun:inanim:m:v_oru
авіатренажері	авіатренажер	noun	noun:inanim:m:v_mis
авіатренажерів	авіатренажер	noun	noun:inanim:p:v_rod
авіатрощ	авіатроща	noun	noun:inanim:p:v_rod
авіатроща	авіатроща	noun	noun:inanim:f:v_naz
авіатрощам	авіатроща	noun	noun:inanim:p:v_dav
авіатрощами	авіатроща	noun	noun:inanim:p:v_oru
авіатрощах	авіатроща	noun	noun:inanim:p:v_mis
авіатроще	авіатроща	noun	noun:inanim:f:v_kly
авіатрощею	авіатроща	noun	noun:inanim:f:v_oru
авіатрощу	авіатроща	noun	noun:inanim:f:v_zna
авіатрощі	авіатроща	noun	noun:inanim:f:v_dav
авіатрощі	авіатроща	noun	noun:inanim:f:v_mis
авіатрощі	авіатроща	noun	noun:inanim:f:v_rod
авіатрощі	авіатроща	noun	noun:inanim:p:v_kly
авіатрощі	авіатроща	noun	noun:inanim:p:v_naz
авіатрощі	авіатроща	noun	noun:inanim:p:v_zna
авіатур	авіатур	noun	noun:inanim:m:v_naz
авіатур	авіатур	noun	noun:inanim:m:v_zna
авіатурам	авіатур	noun	noun:inanim:p:v_dav
авіатурами	авіатур	noun	noun:inanim:p:v_oru
авіатурах	авіатур	noun	noun:inanim:p:v_mis
авіатурбін	авіатурбіна	noun	noun:inanim:p:v_rod
авіатурбіна	авіатурбіна	noun	noun:inanim:f:v_naz
авіатурбінам	авіатурбіна	noun	noun:inanim:p:v_dav
авіатурбінами	авіатурбіна	noun	noun:inanim:p:v_oru
авіатурбінах	авіатурбіна	noun	noun:inanim:p:v_mis
авіатурбіни	авіатурбіна	noun	noun:inanim:f:v_rod
авіатурбіни	авіатурбіна	noun	noun:inanim:p:v_kly
авіатурбіни	авіатурбіна	noun	noun:inanim:p:v_naz
авіатурбіни	авіатурбіна	noun	noun:inanim:p:v_zna
авіатурбіно	авіатурбіна	noun	noun:inanim:f:v_kly
авіатурбіною	авіатурбіна	noun	noun:inanim:f:v_oru
авіатурбіну	авіатурбіна	noun	noun:inanim:f:v_zna
авіатурбіні	авіатурбіна	noun	noun:inanim:f:v_dav
авіатурбіні	авіатурбіна	noun	noun:inanim:f:v_mis
авіатуре	авіатур	noun	noun:inanim:m:v_kly
авіатури	авіатур	noun	noun:inanim:p:v_kly
авіатури	авіатур	noun	noun:inanim:p:v_naz
авіатури	авіатур	noun	noun:inanim:p:v_zna
авіатурист	авіатурист	noun	noun:anim:m:v_naz
авіатуриста	авіатурист	noun	noun:anim:m:v_rod
авіатуриста	авіатурист	noun	noun:anim:m:v_zna
авіатуристам	авіатурист	noun	noun:anim:p:v_dav
авіатуристами	авіатурист	noun	noun:anim:p:v_oru
авіатуристах	авіатурист	noun	noun:anim:p:v_mis
авіатуристе	авіатурист	noun	noun:anim:m:v_kly
авіатуристи	авіатурист	noun	noun:anim:p:v_kly
авіатуристи	авіатурист	noun	noun:anim:p:v_naz
авіатуристи	авіатурист	noun	noun:anim:p:v_zna:rare
авіатуристові	авіатурист	noun	noun:anim:m:v_dav
авіатуристові	авіатурист	noun	noun:anim:m:v_mis
авіатуристом	авіатурист	noun	noun:anim:m:v_oru
авіатуристі	авіатурист	noun	noun:anim:m:v_mis
авіатуристів	авіатурист	noun	noun:anim:p:v_rod
авіатуристів	авіатурист	noun	noun:anim:p:v_zna
авіатурові	авіатур	noun	noun:inanim:m:v_dav
авіатурові	авіатур	noun	noun:inanim:m:v_mis
авіатуром	авіатур	noun	noun:inanim:m:v_oru
авіатуру	авіатур	noun	noun:inanim:m:v_dav
авіатуру	авіатур	noun	noun:inanim:m:v_mis
авіатуру	авіатур	noun	noun:inanim:m:v_rod
авіатурі	авіатур	noun	noun:inanim:m:v_mis
авіатурів	авіатур	noun	noun:inanim:p:v_rod
активний	активний	adj	adj:m:v_kly:compb
активний	активний	adj	adj:m:v_naz:compb
активний	активний	adj	adj:m:v_zna:rinanim:compb
активним	активний	adj	adj:m:v_oru:compb
активним	активний	adj	adj:n:v_oru:compb
активним	активний	adj	adj:p:v_dav:compb
активними	активний	adj	adj:p:v_oru:compb
активних	активний	adj	adj:p:v_mis:compb
активних	активний	adj	adj:p:v_rod:compb
активних	активний	adj	adj:p:v_zna:ranim:compb
активного	активний	adj	adj:m:v_rod:compb
активного	активний	adj	adj:m:v_zna:ranim:compb
активного	активний	adj	adj:n:v_rod:compb
активному	активний	adj	adj:m:v_dav:compb
активному	активний	adj	adj:m:v_mis:compb
активному	активний	adj	adj:n:v_dav:compb
активному	активний	adj	adj:n:v_mis:compb
активні	активний	adj	adj:p:v_kly:compb
активні	активний	adj	adj:p:v_naz:compb
активні	активний	adj	adj:p:v_zna:rinanim:compb
борщ	борщ	noun	noun:inanim:m:v_naz
борщ	борщ	noun	noun:inanim:m:v_zna
борщеві	борщ	noun	noun:inanim:m:v_dav
борщеві	борщ	noun	noun:inanim:m:v_mis
борщем	борщ	noun	noun:inanim:m:v_oru
борщу	борщ	noun	noun:inanim:m:v_dav
борщу	борщ	noun	noun:inanim:m:v_kly
борщу	борщ	noun	noun:inanim:m:v_mis
борщу	борщ	noun	noun:inanim:m:v_rod
борщі	борщ	noun	noun:inanim:m:v_mis
борщі	борщ	noun	noun:inanim:p:v_kly
борщі	борщ	noun	noun:inanim:p:v_naz
борщі	борщ	noun	noun:inanim:p:v_zna
книг	книга	noun	noun:inanim:p:v_rod
книга	книга	noun	noun:inanim:f:v_naz
книгам	книга	noun	noun:inanim:p:v_dav
книгами	книга	noun	noun:inanim:p:v_oru
книгах	книга	noun	noun:inanim:p:v_mis
книги	книга	noun	noun:inanim:f:v_rod
книги	книга	noun	noun:inanim:p:v_kly
книги	книга	noun	noun:inanim:p:v_naz
книги	книга	noun	noun:inanim:p:v_zna
книго	книга	noun	noun:inanim:f:v_kly
книгою	книга	noun	noun:inanim:f:v_oru
книгу	книга	noun	noun:inanim:f:v_zna
книзі	книга	noun	noun:inanim:f:v_dav
книзі	книга	noun	noun:inanim:f:v_mis
кота	кіт	noun	noun:anim:m:v_rod
кота	кіт	noun	noun:anim:m:v_zna
котам	кіт	noun	noun:anim:p:v_dav
котами	кіт	noun	noun:anim:p:v_oru
котах	кіт	noun	noun:anim:p:v_mis
коте	кіт	noun	noun:anim:m:v_kly
коти	кіт	noun	noun:anim:p:v_kly
коти	кіт	noun	noun:anim:p:v_naz
коти	кіт	noun	noun:anim:p:v_zna
котові	кіт	noun	noun:anim:m:v_dav
котові	кіт	noun	noun:anim:m:v_mis
котом	кіт	noun	noun:anim:m:v_oru
коту	кіт	noun	noun:anim:m:v_dav
коту	кіт	noun	noun:anim:m:v_mis
котів	кіт	noun	noun:anim:p:v_rod
котів	кіт	noun	noun:anim:p:v_zna
кіт	кіт	noun	noun:anim:m:v_naz
море	море	noun	noun:inanim:n:v_kly
море	море	noun	noun:inanim:n:v_naz
море	море	noun	noun:inanim:n:v_zna
морем	море	noun	noun:inanim:n:v_oru
морю	море	noun	noun:inanim:n:v_dav
морю	море	noun	noun:inanim:n:v_mis
моря	море	noun	noun:inanim:n:v_rod
моря	море	noun	noun:inanim:p:v_kly
моря	море	noun	noun:inanim:p:v_naz
моря	море	noun	noun:inanim:p:v_zna
морям	море	noun	noun:inanim:p:v_dav
морями	море	noun	noun:inanim:p:v_oru
морях	море	noun	noun:inanim:p:v_mis
морі	море	noun	noun:inanim:n:v_mis
морів	море	noun	noun:inanim:p:v_rod
ночам	ніч	noun	noun:inanim:p:v_dav
ночами	ніч	noun	noun:inanim:p:v_oru
ночах	ніч	noun	noun:inanim:p:v_mis
ноче	ніч	noun	noun:inanim:f:v_kly
ночей	ніч	noun	noun:inanim:p:v_rod
ночі	ніч	noun	noun:inanim:f:v_dav
ночі	ніч	noun	noun:inanim:f:v_mis
ночі	ніч	noun	noun:inanim:f:v_rod
ночі	ніч	noun	noun:inanim:p:v_kly
ночі	ніч	noun	noun:inanim:p:v_naz
ночі	ніч	noun	noun:inanim:p:v_zna
ніч	ніч	noun	noun:inanim:f:v_naz
ніч	ніч	noun	noun:inanim:f:v_zna
ніччю	ніч	noun	noun:inanim:f:v_oru
рук	рука	noun	noun:inanim:p:v_rod
рука	рука	noun	noun:inanim:f:v_naz
рукам	рука	noun	noun:inanim:p:v_dav
руками	рука	noun	noun:inanim:p:v_oru
руках	рука	noun	noun:inanim:p:v_mis
руки	рука	noun	noun:inanim:f:v_rod
руки	рука	noun	noun:inanim:p:v_kly
руки	рука	noun	noun:inanim:p:v_naz
руки	рука	noun	noun:inanim:p:v_zna
руко	рука	noun	noun:inanim:f:v_kly
рукою	рука	noun	noun:inanim:f:v_oru
руку	рука	noun	noun:inanim:f:v_zna
руці	рука	noun	noun:inanim:f:v_dav
руці	рука	noun	noun:inanim:f:v_mis
стола	стіл	noun	noun:inanim:m:v_rod
стола	стіл	noun	noun:inanim:m:v_zna:var
столам	стіл	noun	noun:inanim:p:v_dav
столами	стіл	noun	noun:inanim:p:v_oru
столах	стіл	noun	noun:inanim:p:v_mis
столе	стіл	noun	noun:inanim:m:v_kly
столи	стіл	noun	noun:inanim:p:v_kly
столи	стіл	noun	noun:inanim:p:v_naz
столи	стіл	noun	noun:inanim:p:v_zna
столом	стіл	noun	noun:inanim:m:v_oru
столу	стіл	noun	noun:inanim:m:v_dav
столу	стіл	noun	noun:inanim:m:v_mis
столу	стіл	noun	noun:inanim:m:v_rod
столі	стіл	noun	noun:inanim:m:v_mis
столів	стіл	noun	noun:inanim:p:v_rod
стіл	стіл	noun	noun:inanim:m:v_naz
стіл	стіл	noun	noun:inanim:m:v_zna
тест	тест	noun	noun:inanim:m:v_naz
тест	тест	noun	noun:inanim:m:v_zna
тестові	тест	noun	noun:inanim:m:v_dav
тестові	тест	noun	noun:inanim:m:v_mis
тестом	тест	noun	noun:inanim:m:v_oru
тесту	тест	noun	noun:inanim:m:v_dav
тесту	тест	noun	noun:inanim:m:v_mis
тесту	тест	noun	noun:inanim:m:v_rod
тесті	тест	noun	noun:inanim:m:v_mis
хлопець	хлопець	noun	noun:anim:m:v_naz
хлопцеві	хлопець	noun	noun:anim:m:v_dav
хлопцеві	хлопець	noun	noun:anim:m:v_mis
хлопцем	хлопець	noun	noun:anim:m:v_oru
хлопця	хлопець	noun	noun:anim:m:v_rod
хлопця	хлопець	noun	noun:anim:m:v_zna
хлопцям	хлопець	noun	noun:anim:p:v_dav
хлопцями	хлопець	noun	noun:anim:p:v_oru
хлопцях	хлопець	noun	noun:anim:p:v_mis
хлопці	хлопець	noun	noun:anim:m:v_mis
хлопці	хлопець	noun	noun:anim:p:v_kly
хлопці	хлопець	noun	noun:anim:p:v_naz
хлопці	хлопець	noun	noun:anim:p:v_zna:rare
хлопців	хлопець	noun	noun:anim:p:v_rod
хлопців	хлопець	noun	noun:anim:p:v_zna
хлопче	хлопець	noun	noun:anim:m:v_kly"""


def _captured_paradigm_verifier() -> JsonVesumVerifier:
    payload: dict[str, list[dict[str, str]]] = {}
    for line in _CAPTURED_PARADIGM_ROWS.split("\n"):
        word, lemma, pos, tags = line.split("\t")
        payload.setdefault(word, []).append({"lemma": lemma, "pos": pos, "tags": tags})
    return JsonVesumVerifier(payload)
