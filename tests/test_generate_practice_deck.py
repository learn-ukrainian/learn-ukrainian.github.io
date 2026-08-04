from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

import scripts.audit.generate_practice_deck as generate_practice_deck
from scripts.audit.generate_practice_deck import (
    DEFAULT_TARGET,
    DRILL_MODES,
    BuildConfig,
    JsonVesumVerifier,
    RealVesumVerifier,
    ReviewedSourceAllowlist,
    _aspect_category,
    _build_antonym_items,
    _build_classify_items,
    _build_cloze_items,
    _build_heritage_items,
    _build_homonym_items,
    _build_lexeme,
    _build_paradigm_items,
    _build_paronym_items,
    _declension_category,
    _eligible_decoys,
    _heritage_availability_level,
    _meaning_mc_eligible,
    _option_strategy_for_level,
    _select_practice_lexemes,
    _stress_position,
    _vesum_aspect_by_lemma,
    apply_size_budgets,
    build_practice_shards,
    compact_cloze_emit_fields,
    main,
    merge_practice_seed_entries,
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
    validate_classify_item,
    validate_heritage_item,
    validate_heritage_pair,
    validate_homonym_item,
    validate_homonym_pair,
    validate_option_set,
    validate_paradigm_item,
    validate_paronym_item,
    validate_paronym_pair,
    validate_synonym_item,
    write_aspect_residual_report,
    write_shards,
)

FIXTURES = Path("tests/fixtures")
MANIFEST = FIXTURES / "lexicon-practice-manifest.json"
ALLOWLIST = FIXTURES / "lexicon-practice-reviewed-allowlist.json"
VESUM = FIXTURES / "lexicon-practice-vesum.json"
CLOZE_SOURCES = FIXTURES / "lexicon-practice-cloze-sources.json"
HERITAGE_PAIRS = FIXTURES / "lexicon-practice-heritage-pairs.yaml"
PARONYM_PAIRS = FIXTURES / "lexicon-practice-paronym-pairs.yaml"
CURATED_V5_SEED = FIXTURES / "atlas" / "curated_v5_practice_seed.json"


def test_default_target_preserves_committed_practice_surface() -> None:
    assert DEFAULT_TARGET >= 6000
    assert BuildConfig().target == DEFAULT_TARGET


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
    indexed = {
        item["lemmaId"]: item
        for level in shards.values()
        for item in level["index"]["items"]
    }
    lexemes = {
        item["lemmaId"]: item
        for level in shards.values()
        for item in level["lexemes"]["lexemes"]
    }
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


def test_local_practice_seed_accepts_attested_rows_alongside_local_recognition_rows(tmp_path: Path) -> None:
    seed_path = tmp_path / "mixed-seed.json"
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
                    },
                    {
                        "seedRow": 2,
                        "lemma": "речення",
                        "slug": "речення",
                        "cefr": "A1",
                        "sentenceStatus": "ok",
                        "example": "Це речення.",
                        "provenance": {"source_file": "fixture", "credit": "Fixture"},
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    rows = read_practice_seed(seed_path, allow_local_private=True)

    assert [row["seedRow"] for row in rows] == [1, 2]


def test_local_practice_seed_rows_are_selected_before_ordinary_course_entries() -> None:
    entries = [
        {
            "lemma": "справедливий",
            "url_slug": "справедливий",
            "gloss": "fair",
            "enrichment": {"cefr": {"level": "A2"}},
            "surface_admission": {"practice": True, "cloze": False},
            "local_practice_private_teacher": True,
        },
        {
            "lemma": "витирати",
            "url_slug": "витирати",
            "gloss": "wipe",
            "enrichment": {"cefr": {"level": "A2"}},
            "course_usage": [{"module": "fixture"}],
        },
    ]

    selected, _lexemes, _by_plain_lemma, _by_id = _select_practice_lexemes(
        entries,
        JsonVesumVerifier.from_path(VESUM),
        BuildConfig(target=1, source_label="fixture"),
    )

    assert [entry["url_slug"] for entry, _lexeme in selected] == ["справедливий"]


def test_representative_seed_selection_round_robins_available_cefr_and_pos_strata() -> None:
    entries = [
        {
            "lemma": lemma,
            "url_slug": lemma,
            "gloss": "fixture gloss",
            "pos": pos,
            "enrichment": {"cefr": {"level": cefr}},
            "surface_admission": {"practice": True, "cloze": False},
            "local_practice_private_teacher": True,
        }
        for lemma, cefr, pos in (
            ("а", "A1", "noun"),
            ("б", "A1", "noun"),
            ("в", "A1", "verb"),
            ("г", "A2", "noun"),
            ("ґ", "A2", "verb"),
        )
    ]

    selected, _lexemes, _by_plain_lemma, _by_id = _select_practice_lexemes(
        entries,
        JsonVesumVerifier.from_path(VESUM),
        BuildConfig(target=5, source_label="fixture", seed_selection="representative"),
    )

    assert [entry["url_slug"] for entry, _lexeme in selected] == ["а", "г", "в", "ґ", "б"]


def test_source_backed_priority_lexemes_precede_general_course_fill() -> None:
    entries = read_manifest(MANIFEST)
    selected, _lexemes, _by_plain_lemma, _by_id = _select_practice_lexemes(
        entries,
        JsonVesumVerifier.from_path(VESUM),
        BuildConfig(target=1, source_label="fixture"),
        {"knyha"},
    )

    assert [entry["url_slug"] for entry, _lexeme in selected] == ["knyha"]


def test_real_vesum_verifier_uses_an_explicit_database_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    observed: dict[str, object] = {}

    def fake_verify_words(words: list[str], *, pos_filter: str | None, db_path: Path) -> dict[str, list[dict]]:
        observed.update(words=words, pos_filter=pos_filter, db_path=db_path)
        return {word: [] for word in words}

    from scripts.verification import vesum

    monkeypatch.setattr(vesum, "verify_words", fake_verify_words)
    database = tmp_path / "vesum-shadow.db"
    assert RealVesumVerifier(database).verify_words(["слово"], pos_filter="noun") == {"слово": []}
    assert observed == {"words": ["слово"], "pos_filter": "noun", "db_path": database}


def test_practice_seed_entries_are_selected_before_ordinary_course_entries() -> None:
    entries = [
        {
            "lemma": "звичайний",
            "url_slug": "звичайний",
            "gloss": "ordinary",
            "enrichment": {"cefr": {"level": "A1"}},
            "course_usage": [{"module": "fixture"}],
        },
        {
            "lemma": "насіннєвий",
            "url_slug": "насіннєвий",
            "gloss": "seeded",
            "enrichment": {"cefr": {"level": "A1"}},
            "primary_source": "source_inventory_grow",
            "surface_admission": {"practice": True},
            "practice_example": {
                "text": "Це насіннєвий матеріал.",
                "provenance": {"source_file": "fixture", "credit": "Fixture"},
            },
        },
    ]

    selected, _lexemes, _by_plain_lemma, _by_id = _select_practice_lexemes(
        entries,
        JsonVesumVerifier.from_path(VESUM),
        BuildConfig(target=1, source_label="fixture"),
    )

    assert [entry["url_slug"] for entry, _lexeme in selected] == ["насіннєвий"]


def test_practice_seed_validates_duplicate_attestations_but_emits_one_route_example(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.json"
    provenance = {"source_file": "ukrlib-example", "credit": "Автор"}
    seed_path.write_text(
        json.dumps(
            {
                "schema": "curated-v5-practice-seed-v1",
                "entries": [
                    {"lemma": "слово", "slug": "слово", "cefr": "A1", "example": "Перший.", "provenance": provenance, "sentenceStatus": "ok"},
                    {"lemma": "слово", "slug": "слово", "cefr": "A1", "example": "Другий.", "provenance": provenance, "sentenceStatus": "ok"},
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


def test_curated_cloze_derives_missing_target_form_from_paradigm() -> None:
    entries = read_manifest(MANIFEST)
    allowlist = ReviewedSourceAllowlist.from_path(ALLOWLIST)
    verifier = JsonVesumVerifier.from_path(VESUM)
    cloze_sources = read_cloze_sources(CLOZE_SOURCES)
    candidate = next(row for row in cloze_sources if row["lemmaId"] == "knyha")
    candidate.pop("form")

    shards = build_practice_shards(entries, allowlist, verifier, cloze_sources, BuildConfig())

    cloze = next(item for item in shards["A1"]["cloze"]["cloze"] if item["lemmaId"] == "knyha")
    assert cloze["blankCase"] == "accusative"
    assert cloze["number"] == "singular"
    assert cloze["form"] == "книгу"


def test_manifest_cloze_fields_are_ignored_without_curated_sources() -> None:
    shards = _build(cloze_sources_path=None)

    assert shards["A1"]["index"]["counts"]["lexemes"] == 7
    assert shards["A1"]["index"]["counts"]["cloze"] == 0
    assert shards["A1"]["cloze"]["cloze"] == []


def test_disable_cloze_emits_no_cards_even_when_curated_sources_are_available() -> None:
    shards = _build(BuildConfig(cloze_enabled=False))

    assert all(not item["hasCloze"] for shard in shards.values() for item in shard["index"]["items"])
    assert all(not shard["cloze"]["cloze"] for shard in shards.values())


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

    indexed_lemma_ids = {item["lemmaId"] for item in a2["index"]["items"]}
    for mode in DRILL_MODES:
        emitted_ids = {
            item["lemmaId"]
            for item in a2[mode][mode]
            if item["lemmaId"] in indexed_lemma_ids
        }
        advertised_ids = {
            item["lemmaId"]
            for item in a2["index"]["items"]
            if mode in item["modes"]
        }
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


def test_heritage_builder_copies_curated_prompt_en_and_suppresses_placeholders() -> None:
    pair = _fixture_heritage_pair()
    lexemes = _fixture_lexemes()
    pair["frames"][0]["sentence_en"] = "I am reading a book."

    item = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1")[0]
    assert item["promptEn"] == "I am reading a book."

    pair["frames"][0].pop("sentence_en")
    item_without_en = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1")[0]
    assert "promptEn" not in item_without_en

    pair["frames"][0]["sentence_en"] = "Context sentence for книгу"
    placeholder_item = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1")[0]
    assert "promptEn" not in placeholder_item


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


def test_heritage_a1_admission_is_explicit_and_emitted_with_severity() -> None:
    pair = _fixture_heritage_pair()
    pair["cefrAvailability"] = "a1"
    pair["severity"] = "russianism"
    lexemes = _fixture_lexemes()

    assert _heritage_availability_level(pair) == "A1"
    item = _build_heritage_items(pair, lexemes[0], lexemes, "deck-v1")[0]
    assert item["cefr"] == "A1"
    assert item["severity"] == "russianism"


def test_heritage_pair_requires_known_severity_and_allows_a1_guidance() -> None:
    pair = _fixture_heritage_pair()
    pair["cefrAvailability"] = "a1"
    pair["severity"] = "enrichment"
    assert validate_heritage_pair(pair) == []

    pair["severity"] = "warning"
    assert "heritage_pair severity must be russianism or enrichment" in validate_heritage_pair(pair)


def test_stress_position_preserves_non_stress_combining_marks() -> None:
    assert _stress_position("пої́здка") == ("поїздка", 2)
    assert _stress_position("кра́й") == ("край", 2)


def test_neuter_a_ya_nouns_can_reach_fourth_declension() -> None:
    entry = {"lemma": "ім'я", "pos": "noun"}
    paradigm = {"cases": {"nominative": {"singular": "ім'я"}}}

    assert _declension_category(entry, ["ім. сер."], paradigm) == "declension-4"


@pytest.mark.parametrize(
    ("lemma", "labels", "expected"),
    [
        ("писати", ["verb:imperf:pres"], "imperfective"),
        ("написати", ["verb:perf:futr"], "perfective"),
    ],
)
def test_aspect_category_reads_explicit_vesum_tags(
    lemma: str, labels: list[str], expected: str
) -> None:
    assert _aspect_category(labels) == expected, lemma


def test_aspect_category_explicit_tag_wins_over_tense_proxy() -> None:
    assert _aspect_category(["доконаний", "теперішній"]) == "perfective"


def test_classify_prefers_explicit_morphology_aspect_over_vesum_or_tense() -> None:
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

    classify = _build_classify_items(entry, lexeme, vesum_aspect="imperfective")

    aspect_set = next(item for item in classify[0]["sets"] if item["setId"] == "aspect")
    assert aspect_set["answer"] == "perfective"


def test_aspect_category_uses_imperfective_fallback_for_present_and_future() -> None:
    assert _aspect_category(["теперішній", "майбутній"]) == "imperfective"


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


def test_write_aspect_residual_report_is_named_and_deterministic(tmp_path: Path) -> None:
    report = tmp_path / "aspect-residuals.json"

    write_aspect_residual_report(
        report,
        [
            {"lemmaId": "z", "lemma": "знати", "cefr": "B1", "reason": "missing_morphology"},
            {"lemmaId": "a", "lemma": "абити", "cefr": "A2", "reason": "no_explicit_aspect_or_tense_proxy"},
        ],
    )

    assert json.loads(report.read_text(encoding="utf-8")) == {
        "schema": "atlas-practice-aspect-residuals-v1",
        "scope": "selected practice verbs at A2-C1 with no emitted aspect set",
        "count": 2,
        "verbs": [
            {"lemmaId": "a", "lemma": "абити", "cefr": "A2", "reason": "no_explicit_aspect_or_tense_proxy"},
            {"lemmaId": "z", "lemma": "знати", "cefr": "B1", "reason": "missing_morphology"},
        ],
    }




def test_vesum_aspect_lookup_drops_biaspectual_combined_tag() -> None:
    verifier = JsonVesumVerifier(
        {
            "атакувати": [
                {"lemma": "атакувати", "pos": "verb", "tags": "verb:imperf:perf:inf"}
            ],
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
        entry, lexeme, vesum_aspect="imperfective", aspect_residuals=residuals
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


def test_build_classify_items_records_conflicting_explicit_aspect_residual() -> None:
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

    classify = _build_classify_items(entry, lexeme, aspect_residuals=residuals)

    assert not any(s.get("setId") == "aspect" for item in classify for s in item.get("sets", []))
    assert residuals == [
        {
            "lemmaId": "omonym",
            "lemma": "омонім",
            "cefr": "A2",
            "reason": "conflicting_explicit_aspect",
        }
    ]


def test_build_classify_items_records_no_explicit_aspect_or_tense_proxy_residual() -> None:
    entry = {
        "lemma": "абити",
        "pos": "verb",
        "enrichment": {
            "morphology": {
                "pos": "verb",
                "forms": [{"label": "інфінітив"}],
            }
        },
    }
    lexeme = {"lemmaId": "abyty", "lemma": "абити", "cefr": "A2"}
    residuals: list[dict[str, str]] = []

    classify = _build_classify_items(entry, lexeme, aspect_residuals=residuals)

    assert not any(s.get("setId") == "aspect" for item in classify for s in item.get("sets", []))
    assert residuals == [
        {
            "lemmaId": "abyty",
            "lemma": "абити",
            "cefr": "A2",
            "reason": "no_explicit_aspect_or_tense_proxy",
        }
    ]


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


def test_classify_emits_all_context_free_pos_answers_for_multi_pos_lemma() -> None:
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
            "definition_cards": [
                {"definitions": ["1. спол. для протиставлення; 2. присл., у знач. вставн. сл."]}
            ],
        },
    }
    lexeme = {"lemmaId": "prote", "lemma": "проте", "cefr": "B1"}

    classify = _build_classify_items(entry, lexeme)

    pos_sets = [item for item in classify[0]["sets"] if item["setId"] == "pos"]
    assert len(pos_sets) == 1
    assert pos_sets[0]["answer"] == "adverb"
    assert pos_sets[0]["answers"] == ["adverb", "conjunction"]
    assert pos_sets[0]["answerLabelUk"] == "прислівник"


def test_classify_validator_requires_ordered_multi_pos_answers() -> None:
    item = {
        "sets": [
            {
                "setId": "pos",
                "answer": "conjunction",
                "answers": ["conjunction", "adverb"],
                "options": [
                    {"value": value, "labelUk": label[0]}
                    for value, label in generate_practice_deck.CLASSIFY_LABELS["pos"].items()
                ],
            }
        ]
    }

    assert "classify POS answers must use school order with answer first" in validate_classify_item(item)


def test_classify_keeps_pos_set_for_unambiguous_noun() -> None:
    entry = {
        "lemma": "книга",
        "pos": "noun",
        "enrichment": {
            "cefr": {"level": "A2", "pos": "noun"},
            "morphology": {
                "pos": "noun",
                "forms": [{"label": "ім. жін."}],
            },
            "translation": {"en": ["book"], "pos": "noun"},
        },
    }
    lexeme = {"lemmaId": "knyha", "lemma": "книга", "cefr": "A2"}

    classify = _build_classify_items(entry, lexeme)[0]

    pos_sets = [item for item in classify["sets"] if item["setId"] == "pos"]
    assert len(pos_sets) == 1
    assert pos_sets[0]["answer"] == "noun"


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
        ("intj", "interjection"),
    ],
)
def test_classify_pos_aliases_normalize_to_distinct_closed_buckets(
    raw_pos: str, expected_bucket: str
) -> None:
    assert generate_practice_deck._normalize_pos_buckets(raw_pos) == [expected_bucket]


def test_classify_pos_generic_part_does_not_match_prose() -> None:
    assert generate_practice_deck._normalize_pos_buckets("part of speech") == []
    assert generate_practice_deck._normalize_pos_buckets("participle") == []
    assert generate_practice_deck._definition_card_pos_buckets(
        {"definition_cards": [{"definitions": ["part of speech"]}]}
    ) == []


def test_classify_pos_closed_set_uses_school_taxonomy() -> None:
    assert list(generate_practice_deck.CLASSIFY_LABELS["pos"]) == [
        "noun",
        "adjective",
        "numeral",
        "pronoun",
        "verb",
        "adverb",
        "preposition",
        "conjunction",
        "particle",
        "interjection",
    ]
    assert [
        labels[0] for labels in generate_practice_deck.CLASSIFY_LABELS["pos"].values()
    ] == [
        "іменник",
        "прикметник",
        "числівник",
        "займенник",
        "дієслово",
        "прислівник",
        "прийменник",
        "сполучник",
        "частка",
        "вигук",
    ]


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


def test_meaning_mc_eligibility_requires_a_latin_majority_gloss() -> None:
    assert _meaning_mc_eligible("justice", "справедливість", "noun") is True
    assert _meaning_mc_eligible("сукупність прав", "право", "noun") is False
    # A Latin-majority label with a brief Cyrillic clarification remains a learner English gloss.
    assert _meaning_mc_eligible("justice укр", "справедливість", "noun") is True
    assert _meaning_mc_eligible("justice справедливість", "справедливість", "noun") is False

    entries = [
        {
            "lemma": "право",
            "url_slug": "pravo",
            "gloss": "сукупність прав",
            "pos": "noun",
            "primary_source": "course_vocab",
            "cefr": "A1",
        },
    ]
    shards = build_practice_shards(
        entries, ReviewedSourceAllowlist.from_payload([]), JsonVesumVerifier({})
    )
    lexeme = shards["A1"]["lexemes"]["lexemes"][0]
    index_item = shards["A1"]["index"]["items"][0]

    assert lexeme["meaningMcEligible"] is False
    assert index_item["modes"] == ["flashcards"]


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


def test_course_anchored_lexeme_without_cefr_stays_recognition_eligible() -> None:
    entry = {
        "lemma": "ґудзик",
        "url_slug": "gudzik",
        "gloss": "button",
        "pos": "noun",
        "primary_source": "course_vocab",
        "course_usage": [{"module_num": 2, "slug": "clothes"}],
    }

    shards = build_practice_shards(
        [entry],
        ReviewedSourceAllowlist.from_payload([]),
        JsonVesumVerifier({}),
        config=BuildConfig(target=1),
        synonym_verdicts={"approved": [], "rejected": []},
    )

    index_item = shards["A1"]["index"]["items"][0]
    lexeme = shards["A1"]["lexemes"]["lexemes"][0]
    assert index_item["lemmaId"] == "gudzik"
    assert index_item["cefr"] is None
    assert index_item["modes"] == ["flashcards", "matching", "choice"]
    assert lexeme["cefr"] is None
    assert shards["A1"]["cloze"]["cloze"] == []


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
    cloze_items = shards["A1"]["cloze"]["cloze"]
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
            assert all(
                key in option
                for key in ("optionId", "label", "lemmaId", "kind", "case", "pos")
            )


def test_size_budget_cloze_trim_prioritizes_unique_lemmas(capsys: pytest.CaptureFixture[str]) -> None:
    cloze_items = [
        {
            "clozeId": f"{lemma_id}:cloze:{index}",
            "lemmaId": lemma_id,
            "form": lemma_id,
            "padding": "x" * 1_500,
        }
        for index, lemma_id in enumerate(("a", "a", "b", "c"), start=1)
    ]
    index = {
        "schema": "atlas-practice-index",
        "items": [
            {
                "lemmaId": lemma_id,
                "lemma": lemma_id,
                "cefr": "A1",
                "modes": ["flashcards", "cloze"],
                "hasCloze": True,
                "clozeIds": [f"{lemma_id}:cloze:1"],
                "newOrder": order,
            }
            for order, lemma_id in enumerate(("a", "b", "c"))
        ],
        "counts": {
            "lexemes": 3,
            "cloze": 4,
            "clozeEligibleLexemes": 3,
            "clozeCoverage": 1.0,
            "modeCounts": {"cloze": 4},
            "modeCoverage": {"cloze": 1.0},
        },
    }
    lexemes = {
        "schema": "atlas-practice-lexemes",
        "lexemes": [{"lemmaId": lemma_id, "lemma": lemma_id} for lemma_id in ("a", "b", "c")],
    }
    cloze = {"schema": "atlas-practice-cloze", "cloze": cloze_items}
    shards = {"A1": {"index": index, "lexemes": lexemes, "cloze": cloze}}

    probe = {**cloze, "cloze": cloze_items[:3]}
    probe_budget = generate_practice_deck._size_budget(probe, 1_000_000, 1_000_000)
    apply_size_budgets(
        shards,
        raw_limit=int(probe_budget["rawBytes"]) + 200,
        gzip_limit=int(probe_budget["gzipBytes"]) + 200,
    )

    assert "trimmed cloze items 4 -> 3" in capsys.readouterr().err
    assert {item["lemmaId"] for item in shards["A1"]["cloze"]["cloze"]} == {"a", "b", "c"}
    assert shards["A1"]["index"]["counts"]["clozeEligibleLexemes"] == 3
    assert shards["A1"]["index"]["counts"]["clozeCoverage"] == 1.0
    assert shards["A1"]["index"]["items"][0]["clozeIds"] == ["a:cloze:1"]


def test_size_budget_cloze_warning_reports_eligible_lemma_counts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    cloze_items = [
        {
            "clozeId": f"{lemma_id}:cloze:1",
            "lemmaId": lemma_id,
            "form": lemma_id,
            "padding": "x" * 1_500,
        }
        for lemma_id in ("a", "b", "c", "d")
    ]
    cloze = {"schema": "atlas-practice-cloze", "cloze": cloze_items}
    probe = {**cloze, "cloze": cloze_items[:3]}
    raw_budget = generate_practice_deck._size_budget(probe, 1_000_000, 1_000_000)

    apply_size_budgets(
        {"A1": {"cloze": cloze}},
        raw_limit=int(raw_budget["rawBytes"]) + 200,
        gzip_limit=int(raw_budget["gzipBytes"]) + 200,
    )

    assert "trimmed cloze items 4 -> 3; eligible lemmas 4 -> 3" in capsys.readouterr().err


def test_size_budget_uses_dedicated_cloze_limits() -> None:
    cloze = {
        "schema": "atlas-practice-cloze",
        "cloze": [{"clozeId": "a:cloze:1", "lemmaId": "a", "padding": "x" * 500}],
    }
    dedicated_budget = generate_practice_deck._size_budget(cloze, 1_000_000, 1_000_000)

    shards = {"A1": {"cloze": cloze}}
    apply_size_budgets(
        shards,
        raw_limit=1,
        gzip_limit=1,
        cloze_raw_limit=int(dedicated_budget["rawBytes"]) + 1,
        cloze_gzip_limit=int(dedicated_budget["gzipBytes"]) + 1,
    )

    assert len(shards["A1"]["cloze"]["cloze"]) == 1
    assert shards["A1"]["cloze"]["sizeBudget"]["rawLimitBytes"] == int(
        dedicated_budget["rawBytes"]
    ) + 1


def test_size_budget_surface_trim_prioritizes_cloze_coverage(capsys: pytest.CaptureFixture[str]) -> None:
    lemma_ids = ("a", "b", "c", "d")
    cloze_lemma_ids = ("a", "c", "d")
    index = {
        "schema": "atlas-practice-index",
        "items": [
            {
                "lemmaId": lemma_id,
                "lemma": lemma_id,
                "cefr": "A1",
                "modes": ["flashcards", "cloze"] if lemma_id in cloze_lemma_ids else ["flashcards"],
                "hasCloze": lemma_id in cloze_lemma_ids,
                "clozeIds": [f"{lemma_id}:cloze:1"] if lemma_id in cloze_lemma_ids else [],
                "newOrder": order,
            }
            for order, lemma_id in enumerate(lemma_ids)
        ],
        "counts": {
            "lexemes": len(lemma_ids),
            "cloze": len(cloze_lemma_ids),
            "clozeEligibleLexemes": len(cloze_lemma_ids),
            "clozeCoverage": 0.75,
            "modeCounts": {"cloze": len(cloze_lemma_ids)},
            "modeCoverage": {"cloze": 0.75},
        },
    }
    lexemes = {
        "schema": "atlas-practice-lexemes",
        "lexemes": [
            {"lemmaId": lemma_id, "lemma": lemma_id, "padding": "x" * 1_500}
            for lemma_id in lemma_ids
        ],
    }
    cloze = {
        "schema": "atlas-practice-cloze",
        "cloze": [
            {"clozeId": f"{lemma_id}:cloze:1", "lemmaId": lemma_id, "form": lemma_id}
            for lemma_id in cloze_lemma_ids
        ],
    }
    shards = {"A1": {"index": index, "lexemes": lexemes, "cloze": cloze}}

    probe_index = {**index, "items": index["items"][:2]}
    probe_lexemes = {**lexemes, "lexemes": lexemes["lexemes"][:2]}
    index_budget = generate_practice_deck._size_budget(probe_index, 1_000_000, 1_000_000)
    lexeme_budget = generate_practice_deck._size_budget(probe_lexemes, 1_000_000, 1_000_000)
    apply_size_budgets(
        shards,
        raw_limit=max(int(index_budget["rawBytes"]), int(lexeme_budget["rawBytes"])) + 200,
        gzip_limit=max(int(index_budget["gzipBytes"]), int(lexeme_budget["gzipBytes"])) + 200,
    )

    assert "trimmed surface lexemes 4 -> 2" in capsys.readouterr().err
    assert [item["lemmaId"] for item in shards["A1"]["index"]["items"]] == ["a", "c"]
    assert [item["lemmaId"] for item in shards["A1"]["lexemes"]["lexemes"]] == ["a", "c"]
    assert {item["lemmaId"] for item in shards["A1"]["cloze"]["cloze"]} == {"a", "c"}
    assert shards["A1"]["index"]["counts"]["clozeEligibleLexemes"] == 2
    assert shards["A1"]["index"]["counts"]["clozeCoverage"] == 1.0


def test_size_budget_trims_oversized_mode_without_cutting_cloze_surface(
    capsys: pytest.CaptureFixture[str],
) -> None:
    index = {
        "schema": "atlas-practice-index",
        "items": [
            {
                "lemmaId": "one",
                "lemma": "слово",
                "cefr": "A1",
                "modes": ["flashcards", "cloze"],
                "hasCloze": True,
                "clozeIds": ["one:cloze:1"],
                "newOrder": 0,
            }
        ],
        "counts": {
            "lexemes": 1,
            "cloze": 1,
            "clozeEligibleLexemes": 1,
            "clozeCoverage": 1.0,
            "modeCounts": {"cloze": 1, "classify": 12},
            "modeCoverage": {"cloze": 1.0, "classify": 1.0},
        },
    }
    lexemes = {
        "schema": "atlas-practice-lexemes",
        "lexemes": [{"lemmaId": "one", "lemma": "слово", "cefr": "A1"}],
    }
    cloze = {
        "schema": "atlas-practice-cloze",
        "cloze": [{"clozeId": "one:cloze:1", "lemmaId": "one", "form": "слово"}],
    }
    classify = {
        "schema": "atlas-practice-classify",
        "classify": [
            {"classifyId": f"one:classify:{index}", "lemmaId": "one", "evidence": "x" * 500}
            for index in range(12)
        ],
    }
    shards = {"A1": {"index": index, "lexemes": lexemes, "cloze": cloze, "classify": classify}}
    stable_budgets = [
        generate_practice_deck._size_budget(payload, 1_000_000, 1_000_000)
        for payload in (index, lexemes, cloze)
    ]
    raw_limit = max(int(budget["rawBytes"]) for budget in stable_budgets) + 500
    gzip_limit = max(int(budget["gzipBytes"]) for budget in stable_budgets) + 500

    apply_size_budgets(shards, raw_limit=raw_limit, gzip_limit=gzip_limit)

    captured = capsys.readouterr()
    assert "trimmed classify items" in captured.err
    assert len(shards["A1"]["index"]["items"]) == 1
    assert len(shards["A1"]["lexemes"]["lexemes"]) == 1
    assert len(shards["A1"]["cloze"]["cloze"]) == 1
    assert len(shards["A1"]["classify"]["classify"]) < 12
    assert shards["A1"]["index"]["counts"]["cloze"] == 1
    assert shards["A1"]["index"]["counts"]["modeCounts"]["classify"] < 12
    assert all(
        payload["sizeBudget"]["ok"]
        for payload in shards["A1"].values()
    )


def test_size_budget_skips_final_recompute_when_no_trim_occurs(monkeypatch: pytest.MonkeyPatch) -> None:
    shards = {"A1": {"index": {"schema": "atlas-practice-index", "items": []}}}
    calls = 0
    original_size_budget = generate_practice_deck._size_budget

    def count_size_budget(payload: dict[str, object], raw_limit: int, gzip_limit: int) -> dict[str, int | bool]:
        nonlocal calls
        calls += 1
        return original_size_budget(payload, raw_limit, gzip_limit)

    monkeypatch.setattr(generate_practice_deck, "_size_budget", count_size_budget)

    apply_size_budgets(shards, raw_limit=50_000, gzip_limit=15_000)

    assert calls == 1


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
                        "sentence": "Це книга.",
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
    assert candidates[0]["sentence"] == "Це ___."
    assert candidates[0]["form"] == "книга"
    assert candidates[0]["provenance"]["status"] == "sentence_inventory"
    assert candidates[0]["provenance"]["path"] == str(inventory_path)

    # Force the route that previously built duplicate answer/lemma labels for
    # the nominative form "книга".  Inventory cloze must override it with the
    # valid no-pair strategy.
    monkeypatch.setattr(generate_practice_deck, "_option_strategy_for_level", lambda _level, _rng: "two-pair")

    shards = build_practice_shards(
        read_manifest(MANIFEST),
        ReviewedSourceAllowlist.from_payload(
            [{"status": "sentence_inventory", "path": str(inventory_path)}]
        ),
        JsonVesumVerifier.from_path(VESUM),
        candidates,
        BuildConfig(),
    )
    cloze = next(item for item in shards["A1"]["cloze"]["cloze"] if item["clozeId"] == "knyha:inventory:1")
    assert cloze["blankCase"] == "nominative"
    assert cloze["number"] == "singular"
    assert "clozeEn" not in cloze
    assert cloze["caseRule"]["feedback"] == "словникова (називний) форма: книга"
    labels = [option["label"] for option in cloze["options"]]
    assert len(labels) == len(set(labels)) == 4
    assert {option["strategy"] for option in cloze["options"]} == {"no-pair"}
    assert validate_option_set(cloze) == []
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
    verifier = JsonVesumVerifier(
        {"книга": [{"lemma": "книга", "pos": "noun", "tags": "noun:inanim:f:v_naz"}]}
    )

    assert generate_practice_deck._inventory_form_details(
        "книга", "noun", "Книга", verifier
    ) == ("nominative", "singular")


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
    allowlist = ReviewedSourceAllowlist.from_payload(
        [{"status": "sentence_inventory", "path": str(inventory_path)}]
    )
    verifier = JsonVesumVerifier({"та": [{"lemma": "та", "pos": "conj", "tags": "conj"}]})

    assert _build_cloze_items(lexeme, candidates, allowlist, verifier, "deck-v6") == []

    curated = [{**candidates[0], "curated": True}]
    assert len(_build_cloze_items(lexeme, curated, allowlist, verifier, "deck-v6")) == 1


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


def test_inventory_identity_decoys_are_seeded_and_length_matched() -> None:
    lexemes = _fixture_lexemes()
    answer = next(lexeme for lexeme in lexemes if lexeme["lemmaId"] == "knyha")
    cloze = {
        "clozeId": "knyha:inventory:1",
        "form": "книга",
        "lemma": "книга",
        "provenance": {"status": "sentence_inventory"},
        "caseRule": {"ruleId": "nominative_identification"},
    }

    first = generate_practice_deck._make_no_pair_options(
        cloze, answer, lexemes, random.Random(0)
    )
    second = generate_practice_deck._make_no_pair_options(
        cloze, answer, lexemes, random.Random(1)
    )
    first_decoys = [option["label"] for option in first if option["kind"] != "answer"]
    second_decoys = [option["label"] for option in second if option["kind"] != "answer"]

    assert len(first_decoys) == len(second_decoys) == 3
    assert all(abs(len(label) - len("книга")) <= 3 for label in first_decoys + second_decoys)
    assert first_decoys != second_decoys


def test_inventory_identity_decoys_exclude_phrase_labels() -> None:
    answer = {
        "lemmaId": "po-druhe",
        "lemma": "по-друге",
        "lemmaPlain": "по-друге",
        "gloss": "secondly",
        "pos": "phrase",
        "cefr": "A2",
    }
    clean_decoys = [
        {
            "lemmaId": lemma,
            "lemma": lemma,
            "gloss": "fixture",
            "pos": "phrase",
            "cefr": "A1",
        }
        for lemma in ("Привіт", "Нормально", "Чудово")
    ]
    phrase_decoys = [
        {
            "lemmaId": lemma,
            "lemma": lemma,
            "gloss": "fixture",
            "pos": "phrase",
            "cefr": "A1",
        }
        for lemma in ("Звідки ти?", "Як справи?")
    ]
    cloze = {
        "clozeId": "po-druhe:inventory:1",
        "form": "По-друге",
        "lemma": "по-друге",
        "provenance": {"status": "sentence_inventory"},
        "caseRule": {"ruleId": "nominative_identification"},
    }

    options = generate_practice_deck._make_no_pair_options(
        cloze, answer, [answer, *clean_decoys, *phrase_decoys], random.Random(0)
    )

    assert len(options) == 4
    assert all("?" not in option["label"] for option in options)
    assert validate_option_set({**cloze, "options": options}) == []


def test_inventory_identity_decoys_use_attested_surface_capitalization() -> None:
    lexemes = _fixture_lexemes()
    answer = next(lexeme for lexeme in lexemes if lexeme["lemmaId"] == "knyha")
    capitalized_decoy = {
        **next(lexeme for lexeme in lexemes if lexeme["lemmaId"] == "misto"),
        "lemmaId": "kyiv",
        "lemma": "Київ",
        "gloss": "Kyiv",
    }
    cloze = {
        "clozeId": "knyha:inventory:capitalized",
        "form": "Книга",
        "lemma": "книга",
        "provenance": {"status": "sentence_inventory"},
        "caseRule": {"ruleId": "nominative_identification"},
    }

    options = generate_practice_deck._make_no_pair_options(
        cloze, answer, [*lexemes, capitalized_decoy], random.Random(0)
    )

    assert len(options) == 4
    assert any(
        option["kind"] != "answer" and generate_practice_deck._initial_capitalization(option["label"])
        for option in options
    )
    assert validate_option_set({**cloze, "options": options}) == []


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

    options = generate_practice_deck._make_no_pair_options(
        cloze, answer, lexemes, random.Random(0)
    )

    assert len(options) == 4
    assert all(
        generate_practice_deck._initial_capitalization(option["label"])
        for option in options
    )
    assert validate_option_set({**cloze, "options": options}) == []


@pytest.mark.parametrize(
    ("manifest_pos", "expected_bucket"),
    [
        ("infinitive", "verb"),
        ("imperative", "verb"),
        ("numr", "numeral"),
        ("intj", "interjection"),
    ],
)
def test_option_pos_bucket_normalizes_unambiguous_manifest_aliases(
    manifest_pos: str, expected_bucket: str
) -> None:
    assert generate_practice_deck._option_pos_bucket(manifest_pos) == expected_bucket


def test_sentence_inventory_identity_cloze_scales_across_levels_and_pos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
        entry("апостроф", "apostrof", "apostrophe", "noun", "A1"),
        entry("книга", "knyha", "book", "noun", "A1"),
        entry("місто", "misto", "city", "noun", "A1"),
        entry("школа", "shkola", "school", "noun", "A1"),
        entry("аналогічно", "analogichno", "similarly", "adverb", "A2"),
        entry("постійно", "postiino", "always", "adv", "A2"),
        entry("зазвичай", "zazvychai", "usually", "adv", "A2"),
        entry("поступово", "postupovo", "gradually", "adv", "A2"),
    ]
    inventory_path = tmp_path / "sentence-inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": "atlas-sentence-inventory",
                "schemaVersion": 1,
                "rows": [
                    {
                        "lemma": "апостроф",
                        "lemmaId": "apostrof",
                        "sentence": "Це апостроф.",
                        "targetForm": "апостроф",
                        "cefr": "A1",
                        "uses": ["example"],
                        "provenance": {
                            "source": "fixture-textbook",
                            "label": "Fixture textbook",
                            "locator": "a1-1",
                        },
                        "license": {"status": "fixture"},
                    },
                    {
                        "lemma": "аналогічно",
                        "lemmaId": "analogichno",
                        "sentence": "Це аналогічно.",
                        "targetForm": "аналогічно",
                        "cefr": "A2",
                        "uses": ["example"],
                        "provenance": {
                            "source": "fixture-textbook",
                            "label": "Fixture textbook",
                            "locator": "a2-1",
                        },
                        "license": {"status": "fixture"},
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    vesum_path = tmp_path / "vesum.json"
    vesum_path.write_text(
        json.dumps(
            {
                # Two same-lemma analyses prove that dictionary-form identity
                # clozes do not require an arbitrary single VESUM case.
                "апостроф": [
                    {"lemma": "апостроф", "pos": "noun", "tags": "noun:inanim:m:v_naz"},
                    {"lemma": "апостроф", "pos": "noun", "tags": "noun:inanim:m:v_zna"},
                ],
                "аналогічно": [{"lemma": "аналогічно", "pos": "adv", "tags": "adv"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(generate_practice_deck, "_option_strategy_for_level", lambda _level, _rng: "no-pair")
    candidates = read_sentence_inventory(inventory_path)
    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_payload(
            [{"status": "sentence_inventory", "path": str(inventory_path)}]
        ),
        JsonVesumVerifier.from_path(vesum_path),
        candidates,
        BuildConfig(target=len(entries), source_label="fixture"),
    )

    for level, lemma_id, pos in (
        ("A1", "apostrof", "noun"),
        ("A2", "analogichno", "adverb"),
    ):
        cloze = next(
            item for item in shards[level]["cloze"]["cloze"] if item["lemmaId"] == lemma_id
        )
        assert cloze["provenance"]["status"] == "sentence_inventory"
        assert cloze["attribution"] == {
            "source": "fixture-textbook",
            "label": "Fixture textbook",
            "locator": "a1-1" if level == "A1" else "a2-1",
        }
        assert cloze["blankCase"] == "nominative"
        assert len(cloze["options"]) == 4
        assert {option["pos"] for option in cloze["options"]} == {pos}
        assert validate_option_set(cloze) == []

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
        ReviewedSourceAllowlist.from_payload(
            [{"status": "sentence_inventory", "path": str(inventory_path)}]
        ),
        JsonVesumVerifier.from_path(VESUM),
        candidates,
        BuildConfig(),
    )

    assert all(
        item["clozeId"] != "knyha:inventory:1"
        for level in shards.values()
        for item in level["cloze"]["cloze"]
    )


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
        ReviewedSourceAllowlist.from_payload(
            [{"status": "sentence_inventory", "path": str(inventory_path)}]
        ),
        JsonVesumVerifier.from_path(VESUM),
        read_sentence_inventory(inventory_path),
        BuildConfig(),
    )

    assert all(
        item["clozeId"] != "knyha:inventory:1"
        for level in shards.values()
        for item in level["cloze"]["cloze"]
    )


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


def test_paronym_builder_copies_optional_curated_prompt_en() -> None:
    lex_a = {"lemmaId": "бігати", "lemma": "бігати", "cefr": "B1"}
    lex_b = {"lemmaId": "бігти", "lemma": "бігти", "cefr": "B1"}
    pair = {
        "slugA": "бігати",
        "slugB": "бігти",
        "distinction_gloss_uk": "Бігати регулярно, бігти конкретно зараз.",
        "citations": ["fixture-test"],
        "frames": [{
            "sentence_with_slot": "Він ___ вранці.",
            "prompt_en": "He ___ in the morning.",
            "answer_form": "бігає",
            "confusable_form": "біжить",
            "origin": "fixture",
        }],
    }

    item = _build_paronym_items(pair, lex_a, lex_b, "deck-v1")[0]
    assert item["promptEn"] == "He ___ in the morning."

    pair["frames"][0].pop("prompt_en")
    item_without_en = _build_paronym_items(pair, lex_a, lex_b, "deck-v1")[0]
    assert "promptEn" not in item_without_en

    pair["frames"][0]["prompt_en"] = "Context sentence for бігати"
    placeholder_item = _build_paronym_items(pair, lex_a, lex_b, "deck-v1")[0]
    assert "promptEn" not in placeholder_item


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


def test_live_paronym_pairs_yaml_is_valid_and_has_promoted_candidates() -> None:
    live_path = Path("data/lexicon/paronym_pairs.yaml")
    assert live_path.exists()
    pairs = read_paronym_pairs(live_path)
    assert len(pairs) == 103, f"Expected 103 paronym pairs (55 baseline + 48 promoted), got {len(pairs)}"
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
def test_antonym_pairs_emit_items_both_directions_and_validate(capsys: pytest.CaptureFixture[str]) -> None:
    entries = [
        {"lemmaId": "день", "lemma": "день", "gloss": "day", "pos": "noun", "cefr": "A1", "url_slug": "день", "primary_source": "course_vocab", "course_usage": [{"track": "a1"}]},
        {"lemmaId": "ніч", "lemma": "ніч", "gloss": "night", "pos": "noun", "cefr": "A1", "url_slug": "ніч", "primary_source": "course_vocab", "course_usage": [{"track": "a1"}]},
    ]
    pair = {
        "slugA": "день",
        "slugB": "ніч",
        "distinction_gloss_uk": "День протилежний ночі.",
        "citations": ["fixture-test"],
        "frames": [
            {"sentence_with_slot": "Настав ___.", "answer_form": "день", "confusable_form": "ніч", "origin": "t"},
            {"sentence_with_slot": "Прийшла ___.", "answer_form": "ніч", "confusable_form": "день", "origin": "t2"},
        ],
    }
    allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier({})
    shards = build_practice_shards(entries, allowlist, verifier, [], BuildConfig(target=10), antonym_pairs=[pair])
    a1_items = shards.get("A1", {}).get("antonym", {}).get("antonym", [])
    assert len(a1_items) >= 1, "antonym should emit at least one item"
    assert validate_antonym_pair(pair) == []
    for it in a1_items:
        assert validate_antonym_item(it) == []


def test_antonym_builder_copies_optional_curated_prompt_en() -> None:
    lex_a = {"lemmaId": "великий", "lemma": "великий", "cefr": "A1"}
    lex_b = {"lemmaId": "малий", "lemma": "малий", "cefr": "A1"}
    pair = {
        "slugA": "великий",
        "slugB": "малий",
        "distinction_gloss_uk": "Великий проти малий.",
        "citations": ["fixture-test"],
        "frames": [{
            "sentence_with_slot": "Це ___ будинок.",
            "prompt_en": "This is a ___ house.",
            "answer_form": "великий",
            "confusable_form": "малий",
            "origin": "fixture",
        }],
    }

    item = _build_antonym_items(pair, lex_a, lex_b, "deck-v1")[0]
    assert item["promptEn"] == "This is a ___ house."

    pair["frames"][0].pop("prompt_en")
    item_without_en = _build_antonym_items(pair, lex_a, lex_b, "deck-v1")[0]
    assert "promptEn" not in item_without_en


def test_antonym_missing_slug_skips_with_warn(capsys: pytest.CaptureFixture[str]) -> None:
    entries = [{"lemmaId": "foo", "lemma": "foo", "gloss": "x", "pos": "noun", "cefr": "B1", "url_slug": "foo", "primary_source": "course_vocab", "course_usage": [{"track": "b1"}]}]
    pair = {"slugA": "missingA", "slugB": "missingB", "distinction_gloss_uk": "x", "citations": ["t"], "frames": [{"sentence_with_slot": "X ___ .", "answer_form": "x", "confusable_form": "y", "origin": "o"}]}
    allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier({})
    shards = build_practice_shards(entries, allowlist, verifier, [], BuildConfig(), antonym_pairs=[pair])
    assert shards["B1"]["antonym"]["antonym"] == []
    err = capsys.readouterr().err
    assert "not in practice lexemes; emitted 0 items" in err


def test_antonym_empty_file_emits_empty_fail_closed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = tmp_path / "empty-ant.yaml"
    p.write_text("schema_version: 1\npairs: []\n", encoding="utf-8")
    rows = read_antonym_pairs(p)
    assert rows == []
    err = capsys.readouterr().err
    assert "curated antonym pairs empty" in err
    entries = [{"lemmaId": "a", "lemma": "a", "gloss": "g", "pos": "n", "cefr": "B1", "url_slug": "a", "primary_source": "c", "course_usage": [{}]}]
    shards = build_practice_shards(entries, ReviewedSourceAllowlist.from_payload([]), JsonVesumVerifier({}), [], BuildConfig(), antonym_pairs=[])
    assert shards["B1"]["antonym"]["antonym"] == []


def test_live_antonym_pairs_yaml_is_valid_and_has_promoted_candidates() -> None:
    live_path = Path("data/lexicon/antonym_pairs.yaml")
    assert live_path.exists()
    pairs = read_antonym_pairs(live_path)
    assert len(pairs) == 392, f"Expected 392 reviewed antonym pairs, got {len(pairs)}"
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


def test_homonym_pairs_emit_items_both_directions_and_validate(capsys: pytest.CaptureFixture[str]) -> None:
    entries = [
        {"lemmaId": "байка", "lemma": "байка", "gloss": "fable/fabric", "pos": "noun", "cefr": "A1", "url_slug": "байка", "primary_source": "course_vocab", "course_usage": [{"track": "a1"}]},
    ]
    pair = {
        "slugA": "байка",
        "slugB": "байка",
        "distinction_gloss_uk": "Байка — алегоричний твір чи м'яка тканина.",
        "citations": ["fixture-test"],
        "frames": [
            {"sentence_with_slot": "Езоп написав ___.", "answer_form": "байку", "confusable_form": "байку", "origin": "t"},
            {"sentence_with_slot": "Сорочка з м'якої ___.", "answer_form": "байки", "confusable_form": "байки", "origin": "t2"},
        ],
    }
    allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier({})
    shards = build_practice_shards(entries, allowlist, verifier, [], BuildConfig(target=10), homonym_pairs=[pair])
    a1_items = shards.get("A1", {}).get("homonym", {}).get("homonym", [])
    assert len(a1_items) >= 1, "homonym should emit at least one item"
    assert validate_homonym_pair(pair) == []
    for it in a1_items:
        assert validate_homonym_item(it) == []


def test_homonym_builder_copies_optional_curated_prompt_en() -> None:
    lex_a = {"lemmaId": "байка", "lemma": "байка", "cefr": "A1"}
    lex_b = {"lemmaId": "байка", "lemma": "байка", "cefr": "A1"}
    pair = {
        "slugA": "байка",
        "slugB": "байка",
        "distinction_gloss_uk": "Байка розрізнення.",
        "citations": ["fixture-test"],
        "frames": [{
            "sentence_with_slot": "Езоп написав ___.",
            "prompt_en": "Aesop wrote a ___.",
            "answer_form": "байку",
            "confusable_form": "байку",
            "origin": "fixture",
        }],
    }

    item = _build_homonym_items(pair, lex_a, lex_b, "deck-v1")[0]
    assert item["promptEn"] == "Aesop wrote a ___."

    pair["frames"][0].pop("prompt_en")
    item_without_en = _build_homonym_items(pair, lex_a, lex_b, "deck-v1")[0]
    assert "promptEn" not in item_without_en


def test_homonym_missing_slug_skips_with_warn(capsys: pytest.CaptureFixture[str]) -> None:
    entries = [{"lemmaId": "foo", "lemma": "foo", "gloss": "x", "pos": "noun", "cefr": "B1", "url_slug": "foo", "primary_source": "course_vocab", "course_usage": [{"track": "b1"}]}]
    pair = {"slugA": "missingA", "slugB": "missingB", "distinction_gloss_uk": "x", "citations": ["t"], "frames": [{"sentence_with_slot": "X ___ .", "answer_form": "x", "confusable_form": "y", "origin": "o"}]}
    allowlist = ReviewedSourceAllowlist.from_payload([])
    verifier = JsonVesumVerifier({})
    shards = build_practice_shards(entries, allowlist, verifier, [], BuildConfig(), homonym_pairs=[pair])
    assert shards["B1"]["homonym"]["homonym"] == []
    err = capsys.readouterr().err
    assert "not in practice lexemes; emitted 0 items" in err


def test_homonym_empty_file_emits_empty_fail_closed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = tmp_path / "empty-hom.yaml"
    p.write_text("schema_version: 1\npairs: []\n", encoding="utf-8")
    rows = read_homonym_pairs(p)
    assert rows == []
    err = capsys.readouterr().err
    assert "curated homonym pairs empty" in err
    entries = [{"lemmaId": "a", "lemma": "a", "gloss": "g", "pos": "n", "cefr": "B1", "url_slug": "a", "primary_source": "c", "course_usage": [{}]}]
    shards = build_practice_shards(entries, ReviewedSourceAllowlist.from_payload([]), JsonVesumVerifier({}), [], BuildConfig(), homonym_pairs=[])
    assert shards["B1"]["homonym"]["homonym"] == []


def test_live_homonym_pairs_yaml_is_valid_and_has_promoted_candidates() -> None:
    live_path = Path("data/lexicon/homonym_pairs.yaml")
    assert live_path.exists()
    pairs = read_homonym_pairs(live_path)
    assert len(pairs) == 75, f"Expected 75 homonym pairs, got {len(pairs)}"
    for index, pair in enumerate(pairs):
        errors = validate_homonym_pair(pair)
        assert not errors, f"Pair {index} ({pair.get('slugA')}/{pair.get('slugB')}) invalid: {errors}"
