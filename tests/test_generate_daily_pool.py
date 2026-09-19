from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.atlas import atlas_db
from scripts.audit.generate_daily_pool import (
    DEFAULT_OUT,
    VERIFIED_ENGLISH_GLOSSES,
    VERIFIED_SENTENCE_EN,
    _clean_origin,
    _entry_gloss,
    _first_origin,
    _is_eligible,
    _pool_item,
    build_pool,
    compute_weight,
    load_db_entries,
    main,
)


def fixture_entries() -> list[dict[str, object]]:
    return [
        {
            "lemma": "баба",
            "url_slug": "baba",
            "gloss": "grandmother",
            "primary_source": "course",
            "course_usage": [
                {
                    "track": "a1",
                    "module_num": 1,
                    "slug": "family",
                    "context": "Баба вдома.",
                }
            ],
            # Real manifest shape: enrichment.cefr is a dict, not a bare string (#PR2 regression guard).
            "enrichment": {"cefr": {"level": "B2", "source": "estimated", "text": "B2"}},
        },
        {
            "lemma": "авось",
            "url_slug": "avos",
            "gloss": "avoid: ану ж",
            "primary_source": "surzhyk_to_avoid",
            "course_usage": [],
        },
        {
            "lemma": "дім",
            "url_slug": "dim",
            "gloss": "house",
            "primary_source": "course",
            "course_usage": [],
            "enrichment": {"cefr": {"level": "A1", "source": "estimated", "text": "A1"}},
        },
        {
            "lemma": "жмур",
            "url_slug": "zhmur",
            "gloss": None,
            "primary_source": "remainder",
            "course_usage": [],
        },
        {
            "lemma": "добрий день",
            "url_slug": "dobryi-den",
            "gloss": "good afternoon",
            "primary_source": "remainder",
            "course_usage": [],
        },
    ]


def test_compute_weight_rules() -> None:
    entries = fixture_entries()

    assert compute_weight(entries[0]) == 3
    assert compute_weight(entries[1]) == 2
    assert compute_weight(entries[2]) == 2
    assert compute_weight(entries[3]) == 0
    assert compute_weight(entries[4]) == 0


def test_build_pool_schema_sorting_and_filters() -> None:
    pool = build_pool(fixture_entries(), size=10)

    assert [item["lemma"] for item in pool] == ["баба", "добрий день", "дім"]
    assert "жмур" not in {item["lemma"] for item in pool}
    assert "авось" not in {item["lemma"] for item in pool}
    assert "добрий день" in {item["lemma"] for item in pool}
    assert all(item["k"] != "avoid" for item in pool)

    by_lemma = {item["lemma"]: item for item in pool}
    assert by_lemma["баба"] == {
        "lemma": "баба",
        "slug": "baba",
        "gloss": "grandmother",
        "k": "other",
        "weight": 3,
        "lessonTag": "a1",
        # #6728: the pool emits a row's TRUE CEFR level, not just A1/A2/B1 — so the
        # B2 enrichment on this fixture now reaches the served artifact.
        "cefr": "B2",
    }
    assert by_lemma["дім"] == {
        "lemma": "дім",
        "slug": "dim",
        "gloss": "house",
        "k": "other",
        "weight": 2,
        "cefr": "A1",
    }
    assert set(by_lemma["добрий день"]) == {"lemma", "slug", "gloss", "k", "weight"}


def test_build_pool_includes_pos_when_present_and_omits_key_when_absent() -> None:
    """#5856 fix-round-2: the pool row must carry `pos` (same conditional-omit
    style as cefr/lessonTag) — the served artifact was silently dropping it,
    so payload-first pos could never reach production."""
    entries = [
        {
            "lemma": "баба",
            "url_slug": "baba",
            "gloss": "grandmother",
            "pos": "noun",
            "primary_source": "course",
            "course_usage": [],
        },
        {
            "lemma": "дім",
            "url_slug": "dim",
            "gloss": "house",
            "pos": "",
            "primary_source": "course",
            "course_usage": [],
        },
        {
            "lemma": "жити",
            "url_slug": "zhyty",
            "gloss": "to live",
            "primary_source": "course",
            "course_usage": [],
        },
    ]

    by_lemma = {item["lemma"]: item for item in build_pool(entries, size=10)}

    assert by_lemma["баба"]["pos"] == "noun"
    # An empty-string pos and an absent pos both mean "no signal" — never emit null spam.
    assert "pos" not in by_lemma["дім"]
    assert "pos" not in by_lemma["жити"]


def test_build_pool_prefers_inventory_example_with_provenance() -> None:
    inventory = {
        "баба": {
            "lemma": "баба",
            "sentence": "Баба читає книжку.",
            "provenance": {"source": "textbook", "label": "Ukrainian school textbook"},
            "license": {"status": "not_openly_licensed"},
        }
    }

    row = next(item for item in build_pool(fixture_entries(), sentence_inventory=inventory) if item["lemma"] == "баба")

    assert row["example"] == "Баба читає книжку."
    assert row["exampleProvenance"] == inventory["баба"]["provenance"]
    assert row["exampleLicense"] == inventory["баба"]["license"]


def test_build_pool_top_n_uses_weight_then_lemma() -> None:
    pool = build_pool(fixture_entries(), size=2)

    assert [item["lemma"] for item in pool] == ["баба", "дім"]


def test_build_pool_excludes_derived_forms_and_avoid_classified_lemmas() -> None:
    entries = [
        # Inflected/normalized duplicate — must be dropped even though it has a gloss + course.
        {
            "lemma": "автобусом",
            "url_slug": "avtobusom",
            "gloss": "by bus (instr.)",
            "primary_source": "built_vocabulary_form",
            "course_usage": [{"track": "a1", "module_num": 2, "slug": "transport", "context": "x"}],
            "enrichment": {"cefr": {"level": "A1", "source": "estimated", "text": "A1"}},
        },
        # Highest possible weight (course + early CEFR = 5).
        {
            "lemma": "автобус",
            "url_slug": "avtobus",
            "gloss": "bus",
            "primary_source": "built_vocabulary",
            "course_usage": [{"track": "a1", "module_num": 2, "slug": "transport", "context": "x"}],
            "enrichment": {"cefr": {"level": "A1", "source": "estimated", "text": "A1"}},
        },
        # Avoid-classified: an error-modeling lemma must never enter a neutral daily pool.
        {
            "lemma": "всьо",
            "url_slug": "vso",
            "gloss": "avoid: все",
            "primary_source": "surzhyk_to_avoid",
            "course_usage": [],
        },
    ]

    pool = build_pool(entries, size=10)

    assert "автобусом" not in {item["lemma"] for item in pool}
    assert "всьо" not in {item["lemma"] for item in pool}
    assert all(item["k"] != "avoid" for item in pool)
    assert [item["lemma"] for item in build_pool(entries, size=1)] == ["автобус"]


def test_main_writes_deterministic_json_bytes(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"entries": fixture_entries()}, ensure_ascii=False),
        encoding="utf-8",
    )
    out_one = tmp_path / "one.json"
    out_two = tmp_path / "two.json"

    assert main(["--manifest", str(manifest), "--out", str(out_one), "--size", "10"]) == 0
    assert main(["--manifest", str(manifest), "--out", str(out_two), "--size", "10"]) == 0

    assert out_one.read_bytes() == out_two.read_bytes()
    assert out_one.read_text(encoding="utf-8").endswith("\n")


def _daily_atlas_db(tmp_path: Path) -> Path:
    """Materialize a fixture atlas.db from a small manifest via the real migrator.

    Two eligible public lemma articles, one gloss-less lemma (admission-excluded),
    and one ``form_of`` alias route (payload-only, no ``articles`` row) that the
    entry-model SSOT must keep out of Word-of-the-Day.
    """
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "lemma": "баба",
                        "url_slug": "baba",
                        "gloss": "grandmother",
                        "primary_source": "course",
                        "course_usage": [{"track": "a1", "module_num": 1, "slug": "family", "context": "x"}],
                        "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
                    },
                    {
                        "lemma": "дім",
                        "url_slug": "dim",
                        "gloss": "house",
                        "primary_source": "course",
                        "course_usage": [],
                        "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
                    },
                    # No gloss → admission-excluded by build_pool, but still an article row.
                    {"lemma": "жмур", "url_slug": "zhmur", "primary_source": "remainder"},
                    # form_of alias route: public payload, NO articles row → structurally excluded.
                    {"lemma": "бабу", "url_slug": "babu", "form_of": {"url_slug": "baba"}},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "atlas.db"
    atlas_db.migrate_manifest(manifest, db)
    return db


def test_load_db_entries_returns_only_approved_public_articles(tmp_path) -> None:
    entries = load_db_entries(_daily_atlas_db(tmp_path))

    slugs = {entry["url_slug"] for entry in entries}
    # form_of alias route (babu) has no articles row → never a candidate.
    assert slugs == {"baba", "dim", "zhmur"}
    assert "babu" not in slugs


def test_db_mode_matches_manifest_admission_and_excludes_form_of(tmp_path) -> None:
    db = _daily_atlas_db(tmp_path)

    # payload_json stores the exact public manifest entry, so DB-sourced admission
    # is identical to manifest-sourced admission over the same article rows.
    article_entries = [
        {
            "lemma": "баба",
            "url_slug": "baba",
            "gloss": "grandmother",
            "primary_source": "course",
            "course_usage": [{"track": "a1", "module_num": 1, "slug": "family", "context": "x"}],
            "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
        },
        {
            "lemma": "дім",
            "url_slug": "dim",
            "gloss": "house",
            "primary_source": "course",
            "course_usage": [],
            "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
        },
        {"lemma": "жмур", "url_slug": "zhmur", "primary_source": "remainder"},
    ]
    assert build_pool(load_db_entries(db), 300) == build_pool(article_entries, 300)

    out = tmp_path / "pool.json"
    assert main(["--db", str(db), "--out", str(out), "--size", "300"]) == 0
    pool = json.loads(out.read_text(encoding="utf-8"))
    assert [item["lemma"] for item in pool] == ["баба", "дім"]  # жмур dropped (no gloss)
    assert "babu" not in {item["slug"] for item in pool}


def test_db_mode_carries_pos_from_migrated_article_into_pool_row(tmp_path) -> None:
    """#5856 fix-round-2 production gap: `articles.pos` was populated in
    `atlas.db` all along, but `_pool_item` never copied it into the served
    pool row. Exercise the real migration path (manifest -> atlas_db ->
    payload_json -> load_db_entries -> build_pool -> main's JSON file) so a
    regression here is caught end to end, not just at the dict-fixture level."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "lemma": "баба",
                        "url_slug": "baba",
                        "gloss": "grandmother",
                        "pos": "noun",
                        "primary_source": "course",
                        "course_usage": [{"track": "a1", "module_num": 1, "slug": "family", "context": "x"}],
                        "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
                    },
                    {
                        "lemma": "дім",
                        "url_slug": "dim",
                        "gloss": "house",
                        "primary_source": "course",
                        "course_usage": [],
                        "enrichment": {"cefr": {"level": "A1", "source": "est", "text": "A1"}},
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "atlas.db"
    atlas_db.migrate_manifest(manifest, db)

    out = tmp_path / "pool.json"
    assert main(["--db", str(db), "--out", str(out), "--size", "300"]) == 0
    pool = {item["lemma"]: item for item in json.loads(out.read_text(encoding="utf-8"))}

    assert pool["баба"]["pos"] == "noun"
    assert "pos" not in pool["дім"]


def test_db_mode_writes_deterministic_json_bytes(tmp_path) -> None:
    db = _daily_atlas_db(tmp_path)
    out_one = tmp_path / "one.json"
    out_two = tmp_path / "two.json"

    assert main(["--db", str(db), "--out", str(out_one), "--size", "300"]) == 0
    assert main(["--db", str(db), "--out", str(out_two), "--size", "300"]) == 0
    assert out_one.read_bytes() == out_two.read_bytes()
    assert out_one.read_text(encoding="utf-8").endswith("\n")


def test_build_pool_keeps_source_inventory_browse_only_by_default() -> None:
    entries = [
        {
            "lemma": "барабан",
            "url_slug": "baraban",
            "gloss": "drum",
            "primary_source": "source_inventory_grow",
            "course_usage": [],
            "enrichment": {"cefr": {"level": "A1", "source": "fixture", "text": "A1"}},
        },
        {
            "lemma": "кіт",
            "url_slug": "kit",
            "gloss": "cat",
            "primary_source": "source_inventory_grow",
            "course_usage": [],
            "enrichment": {"cefr": {"level": "A1", "source": "fixture", "text": "A1"}},
            "surface_admission": {"daily": True},
        },
    ]

    assert [item["lemma"] for item in build_pool(entries, size=10)] == ["кіт"]


def test_clean_origin_strips_latin_parentheticals_and_comparisons() -> None:
    raw = "From наштовх(ну́ти) (naštovx(núty)) + -увати (-uvaty)."
    assert _clean_origin(raw) == "From наштовх(ну́ти) + -увати."

    compare = "From одно- + кімна́та + -ний. Compare Russian одноко́мнатный."
    assert _clean_origin(compare) == "From одно- + кімна́та + -ний."


def test_clean_origin_rejects_garbage_and_esum_labels() -> None:
    assert _clean_origin("   ") is None
    assert _clean_origin("(núty) (odnokómnatnyj)") is None
    assert _clean_origin("Стаття ЕСУМ: вода; етимонів: 3.") is None


def test_first_origin_only_returns_kaikki_sourced_prose() -> None:
    kaikki_entry = {
        "lemma": "монета",
        "url_slug": "moneta",
        "gloss": "coin",
        "primary_source": "course",
        "course_usage": [],
        "enrichment": {"etymology": {"text": "From Latin monēta.", "source": "kaikki/Wiktionary (CC BY-SA 3.0)"}},
    }
    esum_entry = {
        "lemma": "вода",
        "url_slug": "voda",
        "gloss": "water",
        "primary_source": "course",
        "course_usage": [],
        "enrichment": {"etymology": {"text": "Стаття ЕСУМ: вода; етимонів: 3.", "source": "ЕСУМ"}},
    }

    assert _first_origin(kaikki_entry) == "From Latin monēta."
    assert _first_origin(esum_entry) is None


def test_build_pool_carries_cleaned_etymology_for_kaikki_origin() -> None:
    entries = [
        {
            "lemma": "монета",
            "url_slug": "moneta",
            "gloss": "coin",
            "primary_source": "course",
            "course_usage": [],
            "enrichment": {
                "cefr": {"level": "A1", "source": "fixture", "text": "A1"},
                "etymology": {
                    "text": "From Latin monēta.",
                    "source": "kaikki/Wiktionary (CC BY-SA 3.0)",
                },
            },
        },
        {
            "lemma": "вода",
            "url_slug": "voda",
            "gloss": "water",
            "primary_source": "course",
            "course_usage": [],
            "enrichment": {
                "cefr": {"level": "A1", "source": "fixture", "text": "A1"},
                "etymology": {
                    "text": "Стаття ЕСУМ: вода; етимонів: 3.",
                    "source": "ЕСУМ",
                },
            },
        },
    ]

    pool = {item["lemma"]: item for item in build_pool(entries, size=10)}
    assert pool["монета"]["etymology"] == "From Latin monēta."
    assert "etymology" not in pool["вода"]


def _level_entry(lemma: str, slug: str, level: str) -> dict[str, object]:
    return {
        "lemma": lemma,
        "url_slug": slug,
        "gloss": f"gloss for {lemma}",
        "primary_source": "course",
        "course_usage": [],
        "enrichment": {"cefr": {"level": level, "source": "fixture", "text": level}},
    }


def test_build_pool_emits_true_cefr_level_above_b1() -> None:
    """#6728: a B2/C1/C2 enrichment must reach the served row. The old `_early_cefr`
    cap hid every level above B1, so the WotD C-level tabs could never match a card."""
    for level in ("B2", "C1", "C2"):
        pool = build_pool([_level_entry("слово", "slovo", level)], size=10)
        assert pool[0]["cefr"] == level, f"level {level} was dropped from the pool row"


def test_build_pool_reserves_slots_for_every_present_cefr_level() -> None:
    """#6728: the pool must actually CONTAIN C1/B2 lemmas, not merely emit a CEFR
    field. Selection is level-stratified so a flood of A1/A2/B1 words can no longer
    crowd every C1 word out of the top-N — each present level gets its quota first."""
    entries = [_level_entry(f"а{i}", f"a{i}", "A1") for i in range(200)]
    entries += [_level_entry(f"б{i}", f"b{i}", "C1") for i in range(60)]
    entries += [_level_entry(f"в{i}", f"v{i}", "B2") for i in range(60)]

    # size=120, min_per_level=40 → 40 C1 + 40 B2 reserved before the A1 fill.
    pool = build_pool(entries, size=120, min_per_level=40)
    by_level: dict[str | None, int] = {}
    for item in pool:
        by_level[item.get("cefr")] = by_level.get(item.get("cefr"), 0) + 1

    assert by_level.get("C1", 0) == 40
    assert by_level.get("B2", 0) == 40
    # The remaining 40 slots fill from the weighted pool (A1 dominates by count).
    assert by_level.get("A1", 0) == 40
    assert len(pool) == 120


def test_build_pool_includes_c1_words_alongside_a_lower_level_majority() -> None:
    """#6728 integration shape: with default quotas, a large beginner majority must
    not erase C1 representation. Mirrors the real manifest where ~4400 A1/A2/B1
    eligible words used to squeeze out all 596 C1 candidates."""
    entries = [_level_entry(f"а{i:03d}", f"a{i:03d}", "A1") for i in range(300)]
    entries += [_level_entry(f"с{i:03d}", f"s{i:03d}", "C1") for i in range(50)]

    pool = build_pool(entries, size=300)
    c1 = [item for item in pool if item.get("cefr") == "C1"]
    assert len(c1) == 40  # default MIN_PER_LEVEL
    # Every C1 card carries its true level so the WotD C1 tab can match it.
    assert all(item["cefr"] == "C1" for item in c1)


def test_entry_gloss_and_eligibility_enforces_english() -> None:
    """#8258: raw Cyrillic definitions from СУМ/ВТС must not leak into the daily pool
    without a verified English gloss; verified English glosses must be applied."""
    # Entry with pure Cyrillic definition from СУМ/ВТС not in VERIFIED_ENGLISH_GLOSSES
    cyrillic_unverified = {
        "lemma": "невідомеслово",
        "url_slug": "nevidomeslovo",
        "gloss": "який не потребує коштів, оплати; безплатний",
        "primary_source": "course",
    }
    assert _entry_gloss(cyrillic_unverified) is None
    assert not _is_eligible(cyrillic_unverified)

    # Entry with verified English gloss override
    verified_entry = {
        "lemma": "дівчина",
        "url_slug": "дівчина",
        "gloss": "молода неодружена особа жіночої статі",
        "primary_source": "course",
        "entry_type": "lexeme",
    }
    assert _entry_gloss(verified_entry) == VERIFIED_ENGLISH_GLOSSES["дівчина"]
    assert _is_eligible(verified_entry)

    # Entry with standard English gloss
    english_entry = {
        "lemma": "книга",
        "url_slug": "knyha",
        "gloss": "book",
        "primary_source": "course",
        "entry_type": "lexeme",
    }
    assert _entry_gloss(english_entry) == "book"
    assert _is_eligible(english_entry)


def test_committed_daily_pool_has_only_valid_english_glosses() -> None:
    """#8258: 100% of cards in the committed daily pool must carry non-empty English glosses
    with zero Cyrillic characters."""
    pool = json.loads(DEFAULT_OUT.read_text(encoding="utf-8"))
    assert len(pool) >= 1

    cyrillic_re = re.compile(r"[\u0400-\u04FF]")
    latin_re = re.compile(r"[A-Za-z]")

    for item in pool:
        lemma = item.get("lemma")
        gloss = item.get("gloss")
        assert isinstance(gloss, str), f"Card '{lemma}' is missing a gloss"
        assert gloss.strip(), f"Card '{lemma}' has an empty gloss"
        assert latin_re.search(gloss), f"Card '{lemma}' gloss has no Latin/English letters: '{gloss}'"
        assert not cyrillic_re.search(gloss), f"Card '{lemma}' gloss contains Cyrillic: '{gloss}'"


def test_example_translation_pairing_safety() -> None:
    """#8258 Claude CF: an entry's exampleEn must NEVER attach to a differing inventory sentence,
    and VERIFIED_SENTENCE_EN must strictly match the displayed Ukrainian text."""
    entry = {
        "lemma": "тест",
        "url_slug": "test",
        "gloss": "test",
        "primary_source": "course",
        "example": {"uk": "Речення з джерела.", "en": "Sentence from source."},
    }

    # Differing inventory sentence -> entry's example_en must NOT be attached
    differing_inventory = {
        "тест": {
            "sentence": "Зовсім інше речення з інвентаря.",
            "provenance": {"source": "textbook"},
            "license": {"type": "cc-by"},
        }
    }
    item = _pool_item(entry, differing_inventory)
    assert item is not None
    assert item["example"] == "Зовсім інше речення з інвентаря."
    assert "exampleEn" not in item  # Must NOT receive "Sentence from source."

    # Matching inventory sentence -> entry's example_en IS attached
    matching_inventory = {
        "тест": {
            "sentence": "Речення з джерела.",
            "provenance": {"source": "textbook"},
            "license": {"type": "cc-by"},
        }
    }
    item2 = _pool_item(entry, matching_inventory)
    assert item2 is not None
    assert item2["example"] == "Речення з джерела."
    assert item2.get("exampleEn") == "Sentence from source."

    # Sentence present in VERIFIED_SENTENCE_EN -> verified translation attached
    sample_uk = "Вербинка обережно підважила мох."
    sample_en = VERIFIED_SENTENCE_EN[sample_uk]
    moh_inventory = {
        "мох": {
            "sentence": sample_uk,
            "provenance": {"source": "textbook"},
            "license": {"type": "cc-by"},
        }
    }
    moh_entry = {
        "lemma": "мох",
        "url_slug": "mokh",
        "gloss": "moss",
        "primary_source": "course",
    }
    item3 = _pool_item(moh_entry, moh_inventory)
    assert item3 is not None
    assert item3["example"] == sample_uk
    assert item3.get("exampleEn") == sample_en
