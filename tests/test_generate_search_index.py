from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas import atlas_db
from scripts.audit.generate_search_index import (
    DEFAULT_BROWSE_DIR,
    DEFAULT_BROWSE_META_OUT,
    DEFAULT_SEARCH_OUT,
    UKRAINIAN_ALPHABET,
    _sanitize_typeahead_gloss,
    _search_gloss,
    build_atlas_db_search_artifacts,
    build_browse_outputs,
    build_index,
    classification_code,
    guard_browse_staleness,
    main,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def entry(
    lemma: str,
    *,
    slug: str | None = None,
    gloss: object = "gloss",
    primary_source: str = "built_vocabulary",
    classification: str | None = None,
    is_russianism: bool = False,
    warning_severity: str | None = None,
    cefr: object | None = None,
) -> dict[str, object]:
    heritage: dict[str, object] = {}
    if classification:
        heritage["classification"] = classification
    if is_russianism:
        heritage["is_russianism"] = True
    if warning_severity:
        heritage["warning_severity"] = warning_severity

    row: dict[str, object] = {
        "lemma": lemma,
        "url_slug": slug or lemma,
        "gloss": gloss,
        "primary_source": primary_source,
    }
    if heritage:
        row["enrichment"] = {"heritage": heritage}
    if cefr is not None:
        row["cefr"] = cefr
    return row


def fixture_entries() -> list[dict[str, object]]:
    return [
        entry("офіс", gloss="office"),
        entry("всьо", gloss="avoid: все", primary_source="surzhyk_to_avoid"),
        entry("дім", gloss="house", primary_source="plan_required", cefr="A1"),
        entry("кава", gloss="coffee", primary_source="plan_recommended", cefr={"level": "b1"}),
        entry("баба", slug="baba", gloss=7, primary_source="remainder"),
        {"lemma": "", "url_slug": "empty", "gloss": "skip"},
        {"lemma": "нема", "url_slug": "", "gloss": "skip"},
    ]


def atlas_db_fixture(
    tmp_path: Path,
    *,
    entries: list[dict[str, object]] | None = None,
) -> Path:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "entries": entries
                if entries is not None
                else [
                    entry("Іван", slug="іван", gloss="Ivan"),
                    entry("автобус", gloss="bus"),
                    {"lemma": "Іване", "url_slug": "іване", "form_of": {"url_slug": "іван"}},
                    {"lemma": "автобусом", "url_slug": "автобусом", "form_of": {"url_slug": "автобус"}},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "atlas.db"
    atlas_db.migrate_manifest(manifest, db)
    return db


def test_db_artifacts_keep_articles_and_aliases_separate_and_deduplicate(tmp_path: Path) -> None:
    db = atlas_db_fixture(tmp_path)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO aliases(alias, kind, source, target_slug, visibility) VALUES (?,?,?,?,?)",
        ("Іване", "spelling_variant", "test", "іван", "public"),
    )
    conn.commit()
    conn.close()

    articles, aliases, counts = build_atlas_db_search_artifacts(db)

    assert [row["s"] for row in articles] == ["автобус", "іван"]
    assert all(row["t"] == "lemma" for row in articles)
    assert {row["a"]: (row["s"], row["h"]) for row in aliases}["Іване"] == ("іван", "Іван")
    assert {row["a"]: row["s"] for row in aliases}["автобусом"] == "автобус"
    assert len([row for row in aliases if row["a"] == "Іване" and row["s"] == "іван"]) == 1
    assert counts["reviewed_entries"] == 2
    assert counts["public_alias_records"] == 6
    assert counts["emitted_aliases"] == 5
    assert counts["deduplicated_aliases"] == 1


def test_db_artifact_build_fails_on_the_site_build_entry_model_gates(tmp_path: Path) -> None:
    db = atlas_db_fixture(tmp_path)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO aliases(alias, kind, source, target_slug, visibility) VALUES (?,?,?,?,?)",
        ("привид", "spelling_variant", "test", "missing", "public"),
    )
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="alias_target_integrity failure"):
        build_atlas_db_search_artifacts(db)


def test_db_artifacts_emit_only_provenance_safe_gerund_parents(tmp_path: Path) -> None:
    dictionary_gerund = entry("читаючи", gloss="while reading")
    dictionary_gerund["enrichment"] = {
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["чита́ючи Дієприсл. недоконаного виду до чита́ти."],
            }
        ]
    }
    meaning_gerund = entry("прочитавши", gloss="having read")
    meaning_gerund["enrichment"] = {
        "meaning": {
            "source": "словник",
            "definitions": ["Дієприсл. доконаного виду до прочита́ти."],
        }
    }
    vesum_hint = entry("йдучи", gloss="while going")
    vesum_hint["enrichment"] = {
        "morphology": {
            "source": "VESUM",
            "pos": "advp",
            "paradigm": {"kind": "other", "verb": "іти"},
        }
    }
    pos_only = entry("сидячи", gloss="while sitting")
    pos_only["enrichment"] = {
        "morphology": {"source": "VESUM", "pos": "advp", "paradigm": {"kind": "other"}}
    }
    non_vesum = entry("лежачи", gloss="while lying")
    non_vesum["enrichment"] = {
        "morphology": {
            "source": "manual",
            "pos": "advp",
            "paradigm": {"kind": "other", "verb": "лежати"},
        }
    }
    wrong_vesum_pos = entry("стоячи", gloss="while standing")
    wrong_vesum_pos["enrichment"] = {
        "morphology": {
            "source": "VESUM",
            "pos": "adverbial participle",
            "paradigm": {"kind": "other", "verb": "стояти"},
        }
    }
    missing_parent = entry("кажучи", gloss="while saying")
    missing_parent["enrichment"] = {
        "definition_cards": [
            {"id": "sum20", "source": "СУМ-20", "definitions": ["Ка́жучи, дієприсл."]}
        ]
    }
    conflicting_parents = entry("роблячи", gloss="while doing")
    conflicting_parents["enrichment"] = {
        "meaning": {
            "source": "словник",
            "definitions": ["Дієприсл. недоконаного виду до роби́ти."],
        },
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["Роблячи Дієприсл. до вико́нувати."],
            }
        ],
    }
    unsourced_definition = entry("співаючи", gloss="while singing")
    unsourced_definition["enrichment"] = {
        "definition_cards": [
            {"id": "unattributed", "definitions": ["Дієприсл. до співа́ти."]}
        ]
    }
    learner_gloss = entry("танцюючи", gloss="Дієприсл. до танцюва́ти.")
    passive_participle = entry("читаний", gloss="read")
    passive_participle["enrichment"] = {
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["Дієпр. пас. мин. часу до чита́ти."],
            }
        ]
    }
    anna_copy = entry("працюючи", gloss="while working")
    anna_copy["enrichment"] = {
        "meaning": {
            "source": "Anna Ohoiko",
            "definitions": ["Дієприсл. до працюва́ти."],
        }
    }

    db = atlas_db_fixture(
        tmp_path,
        entries=[
            entry("читати"),
            entry("прочитати"),
            entry("іти"),
            dictionary_gerund,
            meaning_gerund,
            vesum_hint,
            pos_only,
            non_vesum,
            wrong_vesum_pos,
            missing_parent,
            conflicting_parents,
            unsourced_definition,
            learner_gloss,
            passive_participle,
            anna_copy,
        ],
    )

    articles, _, _ = build_atlas_db_search_artifacts(db)
    by_slug = {row["s"]: row for row in articles}

    assert by_slug["читаючи"]["p"] == "чита́ти"
    assert by_slug["прочитавши"]["p"] == "прочита́ти"
    assert by_slug["йдучи"]["p"] == "іти"
    for slug in (
        "сидячи",
        "лежачи",
        "стоячи",
        "кажучи",
        "роблячи",
        "співаючи",
        "танцюючи",
        "читаний",
        "працюючи",
    ):
        assert "p" not in by_slug[slug]


def test_db_mode_preserves_gerund_parent_in_search_rows_and_shards(tmp_path: Path) -> None:
    gerund = entry("говорячи", gloss="while speaking")
    gerund["enrichment"] = {
        "definition_cards": [
            {
                "id": "sum20",
                "source": "СУМ-20",
                "definitions": ["гово́рячи Дієприсл. до говори́ти."],
            }
        ]
    }
    db = atlas_db_fixture(tmp_path, entries=[entry("говорити"), gerund])
    search_out = tmp_path / "search.json"
    aliases_out = tmp_path / "aliases.json"
    search_shards_out = tmp_path / "search-shards.json"
    search_shard_dir = tmp_path / "search-shards"
    browse_meta_out = tmp_path / "browse-meta.json"
    browse_flagged_out = tmp_path / "browse-flagged.json"
    browse_dir = tmp_path / "browse"

    assert (
        main(
            [
                "--db",
                str(db),
                "--out",
                str(search_out),
                "--aliases-out",
                str(aliases_out),
                "--search-shards-out",
                str(search_shards_out),
                "--search-shard-dir",
                str(search_shard_dir),
                "--browse-meta-out",
                str(browse_meta_out),
                "--browse-flagged-out",
                str(browse_flagged_out),
                "--browse-dir",
                str(browse_dir),
            ]
        )
        == 0
    )

    search_rows = json.loads(search_out.read_text(encoding="utf-8"))
    gerund_row = next(row for row in search_rows if row["s"] == "говорячи")
    assert gerund_row["p"] == "говори́ти"

    search_shards = json.loads(search_shards_out.read_text(encoding="utf-8"))
    shard_key = next(
        key
        for key in search_shards["shards"]
        if any(
            row["s"] == "говорячи"
            for row in json.loads((search_shard_dir / f"{key}.json").read_text(encoding="utf-8"))
        )
    )
    shard_rows = json.loads((search_shard_dir / f"{shard_key}.json").read_text(encoding="utf-8"))
    assert next(row for row in shard_rows if row["s"] == "говорячи")["p"] == "говори́ти"
    assert all("p" not in row for row in json.loads((browse_dir / "Г.json").read_text(encoding="utf-8")))


def test_build_index_schema_sorting_filters_and_kind_buckets() -> None:
    rows = build_index(fixture_entries())

    assert [row["l"] for row in rows] == ["баба", "всьо", "дім", "кава", "офіс"]
    assert rows == [
        {"l": "баба", "s": "baba", "g": None, "r": "baba", "k": "other"},
        {"l": "всьо", "s": "всьо", "g": "avoid: все", "r": "vso", "k": "avoid", "cls": "avoid"},
        {"l": "дім", "s": "дім", "g": "house", "r": "dim", "k": "obov", "c": "A1"},
        {"l": "кава", "s": "кава", "g": "coffee", "r": "kava", "k": "rek", "c": "B1"},
        {"l": "офіс", "s": "офіс", "g": "office", "r": "ofis", "k": "vyv"},
    ]
def test_build_index_uses_translation_when_gloss_missing() -> None:
    rows = build_index(
        [
            {
                "lemma": "помішувати",
                "url_slug": "помішувати",
                "gloss": None,
                "primary_source": "built_vocabulary_normalized",
                "enrichment": {
                    "translation": {
                        "en": ["stir", "mix lightly"],
                        "source": "test",
                    }
                },
            }
        ]
    )

    assert rows == [
        {
            "l": "помішувати",
            "s": "помішувати",
            "g": "stir; mix lightly",
            "r": "pomishuvaty",
            "k": "vyv",
        }
    ]


_VOYEVODA_MASHED_GLOSS = (
    "1. У давній Русі та інших слов’янських державах — вождь, полководець, "
    "а також правитель міста, округу в XVI-XVIII ст. А в Римі свято. "
    "Велике свято! Тиск народу, Зо всього царств..."
)

# Cloned from lemma ба: Unicode ellipsis precedes a later ASCII ``...``.
_BA_MIXED_ELLIPSIS_GLOSS = (
    "Уживається для вираження здивування, здогаду і т. ін.; значенням близький "
    "до дивись. — Ти, як те сонечко, закрасиш мою смутну хату, розвеселиш "
    "матір… — Ба! У тебе й мати є? А я ..."
)


def test_sanitize_typeahead_gloss_keeps_sense_one_only_for_voyevoda_mash() -> None:
    gloss = _sanitize_typeahead_gloss(_VOYEVODA_MASHED_GLOSS)
    assert gloss is not None
    assert gloss.startswith("У давній Русі")
    assert "А в Римі свято" not in gloss
    assert "Велике свято" not in gloss
    assert "царств" not in gloss
    assert not gloss.endswith("...")
    assert not gloss.endswith("…")
    assert len(gloss) <= 180


def test_sanitize_typeahead_gloss_cuts_at_earliest_ellipsis_for_ba_mixed_markers() -> None:
    """Unicode ``…`` before ASCII ``...`` must win by index, not tuple order."""
    assert _BA_MIXED_ELLIPSIS_GLOSS.find("…") < _BA_MIXED_ELLIPSIS_GLOSS.find("...")
    gloss = _sanitize_typeahead_gloss(_BA_MIXED_ELLIPSIS_GLOSS)
    assert gloss is not None
    assert "…" not in gloss
    assert "..." not in gloss
    assert "— Ба!" not in gloss
    assert "мати є" not in gloss
    assert "дивись" in gloss
    assert len(gloss) <= 180


def test_sanitize_typeahead_gloss_leaves_short_voda_shaped_gloss_unchanged() -> None:
    assert _sanitize_typeahead_gloss("water") == "water"
    assert _sanitize_typeahead_gloss("shore, bank") == "shore, bank"


def test_search_gloss_falls_through_to_translation_when_empty_or_missing() -> None:
    translation_entry = {
        "lemma": "помішувати",
        "url_slug": "помішувати",
        "gloss": None,
        "enrichment": {"translation": {"en": ["stir", "mix lightly"]}},
    }
    assert _search_gloss(translation_entry) == "stir; mix lightly"
    assert _search_gloss({**translation_entry, "gloss": ""}) == "stir; mix lightly"
    assert _search_gloss({**translation_entry, "gloss": "   "}) == "stir; mix lightly"
    assert _search_gloss({"lemma": "x", "url_slug": "x", "gloss": None}) is None


def test_build_index_sanitizes_mashed_voyevoda_gloss_for_typeahead() -> None:
    rows = build_index(
        [
            entry("воєвода", gloss=_VOYEVODA_MASHED_GLOSS),
            entry("вода", gloss="water"),
        ]
    )
    by_lemma = {row["l"]: row for row in rows}
    assert by_lemma["вода"]["g"] == "water"
    assert by_lemma["воєвода"]["g"] is not None
    assert "А в Римі свято" not in by_lemma["воєвода"]["g"]
    assert "Велике свято" not in by_lemma["воєвода"]["g"]
    assert by_lemma["воєвода"]["g"].startswith("У давній Русі")


def test_classification_code_precedence_and_standard_omit() -> None:
    cases = [
        (
            entry(
                "avoid",
                primary_source="surzhyk_to_avoid",
                warning_severity="russianism_red",
                classification="borrowing",
            ),
            "avoid",
        ),
        (entry("red", warning_severity="russianism_red"), "rus"),
        (entry("shadow", classification="unknown", is_russianism=True), "rus"),
        (entry("calque", warning_severity="calque_yellow"), "calq"),
        (entry("arch", classification="authentic-archaism"), "arch"),
        (entry("dial", classification="dialect"), "dial"),
        (entry("hist", classification="historism"), "hist"),
        (entry("borr", classification="borrowing"), "borr"),
        (entry("standard", classification="standard"), None),
    ]

    assert [classification_code(row) for row, _ in cases] == [
        expected for _, expected in cases
    ]


def test_russianism_does_not_override_treasured_authentic_classifications() -> None:
    assert (
        classification_code(
            entry("другоє", classification="authentic-archaism", is_russianism=True)
        )
        == "arch"
    )
    assert classification_code(entry("ґазда", classification="dialect", is_russianism=True)) == "dial"
    assert (
        classification_code(entry("осавул", classification="historism", is_russianism=True))
        == "hist"
    )
    # A stale/hand-edited row may carry BOTH an authentic classification AND
    # warning_severity=russianism_red; the authentic class must still win (the
    # russianism_red branch was previously unconditional — cursor review catch).
    assert (
        classification_code(
            entry(
                "другоє",
                classification="authentic-archaism",
                warning_severity="russianism_red",
            )
        )
        == "arch"
    )


def test_browse_meta_counts_and_shards() -> None:
    rows = build_index(
        [
            entry("абетка", gloss="alphabet"),
            entry("архаїзм", gloss="archaism", classification="authentic-archaism"),
            entry("бета", gloss="beta", warning_severity="russianism_red"),
            entry("борщ", gloss="borshch", classification="borrowing"),
            entry("всьо", gloss="avoid all", primary_source="surzhyk_to_avoid"),
            entry("гетьман", gloss="hetman", classification="historism"),
            entry("ґанок", gloss="porch", classification="dialect"),
            entry("ґазда", gloss="host", classification="dialect"),
            entry("калька", gloss="calque", warning_severity="calque_yellow"),
        ]
    )

    meta, shards, flagged = build_browse_outputs(rows)

    assert meta["total"] == 9
    assert meta["letterCounts"]["А"] == 2
    assert meta["letterCounts"]["Б"] == 2
    assert meta["letterCounts"]["В"] == 1
    assert meta["letterCounts"]["Ґ"] == 2
    assert meta["letterCounts"]["Я"] == 0
    assert meta["chipCounts"] == {
        "avoid": 1,
        "rus": 1,
        "calq": 1,
        "arch": 1,
        "dial": 2,
        "hist": 1,
        "borr": 1,
    }
    assert meta["letterChip"]["А"]["arch"] == 1
    assert meta["letterChip"]["А"]["rus"] == 0
    assert meta["letterChip"]["Ґ"]["dial"] == 2
    assert meta["letterChip"]["Я"]["avoid"] == 0

    assert flagged == [
        {"l": "архаїзм", "s": "архаїзм", "g": "archaism", "c": None, "cls": "arch", "letter": "А"},
        {"l": "бета", "s": "бета", "g": "beta", "c": None, "cls": "rus", "letter": "Б"},
        {"l": "борщ", "s": "борщ", "g": "borshch", "c": None, "cls": "borr", "letter": "Б"},
        {"l": "всьо", "s": "всьо", "g": "avoid all", "c": None, "cls": "avoid", "letter": "В"},
        {"l": "гетьман", "s": "гетьман", "g": "hetman", "c": None, "cls": "hist", "letter": "Г"},
        {"l": "ґазда", "s": "ґазда", "g": "host", "c": None, "cls": "dial", "letter": "Ґ"},
        {"l": "ґанок", "s": "ґанок", "g": "porch", "c": None, "cls": "dial", "letter": "Ґ"},
        {"l": "калька", "s": "калька", "g": "calque", "c": None, "cls": "calq", "letter": "К"},
    ]

    assert list(shards) == ["А", "Б", "В", "Г", "Ґ", "К"]
    assert [row["l"] for row in shards["Ґ"]] == ["ґазда", "ґанок"]
    assert shards["А"][0] == {
        "l": "абетка",
        "s": "абетка",
        "g": "alphabet",
        "c": None,
        "hay": "абетка alphabet abetka",
    }
    assert shards["А"][1]["cls"] == "arch"
    assert shards["В"][0]["cls"] == "avoid"
    assert set(shards["Б"][0]) == {"l", "s", "g", "c", "hay", "cls"}


def test_main_writes_search_meta_and_per_letter_shards(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    search_out = tmp_path / "search.json"
    search_shards_out = tmp_path / "search-shards.json"
    search_shard_dir = tmp_path / "search-shards"
    meta_out = tmp_path / "meta.json"
    flagged_out = tmp_path / "flagged.json"
    browse_dir = tmp_path / "browse"
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    entry("арка", gloss="arch"),
                    entry("всьо", gloss="avoid all", primary_source="surzhyk_to_avoid"),
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert (
        main(
            [
                "--manifest",
                str(manifest),
                "--out",
                str(search_out),
                "--search-shards-out",
                str(search_shards_out),
                "--search-shard-dir",
                str(search_shard_dir),
                "--browse-meta-out",
            str(meta_out),
            "--browse-flagged-out",
            str(flagged_out),
            "--browse-dir",
            str(browse_dir),
            ]
        )
        == 0
    )

    search_rows = json.loads(search_out.read_text(encoding="utf-8"))
    search_shards = json.loads(search_shards_out.read_text(encoding="utf-8"))
    search_shard = json.loads((search_shard_dir / "u0432.json").read_text(encoding="utf-8"))
    meta = json.loads(meta_out.read_text(encoding="utf-8"))
    flagged = json.loads(flagged_out.read_text(encoding="utf-8"))
    shard = json.loads((browse_dir / "В.json").read_text(encoding="utf-8"))

    assert search_rows[1]["cls"] == "avoid"
    assert search_shards["total"] == 2
    assert search_shards["shards"]["u0432"]["count"] == 1
    assert search_shard == [search_rows[1]]
    assert meta["total"] == 2
    assert meta["chipCounts"] == {"avoid": 1}
    assert flagged == [{"l": "всьо", "s": "всьо", "g": "avoid all", "c": None, "cls": "avoid", "letter": "В"}]
    assert shard == [
        {
            "l": "всьо",
            "s": "всьо",
            "g": "avoid all",
            "c": None,
            "hay": "всьо avoid all vso",
            "cls": "avoid",
        }
    ]


def test_committed_browse_records_remain_distinct_from_article_search_entries() -> None:
    search_rows = json.loads((PROJECT_ROOT / DEFAULT_SEARCH_OUT).read_text(encoding="utf-8"))
    meta = json.loads((PROJECT_ROOT / DEFAULT_BROWSE_META_OUT).read_text(encoding="utf-8"))
    letter_counts = meta["letterCounts"]

    assert set(letter_counts) == set(UKRAINIAN_ALPHABET)
    # Browse keeps legacy route records for compatibility; the DB-derived
    # search index contains reviewed articles only and is the only surface
    # whose count is an entry total.
    assert all("t" in row for row in search_rows)
    assert meta["total"] >= len(search_rows)

    shard_total = 0
    for letter in UKRAINIAN_ALPHABET:
        shard_path = PROJECT_ROOT / DEFAULT_BROWSE_DIR / f"{letter}.json"
        rows = json.loads(shard_path.read_text(encoding="utf-8")) if shard_path.exists() else []
        assert len(rows) == letter_counts[letter]
        shard_total += len(rows)

    assert shard_total == meta["total"]


def test_legacy_run_refuses_to_overwrite_article_index(tmp_path, monkeypatch) -> None:
    """A plain (manifest-lemma) run must not clobber the DB-derived articles index (#5080)."""
    import scripts.audit.generate_search_index as gsi

    article_out = tmp_path / "lexicon-search-index.json"
    article_out.write_text(json.dumps([{"t": "Стаття", "l": "стаття"}]), encoding="utf-8")
    monkeypatch.setattr(gsi, "DEFAULT_SEARCH_OUT", article_out)

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"entries": []}), encoding="utf-8")

    with pytest.raises(SystemExit, match="refusing legacy manifest-lemma run"):
        gsi.main(["--manifest", str(manifest)])

    # Lemma-format existing file (no "t") does NOT trip the guard.
    article_out.write_text(json.dumps([{"l": "стаття", "s": "стаття"}]), encoding="utf-8")
    rc = gsi.main(
        [
            "--manifest", str(manifest),
            "--aliases-out", str(tmp_path / "aliases.json"),
            "--search-shards-out", str(tmp_path / "shards.json"),
            "--search-shard-dir", str(tmp_path / "shard-dir"),
            "--browse-meta-out", str(tmp_path / "browse-meta.json"),
            "--browse-flagged-out", str(tmp_path / "browse-flagged.json"),
            "--browse-dir", str(tmp_path / "browse"),
        ]
    )
    assert rc == 0


def test_db_mode_writes_browse_artifacts(tmp_path: Path) -> None:
    db = atlas_db_fixture(tmp_path)
    search_out = tmp_path / "search.json"
    aliases_out = tmp_path / "aliases.json"
    search_shards_out = tmp_path / "search-shards.json"
    meta_out = tmp_path / "browse-meta.json"
    flagged_out = tmp_path / "browse-flagged.json"
    browse_dir = tmp_path / "browse"

    assert (
        main(
            [
                "--db",
                str(db),
                "--out",
                str(search_out),
                "--aliases-out",
                str(aliases_out),
                "--search-shards-out",
                str(search_shards_out),
                "--browse-meta-out",
                str(meta_out),
                "--browse-flagged-out",
                str(flagged_out),
                "--browse-dir",
                str(browse_dir),
            ]
        )
        == 0
    )

    _, _, counts = build_atlas_db_search_artifacts(db)
    meta = json.loads(meta_out.read_text(encoding="utf-8"))
    flagged = json.loads(flagged_out.read_text(encoding="utf-8"))
    search_rows = json.loads(search_out.read_text(encoding="utf-8"))

    assert counts["reviewed_entries"] == 2
    assert len(search_rows) == 2
    assert meta["schema"] == "atlas-browse-meta"
    assert meta["total"] == 2
    assert meta["letterCounts"]["А"] == 1
    assert meta["letterCounts"]["І"] == 1
    assert flagged == []
    assert json.loads((browse_dir / "А.json").read_text(encoding="utf-8")) == [
        {
            "l": "автобус",
            "s": "автобус",
            "g": "bus",
            "c": None,
            "hay": "автобус bus avtobus",
        },
    ]
    assert json.loads((browse_dir / "І.json").read_text(encoding="utf-8")) == [
        {
            "l": "Іван",
            "s": "іван",
            "g": "Ivan",
            "c": None,
            "hay": "іван ivan ivan",
        },
    ]


def test_browse_staleness_guard_fires_when_browse_would_stay_pinned(tmp_path: Path) -> None:
    stale_meta = tmp_path / "browse-meta.json"
    stale_meta.write_text(json.dumps({"total": 1}), encoding="utf-8")

    with pytest.raises(SystemExit, match="browse-meta stale"):
        guard_browse_staleness(stale_meta, reviewed_article_count=5, will_refresh_browse=False)


def test_browse_staleness_guard_allows_refresh_when_browse_will_be_rewritten(tmp_path: Path) -> None:
    stale_meta = tmp_path / "browse-meta.json"
    stale_meta.write_text(json.dumps({"total": 1}), encoding="utf-8")

    guard_browse_staleness(stale_meta, reviewed_article_count=5, will_refresh_browse=True)
